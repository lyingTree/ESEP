# -*- coding:utf-8 -*-
"""
--------------------------------------------------------------------------------
                                                                              
                    File Name : core.py

                   Start Date : 2021-08-31 15:46

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

--------------------------------------------------------------------------------
Introduction:

job queue core

--------------------------------------------------------------------------------
"""
import abc
import logging
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from contextlib import contextmanager, suppress
from pathlib import Path

logger = logging.getLogger(__name__)
job_parameters = """
    cores : int
        Total number of cores per job
    memory: str
        Total amount of memory per job
    processes : int
        Cut the job up into this many processes. Good for GIL workloads or for
        nodes with many cores.
        By default, ``process ~= sqrt(cores)`` so that the number of processes
        and the number of threads per process is roughly the same.
    interface : str
        Network interface like 'eth0' or 'ib0'. This will be used both for the
        Dask scheduler and the Dask workers interface. If you need a different
        interface for the Dask scheduler you can pass it through
        the ``scheduler_options`` argument:
        ``interface=your_worker_interface, scheduler_options={'interface': your_scheduler_interface}``.
    nanny : bool
        Whether or not to start a nanny process
    local_directory : str
        Dask worker local directory for file spilling.
    death_timeout : float
        Seconds to wait for a scheduler before closing workers
    extra : list
        Additional arguments to pass to `dask-worker`
    env_extra : list
        Other commands to add to script before launching worker.
    header_skip : list
        Lines to skip in the header.
        Header lines matching this text will be removed
    log_directory : str
        Directory to use for job scheduler logs.
    shebang : str
        Path to desired interpreter for your batch submission script.
    python : str
        Python executable used to launch Dask workers.
        Defaults to the Python that is submitting these jobs
    config_name : str
        Section to use from jobqueue.yaml configuration file.
    name : str
        Name of Dask worker.  This is typically set by the Cluster
""".strip()


@contextmanager
def tmpfile(extension=""):
    extension = "." + extension.lstrip(".")
    handle, filepath = tempfile.mkstemp(extension)
    os.close(handle)
    Path(filepath).unlink()

    yield filepath
    fp = Path(filepath)
    if fp.exists():
        try:
            if fp.is_dir():
                shutil.rmtree(fp)
            else:
                fp.unlink()
        except OSError:  # sometimes we can't remove a generated temp file
            pass


class Job:
    """ Base class to launch Dask workers on Job queues

    This class should not be used directly, use a class appropriate for
    your queueing system (e.g. PBScluster or SLURMCluster) instead.

    Parameters
    ----------
    {job_parameters}

    Attributes
    ----------
    submit_command: str
        Abstract attribute for job scheduler submit command,
        should be overridden
    cancel_command: str
        Abstract attribute for job scheduler cancel command,
        should be overridden

    See Also
    --------
    PBSCluster
    SLURMCluster
    SGECluster
    OARCluster
    LSFCluster
    MoabCluster
    """.format(
        job_parameters=job_parameters
    )

    _script_template = """%(shebang)s\n%(job_header)s\n\n%(env_header)s\n\n%(run_command)s\n""".lstrip()

    # Following class attributes should be overridden by extending classes.
    submit_command = None
    cancel_command = None
    check_command = None
    manage_command = None
    job_id_regexp = r"(?P<job_id>\d+)"
    _job_file = None

    @abc.abstractmethod
    def __init__(self, app_command, nodes=None, cores=None, mpi_extra=None, env_extra=None, header_skip=None,
                 log_directory=None, shebang=None, job_name=None):
        # self.scheduler = scheduler
        self.job_id = None

        # This attribute should be set in the derived class
        self.job_header = None
        self.nodes = nodes or 1
        self.cores = cores or 1

        if job_name is None:
            job_name = "Test"
        self.job_name = job_name

        if shebang is None:
            shebang = "#!/bin/sh"
        self.shebang = shebang
        if env_extra is None:
            env_extra = []
        if header_skip is None:
            header_skip = ()

        self._env_header = "\n".join(filter(None, env_extra))
        self.header_skip = set(header_skip)
        if mpi_extra is None:
            mpi_extra = []
        command_args = ["mpiexec -np", self.nodes * self.cores]
        command_args.extend(mpi_extra)
        command_args.append(app_command)
        self._command = " ".join(map(str, command_args))

        self.log_directory = log_directory
        if self.log_directory is not None:
            log_dir_path = Path(self.log_directory)
            if not log_dir_path.exists():
                log_dir_path.mkdir()

    @classmethod
    def default_config_name(cls):
        config_name = getattr(cls, "config_name", None)
        if config_name is None:
            raise ValueError(
                "The class {} is required to have a 'config_name' class variable.\n"
                "If you have created this class, please add a 'config_name' class variable.\n"
                "If not this may be a bug, feel free to create an issue at: "
                "https://github.com/dask/dask-jobqueue/issues/new".format(cls)
            )
        return config_name

    def job_script(self):
        """Construct a job submission script"""
        header = "\n".join(
            [
                line
                for line in self.job_header.split("\n")
                if not any(skip in line for skip in self.header_skip)
            ]
        )
        pieces = {
            "shebang": self.shebang,
            "job_header": header,
            "env_header": self._env_header,
            "run_command": self._command,
        }
        return self._script_template % pieces

    def job_file(self, filepath):
        """Write job submission script to temporary file"""
        with open(filepath, 'w') as fh:
            logger.debug("writing job script: \n%s", self.job_script())
            fh.write(self.job_script())
        self._job_file = filepath

    def submit(self):
        """Start job"""
        out = self._submit_job(str(self._job_file))
        self.job_id = self._job_id_from_submit_output(out)
        logger.debug("Starting job: %s", self.job_id)

    def _submit_job(self, script_filename):
        return self._call(shlex.split(self.submit_command) + [script_filename])

    def _job_id_from_submit_output(self, out):
        match = re.search(self.job_id_regexp, out)
        if match is None:
            msg = (
                "Could not parse job id from submission command "
                "output.\nJob id regexp is {!r}\nSubmission command "
                "output is:\n{}".format(self.job_id_regexp, out)
            )
            raise ValueError(msg)

        job_id = match.groupdict().get("job_id")
        if job_id is None:
            msg = (
                "You need to use a 'job_id' named group in your regexp, e.g. "
                "r'(?P<job_id>\\d+)'. Your regexp was: "
                "{!r}".format(self.job_id_regexp)
            )
            raise ValueError(msg)

        return job_id

    def close(self):
        logger.debug("Stopping job: %s", self.job_id)
        self._close_job(self.job_id)

    def status(self):
        logger.debug("Getting job: %s information", self.job_id)
        return self._job_status(self.job_id)

    @classmethod
    def _close_job(cls, job_id):
        if job_id:
            with suppress(RuntimeError):  # deleting job when job already gone
                cls._call(shlex.split(cls.cancel_command) + [job_id])
            logger.debug("Closed job %s", job_id)

    @classmethod
    def _job_status(cls, job_id):
        if job_id:
            logger.debug("checking job %s\n", job_id)
            try:
                out = cls._call(shlex.split(cls.check_command) + [job_id])
            except RuntimeError:
                logger.debug("job %s occur ERROR\n\n%s\n\n", job_id, out)
                return False, out
            logger.debug("%s\n", out)
            return True, out
        return False, ""

    @staticmethod
    def _call(cmd, **kwargs):
        """Call a command using subprocess.Popen.

        This centralizes calls out to the command line, providing consistent
        outputs, logging, and an opportunity to go asynchronous in the future.

        Parameters
        ----------
        cmd: List(str))
            A command, each of which is a list of strings to hand to
            subprocess.Popen

        Examples
        --------
        >>> self._call(['ls', '/foo'])

        Returns
        -------
        The stdout produced by the command, as string.

        Raises
        ------
        RuntimeError if the command exits with a non-zero exit code
        """
        cmd_str = " ".join(cmd)
        logger.debug(
            "Executing the following command to command line\n{}".format(cmd_str)
        )

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )

        out, err = proc.communicate()
        out, err = out.decode(), err.decode()

        if proc.returncode != 0:
            raise RuntimeError(
                "Command exited with non-zero exit code.\n"
                "Exit code: {}\n"
                "Command:\n{}\n"
                "stdout:\n{}\n"
                "stderr:\n{}\n".format(proc.returncode, cmd_str, out, err)
            )
        return out


class JobQueueCluster:
    __doc__ = """ Deploy program on a Job queuing system

    This is a superclass, and is rarely used directly.  It is more common to
    use an object like SGECluster, SLURMCluster, PBSCluster, LSFCluster, or
    others.

    However, it can be used directly if you have a custom ``Job`` type.
    This class relies heavily on being passed a ``Job`` type that is able to
    launch one Job on a job queueing system.

    Parameters
    ----------
    Job : Job
        A class that can be awaited to ask for a single Job

    """

    def __init__(self, job_cls: Job = None, **job_kwargs):
        default_job_cls = getattr(type(self), "job_cls", None)
        self.job_cls = default_job_cls
        if job_cls is not None:
            self.job_cls = job_cls

        if self.job_cls is None:
            raise ValueError(
                "You need to specify a Job type. Two cases:\n"
                "- you are inheriting from JobQueueCluster (most likely): you need to add a 'job_cls' class variable "
                "in your JobQueueCluster-derived class {}\n"
                "- you are using JobQueueCluster directly (less likely, only useful for tests): "
                "please explicitly pass a Job type through the 'job_cls' parameter.".format(
                    type(self)
                )
            )
        self._dummy_job = self.job_cls(**job_kwargs)

    @property
    def job_header(self):
        return self._dummy_job.job_header

    @property
    def job_script(self):
        return self._dummy_job.job_script()

    def script2file(self, filepath):
        return self._dummy_job.job_file(filepath)

    def submit(self):
        return self._dummy_job.submit()

    def close(self):
        return self._dummy_job.close()

    @property
    def status(self):
        return self._dummy_job.status()

    @property
    def job_name(self):
        return self._dummy_job.job_name

    @property
    def job_id(self):
        return self._dummy_job.job_id

# -*- coding:utf-8 -*-
"""
--------------------------------------------------------------------------------

                    File Name : pbs.py

                   Start Date : 2021-09-09 00:00

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

--------------------------------------------------------------------------------
Introduction:

Protable Batch System

--------------------------------------------------------------------------------
"""
import logging
import os

from .core import Job, JobQueueCluster, job_parameters

logger = logging.getLogger(__name__)


class PBSJob(Job):
    submit_command = "qsub"
    cancel_command = "qdel"
    check_command = "qstat"
    manage_command = "pbsnodes"

    def __init__(self, app_command, queue=None, project=None, walltime=None, **base_class_kwargs):
        super().__init__(app_command, **base_class_kwargs)

        # Try to find a project name from environment variable
        project = project or os.environ.get("PBS_ACCOUNT")

        header_lines = []
        # PBS header build
        if self.job_name is not None:
            header_lines.append("#PBS -N %s" % self.job_name)
        if queue is not None:
            header_lines.append("#PBS -q %s" % queue)
        if project is not None:
            header_lines.append("#PBS -A %s" % project)
        if self.nodes is None:
            self.nodes = 1
        if self.cores is None:
            self.cores = 1
        resource_spec = "nodes={0}:ppn={1}".format(self.nodes, self.cores)
        header_lines.append("#PBS -l %s" % resource_spec)
        if walltime is not None:
            header_lines.append("#PBS -l walltime=%s" % walltime)
        if self.log_directory is not None:
            header_lines.append("#PBS -e %s/" % self.log_directory)
            header_lines.append("#PBS -o %s/" % self.log_directory)

        # Declare class attribute that shall be overridden
        self.job_header = "\n".join(header_lines)

        logger.debug("Job script: \n %s" % self.job_script())


class PBSCluster(JobQueueCluster):
    __doc__ = """ Run the program on a PBS cluster

    Parameters
    ----------
    queue : str
        Destination queue for each worker job. Passed to `#PBS -q` option.
    project : str
        Accounting string associated with each worker job. Passed to `#PBS -A` option.
    {job}
    resource_spec : str
        Request resources and specify job placement. Passed to `#PBS -l` option.
    walltime : str
        Walltime for each worker job.
    
    """.format(job=job_parameters)

    job_cls = PBSJob

    @property
    def status(self):
        out_dict = dict()
        flag, out = self._dummy_job.status()
        if flag:
            tmp = list(filter(None, out.split('\n')[2].split(' ')))
            out_dict = dict(job_id=tmp[0].split('.')[0], job_name=tmp[1], user=tmp[2], time_use=tmp[3], status=tmp[4],
                            queue=tmp[5])
        return flag, out, out_dict

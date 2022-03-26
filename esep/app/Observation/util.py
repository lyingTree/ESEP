# -*- coding:uft-8 -*-
import multiprocessing as mp
import re
from datetime import datetime, timedelta
from os import getcwd, makedirs, path as os_path

import numpy as np
from netCDF4 import Dataset, num2date, date2num


def check_needed_dir(prefix):
    curt_dir = getcwd()
    if not os_path.exists(prefix + 'Preprocess'):
        makedirs(prefix + 'Preprocess')

    if not os_path.exists(curt_dir + '/result/Valid_Range'):
        makedirs(curt_dir + '/result/Valid_Range')

    if not os_path.exists(curt_dir + '/result/Current_Magnitude'):
        makedirs(curt_dir + '/result/Current_Magnitude')


def parallel_apply_along_axis(func1d, axis, arr, *args, **kwargs):
    """
    Like numpy.apply_along_axis(), but takes advantage of multiple cores.
    """
    # Effective axis where apply_along_axis() will be applied by each
    # worker (any non-zero axis number would work, so as to allow the use
    # of `np.array_split()`, which is only done on axis 0):
    if len(np.shape(arr)) > 1:
        effective_axis = 1 if axis == 0 else axis
        if effective_axis != axis:
            arr = np.swapaxes(arr, axis, effective_axis)
    else:
        effective_axis = 0

    # Chunks for the mapping (only a few chunks):
    chunks = [(func1d, effective_axis, sub_arr, args, kwargs)
              for sub_arr in np.array_split(arr, mp.cpu_count())]
    pool = mp.Pool(mp.cpu_count())
    individual_results = pool.map(unpacking_apply_along_axis, chunks)
    # Freeing the workers:
    pool.close()
    pool.join()

    return np.concatenate(individual_results)


def unpacking_apply_along_axis(all_args):
    (func1d, axis, arr, args, kwargs) = all_args
    return np.apply_along_axis(func1d, axis, arr, *args, **kwargs)


class SegmentOperate(object):
    def __init__(self, data, length, method=np.nanmean, axis=0):
        axis_len = np.shape(data)[axis]
        self.num = int(np.ceil(axis_len / length))
        self.calc_len = np.size(data) / axis_len
        self.method = method
        self.data = data
        self.axis = axis

    @property
    def value(self):
        if (self.calc_len > 100 and self.num > 10) or self.num > 500:
            return parallel_apply_along_axis(self.calc, self.axis, self.data)
        else:
            return np.apply_along_axis(self.calc, self.axis, self.data)

    def calc(self, data):
        return np.array(
            [self.method(x) for x in np.array_split(data, self.num)])


def time_round(org_dt, time_units, calendar):
    org_dt = num2date(org_dt, time_units, calendar)
    for i, dt in enumerate(org_dt):
        if dt.second > 30:
            org_dt[i] = datetime(dt.year, dt.month, dt.day, dt.hour,
                                 dt.minute) + timedelta(minutes=1)
        else:
            org_dt[i] = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute)
    return date2num(org_dt, time_units, calendar)


def correct0drift(dep, vdd):
    # correct 0 drifting
    pre_time_end = 0
    for i in range(len(dep) - 1):
        if np.abs(dep[i + 1] - dep[i]) > vdd:
            pre_time_end = i + 1
            break
    if pre_time_end == 0:
        raise IndexError('The 0 drifting not found')
    return np.mean(dep[:pre_time_end])


def detect_brand(obs, instrument):
    rslt = []
    for i, val in enumerate(obs):
        if instrument == val.split('-')[0]:
            rslt.append(val.split('-')[-1])
    return rslt


def is_number(num_str: str) -> bool:
    """Judge the string whether is a digital string.

    :param num_str: class:str, A string that could be a number
    :return: class:bool, the result of judge whether the string is a number.
    ------------------------------------------------------------------
    Examples:

    """
    pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    rslt = pattern.match(num_str)
    if rslt:
        return True
    else:
        return False


def extract_valid_time(data_path, save_path, group=None, vdd=0.2, zlib=False,
                       complevel=1):
    resp = []
    ncfile = Dataset(data_path)
    data_grp = ncfile
    if group is not None:
        if group not in ncfile.groups:
            resp.append('Lack of average data can not filter valid time')
            return False, resp
        else:
            data_grp = ncfile[group]
    dep = data_grp['dep']
    last_idx = len(dep) - 1
    valid_strt = 0
    valid_end = last_idx
    data = {}
    flag = False
    for i in range(last_idx):
        if flag and np.abs(dep[i + 1] - dep[i]) < vdd:
            valid_strt = i
            break
        else:
            if np.abs(dep[i + 1] - dep[i]) > vdd:
                flag = True
    flag = False
    for i in range(last_idx, 0, -1):
        if flag and np.abs(dep[i - 1] - dep[i]) < vdd:
            valid_end = i
            break
        else:
            if np.abs(dep[i - 1] - dep[i]) > vdd:
                flag = True

    for name in data_grp.variables:
        var = data_grp[name]
        dim = var.dimensions
        dim_len = len(dim)
        if 'time' in dim:
            if dim_len == 1:
                data[name] = var[valid_strt:valid_end].data
            else:
                time_idx = dim.index('time')
                if time_idx:
                    data[name] = var[:, valid_strt:valid_end].data
                else:
                    data[name] = var[valid_strt:valid_end, :].data
    modify_nc(data_path, save_path, data, group, zlib=zlib, complevel=complevel)
    return True, None


def modify_nc(src_path, dst_path, data=None, tgt_datagrp=None, meta=None,
              tgt_metagrp=None, zlib=False, complevel=1):
    with Dataset(src_path) as src, Dataset(dst_path, "w") as dst:
        # create groups
        for grpname in src.groups:
            dst.createGroup(grpname)

        # copy attributes
        for name in src.ncattrs():
            if meta is not None and tgt_metagrp is None and name in meta:
                dst.setncattr(name, meta[name])
            else:
                dst.setncattr(name, src.getncattr(name))

        # copy dimensions
        for name, dimension in src.dimensions.items():
            if data is not None and tgt_datagrp is None and name in data:
                dst.createDimension(name, (
                    len(data[name]) if not dimension.isunlimited else None))
            else:
                dst.createDimension(name, (
                    len(dimension) if not dimension.isunlimited else None))

        # copy variables
        for name, variable in src.variables.items():
            tmp = dst.createVariable(name, variable.datatype,
                                     variable.dimensions, zlib=zlib,
                                     complevel=complevel)
            if data is not None and tgt_datagrp is None and name in data:
                dst.variables[name][:] = data[name]
            else:
                dst.variables[name][:] = src.variables[name][:]
                for attr_name in src[name].ncattrs():
                    tmp.setncattr(attr_name, src[name].getncattr(attr_name))
        # ----------------------------------------------------------------------
        # Groups
        for grpname in src.groups:
            # copy groups attributes
            for name in src[grpname].ncattrs():
                if meta is not None and name in meta and grpname == tgt_datagrp:
                    dst[grpname].setncattr(name, meta[name])
                else:
                    dst[grpname].setncattr(name, src[grpname].getncattr(name))

            # copy groups dimensions
            for name, dimension in src[grpname].dimensions.items():
                if data is not None and name in data and grpname == tgt_datagrp:
                    dst[grpname].createDimension(name, (
                        len(data[name]) if not dimension.isunlimited else None))
                else:
                    dst[grpname].createDimension(name, (
                        len(dimension) if not dimension.isunlimited else None))
            # copy groups variables
            for name, variable in src[grpname].variables.items():
                tmp = dst[grpname].createVariable(name, variable.datatype,
                                                  variable.dimensions,
                                                  zlib=zlib,
                                                  complevel=complevel)
                if data is not None and name in data and grpname == tgt_datagrp:
                    dst[grpname].variables[name][:] = data[name]
                else:
                    dst[grpname].variables[name][:] = src[grpname].variables[
                                                          name][:]
                for attr_name in src[grpname][name].ncattrs():
                    tmp.setncattr(attr_name,
                                  src[grpname][name].getncattr(attr_name))

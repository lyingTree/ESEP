# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : hpc.py

                   Start Date : 2022-03-25 08:04

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

高性能计算设计函数

-------------------------------------------------------------------------------
"""
import multiprocessing as mp

import numpy as np


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
    def __init__(self, data, length, method=np.nanmean, axis=0, split_enable=True, *args, **kwargs):
        axis_len = np.shape(data)[axis]
        self.num = int(np.ceil(axis_len / length))
        self.calc_len = np.size(data) / axis_len
        self.method = method
        self.data = data
        self.axis = axis
        self.split_enable = split_enable
        self.args = args
        self.kwargs = kwargs

    @property
    def value(self):
        # 这里的 1000、50、5000 纯粹是自身经验的选择
        if self.split_enable and (self.calc_len > 1000 and self.num > 50) or self.num > 5000:
            return parallel_apply_along_axis(self._calc, self.axis, self.data)
        return np.apply_along_axis(self._calc, self.axis, self.data)

    def _calc(self, data):
        return np.array(self.method(data, *self.args, **self.kwargs))

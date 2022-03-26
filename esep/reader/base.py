# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : base.py

                   Start Date : 2021-10-06 10:44

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

数据读取基类

-------------------------------------------------------------------------------
"""
from datetime import datetime, timedelta
from pathlib import Path

import netCDF4 as nc
import numpy as np


class ModelBaseReader:
    time_name = None

    def __init__(self, fp):
        self.ds = nc.MFDataset(fp) if isinstance(fp, list) else nc.Dataset(fp)
        self.lon = self.ds['lon'][:]
        self.lat = self.ds['lat'][:]
        self.time = self.ds[self.time_name][:]

    def variables(self, variables_name: list):
        for var_name in variables_name:
            self.__setattr__(var_name, self.ds[var_name])


class UnstructuredReaderModel(ModelBaseReader):
    def __init__(self, fp):
        super(UnstructuredReaderModel, self).__init__(fp)
        self.time = np.array([datetime.strptime(x.tobytes().decode(), '%Y-%m-%dT%H:%M:%S.%f') for x in self.time])
        self.time_bj = np.array([x + timedelta(hours=8) for x in self.time])
        self.lonc = self.ds['lonc'][:]
        self.latc = self.ds['latc'][:]
        # 减去1是将 node ID 转为python中的 node index
        self.tri = np.transpose(self.ds['nv'][:]) - 1


class NormalReader:
    ds = None

    def __init__(self, fp):
        self.fp = Path(fp)

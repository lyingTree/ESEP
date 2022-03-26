# -*- coding: utf-8 -*-
"""
#------------------------------------------------------------------------------#
#                                                                              #
#                 Project Name : Atmosphere&Ocean                              #
#                                                                              #
#                    File Name : data_read.py                                  #
#                                                                              #
#                      Version : 0.0.1                                         #
#                                                                              #
#                  Contributor : D.CW                                          #
#                                                                              #
#                   Start Date : 2020-04-01 09:15:09                           #
#                                                                              #
#                  Last Update : 2020-07-17 23:08:57                           #
#                                                                              #
#                        Email : dengchuangwu@gmail.com                        #
#                                                                              #
#------------------------------------------------------------------------------#
# Introduction:                                                                #
# Provides data reading function for linear grid netcdf files, HDF files       #
# and WRF-ouput.                                                               #
#                                                                              #
#-----------------------------------------------------------------------------*#
# Functions:                                                                   #
#******************************* class: WrfData *******************************#
#                                                                              #
#                                                                              #
#******************************* class: NcData ********************************#
#   set_rng -- Set the value range.                                            #
#   get_var -- Get the value of the specified variable.                        #
#                                                                              #
#******************************* class: HdfData *******************************#
#   set_rng -- Set the value range.                                            #
#   get_var -- Get the value of the specified variable.                        #
#                                                                              #
#------------------------------------------------------------------------------#
"""
# Standard libraries
from __future__ import (absolute_import, division, print_function)
from datetime import datetime
from glob import glob
from os import remove

# Third-party libraries
from netCDF4 import Dataset, MFDataset, MFTime
from xarray import open_mfdataset, DataArray
import numpy as np
import pyresample
import wrf

# Local libraries
from .decorator import is_none
from .util import path2nc, extra_same_elem, get_dims, adjust_dim, \
    cnv_ls2slice,get_time


class WrfData(object):
    def __init__(self):
        pass

    def read(self, wrf_fpaths, var_name, lev_seq, lat_seq, lon_seq,
             interp_ena=False):
        nc_ls = path2nc(wrf_fpaths)
        var = wrf.getvar(nc_ls, var_name, method='join')
        if interp_ena:
            var = self._interp(wrf_fpaths, var, lev_seq, lat_seq, lon_seq)

        return var

    def pvo(self, wrf_fpaths, lev_seq, lat_seq, lon_seq, interp_ena=False):
        nc_ls = path2nc(wrf_fpaths)

        U = wrf.getvar(nc_ls, "U", method='join')
        V = wrf.getvar(nc_ls, "V", method='join')
        THETA = wrf.getvar(nc_ls, "T", method='join')
        P = wrf.getvar(nc_ls, "P", method='join')
        PB = wrf.getvar(nc_ls, "PB", method='join')
        MSFU = wrf.getvar(nc_ls, "MAPFAC_U", method='join')
        MSFV = wrf.getvar(nc_ls, "MAPFAC_V", method='join')
        MSFM = wrf.getvar(nc_ls, "MAPFAC_M", method='join')
        COR = wrf.getvar(nc_ls, "F", method='join')
        DX = nc_ls[0].DX
        DY = nc_ls[0].DY
        # 数据处理
        THETA = THETA + 300
        P = P + PB
        PV = wrf.pvo(U, V, THETA, P, MSFU, MSFV, MSFM, COR, DX, DY)
        if interp_ena:
            PV = self._interp(wrf_fpaths, PV, lev_seq, lat_seq, lon_seq)

        return PV

    def _interp(self, wrf_fpaths, var, lev_seq, lat_seq, lon_seq):
        lev_num = np.size(lev_seq)
        lat_num = np.size(lat_seq)
        lon_num = np.size(lon_seq)
        nc_ls = path2nc(wrf_fpaths)
        lon_curv = wrf.getvar(nc_ls, "XLONG")
        lat_curv = wrf.getvar(nc_ls, "XLAT")
        p = wrf.getvar(nc_ls, "pressure", method='join')

        orig_shp = np.shape(p)
        wrf_var = np.ones([orig_shp[0], lev_num, lat_num, lon_num])
        lon2d_inter, lat2d_inter = np.meshgrid(lon_seq, lat_seq)
        orig_def = pyresample.geometry.SwathDefinition(
            lons=lon_curv, lats=lat_curv)
        targ_def = pyresample.geometry.SwathDefinition(
            lons=lon2d_inter, lats=lat2d_inter)

        var = self.eliminate_stagger(var)
        for i in range(0, orig_shp[0]):
            var_vert_interp = wrf.to_np(
                wrf.interplevel(var[i], p[i], lev_seq, False))
            for j in range(0, lev_num):
                wrf_var[i, j, :, :] = pyresample.kd_tree.resample_nearest(
                    orig_def, var_vert_interp[j], targ_def,
                    radius_of_influence=500000, fill_value=None)
        return wrf_var

    @staticmethod
    def eliminate_stagger(var: DataArray):
        """Interpolate stagger grid to regular grid

        :param var: class:xarray.DataArray, The variable of wrf-output with
        stagger dimension
        :return: class:xarray.DataArray, The variable of wrf-output with
        normal dimensions
        ------------------------------------------------------------------
        Examples:

        """
        dims = var.dims
        # 插值到需要的层次、区域，同时也将域坐标转换为了经纬坐标
        for i in range(np.size(dims)):
            if "stag" in dims[i]:
                var = wrf.destagger(var, i, meta=True)

        return var


class NcData(object):
    """Read linear grid file in netCDF

    Created date: 2020-06-03 19:03:06
    Last modified date: 2020-06-06 17:46:21
    Contributor: D.CW
    Email: dengchuangwu@gmail.com
    """
    time = None
    lev = None
    lat = None
    lon = None

    _rng = None
    dims = None

    def __init__(self, fnames: str, engine: str = "netcdf",
                 group: str = None, concat_dim: str = "time", **kwargs):

        engines = ["netcdf", "xarray"]
        if engine not in engines:
            raise ValueError(
                "unrecognized engine for open_dataset: {}\n"
                "must be one of: {}".format(engine, engines)
            )

        fname_ls = glob(fnames)
        if engine == "xarray":
            self.data_obj = open_mfdataset(fname_ls, group=group,
                                           concat_dim=concat_dim,
                                           combine='by_coords', **kwargs)
            engine = 0
        elif engine == "netcdf":
            if len(fname_ls) == 1:
                self.data_obj = Dataset(fname_ls[0], **kwargs)
            else:
                self.data_obj = MFDataset(fname_ls, aggdim=concat_dim,
                                          **kwargs)
                if hasattr(self.data_obj['time'], 'calendar'):
                    cal = self.data_obj['time'].calendar
                else:
                    cal = 'standard'
                self._orig_time = MFTime(self.data_obj['time'], calendar=cal)
            engine = 1

        self.engine = engine

    def set_rng(self, time_rng: tuple = None, lev_rng: tuple = None,
                lat_rng: tuple = None, lon_rng: tuple = None):
        """Set the value range.

        :param time_rng: class:tuple, time range
        :param lev_rng: class:tuple, level or height range
        :param lat_rng: class:tuple, latitude range
        :param lon_rng: class:tuple, longitude range
        :return: class: list, valid limited range, which is prepared for
        extracting the values of specified variable
        ------------------------------------------------------------------
        Examples:

        """
        self._rng = []
        self.dims = []
        dims = get_dims(self.data_obj)
        for dim in dims:
            if dim.upper() in ['TIME', 'TIMES']:
                orig_time_exist = hasattr(self, '_orig_time')
                if orig_time_exist:
                    trgt_time_rng = cnv_ls2slice(
                        self._get_multi_rng(var=self._orig_time,
                                            boundary=time_rng, pos=0))
                    self.time = self._engine_sel(
                        self._orig_time, trgt_time_rng)
                else:
                    trgt_time_rng = cnv_ls2slice(
                        self._get_multi_rng(var=self.data_obj[dim],
                                            boundary=time_rng, pos=0))
                    self.time = self._engine_sel(self.data_obj[dim],
                                                 trgt_time_rng)
                self._rng.append(trgt_time_rng)

                if self.engine:
                    if orig_time_exist:
                        time = get_time(self._orig_time)
                    else:
                        time = get_time(self.data_obj[dim])
                    self.time.values = time[trgt_time_rng]
                self.dims.append(dim)
            elif dim.upper() in ['LEV', 'LEVEL', 'LEVELS', 'EXPVER']:
                lev_trgt_rng = cnv_ls2slice(
                    self._get_multi_rng(var=self.data_obj[dim],
                                        boundary=lev_rng, pos=1))
                self._rng.append(lev_trgt_rng)
                self.lev = self._engine_sel(self.data_obj[dim], lev_trgt_rng)
                self.dims.append(dim)
            elif dim.upper() in ['LAT', 'LATITUDE', 'LATITUDES']:
                lat_trgt_rng = cnv_ls2slice(
                    self._get_multi_rng(var=self.data_obj[dim],
                                        boundary=lat_rng, pos=2))
                self._rng.append(lat_trgt_rng)
                self.lat = self._engine_sel(self.data_obj[dim], lat_trgt_rng)
                self.dims.append(dim)
            elif dim.upper() in ['LON', 'LONGITUDE', 'LONGITUDES']:
                lon_trgt_rng = cnv_ls2slice(
                    self._get_multi_rng(var=self.data_obj[dim],
                                        boundary=lon_rng, pos=3))
                self._rng.append(lon_trgt_rng)
                self.lon = self._engine_sel(self.data_obj[dim], lon_trgt_rng)
                self.dims.append(dim)
        return self._rng

    def get_var(self, var_name: str):
        """Extract specified variable values in a limited area.

        :param var_name: class:str, the name of variable
        :return: class:xarray.Dataset, class:xarray.Variable, dataset with
        attributes
        ------------------------------------------------------------------
        Examples:

        """
        var = self.data_obj[var_name]
        self._rng, self.dims = adjust_dim(self._rng, self.dims, get_dims(var))
        rslt = self._engine_sel(var, tuple(self._rng))
        return rslt.squeeze()

    def _engine_sel(self, var_obj, rng: tuple or list):
        if self.engine:
            rslt = DataArray(data=var_obj[rng], dims=get_dims(var_obj),
                             attrs=var_obj.__dict__)
        else:
            rslt = var_obj[rng]
        return rslt

    @is_none
    def _get_multi_rng(self, **kwargs):
        rslt = []
        if np.size(np.shape(kwargs['boundary'])) > 1:
            for bdry in kwargs['boundary']:
                if kwargs['pos'] == 1:
                    rslt.extend(
                        self._get_lev_rng(var=kwargs['var'], boundary=bdry))
                elif kwargs['pos'] == 2:
                    rslt.extend(
                        self._get_lat_rng(var=kwargs['var'], boundary=bdry))
                elif kwargs['pos'] == 3:
                    rslt.extend(
                        self._get_lon_rng(var=kwargs['var'], boundary=bdry))
                else:
                    rslt.extend(
                        self._get_time_rng(var=kwargs['var'], boundary=bdry))

        else:
            if kwargs['pos'] == 1:
                return self._get_lev_rng(var=kwargs['var'],
                                         boundary=kwargs['boundary'])
            elif kwargs['pos'] == 2:
                return self._get_lat_rng(var=kwargs['var'],
                                         boundary=kwargs['boundary'])
            elif kwargs['pos'] == 3:
                return self._get_lon_rng(var=kwargs['var'],
                                         boundary=kwargs['boundary'])
            else:
                return self._get_time_rng(var=kwargs['var'],
                                          boundary=kwargs['boundary'])
        return rslt

    def _get_lon_rng(self, **kwargs):
        lon = kwargs['var'][:]
        min_bdry = kwargs['boundary'][0]
        max_bdry = kwargs['boundary'][-1]
        if min_bdry < -180 or max_bdry > 180:
            raise ValueError("Longitude range is [-180,180]")

        if max_bdry < min_bdry:
            raise ValueError("In the setting of longitude range, the value "
                             "on the left needs to be smaller than the value "
                             "on the right.")

        if not len(np.where(lon < 0)[0]):
            if min_bdry < 0:
                min_bdry = 360 + min_bdry
            if max_bdry < 0:
                max_bdry = 360 + max_bdry

        ind = np.where(lon >= min_bdry)[0]
        ind2 = np.where(lon <= max_bdry)[0]
        rslt = extra_same_elem(ind, ind2)
        if not len(rslt):
            raise ValueError("Due to the longitude resolution, the "
                             "longitude range you set is too fine, "
                             "please expand your setting range.")
        return rslt

    def _get_lat_rng(self, **kwargs):
        lat = kwargs['var'][:]
        min_bdry = kwargs['boundary'][0]
        max_bdry = kwargs['boundary'][-1]
        if min_bdry < -90 or max_bdry > 90:
            raise ValueError("Longitude range is [-90,90]")
        if max_bdry < min_bdry:
            raise ValueError("In the latitude range setting, the value "
                             "on the left needs to be smaller than "
                             "the value on the right.")

        ind = np.where(lat >= min_bdry)[0]
        ind2 = np.where(lat <= max_bdry)[0]
        rslt = extra_same_elem(ind, ind2)
        if not len(rslt):
            raise ValueError("Due to latitude resolution, the "
                             "latitude range you set is too fine, "
                             "please expand your setting range.")
        return rslt

    def _get_lev_rng(self, **kwargs):
        lev = kwargs['var'][:]
        min_bdry = kwargs['boundary'][0]
        max_bdry = kwargs['boundary'][-1]

        if max_bdry < min_bdry:
            raise ValueError("In the height range setting, the value "
                             "on the left needs to be smaller than "
                             "the value on the right.")

        ind = np.where(lev >= min_bdry)[0]
        ind2 = np.where(lev <= max_bdry)[0]
        rslt = extra_same_elem(ind, ind2)
        if not len(rslt):
            raise ValueError("Due to the height resolution, the height range "
                             "you set is too fine, please expand your setting "
                             "range.")
        return rslt

    def _get_time_rng(self, **kwargs):
        min_bdry = kwargs['boundary'][0]
        max_bdry = kwargs['boundary'][-1]
        var = kwargs['var']

        min_bdry = datetime.strptime(min_bdry, '%Y-%m-%d %H:%M:%S')
        max_bdry = datetime.strptime(max_bdry, '%Y-%m-%d %H:%M:%S')

        if max_bdry < min_bdry:
            raise ValueError("In the time setting, the value on the left "
                             "precedes the value on the right.")
        if self.engine:
            time = get_time(var)
            ind = np.where(time >= min_bdry)[0]
            ind2 = np.where(time <= max_bdry)[0]
        else:
            min_bdry = np.datetime64(min_bdry)
            max_bdry = np.datetime64(max_bdry)
            ind = np.where(var >= min_bdry)[0]
            ind2 = np.where(var <= max_bdry)[0]
        rslt = extra_same_elem(ind, ind2)

        if not len(rslt):
            raise ValueError("Due to time resolution, the time range you set "
                             "is too fine, please expand your setting range.")
        return rslt


class HdfData(object):
    """HDF file reading

    Created date: 2020-06-05 12:54:13
    Last modified date: 2020-06-05 16:09:26
    Contributor: D.CW
    Email: dengchuangwu@gmail.com
    """
    time = None
    lev = None
    lat = None
    lon = None

    def __init__(self, fnames: str, group: str = "Merged",
                 concat_dim: str = "time", engine: str = 'xarray', **kwargs):
        engines = ["netcdf", "xarray"]
        if engine not in engines:
            raise ValueError(
                "unrecognized engine for open_dataset: {}\n"
                "must be one of: {}".format(engine, engines)
            )

        if engine == "xarray":
            self.nc_obj = NcData(fnames, group=group, concat_dim=concat_dim,
                                 engine=engine, **kwargs)
        elif engine == "netcdf":
            fname_ls = glob(fnames)
            xd = open_mfdataset(fname_ls, group=group,
                                concat_dim=concat_dim,
                                combine="by_coords", **kwargs)
            self.tmp_fname = ''.join(
                [datetime.now().strftime("%Y%m%d%H%M%S%f"), '.nc'])
            xd.to_netcdf(self.tmp_fname)
            self.nc_obj = NcData(self.tmp_fname, concat_dim=concat_dim,
                                 **kwargs)

    def set_rng(self, time_rng: tuple = None, lev_rng: tuple = None,
                lat_rng: tuple = None, lon_rng: tuple = None):
        """Set the value range.

        :param time_rng: class:tuple, time range
        :param lev_rng: class:tuple, level or height range
        :param lat_rng: class:tuple, latitude range
        :param lon_rng: class:tuple, longitude range
        :return: class: list, valid limited range, which is prepared for
        extracting the values of specified variable
        ------------------------------------------------------------------
        Examples:

        """
        rng = self.nc_obj.set_rng(time_rng=time_rng, lev_rng=lev_rng,
                                  lat_rng=lat_rng, lon_rng=lon_rng)
        self.time = self.nc_obj.time
        self.lev = self.nc_obj.lev
        self.lat = self.nc_obj.lat
        self.lon = self.nc_obj.lon
        return rng

    def get_var(self, var_name: str):
        """Extract specified variable values in a limited area.

        :param var_name: class:str, the name of variable
        :return: class:xarray.Dataset, class:xarray.Variable, dataset with
        attributes
        ------------------------------------------------------------------
        Examples:

        """
        return self.nc_obj.get_var(var_name)

    def __del__(self):
        if self.nc_obj.engine:
            self.nc_obj.data_obj.close()
            remove(self.tmp_fname)

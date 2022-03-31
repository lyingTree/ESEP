# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : Changjiang_estuary
                                                                              
                    File Name : analysis.py

                   Start Date : 2022-03-28 01:42

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

模型快速分析模块

-------------------------------------------------------------------------------
"""

import numpy as np

from ESEP.esep.physics.base import speed
from ESEP.esep.plot.horizonal_distribution import HorizontalDistribution
from ESEP.esep.reader.unstructured import FvcomReader
from ESEP.esep.utils import interpolate
from ESEP.esep.utils.hpc import SegmentOperate
from ESEP.esep.utils.timer import TimeUtil
from ESEP.esep.utils.unstructured import nodes2elems, construct_mask


class Analysis:
    fvcom_ls = []
    case_ls = []
    fvcom_mask = None

    def __init__(self, cases, time_period=None, lon_rng=None, lat_rng=None, z=None, interp_space=0.1):
        for case_name, fp_ls in cases.items():
            self.case_ls.append(cases)
            self.fvcom_ls.append(FvcomReader(fp_ls))

        self.time_period = time_period
        self.lon_rng = lon_rng
        self.lat_rng = lat_rng
        self.z = z
        self.interp_space = interp_space

    def _horizontal_distribution_extract_data(self, var_name):
        lon_grid, lat_grid = None, None
        for fvcom in self.fvcom_ls:
            fvcom.variables([var_name])
            lonc = fvcom.lonc[:]
            latc = fvcom.latc[:]
            cell_idx = np.where(
                np.logical_and(np.logical_and(lonc <= self.lon_rng[-1] + 0.1, lonc >= self.lon_rng[0] - 0.1),
                               np.logical_and(latc <= self.lat_rng[-1] + 0.1, latc >= self.lat_rng[0] - 0.1)))[0]
            var_data = getattr(fvcom, var_name)[:]

            # 确保var为二维数据，(time，nele)
            dims = getattr(fvcom, var_name).dimensions
            if 'node' in dims:
                var_data = nodes2elems(var_data, fvcom.tri)
            var_data = var_data[..., cell_idx]

            if len(dims) == 3:
                # TODO: 这里的 z 需要确定用index，还是气压，还是什么来确定
                if self.z is None:
                    var_data = np.nanmean(var_data, axis=1)
                elif isinstance(self.z, list):
                    var_data = np.nanmean(var_data[:, self.z, :], axis=1)
                else:
                    var_data = var_data[:, self.z, :]

            if len(np.shape(var_data)) < 2:
                var_data = np.expand_dims(var_data, axis=1)

            if self.time_period is not None and 'time' in dims:
                time_idx, _ = TimeUtil().extract_common_time_idx(fvcom.time_bj, self.time_period)
                var_data = var_data[time_idx]

            if len(np.shape(var_data)) < 2:
                var_data = np.expand_dims(var_data, axis=0)

            lon = fvcom.lonc[cell_idx].data
            lat = fvcom.latc[cell_idx].data
            loc_range = [self.lon_rng[0], self.lon_rng[-1], self.lat_rng[0], self.lat_rng[-1]]
            args = (lon, lat, loc_range, self.interp_space, 'linear')
            tmp = SegmentOperate(var_data, 100, interpolate.station2grid, 1, False, *args).value
            lon_grid, lat_grid = tmp[0, :2]
            if self.fvcom_mask is None or np.shape(self.fvcom_mask) != np.shape(lon_grid):
                self.fvcom_mask, self.domain_polygon = construct_mask(fvcom.lon, fvcom.lat, fvcom.tri, lon_grid,
                                                                      lat_grid)
            interp_var_data = tmp[:, 2]
            interp_var_data[:, self.fvcom_mask] = np.nan
        return lon_grid, lat_grid, interp_var_data

    def domain(self, level=None, with_edge=True, with_depth=False, add_features_func=None, *args, **kwargs):
        self.fvcom.variables(['h'])
        tri = np.transpose(self.fvcom.tri[:]).T
        depth = nodes2elems(np.squeeze(self.fvcom.h[:]), tri)
        cb_label = '水深[m]'
        kwargs['edgecolor'] = 'yellow'
        if not with_depth:
            depth[:] = np.nan
            cb_label = None
            kwargs['edgecolor'] = 'black'
        if not with_edge:
            kwargs.pop('edgecolor')

        save_path = kwargs['save_path'] if 'save_path' in kwargs else self.save_dir.joinpath('网格')
        kwargs.pop('save_path') if 'save_path' in kwargs else None

        draw_manager = HorizontalDistribution(self.fvcom.lon, self.fvcom.lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        if level is None:
            level = depth
        draw_manager.tripcolor(tri, depth, level, self.lon_rng, self.lat_rng, save_path, cb_label, *args, **kwargs)

    def cum_erosion(self, level=np.linspace(-1, 1, 51), add_features_func=None, *args, **kwargs):
        lon, lat, data = self._horizontal_distribution_extract_data('bot_dthck')
        data = np.nansum(data, axis=0)
        draw_manager = HorizontalDistribution(lon, lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.contourf(data, level, self.lon_rng, self.lat_rng, self.save_dir.joinpath('冲淤累积图'), '冲淤[m]',
                              *args, **kwargs)

    def current(self, scale=40, add_features_func=None, *args, **kwargs):
        lon, lat, u = self._horizontal_distribution_extract_data('u')
        _, _, v = self._horizontal_distribution_extract_data('v')
        u, v = np.nanmean(u, axis=0), np.nanmean(v, axis=0)

        draw_manager = HorizontalDistribution(lon, lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.quiver(u, v, scale, self.lon_rng, self.lat_rng, self.save_dir.joinpath('流场水平分布图'), qk_u=1, *args,
                            **kwargs)

    def speed(self, level=np.linspace(0, 1, 51), add_features_func=None, *args, **kwargs):
        lon, lat, u = self._horizontal_distribution_extract_data('u')
        _, _, v = self._horizontal_distribution_extract_data('v')
        u, v = np.nanmean(u, axis=0), np.nanmean(v, axis=0)
        cs = speed(u, v)

        draw_manager = HorizontalDistribution(lon, lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.contourf(cs, level, self.lon_rng, self.lat_rng, self.save_dir.joinpath('流速水平分布图'), '流速[m/s]',
                              *args, **kwargs)

    def ssc(self, ssc_name='ssc0', level=np.linspace(0, 3, 51), add_features_func=None, *args, **kwargs):
        lon, lat, data = self._horizontal_distribution_extract_data(ssc_name)
        draw_manager = HorizontalDistribution(lon, lat)
        data = np.nanmean(data, axis=0)

        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.contourf(data, level, self.lon_rng, self.lat_rng, self.save_dir.joinpath('含沙量水平分布图'), '含沙量[g/l]',
                              *args, **kwargs)

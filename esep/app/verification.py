# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : verification.py

                   Start Date : 2022-03-24 00:40

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

模型快速验证模块

-------------------------------------------------------------------------------
"""
from itertools import product

import numpy as np

from ESEP.esep.physics.base import speed
from ESEP.esep.plot.horizonal_distribution import HorizontalDistribution, HorizDistAnimation
from ESEP.esep.plot.time_series import TimeSeries
from ESEP.esep.reader.get_obs_data import get_obs_data, get_tide_station_info, get_obs_tide_data, get_obs_data_sediment
from ESEP.esep.reader.unstructured import FvcomReader
from ESEP.esep.utils import interpolate
from ESEP.esep.utils.hpc import SegmentOperate
from ESEP.esep.utils.spatial import find_nearest, CoordinateTransform
from ESEP.esep.utils.timer import TimeUtil
from ESEP.esep.utils.unstructured import nodes2elems, construct_mask


class Verification:
    def __init__(self, case_name, save_dir, fp_ls):
        self.case_name = case_name
        self.fvcom = FvcomReader(fp_ls)
        self.save_dir = save_dir.joinpath(self.case_name)

        self.save_dir.mkdir(parents=True, exist_ok=True)


class TimeSeriesVerify(Verification):
    def __init__(self, case_name, save_dir, fp_ls, neap_tide, spring_tide):
        super(TimeSeriesVerify, self).__init__(case_name, save_dir, fp_ls)
        self.neap_tide = neap_tide
        self.spring_tide = spring_tide

    def time_series_single_point_current(self, obs_coordinates):
        level_num = self.fvcom.ds.dimensions['siglev'].size
        elevation_levels = {
            'surface': 0,
            'middle': int(level_num / 2),
            'bottom': -1,
            'verticalMean': slice(level_num),
        }
        obs_fp = './OBS_DATA/HangZhouWan_C_5.xls'
        self.fvcom.variables(['u', 'v'])
        station_dict = find_nearest(obs_coordinates, (self.fvcom.lonc, self.fvcom.latc),
                                    (self.fvcom.lon, self.fvcom.lat))

        for sta_info, lev_info in product(station_dict.items(), elevation_levels.items()):
            station_name, sta_val = sta_info
            lev_name, lev_idx = lev_info
            draw_manager = TimeSeries(station_name)
            tmp_dir = self.save_dir.joinpath('current', '{0}_{1}'.format(station_name, lev_name))
            tmp_dir.mkdir(parents=True, exist_ok=True)

            for tt_idx, tt_name, time_seg in zip([0, 1], ['小潮', '大潮'], [self.neap_tide, self.spring_tide]):
                obs_cs_data, obs_dir_data, obs_time, obs_depth = get_obs_data(obs_fp, station_name, lev_name,
                                                                              merge=False, tt_idx=tt_idx)
                cell_idx = sta_val['cell_id'][0]
                if lev_name == 'verticalMean':
                    ucur_data = np.nanmean(self.fvcom.u[:, lev_idx, cell_idx], axis=-1)
                    vcur_data = np.nanmean(self.fvcom.v[:, lev_idx, cell_idx], axis=-1)
                else:
                    ucur_data = self.fvcom.u[:, lev_idx, cell_idx]
                    vcur_data = self.fvcom.v[:, lev_idx, cell_idx]
                model_dir, model_cs = CoordinateTransform().uv2ocean(ucur_data, vcur_data)
                obs_idx, model_idx = TimeUtil().extract_common_time_idx(obs_time, self.fvcom.time_bj, time_seg[0],
                                                                        time_seg[1])
                obs = (obs_cs_data[obs_idx], obs_dir_data[obs_idx])
                model = (model_cs[model_idx], model_dir[model_idx])

                draw_manager.cs_dir(obs_time[obs_idx], self.fvcom.time_bj[model_idx], obs, model,
                                    tmp_dir.joinpath(tt_name))

    def time_series_single_point_depth(self):
        obs_coordinate, obs_fp = get_tide_station_info('./OBS_DATA/1 、潮位/')
        self.fvcom.variables(['h', 'zeta'])
        station_dict = find_nearest(obs_coordinate, cell_lonlat=(self.fvcom.lonc, self.fvcom.latc),
                                    node_lonlat=(self.fvcom.lon, self.fvcom.lat))
        # --------------------------------------------------------------------------------------------------------------
        for j, sta_info in enumerate(station_dict.items()):
            station_name, sta_val = sta_info
            draw_manager = TimeSeries(station_name)
            tmp_dir = self.save_dir.joinpath('water_level', '{:}'.format(station_name))
            tmp_dir.mkdir(parents=True, exist_ok=True)

            node_idx = sta_val['node_id'][0]
            model_depth = self.fvcom.h[node_idx] + self.fvcom.zeta[:, node_idx]
            obs_time, obs_depth = get_obs_tide_data(obs_fp[j])
            for tt_name, time_seg in zip(['小潮', '大潮'], [self.neap_tide, self.spring_tide]):
                obs_idx, model_idx = TimeUtil().extract_common_time_idx(obs_time, self.fvcom.time_bj, time_seg[0],
                                                                        time_seg[1])
                draw_manager.depth(obs_time[obs_idx], self.fvcom.time_bj[model_idx], obs_depth[obs_idx],
                                   model_depth[model_idx], tmp_dir.joinpath(tt_name))

    def time_series_single_point_sediment(self, obs_coordinates, sed_name='ssc0'):
        station_name_mapping = {
            '1#': 'C1',
            '2#': 'C2',
            '3#': 'C3',
            '4#': 'C4',
            '5#': 'C5',
            '6#': 'C6',
            '7#': 'C7',
        }
        lev_name = 'verticalMean'
        obs_fp = './OBS_DATA/3、含沙量/吴泾电厂等容量绿色煤电异地新建工程含沙量观测记录报表.xls'
        # --------------------------------------------------------------------------------------------------------------
        self.fvcom.variables([sed_name])
        station_dict = find_nearest(obs_coordinates, cell_lonlat=(self.fvcom.lonc, self.fvcom.latc),
                                    node_lonlat=(self.fvcom.lon, self.fvcom.lat))

        # --------------------------------------------------------------------------------------------------------------
        for station_name, sta_val in station_dict.items():
            name = station_name_mapping[station_name]
            tmp_dir = self.save_dir.joinpath('sediment', '{0}_{1}'.format(name, lev_name))
            tmp_dir.mkdir(parents=True, exist_ok=True)
            draw_manager = TimeSeries(name)

            for tt_idx, tt_name, time_seg in zip([0, 1], ['小潮', '大潮'], [self.neap_tide, self.spring_tide]):
                obs_data, obs_time, obs_depth = get_obs_data_sediment(obs_fp, station_name, lev_name, merge=False,
                                                                      tt_idx=tt_idx)

                model_data = np.nanmean(getattr(self.fvcom, sed_name)[:, :, sta_val['node_id'][0]], axis=-1)
                obs_idx, model_idx = TimeUtil().extract_common_time_idx(obs_time, self.fvcom.time_bj, time_seg[0],
                                                                        time_seg[1])
                draw_manager.sediment(obs_time[obs_idx], self.fvcom.time_bj[model_idx], obs_data[obs_idx],
                                      model_data[model_idx], tmp_dir.joinpath(tt_name))


class HorizDistVerify(Verification):
    fvcom_mask = None

    def __init__(self, case_name, save_dir, fp_ls, time_period=None, lon_rng=None, lat_rng=None, z=None,
                 interp_space=0.1):
        super(HorizDistVerify, self).__init__(case_name, save_dir, fp_ls)
        self.time_period = time_period
        self.lon_rng = lon_rng
        self.lat_rng = lat_rng
        self.z = z
        self.interp_space = interp_space

    def _horizontal_distribution_extract_data(self, var_name):
        self.fvcom.variables([var_name])
        lonc = self.fvcom.lonc[:]
        latc = self.fvcom.latc[:]
        cell_idx = np.where(
            np.logical_and(np.logical_and(lonc <= self.lon_rng[-1] + 0.1, lonc >= self.lon_rng[0] - 0.1),
                           np.logical_and(latc <= self.lat_rng[-1] + 0.1, latc >= self.lat_rng[0] - 0.1)))[0]
        var_data = getattr(self.fvcom, var_name)[:]

        # 确保var为二维数据，(time，nele)
        dims = getattr(self.fvcom, var_name).dimensions
        if 'node' in dims:
            var_data = nodes2elems(var_data, self.fvcom.tri)
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
            time_idx, _ = TimeUtil().extract_common_time_idx(self.fvcom.time_bj, self.time_period)
            var_data = var_data[time_idx]

        if len(np.shape(var_data)) < 2:
            var_data = np.expand_dims(var_data, axis=0)

        lon = self.fvcom.lonc[cell_idx].data
        lat = self.fvcom.latc[cell_idx].data
        loc_range = [self.lon_rng[0], self.lon_rng[-1], self.lat_rng[0], self.lat_rng[-1]]
        args = (lon, lat, loc_range, self.interp_space, 'linear')
        tmp = SegmentOperate(var_data, 100, interpolate.station2grid, 1, False, *args).value
        lon_grid, lat_grid = tmp[0, :2]
        if self.fvcom_mask is None or np.shape(self.fvcom_mask) != np.shape(lon_grid):
            self.fvcom_mask, self.domain_polygon = construct_mask(self.fvcom.lon, self.fvcom.lat, self.fvcom.tri,
                                                                  lon_grid, lat_grid)
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


class TimeSeriesAniVerify(TimeSeriesVerify):
    def animation_cum_erosion(self):
        pass

    def animation_current(self):
        pass

    def animation_speed(self):
        pass

    def animation_ssc(self):
        pass


class HorizDistAniVerify(HorizDistVerify):
    def cum_erosion(self, level=np.linspace(-1, 1, 51), add_features_func=None, *args, **kwargs):
        lon, lat, data = self._horizontal_distribution_extract_data('bot_dthck')
        tmp = data
        for i, val in enumerate(tmp):
            data[i] = np.nansum(tmp[:i + 1], axis=0)
        draw_manager = HorizDistAnimation(lon, lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.contourf(data, level, self.lon_rng, self.lat_rng, self.save_dir.joinpath('冲淤累积变化图'), '冲淤[m]',
                              *args, **kwargs)

    def current(self, scale=40, qk_u=1, add_features_func=None, *args, **kwargs):
        lon, lat, u = self._horizontal_distribution_extract_data('u')
        _, _, v = self._horizontal_distribution_extract_data('v')
        draw_manager = HorizDistAnimation(lon, lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.quiver(u, v, scale, self.lon_rng, self.lat_rng, self.save_dir.joinpath('流场平面变化图'), qk_u, *args,
                            **kwargs)

    def speed(self, level=np.linspace(0, 1, 51), add_features_func=None, *args, **kwargs):
        lon, lat, u = self._horizontal_distribution_extract_data('u')
        _, _, v = self._horizontal_distribution_extract_data('v')
        cs = speed(u, v)

        draw_manager = HorizDistAnimation(lon, lat)
        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.contourf(cs, level, self.lon_rng, self.lat_rng, self.save_dir.joinpath('流速平面变化图'), '流速[m/s]',
                              *args, **kwargs)

    def ssc(self, ssc_name='ssc0', level=np.linspace(0, 3, 51), add_features_func=None, *args, **kwargs):
        lon, lat, data = self._horizontal_distribution_extract_data(ssc_name)
        draw_manager = HorizDistAnimation(lon, lat)

        if add_features_func is not None:
            HorizontalDistribution.add_features = add_features_func
        draw_manager.contourf(data, level, self.lon_rng, self.lat_rng, self.save_dir.joinpath('含沙量平面变化图'), '含沙量[g/l]',
                              *args, **kwargs)

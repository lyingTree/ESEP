# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : horizonal_distribution.py
                      
                   Start Date : 2021-08-21 10:10
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
Introduction:

水平分布图通用方法集
                                                                              
--------------------------------------------------------------------------------
"""

from abc import abstractmethod, ABC
from datetime import datetime
from functools import partial

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
from cartopy.mpl.gridliner import LongitudeFormatter, LatitudeFormatter
from matplotlib.animation import FuncAnimation

from ESEP.esep.plot import plot as _plt
from .base import tripcolor, cbar_kw_default, tricontourf
from .color_bar import adjust_cbar_position
from .ticks import adjust_cbar_tick


class HorizontalDistribution:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat
        self.fig, self.ax = plt.subplots(1, 1, figsize=(12, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
        self.fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.05)
        self.fig_fmt = 'png'

    def _common(self, xticks, yticks, extent=None, **kwargs):
        tk_kwargs = {}
        label_kwargs = {}
        kwargs.setdefault('face_color', 'white')
        if 'ticks' in kwargs:
            tk_kwargs = kwargs['ticks']
            kwargs.pop('ticks')

        tk_kwargs.setdefault('labelsize', 12)
        tk_kwargs.setdefault('direction', 'in')
        tk_kwargs.setdefault('length', 5)
        tk_kwargs.setdefault('width', 1.5)

        if 'label' in kwargs:
            label_kwargs = kwargs['label']
            kwargs.pop('label')
        label_kwargs.setdefault('fontsize', 18)

        if self.add_features.__code__.co_argcount > 1:
            self.add_features()
        if extent is not None:
            self.ax.set_extent(extent)
        self.ax.set_xticks(xticks)
        self.ax.set_yticks(yticks)
        self.ax.xaxis.set_major_formatter(LongitudeFormatter())
        self.ax.yaxis.set_major_formatter(LatitudeFormatter())
        self.ax.tick_params(**tk_kwargs)
        self.ax.yaxis.set_zorder(999)
        self.ax.xaxis.set_zorder(999)
        self.ax.set_xlabel('经度', **label_kwargs)
        self.ax.set_ylabel('纬度', **label_kwargs)
        self.ax.patch.set_facecolor(kwargs.get('face_color'))
        for spline in self.ax.spines:
            self.ax.spines[spline].set_linewidth(1.5)
            self.ax.spines[spline].set_zorder(999)

    def _save_fig(self, save_path):
        self.fig.savefig(save_path, fomart=self.fig_fmt, bbox_inches='tight', pad_inches=0.1)
        self.ax.cla()

    def _add_color_bar(self, handle, level, label, **kwargs):
        tk_kwargs = {}
        label_kwargs = {}

        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('extend', 'both')
        kwargs.setdefault('cax', adjust_cbar_position(self.fig, [0.13, 0.00, 0.75, 0.03]))
        if 'ticks' in kwargs:
            tk_kwargs = kwargs['ticks']
            kwargs.pop('ticks')

        tk_kwargs.setdefault('labelsize', 12)
        tk_kwargs.setdefault('direction', 'in')
        tk_kwargs.setdefault('length', 5)
        tk_kwargs.setdefault('width', 1.5)

        if 'label' in kwargs:
            label_kwargs = kwargs['label']
            kwargs.pop('label')
        label_kwargs.setdefault('fontsize', 15)

        cbar = self.fig.colorbar(handle, **kwargs)
        cbar.ax.tick_params(**tk_kwargs)
        cbar.ax.set_xlabel(label, **label_kwargs)
        adjust_cbar_tick(cbar, level)

    def contourf(self, data, level, lon_rng, lat_rng, save_path, cb_label=None, *args, **kwargs):
        kwargs.setdefault('extend', 'both')
        kwargs.setdefault('cmap', 'bwr')
        cb_kwargs = {}
        if 'colorbar' in kwargs:
            cb_kwargs = kwargs.get('colorbar')
            kwargs.pop('colorbar')

        common_kwargs = {}
        if 'common' in kwargs:
            common_kwargs = kwargs.get('common')
            kwargs.pop('common')
        handle = self.ax.contourf(self.lon, self.lat, data, level, *args, **kwargs)
        extent = [lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]]
        self._common(lon_rng, lat_rng, extent, **common_kwargs)
        if cb_label is not None:
            self._add_color_bar(handle, level, cb_label, **cb_kwargs)
        if save_path is not None:
            self._save_fig(save_path)
            return None
        return handle

    def quiver(self, u, v, scale, lon_rng, lat_rng, save_path, *args, **kwargs):
        kwargs.setdefault('width', 'black')
        kwargs.setdefault('headwidth', 'black')
        kwargs.setdefault('headlength', 'black')
        kwargs.setdefault('color', 'black')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('animated', True)

        qk_labelpos = kwargs.get('labelpos')
        qk_fontproperties = kwargs.get('fontproperties')
        qk_labelpos = 'E' if qk_labelpos is None else qk_labelpos
        qk_fontproperties = dict(size=15) if qk_fontproperties is None else qk_fontproperties

        kwargs.pop('labelpos') if 'labelpos' in kwargs else None
        kwargs.pop('fontproperties') if 'fontproperties' in kwargs else None

        common_kwargs = {}
        if 'common' in kwargs:
            common_kwargs = kwargs.get('common')
            kwargs.pop('common')
        handle = self.ax.quiver(self.lon, self.lat, u, v, scale=scale, *args, **kwargs)

        kwargs.get('labelpos')
        # TODO: 自动识别调整 qk_x, qk_y
        qk_x, qk_y = 0.8, 0.8
        self.ax.quiverkey(handle, qk_x, qk_y, 1, '1m/s', labelpos=qk_labelpos, coordinates='figure',
                          fontproperties=qk_fontproperties)

        extent = [lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]]
        self._common(lon_rng, lat_rng, extent, **common_kwargs)
        if save_path is not None:
            self._save_fig(save_path)
            return None
        return handle

    @abstractmethod
    def add_features(self):
        pass


class HorizDistAnimation(HorizontalDistribution, ABC):
    def __init__(self, lon, lat):
        super(HorizDistAnimation, self).__init__(lon, lat)
        self.fig.set_size_inches(12, 12)

    def contourf(self, data, level, lon_rng, lat_rng, save_path, cb_label=None, *args, **kwargs):
        init_func = partial(self.init, data=data[0], level=level, lon_rng=lon_rng, lat_rng=lat_rng, cb_label=cb_label,
                            *args, **kwargs)
        update_func = partial(self.update, lon_rng=lon_rng, lat_rng=lat_rng, level=level, *args, **kwargs)
        animation = FuncAnimation(fig=self.fig, func=update_func, frames=data[1:], init_func=init_func,
                                  save_count=np.shape(data)[0], interval=200, blit=False)

        animation.save('.'.join([str(save_path), 'gif']), writer='pillow')

    def init(self, data, level, lon_rng, lat_rng, cb_label, *args, **kwargs):
        return super(HorizDistAnimation, self).contourf(data, level, lon_rng, lat_rng, save_path=None,
                                                        cb_label=cb_label, *args, **kwargs)

    def update(self, data, lon_rng, lat_rng, level, *args, **kwargs):
        return super(HorizDistAnimation, self).contourf(data, level, lon_rng, lat_rng, save_path=None, *args, **kwargs)


def plot(filepath, save_path, var_name, time, lev=None, **kwargs):
    lon, lat, tri, data, cbar_xlabel = _data_read(filepath, var_name, time, lev)
    fig, ax, cbar = _h_dist_tripcolor(lon, lat, tri, data, cbar_xlabel=cbar_xlabel, **kwargs)

    _plt.save_fig(fig, save_path, **kwargs.setdefault('save_fig_kwargs', dict()))
    return fig, ax, cbar


def plot2(filepath, save_path, var_name, time, lev=None, **kwargs):
    lon, lat, tri, data, cbar_xlabel = _data_read2(filepath, var_name, time, lev)
    fig, ax, cbar = _h_dist(lon, lat, tri, data, cbar_xlabel=cbar_xlabel, **kwargs)

    _plt.save_fig(fig, save_path, **kwargs.setdefault('save_fig_kwargs', dict()))
    return fig, ax, cbar


def _data_read(filepath, var_name, time_str, lev):
    ds = nc.Dataset(filepath)
    ds_vars = ds.variables
    lon = ds_vars.get('lon')[:]
    lat = ds_vars.get('lat')[:]
    tri = np.transpose(ds_vars.get('nv')[:]) - 1
    time_idx = _time_proc(ds_vars, time_str)

    data = ds_vars.get(var_name)
    cbar_xlabel = ''.join([data.long_name, '[', data.units, ']'])
    if len(data.dimensions) == 2:
        data = data[time_idx, :]
    else:
        data = data[time_idx, lev, :]
    return lon, lat, tri, data, cbar_xlabel


def _data_read2(filepath, var_name, time_str, lev):
    ds = nc.Dataset(filepath)
    ds_vars = ds.variables
    lon = ds_vars.get('lonc')[:]
    lat = ds_vars.get('latc')[:]
    tri = np.transpose(ds_vars.get('nv')[:]) - 1
    time_idx = _time_proc(ds_vars, time_str)

    data = ds_vars.get(var_name)
    cbar_xlabel = ''.join([data.long_name, '[', data.units, ']'])
    if len(data.dimensions) == 2:
        data = data[time_idx, :]
    else:
        data = data[time_idx, lev, :]
    return lon, lat, tri, data, cbar_xlabel


def _time_proc(ds_vars, time_str):
    time = [datetime.strptime(x.tobytes().decode(), '%Y-%m-%dT%H:%M:%S.%f') for x in ds_vars.get('Times')[:]]
    time_sel = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    return time.index(time_sel)


def _h_dist(lon, lat, tri, data, cbar_xlabel=None, cbar_rng=None, cbar_position=None, figure_kwargs=None,
            subplot_kwargs=None, cbar_xlabel_kw: dict = None, cbar_tick_kw=None, **kwargs):
    cbar_tick_kw, cbar_xlabel_kw = cbar_kw_default(cbar_tick_kw, cbar_xlabel_kw)
    cbar_rng = np.linspace(np.nanmin(data), np.nanmax(data), 10) if cbar_rng is None else cbar_rng
    data[data < cbar_rng[0]] = cbar_rng[0]
    data[data > cbar_rng[-1]] = cbar_rng[-1]
    fig, ax, handle = tricontourf(lon, lat, tri, data, cbar_rng, figure_kwargs, subplot_kwargs, **kwargs)
    cbar = _plt.add_colorbar(fig, handle, cbar_rng, cbar_position)
    cbar.ax.set_xlabel(cbar_xlabel, **cbar_xlabel_kw)
    cbar.ax.tick_params(**cbar_tick_kw)
    return fig, ax, cbar


def _h_dist_tripcolor(lon, lat, tri, data, cbar_xlabel=None, cbar_rng=None, cbar_position=None, figure_kwargs=None,
                      subplot_kwargs=None, cbar_xlabel_kw: dict = None, cbar_tick_kw=None, extend='both', **kwargs):
    cbar_tick_kw, cbar_xlabel_kw = cbar_kw_default(cbar_tick_kw, cbar_xlabel_kw)
    cbar_rng = np.linspace(np.nanmin(data), np.nanmax(data), 10) if cbar_rng is None else cbar_rng
    data[data < cbar_rng[0]] = cbar_rng[0]
    data[data > cbar_rng[-1]] = cbar_rng[-1]
    fig, ax, handle = tripcolor(lon, lat, tri, data, cbar_rng, figure_kwargs, subplot_kwargs, **kwargs)
    cbar = _plt.add_colorbar(fig, handle, cbar_rng, cbar_position, extend)
    cbar.ax.set_xlabel(cbar_xlabel, **cbar_xlabel_kw)
    cbar.ax.tick_params(**cbar_tick_kw)
    return fig, ax, cbar

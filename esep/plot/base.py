# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : base.py
                      
                   Start Date : 2021-08-21 11:17
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
Introduction:


                                                                              
--------------------------------------------------------------------------------
"""

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from cartopy.mpl.gridliner import LongitudeFormatter, LatitudeFormatter

from .ticks import TickLabels


class Plot(object):
    fig = None
    ax = None
    _levels = None
    _cbar_tk = None
    _cbar_tl = None
    cbar_labelsize = 10
    bar_extend = 'both'
    ax_pos = [0.12, 0.25, 0.78, 0.03]
    lat_tk = np.arange(-90, 91, 30)
    lon_tk = np.arange(-180, 181, 60)
    color_map = 'RdBu'

    def __init__(self, save_path, variable):
        self.lon, self.lat = np.meshgrid(range(-180, 180), range(-90, 90))
        self.save_path = save_path
        self.var = variable

    def init_layout(self, nrows=1, ncols=1, grid=False, subplot_kw=None, gridspec_kw=None):
        self.fig = plt.Figure()
        if grid:
            gs = self.fig.add_gridspec(nrows, ncols)
            # FIXME: 补充完整，将gs转换为axes
        else:
            self.ax = self.fig.subplots(nrows, ncols, subplot_kw=subplot_kw)

    def lim_lat(self, min_lat, max_lat):
        self.lat_tk = np.arange(min_lat, max_lat + 1, 30)
        self.var[np.where(
            np.logical_or(self.lat < min_lat, self.lat > max_lat))] = np.nan
        return self

    def lim_lon(self, min_lon, max_lon):
        self.lat_tk = np.arange(min_lon, max_lon + 1, 60)
        self.var[np.where(
            np.logical_or(self.lon < min_lon, self.lon > max_lon))] = np.nan
        return self

    def set_levels(self, levels: list or np.ndarray, cbar_tk: list = None,
                   enable_format: bool = True, fnum: int = None):
        self._levels = levels
        if cbar_tk is not None:
            self._cbar_tk = cbar_tk
        else:
            self._cbar_tk = self._levels[::2]

        if enable_format:
            self._cbar_tl = TickLabels(self._cbar_tk, fnum).tick_format()

    def plot(self):
        self._cbar_pre_conf()
        self.ax.set_extent(self._extent_check())

        ctf = self.ax.contourf(self.lon, self.lat, self.var, self._levels,
                               transform=ccrs.PlateCarree(), cmap=self.color_map,
                               extend=self.bar_extend)
        # self.ax.coastlines(linewidths=0.5, resolution="50m")
        self.ax.set_xticks(self.lon_tk, crs=ccrs.PlateCarree())
        self.ax.set_yticks(self.lat_tk, crs=ccrs.PlateCarree())
        self.ax.xaxis.set_major_formatter(
            LongitudeFormatter(zero_direction_label=True, number_format='.0f'))
        self.ax.yaxis.set_major_formatter(LatitudeFormatter())
        self.ax.tick_params(direction='in', labelsize=9)

        # FIXME: 这里需要改进，应该处理为自动识别图片，然后在图片下方或右方
        cax = self.fig.add_axes(self.ax_pos)
        cbar = self.fig.colorbar(ctf, cax=cax, orientation='horizontal')
        cbar.set_ticks(self._cbar_tk)
        cbar.set_ticklabels(self._cbar_tl)
        cbar.ax.tick_params(direction='in', labelsize=self.cbar_labelsize)

        self._save_fig()

    def _cbar_pre_conf(self):
        if self._levels is None:
            if np.nanmin(self.var) == np.nanmax(self.var):
                self._levels = np.linspace(0, 1, 21)
            else:
                self._levels = np.linspace(np.nanmin(self.var),
                                           np.nanmax(self.var), 21)
        if self._cbar_tk is None:
            self._cbar_tk = self._levels[::2]
        if self._cbar_tl is None:
            self._cbar_tl = TickLabels(self._cbar_tk).tick_format()

    def _save_fig(self):
        self.fig.savefig(self.save_path, bbox_inches="tight", pad_inches=0.0,
                         dpi=600)

    def _extent_check(self):
        lon_min = np.min(self.lon_tk)
        lon_max = np.max(self.lon_tk)
        lat_min = np.min(self.lat_tk)
        lat_max = np.max(self.lat_tk)
        return lon_min, lon_max, lat_min, lat_max

    def __del__(self):
        plt.close(self.fig)
        attr_ls = [key for key in self.__dict__.keys()]
        for key in attr_ls:
            self.__delattr__(key)


def tripcolor(lon, lat, tri, data, level, figure_kwargs=None, subplot_kwargs=None, **kwargs):
    subplot_kwargs = subplot_kwargs or dict()
    figure_kwargs = figure_kwargs or dict()
    subplot_kwargs.update(dict(nrows=1, ncols=1, subplot_kw=dict(projection=ccrs.PlateCarree())))
    fig, ax = plt.set_framework(figure_kwargs, subplot_kwargs)

    handle = plt.tripcolor(ax, lon, lat, tri, data, level, **kwargs)

    return fig, ax, handle


def tricontourf(lon, lat, tri, data, level, figure_kwargs=None, subplot_kwargs=None, **kwargs):
    subplot_kwargs = subplot_kwargs or dict()
    figure_kwargs = figure_kwargs or dict()
    subplot_kwargs.update(dict(nrows=1, ncols=1, subplot_kw=dict(projection=ccrs.PlateCarree())))
    fig, ax = plt.set_framework(figure_kwargs, subplot_kwargs)

    handle = plt.tricontourf(ax, lon, lat, tri, data, level, **kwargs)

    return fig, ax, handle


def cbar_kw_default(cbar_tick_kw, cbar_xlabel_kw):
    cbar_tick_kw = cbar_tick_kw or dict()
    cbar_xlabel_kw = cbar_xlabel_kw or dict()
    cbar_xlabel_kw.setdefault('labelpad', -0.5)
    cbar_xlabel_kw.setdefault('size', 7)
    cbar_tick_kw.setdefault('labelsize', 5)
    cbar_tick_kw.setdefault('direction', 'in')
    cbar_tick_kw.setdefault('length', 3)
    cbar_tick_kw.setdefault('width', 0.5)
    return cbar_tick_kw, cbar_xlabel_kw

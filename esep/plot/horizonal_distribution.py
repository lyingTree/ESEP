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
from functools import partial

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from cartopy.mpl.gridliner import LongitudeFormatter, LatitudeFormatter
from matplotlib.animation import FuncAnimation

from .ticks import adjust_cbar_tick
from ..physics.base import speed


class HorizontalDistribution:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat
        self.fig, self.ax = plt.subplots(1, 1, figsize=(12, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
        self.fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.05)
        self.fig_fmt = 'png'

    def _common(self, xticks, yticks, extent=None, **kwargs):
        kwargs.setdefault('ticks', {})
        kwargs.get('ticks').setdefault('labelsize', 12)
        kwargs.get('ticks').setdefault('direction', 'in')
        kwargs.get('ticks').setdefault('length', 5)
        kwargs.get('ticks').setdefault('width', 1.5)

        kwargs.setdefault('label', {})
        kwargs.get('label').setdefault('fontsize', 18)

        kwargs.setdefault('face_color', 'white')
        if self.add_features.__code__.co_argcount > 1:
            self.add_features()
        if extent is not None:
            self.ax.set_extent(extent)
        self.ax.set_xticks(xticks)
        self.ax.set_yticks(yticks)
        self.ax.xaxis.set_major_formatter(LongitudeFormatter())
        self.ax.yaxis.set_major_formatter(LatitudeFormatter())
        self.ax.tick_params(**kwargs.get('ticks'))
        self.ax.yaxis.set_zorder(999)
        self.ax.xaxis.set_zorder(999)
        self.ax.set_xlabel('经度', **kwargs.get('label'))
        self.ax.set_ylabel('纬度', **kwargs.get('label'))
        self.ax.patch.set_facecolor(kwargs.get('face_color'))
        for spline in self.ax.spines:
            self.ax.spines[spline].set_linewidth(1.5)
            self.ax.spines[spline].set_zorder(999)

    def _save_fig(self, save_path):
        if isinstance(self.fig_fmt, list):
            for fmt in self.fig_fmt:
                self.fig.savefig(save_path, fomart=fmt, bbox_inches='tight', pad_inches=0.2)
        else:
            self.fig.savefig(save_path, fomart=self.fig_fmt, bbox_inches='tight', pad_inches=0.2)
        self.ax.cla()

    def _add_color_bar(self, handle, level, label, **kwargs):
        tk_kwargs = {}
        label_kwargs = {}

        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('extend', 'both')
        kwargs.setdefault('width', 0.03)
        labelpad, lb_hgt, lb_width, tb_hgt, tb_width, xsize, ysize, x0, y0, x1, y1 = self._get_position()

        if kwargs.get('orientation') == 'horizontal':
            # 第一个labelpad是ticklabel和axes，第二个是xlabel和ticklabel，第三个是colorbar和xlabel
            tmp = (tb_hgt + lb_hgt + labelpad * 3) / ysize
            rect = [x0, y0 - kwargs.get('width') - tmp, x1 - x0, kwargs.get('width')]  # [left, bottom, width, height]
        else:
            tmp = tb_width / xsize / 2
            rect = [x1 + tmp, y0, kwargs.get('width'), y1 - y0]
        kwargs.pop('width')

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

        cbar = self.fig.colorbar(handle, cax=self.fig.add_axes(rect), **kwargs)
        cbar.ax.tick_params(**tk_kwargs)
        if kwargs.get('orientation') == 'horizontal':
            cbar.ax.set_xlabel(label, **label_kwargs)
        else:
            cbar.ax.set_ylabel(label, **label_kwargs)

        adjust_cbar_tick(cbar, level)

    def _add_qk(self, handle, qu, qk_label, **kwargs):
        kwargs.setdefault('labelpos', 'E')
        kwargs.setdefault('fontproperties', dict(size=15))
        kwargs.setdefault('coordinates', 'figure')

        qk = self.ax.quiverkey(handle, 0, 0, qu, qk_label, zorder=999, **kwargs)
        labelpad, lb_hgt, lb_width, tb_hgt, tb_width, xsize, ysize, x0, y0, x1, y1 = self._get_position()
        qk_extent = qk.text.get_window_extent(self.fig.canvas.draw(), self.fig.dpi)
        qk_width = qk_extent.width
        qk_hgt = qk_extent.height
        # 10 表示 →后的那个空格的宽度，qk_extent的宽度不包含 →和空格
        qk.X = x1 - (qk_width + 10) / xsize
        qk.Y = y1 + (qk_hgt / 2 / ysize)

    def _get_position(self):
        ax_xaxis = self.ax.xaxis
        tb_extent = ax_xaxis.get_ticklabels()[-1].get_window_extent(self.fig.canvas.draw(), self.fig.dpi)
        tb_hgt = tb_extent.height
        tb_width = tb_extent.width

        lb_extent = ax_xaxis.get_label().get_window_extent(self.fig.canvas.draw(), self.fig.dpi)
        lb_hgt = lb_extent.height
        lb_width = lb_extent.width

        x0, y0, x1, y1 = self.ax.get_position().extents
        xsize, ysize = self.fig.get_size_inches() * self.fig.dpi
        labelpad = ax_xaxis.labelpad
        return labelpad, lb_hgt, lb_width, tb_hgt, tb_width, xsize, ysize, x0, y0, x1, y1

    def contourf(self, data, level, lon_rng, lat_rng, save_path, cb_label=None, only_chart=False, *args, **kwargs):
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

        if only_chart:
            return handle
        extent = [lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]]
        self._common(lon_rng, lat_rng, extent, **common_kwargs)
        if cb_label is not None:
            self._add_color_bar(handle, level, cb_label, **cb_kwargs)
        if save_path is not None:
            self._save_fig(save_path)
            return None
        return handle

    def quiver(self, u, v, scale, lon_rng, lat_rng, save_path, qk_u=None, *args, **kwargs):
        kwargs.setdefault('width', 0.001)
        kwargs.setdefault('headwidth', 10)
        kwargs.setdefault('headlength', 10)
        kwargs.setdefault('color', 'black')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('animated', True)

        common_kwargs = {}
        if 'common' in kwargs:
            common_kwargs = kwargs.get('common')
            kwargs.pop('common')

        qk_kwargs = {}
        if 'qk' in kwargs:
            qk_kwargs = kwargs.get('qk')
            kwargs.pop('qk')

        handle = self.ax.quiver(self.lon, self.lat, u, v, scale=scale, *args, **kwargs)

        if qk_u is None:
            qk_u = np.round(np.nanmean(speed(u, v)), 2)
        self._add_qk(handle, qk_u, '{qk_u}m/s'.format(qk_u=qk_u), **qk_kwargs)

        extent = [lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]]
        self._common(lon_rng, lat_rng, extent, **common_kwargs)
        if save_path is not None:
            self._save_fig(save_path)
            return None
        return handle

    def tripcolor(self, tri, data, level, lon_rng, lat_rng, save_path, cb_label=None, only_chart=False, *args,
                  **kwargs):
        kwargs.setdefault('cmap', 'bwr')

        cb_kwargs = {}
        if 'colorbar' in kwargs:
            cb_kwargs = kwargs.get('colorbar')
            kwargs.pop('colorbar')

        common_kwargs = {}
        if 'common' in kwargs:
            common_kwargs = kwargs.get('common')
            kwargs.pop('common')
        vmin, vmax = np.nanmin(level), np.nanmax(level)
        handle = self.ax.tripcolor(self.lon, self.lat, tri, data, vmin=vmin, vmax=vmax, *args, **kwargs)

        if only_chart:
            return handle
        extent = [lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]]
        self._common(lon_rng, lat_rng, extent, **common_kwargs)
        if cb_label is not None:
            self._add_color_bar(handle, level, cb_label, **cb_kwargs)
        if save_path is not None:
            self._save_fig(save_path)
            return None
        return handle

    @abstractmethod
    def add_features(self):
        pass


class HorizDistAnimation(HorizontalDistribution, ABC):
    handle = None

    def __init__(self, lon, lat):
        super(HorizDistAnimation, self).__init__(lon, lat)
        self.fig.set_size_inches(12, 12)

    def contourf(self, data, level, lon_rng, lat_rng, save_path, cb_label=None, *args, **kwargs):
        init_func = partial(self._init_ctf, data=data[0], level=level, lon_rng=lon_rng, lat_rng=lat_rng,
                            cb_label=cb_label, *args, **kwargs)
        update_func = partial(self._update_ctf, lon_rng=lon_rng, lat_rng=lat_rng, level=level, only_chart=True, *args,
                              **kwargs)

        animation = FuncAnimation(fig=self.fig, func=update_func, frames=data, init_func=init_func,
                                  save_count=np.shape(data)[0], interval=200)

        animation.save('.'.join([str(save_path), 'gif']), writer='ffmpeg')

    def quiver(self, u, v, scale, lon_rng, lat_rng, save_path, qk_u=None, *args, **kwargs):
        init_func = partial(self._init_quiver, u=u[0], v=v[0], scale=scale, lon_rng=lon_rng, lat_rng=lat_rng, qk_u=qk_u,
                            *args, **kwargs)
        update_func = partial(self._update_quiver, *args, **kwargs)

        animation = FuncAnimation(fig=self.fig, func=update_func, frames=zip(u, v), init_func=init_func,
                                  save_count=np.shape(u)[0], interval=200, blit=True)
        animation.save('.'.join([str(save_path), 'gif']), writer='ffmpeg')

    def _init_quiver(self, u, v, scale, lon_rng, lat_rng, qk_u, *args, **kwargs):
        self.handle = super(HorizDistAnimation, self).quiver(u, v, scale, lon_rng, lat_rng, save_path=None, qk_u=qk_u,
                                                             *args, **kwargs)
        return [self.handle]

    def _update_quiver(self, data):
        u, v = data
        self.handle.set_UVC(u, v)
        return [self.handle]

    def _init_ctf(self, data, level, lon_rng, lat_rng, cb_label, *args, **kwargs):
        self.handle = [super(HorizDistAnimation, self).contourf(data, level, lon_rng, lat_rng, save_path=None,
                                                                cb_label=cb_label, *args, **kwargs)]
        return self.handle

    def _update_ctf(self, data, lon_rng, lat_rng, level, only_chart, *args, **kwargs):
        for hp in self.handle[0].collections:
            hp.remove()

        self.handle = [super(HorizDistAnimation, self).contourf(data, level, lon_rng, lat_rng, save_path=None,
                                                                only_chart=only_chart, *args, **kwargs)]
        return self.handle

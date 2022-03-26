# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : plot.py
                      
                   Start Date : 2021-08-20 12:30
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
Introduction:

plot functions
                                                                              
--------------------------------------------------------------------------------
"""

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from matplotlib import patches

from ESEP.esep.plot.color_bar import adjust_cbar_position
from ESEP.esep.plot.ticks import tick_labels


def set_framework(figure_kwargs, subplot_kwargs):
    fig = plt.figure(**figure_kwargs)
    axes = fig.subplots(**subplot_kwargs)
    return fig, axes


def tripcolor(ax, lon: np.ndarray, lat: np.ndarray, tri: np.ndarray, data: np.ndarray, level,
              lon_rng: np.ndarray = None, lat_rng: np.ndarray = None, **kwargs) -> tuple:
    kwargs.setdefault('cmap', 'Blues')
    kwargs.setdefault('linewidth', 0.02)
    kwargs.setdefault('edgecolor', 'k')
    # lon_rng = set_detect(lon, lon_rng, 5)
    # lat_rng = set_detect(lat_detect(lat), lat_rng, 5)

    ax.set_extent([lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]], crs=ccrs.PlateCarree())
    ax.set_xticks(lon_rng, crs=ccrs.PlateCarree())
    ax.set_yticks(lat_rng, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(direction='in', labelsize=8, length=2.5, width=0.7)
    tca = ax.tripcolor(lon, lat, tri, data, vmin=level[0], vmax=level[-1], transform=ccrs.PlateCarree(), **kwargs)

    return tca


def tricontourf(ax, lon: np.ndarray, lat: np.ndarray, tri: np.ndarray, data: np.ndarray, level=None,
                lon_rng: np.ndarray = None, lat_rng: np.ndarray = None, **kwargs) -> tuple:
    kwargs.setdefault('cmap', 'Blues')
    kwargs.setdefault('linewidth', 0.02)
    kwargs.setdefault('edgecolor', 'k')

    # lon_rng = set_detect(lon, lon_rng, 5)
    # lat_rng = set_detect(lat_detect(lat), lat_rng, 5)

    ax.set_extent([lon_rng[0], lon_rng[-1], lat_rng[0], lat_rng[-1]], crs=ccrs.PlateCarree())
    ax.set_xticks(lon_rng, crs=ccrs.PlateCarree())
    ax.set_yticks(lat_rng, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(direction='in', labelsize=8, length=2.5, width=0.7)
    tca = ax.tricontourf(lon, lat, tri, data, level, transform=ccrs.PlateCarree(), **kwargs)

    return tca


def add_boundaries_point(ax, open_boundaries, node_style='ro', node_size=1):
    handles = []
    for boundary in open_boundaries:
        handles.append(ax.plot(*boundary, node_style, markersize=node_size))
    return handles


def add_colorbar(fig, handle, level, position=None, extend='both'):
    cbar = fig.colorbar(handle, cax=adjust_cbar_position(fig, position), orientation='horizontal', extend=extend)
    cbar_tick = [x for x in level[::2]]
    cbar_tick_labels = tick_labels(cbar_tick)
    cbar.set_ticks(cbar_tick)
    cbar.set_ticklabels(cbar_tick_labels)
    cbar.ax.tick_params(labelsize=7, direction='in', length=1, width=0.4)
    return cbar


def save_fig(fig, filepath, **kwargs):
    if 'dpi' not in kwargs:
        kwargs['dpi'] = 1200
    if 'bbox_inches' not in kwargs:
        kwargs['bbox_inches'] = 'tight'
    fig.savefig(filepath, **kwargs)


def multiax_xylabels(row, col, index, ax, xt, xtl, xl, yt, ytl, yl, lb_fz, tl_fz):
    ax.set_xticks(xt)
    ax.set_yticks(yt)
    if row > 1 and col == 1:
        if index == row - 1:
            ax.set_xticklabels(xtl, fontsize=tl_fz)
            ax.set_xlabel(xl, fontsize=lb_fz)
        else:
            ax.set_xticklabels("")
            ax.set_xlabel("")
        ax.set_yticklabels(ytl, fontsize=tl_fz)
        ax.set_ylabel(yl, fontsize=lb_fz)
    elif row > 1 and col > 1:
        if index >= col * (row - 1):
            ax.set_xticklabels(xtl, fontsize=tl_fz)
            ax.set_xlabel(xl, fontsize=lb_fz)
        else:
            ax.set_xticklabels("")
            ax.set_xlabel("")
        if not index % col:
            ax.set_yticklabels(ytl, fontsize=tl_fz)
            ax.set_ylabel(yl, fontsize=lb_fz)
        else:
            ax.set_yticklabels("")
            ax.set_ylabel("")
    else:
        if index == 0:
            ax.set_yticklabels(ytl, fontsize=tl_fz)
            ax.set_ylabel(yl, fontsize=lb_fz)
        else:
            ax.set_yticklabels("")
            ax.set_ylabel("")
        ax.set_xticklabels(xtl, fontsize=tl_fz)
        ax.set_xlabel(xl, fontsize=lb_fz)


def trans_rng(data_arr, rng: tuple = None):
    if rng is None:
        rng = [None, None]
        rng[0] = np.min(data_arr)
        rng[-1] = np.max(data_arr)
    return rng


class PlotSetting(object):
    class Figure(object):
        def __init__(self, fig_num=None, size=None, dpi=None, face_color=None,
                     edge_color=None):
            self.size = size
            self.dpi = dpi
            self.face_color = face_color
            self.edge_color = edge_color
            self.fig = plt.figure(fig_num, size, dpi, face_color, edge_color)

    class SubPlt(object):
        def __init__(self, row=1, col=1, h_gap=0.5, w_gap=0.5, left=0,
                     bottom=0, right=1, top=1):
            self.row = row
            self.col = col
            self.h_gap = h_gap
            self.w_gap = w_gap
            self.left = left
            self.bottom = bottom
            self.right = right
            self.top = top

        def sub_plt_gap(self):
            return dict(hspace=self.h_gap, wspace=self.w_gap)

        def sub_plt_size(self):
            return dict(left=self.left, bottom=self.bottom, right=self.right,
                        top=self.top)

    class Axis(object):
        def __init__(self, direction="in", length=2, width=0.4, color="k", tl_fontsize=6, label_fontsize=8,
                     right_axis_enabled=False):
            self.direction = direction
            self.length = length
            self.width = width
            self.color = color
            self.tl_fontsize = tl_fontsize
            self.label_fontsize = label_fontsize
            self.right_axis_enabled = right_axis_enabled

        class YAxis(object):
            def __init__(self, sequence=None, tick_label=None, label=None, label_pad=0.1, invert=False, scale="linear",
                         lim=None, rotation=0):
                if label is None:
                    label = []
                if tick_label is None:
                    tick_label = []
                if sequence is None:
                    sequence = []
                self.sequence = sequence
                self.tick_label = tick_label
                self.label = label
                self.label_pad = label_pad
                self.invert = invert
                self.scale = scale
                self.lim = lim
                self.rotation = rotation

        class RightAxis(object):
            def __init__(self, sequence=None, tick_label=None, label=None, label_pad=0.1, invert=False, scale="linear",
                         lim=None, rotation=0):
                if label is None:
                    label = []
                if tick_label is None:
                    tick_label = []
                if sequence is None:
                    sequence = []
                self.sequence = sequence
                self.tick_label = tick_label
                self.label = label
                self.label_pad = label_pad
                self.invert = invert
                self.scale = scale
                self.lim = lim
                self.rotation = rotation

        class XAxis(object):
            def __init__(self, sequence=None, tick_label=None, label=None, label_pad=0.1, invert=False, scale="linear",
                         lim=None, rotation=0):
                if label is None:
                    label = []
                if tick_label is None:
                    tick_label = []
                if sequence is None:
                    sequence = []
                self.sequence = sequence
                self.tick_label = tick_label
                self.label = label
                self.label_pad = label_pad
                self.invert = invert
                self.scale = scale
                self.lim = lim
                self.rotation = rotation

    class ColorBar(object):
        def __init__(self, left, bottom, width, height, orientation):
            self.left = left
            self.bottom = bottom
            self.width = width
            self.height = height
            self.orientation = orientation

        class Axis(object):
            def __init__(self, direction="in", length=2, width=0.4, color="k",
                         tl_fontsize=6, label_fontsize=8):
                self.direction = direction
                self.length = length
                self.width = width
                self.color = color
                self.tl_fontsize = tl_fontsize
                self.label_fontsize = label_fontsize

            class YAxis(object):
                def __init__(self, label=None, label_pad=0.1, invert=False, scale="linear", lim=None, rotation=0):
                    if label is None:
                        label = []
                    self.label = label
                    self.label_pad = label_pad
                    self.invert = invert
                    self.scale = scale
                    self.lim = lim
                    self.rotation = rotation

            class XAxis(object):
                def __init__(self, sequence=None, tick_label=None, label=None, label_pad=0.1, invert=False,
                             scale="linear", lim=None, rotation=0):
                    if label is None:
                        label = []
                    if tick_label is None:
                        tick_label = []
                    if sequence is None:
                        sequence = []
                    self.sequence = sequence
                    self.tick_label = tick_label
                    self.label = label
                    self.label_pad = label_pad
                    self.invert = invert
                    self.scale = scale
                    self.lim = lim
                    self.rotation = rotation

    class Text(object):
        def __init__(self):
            self.left = []
            self.bottom = []
            self.text_str = []
            self.fontsize = []
            self.color = []
            self.rotation = []

        def add_text(self, left, bottom, text_str, fontsize=4, color='k',
                     rotation=0):
            self.left.append(left)
            self.bottom.append(bottom)
            self.text_str.append(text_str)
            self.fontsize.append(fontsize)
            self.color.append(color)
            self.rotation.append(rotation)

        def plot_text(self, ind):
            plt.text(self.left[ind], self.bottom[ind], self.text_str[ind],
                     fontsize=self.fontsize[ind], color=self.color[ind],
                     rotation=self.rotation[ind])

    class Polygon(object):
        def __init__(self):
            self.x = []
            self.y = []

        def add_polygon(self, x, y):
            self.x.append(x)
            self.y.append(y)

        def plot_polygon(self, ind):
            plt.add_patch(patches.Polygon(xy=list(zip(self.x[ind], self.y[ind])), fill=False))


def plot_init(plt_config, plt_type, *args, **kwargs):
    sub_plt_row = plt_config.SubPlt.row
    sub_plt_col = plt_config.SubPlt.col
    sub_plt_num = sub_plt_row * sub_plt_col

    fig = plt_config.Figure.fig
    plt.subplots_adjust(plt_config.SubPlt.sub_plt_size())
    plt.subplots_adjust(plt_config.SubPlt.sub_plt_gap())

    for i in range(1, sub_plt_num + 1):
        left_axis = fig.add_subplot(sub_plt_row, sub_plt_col, i)
        plt_type(left_axis, *args)

        # 坐标轴统一属性
        tkw = dict(size=plt_config.Axis.length, width=plt_config.Axis.width,
                   colors=plt_config.Axis.color,
                   direction=plt_config.Axis.direction)
        tlw = dict(fontsize=plt_config.Axis.tl_fontsize)
        lbw = dict(fontsize=plt_config.Axis.label_fontsize,
                   color=plt_config.Axis.color)

        # 左坐标轴设置
        left_axis.set_yticks(plt_config.Axis.YAxis.sequence)
        lev_str = plt_config.Axis.YAxis.tick_label
        if i % sub_plt_col == 1:
            left_axis.set_yticklabels(lev_str, **tlw)
            left_axis.set_ylabel(plt_config.Axis.YAxis.label, **lbw)
        else:
            left_axis.set_yticklabels('')
        left_axis.set_ylim(bottom=plt_config.Axis.YAxis.lim[0],
                           top=plt_config.Axis.YAxis.lim[1])
        if plt_config.Axis.YAxis.invert:
            left_axis.invert_yaxis()  # y轴反向
        left_axis.tick_params(**tkw)

        # 左坐标轴设置
        if plt_config.Axis.right_axis_enabled:
            right_axis = left_axis.twinx()
            right_axis.set_yticks(plt_config.Axis.RightAxis.sequence)
            height_str = plt_config.Axis.RightAxis.tick_label
            if i % sub_plt_col == 0:
                right_axis.set_yticklabels(height_str, **tlw)
                right_axis.set_ylabel(plt_config.Axis.RightAxis.label, **lbw)
            else:
                right_axis.set_yticklabels('')
            right_axis.set_ylim(bottom=plt_config.Axis.RightAxis.lim[0],
                                top=plt_config.Axis.RightAxis.lim[1])
            if plt_config.Axis.RightAxis.invert:
                right_axis.invert_yaxis()  # y轴反向
            right_axis.tick_params(**tkw)

            # 以右坐标轴绘制地形
            plt_type(right_axis, **kwargs)

        # X轴设置
        left_axis.set_xticks(plt_config.Axis.XAxis.sequence)
        if i > (sub_plt_row - 1) * sub_plt_col:
            left_axis.set_xticklabels(plt_config.Axis.XAxis.tick_label, **tlw)
        else:
            left_axis.set_xticklabels('')
        left_axis.set_xlim(bottom=plt_config.Axis.XAxis.lim[0],
                           top=plt_config.Axis.XAxis.lim[1])

        # TODO:为标注、文字、标题等添加设置
        # 添加标注、文字、标题
        plt_config.Text.plot_text(i - 1)
        plt_config.Polygon.plot_polygon(i - 1)

    # color bar设置
    cbar_config = plt_config.ColorBar()
    cax = plt.axes([cbar_config.left, cbar_config.bottom, cbar_config.width,
                    cbar_config.height])  # [左，下，宽，高]
    cbar = plt.colorbar(cax=cax, orientation=cbar_config.orientation)
    # TODO:修改color bar标签
    cbar.ax.set_xlabel(cbar_config.XAixs.label, labelpad=cbar_config.XAixs.label_pad, size=cbar_config.label_fontsize)
    cbar.set_ticks(cbar_config.XAixs.sequence)
    cbar.set_ticklabels(cbar_config.XAixs.tick_label)
    cbar.ax.tick_params(labelsize=cbar_config.tl_fontsize, direction=cbar_config.direction, length=cbar_config.length,
                        width=cbar_config.width)

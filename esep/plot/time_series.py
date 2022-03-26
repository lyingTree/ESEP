# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : time_series.py
                      
                   Start Date : 2021-08-21 12:59
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
Introduction:


                                                                              
--------------------------------------------------------------------------------
"""

from datetime import datetime

import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np

from ESEP.esep.plot import plot as _plt
from ESEP.esep.plot.base import tripcolor, cbar_kw_default


def plot(filepath, save_path, var_name, time, lev=None, **kwargs):
    lon, lat, tri, data, cbar_xlabel = _data_read(filepath, var_name, time, lev)
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


def _time_proc(ds_vars, time_str):
    time = [datetime.strptime(x.tobytes().decode(), '%Y-%m-%dT%H:%M:%S.%f') for x in ds_vars.get('Times')[:]]
    time_sel = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    return time.index(time_sel)


def _h_dist(lon, lat, tri, data, cbar_xlabel=None, cbar_rng=None, cbar_position=None, figure_kwargs=None,
            subplot_kwargs=None,
            cbar_xlabel_kw: dict = None, cbar_tick_kw=None, **kwargs):
    cbar_tick_kw, cbar_xlabel_kw = cbar_kw_default(cbar_tick_kw, cbar_xlabel_kw)
    cbar_rng = np.linspace(np.nanmin(data), np.nanmax(data), 10) if cbar_rng is None else cbar_rng
    data[data < cbar_rng[0]] = cbar_rng[0]
    data[data > cbar_rng[-1]] = cbar_rng[-1]
    fig, ax, handle = tripcolor(lon, lat, tri, data, figure_kwargs, subplot_kwargs, **kwargs)
    cbar = _plt.add_colorbar(fig, handle, cbar_rng, cbar_position)
    cbar.ax.set_xlabel(cbar_xlabel, **cbar_xlabel_kw)
    cbar.ax.tick_params(**cbar_tick_kw)
    return fig, ax, cbar


class TimeSeries:
    def __init__(self, station_name):
        self.station_name = station_name
        self.fig, self.ax = plt.subplots(1, 1, figsize=(12, 4))
        self.fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.2)
        self.min_num_data = 30

    def _common(self, ylabel, xticks, yticks, add_zero=True, add_title=True, add_xlabel=True):
        if add_zero:
            self.ax.hlines(0, -9E99, 9E99, linestyles='--', colors='black')
        self.ax.set_xticks(xticks)
        self.ax.set_xticklabels([x.strftime('%d-%H:%M') for x in xticks])
        if add_xlabel:
            self.ax.set_xlabel('时间', fontsize=16)

        self.ax.set_ylabel(ylabel, fontsize=16)
        if add_title:
            self.ax.set_title(self.station_name, fontsize=30)

        self.ax.set_xlim([xticks[0], xticks[-1]])
        if yticks is not None:
            self.ax.set_ylim([yticks[0], yticks[-1]])
            self.ax.set_yticks(yticks)
            self.ax.set_yticklabels([str(x) for x in yticks])
        self.ax.tick_params(labelsize=12, direction='in')
        self.ax.legend(loc='upper right', fontsize=12)

    def _save_fig(self, save_path):
        self.fig.savefig(save_path, fomart='png', bbox_inches='tight', pad_inches=0.1)
        self.ax.cla()

    def sediment(self, obs_time, model_time, obs, model, save_path):
        obs_invl = np.round(np.size(obs_time) / self.min_num_data).astype(int)
        model_invl = np.round(np.size(model_time) / self.min_num_data).astype(int)
        self.ax.scatter(obs_time[::obs_invl], obs[::obs_invl], s=20, color='black', label='观测')
        self.ax.plot(model_time[::model_invl], model[::model_invl], linewidth=2, color='black', label='模型')
        self._common('含沙量[kg/m3]', model_time[::model_invl + 1], np.arange(0, 3.51, 0.5), False)
        self._save_fig(save_path)

    def depth(self, obs_time, model_time, obs, model, save_path):
        obs_invl = np.round(np.size(obs_time) / self.min_num_data).astype(int)
        model_invl = np.round(np.size(model_time) / self.min_num_data).astype(int)
        self.ax.scatter(obs_time[::obs_invl], (obs - np.nanmean(obs))[::obs_invl], s=35, color='black', label='观测')
        self.ax.plot(model_time[::model_invl], (model - np.nanmean(model))[::model_invl], linewidth=2, color='black',
                     label='模型')
        self._common('潮位[m]', model_time[::model_invl + 1], np.arange(-4, 5))
        self._save_fig(save_path)

    def cs_dir(self, obs_time, model_time, obs, model, save_path):
        obs_invl = np.round(np.size(obs_time) / self.min_num_data).astype(int)
        model_invl = np.round(np.size(model_time) / self.min_num_data).astype(int)
        self.fig.set_size_inches(12, 4)
        self.fig.clf()
        axs = self.fig.subplots(2, 1)
        ylabels = [
            '流速[m/s]',
            '流向[°]'
        ]
        yticks = [
            [0, 0.6, 1.2, 1.8],
            [0, 100, 200, 300, 400]
        ]

        for idx, ax in enumerate(axs):
            self.ax = ax
            ax.scatter(obs_time[::obs_invl], obs[idx][::obs_invl], s=20, color='black', label='观测')
            ax.plot(model_time[::model_invl], model[idx][::model_invl], linewidth=2, color='black', label='模型')
            flag = False if idx else True
            self._common(ylabels[idx], model_time[::model_invl + 1], yticks[idx], False, flag, not flag)
            if not idx:
                self.ax.set_xticks([])
                self.ax.set_xticklabels([])

        self._save_fig(save_path)

    def __del__(self):
        plt.close(self.fig)

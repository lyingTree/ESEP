# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : domain.py
                      
                   Start Date : 2021-08-20 16:44
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
Introduction:

模式模拟区域示意图通用方法集
                                                                              
--------------------------------------------------------------------------------
"""
import PyFVCOM as pf
import netCDF4 as nc
import numpy as np

from ESEP.esep.plot import plot as plt
from ESEP.esep.plot.base import tripcolor, cbar_kw_default
from ESEP.esep.utils import nodes2elems


def sms2dm(filepath, save_path, **kwargs):
    tri, nodes, lon, lat, zeta, types, node_strings = pf.grid.read_sms_mesh(filepath, nodestrings=True)
    zeta = nodes2elems(zeta, tri)

    open_boundaries = []
    for node_string in node_strings:
        open_boundaries.append((lon[node_string], lat[node_string]))
    fig, ax, cbar = _domain(lon, lat, tri, zeta, **kwargs)
    # plt.add_boundaries_point(ax, open_boundaries)
    plt.save_fig(fig, save_path)
    return fig, ax, cbar


def netcdf(filepath, save_path, **kwargs):
    ds = nc.Dataset(filepath)
    ds_vars = ds.variables
    lon = ds_vars.get('lon')[:]
    lat = ds_vars.get('lat')[:]
    tri = np.transpose(ds_vars.get('nv')[:]) - 1
    zeta = np.squeeze(ds_vars.get('h')[:])
    zeta = nodes2elems(zeta, tri)

    fig, ax, cbar = _domain(lon, lat, tri, zeta, **kwargs)

    plt.save_fig(fig, save_path, **kwargs.setdefault('save_fig_kwargs', dict()))
    return fig, ax, cbar


def _domain(lon, lat, tri, data, domain_name='', level=None, cbar_position=None, figure_kwargs=None,
            subplot_kwargs=None, cbar_xlabel_kw: dict = None, cbar_tick_kw=None, extend='both', **kwargs):
    cbar_tick_kw, cbar_xlabel_kw = cbar_kw_default(cbar_tick_kw, cbar_xlabel_kw)
    level = np.linspace(np.nanmin(data), np.nanmax(data), 10) if level is None else level
    data[data < level[0]] = level[0]
    data[data > level[-1]] = level[-1]
    fig, ax, handle = tripcolor(lon, lat, tri, data, level, figure_kwargs, subplot_kwargs, **kwargs)
    ax.set_title(domain_name)
    cbar = plt.add_colorbar(fig, handle, level, cbar_position, extend)
    cbar.ax.set_xlabel('Bathymetry[m]', **cbar_xlabel_kw)
    cbar.ax.tick_params(**cbar_tick_kw)
    return fig, ax, cbar


__all__ = ['sms2dm', 'netcdf']

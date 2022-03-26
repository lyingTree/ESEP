# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : plot_tmp.py

                   Start Date : 2021-10-06 14:40

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

$END$

-------------------------------------------------------------------------------
"""
import matplotlib.pyplot as plt
import numpy as np


def init_fig(row, col, figsize=(12, 8), left=None, bottom=None, right=None, top=None, wspace=None, hspace=None):
    fig, axs = plt.subplots(row, col, figsize=figsize)
    fig.subplots_adjust(left=left, bottom=bottom, right=right, top=top, wspace=wspace, hspace=0.05)
    return fig, axs


def time_series(data_ls, row, col, fig_conf, add_idx_text):
    fig, axs = init_fig(row, col, **fig_conf)
    if not isinstance(axs, list):
        axs = [axs]
    handles = []
    for idx, data in enumerate(data_ls):
        x, y, z, addition_data, plot_type, plt_opt = data

        if plot_type == 'scatter':
            tmp = axs[idx].scatter(x, y, **plt_opt)
        elif plot_type == 'contour':
            tmp = axs[idx].contour(x, y, z, **plt_opt)
        elif plot_type == 'contourf':
            tmp = axs[idx].contourf(x, y, z, **plt_opt)
        else:
            tmp = axs[idx].plot(x, y, **plt_opt)
        handles.append(tmp)

        xticks = x if addition_data.get('xticks') is None else addition_data.get('xticks')
        xlabels = x if addition_data.get('xlabels') is None else addition_data.get('xlabels')
        yticks = y if addition_data.get('yticks') is None else addition_data.get('yticks')
        ylabels = y if addition_data.get('ylabels') is None else addition_data.get('ylabels')
        xlim = [np.nanmin(x), np.nanmax(x)] if addition_data.get('xlim') is None else addition_data.get('xlim')
        ylim = [np.nanmin(y), np.nanmax(y)] if addition_data.get('ylim') is None else addition_data.get('ylim')
        legend = addition_data.get('legend')

        axs[idx].set_xticks(xticks)

        axs[idx].set_xticklabels(xlabels)
        axs[idx].set_yticks(yticks)
        axs[idx].set_yticklabels(ylabels)
        axs[idx].set_xlim(xlim)
        axs[idx].set_ylim(ylim)
        axs[idx].legend(legend)
        if add_idx_text:
            axs[idx].text(0.005, 0.88, '({0})'.format(chr(97 + idx)), fontsize=20, transform=axs[idx].transAxes)

    return fig, axs

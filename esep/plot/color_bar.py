# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : color_bar.py

                   Start Date : 2022-03-25 05:27

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""


def adjust_cbar_position(fig, position):
    if position is None:
        # TODO: 自动调整colorbar axes位置
        cax = fig.add_axes([0.125, 0.05, 0.775, 0.03])  # [左，下，宽，高]
    else:
        cax = fig.add_axes(position)
    return cax

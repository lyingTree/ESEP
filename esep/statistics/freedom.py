"""
#                                                                             #
# Corresponding source code is free software: you can redistribute it and/or  #
# modify it under the terms of the GNU General Public License as published    #
# by the Free Software Foundation, either version 3 of the License, or (at    #
# your option) any later version.                                             #
#-----------------------------------------------------------------------------#
#                                                                             #
#                 Project Name : Atmosphere&Ocean                             #
#                                                                             #
#                    File Name : base.py                                      #
#                                                                             #
#                      Version : 0.0.1                                        #
#                                                                             #
#                   Programmer : D.CW                                         #
#                                                                             #
#                   Start Date : 2020-06-05 16:38:59                          #
#                                                                             #
#                  Last Update : 2020-06-12 11:30:18                          #
#                                                                             #
#                        Email : dengchuangwu@gmail.com                       #
#                                                                             #
#-----------------------------------------------------------------------------#
# Introduction:                                                               #
# 提供了统计学的python算法实现                                                    #
#                                                                             #
#-----------------------------------------------------------------------------#
# Functions:                                                                  #
#   _xcor -- Calculation of the Cross-correlation.                            #
#                                                                             #
#-----------------------------------------------------------------------------#
"""

import numpy as np

from .base import xcor


class TTest(object):
    @staticmethod
    def normal(base_ts, ts, lag):
        N = np.size(base_ts)
        return N - abs(lag) - 2

    # Reference:
    # Pyper, B. J., and R. M. Peterman, 1998: Comparison of methods to account for autocorrelation in correlation
    # analyses of fish data.Can. J. Fish. Aquat. Sci.,55,2127–2140.
    @staticmethod
    def pyper(base_ts, ts, lag):
        N = np.size(base_ts)
        tmp = 0
        for j in range(1, N):
            tmp = tmp + (N - j) / N * (
                xcor(base_ts, base_ts, j) * xcor(ts, ts, j))
        n_eff = 1 / (1 / N + 2 / N * tmp)
        return n_eff

    # Reference:
    # 李刚,李崇银,谭言科,白涛.北半球冬季南太平洋海表温度异常的主要模态及其与ENSO的关系[J].海洋学报(中文版),2012,34(02):48-56.
    @staticmethod
    def li_gang(base_ts, ts, lag):
        N = np.size(base_ts)
        r1 = xcor(base_ts, base_ts, 1)
        r2 = xcor(ts, ts, 1)
        N_dof = N * ((1 - r1 * r2) / (1 + r1 * r2))
        return N_dof

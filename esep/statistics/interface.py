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
#                    File Name : interface.py                                 #
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
# Provide statistical Python implementation interface.                        #
#                                                                             #
#-----------------------------------------------------------------------------#
# Functions:                                                                  #
#***************************** class: Correlation ****************************#
#   xcor -- Obtain autocorrelation and correlation coefficient test values.   #
#                                                                             #
#-----------------------------------------------------------------------------#
"""

import scipy.stats as stats

from ._base import _xcor
from ._freedom import *


def fermat_point(a1, a2):
    n = np.size(a1)
    x = np.nanmean(a1)
    y = np.nanmean(a2)
    while True:
        xfenzi = 0
        xfenmu = 0
        yfenzi = 0
        yfenmu = 0
        for i in np.arange(n):
            g = np.sqrt((x - a1[i]) ** 2 + (y - a2[i]) ** 2)
            xfenzi = xfenzi + a1[i] / g
            xfenmu = xfenmu + 1 / g
            yfenzi = yfenzi + a2[i] / g
            yfenmu = yfenmu + 1 / g
        xn = xfenzi / xfenmu
        yn = yfenzi / yfenmu
        if abs(xn - x) < 0.01 and abs(yn - y) < 0.01:
            break
        else:
            x = xn
            y = yn
    return x, y


# TODO: Build detection module
class Correlation(object):
    def __init__(self):
        pass

    @staticmethod
    def xcor(x, y, lag: int = 0, alpha: float = 0.95, method=TTest) -> tuple:
        """

        :param x:
        :param y:
        :param lag:
        :param alpha:
        :param method:
        :return:
        ------------------------------------------------------------------
        Examples:

        ------------------------------------------------------------------
        Reference:
        Zar, J. H., 1984:Biostatistical Analysis. Prentice Hall, 718 pp, p.309
        """
        dof = method.freedom(x, y, lag)
        t_test = stats.t.ppf((1 + alpha) / 2, dof)  # alpha置信度的双侧t检验值
        r_crit = np.sqrt(t_test ** 2 / (t_test ** 2 + dof))
        rel = _xcor(x, y, lag)
        return rel, r_crit

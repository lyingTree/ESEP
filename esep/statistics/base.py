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
#                  Last Update : 2020-06-12 11:53:27                          #
#                                                                             #
#                        Email : dengchuangwu@gmail.com                       #
#                                                                             #
#-----------------------------------------------------------------------------#
# Introduction:                                                               #
# Provides a statistical implementation of the python algorithm.              #
#                                                                             #
#-----------------------------------------------------------------------------#
# Functions:                                                                  #
#   _xcor -- Calculation of the Cross-correlation.                            #
#                                                                             #
#-----------------------------------------------------------------------------#
"""
import numpy as np



def xcor(ts1, ts2, lag: int = 0) -> float:
    """Cross-correlation of two discrete time series

    A normal method to calculate degrees of freedom for t-test.Usually
    takes the value n-2, where n is the number of valid samples.

    :param ts1: A time series
    :param ts2: A time series
    :param lag: class:int, Time ahead or lagging behind
    :type ts1: list, ndarray
    :type ts2: list, ndarray
    :type lag: int
    :return: The cross-correlation of two discrete-time sequences
    :rtype: float

    :Example:

    >>> import numpy as np
    >>> ts1=np.arange(0,10)
    >>> ts2=np.arange(20,30)
    >>> xcor(ts1,ts2,2)
    0.5151515151515151

    .. note:: Reference:
        黄嘉佑. (2004). 气象统计分析与预报方法(第3版). 气象出版社. 298pp. p17
    .. warning:: ts1 and ts2 must have the same size.

    """
    if lag < 0:
        rlat = np.mean(((ts1[-lag:] - np.mean(ts1)) / np.std(ts1)) * (
                (ts2[:lag] - np.mean(ts2)) / np.std(ts2)))
    else:
        rlat = np.mean(((ts1[: - lag] - np.mean(ts1)) / np.std(ts1)) * (
                (ts2[lag:] - np.mean(ts2)) / np.std(ts2)))
    return float(rlat)


def synthetic_analysis_t_test(ts1, ts2) -> float:
    """TODO:complete it

    :param ts1: A time series
    :param ts2: A time series
    :type ts1: list, ndarray
    :type ts2: list, ndarray
    :return:
    :rtype: float

    """
    n1 = np.size(ts1)
    n2 = np.size(ts2)
    tmp1 = np.mean(ts1) - np.mean(ts2)
    tmp2 = ((n1 - 1) * np.var(ts1) + (n2 - 1) * np.var(ts2))
    tmp3 = 1 / n1 + 1 / n2
    dof = n1 + n2 - 2
    return tmp1 / (np.sqrt(tmp2 / dof * np.sqrt(tmp3)))


def causality_est(ts1, ts2, tsd, dt: int = 1, alpha=0.95):
    """TODO:complete it

    :param ts1:
    :type ts1:
    :param ts2:
    :type ts2:
    :param tsd:
    :type tsd:
    :param dt:
    :type dt:
    :param alpha:
    :type alpha:
    :return:
    :rtype:
    """
    ts1 = np.array(ts1)
    ts2 = np.array(ts2)

    dx1 = (ts1[tsd:] - ts1[:-tsd]) / (tsd * dt)
    dx2 = (ts2[tsd:] - ts2[:-tsd]) / (tsd * dt)
    N = np.size(ts1) - tsd
    x1 = ts1[:-tsd]
    x2 = ts2[:-tsd]
    C = np.cov(x1, x2)
    dc = np.ones([2, 2])
    dc[0, 0] = np.sum((x1 - np.mean(x1)) * (dx1 - np.mean(dx1)))
    dc[0, 1] = np.sum((x1 - np.mean(x1)) * (dx2 - np.mean(dx2)))
    dc[1, 0] = np.sum((x2 - np.mean(x2)) * (dx1 - np.mean(dx1)))
    dc[1, 1] = np.sum((x2 - np.mean(x2)) * (dx2 - np.mean(dx2)))
    dc = dc / (N - 1)
    detc = np.linalg.det(C)

    a11 = (C[1, 1] * dc[0, 0] - C[0, 1] * dc[1, 0]) / detc
    a12 = (-C[0, 1] * dc[0, 0] + C[0, 0] * dc[1, 0]) / detc
    T21 = C[0, 1] / C[0, 0] * (-C[1, 0] * dc[0, 0] + C[0, 0] * dc[1, 0]) / detc

    # Examination
    f1 = np.mean(dx1) - a11 * np.mean(x1) - a12 * np.mean(x2)
    R1 = dx1 - (f1 + a11 * x1 + a12 * x2)
    Q1 = np.sum(R1 ** 2)
    b1 = np.sqrt(Q1 * dt / N)

    NI = np.ones([4, 4])

    NI[0, 0] = N * dt / b1 / b1
    NI[0, 1] = dt / b1 / b1 * np.sum(x1)
    NI[0, 2] = dt / b1 / b1 * np.sum(x2)
    NI[0, 3] = 2 * dt / b1 ** 3 * np.sum(R1)

    NI[1, 1] = dt / b1 / b1 * np.sum(x1 * x1)
    NI[1, 2] = dt / b1 / b1 * np.sum(x1 * x2)
    NI[1, 3] = 2 * dt / b1 ** 3 * np.sum(R1 * x1)

    NI[2, 2] = dt / b1 / b1 * np.sum(x2 * x2)
    NI[2, 3] = 2 * dt / b1 ** 3 * np.sum(R1 * x2)

    NI[3, 3] = 3 * dt / b1 ** 4 * np.sum(R1 * R1) - N / b1 / b1

    NI[1, 0] = NI[0, 1]
    NI[2, 0] = NI[0, 2]
    NI[3, 0] = NI[0, 3]
    NI[2, 1] = NI[1, 2]
    NI[3, 1] = NI[1, 3]
    NI[3, 2] = NI[2, 3]

    invNI = np.linalg.inv(NI)
    var_a12 = invNI[2, 2]
    var_T21 = (C[0, 1] / C[0, 0]) ** 2 * var_a12
    err = np.sqrt(var_T21) * stats.norm.ppf((1 + alpha) / 2)

    return T21, err

# -*- coding: utf-8 -*-
"""
#------------------------------------------------------------------------------#
#                                                                              #
#                 Project Name : Atmosphere&Ocean                              #
#                                                                              #
#                    File Name : freedom.py                                    #
#                                                                              #
#                      Version : 0.0.1                                         #
#                                                                              #
#                  Contributor : D.CW                                          #
#                                                                              #
#                   Start Date : 2020-06-12 22:19:35                           #
#                                                                              #
#                  Last Update : 2020-06-15 21:37:54                           #
#                                                                              #
#                        Email : dengchuangwu@gmail.com                        #
#                                                                              #
#------------------------------------------------------------------------------#
# Introduction:                                                                #
# Calculation of Degrees of Freedom.                                           #
#                                                                              #
#------------------------------------------------------------------------------#
# Functions:                                                                   #
#******************************** class: TTest ********************************#
#   freedom -- A virtual static method, which is prepared for the same         #
#              method in others class to override.                             #
#                                                                              #
#******************************* class: Normal ********************************#
#   freedom -- A normal method to calculate degrees of freedom for t-test.     #
#              Usually takes the value n-2, where n is the number of valid     #
#              samples.                                                        #
#                                                                              #
#******************************** class: Pyper ********************************#
#   freedom -- A specific method to calculate degrees of freedom for t-test,   #
#              when the t-test is applied to Cross-correlation.                #
#                                                                              #
#******************************* class: LiGang ********************************#
#   freedom -- A specific method to calculate degrees of freedom for t-test,   #
#              which applies when the Cross-correlation of the data increases  #
#              due to filtering of the data.                                   #
#                                                                              #
#------------------------------------------------------------------------------#
"""

from abc import abstractmethod

import numpy as np

from .base import xcor


class TTest(object):
    @staticmethod
    @abstractmethod
    def freedom(*args):
        pass


class Normal(TTest):
    @staticmethod
    def freedom(ts1, ts2, lag: int) -> float:
        """Calculation of degrees of freedom

        A normal method to calculate degrees of freedom for t-test.Usually
        takes the value n-2, where n is the number of valid samples.

        :param ts1: A time series.
        :param ts2: A time series.
        :param lag: ts2 versus ts1 lag time
        :type ts1: list, ndarray
        :type ts2: list, ndarray
        :type lag: int
        :return: Degrees of freedom
        :rtype: float

        :Example:

        >>> import numpy as np
        >>> dof=Normal
        >>> ts1=np.arange(0,10)
        >>> ts2=np.arange(20,30)
        >>> dof.freedom(ts1,ts2,2)
        16

        """
        n = np.size(ts1)+np.size(ts2)
        dof = n - abs(lag) - 2
        return dof


class Pyper(TTest):
    @staticmethod
    def freedom(ts1, ts2, lag: int) -> float:
        """Calculation of degrees of freedom

        A specific method to calculate degrees of freedom for t-test,
        when the t-test is applied to Cross-correlation.

        :param ts1: A time series.
        :param ts2: A time series.
        :param lag: ts2 versus ts1 lag time
        :type ts1: list, ndarray
        :type ts2: list, ndarray
        :type lag: int
        :return: Degrees of freedom
        :rtype: float

        :Example:

        >>> import numpy as np
        >>> dof=Pyper
        >>> ts1=np.arange(0,10)
        >>> ts2=np.arange(20,30)
        >>> dof.freedom(ts1,ts2,2)
        1.3487738419618527

        .. note:: Reference:
            Pyper, B. J., and R. M. Peterman, 1998: Comparison of methods to account for autocorrelation in
            correlation analyses of fish data.Can. J. Fish.Aquat. Sci.,55,2127–2140.
        .. warning:: ts1 and ts2 must have the same size.

        """
        n = np.size(ts1)
        tmp = 0
        for j in range(1, n):
            tmp = tmp + (n - j) / n * (
                    _xcor(ts1, ts1, j) * _xcor(ts2, ts2, j))
        dof = 1 / (1 / n + 2 / n * tmp)
        return dof


class LiGang(TTest):
    @staticmethod
    def freedom(ts1, ts2, lag: int) -> float:
        """Calculation of degrees of freedom

        A specific method to calculate degrees of freedom for t-test,
        which applies when the Cross-correlation of the data increases due
        to filtering of the data.

        :param ts1: A time series.
        :param ts2: A time series.
        :param lag: ts2 versus ts1 lag time
        :type ts1: list, ndarray
        :type ts2: list, ndarray
        :type lag: int
        :return: Degrees of freedom
        :rtype: float

        :Example:

        >>> import numpy as np
        >>> dof=LiGang
        >>> ts1=np.arange(0,10)
        >>> ts2=np.arange(20,30)
        >>> dof.freedom(ts1,ts2,2)
        2.4615384615384612

        .. note:: Reference:
            Li, G., Li, C. Y., Tan, Y. K., & Bai, T. (2012). Principal modes of the boreal wintertime SSTA in the
            South Pacific and their relationships with the ENSO. Acta Oceanol. Sin, 34, 48-56.
        .. warning:: ts1 and ts2 must have the same size.

        """
        n = np.size(ts1)
        r1 = _xcor(ts1, ts1, 1)
        r2 = _xcor(ts2, ts2, 1)
        dof = n * ((1 - r1 * r2) / (1 + r1 * r2))
        return dof

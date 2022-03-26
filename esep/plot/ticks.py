# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : ticks.py

                   Start Date : 2022-03-25 05:24

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
# Introduction:                                                                #
# Provides the realization of various small functions for plotting.            #
#                                                                              #
#------------------------------------------------------------------------------#
# Functions:                                                                   #
#   tick_labels -- Convert to the string in appropriate format according to    #
#                  the value of the ticks for color bar.                       #
#   trans_rng -- Determine the range to be plotted based on the sequence of    #
#                dimensional variables.                                        #
#                                                                              #
#------------------------------------------------------------------------------#
-------------------------------------------------------------------------------
"""
import numpy as np


def tick_labels(cbar_tick):
    res = []
    for x in cbar_tick:
        fnum_tmp = str(x).split(".")
        if len(fnum_tmp) - 1:
            fnum = len(fnum_tmp[1])
            if fnum > 2:
                fnum = 2
        else:
            fnum = 1
        if x == 0:
            res.append(str(int(x)))
        elif -1E-2 < x < 1E-2:
            fmt = '%.' + str(fnum) + 'E'
            res.append(fmt % x)
        elif -1000 <= x <= 1000:
            fmt = '%.' + str(fnum) + 'f'
            res.append(fmt % x)
        else:
            fmt = '%.' + str(fnum) + 'E'
            res.append(fmt % x)
    return res


def adjust_cbar_tick(cbar, level):
    cbar_tick = np.linspace(min(level), max(level), 7)
    cbar_tick_labels = tick_labels(cbar_tick)
    cbar.set_ticks(cbar_tick)
    cbar.set_ticklabels(cbar_tick_labels)


class TickLabels(object):
    def __init__(self, ticks, decimal_num=None, max_val: int = 10000,
                 min_val: float = 0.1):
        """Convert to the string in appropriate format according to the value of
        the ticks for color bar.

        :param decimal_num: 保留的小数点位数
        :param ticks: class:list, the list of the ticks in color bar.
        :return: the list of string which is prepared to plot in color bar.

        """
        self.ticks = ticks
        self.decimal_num = decimal_num
        self.max_val = max_val
        self.min_val = min_val

    def tick_format(self):
        """
        :return: the list of string which is prepared to plot in color bar.
        """
        result = []
        for tick in self.ticks:
            if tick % 1 == 0:
                result.append(self.int_format(tick))
                continue
            result.append(self.float_format(tick))
        return result

    def int_format(self, tick):
        if tick == 0:
            return int(tick)
        decimal_num = self.decimal_num
        if decimal_num is None:
            digits_num = int(math.log10(abs(tick)))
            decimal_num = _get_decimal_num(tick / 10 ** digits_num)
        if tick > self.max_val:
            return ('%.{}E'.format(decimal_num)) % tick
        return int(tick)

    def float_format(self, tick):
        decimal_num = self.decimal_num
        if decimal_num is None:
            decimal_num = _get_decimal_num(tick)
        if -self.max_val <= tick <= -self.min_val or self.min_val <= tick <= self.max_val:
            return ('%.' + str(decimal_num) + 'f') % tick
        return ('%.' + str(decimal_num) + 'E') % tick


def _get_decimal_num(tick):
    split_tick = str(tick).split(".")
    if not (len(split_tick) - 1) or tick % 1 == 0:
        return 0
    decimal_num = len(split_tick[1])
    if decimal_num > 2:
        decimal_num = 2
    return decimal_num


def tick_labels(cbar_ticks: list) -> list:
    """Convert to the string in appropriate format according to the value of
    the ticks for color bar.

    :param cbar_ticks: class:list, the list of the ticks in color bar.
    :type cbar_ticks: list
    :return: the list of string which is prepared to plot in color bar.
    :rtype: list

    :Example:

    >>> tick_labels([-1001,-1000,-0.002,-0.001,0,0.001,0.002,1000,1001])
    ['-1.0E+03','-1000.0','-2.00E-03','-1.00E-03','0','1.00E-03','2.00E-03','1000.0','1.0E+03']

    """
    rslt = []
    for cbar_tick in cbar_ticks:
        tmp_fnum = str(cbar_tick).split(".")
        if len(tmp_fnum) - 1:
            fnum = len(tmp_fnum[1])
            if fnum > 2:
                fnum = 2
        else:
            fnum = 1
        if cbar_tick == 0:
            rslt.append(str(int(cbar_tick)))
        elif -1E-2 < cbar_tick < 1E-2:
            fmt = "%." + str(fnum) + "E"
            rslt.append(fmt % cbar_tick)
        elif -1000 <= cbar_tick <= 1000:
            fmt = "%." + str(fnum) + "f"
            rslt.append(fmt % cbar_tick)
        else:
            fmt = "%." + str(fnum) + "E"
            rslt.append(fmt % cbar_tick)
    return rslt


def tick_labels(cbar_ticks: list) -> list:
    """Convert to the string in appropriate format according to the value of
    the ticks for color bar.

    :param cbar_ticks: class:list, the list of the ticks in color bar.
    :type cbar_ticks: list
    :return: the list of string which is prepared to plot in color bar.
    :rtype: list

    :Example:

    >>> tick_labels([-1001,-1000,-0.002,-0.001,0,0.001,0.002,1000,1001])
    ['-1.0E+03','-1000.0','-2.00E-03','-1.00E-03','0','1.00E-03','2.00E-03','1000.0','1.0E+03']

    """
    rslt = []
    for cbar_tick in cbar_ticks:
        tmp_fnum = str(cbar_tick).split(".")
        if len(tmp_fnum) - 1:
            fnum = len(tmp_fnum[1])
            if fnum > 2:
                fnum = 2
        else:
            fnum = 1
        if cbar_tick == 0:
            rslt.append(str(int(cbar_tick)))
        elif -1E-2 < cbar_tick < 1E-2:
            fmt = '%.' + str(fnum) + 'E'
            rslt.append(fmt % cbar_tick)
        elif -1000 <= cbar_tick <= 1000:
            fmt = '%.' + str(fnum) + 'f'
            rslt.append(fmt % cbar_tick)
            # TODO:If the decimal is zero, then converting it to an integer.
        else:
            fmt = '%.' + str(fnum) + 'E'
            rslt.append(fmt % cbar_tick)
    return rslt


def trans_rng(seq) -> tuple:
    """Determine the range to be plotted based on the sequence of
    dimensional variables.

    :param seq: class:ndarray, The sequence of dimensional variables.
    :type seq: list, ndarray
    :return: The range to be plotted with a fixed format. (min,max)
    :rtype: tuple

    :Example:

    >>> trans_rng([-80,1,2,3,4,5,90])
    (-80, 90)
    >>> import numpy as np
    >>> a = np.linspace(-180,180,10)
    >>> trans_rng(a)
    (-180.0, 180.0)

    """
    min_val = np.min(seq)
    max_val = np.max(seq)
    return min_val, max_val

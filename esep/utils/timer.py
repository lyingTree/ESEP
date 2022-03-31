# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : timer.py

                   Start Date : 2022-03-25 05:18

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

utils for processing time data

-------------------------------------------------------------------------------
#****************************** class: TimeUtil ******************************#
#   get_base_time -- Get the base time of a file object.                      #
#   get_time -- Get the corresponding sequence of moments from the base time  #
#               and the interval time list.                                   #
#   num_time2datetime -- Convert numeric time values to datetime instance.    #
#-----------------------------------------------------------------------------#
"""
from datetime import datetime
from typing import *

import numpy as np
from dateutil.relativedelta import relativedelta
from netCDF4 import num2date, Variable


class TimeUtil:
    def __init__(self):
        pass

    @staticmethod
    def get_base_time(t: Variable, output_interval_units=False) -> Union[datetime, tuple]:
        """获取netcdf文件的基准时间以及时间单位
        Created date: 2020-06-03 19:48:16
        Last modified date: 2020-06-04 17:19:31
        Contributor: D.CW
        Email: dengchuangwu@gmail.com

        Args:
            t: The time variable in netCDF4
            output_interval_units: Whether output the unit of interval, e.g. Seconds, Minutes, Hours

        Returns:
            The base time of the time variable

        """
        tmp_str = t.units
        try:
            time_split = tmp_str.split(' ')
            std_time_str = ' '.join((time_split[-2], time_split[-1]))
            base_time = datetime.strptime(std_time_str[:19], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            time_split = tmp_str.split(' ')
            std_time_str = time_split[-1]
            base_time = datetime.strptime(std_time_str, '%Y-%m-%d')
        if output_interval_units:
            return base_time, time_split[0]
        else:
            return base_time

    @staticmethod
    def get_time(base_time: datetime, interval_units: str, interval_ls: Union[list, np.ndarray]) -> list:
        """基于某一个时刻(base_time)，根据一维的相对时间间隔列表(invls)、数组，转化为对应时间的datetime列表
        Created date: 2020-06-03 19:47:17
        Last modified date: 2020-06-04 18:30:15
        Contributor: D.CW
        Email: dengchuangwu@gmail.com

        Args:
            base_time: The base time
            interval_units: The unit of interval
            interval_ls: A 1D arrays and lists of intervalsdatetime list of reference base time

        Returns:
            datetime list of reference base time intervals

        """
        interval_units = interval_units.lower()
        ret = []
        if len(np.shape(interval_ls)) > 1:
            raise TypeError('时间间隔只允许一维或单个数值')

        valid_units = ['microsecond', 'second', 'minute', 'hour', 'day', 'week', 'month', 'year']
        if interval_units in valid_units:
            interval_units += 's'
        elif interval_units[:-1] in valid_units:
            pass
        else:
            raise TypeError('时间间隔单位字符串错误')

        for interval in interval_ls:
            ret.append(base_time + relativedelta(**{interval_units: +int(interval)}))

        return ret

    @staticmethod
    def extract_common_time_idx(d1: Union[list, np.ndarray], d2: Union[list, np.ndarray], lim_start=None,
                                lim_end=None) -> tuple:
        d1, d2 = np.array(d1), np.array(d2)
        start_time = d1[0] if d1[0] > d2[0] else d2[0]
        end_time = d1[-1] if d1[-1] < d2[-1] else d2[-1]

        if d1[0] > d2[0]:
            for dt in d1:
                if dt in d2:
                    start_time = dt
                    break
        else:
            for dt in d2:
                if dt in d1:
                    start_time = dt
                    break

        if d1[-1] < d2[-1]:
            for dt in d1[::-1]:
                if dt in d2:
                    end_time = dt
                    break
        else:
            for dt in d2[::-1]:
                if dt in d1:
                    end_time = dt
                    break
        if lim_start is not None:
            start_time = lim_start
        if lim_end is not None:
            end_time = lim_end
        obs_idx = np.where(np.logical_and(start_time <= d1, d1 <= end_time))[0]
        model_idx = np.where(np.logical_and(start_time <= d2, d2 <= end_time))[0]
        return obs_idx, model_idx

    @staticmethod
    def num_time2datetime(t, units: str = None, calendar: str = None) -> datetime:
        """ Convert numeric time values to datetime instance.

        The returned datetime objects represent UTC with no time-zone offset.

        :param t: A time object or numeric time values.
        :param units: a string of the form <time units> since <reference time>
            describing the time units. <time units> can be days, hours, minutes,
            seconds, milliseconds or microseconds. <reference time> is the time
            origin. months_since is allowed only for the 360_day calendar.
        :type units: str
        :param calendar: describes the calendar used in the time calculations.
            All the values currently defined in the Valid calendars ‘standard’,
            ‘gregorian’, ‘proleptic_gregorian’ ‘noleap’, ‘365_day’, ‘360_day’,
            ‘julian’, ‘all_leap’, ‘366_day’. Default is ‘standard’, which is a
            mixed Julian/Gregorian calendar.
        :type calendar: str
        :return: a datetime instance, or an array of datetime instances with
            approximately 100 microsecond accuracy.

        .. warning:: The datetime objects must be in UTC with no time-zone offset.
            If there is a time-zone offset in units, it will be applied to the
            returned numeric values.
        """
        if units is None:
            if hasattr(t, 'units'):
                units = t.units
            else:
                raise ValueError('Please assign a string to the units.')
        if calendar is None:
            if hasattr(t, 'calendar'):
                calendar = t.calendar
            else:
                calendar = 'standard'
        return num2date(t, units=units, calendar=calendar)

    @staticmethod
    def obj2datetime(dt_raw: Union[str, datetime]) -> datetime:
        if isinstance(dt_raw, datetime):
            return dt_raw
        dt_raw = str(dt_raw)
        dt_len = len(dt_raw)
        if dt_len == 5:
            return datetime.strptime(dt_raw, '%H:%M')
        elif dt_len == 8:
            try:
                return datetime.strptime(dt_raw, '%H:%M:%S')
            except ValueError:
                return datetime.strptime(dt_raw, '%d %H:%M')
        elif dt_len == 11:
            try:
                return datetime.strptime(dt_raw, '%d %H:%M:%S')
            except ValueError:
                return datetime.strptime(dt_raw, '%m-%d %H:%M')
        elif dt_len == 14:
            return datetime.strptime(dt_raw, '%m-%d %H:%M:%s')
        else:
            return datetime.strptime(dt_raw, '%Y-%m-%d %H:%M:%s')

    @staticmethod
    def nc_time_var2str(t) -> tuple:
        """将NetCDF数据文件中的 时间变量数组 转为 UTC字符串元组

        Args:
            t: The time variable in netCDF4

        Returns:
            UTC字符串元组
        """
        time_str_ls = ['' for _ in range(len(t))]
        calendar = None
        time_units = 'seconds since 1970-01-01 00:00:00'
        if hasattr(t, 'calendar'):
            calendar = getattr(t, 'calendar')
        if hasattr(t, 'units'):
            time_units = getattr(t, 'units')
        time_var_date_fmt = num2date(t[:], time_units) if calendar is None else num2date(t[:], time_units, calendar)
        for idx, t in enumerate(time_var_date_fmt):
            time_str_ls[idx] = t.strftime("%Y-%m-%d %H:%M:%SZ")
        return tuple(time_str_ls)

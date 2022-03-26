# -*- coding:utf-8 -*-
"""
--------------------------------------------------------------------------------
                                                                              
                    File Name : string.py

                   Start Date : 2021-09-05 09:08

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

--------------------------------------------------------------------------------
Introduction:

字符串处理函数集

--------------------------------------------------------------------------------
"""
import time

from netCDF4 import num2date


def delete_space(row_str):
    return re.sub('\n+', '', re.sub(' +', '', row_str))


def str2var_name(string: str, default_missing_prefix='var'):
    string = ''.join(filter(lambda x: x in [' '] or x.isalnum(), string)).strip().replace(' ', '_')
    tmp_name = '_'.join([default_missing_prefix, str(int(round(time.time() * 1000)))])
    flag = False
    while True:
        if string[0].isdigit():
            if not (len(string) - 1):
                flag = True
                break
            string = string[1:]
            continue
        break
    if flag:
        var_name = tmp_name
    else:
        var_name = string
    return var_name

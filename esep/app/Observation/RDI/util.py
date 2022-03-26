# -*- coding:uft-8 -*-
import re
from datetime import datetime, timedelta

import numpy as np


def get_val_from_str(string: str, only_first=True):
    ret = re.findall(
        r'\d*/{0,1}\d*/{0,1}\d* {0,1}\d+:\d+:{0,1}\d*:{0,1}\d*\.\d*', string)
    if ret:
        return ret[0].strip()
    else:
        return get_num_from_str(string, only_first)


def get_num_from_str(string: str, only_first=True):
    if only_first:
        ret = re.findall(r'[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*', string)[0]
        if is_int_str(ret):
            ret = int(ret)
        else:
            ret = float(ret)
    else:
        tmp = re.findall(r'[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*', string)
        ret = []
        for it in tmp:
            if is_int_str(it):
                ret.append(int(it))
            else:
                ret.append(float(it))
    return ret


def is_int_str(string: str):
    if re.findall(r'', string):
        return False
    else:
        return True


def detect_beam_index(filepath: str):
    tmp = filepath.split('/')
    tmp = tmp[-1].split('\\')
    tmp = tmp[-1].split('.')
    ret = re.findall(r'\d', tmp[0])
    return int(ret[-1])


def detect_data_idx(cor, less=False, is_end=False, axis=0):
    cor_ave = np.mean(cor[:, :3], axis=1)
    ave = np.mean(cor_ave)
    scale = (-1) ** less
    scale2 = (-1) ** is_end
    flag1 = False
    flag2 = False
    shp = np.shape(cor_ave)
    if is_end:
        tmp = range(shp[axis] - 1, 0, -1)
    else:
        tmp = range(shp[axis] - 1)
    for i in tmp:
        if cor[i + scale2] * scale < cor[i] * scale:
            flag1 = True
        if flag1 and cor[i + scale2] * scale > cor[i] * scale:
            flag2 = True
        if flag1 and flag2 and cor[i] - ave < 10:  # %0.1
            return i


def type_detect(value):
    if isinstance(value, str):
        return 'S1'
    elif isinstance(value, float):
        return 'f4'
    elif isinstance(value, int):
        return 'i4'
    elif isinstance(value, (list, tuple)):
        return 'f8'
    elif isinstance(value, np.ndarray):
        if value.dtype == np.int64:
            return 'i8'
        elif value.dtype == np.int32:
            return 'i4'
        elif value.dtype == np.int16:
            return 'i2'
        elif value.dtype == np.int8:
            return 'i1'
        elif value.dtype == np.uint64:
            return 'u8'
        elif value.dtype == np.uint32:
            return 'u4'
        elif value.dtype == np.uint16:
            return 'u2'
        elif value.dtype == np.uint8:
            return 'u1'
        elif value.dtype == np.float64:
            return 'f8'
        elif value.dtype == np.float32:
            return 'f4'
        elif value.dtype == np.str:
            return 'S1'
        else:
            return 'f8'
    else:
        raise ValueError('Invalid type')


def gen_time(mat_data, time_offset):
    time = []
    hh = mat_data['SerHour'][:, 0].tolist()
    mm = mat_data['SerMin'][:, 0].tolist()
    ss = mat_data['SerSec'][:, 0].tolist()
    us = (mat_data['SerHund'][:, 0].astype(int) * 10000).tolist()
    if 'SerYear' in mat_data and 'SerMon' in mat_data and 'SerDay' in mat_data:
        # The year data has only two digits, and pandas.to_datetime can't
        # be used directly. The format of the year data to be matched is %Y.
        yy = (mat_data['SerYear'] + 2000)[:, 0].tolist()
        mon = mat_data['SerMon'][:, 0].tolist()
        dd = mat_data['SerDay'][:, 0].tolist()
        for i in range(len(yy)):
            time.append(
                req_datetime(yy[i], mon[i], dd[i], hh[i], mm[i], ss[i], us[i],
                             time_offset))
    else:
        tmp_date = ''.join(['20', mat_data['RDIEnsDate']])
        tmp_date = datetime.strptime(tmp_date, '%Y/%m/%d')
        time.append(
            req_datetime(tmp_date.year, tmp_date.month, tmp_date.day, hh[0],
                         mm[0], ss[0], us[0], time_offset))
        for i in range(1, len(hh)):
            if i == 0:
                time.append(
                    req_datetime(tmp_date.year, tmp_date.month, tmp_date.day,
                                 hh[i], mm[i], ss[i], us[i], time_offset))
            else:
                if hh[i] < hh[i - 1]:
                    tmp_date = tmp_date + timedelta(days=1)
                time.append(
                    req_datetime(tmp_date.year, tmp_date.month, tmp_date.day,
                                 hh[i], mm[i], ss[i], us[i], time_offset))
    return time


def req_datetime(yy, mon, dd, hh, mm, ss, us, time_offset):
    return datetime(year=yy, month=mon, day=dd, hour=hh, minute=mm, second=ss,
                    microsecond=us) + timedelta(hours=time_offset)

# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : get_obs_data.py

                   Start Date : 2021-10-08 11:53

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

各类观测数据的读取与预处理

-------------------------------------------------------------------------------
"""

import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pint

from ESEP.esep.reader.general import ExcelReader, TxtReader
from ESEP.esep.utils.string import delete_space
from ESEP.esep.utils.timer import TimeUtil

ureg = pint.UnitRegistry()


class ObsData(ExcelReader, TxtReader):
    def __init__(self, fp):
        tmp = Path(fp)
        if tmp.suffix in ['.csv', '.xls', '.xlsx']:
            ExcelReader.__init__(self, fp)
        else:
            TxtReader.__init__(self, fp)

    def flow_vel_dir_statements_fixed_point_station(self, stations: list):
        def _get_scale():
            speed_unit = 'm/s'
            direction_unit = 'degree'
            depth_unit = 'm'
            for row_idx, row in df.iterrows():
                row_str = delete_space(','.join(filter(lambda x: isinstance(x, str), row.values)))

                if '单位' in row_str:
                    speed_unit = row_str[row_str.find('流速') + 3:row_str.find('流向') - 1].lower()
                    direction_unit = row_str[row_str.find('流向') + 3:row_str.find('水深') - 1].lower()
                    depth_unit = row_str[row_str.find('水深') + 3:-1].lower()
                    break

                if '表层,0.2H,0.4H,0.6H,0.8H,底层,垂线' in row_str:
                    tmp_ls = row.tolist()
                    depth_col_idx = 2
                    speed_col_idx = 3
                    direction_col_idx = 4
                    for tmp_idx, tmp in enumerate(tmp_ls):
                        if not isinstance(tmp, str):
                            continue

                        if '水深' == re.sub('\n+', '', re.sub(' +', '', tmp)):
                            depth_col_idx = tmp_idx

                        if '表层' == re.sub('\n+', '', re.sub(' +', '', tmp)):
                            speed_col_idx = tmp_idx
                            direction_col_idx = tmp_idx + 1

                    def extract_unit(tmp_row_idx, tmp_col_idx, data_type='流速'):
                        tmp_row_str = delete_space(df.loc[tmp_row_idx + 1, tmp_col_idx])
                        sub_str_idx = tmp_row_str.find(data_type) + 3 if len(data_type) else 1
                        return tmp_row_str[sub_str_idx:-1].lower()

                    speed_unit = extract_unit(row_idx, speed_col_idx, data_type='流速')
                    direction_unit = extract_unit(row_idx, direction_col_idx, data_type='流向')
                    depth_unit = extract_unit(row_idx, depth_col_idx, data_type='')
                    break

            if direction_unit in ['o', '0', 'O', '°']:
                direction_unit = 'degree'
            speed_trans = 1 * ureg(speed_unit).to('m/s')
            direction_trans = 1 * ureg(direction_unit).to('degree')
            depth_trans = 1 * ureg(depth_unit).to('m')
            return speed_trans, direction_trans, depth_trans

        def _get_data_array(sscale, dscale, depscale):
            start_date = datetime.utcnow()
            start_date_detected_flag = False
            data_row_idx_detected_flag = False
            data_row_idx = 0
            data_dict = {'表层': {'流速': [], '流向': []}, '0.2H': {'流速': [], '流向': []}, '0.4H': {'流速': [], '流向': []},
                         '0.6H': {'流速': [], '流向': []}, '0.8H': {'流速': [], '流向': []}, '底层': {'流速': [], '流向': []},
                         '垂线': {'流速': [], '流向': []}, '水深': [], '时间': []}
            data_idx = {}
            for row_idx, row in df.iterrows():
                if start_date_detected_flag and data_row_idx_detected_flag:
                    break
                tmp_row = filter(lambda x: isinstance(x, str), row.values)
                for col_str in tmp_row:
                    tmp_col_str = delete_space(col_str)
                    if '观测日期' in tmp_col_str:
                        tmp = [int(x) for x in re.findall(r'\d+', tmp_col_str)]
                        start_date = datetime(tmp[0], tmp[1], tmp[2])
                        start_date_detected_flag = True
                        break

                tmp_row_str = delete_space(','.join(filter(lambda x: isinstance(x, str), row.values)))
                if '表层,0.2H,0.4H,0.6H,0.8H,底层,垂线' in tmp_row_str:
                    data_row_idx = row_idx + 2
                    tmp_row = list(map(lambda x: delete_space(x) if isinstance(x, str) else x, row.values))
                    for key in data_dict:
                        for col_idx, col_name in enumerate(tmp_row):
                            if isinstance(col_name, str) and key in col_name:
                                data_idx[key] = col_idx
                    data_row_idx_detected_flag = True

            for row_data in df.itertuples():
                if row_data.Index < data_row_idx:
                    continue
                for key in data_dict:
                    if key == '水深':
                        data_dict[key].append(row_data[data_idx[key] + 1] * depscale)
                    elif key == '时间':
                        data_dict[key].append(TimeUtil().num_time2datetime(row_data[1]))
                    else:
                        data_dict[key]['流速'].append(row_data[data_idx[key] + 1] * sscale)
                        data_dict[key]['流向'].append(row_data[data_idx[key] + 1 + 1] * dscale)
            return data_dict

        for station in stations:
            df = self.reader(self.fp, sheet_name=station, header=None)
            speed_scale, direction_scale, depth_scale = _get_scale()
            data_dict = _get_data_array(speed_scale, direction_scale, depth_scale)
            return data_dict


def get_tide_station_info(obs_path='./OBS_DATA', row_idx=0, col_idx=4):
    # get obs station info (name,lon,lat)
    obs_path = Path(obs_path)
    obs_name = get_filename(obs_path, '.xlsx')
    obs_fp = get_filename(obs_path, '.xlsx')
    obs_lon = np.ones(len(obs_name))
    obs_lat = np.ones(len(obs_name))
    for idx, name in enumerate(obs_name):
        obs_fp[idx] = obs_path.joinpath(name + '.xlsx')
        df = pd.read_excel(obs_fp[idx])
        obs_info = df.values[row_idx, col_idx]
        str1 = '（'
        str2 = '）'
        obs_name[idx] = obs_info[:obs_info.index(str1)][3:]
        obs_info = obs_info[obs_info.index(str1):obs_info.index(str2)]
        obs_info = re.findall(r'\d+', obs_info)
        obs_lon[idx] = float(obs_info[0]) + float(obs_info[1]) / 60 + float(obs_info[2]) / 3600 + float(obs_info[3]) / (
            3600 * 10)
        obs_lat[idx] = float(obs_info[4]) + float(obs_info[5]) / 60 + float(obs_info[6]) / 3600 + float(obs_info[7]) / (
            3600 * 10)

    # 观测点经纬度
    obs_coordinate = {
        obs_name[0]: [obs_lon[0], obs_lat[0]],
        obs_name[1]: [obs_lon[1], obs_lat[1]],
        obs_name[2]: [obs_lon[2], obs_lat[2]],
        obs_name[3]: [obs_lon[3], obs_lat[3]],
        obs_name[4]: [obs_lon[4], obs_lat[4]],
        obs_name[5]: [obs_lon[5], obs_lat[5]],
    }
    return obs_coordinate, obs_fp


def get_sediment_station_info(obs_path='./OBS_DATA', row_idx=0, col_idx=4, sheet_name=None):
    obs_path = Path(obs_path)
    obs_name = get_filename(obs_path, '.xlsx')
    obs_fp = get_filename(obs_path, '.xlsx')
    obs_lon = np.ones(len(obs_name))
    obs_lat = np.ones(len(obs_name))
    for idx, name in enumerate(obs_name):
        obs_fp[idx] = obs_path.joinpath(name + '.xlsx')
        df = pd.read_excel(obs_fp[idx], sheet_name=sheet_name)
        obs_info = df.values[row_idx, col_idx]
        str1 = '（'
        str2 = '）'
        obs_name[idx] = obs_info[:obs_info.index(str1)][3:]
        obs_info = obs_info[obs_info.index(str1):obs_info.index(str2)]
        obs_info = re.findall(r'\d+', obs_info)
        obs_lon[idx] = float(obs_info[0]) + float(obs_info[1]) / 60 + float(obs_info[2]) / 3600 + float(obs_info[3]) / (
            3600 * 10)
        obs_lat[idx] = float(obs_info[4]) + float(obs_info[5]) / 60 + float(obs_info[6]) / 3600 + float(obs_info[7]) / (
            3600 * 10)

    return obs_name[0], obs_lon[0], obs_lat[0]


def get_filename(dir_path, filetype):
    name = []
    for fp in dir_path.iterdir():
        if fp.suffix == filetype:
            name.append(fp.stem)
    return name


def get_obs_tide_data(filepath):
    df1 = pd.read_excel(filepath)
    y_m = df1.values[0, 0]
    y_m = re.findall(r'\d+', y_m)
    df2 = pd.read_excel(filepath, skiprows=4)
    data_val = df2.values[:-3, :-10]
    dd = data_val[:, 0]
    yy = y_m[0]
    data_time = []
    for idx, days in enumerate(dd):
        if days >= dd[0]:
            mm = y_m[1]
        else:
            mm = y_m[2]
        for hh in range(24):
            data_time_str = ''.join([yy, '-', mm, '-', str(days), ' ', str(hh), ':', '00'])
            data_time.append(datetime.strptime(data_time_str, '%Y-%m-%d %H:%M'))
    data_time = np.array([x for x in data_time])
    # get tide level
    tide_data = data_val[:, 3:]
    [x, y] = tide_data.shape
    tide_data = tide_data.reshape(x * y) / 100
    tide_data = np.array([x for x in tide_data])
    return data_time, tide_data


def get_obs_data(filepath, sta_name, lev_name, merge=True, tt_idx=0):
    sheet_name = []
    for tide_type in ['-小潮', '-大潮']:
        sheet_name.append(sta_name + tide_type)
    df1 = pd.read_excel(filepath, sheet_name=sheet_name[0], skiprows=4)
    df2 = pd.read_excel(filepath, sheet_name=sheet_name[1], skiprows=4)

    if merge:
        data_val = np.append(df1.values[:-1, :], df2.values[:-1, :], axis=0)
    else:
        data_val = df2.values[:-1, :] if tt_idx else df1.values[:-1, :]

    date_ls = data_val[:, 0]
    time = data_val[:, 1]
    data_time_str = []
    data_time = []
    for idx, dt in enumerate(date_ls):
        data_time_str.append(dt.strftime('%Y-%m-%d') + ' ' + time[idx].strftime('%H:%M'))
        data_time.append(datetime.strptime(data_time_str[idx], '%Y-%m-%d %H:%M'))
    if lev_name == 'surface':
        obs_col_idx = 3
    elif lev_name == 'middle':
        obs_col_idx = 7
    elif lev_name == 'bottom':
        obs_col_idx = 13
    else:
        obs_col_idx = 15
    obs_cs_data = data_val[:, obs_col_idx]
    obs_dir_data = data_val[:, obs_col_idx + 1]
    obs_depth = data_val[:, 3]
    data_time = np.array(data_time)
    return obs_cs_data, obs_dir_data, data_time, obs_depth


def get_obs_data_sediment(filepath, sta_name, lev_name, merge=True, tt_idx=0):
    sheet_name = []
    for tide_type in ['-小潮', '-大潮']:
        sheet_name.append(sta_name + tide_type)
    df1 = pd.read_excel(filepath, sheet_name=sheet_name[0], skiprows=4)
    df2 = pd.read_excel(filepath, sheet_name=sheet_name[1], skiprows=4)

    if merge:
        data_val = np.append(df1.values[:-1, :], df2.values[:-1, :], axis=0)
    else:
        data_val = df2.values[:-1, :] if tt_idx else df1.values[:-1, :]

    date_ls = data_val[:, 0]
    time = data_val[:, 1]
    data_time_str = []
    data_time = []
    for idx, dt in enumerate(date_ls):
        data_time_str.append(dt.strftime('%Y-%m-%d') + ' ' + time[idx].strftime('%H:%M'))
        data_time.append(datetime.strptime(data_time_str[idx], '%Y-%m-%d %H:%M'))
    if lev_name == 'surface':
        obs_col_idx = 3
    elif lev_name == 'middle':
        obs_col_idx = 6
    elif lev_name == 'bottom':
        obs_col_idx = 8
    else:
        obs_col_idx = 9
    obs_data = data_val[:, obs_col_idx]
    obs_depth = data_val[:, 2]
    data_time = np.array(data_time)
    return obs_data, data_time, obs_depth

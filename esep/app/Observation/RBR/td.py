# -*- coding:uft-8 -*-
import json
from datetime import datetime, timedelta
from os import path

import numpy as np
import pandas as pd
from more_itertools import chunked
from netCDF4 import Dataset, date2num
from yaml import full_load

from .util import create_meta_grp, offset_from_utc
from ..util import time_round, SegmentOperate, correct0drift, \
    extract_valid_time


def cut_time(data_path, save_path, vdd, zlib, complevel):
    return extract_valid_time(data_path, save_path, 'Average Data Group', vdd,
                              zlib, complevel)


def convert2nc(td_path, save_path, time_win, time_units, calendar, sta_info,
               vdd, time_offset=None, corr0drift=True, zlib=False, complevel=1,
               author='DengCW', email='dengchuangwu@gmail.com'):
    this_file_dir = path.split(path.abspath(__file__))[0]
    td_conf = full_load(open('/'.join([this_file_dir, 'config.yml'])))
    variables = td_conf['TD']['variables']
    lon = sta_info['lon']
    lat = sta_info['lat']
    # <editor-fold desc='DATA READING'>
    data = pd.read_csv(td_path + '_data.txt')
    with open(td_path + '_metadata.txt', 'r') as f:
        meta = json.load(f)
    var_data = {}
    for name, abbr in variables.items():
        var_data[abbr] = data[name].to_numpy()
    # </editor-fold>

    # <editor-fold desc='DATA PROCESSING'>

    # <editor-fold desc="Convert the data time to East 8 time zone">
    time_offset_check = offset_from_utc(meta)
    if time_offset is None:
        if not time_offset_check[0]:
            raise ValueError(
                'You need to fill in time_offset in the TD_info node in the '
                'Preprocess module in the configuration file')
        else:
            time_offset = 8 - time_offset_check[1]
    else:
        time_offset = 8 - time_offset
    tmp_time = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f') + timedelta(
        hours=time_offset) for x in data['Time']]
    # </editor-fold>

    time = date2num(tmp_time, time_units, calendar)
    delta = time[1] - time[0]
    ave_len = int(time_win * 60 * 1E3 / delta)
    time_ave = [np.nanmean(x) for x in chunked(time, ave_len)]
    time_ave = time_round(time_ave, time_units, calendar)
    var_ave_data = {}
    for name, abbr in variables.items():
        var_ave_data[abbr] = SegmentOperate(var_data[abbr], ave_len).value
    if 'dep' in var_ave_data and corr0drift:
        var_ave_data['dep'] = var_ave_data['dep'] - correct0drift(
            var_ave_data['dep'], vdd)
    # </editor-fold>

    # <editor-fold desc='OUTPUT'>
    td2nc(save_path, lon, lat, time, time_units, calendar, time_ave, time_win,
          meta, var_data, var_ave_data, variables, zlib, complevel, author,
          email)

    return True, None


def td2nc(save_path, lon, lat, time, time_units, calendar, time_ave=None,
          time_win=None, meta=None, data=None, data_ave=None, variables=None,
          zlib=False, complevel=1, author='DengCW',
          email='dengchuangwu@gmail.com'):
    out_file = Dataset(save_path, 'w')
    # <editor-fold desc='create dimensions'>
    out_file.createDimension('time', len(time))
    out_file.createDimension('lon', 1)
    out_file.createDimension('lat', 1)
    # </editor-fold>

    # <editor-fold desc='global attributes'>
    out_file.setncattr('Author', author)
    out_file.setncattr('Email', email)
    if meta is not None:
        create_meta_grp(out_file, meta)
    # </editor-fold>

    # <editor-fold desc='create variables'>

    # --------------------------------------------------------------------------
    # <editor-fold desc='Longitude and Latitude'>
    var_lon = out_file.createVariable('lon', 'f4', 'lon', zlib=zlib,
                                      complevel=complevel)
    var_lat = out_file.createVariable('lat', 'f4', 'lat', zlib=zlib,
                                      complevel=complevel)
    var_lon.units = 'degrees_east'
    var_lon.long_name = 'longitude'
    var_lat.units = 'degrees_north'
    var_lat.long_name = 'latitude'
    out_file.variables['lon'][:] = lon
    out_file.variables['lat'][:] = lat
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Time'>
    var_time = out_file.createVariable('time', 'f8', 'time', zlib=zlib,
                                       complevel=complevel)
    var_time.units = time_units
    var_time.calendar = calendar
    out_file.variables['time'][:] = time
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Variables'>
    if data is not None:
        for name, abbr in variables.items():
            var_tmp = out_file.createVariable(abbr, 'f8', 'time', zlib=zlib,
                                              complevel=complevel)
            var_tmp.units = out_file['Meta Group']['dataheader'][
                ' '.join([name, 'Meta Group'])].units
            var_tmp.long_name = ' '.join(
                ['The', name.lower(), 'measured from the RBR CTD'])
            out_file.variables[abbr][:] = data[abbr]
    # </editor-fold>
    # --------------------------------------------------------------------------
    if time_ave is None:
        out_file.close()
        return True, None
    ave_data_grp = out_file.createGroup('Average Data Group')
    ave_data_grp.createDimension('time', len(time_ave))
    time_win = str(time_win)
    # --------------------------------------------------------------------------
    # <editor-fold desc='Average Time'>
    var_time_ave = ave_data_grp.createVariable('time', 'f8', 'time', zlib=zlib,
                                               complevel=complevel)
    var_time_ave.units = time_units
    var_time_ave.calendar = calendar
    ave_data_grp.variables['time'][:] = time_ave
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Average Variables'>
    if data_ave is not None:
        for name, abbr in variables.items():
            var_tmp = ave_data_grp.createVariable(abbr, 'f8', 'time', zlib=zlib,
                                                  complevel=complevel)
            var_tmp.units = out_file['Meta Group']['dataheader'][
                ' '.join([name, 'Meta Group'])].units
            var_tmp.long_name = " ".join(["The", name.lower(),
                                          "measured from the RBR's TD is "
                                          "averaged every",
                                          time_win, "minutes"])
            ave_data_grp.variables[abbr][:] = data_ave[abbr]
    # </editor-fold>
    # -------------------------------------------------------------------------

    # </editor-fold>

    # <editor-fold desc='POST-PROCESSING'>
    # Clear data, memory space, windows, etc.
    out_file.close()
    # </editor-fold>
    return True, None

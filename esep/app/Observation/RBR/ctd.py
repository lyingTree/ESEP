# -*- coding:uft-8 -*-
import json
from datetime import datetime, timedelta
from os import path

import numpy as np
from netCDF4 import Dataset, date2num
from pandas import read_csv
from yaml import full_load

from .util import create_meta_grp, offset_from_utc


def convert2nc(ctd_path, save_path, time_units, calendar, sta_info, bin_size,
               ref_dep, ref_time, time_offset=None, zlib=False, complevel=1,
               author='DengCW', email='dengchuangwu@gmail.com'):
    this_file_dir = path.split(path.abspath(__file__))[0]
    ctd_conf = full_load(open('/'.join([this_file_dir, 'config.yml'])))
    variables = ctd_conf['CTD']['variables']
    lon = sta_info['lon']
    lat = sta_info['lat']
    # <editor-fold desc='DATA READING'>
    updown = read_csv(''.join([ctd_path + '_annotations_profile.txt']))
    data = read_csv(''.join([ctd_path + '_data.txt']))

    with open(ctd_path + '_metadata.txt', 'r') as f:
        meta = json.load(f)

    var_data = {}
    for name, abbr in variables.items():
        var_data[abbr] = data[name].to_numpy()

    dep = var_data['dep']
    # </editor-fold>

    # <editor-fold desc='DATA PROCESSING'>
    # <editor-fold desc="Convert the data time to East 8 time zone">
    time_offset_check = offset_from_utc(meta)
    if time_offset is None:
        if not time_offset_check[0]:
            raise ValueError(
                'You need to fill in time_offset in the CTD_info node in the '
                'Preprocess module in the configuration file')
        else:
            time_offset = 8 - time_offset_check[1]
    else:
        time_offset = 8 - time_offset
    tmp_time = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f') + timedelta(
        hours=time_offset) for x in data['Time']]
    # </editor-fold>

    time = date2num(tmp_time, time_units, calendar)
    down = updown[updown['Type'].isin(['DOWN'])]
    profile_size = np.shape(down)[0]
    max_bin_size = np.floor(np.nanmax(ref_dep) / bin_size).astype(int)
    time_ave = np.zeros(profile_size)
    var_data_ave = {}
    hgt = np.arange(0, max_bin_size * bin_size, bin_size)
    for name, abbr in variables.items():
        var_data_ave[abbr] = np.zeros([profile_size, max_bin_size])
        var_data_ave[abbr].fill(np.nan)

    for i, val in enumerate(down.to_numpy()):
        dt1 = datetime.strptime(val[0], '%Y-%m-%d %H:%M:%S.%f') + timedelta(
            hours=time_offset)
        dt2 = datetime.strptime(val[1], '%Y-%m-%d %H:%M:%S.%f') + timedelta(
            hours=time_offset)
        dt1_num = date2num(dt1, time_units, calendar)
        dt2_num = date2num(dt2, time_units, calendar)
        time_ave[i] = (dt1_num + dt2_num) / 2
        idx1 = np.where(np.array(tmp_time) <= dt2)[0]
        idx2 = np.where(dt1 <= np.array(tmp_time))[0]
        down_cast_idx = list(set(idx1).intersection(set(idx2)))
        tmp_dep_down = dep[down_cast_idx]
        idx1 = np.where(ref_time <= dt2)[0]
        idx2 = np.where(dt1 <= ref_time)[0]
        idx_ref = list(set(idx1).intersection(set(idx2)))
        # The value below 1m is the normal value
        crit_dep = np.nanmean(ref_dep[idx_ref])
        for j in range(np.floor(crit_dep / bin_size).astype(int) - np.round(
                1 / bin_size).astype(int)):
            tmp = crit_dep - bin_size * (j + 1)
            up_bound = 0 if tmp < 0 else tmp
            low_bound = tmp + bin_size
            idx1 = np.where(tmp_dep_down <= low_bound)[0]
            idx2 = np.where(up_bound < tmp_dep_down)[0]
            idx = list(set(idx1).intersection(set(idx2)))
            rslt_idx = idx if idx else np.nan
            for name, abbr in variables.items():
                if not np.isnan(rslt_idx).all():
                    var_data_ave[abbr][i, j] = np.nanmean(
                        var_data[abbr][down_cast_idx][rslt_idx])
    # </editor-fold>

    # <editor-fold desc='OUTPUT'>
    ctd2nc(save_path, lon, lat, time, time_units, calendar, time_ave, hgt,
           var_data, var_data_ave, meta, bin_size, variables, zlib, complevel,
           author, email)
    # </editor-fold>


def ctd2nc(save_path, lon, lat, time, time_units, calendar, time_ave=None,
           hgt=None, data=None, data_ave=None, meta=None, bin_size=None,
           variables=None, zlib=False, complevel=1, author='DengCW',
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
            var_tmp = out_file.createVariable(abbr, 'f8', 'time',
                                              zlib=zlib, complevel=complevel)
            var_tmp.units = out_file['Meta Group']['dataheader'][
                " ".join([name, "Meta Group"])].units
            var_tmp.long_name = name
            var_tmp.description = " ".join(
                ["The", name.lower(), "measureed from RBR's CTD"])
            out_file.variables[abbr][:] = data[abbr]
    # --------------------------------------------------------------------------
    if time_ave is None:
        out_file.close()
        return True
    downcast_grp = out_file.createGroup('Downcast Data Group')
    downcast_grp.createDimension('time', len(time_ave))
    downcast_grp.createDimension('height', len(hgt))
    # --------------------------------------------------------------------------
    # <editor-fold desc='Downcast Time'>
    var_time_downcast = downcast_grp.createVariable('time', 'f8', 'time',
                                                    zlib=zlib,
                                                    complevel=complevel)
    var_time_downcast.units = time_units
    var_time_downcast.calendar = calendar
    downcast_grp.variables['time'][:] = time_ave
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Height'>
    if hgt is None:
        raise ValueError('You need input the argument hgt.')
    else:
        var_hgt_downcast = downcast_grp.createVariable('height', 'f4', 'height',
                                                       zlib=zlib,
                                                       complevel=complevel)
        var_hgt_downcast.units = 'm'
        var_hgt_downcast.long_name = 'Height above sea bed'
        downcast_grp.variables['height'][:] = hgt
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Downcast Variables'>
    if data_ave is not None:
        for name, abbr in variables.items():
            var_tmp_downcast = downcast_grp.createVariable(abbr, 'f8',
                                                           ('time', 'height'),
                                                           zlib=zlib,
                                                           complevel=complevel)
            var_tmp_downcast.units = out_file['Meta Group']['dataheader'][
                " ".join([name, "Meta Group"])].units
            var_tmp_downcast.long_name = name
            var_tmp_downcast.description = " ".join(
                ["The downcast is extracted from the", name.lower(),
                 "measureed from RBR's CTD and then divided into bins based on "
                 "the depth of the water, each with a size of", str(bin_size),
                 "meters"])
            downcast_grp.variables[abbr][:] = data_ave[abbr]
    # --------------------------------------------------------------------------

    # </editor-fold>

    # <editor-fold desc='POST-PROCESSING'>
    # Clear data, memory space, windows, etc.
    out_file.close()
    # </editor-fold>

# -*- coding:uft-8 -*-
import copy
import warnings
from glob import glob
from os import path

import numpy as np
from more_itertools import chunked, consecutive_groups
from netCDF4 import Dataset, date2num
from scipy.io import loadmat
from yaml import full_load

from .util import get_val_from_str, detect_beam_index, type_detect, gen_time
from ..util import SegmentOperate, correct0drift, is_number, \
    extract_valid_time, modify_nc


def deploy_file_deconstruct(filepath, meta_var):
    setup_meta = {}
    with open(filepath) as f:
        deploy_conf = f.read()
    deploy_conf_parts = deploy_conf.split(';\n')
    commands = deploy_conf_parts[0].split('\n')[:-1]
    setup_detail = deploy_conf_parts[1].split('\n')[:-1]
    for it in commands:
        key = it[:2]
        val = it[2:]
        if key in meta_var:
            setup_meta[key] = copy.deepcopy(meta_var[key])
            tmp_val = val.split(',')
            if len(tmp_val) - 1:
                tmp = []
                for v in tmp_val:
                    v = v.strip()
                    if is_number(v):
                        tmp.append(int(v))
                    else:
                        tmp = tmp_val
                        break
                setup_meta[key]['value'] = tmp
            else:
                if is_number(val):
                    setup_meta[key]['value'] = int(val)
                else:
                    setup_meta[key]['value'] = val
    for it in setup_detail:
        tmp = it[1:].split('=')
        key = tmp[0].strip()
        val = tmp[1].strip()
        if is_number(val):
            setup_meta[key] = float(val)
        else:
            setup_meta[key] = val
    return setup_meta


def details_file_deconstruct(filepath, meta_var):
    detail_meta = {}
    with open(filepath) as f:
        details = f.readlines()
    detail_meta['Firmware Version'] = get_val_from_str(details[9])
    detail_meta['System Frequency'] = get_val_from_str(details[11])
    detail_meta['Beam Pattern'] = details[12][:-1]
    detail_meta['System Configuration'] = get_val_from_str(details[13])
    detail_meta['Beam angle'] = get_val_from_str(details[16])
    detail_meta['CPU Serial Number'] = details[21].split(':')[-1].strip()

    detail_meta['Sensor Avail'] = details[42][-16:-1]
    detail_meta['Hardware'] = str(get_val_from_str(details[46])) + ' Beams'
    detail_meta['Lag'] = get_val_from_str(details[47])
    detail_meta['Code Reps'] = get_val_from_str(details[48])
    detail_meta['Lag Length'] = get_val_from_str(details[49])

    detail_meta['CQ'] = copy.deepcopy(meta_var['CQ'])
    detail_meta['CQ']['value'] = get_val_from_str(details[23])

    detail_meta['CX'] = copy.deepcopy(meta_var['CX'])
    detail_meta['CX']['value'] = get_val_from_str(details[24])

    detail_meta['WA'] = copy.deepcopy(meta_var['WA'])
    detail_meta['WA']['value'] = get_val_from_str(details[26])

    detail_meta['WB'] = copy.deepcopy(meta_var['WB'])
    detail_meta['WB']['value'] = get_val_from_str(details[27])

    detail_meta['WC'] = copy.deepcopy(meta_var['WC'])
    detail_meta['WC']['value'] = get_val_from_str(details[28])

    detail_meta['WE'] = copy.deepcopy(meta_var['WE'])
    detail_meta['WE']['value'] = get_val_from_str(details[29])

    detail_meta['WF'] = copy.deepcopy(meta_var['WF'])
    detail_meta['WF']['value'] = get_val_from_str(details[30]) * 100

    detail_meta['WG'] = copy.deepcopy(meta_var['WG'])
    detail_meta['WG']['value'] = get_val_from_str(details[31])

    detail_meta['WL'] = copy.deepcopy(meta_var['WL'])
    detail_meta['WL']['value'] = get_val_from_str(details[32], False)

    detail_meta['WM'] = copy.deepcopy(meta_var['WM'])
    detail_meta['WM']['value'] = get_val_from_str(details[33])

    detail_meta['WN'] = copy.deepcopy(meta_var['WN'])
    detail_meta['WN']['value'] = get_val_from_str(details[34])

    detail_meta['WP'] = copy.deepcopy(meta_var['WP'])
    detail_meta['WP']['value'] = get_val_from_str(details[35])

    detail_meta['WS'] = copy.deepcopy(meta_var['WS'])
    detail_meta['WS']['value'] = int(get_val_from_str(details[36]) * 100)

    detail_meta['EA'] = copy.deepcopy(meta_var['EA'])
    detail_meta['EA']['value'] = int(get_val_from_str(details[38]) * 100)

    detail_meta['EB'] = copy.deepcopy(meta_var['EB'])
    detail_meta['EB']['value'] = int(get_val_from_str(details[39]) * 100)

    detail_meta['EX'] = copy.deepcopy(meta_var['EX'])
    detail_meta['EX']['value'] = get_val_from_str(details[40])

    detail_meta['EZ'] = copy.deepcopy(meta_var['EZ'])
    detail_meta['EZ']['value'] = get_val_from_str(details[41])

    detail_meta['TP'] = copy.deepcopy(meta_var['TP'])
    detail_meta['TP']['value'] = get_val_from_str(details[44])

    detail_meta['WT'] = copy.deepcopy(meta_var['WT'])
    detail_meta['WT']['value'] = int(get_val_from_str(details[50]) * 100)

    detail_meta['BP'] = copy.deepcopy(meta_var['BP'])
    detail_meta['BP']['value'] = get_val_from_str(details[53])

    detail_meta['BD'] = copy.deepcopy(meta_var['BD'])
    detail_meta['BD']['value'] = get_val_from_str(details[54])

    detail_meta['BC'] = copy.deepcopy(meta_var['BC'])
    detail_meta['BC']['value'] = get_val_from_str(details[55])

    detail_meta['BA'] = copy.deepcopy(meta_var['BA'])
    detail_meta['BA']['value'] = get_val_from_str(details[56])

    detail_meta['BG'] = copy.deepcopy(meta_var['BG'])
    detail_meta['BG']['value'] = get_val_from_str(details[57])

    detail_meta['BM'] = copy.deepcopy(meta_var['BM'])
    detail_meta['BM']['value'] = get_val_from_str(details[58])

    detail_meta['BE'] = copy.deepcopy(meta_var['BE'])
    detail_meta['BE']['value'] = get_val_from_str(details[59])

    detail_meta['BX'] = copy.deepcopy(meta_var['BX'])
    detail_meta['BX']['value'] = get_val_from_str(details[60])
    return detail_meta


def detect_valid_data(data, valid_dep_dif):
    tmp_cor = data['cor_ave']['value'].astype(float)
    idx1 = np.where(tmp_cor > 150)
    idx2 = np.where(tmp_cor < 100)
    tmp_cor[idx1] = np.nan
    tmp_cor[idx2] = np.nan
    tmp_shp = np.shape(tmp_cor)
    if tmp_shp[1] > 10:
        bins_num = int(np.floor(tmp_shp[1] / 2))
    else:
        bins_num = 5
    for i in range(bins_num):
        idx1 = 0
        idx2 = 1E10
        for group in consecutive_groups(
                np.where(np.isnan(tmp_cor[:, i]) == False)[0]):
            l1 = list(group)
            if len(l1) < tmp_shp[0] * 0.008:
                tmp_cor[l1, i] = np.nan
        for group in consecutive_groups(
                np.where(np.isnan(tmp_cor[:, i]))[0]):
            l1 = list(group)
            if l1[0] == 0 and l1[-1] > idx1:
                idx1 = l1[-1]
            if l1[-1] == tmp_shp[0] - 1 and l1[0] < idx2:
                idx2 = l1[0]
    tmp_cor[:idx1 + 1, :] = np.nan
    tmp_cor[idx2:, :] = np.nan
    tmp_ave = np.nanmean(tmp_cor[:, :bins_num], axis=1)
    tmp_ave_val = np.nanmean(tmp_ave)
    min_lim = tmp_ave_val * 0.95
    max_lim = tmp_ave_val * 1.05
    for i, val in enumerate(tmp_ave):
        if val < min_lim or val > max_lim:
            tmp_ave[i] = np.nan
        else:
            break
    for i in range(tmp_shp[0] - 1, -1, -1):
        if tmp_ave[i] < min_lim or tmp_ave[i] > max_lim:
            tmp_ave[i] = np.nan
        else:
            break
    idx = np.where(np.isnan(tmp_ave) == False)[0]
    add_offset = [0, 0]
    dep = data['dep']['value']
    for i in range(idx[0], idx[-1]):
        if np.abs(dep[i + 1] - dep[i]) > valid_dep_dif:
            add_offset[0] = add_offset[0] + 1
        else:
            break

    for i in range(idx[-1], idx[0], -1):
        if np.abs(dep[i - 1] - dep[i]) > valid_dep_dif:
            add_offset[-1] = add_offset[-1] + 1
        else:
            break
    if add_offset[-1] == 0:
        return idx[add_offset[0]:]
    else:
        return idx[add_offset[0]:0 - add_offset[-1]]


def del_dif(filter_var, nan_arr, filter_val):
    shp = np.shape(filter_var)
    for i in range(shp[0]):
        for j in range(shp[1] - 1):
            if np.abs(filter_var[i, j + 1] - filter_var[i, j]) > filter_val:
                nan_arr[i, j + 1:] = np.nan
                break
    return nan_arr


def del_disp(data, nan_arr, disp_num):
    data[np.isnan(nan_arr)] = np.nan
    rslt = nan_arr
    shp = np.shape(data)
    for j in np.arange(shp[1] - 1):
        idx = np.isfinite(rslt[:, j])
        # when the effective continuous time is less than
        # disp_num, the value of the segment is set to nan
        for group in consecutive_groups(np.where(idx == 1)[0]):
            l1 = list(group)
            if len(l1) and np.max(l1) - np.min(l1) < disp_num:
                rslt[l1[:], j] = np.nan
    return nan_arr


def ssl_detect(data_path, save_path, vdd, filter_val, corr0drift=False,
               debug=False, zlib=False, complevel=1):
    data_obj = Dataset(data_path)
    data_ave = {}
    data_grp = 'Average Data Group'
    var_ls = data_obj[data_grp].variables
    var2dim_ls = []
    for name in var_ls:
        data_ave[name] = data_obj[data_grp][name][:].data

    for name in var_ls:
        var = data_ave[name][:]
        if len(np.shape(var)) == 2:
            var2dim_ls.append(name)

    if 'dep' in var_ls:
        if corr0drift:
            dep0bias = correct0drift(data_ave['dep'][:], vdd)
            data_ave['dep'] = data_ave['dep'][:] - dep0bias
        tmp_bin_ave = np.squeeze(np.floor((data_ave['dep'] - data_obj.getncattr(
            'RDIBin1Mid')) / data_obj.getncattr('RDIBinSize') - 1).astype(int))
        tmp_bin_ave[tmp_bin_ave < 0] = 0
        # Clear data above the sea

        for name in var2dim_ls:
            var = data_ave[name][:]
            tmp_shp = np.shape(var)
            nan_arr = np.ones(tmp_shp)
            for i in np.arange(tmp_shp[0]):
                nan_arr[i, tmp_bin_ave[i]:] = np.nan
                continue
            break

        for name in ['u', 'v', 'w']:
            if name not in var_ls:
                continue
            nan_arr = del_dif(data_ave[name], nan_arr, filter_val[name])
        nan_arr = del_disp(data_ave[name], nan_arr, filter_val['scatter'])

        for name in var2dim_ls:
            data_ave[name][np.isnan(nan_arr)] = np.nan
        if debug:
            pass
        else:
            data_obj.close()
            modify_nc(data_path, save_path, data_ave, data_grp, zlib=zlib,
                      complevel=complevel)
        return True, None
    else:
        return False, 'SSL cannot be detected without depth data'


def convert2nc(mat_path, save_path, time_win, time_units, calendar, sta_info,
               beam_fill_value, time_offset, pg_std, vdd, adcp_hgt=0,
               beam_path=None, detail_path=None, deploy_path=None, zlib=False,
               complevel=1, corr0drift=True, author='DengCW',
               email='dengchuangwu@gmail.com'):
    resp = []
    this_file_dir = path.split(path.abspath(__file__))[0]
    meta_var = full_load(open('/'.join([this_file_dir, 'config.yml'])))['meta']
    data_var = full_load(open('/'.join([this_file_dir, 'config.yml'])))['data']
    # <editor-fold desc='DATA READING'>

    # <editor-fold desc="create metadata dictionary">
    if deploy_path is not None:
        deploy_meta = deploy_file_deconstruct(deploy_path, meta_var)
    else:
        deploy_meta = None
    if detail_path is not None:
        detail_meta = details_file_deconstruct(detail_path, meta_var)
    else:
        detail_meta = None
    # </editor-fold>

    data = {}
    data_ave = {}
    data_meta = {}
    mat_data = loadmat(mat_path)
    for key in mat_data:
        if 'RDI' in key:
            if isinstance(mat_data[key][0], str):
                data_meta[key] = mat_data[key][0]
            else:
                data_meta[key] = mat_data[key][0][0]

    lon = sta_info['lon']
    lat = sta_info['lat']

    bin1_hgt = adcp_hgt + data_meta['RDIBin1Mid']
    hgt = np.round([bin1_hgt + x * data_meta['RDIBinSize'] for x in
                    range(np.size(mat_data['SerBins']))], 2)
    beam_data = [1, 2, 3, 4]
    beam_data_ave = [1, 2, 3, 4]
    bm_var = [1, 2, 3, 4]
    rey12 = None
    rey34 = None
    try:
        filepath_ls = glob(''.join([beam_path, '*']))
        for filepath in filepath_ls:
            idx = detect_beam_index(filepath) - 1
            beam_data[idx] = np.recfromcsv(filepath,
                                           missing_value=beam_fill_value,
                                           filling_values=np.nan)[:, 1:]
            # beam_data[idx][beam_data[idx] == beam_fill_value] = np.nan
            beam_data[idx] = beam_data[idx] / 1000
    except KeyError:
        warnings.warn('Lack of beam data')
        beam_data = None

    for it in mat_data:
        if it in data_var:
            name = data_var[it]['name']
            data[name] = copy.deepcopy(data_var[it])
            if 'scale' in data_var[it]:
                data[name]['value'] = mat_data[it] / data_var[it]['scale']
                del data[name]['scale']
            else:
                data[name]['value'] = mat_data[it]
    # </editor-fold>
    ############################################################################
    # <editor-fold desc='DATA PROCESSING'>

    # <editor-fold desc="Convert the data time to East 8 time zone">
    if time_offset is None:
        raise ValueError('You need input the argument time_offset.')
    time_offset = 8 - time_offset
    tmp_time = gen_time(mat_data, time_offset)
    # </editor-fold>
    time = date2num(tmp_time, time_units, calendar)
    delta = time[1] - time[0]
    ave_len = int(time_win * 60 * 10 ** 3 / delta)
    time_ave = [np.mean(x) for x in chunked(time, ave_len)]

    pg = np.ones([4, len(np.squeeze(data['ens']['value'])),
                  len(np.squeeze(data['bins']['value']))])
    pg.fill(np.nan)
    for i in range(4):
        if ''.join(['SerPG', str(i + 1)]) in mat_data:
            pg[i, :, :] = mat_data[''.join(['SerPG', str(i + 1)])]
    pg_ave = (pg[0].astype(np.int) + pg[1].astype(np.int) + pg[2].astype(
        np.int) + pg[3].astype(np.int)) / 4
    pg_ave[pg_ave < pg_std] = np.nan

    invalid_ave_data = ['bins', 'ens', 'pg_bm1', 'pg_bm2', 'pg_bm3', 'pg_bm4',
                        'wr_lat']
    for key, val in data.items():
        if key not in invalid_ave_data:
            data_ave[key] = copy.deepcopy(data[key])
            data_ave[key]['value'] = data_ave[key]['value'].astype(float)
            if 'pg' in dir() and len(
                    np.shape(np.squeeze(data_ave[key]['value']))) == 2:
                data_ave[key]['value'][np.isnan(pg_ave)] = np.nan
            data_ave[key]['value'] = SegmentOperate(
                np.squeeze(data_ave[key]['value']), ave_len).value

    if 'dep' in data_ave and corr0drift:
        dep0bias = correct0drift(data_ave['dep']['value'], vdd)
        data_ave['dep']['value'] = data_ave['dep']['value'] - dep0bias

    tmp_beam = copy.deepcopy(beam_data)
    if beam_data is not None:
        for i, val in enumerate(beam_data):
            beam_data_ave[i] = SegmentOperate(val, ave_len).value
            if ('SerPG1' in mat_data) and ('SerPG2' in mat_data) and (
                    'SerPG3' in mat_data) and ('SerPG4' in mat_data):
                tmp_beam[i][pg[i] < pg_std] = np.nan
            bm_var[i] = SegmentOperate(tmp_beam[i], ave_len, np.nanvar).value
        if detail_meta is not None and 'Beam angle' in detail_meta:
            rey12 = (bm_var[1] - bm_var[0]) / (
                    2 * np.sin(np.deg2rad(2 * detail_meta['Beam angle'])))
            rey34 = (bm_var[3] - bm_var[2]) / (
                    2 * np.sin(np.deg2rad(2 * detail_meta['Beam angle'])))
    else:
        beam_data_ave = None

    adcp2nc(save_path, lon, lat, time, time_units, calendar, hgt, time_win,
            time_ave, data, beam_data, data_ave, beam_data_ave, rey12, rey34,
            data_meta, detail_meta, deploy_meta, zlib, complevel, author, email)
    return True, resp
    # </editor-fold>


def cut_time(data_path, save_path, vdd, zlib, complevel):
    return extract_valid_time(data_path, save_path, 'Average Data Group', vdd,
                              zlib, complevel)


def adcp2nc(save_path, lon, lat, time, time_units, calendar, hgt, time_win=None,
            time_ave=None, data=None, beam_data=None, data_ave=None,
            beam_data_ave=None, rey12=None, rey34=None, data_meta=None,
            detail_meta=None, deploy_meta=None, zlib=False, complevel=1,
            author='DengCW', email='dengchuangwu@gmail.com'):
    out_file = Dataset(save_path, 'w')
    # <editor-fold desc='create dimensions'>
    out_file.createDimension('time', np.size(time))
    out_file.createDimension('height', np.size(hgt))
    out_file.createDimension('lon', 1)
    out_file.createDimension('lat', 1)
    # </editor-fold>

    # <editor-fold desc='Attributes'>
    out_file.setncattr('Author', author)
    out_file.setncattr('Email', email)
    if data_meta is not None:
        for key, val in data_meta.items():
            out_file.setncattr(key, val)
    n = 0
    if detail_meta is not None:
        detail_grp = out_file.createGroup('File Details')
        detail_dim = {}
        for key, val in detail_meta.items():
            if isinstance(val, dict):
                value = val['value']
                dim_flag = True
                for dim_key, dim_val in detail_dim.items():
                    if np.size(value) == dim_val:
                        dim_name = dim_key
                        dim_flag = False
                if dim_flag:
                    n += 1
                    dim_name = 'ind' + str(n)
                    detail_dim[dim_name] = np.size(value)
                    detail_grp.createDimension(dim_name, np.size(value))

                val_type = type_detect(value)
                if isinstance(value, (list, tuple, np.ndarray)):
                    tmp = detail_grp.createVariable(key, val_type, dim_name,
                                                    zlib=zlib,
                                                    complevel=complevel)
                else:
                    tmp = detail_grp.createVariable(key, val_type, dim_name,
                                                    zlib=zlib,
                                                    complevel=complevel)
                if isinstance(value, str):
                    tmp.setncattr('value', value)
                else:
                    detail_grp[key][:] = value
                for k, v in val.items():
                    if k == 'value':
                        continue
                    tmp.setncattr(k, v)
            else:
                detail_grp.setncattr(key, val)

    n = 0
    if deploy_meta is not None:
        deploy_grp = out_file.createGroup('Deployment Information')
        deploy_dim = {}
        for key, val in deploy_meta.items():
            if isinstance(val, dict):
                value = val['value']
                dim_flag = True
                for dim_key, dim_val in deploy_dim.items():
                    if np.size(value) == dim_val:
                        dim_name = dim_key
                        dim_flag = False
                if dim_flag:
                    n += 1
                    dim_name = 'ind' + str(n)
                    deploy_dim[dim_name] = np.size(value)
                    deploy_grp.createDimension(dim_name, np.size(value))

                val_type = type_detect(value)
                tmp = deploy_grp.createVariable(key, val_type, dim_name,
                                                zlib=zlib, complevel=complevel)
                if isinstance(value, str):
                    tmp.setncattr('value', value)
                else:
                    deploy_grp[key][:] = value
                for k, v in val.items():
                    if k == 'value':
                        continue
                    tmp.setncattr(k, v)
            else:
                deploy_grp.setncattr(key, val)
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
    # <editor-fold desc='Height above sea bed'>
    var_hgt = out_file.createVariable('height', 'f4', 'height', zlib=zlib,
                                      complevel=complevel)
    var_hgt.units = 'm'
    var_hgt.long_name = 'Height above sea bed'
    out_file.variables['height'][:] = hgt
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Variables'>
    if data is not None:
        for key, val in data.items():
            value = val['value']
            val_type = type_detect(value)
            if key == 'bins':
                tmp = out_file.createVariable(key, val_type, 'height',
                                              zlib=zlib, complevel=complevel)
            else:
                if len(np.shape(np.squeeze(value))) == 2:
                    tmp = out_file.createVariable(key, val_type,
                                                  ('time', 'height'), zlib=zlib,
                                                  complevel=complevel)
                else:
                    tmp = out_file.createVariable(key, val_type, 'time',
                                                  zlib=zlib,
                                                  complevel=complevel)
            for k, v in val.items():
                if k in ['name', 'value']:
                    continue
                tmp.setncattr(k, v)
            out_file[key][:] = np.squeeze(value)
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Beam Variables'>
    if beam_data is not None:
        for i, val in enumerate(beam_data):
            beam_name = 'beam' + str(i + 1)
            var_beam = out_file.createVariable(beam_name, np.float32,
                                               ('time', 'height'), zlib=zlib,
                                               complevel=complevel)
            var_beam.long_name = 'The velocity of ' + beam_name
            var_beam.units = 'm/s'
            out_file.variables[beam_name][:] = val
    # </editor-fold>
    # --------------------------------------------------------------------------
    if time_ave is None:
        out_file.close()
        return True
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
        for key, val in data_ave.items():
            value = val['value']
            val_type = type_detect(value)
            if len(np.shape(np.squeeze(value))) == 2:
                tmp = ave_data_grp.createVariable(key, val_type,
                                                  ('time', 'height'), zlib=zlib,
                                                  complevel=complevel)
            else:
                tmp = ave_data_grp.createVariable(key, val_type, 'time',
                                                  zlib=zlib,
                                                  complevel=complevel)
            for k, v in val.items():
                if k in ['name', 'value']:
                    continue
                if k == 'long_name':
                    tmp.setncattr(k, ' '.join(
                        [v, "was averaged every", time_win, "minutes"]))
                else:
                    tmp.setncattr(k, v)
            ave_data_grp[key][:] = np.squeeze(value)
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Average Beam Variables'>
    if beam_data_ave is not None:
        for i, val in enumerate(beam_data_ave):
            beam_name = 'beam' + str(i + 1)
            var_beam = ave_data_grp.createVariable(beam_name, np.float32,
                                                   ('time', 'height'),
                                                   zlib=zlib,
                                                   complevel=complevel)
            var_beam.long_name = ' '.join(
                ['The velocity of', beam_name, "was averaged every", time_win,
                 "minutes"])
            var_beam.units = 'm/s'
            ave_data_grp.variables[beam_name][:] = val
    # </editor-fold>
    # --------------------------------------------------------------------------
    # <editor-fold desc='Reynolds Stress'>
    if rey12 is not None:
        var_rey12 = ave_data_grp.createVariable('rey12', np.float32,
                                                ('time', 'height'), zlib=zlib,
                                                complevel=complevel)
        var_rey12.long_name = 'Reynolds stress calculated by variance method using beam1 and beam2'
        var_rey12.units = r'm^2/s^2'
        ave_data_grp.variables['rey12'][:] = rey12
    if rey34 is not None:
        var_rey34 = ave_data_grp.createVariable('rey34', np.float32,
                                                ('time', 'height'), zlib=zlib,
                                                complevel=complevel)
        var_rey34.long_name = 'Reynolds stress calculated by variance method using beam3 and beam4'
        var_rey34.units = r'm^2/s^2'
        ave_data_grp.variables['rey34'][:] = rey34
    # </editor-fold>
    # --------------------------------------------------------------------------

    # </editor-fold>

    # <editor-fold desc='POST-PROCESSING'>
    # Clear data, memory space, windows, etc.
    out_file.close()
    # </editor-fold>

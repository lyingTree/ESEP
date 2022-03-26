# -*- coding:uft-8 -*-
from os import path

from yaml import full_load

from .RBR.td import convert2nc as conv2nc_rbr, cut_time
from .util import detect_brand


def td2nc(prefix, td_paths, rslt_path, time_win, time_units, calendar,
          td_info_all, sta_info_all, zlib, complevel, author, email):
    this_file_dir = path.split(path.abspath(__file__))[0]
    conf = full_load(open('/'.join([this_file_dir, 'config.yml'])))
    valid_brands = [x.upper() for x in conf['ValidBrands']['td']]
    for key, val in td_paths.items():
        td_path = ''.join([prefix, val])
        save_path = ''.join([prefix, rslt_path[key]])
        sta_info = sta_info_all[key]
        corr0drift = td_info_all['correct0drift']
        valid_dep_dif = td_info_all['valid_dep_dif'][key]
        if 'time_offset' in td_info_all:
            time_offset = td_info_all['time_offset']
        else:
            time_offset = None
        brands = detect_brand(sta_info['observe_instrument'], 'TD')
        for brand in brands:
            tmp_brand = brand.upper()
            if tmp_brand not in valid_brands:
                raise NotImplementedError(
                    'Invalid brand. You can update the config file and add some'
                    ' method to process the related dataset and export them.')
            elif tmp_brand == 'RBR':
                conv2nc_rbr(td_path, save_path, time_win, time_units, calendar,
                            sta_info, valid_dep_dif, time_offset, corr0drift,
                            zlib, complevel, author, email)
            else:
                raise NotImplementedError('Unrealized functions.')
    return True, None


def td_extract(prefix, data_path_all, save_path_all, td_info_all, zlib,
               complevel):
    for key, val in save_path_all.items():
        data_path = prefix + data_path_all[key]
        save_path = prefix + save_path_all[key]
        vdd = td_info_all['valid_dep_dif'][key]
        state, resp = cut_time(data_path, save_path, vdd, zlib, complevel)
        if not state:
            return state, resp
    return True, None

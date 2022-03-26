# -*- coding:uft-8 -*-
from os import path

from yaml import full_load

from RDI.adcp import convert2nc as conv2nc_rdi, ssl_detect, cut_time
from util import detect_brand


def adcp2nc(prefix, adcp_paths, rslt_path, time_win, time_units, calendar,
            adcp_info_all, sta_info_all, zlib, complevel, author, email):
    this_file_dir = path.split(path.abspath(__file__))[0]
    conf = full_load(open('/'.join([this_file_dir, 'config.yml'])))
    valid_brands = [x.upper() for x in conf['ValidBrands']['adcp']]
    for sta, val in adcp_paths.items():
        mat_path = prefix + val['mat']
        beam_path = prefix + val['beam']
        detail_path = prefix + val['file_details']
        deploy_path = prefix + val['deployment']
        save_path = prefix + rslt_path[sta]
        sta_info = sta_info_all[sta]
        beam_fill_value = adcp_info_all['beam_fill_value']
        time_offset = adcp_info_all['time_offset']
        pg_std = adcp_info_all['pg_std']
        vdd = adcp_info_all['valid_dep_dif'][sta]
        adcp_hgt = adcp_info_all['adcp_hgt']
        corr0drift = adcp_info_all['correct0drift']
        brands = detect_brand(sta_info['observe_instrument'], 'ADCP')

        args = [mat_path, save_path, time_win, time_units, calendar, sta_info,
                beam_fill_value, time_offset, pg_std, vdd, adcp_hgt, beam_path,
                detail_path, deploy_path, corr0drift, zlib, complevel, author,
                email]
        for brand in brands:
            tmp_brand = brand.upper()
            if tmp_brand not in valid_brands:
                raise NotImplementedError(
                    'Invalid brand. You can update the config file and add some'
                    ' method to process the related dataset and export them.')
            elif tmp_brand == 'RDI':
                conv2nc_rdi(*args)
            else:
                raise NotImplementedError('Unrealized functions.')
    return True, None


def adcp_multi_proc(prefix, data_path, adcp_info_all, save_path_all=None,
                    debug=True, zlib=False, complevel=1):
    corr0drift = not adcp_info_all['correct0drift']
    for key, val in data_path.items():
        data_path = prefix + val
        filter_val = adcp_info_all['filter'][key]
        save_path = prefix + save_path_all[key]
        vdd = adcp_info_all['valid_dep_dif'][key]
        state, resp = ssl_detect(data_path, save_path, vdd, filter_val,
                                 corr0drift, debug, zlib, complevel)
        if not state:
            return state, resp
    return True, None


def adcp_extract(prefix, data_path_all, save_path_all, adcp_info_all, zlib,
                 complevel):
    for key, val in save_path_all.items():
        data_path = prefix + data_path_all[key]
        save_path = prefix + save_path_all[key]
        vdd = adcp_info_all['valid_dep_dif'][key]
        state, resp = cut_time(data_path, save_path, vdd, zlib, complevel)
        if not state:
            return state, resp
    return True, None


def wt_separation_from_adcp(b11, b12, b13, b14, b21, b22, b23, b24, n, theta, ave_len):
    data_len = np.size(b11)
    u_var = np.ones([4, np.ceil(data_len / ave_len)])
    k = 0
    for tmp1, tmp2 in distribute(4, [b11, b12, b13, b14, b21, b22, b23, b24]):
        tmp1_ls = list(chunked(tmp1, ave_len))
        tmp2_ls = list(chunked(tmp2, ave_len))
        for i, val in enumerate(tmp1_ls):
            u_var[k, i] = reynolds_var(np.array(val), np.array(tmp2_ls[i]), n)
        k += 1
    vw = (u_var[3] - u_var[2]) / (4 * np.sin(np.deg2rad(theta)) * np.cos(np.deg2rad(theta)))
    uw = (u_var[1] - u_var[0]) / (4 * np.sin(np.deg2rad(theta)) * np.cos(np.deg2rad(theta)))
    return uw, vw

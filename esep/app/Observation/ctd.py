# -*- coding:uft-8 -*-
from os import path

from netCDF4 import Dataset, num2date
from scipy.io import loadmat
from yaml import full_load

from RBR.ctd import convert2nc as conv2nc_rbr
from RDI.util import gen_time
from util import detect_brand


def ctd_ref_data(adcp_path, time_offset, adcp_hgt):
    ext = adcp_path.split('.')[-1]
    if ext.upper() == 'NC':
        data = Dataset(adcp_path)
        ref_dep = data['dep'][:] + adcp_hgt
        ref_time = data['time']
        return ref_dep, num2date(ref_time[:], ref_time.units, ref_time.calendar)
    elif ext.upper() == 'MAT':
        data = loadmat(adcp_path)
        ref_dep = data['AnDepthmm'] / 1000
        ref_time = gen_time(data, time_offset)
        return ref_dep, ref_time


def ctd2nc(prefix, ctd_paths, rslt_path, time_units, calendar, ctd_info_all,
           adcp_info_all, sta_info_all, zlib, complevel, author, email):
    this_file_dir = path.split(path.abspath(__file__))[0]
    conf = full_load(open('/'.join([this_file_dir, 'config.yml'])))
    valid_brands = [x.upper() for x in conf['ValidBrands']['ctd']]
    for key, val in ctd_paths.items():
        ctd_path = ''.join([prefix, val])
        save_path = ''.join([prefix, rslt_path[key]])
        sta_info = sta_info_all[key]
        bin_size = ctd_info_all['bin_size']
        ref_data_path = ctd_info_all['ref_data'][key]
        if 'time_offset' in ctd_info_all:
            time_offset = ctd_info_all['time_offset']
        else:
            time_offset = None
        adcp_time_offset = adcp_info_all['time_offset']
        adcp_hgt = adcp_info_all['adcp_hgt']
        ref_dep, ref_time = ctd_ref_data(''.join([prefix, ref_data_path]),
                                         adcp_time_offset, adcp_hgt)
        brands = detect_brand(sta_info['observe_instrument'], 'CTD')
        for brand in brands:
            tmp_brand = brand.upper()
            if tmp_brand not in valid_brands:
                raise NotImplementedError(
                    'Invalid brand. You can update the config file and add some'
                    ' method to process the related dataset and export them.')
            elif tmp_brand == 'RBR':
                conv2nc_rbr(ctd_path, save_path, time_units, calendar, sta_info,
                            bin_size, ref_dep, ref_time, time_offset, zlib,
                            complevel, author, email)
            else:
                raise NotImplementedError('Unrealized functions.')
    return True, None

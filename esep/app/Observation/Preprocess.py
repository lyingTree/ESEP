# -*- coding:uft-8 -*-
import traceback

from yaml import full_load

from adcp import adcp2nc, adcp_multi_proc, adcp_extract
from ctd import ctd2nc
from td import td2nc, td_extract
from verification import StructureDetect, struct_detect_asd


def fun(x):
    return x[1] - x[0]


# ---------------------------------INITIAL SETUP--------------------------------
def convert2nc(config_path):
    conf = full_load(open(config_path))
    conv2nc = StructureDetect(conf).conv2nc

    if not conv2nc.state:
        return conv2nc.resp

    conf_prefix = conf['prefix']
    data_path = conf['OriginalData']
    nc_path = conf['PreprocessData']
    conf_win = conf['time_window']
    conf_time_units = conf['time_units']
    conf_calendar = conf['calendar']
    conf_sta_info = conf['StationInfo']
    conf_pre = conf['Preprocess']
    section_run = conf['SectionRun']
    author = conf['author']
    email = conf['email']
    zlib = conf['zlib']
    complevel = conf['complevel']
    resp = []
    if 'adcp' in section_run:
        state, msg = conv2nc.adcp()
        if not state:
            resp.append(msg)
        else:
            conf_pre_adcp_info = conf_pre['adcpInfo']
            try:
                state, msg = adcp2nc(conf_prefix, data_path['adcp'],
                                     nc_path['adcp'], conf_win, conf_time_units,
                                     conf_calendar, conf_pre_adcp_info,
                                     conf_sta_info, zlib, complevel, author,
                                     email)
                if not state:
                    resp.append(msg)
                else:
                    resp.append('ADCP completed.')
            except Exception :
                resp.append(traceback.format_exc())

    if 'ctd' in section_run:
        state, msg = conv2nc.ctd()
        if not state:
            resp.append(msg)
        else:
            conf_pre_ctd_info = conf_pre['ctdInfo']
            conf_pre_adcp_info = conf_pre['adcpInfo']
            try:
                state, msg = ctd2nc(conf_prefix, data_path['ctd'],
                                    nc_path['ctd'],
                                    conf_time_units, conf_calendar,
                                    conf_pre_ctd_info, conf_pre_adcp_info,
                                    conf_sta_info, zlib, complevel, author,
                                    email)
                if not state:
                    resp.append(msg)
                else:
                    resp.append('CTD completed.')
            except Exception:
                resp.append(traceback.format_exc())

    if 'td' in section_run:
        state, msg = conv2nc.td()
        if not state:
            resp.append(msg)
        else:
            conf_pre_td_info = conf_pre['tdInfo']
            try:
                state, msg = td2nc(conf_prefix, data_path['td'], nc_path['td'],
                                   conf_win, conf_time_units, conf_calendar,
                                   conf_pre_td_info, conf_sta_info, zlib,
                                   complevel, author, email)
                if not state:
                    resp.append(msg)
                else:
                    resp.append('TD completed.')
            except Exception as e:
                resp.append(traceback.format_exc())

    if isinstance(resp, list):
        return list2str(resp)
    return resp


def adcp_ssl_detect(config_path):
    conf = full_load(open(config_path))
    state, resp = struct_detect_asd(conf)
    if not state:
        return resp

    conf_prefix = conf['prefix']
    conf_pre = conf['Preprocess']
    nc_path = conf_pre['adcpSslDetect']
    adcp_info = conf_pre['adcpInfo']
    save_path = conf_pre['adcpSavePath']
    debug = conf_pre['debug']
    zlib = conf['zlib']
    complevel = conf['complevel']
    resp = 'The program has been completed'
    try:
        adcp_multi_proc(conf_prefix, nc_path, adcp_info, save_path, debug, zlib,
                        complevel)
    except Exception:
        resp = traceback.format_exc()
    if isinstance(resp, list):
        return list2str(resp)
    return resp


def extract_valid_time(config_path):
    resp = []
    conf = full_load(open(config_path))
    # state, resp = struct_detect_asd(conf)
    # if not state:
    #     return resp
    conf_prefix = conf['prefix']
    conf_pre = conf['Preprocess']
    nc_path = conf['PreprocessData']
    conf_intercept = conf_pre['intercept']
    section_run = conf_intercept['sectionRun']
    zlib = conf['zlib']
    complevel = conf['complevel']
    if 'adcp' in section_run:
        conf_pre_adcp_info = conf_pre['adcpInfo']
        save_path = conf_intercept['save_path']['adcp']
        try:
            state, msg = adcp_extract(conf_prefix, nc_path['adcp'], save_path,
                                      conf_pre_adcp_info, zlib, complevel)
            if not state:
                resp.append(msg)
            else:
                resp.append('ADCP completed.')
        except Exception:
            resp.append(traceback.format_exc())

    if 'td' in section_run:
        conf_pre_td_info = conf_pre['tdInfo']
        save_path = conf_intercept['save_path']['td']
        try:
            state, msg = td_extract(conf_prefix, nc_path['td'], save_path,
                                    conf_pre_td_info, zlib, complevel)
            if not state:
                resp.append(msg)
            else:
                resp.append('TD completed.')
        except Exception:
            resp.append(traceback.format_exc())

    if isinstance(resp, list):
        return list2str(resp)
    return resp


def list2str(resp):
    ret = ''
    n = 1
    for i, val in enumerate(resp):
        if 'completed' in val:
            ret = ''.join([ret, val, '\n\n'])
        else:
            ret = ''.join(
                [ret, 'The the index of the error message is ', str(n),
                 '. The content list below:\n', val, '\n\n'])
            n += 1
    return ret


if __name__ == '__main__':
    convert2nc('../config.yml')

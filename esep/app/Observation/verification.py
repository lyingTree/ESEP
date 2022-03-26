# -*- coding:uft-8 -*-
from glob import glob
from os import path


def file_detect(filepath, ext=None, msg=''):
    if not path.exists(filepath):
        return False, ' '.join(['Please input the valid path.', msg])
    if not path.isfile(filepath):
        return False, ' '.join(['The path is a directory.', msg])
    if ext is None:
        return True, None
    if path.splitext(filepath)[-1] != ext:
        return False, ' '.join(['Invalid file.', msg])
    return True, None


class StructureDetect(object):
    def __init__(self, conf_file):
        self.conv2nc = Convert2Nc(conf_file)


class Convert2Nc(object):
    def __init__(self, conf_file):
        self.state, self.resp = self.check(conf_file)
        self.prefix = conf_file['prefix']
        self.conf_pre = conf_file['Preprocess']
        orig_data = conf_file['OriginalData']
        self.nc_path = conf_file['PreprocessData']
        self.detect_orig = OriginalDataDetect(self.prefix, orig_data,
                                              'OriginalData')

    @staticmethod
    def check(conf_file):
        base_key = ['prefix', 'OriginalData', 'PreprocessData', 'time_window',
                    'time_units', 'calendar', 'StationInfo', 'Preprocess',
                    'SectionRun', 'author', 'email']

        for i, val in enumerate(base_key):
            if val not in conf_file:
                return False, ' '.join(
                    ['The', val, 'node is missing in the configuration file.'])
        return True, None

    def adcp(self):
        adcp_key = {'adcp_hgt': (int, float), 'time_offset': int,
                    'pg_std': (int, float), 'correct0drift': bool,
                    'beam_fill_value': (int, float), 'valid_dep_dif': dict}
        if 'adcpInfo' not in self.conf_pre:
            return False, miss_child_node('adcpInfo', 'Preprocess')

        this_node = '->'.join(['Preprocess', 'adcpInfo'])
        adcp_info = self.conf_pre['adcpInfo']
        for key, val in adcp_key:
            if key not in adcp_info:
                return False, miss_key(key, this_node)

            info_val = adcp_info[key]
            if not isinstance(info_val, val):
                return False, invalid_value(key, this_node)

            if key == 'valid_dep_dif':
                vdd_node = '->'.join([this_node, 'valid_dep_dif'])
                for k, v in info_val.items():
                    if not isinstance(v, (int, float)):
                        return False, invalid_value(k, vdd_node)

        state, resp = self.detect_orig.rdi.adcp()
        if not state:
            return state, resp

        state, resp = preprocess_data_module_detect('adcp', self.nc_path,
                                                    'PreprocessData',
                                                    self.prefix)
        if not state:
            return state, resp
        return True, None

    def ctd(self):
        if 'ctdInfo' not in self.conf_pre:
            return False, miss_child_node('ctdInfo', 'Preprocess')

        ctd_info = self.conf_pre['ctdInfo']
        this_node = '->'.join(['Preprocess', 'ctdInfo'])
        ctd_key = {'bin_size': (int, float), 'ref_data': dict}
        for key, val in ctd_key.items():
            if key not in ctd_info:
                return False, miss_key(key, this_node)

            ctd_info_item = ctd_info[key]
            if not isinstance(ctd_info_item, val):
                return False, invalid_struct(this_node + '->' + key)
            if key == 'ref_data':
                ref_data_node = '->'.join([this_node, 'ref_data'])
                for k, v in ctd_info_item.items():
                    if not isinstance(v, str):
                        return False, invalid_value(k, ref_data_node)
                    filepath = ''.join([self.prefix, v])
                    state, resp = file_detect(filepath, '.nc',
                                              invalid_value(k, ref_data_node))
                    if not state:
                        return state, resp
        state, resp = self.detect_orig.rbr.ctd()
        if not state:
            return state, resp

        state, resp = preprocess_data_module_detect('ctd', self.nc_path,
                                                    'PreprocessData',
                                                    self.prefix)
        if not state:
            return state, resp
        return True, None

    def td(self):
        if 'tdInfo' not in self.conf_pre:
            return False, miss_child_node('tdInfo', 'Preprocess')

        td_info = self.conf_pre['tdInfo']
        this_node = '->'.join(['Preprocess', 'tdInfo'])
        td_key = {'valid_dep_dif': dict, 'correct0drift': bool}
        for key, val in td_key.items():
            if key not in td_info:
                return False, miss_key(key, this_node)

            td_info_item = td_info[key]
            if not isinstance(td_info_item, val):
                return False, invalid_struct(this_node + '->' + key)
            if key == 'valid_dep_dif':
                vdd_node = '->'.join([this_node, 'valid_dep_dif'])
                for k, v in td_info_item.items():
                    if not isinstance(v, (int, float)):
                        return False, invalid_value(k, vdd_node)
        state, resp = self.detect_orig.rbr.td()
        if not state:
            return state, resp

        state, resp = preprocess_data_module_detect('td', self.nc_path,
                                                    'PreprocessData',
                                                    self.prefix)
        if not state:
            return state, resp
        return True, None


def struct_detect_asd(conf_file):
    str_pre = 'Preprocess'
    str_ssl = 'adcpSslDetect'
    str_adinfo = 'adcpInfo'
    str_save = 'adcpSavePath'
    str_vdd = 'valid_dep_dif'
    str_filter = 'filter'
    str_0drift = 'correct0drift'
    base_key = ['prefix', str_pre]
    for i, val in enumerate(base_key):
        if val not in conf_file:
            return False, ' '.join(
                ['The', val, 'node is missing in the configuration file.'])
    conf_pre = conf_file[str_pre]
    prefix = conf_file['prefix']

    if str_ssl not in conf_pre:
        return False, miss_child_node(str_ssl, str_pre)
    ssl_detect = conf_pre[str_ssl]
    ssl_detect_node = '->'.join([str_pre, 'str_ssl'])
    for key, val in ssl_detect.items():
        if not isinstance(val, str):
            return False, invalid_value(key, ssl_detect_node)
        filepath = ''.join([prefix, val])
        state, resp = file_detect(filepath, '.nc',
                                  invalid_value(key, ssl_detect_node))
        if not state:
            return state, resp

    if str_adinfo not in conf_pre:
        return False, miss_child_node(str_adinfo, str_pre)
    adcp_info = conf_pre[str_adinfo]
    this_node = '->'.join([str_pre, str_adinfo])
    adcp_key = {str_0drift: bool, str_vdd: dict, str_filter: dict}
    for key, val in adcp_key.items():
        if key not in conf_pre[str_adinfo]:
            return False, miss_key(key, this_node)
        if not isinstance(adcp_info[key], val):
            return False, invalid_value(key, this_node)
        if key == str_vdd:
            vdd_node = '->'.join([this_node, str_vdd])
            vdd = adcp_info[str_vdd]
            for k, v in vdd.items():
                if not isinstance(v, (int, float)):
                    return False, invalid_value(k, vdd_node)
        if key == str_filter:
            filter_node = '->'.join([this_node, str_filter])
            adcp_filter = adcp_info[str_filter]
            for k, v in adcp_filter.items():
                filter_sta_node = '->'.join([filter_node, k])
                if not isinstance(v, dict):
                    return False, invalid_struct(filter_sta_node)
                for kk, vv in v.items():
                    if not isinstance(vv, (int, float)):
                        return False, invalid_value(kk, filter_sta_node)
                    if kk == 'scatter' and not isinstance(vv, int):
                        return False, invalid_value(kk, filter_sta_node)

    if str_save not in conf_pre:
        return False, miss_child_node(str_save, str_pre)
    this_node = '->'.join([str_pre, str_save])
    adcp_save_path = conf_pre[str_save]
    if not isinstance(adcp_info, dict):
        return False, invalid_struct(this_node)

    for key, val in adcp_save_path.items():
        if not isinstance(val, str):
            return False, invalid_value(key, this_node)
        filepath = ''.join([prefix, val])
        (dirpath, filename) = path.split(filepath)
        if not path.exists(dirpath):
            return False, ' '.join(
                ['The NC file directory corresponding to the key',
                 key, ' in the node ', this_node,
                 'does not exist. Please select a existing directory.'])
        if path.splitext(filename)[-1] != '.nc':
            return False, ' '.join(
                ['The NC file extension corresponding to the key',
                 key, ' in the node ', this_node, 'is incorrect.'])
    return True, None


def miss_child_node(child_node, node):
    return ' '.join(
        ['The child node', child_node, 'is missing in the node', node])


def miss_key(key, node):
    return ' '.join(
        ['The key', key, 'is missing in the node', node])


def invalid_struct(node):
    return ' '.join(['Invalid structure occurs in the node', node])


def invalid_value(key, node):
    return ' '.join(['The value corresponding to the', key, 'in the node', node,
                     'is invalid'])


def preprocess_data_module_detect(name, nc_path, str_data_pre, prefix):
    if name not in nc_path:
        return False, miss_child_node(name, str_data_pre)

    this_node = ''.join([str_data_pre, '->', name])
    if not isinstance(nc_path[name], dict):
        return False, invalid_struct(this_node)

    for key, val in nc_path[name].items():
        if not isinstance(val, str):
            return False, invalid_value(key, this_node)
        filepath = ''.join([prefix, val])
        (dirpath, filename) = path.split(filepath)
        if not path.exists(dirpath):
            return False, ' '.join(
                ['The NC file directory corresponding to the key',
                 key, ' in the node ', this_node,
                 'does not exist. Please select a existing directory.'])
        if path.splitext(filename)[-1] != '.nc':
            return False, ' '.join(
                ['The NC file extension corresponding to the key',
                 key, ' in the node ', this_node, 'is incorrect.'])
    return True, None


class OriginalDataDetect(object):
    def __init__(self, prefix, orig_data, str_data_orig):
        self.rbr = RBR(prefix, orig_data, str_data_orig)
        self.rdi = RDI(prefix, orig_data, str_data_orig)


class RBR(object):
    def __init__(self, prefix, orig_data, str_data_orig):
        self.prefix = prefix
        self.orig_data = orig_data
        self.str_data_orig = str_data_orig

    def base(self, name):
        if name not in self.orig_data:
            return False, miss_child_node(name, self.str_data_orig)

        this_node = '->'.join([self.str_data_orig, name])

        if not isinstance(self.orig_data[name], dict):
            return False, invalid_struct(this_node)

        for key, val in self.orig_data[name].items():
            if not isinstance(val, str):
                return False, invalid_value(key, this_node)
            filepath = ''.join([self.prefix, val])
            file_ls = glob(''.join([filepath, '*']))
            if not len(file_ls):
                return False, ' '.join(
                    ['Invalid', name, 'data file path.'])
        return True, None

    def td(self):
        return self.base('td')

    def ctd(self):
        return self.base('ctd')


class RDI(object):
    def __init__(self, prefix, orig_data, str_data_orig):
        self.prefix = prefix
        self.orig_data = orig_data
        self.str_data_orig = str_data_orig

    def adcp(self):
        name = 'adcp'
        if name not in self.orig_data:
            return False, miss_child_node(name, self.str_data_orig)

        this_node = '->'.join([self.str_data_orig, name])
        if not isinstance(self.orig_data[name], dict):
            return False, invalid_struct(this_node)

        for key, val in self.orig_data[name].items():
            this_node = '->'.join([self.str_data_orig, name, key])
            if not isinstance(val, dict):
                return False, invalid_struct(this_node)

            for k in ['mat', 'beam', 'file_details', 'deployment']:
                if k not in val:
                    return False, miss_key(k, this_node)

                v = val[k]
                if not isinstance(v, str):
                    return False, invalid_value(k, this_node)

                if k == 'beam':
                    state, resp = self.beam_detect(v)
                else:
                    state, resp = self.multi_detect(k, v)
                if not state:
                    return state, ' '.join([resp, 'in the node', this_node])
        return True, None

    def beam_detect(self, val):
        filepath = ''.join([self.prefix, val])
        for i in range(4):
            resp = ['Invalid beam file path.', ' '.join(
                ['Beam', str(i), 'file with name conflict'])]
            beam_files = glob(''.join([filepath, str(i + 1), '*']))
            if len(beam_files) != 1:
                return False, resp[len(beam_files) > 1]
        return True, None

    def multi_detect(self, key, val):
        key2ext = {'mat': '.mat', 'file_details': None, 'deployment': '.whp'}
        filepath = ''.join([self.prefix, val])
        return file_detect(filepath, key2ext[key])

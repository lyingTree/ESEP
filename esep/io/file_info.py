# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : file_info.py

                   Start Date : 2020-06-12 22:11:12

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

Get basic information of various files.
File type detection

-------------------------------------------------------------------------------
"""

import csv
import imghdr
import json
from pathlib import Path

import netCDF4 as nc
import netCDF4 as nc
import pandas as pd
import shapefile
import shapefile
from PIL import Image
from PIL.TiffTags import TAGS

type_dict = {
    b'CDF\x01': 'netcdf-CLASSIC', b'CDF\x02': 'netcdf-64BIT',
    b'\x89HDF': 'netcdf4', b'\xef\xbb\xbf': 'csv',
    b'PK\x03\x04': 'xlsx', b'\xd0\xcf\x11\xe0': 'xls',
}


def get_encoding(file_path) -> str:
    """Fetches the encoding of file.

    :param file_path: class：str, The path of a file
    :return: class:str, The encoding the file.
    ------------------------------------------------------------------
    Examples:

    """
    tmp_file = open(file_path, 'rb')
    detector = UniversalDetector()
    for line in tmp_file.readlines():
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    tmp_file.close()
    return detector.result['encoding']


class FileInfo(object):

    def __init__(self, filepath: Uion[str, Path], file_type=None):
        self.filepath = filepath
        self.file_type = file_type

    def get_info(self):
        if self.file_type in ['netcdf-CLASSIC', 'netcdf-64BIT', 'netcdf4', 'WRF']:
            return self._get_ncinfo()
        elif self.file_type == 'csv':
            return self._get_csvinfo()
        elif self.file_type in ['xlsx', 'xls']:
            return self._get_excelinfo()
        elif self.file_type == 'shapefile':
            return self._get_shpinfo()
        elif self.file_type in ['jpeg', 'png', 'tiff']:
            return self._get_imginfo()
        elif self.file_type == 'text':
            return self._get_textinfo()
        elif self.file_type == 'binary':
            pass  # TODO: The binary file has not found suitable test data
        else:
            raise TypeError("Unsupported file types")

    def _get_ncinfo(self):
        tmp_file = nc.Dataset(self.filepath)
        var_dict = {}
        for var_name in list(tmp_file.variables.keys()):
            attr_dict = {}
            var_dict[var_name] = attr_dict
            var = tmp_file[var_name]
            if hasattr(var, 'units'):
                attr_dict['units'] = var.units

            if hasattr(var, 'long_name'):
                attr_dict['name'] = var.long_name
            elif hasattr(var, 'name'):
                attr_dict['name'] = var.name

            if hasattr(var, 'description'):
                attr_dict['description'] = var.description

            dim_names = []
            var_shape = []
            for dim in var.get_dims():
                dim_names.append(dim.name)
                var_shape.append(dim.size)
            attr_dict['dim'] = dim_names
            attr_dict['shape'] = var_shape

        return json.dumps(var_dict)

    def _get_csvinfo(self):
        tmp_file = pd.read_csv(self.filepath, encoding=get_encoding(self.filepath), header=None)
        head_info = tmp_file.head().to_json()
        return head_info

    def _get_excelinfo(self):
        tmp_file = pd.read_excel(self.filepath, encoding=get_encoding(self.filepath), header=None)
        head_info = tmp_file.head().to_json()
        return head_info

    def _get_shpinfo(self):
        tmp_file = shapefile.Reader(self.filepath)
        var_dict = {'bbox': tmp_file.bbox.tolist(), 'shapeTypeName': tmp_file.shapeTypeName}

        return json.dumps(var_dict)

    def _get_imginfo(self):
        img = Image.open(self.filepath)
        var_dict = {}
        if img.format == 'JPEG':
            var_dict['mode'] = img.mode
            var_dict['size'] = img.size
            var_dict['info'] = img.info
        elif img.format == 'PNG':
            var_dict['mode'] = img.mode
            var_dict['size'] = img.size
            var_dict['info'] = img.text
        elif img.format == 'TIFF':
            tags = img.tag_v2
            for key in tags:
                if 'XResolution' in TAGS[key] or 'YResolution' in TAGS[key]:
                    var_dict[TAGS[key]] = tags[key].numerator
                    continue
                var_dict[TAGS[key]] = tags[key]
        return json.dumps(var_dict)

    def _get_textinfo(self):
        tmp_file = open(self.filepath, 'r',
                        encoding=get_encoding(self.filepath))

        line = tmp_file.readline()
        var_dict = {}
        content = []
        dialect = csv.Sniffer().sniff(line)
        var_dict['delimiter'] = dialect.delimiter
        var_dict['value'] = content
        while line:
            line = line.split(dialect.delimiter)
            content.append(line)
            line = tmp_file.readline()
        tmp_file.close()

        return json.dumps(var_dict)


class FileTypeCheck(object):
    def __init__(self, filepath):
        self.filepath = filepath

    def check(self):
        file = open(self.filepath, 'rb')
        for code, file_type in type_dict.items():
            file.seek(0)
            file_code = file.read(len(code))
            if file_code == code:
                if self.is_wrf(file_type):
                    return 'WRF'
                return file_type
        # Recognize image file formats
        if imghdr.what(self.filepath):
            return imghdr.what(self.filepath)
        # Recognize shapefile
        try:
            shapefile.Reader(self.filepath)
            return 'shapefile'
        except Exception:
            pass
        # TODO: Recognize Micaps file

        # Recognize whether it is a text file
        if self.is_binary():
            return 'binary'
        return 'text'

    def is_wrf(self, file_type):
        if 'netcdf' in file_type:
            tmp = nc.Dataset(self.filepath)
            if hasattr(tmp, 'TITLE'):
                if 'WRF' in tmp.TITLE or 'wrf' in tmp.TITLE:
                    return True
        return False

    def is_binary(self):
        fin = open(self.filepath, 'rb')
        try:
            chunk_size = 1024
            while 1:
                chunk = fin.read(chunk_size)
                if b'\0' in chunk:  # found null byte
                    return 1
                if len(chunk) < chunk_size:
                    break  # done
        finally:
            fin.close()
        return 0

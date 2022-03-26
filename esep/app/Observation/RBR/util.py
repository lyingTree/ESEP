# -*- coding:uft-8 -*-
"""
#------------------------------------------------------------------------------#
#                                                                              #
#                 Project Name : Atmosphere&Ocean                              #
#                                                                              #
#                    File Name : util.py                                       #
#                                                                              #
#                  Contributor : D.CW                                          #
#                                                                              #
#                   Start Date : 2020-11-20 15:42:15                           #
#                                                                              #
#                  Last Update : 2020-11-20 16:04:56                           #
#                                                                              #
#                        Email : dengchuangwu@gmail.com                        #
#                                                                              #
#------------------------------------------------------------------------------#
# Introduction:                                                                #
# Tool functions for data obtained by RBR’s instruments                        #
#                                                                              #
#----------------------------------------------------------------------------- #
# Functions:                                                                   #
#   offset_from_utc -- Check the metadata offsetfromutc.                       #
#   create_meta_grp -- Create attribute groups based on the metadata set.      #
#                                                                              #
#------------------------------------------------------------------------------#
"""


def offset_from_utc(meta):
    """Check whether the metadata set has time zone offset metadata,
    if exist, return its value, if not, return False.

    :param meta: Metadata dictionary
    :return:
    """
    for key, val in meta.items():
        if isinstance(val, dict):
            if 'offsetfromutc' in val:
                return True, val['offsetfromutc']
        elif isinstance(val, list):
            for i, it in enumerate(val):
                if 'offsetfromutc' in it:
                    return True, it['offsetfromutc']
    return False, False


def create_meta_grp(out_file, meta: dict = None):
    """Create attribute groups based on the metadata set.

    :param out_file: Output nc file object
    :param meta: Metadata dictionary
    :return:
    """
    if meta is not None:
        meta_grp = out_file.createGroup("Meta Group")
        sub_meta_grp = []
        var_meta_grp = []
        for key, val in meta.items():
            n = len(sub_meta_grp)
            sub_meta_grp.append(meta_grp.createGroup(key))
            if isinstance(val, dict):
                for k, v in val.items():
                    # Note:The value here means that we need to convert the data
                    # time to East 8 time zone.
                    if k == 'offsetfromutc':
                        v = 8
                    sub_meta_grp[n].setncattr(k, v)
            elif isinstance(val, list):
                for i, it in enumerate(val):
                    m = len(var_meta_grp)
                    var_meta_grp.append([sub_meta_grp[n].createGroup(
                        ' '.join([it['name'], 'Meta Group'])), []])
                    for k, v in it.items():
                        if isinstance(v, dict):
                            nn = len(var_meta_grp[m][1])
                            var_meta_grp[m][1].append(
                                var_meta_grp[m][0].createGroup(k))
                            for kk, vv in v.items():
                                var_meta_grp[m][1][nn].setncattr(kk, vv)
                        else:
                            if k == 'index':
                                continue
                            var_meta_grp[m][0].setncattr(k, v)
            else:
                sub_meta_grp[n].setncattr(key, val)
        return True
    else:
        return False

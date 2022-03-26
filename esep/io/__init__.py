# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : __init__.py

                   Start Date : 2022-03-25 07:39

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

path2nc -- Convert the name of files to netCDF4.Dataset object

-------------------------------------------------------------------------------
"""


def path2nc(files_path) -> list:
    """Convert the name of files to netCDF4.Dataset object.

    :param files_path: class:str, The path of multiple files, which can
    contain wildcards
    :return: class: list, The list of netCDF4.Dataset
    ------------------------------------------------------------------
    Examples:

    """
    rslt = []
    file_ls = glob(files_path)
    for i in range(np.size(file_ls)):
        rslt.append(Dataset(file_ls[i]))
    return rslt

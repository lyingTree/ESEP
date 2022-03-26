# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : general.py

                   Start Date : 2022-03-25 05:45

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""

import pandas as pd

from ESEP.esep.reader.base import NormalReader


class ExcelReader(NormalReader):
    def __init__(self, fp):
        super(ExcelReader, self).__init__(fp)
        if self.fp.suffix == '.csv':
            self.reader = pd.read_csv
        elif self.fp.suffix in ['.xls', '.xlsx']:
            self.reader = pd.read_excel
        else:
            raise ValueError('Invalid File Type')

    def get_data(self, col_names=None, col_idx=None):
        if col_names is None and col_idx is None:
            raise ValueError('')
        return self.ds[col_names]


class TxtReader(NormalReader):
    pass

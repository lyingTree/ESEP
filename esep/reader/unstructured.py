# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : unstructured.py

                   Start Date : 2022-03-25 05:44

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""

from ESEP.esep.reader.base import UnstructuredReaderModel


class FvcomReader(UnstructuredReaderModel):
    u = None
    v = None
    lonc = None
    latc = None
    zeta = None
    h = None
    bot_nthck = None
    bot_dthck = None
    time_name = 'Times'

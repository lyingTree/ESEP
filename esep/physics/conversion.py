# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : conversion.py

                   Start Date : 2022-03-25 07:44

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""


def height2lev(height):
    return 1000 / np.exp(height / 7)


def lev2height(lev):
    return 7 * np.log(1000. / lev)


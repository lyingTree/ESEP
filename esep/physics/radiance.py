# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : radiance.py

                   Start Date : 2022-03-25 07:46

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""


def rad2bt(rad: np.ndarray, freq: np.ndarray) -> np.ndarray:
    """ Use Planck function to calculate brightness temperature

    :param rad: radiance, the rightmost dimension is the channel
    :param freq: frequency, Same size as the rightmost dimension of radiance
    :return: brightness temperature

    Reference
    ------
    .. [#] 吴晓.(1998).地球大气透过率及辐射率计算. 应用气象学报(01),3-5.

    """
    c1 = 1.191042 * 10 ** (-5)
    c2 = 1.4387752
    bt = np.ones(np.shape(rad))
    for i, wn in enumerate(freq):
        bt[..., i] = c2 * wn / np.log((c1 * (wn ** 3)) / rad[..., i] + 1)
    return bt


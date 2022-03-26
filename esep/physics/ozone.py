# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : ozone.py

                   Start Date : 2022-03-25 07:44

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""


def ozone_burden(ozone: np.ndarray, pressure: np.ndarray, bot_p: float, top_p: float) -> np.ndarray:
    """
    计算指定气压层之间的臭氧厚度，单位为：多普生单位(Dobson unit, DU)

    :param ozone: 三维臭氧矩阵，必须有一维度跟pressure的长度一致
    :param pressure: 气压序列
    :param bot_p: 计算气压层厚度的底层气压
    :param top_p: 计算气压层厚度的顶层气压
    :return: 臭氧厚度的水平分布
    """
    ozone_shp = list(np.shape(ozone))

    # 检测pressure为哪一维度，然后将其交换至最右维，以便进行多维扩展
    p_dim_idx = ozone_shp.index(len(pressure))
    ozone_shp[p_dim_idx], ozone_shp[-1] = ozone_shp[-1], ozone_shp[p_dim_idx]
    ozone_shp[-1] = 1

    # 计算恒定压力水平系统中bottom pressure和top pressure之间的各层气压厚度
    dp = dpres1d(pressure, bot_p, top_p)

    # np.tile 将dp进行了多维扩展，然后将最右维的pressure维交换回原来的维度位置，以达到与
    # ozone的shape一致
    dp3 = np.swapaxes(np.tile(dp, ozone_shp), p_dim_idx, -1)
    return np.nansum(ozone * dp3 * 0.789, p_dim_idx)

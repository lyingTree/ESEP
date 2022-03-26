# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : base.py

                   Start Date : 2022-03-25 07:45

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""
import numpy as np


def speed(u, v):
    return np.sqrt(u ** 2 + v ** 2)


def day_night_split(solzen: np.ndarray) -> tuple:
    """
    solar zenith angle (degrees, 0->180; daytime if < 85)

    :param solzen: 天顶角矩阵
    :return: 表示白天，黑夜的矩阵索引的元组

    Reference
    ------
    .. [#] AIRS/AMSU/HSB Version 5 Level 1B Product User Guide(P10)

    """

    return np.where(solzen < 85), np.where(solzen >= 85)


def dpres1d(pressure: np.ndarray or list, bot_p: float, top_p: float) -> np.ndarray:
    """
    计算恒定压力水平系统的各层气压厚度

    :param pressure: 气压序列
    :param bot_p: 计算气压层厚度的底层气压
    :param top_p: 计算气压层厚度的顶层气压
    :return: 与输入气压层数相同的各层气压厚度
    """
    dp = np.full(np.shape(pressure), np.nan)
    len_p = len(pressure)
    lev_start_idx = 0
    lev_last_idx = len_p - 1

    if pressure[1] > pressure[0]:
        tmp_p = pressure
    else:
        tmp_p = pressure[::-1]

    if top_p <= tmp_p[0] and bot_p >= tmp_p[-1]:
        dp[0] = (tmp_p[0] + tmp_p[1]) * 0.5 - top_p
        for lev_idx in range(1, len_p - 1):
            dp[lev_idx] = (tmp_p[lev_idx + 1] - tmp_p[lev_idx - 1]) * 0.5
        dp[len_p - 1] = bot_p - (tmp_p[len_p - 1] + tmp_p[len_p - 2]) * 0.5
    else:
        for lev_start_idx in range(len_p - 1, 0, -1):
            if (tmp_p[lev_start_idx - 1] + tmp_p[lev_start_idx]) / 2 < top_p:
                break

        for lev_last_idx in range(len_p - 1):
            if (tmp_p[lev_last_idx + 1] + tmp_p[lev_last_idx]) / 2 > bot_p:
                break

        if lev_start_idx == lev_last_idx:
            dp[lev_start_idx] = bot_p - top_p
        elif lev_start_idx < lev_last_idx:
            dp[lev_start_idx] = (tmp_p[lev_start_idx] + tmp_p[
                lev_start_idx + 1]) * 0.5 - top_p

            for lev_idx in range(lev_start_idx + 1, lev_last_idx - 1):
                dp[lev_idx] = (tmp_p[lev_idx + 1] - tmp_p[
                    lev_idx - 1]) * 0.5

            dp[lev_last_idx] = bot_p - (
                tmp_p[lev_start_idx] + tmp_p[lev_start_idx + 1]) * 0.5
    return dp


def dbe1(dep, curt_mag, dis, delta):
    """One-dimensional Dynamic Balance Equation.

    :param dep: The depth of water
    :param curt_mag: Tidal current
    :param dis: The distance between the two station
    :param delta: Time Step
    :return: The terms of the dynamic balance equation
    :rtype: tuple
    """
    time_len = np.size(curt_mag[0])
    # Pressure Gradient
    p_grad = 9.80665 * (dep[0][:] - dep[1][:]) / dis[0]

    # Local Acceleration
    local_acc = np.zeros(time_len)
    for i in np.arange(1, time_len - 1):
        local_acc[i] = (curt_mag[1][i + 1] - curt_mag[1][i - 1]) / (delta * 2)

    # Advection Acceleration
    adv_acc = np.zeros(time_len)
    for i in np.arange(time_len):
        adv_acc[i] = curt_mag[1][i] * (curt_mag[0][i] - curt_mag[1][i]) / dis[1]

    # Bottom Friction
    bf = local_acc + adv_acc + p_grad
    return p_grad, local_acc, adv_acc, bf

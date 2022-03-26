# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : interpolate.py

                   Start Date : 2022-03-25 05:26

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""
import numpy as np
from scipy.interpolate import griddata


def station2grid(data, lon, lat, loc_range, det_grid=0.1, method='linear'):
    """Interpolation of station data to equally spaced latitude and longitude grids

    Args:
        data: The data from station
        lon: The longitude of station
        lat: The latitude of station
        loc_range: The range of grids used for interpolation, (lat_min,lat_max,lon_min,lon_max)
        det_grid: The spacing of interpolation grids
        method: The method of Interpolation

    Returns:
        tuple: The longitude, latitude and data after interpolation

    """
    # step1: 先将 lon,lat,data转换成 n*1 的array数组
    lon = np.array(lon).reshape(-1, 1)
    lat = np.array(lat).reshape(-1, 1)
    data = np.array(data).reshape(-1, 1)
    points = np.concatenate([lon, lat], axis=1)

    # step2:确定插值区域的经纬度网格
    lon_min, lon_max, lat_min, lat_max = loc_range

    lon_grid, lat_grid = np.meshgrid(np.arange(lon_min, lon_max + det_grid, det_grid),
                                     np.arange(lat_min, lat_max + det_grid, det_grid))

    # step3:进行网格插值
    grid_data = griddata(points, data, (lon_grid, lat_grid), method=method)[:, :, 0]

    return lon_grid, lat_grid, grid_data

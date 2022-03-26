# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : spatial.py

                   Start Date : 2022-03-25 05:16

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

utils for processing spatial data

-------------------------------------------------------------------------------
#****************************** class: Distance *******************************#
#   pt -- Calculate the distance between two points in Pythagorean Theorem.    #
#   spherical_cos -- Calculate the distance between two points in              #
#                    Spherical law of cosines.                                 #
#   haversine -- Calculate the distance between two points in                  #
#                Haversine formula.                                            #
#   vincenty -- Calculate the distance between two points in                   #
#               Vincenty's formula.                                            #
#                                                                              #
"""
import numpy as np
from pyproj import Geod
from ESEP.esep.physics.base import speed


def find_nearest(obs_coordinate: dict, cell_lonlat: tuple = None, node_lonlat: tuple = None, radius: int = None):
    """ 以观测点为圆心，检索在距离范围内的 cell 和 node
        如果指定了检索半径，那么在检索范围内无检索目标则返回None；
        如果没有指定检索半径，那么返回距离最近的目标

    Args:
        obs_coordinate (dict): 观测站点字典，key为站点名，value为站点经纬度元组，(lon,lat)
        cell_lonlat (tuple): cell中点经纬度元组
        node_lonlat (tuple): node经纬度元组
        radius (int): The radius to search in meters

    Returns:
        观测点字典，key为站点名，value为符合条件的 cell 和 node 组成的字典
    """

    def _find(d1, d2):
        dist = Distance(d1, d2).vincenty
        target_id = np.array([np.argmin(dist)]) if radius is None else np.where(dist < radius)[0]
        return target_id, dist[target_id]

    station_dict = {}
    for name, cor in obs_coordinate.items():
        tmp = station_dict[name] = {}
        if cell_lonlat is not None:
            tmp['cell_id'], tmp['cell_distance'] = _find(cell_lonlat, cor)
        if node_lonlat is not None:
            tmp['node_id'], tmp['node_distance'] = _find(node_lonlat, cor)
    return station_dict


class Distance:
    """Calculate the distance between two points.

    Created date: 2020-10-08 09:46:27
    Last modified date: 2022-03-25 05:14:14
    Contributor: D.CW
    Email: dengchuangwu@gmail.com
    """

    def __init__(self, d1, d2):
        """Initialization

        :param d1: A point representing [longitude,latitude] in decimal degrees.
        :param d2: A point representing [longitude,latitude] in decimal degrees.
        """
        self.lon1, self.lat1 = d1
        self.lon2, self.lat2 = d2

        self.lon1_rad, self.lat1_rad = np.deg2rad(d1)
        self.lon2_rad, self.lat2_rad = np.deg2rad(d2)

        self.dlon = self.lon2 - self.lon1
        self.dlon_rad = np.deg2rad(self.dlon)
        self.dlat = self.lat2 - self.lat1
        self.dlat_rad = np.deg2rad(self.dlat)

        self.r = 6371

    @property
    def pt(self):
        """Pythagorean Theorem

        :return: The distance in m.
        :rtype: float

        :Example:

        >>> d1 = [101.1, 20]
        >>> d2 = [150, 2]
        >>> dis = Distance(d1,d2)
        >>> dis.pt
        5794109.319140563

        """
        dsigma = np.sqrt(self.dlon ** 2 + self.dlat ** 2)

        return self.r * dsigma * 1000

    @property
    def spherical_cos(self):
        """Spherical law of cosines

        :return: The distance in m.
        :rtype: float

        :Example:

        >>> d1 = [101.1, 20]
        >>> d2 = [150, 2]
        >>> dis = Distance(d1,d2)
        >>> dis.spherical_cos
        5671184.713237043

        """
        dsigma = np.arccos(
            np.sin(self.lat1_rad) * np.sin(self.lat2_rad) + np.cos(self.lat1_rad) * np.cos(self.lat2_rad) * np.cos(
                self.dlon_rad))

        return self.r * dsigma * 1000

    @property
    def haversine(self):
        """Haversine formula

        :return: The distance in m.
        :rtype: float

        :Example:

        >>> d1 = [101.1, 20]
        >>> d2 = [150, 2]
        >>> dis = Distance(d1,d2)
        >>> dis.haversine
        5671184.713237043

        """
        dsigma = 2 * np.arcsin(np.sqrt(
            np.sin(self.dlat_rad / 2) ** 2 + np.cos(self.lat1_rad) * np.cos(self.lat2_rad) * np.sin(
                self.dlon_rad / 2) ** 2))

        return self.r * dsigma * 1000

    @property
    def vincenty(self) -> np.ndarray:
        """Vincenty's formula

        :return: The distance in m.
        :rtype: np.ndarray

        :Example:

        >>> d1 = [101.1, 20]
        >>> d2 = [150, 2]
        >>> dis = Distance(d1,d2)
        >>> dis.vincenty
        5671184.7132370435

        """
        size1, size2 = np.size(self.lon1), np.size(self.lon2)
        # 此处是为了将lon1,lat1,lon2,lat2的维度、个数统一，以备inv使用
        tmp_lon1 = np.repeat(np.expand_dims(np.array([self.lon1]), 1), size2)
        tmp_lat1 = np.repeat(np.expand_dims(np.array([self.lat1]), 1), size2)
        tmp_lon2 = np.repeat(np.expand_dims(np.array([self.lon2]), 1), size1)
        tmp_lat2 = np.repeat(np.expand_dims(np.array([self.lat2]), 1), size1)
        _, _, dist = Geod(ellps='sphere').inv(tmp_lon1, tmp_lat1, tmp_lon2, tmp_lat2)
        return dist


class CoordinateTransform:
    """
    海洋上，以正北为0，顺时针旋转，表示去向，范围 [0,360]
    数学上，以x轴为0，一般x轴为正东，逆时针旋转为正，顺时针旋转为负，表去向，范围 [-180,180]
    """

    def __init__(self):
        pass

    @staticmethod
    def ocean2uv(current_speed, current_direction):
        math_direction = np.deg2rad(current_direction)
        u = np.sin(math_direction) * current_speed
        v = np.cos(math_direction) * current_speed
        return u, v

    @staticmethod
    def uv2ocean(u, v):
        # direction
        current_dir = np.rad2deg(np.arctan2(v, u))
        first2third_quadrant = np.where(np.logical_and(-180 <= current_dir, current_dir <= 90))
        fourth_quadrant = np.where(np.logical_and(90 < current_dir, current_dir <= 180))
        current_dir[first2third_quadrant] = 90 - current_dir[first2third_quadrant]
        current_dir[fourth_quadrant] = 450 - current_dir[fourth_quadrant]

        # speed
        current_speed = speed(u, v)

        return current_dir, current_speed


def theta_angle(d1, d2):
    k = (d2["lat"] - d1["lat"]) / (d2["lon"] - d1["lon"])
    return np.rad2deg(np.arctan(k))


def beam2earth(b1, b2, b3, b4, roll, pitch, head, ang_b, ang_m, is_convex=True):
    # <editor-fold desc="Beam-to-Instrument Transformation">
    a = 1 / np.sin(np.deg2rad(ang_b))
    b = 1 / (4 * np.cos(np.deg2rad(ang_b)))
    c = int((-1) ** (is_convex + 1))
    x = a * c * (b1 - b2)
    y = a * c * (b4 - b3)
    z = b * (b1 + b2 + b3 + b4)
    # </editor-fold>

    # <editor-fold desc="Instrument-to-Geomagnetic Transformation">
    cr = np.cos(np.deg2rad(roll))
    sr = np.sin(np.deg2rad(roll))

    cp = np.cos(np.deg2rad(pitch))
    sp = np.sin(np.deg2rad(pitch))

    ch = np.cos(np.deg2rad(head))
    sh = np.sin(np.deg2rad(head))

    u = (ch * cr + sh * sp * sr) * x + (sh * cp) * y + (
        ch * sr - sh * sp * cr) * z
    v = (-sh * cr + ch * sp * sr) * x + (ch * cp) * y + (
        -sh * sr - ch * sp * cr) * z
    w = (-cp * sr) * x + sp * y + (cp * cr) * z
    # </editor-fold>

    # <editor-fold desc="Geomagnetc-to-Earth Transformation">
    u_e = u * np.cos(np.deg2rad(ang_m)) + v * np.sin(np.deg2rad(ang_m))
    v_e = v * np.cos(np.deg2rad(ang_m)) - u * np.sin(np.deg2rad(ang_m))
    w_e = w
    # </editor-fold>
    return u_e, v_e, w_e


# heading的取值范围 [000.00,359.99]，顺时针旋转，表示磁北与beam3的夹角。
# 如果仪器部署时，设置了EB指令即设置了磁偏角，那么heading就表示已经经过了磁偏角的矫正了。
# 即不需要在程序处理时减去或加上磁偏角了
def rey_proj(rey12, rey34, head):
    theta = np.expand_dims(head, axis=1)
    rey_east = rey34 * np.sin(np.deg2rad(theta)) + rey12 * np.cos(
        np.deg2rad(theta))
    rey_north = rey34 * np.cos(np.deg2rad(theta)) - rey12 * np.sin(
        np.deg2rad(theta))
    return rey_east, rey_north


def proj(curt_e, curt_n, theta):
    theta = np.deg2rad(theta)
    along = -(curt_n * np.sin(theta) + curt_e * np.cos(theta))
    cross = curt_n * np.cos(theta) - curt_e * np.sin(theta)

    # west: flow in is negative , flow out is positive
    #       along: -N-E
    #       cross: N-E
    # east: flow in is positive , flow out is negative
    #       along: -N-E
    #       cross: N-E
    return along, cross


def lat_detect(lat: np.ndarray) -> np.ndarray:
    lat[lat > 90] -= 90
    return lat

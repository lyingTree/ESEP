# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : unstructured.py

                   Start Date : 2022-03-25 05:16

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

utils for processing unstructured data

-------------------------------------------------------------------------------
"""
import numpy as np

from pygeos import Geometry, multipoints, polygons, STRtree, get_parts, coverage_union_all


def _arr2polygon(coordinate: np.ndarray) -> Geometry:
    """Compared with shapely，the pygeos maximises CPU performance and is much faster

    Args:
        coordinate (np.ndarray): coordinate array; array(lon1,lat1,lon2,lat2,lon3,lat3)

    Returns:
        Geometry: coordinate Polygon

    """
    return polygons(np.reshape(coordinate, [3, 2]))


def construct_mask(fvcom_lon: np.ndarray, fvcom_lat: np.ndarray, fvcom_tri: np.ndarray, lon: np.ndarray,
                   lat: np.ndarray) -> tuple:
    """Constructs a mask for a list of points which is true for points lying outside the specified fvcom domain and
    false for those within.

    Args:
        fvcom_lon (np.ndarray): The array of the lon positions of the FVCOM grid nodes
        fvcom_lat (np.ndarray): The array of the lat positions of the FVCOM grid nodes
        fvcom_tri (np.ndarray): Qx3 python indexed triangulation array for the FVCOM grid
        lon (np.ndarray): The array of the longitudes to mask
        lat (np.ndarray): The array of the longitudes to mask

    Returns:
        tuple: A 1d boolean array true for points outside the FVCOM domain and false for those within
        and fvcom domain polygon

    """
    fvcom_ll = np.concatenate([np.array(fvcom_lon).reshape(-1, 1), np.array(fvcom_lat).reshape(-1, 1)], axis=1)
    grid_points = get_parts(multipoints(np.asarray([lon.flatten(), lat.flatten()]).T))
    tri_ll = fvcom_ll[fvcom_tri]
    tri_ll_shp = np.shape(tri_ll)
    domain_polygon = coverage_union_all(
        np.apply_along_axis(_arr2polygon, 1, np.reshape(tri_ll, [tri_ll_shp[0], np.multiply(*tri_ll_shp[1:])])))
    out_of_domain_mask = np.full_like(grid_points, True, dtype=bool)
    tree = STRtree(grid_points)
    out_of_domain_mask[tree.query(domain_polygon, predicate='covers').tolist()] = False
    out_of_domain_mask = np.reshape(out_of_domain_mask, np.shape(lon))
    return out_of_domain_mask, domain_polygon


def nodes2elems(nodes: np.ndarray, tri: np.ndarray) -> np.ndarray:
    """ Calculate an element-centre value based on the average value for the nodes from which it is formed.
    This involves an average, so the conversion from nodes to elements cannot be reversed without smoothing.

    Args:
        nodes (np.ndarray): Array of unstructured grid node values to move to the element centres.
        tri (np.ndarray): Array of shape (nelem, 3) comprising the list of connectivity for each element.

    Returns:
        np.ndarray: Array of values at the grid nodes.

    """
    if np.ndim(nodes) == 1:
        elems = nodes[tri].mean(axis=-1)
    else:
        elems = nodes[..., tri].mean(axis=-1)
    return elems

# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : utils.py
                      
                   Start Date : 2021-08-20 11:22
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
Introduction:

utility functions
提供了各类小功能的实现，如维度的调序，截取两个序列的相同元素等
                                                                              
--------------------------------------------------------------------------------
# Functions:                                                                  #
#   adjust_dim -- Adjust the position of the dimensions.                      #
#   extra_same_elem -- Extract the same elements from two sequence.           #
#   get_dims -- Fetches the dimensions of the object.                         #
#   is_number -- Judge the string whether is a digital string.                #
#   ls2slice -- Convert the sequence to a slice or itself.                    #
#-----------------------------------------------------------------------------#
"""
import re

import numpy as np


def adjust_dim(dim_rng: list or tuple, orig_dim: list or tuple, trgt_dim: list or tuple) -> tuple:
    """Adjust the position of the dimensions.

    :param dim_rng: class:list, class:tuple,  A list or tuple of ranges of
    various dimensions
    :param orig_dim: class:list, class:tuple, A list or tuple of file
    dimension names
    :param trgt_dim: class:list, class:tuple, A list or tuple of variable
    dimension names
    :return: class:tuple, A tuple of dim_rng and orig_dim, which have been
    adjusted.
    ------------------------------------------------------------------
    Examples:

    """
    for i in np.arange(len(trgt_dim) - 1):
        dim_ind = orig_dim.index(trgt_dim[i])
        dim_rng[i], dim_rng[dim_ind] = dim_rng[dim_ind], dim_rng[i]
        orig_dim[i], orig_dim[dim_ind] = orig_dim[dim_ind], orig_dim[i]
    return dim_rng, orig_dim


def extra_same_elem(ls1, ls2) -> list:
    """Extract the same elements from two sequence.

    :param ls1: class:list，class:ndarray(one-dimension), A list
    :param ls2: class:list，class:ndarray(one-dimension), A list
    :return: class:list, A new list with elements common to lists
    ------------------------------------------------------------------
    Examples:

    """
    return list(set(ls1).intersection(set(ls2)))


def get_dims(obj) -> dict:
    """Fetches the dimensions of the object.

    :param obj: A object of a file or dataset
    :return: the dimension of this object
    ------------------------------------------------------------------
    Examples:

    """
    if hasattr(obj, 'dims'):
        dims = obj.dims
    elif hasattr(obj, 'dimensions'):
        dims = obj.dimensions
    else:
        dims = obj.dimension
    return dims


def is_number(num_str: str) -> bool:
    """Judge the string whether is a digital string.

    :param num_str: class:str, A string that could be a number
    :return: class:bool, the result of judge whether the string is a number.
    ------------------------------------------------------------------
    Examples:

    """
    pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    rslt = pattern.match(num_str)
    if rslt:
        return True
    else:
        return False


def ls2slice(rng: tuple or list):
    """Convert the sequence to a slice or itself.

    :param rng: class:list, class:tuple, A list or tuple
    :return: class:slice, class:rng, A slice object converted from a
    sequence, or the original rng.
    ------------------------------------------------------------------
    Examples:

    """
    rng = sorted(rng)
    it = iter(rng)
    strt = next(it)
    rslt = []
    for i, x in enumerate(it):
        if x - rng[i] != 1:
            end = rng[i]
            if strt == end:
                rslt.append(slice(strt, strt + 1))
            else:
                rslt.append(slice(strt, end + 1))
            strt = x
    if rng[-1] == strt:
        rslt.append(slice(strt, strt + 1))
    else:
        rslt.append(slice(strt, rng[-1] + 1))

    if len(rslt) > 1:
        return rng
    else:
        return rslt[0]

# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : decorator.py

                   Start Date : 2020-06-05 17:26:44

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:

提供了各种功能的装饰器

-------------------------------------------------------------------------------
"""
from collections import Iterable
from functools import wraps

import numpy as np


def is_none(func):
    """Pre-processing of dimensional data extraction functions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        bdry = kwargs['boundary']
        if bdry is None:
            return list(range(0, np.size(kwargs['var'][:])))
        if isinstance(bdry, tuple):
            shp = np.shape(bdry)
            if shp[0] != 2:
                raise TypeError('Invalid input')
            if np.size(shp) > 1:
                for item in bdry:
                    if isinstance(item, tuple):
                        if len(item) != 2:
                            raise TypeError('Range limit variables are limited to tuple containing two values.')
                        for val in item:
                            if not (isinstance(val, int) or
                                    isinstance(val, float)):
                                raise TypeError('Invalid Type')
                    else:
                        raise TypeError('Invalid Type')
            else:
                for item in bdry:
                    if not (isinstance(item, int) or isinstance(item, float)):
                        raise TypeError('Invalid Type')
        else:
            raise TypeError('Invalid Type')
        return func(*args, **kwargs)

    return wrapper


def decorator_for_class(func):
    """ Class global decorator

    :param func: The function actually called by the decorator
    :return:
    """

    def decorator(cls):
        for name, method in inspect.getmembers(cls):
            if (not inspect.ismethod(method) and not inspect.isfunction(
                method)) or inspect.isbuiltin(method) or hasattr(method,
                                                                 '__funskip__'):
                continue
            setattr(cls, name, func(method))
        return cls

    return decorator


def skipper(func):
    """ Set the attribute __funcskip__ to the function
    :param function func: Functions that need to skip the global decorator
    :return:
    """
    func.__funskip__ = True
    return func

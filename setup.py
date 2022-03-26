# -*- coding:utf-8 -*-

import os
import setuptools

here = os.path.abspath(os.path.dirname(__file__))
exec(open(os.path.join(here, 'esep/version.py')).read())

setuptools.setup(
    name='ESEP',
    description='ESEP - Earth Science Exploration Processing',
    author='Chuangwu Deng',
    url='https://github.com/lyingTree/esep',
    version=__version__,
    license='GPLv2',
    python_requires='>=3.7',
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'netCDF4',
        'pyproj',
        'cartopy',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Researcher'
    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
    setup_requires=['setuptools_scm'],
    tests_require=['pytest']
)

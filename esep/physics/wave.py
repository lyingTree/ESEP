# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : wave.py

                   Start Date : 2022-03-25 07:43

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""


class Wave(object):
    def __init__(self):
        pass

    def hm0(self, ts, dep, p):
        """ Calculate the significant wave height.

        :param ts: time series
        :param dep: Water depth series input
        :param p: number of periodograms
        :return: Spectral wave height/significant wave height = 4*sqrt(m0)
        """
        dep = np.squeeze(dep)
        upgrade = 1
        g = 9.80665
        rslt = np.ones(p)
        num = np.size(ts)
        fs = (num - 1) / (ts[-1] - ts[0])
        num_per_p = np.ceil(num / p).astype(np.int)
        for i in np.arange(p):
            dep_seg = dep[i * num_per_p:(num_per_p * (i + 1)) - 1]
            wave_ele = signal.detrend(dep_seg)
            wave_dep = np.mean(dep_seg)
            fq, spec_sensor = signal.periodogram(wave_ele, fs)
            spec_surf = np.zeros(np.size(fq))
            for j in np.arange(np.size(fq)):
                wave_t = 1 / fq[j]
                wavelength = 1.56 * wave_t ** 2
                if wave_dep / wavelength <= 0.05:
                    # very shallow water
                    wavelength = np.sqrt(g * wave_dep) * wave_t
                elif wave_dep / wavelength <= 0.5:
                    # shallow water
                    wavelength = np.sqrt(g * wave_dep) * (
                        1 - wave_dep / wavelength) * wave_t
                else:
                    # deep water
                    wavelength = wavelength

                spec_surf[j] = spec_sensor[j] * (upgrade ** 2) * (
                    np.cosh(2 * np.pi / wavelength * wave_dep) ** 2)
                if spec_surf[j] / spec_sensor[j] > 10:
                    spec_surf[j] = spec_sensor[j]
            rslt[i] = 4 * np.sqrt(integrate.simps(spec_surf, fq))
        return rslt

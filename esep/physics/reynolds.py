# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : reynolds.py

                   Start Date : 2022-03-25 07:46

                  Contributor : D.CW

                        Email : dengchuangwu@gmail.com

-------------------------------------------------------------------------------
Introduction:



-------------------------------------------------------------------------------
"""


def reynolds_var(u1, u2, n):
    u1_ave = np.nanmean(u1)
    m = np.size(u2)
    A = np.ones([m, n])
    A.fill(np.nan)
    for m, n in product(*[range(m), range(n)]):
        if 0 <= m - (n - 1) / 2 <= m:
            A[m, n] = u2[m - (n - 1) / 2]
    s = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(A), A)), np.transpose(A)), u1_ave)
    u1_wave = np.dot(A, s)
    u1_turb = u1 - u1_ave - u1_wave
    return np.nanstd(u1_turb)


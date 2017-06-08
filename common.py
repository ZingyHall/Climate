"""Common functions and constants."""
from __future__ import division

import os


PRESSURE_LEVELS = [
    300,
    500,
    850,
    925,
    1000,
]


def co2_mass2molefrac(co2):
    """Convert CO2 kg/kg to ppm."""
    M_air = 28.9645
    M_co2 = 44.0095

    return co2 * M_air/M_co2 * 1e6


def cm2inch(*tupl):
    inch = 2.54
    if isinstance(tupl[0], tuple):
        return tuple(i/inch for i in tupl[0])
    else:
        return tuple(i/inch for i in tupl)


def output(subdir=""):
    return path("output", subdir)


def path(basedir, subdir=""):
    path = os.path.join(basedir, subdir)
    if not os.path.exists(path):
        os.makedirs(path)

    return path


def plots(subdir=""):
    return path("plots", subdir)


def tmp(subdir=""):
    return path("tmp", subdir)

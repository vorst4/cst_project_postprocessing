import os

from numpy import pi, log10, array

is_running_on_desktop = os.name == 'nt'

delta = 1e-20


class Paths:
    if is_running_on_desktop:
        root = 'C:/Users/Dennis/Documents/generated_projects'
    else:
        root = '/home/tue/s111167/generated_projects'


class Img:
    width = 32
    height = width


class MSF:
    db_min = -10
    db_max = 80
    n = 3200
    phase_limit = [0., 2. * pi]
    amplitude_limit = [0., 1.]


class SAR:
    db_max = 10
    db_min = -60


class DXF:
    background = array([250., 206., 135.])  # BLUE, GREEN, RED
    n_arc = 1000  # number of points used to approximate an arc
    scalar_permittivity = 1. / 80
    scalar_density = 1. / 2160
    scalar_conductivity = 1. / 1.01
    per0 = 80
    con0 = 0
    den0 = 0

from numpy import pi
import os

is_running_on_desktop = os.name == 'nt'


class Paths:
    root = 'C:/Users/Dennis/Documents/generated_projects'
    src = ''
    dst = 'data.zip'


class Img:
    width = 64
    height = 64


class MSF:
    scalar = 1 / 10e3
    n = 3200
    phase_limit = [0., 2. * pi]
    amplitude_limit = [0., 1.]


class DXF:
    background = (135, 206, 250)
    n_arc = 1000  # number of points used to approximate an arc
    scalar_permittivity = 1. / 80
    scalar_density = 1. / 2160
    scalar_conductivity = 1. / 1.01
    per0 = 80
    con0 = 0
    den0 = 0

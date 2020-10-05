import numpy as np
import pandas as pd
import scipy.interpolate

import settings

REAL = 0
IMAG = 1
X = 0
Y = 1
Z = 2
XYZ = 3
COMPLEX = 2
LABELS = [['ExRe [V/m]', 'ExIm [V/m]'],
          ['EyRe [V/m]', 'EyIm [V/m]'],
          ['EzRe [V/m]', 'EzIm [V/m]']]


class ComplexFieldPerAntenna:
    """
    This object loads the Complex electric Field of each Antenna (cfa) and
    interpolates it to the Img.width and Img.height resolution as defined in
    the settings file. Furthermore, the meshgrid points (xx, zz), unique
    points (x, z), and pixel-size (mm_per_px) are also determined.
    """

    def __init__(self, path_project):

        # get e-fields in project folder
        paths_efield = sorted(list(path_project.glob('e-field*.csv')))

        # number of antenna's
        self.na = len(paths_efield)

        # pre-allocate space for cfa
        self.cfa = np.zeros((
            settings.Img.width * settings.Img.height,
            self.na,
            XYZ,
            COMPLEX
        ))

        # loop through exported e-field per antenna
        points_old, points_new, size_old = None, None, None
        for idx, path_efield in enumerate(paths_efield):

            # read e-field into a pandas DataFrame
            data = pd.read_csv(path_efield, delimiter=';')

            # determine interpolation points
            if idx == 0:
                points_old, points_new, size_old = \
                    _interpolation_points(data)

            # interpolate data to desired resolution
            for dim in range(XYZ):
                for unit in range(COMPLEX):
                    self.cfa[:, idx, dim, unit] = _interpolate(
                        data[LABELS[dim][unit]].values.reshape(size_old),
                        points_old,
                        points_new
                    )

        # set attributes
        self.xx = points_new[0]
        self.zz = points_new[1]
        self.np = len(self.xx)
        self.x = np.unique(self.xx)
        self.z = np.unique(self.zz)
        self.mm_per_px = [self.x[1] - self.x[0],
                          self.z[1] - self.z[0]]


def _interpolation_points(data: pd.DataFrame):
    points_old = (np.unique(data['#x [mm]'].values),
                  np.unique(data['z [mm]'].values))
    points_new = _generate_xz(
        settings.Img.width,
        settings.Img.height,
        (data['#x [mm]'].min(), data['#x [mm]'].max()),
        (data['z [mm]'].min(), data['z [mm]'].max())
    )
    size_old = (len(np.unique(points_old[0])),
                len(np.unique(points_old[1])))
    return points_old, points_new, size_old


def _interpolate(data, points_old, points_new):
    # interpolation function
    interpol = scipy.interpolate.RegularGridInterpolator(points_old, data)

    # apply interpolation and return result
    return interpol(points_new).reshape(-1)


def _generate_xz(nx, nz, x_lim, z_lim):
    # generate linearly distributed xyz within given x and z limits
    x = np.linspace(x_lim[0], x_lim[1], nx)
    z = np.linspace(z_lim[0], z_lim[1], nz)

    # create meshgrid
    xx, zz = np.meshgrid(x, z)

    # return flattened meshgrid
    return xx.reshape(-1), zz.reshape(-1)

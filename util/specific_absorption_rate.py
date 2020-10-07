from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

import settings
from .mean_squared_field import MeanSquareField
from .print import Print


class SpecificAbsorptionRate:
    def __init__(self, print_: Print.log):
        self.print_ = print_
        self.sar = None
        self.max = 0
        self.min = 10
        self.msf = None

    def generate_sar(
            self,
            msf_obj: MeanSquareField,
            map_density,
            map_conductivity
    ) -> SpecificAbsorptionRate:
        delta = 1e-20
        self.msf = msf_obj
        img_shape = (settings.Img.width, settings.Img.height)
        self.sar = msf_obj.msf.reshape(img_shape) * map_conductivity / (
                map_density + delta)
        return self

    def save_map(self):
        folder = str(self.msf.folder).replace('msf', 'sar')
        filename = self.msf.filename.replace('msf', 'sar')
        if not Path(folder).exists():
            Path(folder).mkdir()

        cv2.imwrite(filename, self.to_img())

    def to_img(self) -> np.ndarray:
        delta = 1e-20

        # use db scale
        sar = 10 * np.log10(self.sar + delta)

        # save min/max value
        if np.max(sar) > self.max:
            self.max = np.max(sar)
        min_ = np.min(sar[sar != 10*np.log10(delta)])  # ignore sar == 0
        if min_ < self.min:
            self.min = min_

        # log if sar exceeds the maximum given in the settings file
        if np.max(sar) > settings.SAR.db_max:
            self.print_('WARNING: SAR exceeds given maximum\n'
                        '\tsar_max=%f\n\t1/settings db_max=%f' %
                        (np.max(sar), 1 / settings.SAR.db_max))

        # clip
        sar[sar < settings.SAR.db_min] = settings.SAR.db_min
        sar[sar > settings.SAR.db_max] = settings.SAR.db_max

        # map to range [0, 255]
        a = (settings.SAR.db_max - settings.SAR.db_min)
        sar = 255 * (sar - settings.SAR.db_min) / a

        # return sar as image
        return sar.astype(np.uint8)

    def save_configurations(self, msf):
        # get path by modifying path of msf
        path = str(msf.path_configuration).replace('msf', 'sar')

        # configurations are the same as that of the msf, only filenames are
        # different
        conf = msf.configurations
        for idx in range(len(conf)):
            conf[idx]['filename'] = \
                conf[idx]['filename'].replace('msf', 'sar')

        # save config
        with open(path, 'w') as file:
            json.dump(self.msf.configurations, file)

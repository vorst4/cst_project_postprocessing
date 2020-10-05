from __future__ import annotations
import json
from pathlib import Path

import cv2
import numpy as np

import settings
from util.complex_field_per_antenna import REAL, IMAG, ComplexFieldPerAntenna


class MeanSquareField:
    """
    This class is iterable, which iter iteration it generates a new Mean
    Squared electric Field (msf) image from the Complex electric Field of
    each Antenna (CFA) with random phases and amplitudes.

    The phase of the first antenna is set to 0 degrees. The phases and
    amplitudes of the other antennas are chosen  at random within the range
    as defined in settings.MSF.

    The msf image is scaled by 'settings.MSF.scalar'

    This object will stop iterating after 'settings.MSF.n' samples are
    generated.
    """

    def __init__(self, path_project: Path, cfa_obj: ComplexFieldPerAntenna):
        self.cfa_obj = cfa_obj
        self.folder = path_project.joinpath('msf')
        self.path_configuration = self.folder.joinpath('configuration.json')
        self.configurations = []

        # pre-allocate space
        self.cfa = np.zeros(cfa_obj.cfa.shape)
        self.msf = np.zeros((cfa_obj.np, 1))

        # define attributes
        self.cos_phase = None
        self.sin_phase = None
        self.phases = None
        self.amplitudes = None
        self.n_phaseshifts = None
        self.filename = None
        self.idx = None

    def generate_msf(self, idx: int) -> MeanSquareField:
        # generate random phases, note that phase of first antenna is 0
        self.phases = np.random.uniform(
            low=settings.MSF.phase_limit[0],
            high=settings.MSF.phase_limit[1],
            size=self.cfa_obj.na
        )
        self.phases[0] = 0.

        # generate random amplitudes
        self.amplitudes = np.random.uniform(
            low=settings.MSF.amplitude_limit[0],
            high=settings.MSF.amplitude_limit[1],
            size=self.cfa_obj.na
        )

        # apply phase shifts to cfa
        self._shift_cfa()

        # apply scaling to cfa (amplitudes)
        self._scale_cfa()

        # calculate msf
        self._mean_square()

        # set idx & filename
        self.idx = idx
        self.filename = str(self.folder.joinpath('msf_%04i.png' % idx))

        # add msf to generated_msf list of dict
        self.configurations.append({
            'filename': self.filename,
            'phases': list(self.phases),
            'amplitudes': list(self.amplitudes)
        })

        # return msf as image
        return self

    def save_map(self) -> None:
        """
        saves a single generated msf map
        """
        # create msf folder if it doesn't exist yet
        if not self.folder.exists():
            self.folder.mkdir()

        # write image to msf folder
        cv2.imwrite(self.filename, self.to_img())

    def save_configurations(self):
        """"
        Saves the configurations (filename, phases & amplitudes) of each msf
        map that was generated since the creation of this object
        """
        with open(self.path_configuration, 'w') as file:
            json.dump(self.configurations, file)

    def to_img(self) -> np.ndarray:
        img_shape = (settings.Img.width, settings.Img.height)
        img_scaled = 255 * self.msf.reshape(img_shape) * settings.MSF.scalar
        return img_scaled.astype(np.uint8)

    def _shift_cfa(self) -> None:
        # todo: find a different solution to slicing, since that will return
        #  a copy of the ndarray (i think), this  increases computation time

        # cfa : ndarray, shape [n_points, n_antenna, (x,y,z), (real,imag) ]

        # reshape cos_phase and sin_phase such that numpy knows which
        # dimension must be multiplied element-wise
        cos_phase = np.cos(self.phases).reshape(1, -1, 1)
        sin_phase = np.sin(self.phases).reshape(1, -1, 1)

        # real and imag part of cfa
        cfa_real = self.cfa_obj.cfa[:, :, :, REAL]
        cfa_imag = self.cfa_obj.cfa[:, :, :, IMAG]

        # shift cfa
        self.cfa[:, :, :, REAL] = cfa_real * cos_phase - cfa_imag * sin_phase
        self.cfa[:, :, :, IMAG] = cfa_imag * cos_phase + cfa_real * sin_phase

    def _scale_cfa(self) -> None:
        self.cfa *= self.amplitudes.reshape(1, -1, 1, 1)

    def _mean_square(self) -> None:
        self.msf = 0.5 * np.sum(np.sum(self.cfa, axis=1) ** 2, axis=(1, 2))

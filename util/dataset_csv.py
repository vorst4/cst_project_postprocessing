from zipfile import ZipFile
import numpy as np
from .complex_field_per_antenna import ComplexFieldPerAntenna
from .mean_squared_field import MeanSquareField
from .drawing_interchange_format import DrawingInterchangeFormat


class DatasetCSV:

    def __init__(self):
        self.are_headers_defined: bool = False
        self._csv: str = ''
        self.n_antennas: int = 0

    def generate_headers(self, n_antennas: int) -> None:
        self.n_antennas: int = n_antennas
        self._csv = 'idx;' \
                    'input_permittivity;' \
                    'input_conductivity;' \
                    'input_density;'
        for idx_antenna in range(n_antennas):
            self._csv += 'input_phase_%02i;' % idx_antenna
            self._csv += 'input_amplitude_%02i;' % idx_antenna
        self._csv += 'output_img\n'
        self.are_headers_defined = True

    def append(self,
               msf: MeanSquareField,
               dxf: DrawingInterchangeFormat) -> None:
        # index
        self._csv += '%07i;' % msf.idx

        # add paths to permittivity, conductivity & density maps
        for _, filename in dxf.filenames.items():
            self._csv += filename + ';'

        # add phase & amplitude of each antenna
        for idx in range(self.n_antennas):
            # add normalized phase
            self._csv += '%.16f;' % (msf.phases[idx] / (2 * np.pi))
            # add amplitude (which is already normalized)
            self._csv += '%.16f;' % msf.amplitudes[idx]

        # add path to output msf
        self._csv += msf.filename + '\n'

    def save(self, zipfile: ZipFile) -> None:
        zipfile.writestr('dataset.csv', self._csv)

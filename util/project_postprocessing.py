import json
from pathlib import Path
from typing import List

import numpy as np

import settings as settings
from .complex_field_per_antenna import ComplexFieldPerAntenna
from .drawing_interchange_format import DrawingInterchangeFormat
from .mean_squared_field import MeanSquareField
from .print import Print
from .specific_absorption_rate import SpecificAbsorptionRate


def postprocess_project(print_: Print.log, path_project: Path) -> None:
    """
    Converts the data generated in CST to 2D maps
    """
    # return if results don't exist
    if not path_project.joinpath('e-field 11.csv').exists():
        print_('\t...no simulation results present')
        return

    # load materials
    with open(path_project.joinpath('materials.json'), 'r') as file:
        materials = json.load(file)

    # load dxf object of the project, which is used to create the maps
    dxf = DrawingInterchangeFormat(path_project, materials)

    # create cfa object
    cfa = ComplexFieldPerAntenna(path_project)

    # generate and save model/permittivity/conductivity/density map
    dxf.save(cfa.mm_per_px)

    # create msf object from cfa
    msf = MeanSquareField(path_project, cfa, print_)

    # create sar object
    sar = SpecificAbsorptionRate(print_)

    # iteratively generate a msf map with random phases/amplitudes and save it
    pct = 0
    pct_step = 10
    print_('\tgenerating MSF maps (%i)' % settings.MSF.n)
    for idx in range(settings.MSF.n):
        # log
        if idx / settings.MSF.n > 0.01 * pct:
            print_('\t\t%i%%' % pct)
            pct += pct_step
        # generate msf and save it
        msf.generate_msf(idx).save_map()
        sar.generate_sar(msf, dxf.map_den, dxf.map_con).save_map()

    # log
    print_('\t\t100%')
    print_('\tMSF range = [%f, %f]' % (msf.min, msf.max))
    print_('\tSAR range = [%f, %f]' % (sar.min, sar.max))

    # save msf configuration (filenames, phases & amplitudes)
    print_('\tsaving msf/sar configurations')
    msf.save_configurations()
    sar.save_configurations(msf)


def get_project_paths(job_id: int, n_jobs: int) -> List[Path]:
    # obtain all the projects folders
    paths_all_projects = np.array(list(
        Path(settings.Paths.root).glob('project*')
    ))

    # determine the projects that the current job should process
    ids_all = np.arange(len(paths_all_projects))
    ids = ids_all[(ids_all % n_jobs) == job_id]
    paths_projects = paths_all_projects[ids]

    return sorted(list(paths_projects))

import json
import os
from pathlib import Path
from typing import List

import numpy as np


# define constants
class Constants:
    step_max = 15
    step_min = 10
    is_running_on_desktop = os.name == 'nt'  # nt: Windows , posix: Linux
    path_scripttemplate = Path().cwd().joinpath('data/script_template.bas')
    path_macrotemplate = Path().cwd().joinpath('data/macro_template.mcs')
    path_macrocontent = Path().cwd().joinpath('data/macro_content.bas')
    macro_name = 'macro_prep_simulation'
    if is_running_on_desktop:
        path_cst = 'C:/Program Files (x86)/CST Studio Suite 2020/' \
                   'CST DESIGN ENVIRONMENT.exe'
        path_projects = 'C:/Users/Dennis/Documents/generated_projects'
    else:
        path_cst = '/cm/shared/apps/cst/CST_STUDIO_SUITE_2020' \
                   '/cst_design_environment'
        path_projects = '/home/tue/s111167/generated_projects'


def main():
    # array containing path to each project
    paths_projects = get_subdirs(Constants.path_projects)

    # loop through each project
    for path_project in paths_projects:
        print('fixing %s ...' % Path(path_project).stem)
        is_fix_needed = fix_json(path_project)
        if is_fix_needed:
            fix_macro(path_project)
        print('\t...Done')


def fix_json(path_project: str):
    """
    Read 'materials.json' from <path_project>, swap <density> and
    <conductivity> and write the changes back to 'materials.json'. Returns
    False if materials.json was already fixed
    """
    print('\tjson...')
    json_path = join_path(path_project, 'materials.json')

    # read materials, which should be a list of dictionaries
    with open(json_path, 'r') as file:
        materials: List[dict] = json.load(file)

    # return if the conductivity and density are already swapped
    #   NOTE: currently highest conductivity = 1.01
    #                   lowest density = 916, except air which is 0
    for material in materials:
        if material['density'] > 2:
            print('\t\t...project was already fixed')
            return False

    # swap conductivity and density
    for material in materials:
        material['conductivity'], material['density'] = \
            material['density'], material['conductivity']

    # write back the changes
    with open(json_path, 'w') as file:
        json.dump(materials, file)

    print('\t\t...Done')
    return True


def fix_macro(path_project):
    print('\tfixing macro...')
    path_macro = join_path(path_project, 'project/Model/3D/macro.mcs')

    # read macro
    with open(path_macro, 'r') as file:
        macro: str = file.read()

    # swap densities and conductivities
    macro = macro.replace('densities = ', '__temp__')
    macro = macro.replace('conductivities = ', 'densities = ')
    macro = macro.replace('__temp__', 'conductivities = ')

    # write macro back to file
    with open(path_macro, 'w') as file:
        file.write(macro)
    print('\t\t...done')


def join_path(*pieces: str):
    path = Path(pieces[0])
    for piece in pieces[1:]:
        path = path.joinpath(piece)
    return str(path)


def get_subdirs(root_dir: str) -> np.ndarray:
    subdirs = list(Path(root_dir).glob('*/'))
    return np.array(sorted([str(subdir) for subdir in subdirs]))


if __name__ == '__main__':
    main()

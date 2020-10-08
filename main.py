import argparse
from pathlib import Path
from util.project_postprocessing import get_project_paths, postprocess_project
from util.print import Print
from time import time
import settings

# on the server, the job_id, n_jobs & partition id is passed as an argument
if settings.is_running_on_desktop:
    job_id = 0
    n_jobs = 1
    partition_id = 0
else:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job_id", help="id number of the job", type=int)
    parser.add_argument("--n_jobs", help="number of jobs", type=int)
    parser.add_argument("--partition_id", help="server partition id", type=int)
    job_id = parser.parse_args().job_id
    n_jobs = parser.parse_args().n_jobs
    partition_id = parser.parse_args().partition_id

# get project paths which current job should process
paths_project = get_project_paths(job_id, n_jobs)
n_projects = len(paths_project)

# post-process each project path
for idx, path_project in enumerate(paths_project):

    # start timer
    timer = time()

    # create print object which logs the print messages to a log.txt file
    path_log = str(Path(path_project).joinpath('log_postprocessing.txt'))
    print_ = Print(path_log, job_id, n_jobs, partition_id).log

    # log
    print_('PROCESSING PROJECT (%i/%i) %s...' %
           (idx + 1, n_projects, path_project))

    # post-process project
    if settings.is_running_on_desktop:
        postprocess_project(print_, path_project)
    else:
        try:
            postprocess_project(print_, path_project)
        except Exception as e:
            raise type(e)(str(e) + '\nOccurs in file %s' % path_project)

    # log
    print_('...FINISHED IN %.2f MINUTES' % ((time() - timer)/60))

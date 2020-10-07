#!/usr/bin/bash

source /home/tue/s111167/python-env/postprocess-env/bin/activate
python main.py --partition_id $partition_id \
               --n_jobs $n_jobs \
               --job_id $job_id

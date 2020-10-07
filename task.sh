#!/usr/bin/bash

module load anaconda
source activate '/home/tue/s111167/.conda/envs/postprocess-env'
python main.py --partition_id $partition_id \
               --n_jobs $n_jobs \
               --job_id $job_id

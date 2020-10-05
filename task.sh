#!/usr/bin/bash

module load anaconda
source activate '/home/tue/s111167/.conda/envs/conda-env'
python main.py --partition_id $partition_id
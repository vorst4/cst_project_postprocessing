#!/usr/bin/bash

sbatch  --job-name=CST_project_generator_$job_id \
        --nodes=1 \
        --ntasks=1 \
        --cpus-per-task=4 \
        --time=2-00:00:00 \
        --partition=tue.default.q \
        --output=output/t$job_id \
        --error=output/e$job_id \
        --mail-user=d.m.n.v.d.vorst@student.tue.nl \
        --mail-type=ALL \
        task.sh
#!/usr/bin/bash

# verify that argument (partition id) is passed
if [ -z "$1" ]
then
  echo "ERROR: partition id needs to be passed as an argument"
  exit 1
fi

# verify that only 1 argument is passed
if [ $# -gt 2 ]
then
  echo "ERROR: $# arguments are given, only 1 is required"
  exit 1
fi

# verify that number of partitions is not > 3
if [ $2 -gt 3 ]
then
  echo "ERROR: partition id is > 3"
  exit 1
fi

# verify that number of partitions is >= 0
if [ $2 -lt 0 ]
then
  echo "ERROR: partition id is < 0"
  exit 1
fi

declare -a partitions=("tue.default.q"
                       "elec.default.q"
                       "elec.gpu.q"
                       "elec-em.gpu.q")

# execute jobs
for (( job_id=0; job_id<$1; job_id++ ))
do
  export job_id=$job_id
  export n_jobs=$1
  export partition_id=$2
  sbatch  --job-name=CST_project_generator_$job_id_$2 \
          --nodes=1 \
          --ntasks=1 \
          --cpus-per-task=1 \
          --time=10-00:00:00 \
          --partition=${partitions[$2]} \
          --output=output \
          --error=error \
          --mail-user=d.m.n.v.d.vorst@student.tue.nl \
          --mail-type=ALL \
          task.sh
done
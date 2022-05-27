#!/bin/bash
INTERP=python
EXEC=q_learning.py
DIR=test_worlds
SHIELD_THRESHOLD=0.9
NUM_RUNS=25

for world in $DIR/*.world; do
#for world in $DIR/*.world; do
  output=${world}_output
  mkdir -p $output
  #for setting in no_penalty penalty shielded; do
  for setting in penalty; do
    #for threshold in 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 0.95;
    for threshold in 0.95; do
      for ((i=1; i<=NUM_RUNS; i++)); do
        UNIX_EPOCH="$(date +%s)"
        UNIX_EPOCH="${UNIX_EPOCH}_$i"
        set -x
        $INTERP $EXEC $world $setting $threshold 2>&1 | tee $output/${UNIX_EPOCH}_${setting}_${threshold}.log
        set +x
      done
    done
  done
done

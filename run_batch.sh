#!/bin/bash

# type bash run_bash.sh in shell # max gamma tested was 0.036 before infeasbile showing at 0.04
GAMMAS=(0.0 0.004 0.008 0.012 0.016 0.02 0.024 0.028 0.032 0.036)

for GAMMA in "${GAMMAS[@]}"; do
    echo "running model_1.py for $GAMMA ==========================================================="
    python -u model_1.py --g $GAMMA

    echo "running model_2.py for $GAMMA ==========================================================="
    python -u model_2.py --g $GAMMA

    echo "running model_3.py for $GAMMA ==========================================================="
    python -u model_3.py --g $GAMMA

    sleep 1
done
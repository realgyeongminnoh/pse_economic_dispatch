#!/bin/bash

GAMMAS=(0.0 0.01 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1 0.11 0.12 0.13 0.14 0.15)

for GAMMA in "${GAMMAS[@]}"; do
    echo "running model_1.py for $GAMMA =========================================================="
    python -u model_1.py --g $GAMMA

    echo "running model_2.py for $GAMMA =========================================================="
    python -u model_2.py --g $GAMMA

    echo "running model_3.py for $GAMMA =========================================================="
    python -u model_3.py --g $GAMMA

    sleep 1
done
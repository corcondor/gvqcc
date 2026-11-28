#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# The three pinned DQI KMBs, four ZIP manifests and source/API dependencies
# are as described in README. No fixture data is shared in this directory.
g++ -march=native -O3 -std=c++17 other/src/replay512_noraw.cpp -o replay512
OPENBLAS_NUM_THREADS=1 python3.12 other/src/make512.py d294.kmb 102400 paired-complete-review-v1 panel
for a in 294 299 8; do
    ids=()
    for j in 0 1 2 3; do
        ./replay512 "d$a.kmb" "panel$j.bin" "r${a}_$j.csv" 2>"r${a}_$j.log" &
        ids+=("$!")
    done
    python3.12 archive.py "d$a.kmb" joint_work/audit/saved.bin > "a$a.log"
    for id in "${ids[@]}"; do wait "$id"; done
done
python3.12 aggregate.py 294 299 8

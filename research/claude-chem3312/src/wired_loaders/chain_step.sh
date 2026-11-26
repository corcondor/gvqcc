#!/bin/bash
# usage: chain_step.sh BANK TAG BLOCK1 BATCHES SEED WORDS_NPY BASE_FAMILY OUTNAME
set -e
cd <ROOT>/w_push14/planner
if [ -n "$6" ]; then W="$6"; else W=""; fi
timeout 1500 python -X utf8 design.py $1 $2 $3 $4 $5 $W 2>&1 | grep -v inconsistent | grep -E "block|saved|Error|error|try" | tail -8
timeout 600 python -X utf8 special.py $2 4 1 2>&1 | grep -E "luck|ordinary|Error"
for r in 7 14; do FLOOR=268 timeout 900 python -X utf8 tmp/part_driver.py designs/$2/cs_$2_s4g1_row$r.txt 265 276,275,274,272 300 $5 2 designs/$2/part_row$r.json <ROOT>/w_push14/planner/tmp/cs2.exe 2>&1 | tail -1; done
timeout 900 python -X utf8 build_final.py $2 designs/$2/part_row7.json designs/$2/part_row14.json $8 $7 2>&1 | grep -E "evaluate|verify_one|table:|closers|Error" | cut -c1-220

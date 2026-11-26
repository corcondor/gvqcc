#!/bin/bash
# usage: partition.sh TAG ROW  -> designs/TAG/part_rowR.json ; retries seeds/targets until all 5 classes consistent
cd <ROOT>/w_push14/planner
tag=$1; r=$2
CS=<ROOT>/w_push14/planner/tmp/cs2.exe
for seed in 11 22 33 44 55 66; do
  for targets in 282,280,278,276 284,282,278,274 280,278,278,278; do
    res=$(FLOOR=268 timeout 400 python -X utf8 tmp/part_driver.py designs/$tag/cs_${tag}_s4g1_row$r.txt 265 $targets 60 $seed 2 designs/$tag/part_row$r.json $CS 2>&1 | tail -1)
    if python -c "import json,sys; d=json.load(open('designs/$tag/part_row$r.json')); sys.exit(0 if d.get('ok') else 1)" 2>/dev/null; then
      echo "row $r seed $seed targets $targets: $res"; exit 0; fi
    echo "row $r seed $seed targets $targets failed" >&2
  done
done
exit 1

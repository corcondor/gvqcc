#!/bin/bash
# usage: chain2.sh BANK TAG BLOCK1 BATCHES SEED WORDS_NPY BASE_FAMILY OUTNAME S
set -e
cd <ROOT>/w_push14/planner
timeout 1800 python -X utf8 design.py $1 $2 $3 $4 $5 $6 > logs/$2_design.log 2>&1
grep -E "^block|saved" logs/$2_design.log
test -f designs/$2/design.json
python -c "import json,sys; d=json.load(open('designs/$2/design.json')); sys.exit(0 if len(d['blocks_outputs'])==3 else 1)" || { echo "design incomplete"; exit 1; }
timeout 600 python -X utf8 specgen.py export $2 --s $9 --name sg$2 | grep -E "luck|bank"
timeout 900 python -X utf8 partition_g.py $2 sg$2 2 60 | tail -2
timeout 900 python -X utf8 specgen.py build $2 $8 --name sg$2 --base $7 | grep -E "evaluate|verify|table|written|Error"

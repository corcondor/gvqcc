#!/bin/sh
# usage: run234.sh NREL E LIMIT k [k ...]   (95-chip covers; a new seed, i.e. a new search instance, per attempt)
# Create the file STOP234 to stop after the current attempt.
cd "$(dirname "$0")"
NREL=$1; E=$2; LIMIT=$3; shift 3
for k in "$@"; do
  for seed in $(seq 2 60); do
    [ -f STOP234 ] && break
    log="make2_k${k}_n95_r${NREL}_s${seed}.log"
    python -X utf8 -u make2.py "$k" "cover95_k${k}_s1.pkl" "$NREL" "$E" "$seed" "$LIMIT" > "$log" 2>&1
    if grep -q "'status': 'PASS" "$log" && ! grep -q Traceback "$log"; then
      cp "angle_k_${k}_n95_f${NREL}_s${seed}.kmb" "best_angle_k_${k}.kmb"
      echo "$(date +%T) loader $k PASS nrel $NREL seed $seed"
      break
    fi
    echo "$(date +%T) loader $k nrel $NREL seed $seed failed: $(grep -E 'Error|error' "$log" | tail -n 1 | cut -c1-200)"
  done
  [ -f STOP234 ] && break
done
echo ALL DONE

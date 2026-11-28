#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$ROOT/.." && pwd)"
PY=${PYTHON:-python3}
export PYTHONPATH="$ROOT:$BASE/gvqcc_multiform:$BASE/gvqcc_multiform_v3:${PYTHONPATH:-}"
export OPENBLAS_NUM_THREADS=1
"$PY" -m unittest -v \
 "$ROOT/test_global_cofactor.py" "$ROOT/test_high_pair.py" \
 "$ROOT/test_high_pair_general.py" "$ROOT/test_independent_verifier.py"
OUT="$ROOT/replayed_$(date +%Y%m%d%H%M%S)"
mkdir -p "$OUT"
for seed in "$BASE"/gvqcc_multiform/seeds/*.npz; do
 stem=$(basename "$seed" .npz)
 "$PY" "$ROOT/global_cofactor.py" --seed "$seed" --out "$OUT/global_${stem}" --emit > "$OUT/global_${stem}.log"
 "$PY" "$ROOT/high_pair.py" --seed "$seed" --global-offset canonical --modes greedy-paid exact-paid exact --out "$OUT/pair_${stem}" --emit > "$OUT/pair_${stem}.log"
 "$PY" "$ROOT/high_pair_general.py" --seed "$seed" --global-offset canonical --modes greedy exact --out "$OUT/general_${stem}" --emit > "$OUT/general_${stem}.log"
done
"$PY" "$ROOT/audit_all_kmx.py" --data-root "$OUT" --seed-root "$BASE/gvqcc_multiform/seeds" --out "$OUT/audit" --workers 4
"$PY" "$ROOT/certify_matching.py" --data-root "$OUT" --seeds "$BASE"/gvqcc_multiform/seeds/*.npz --out "$OUT/matching_dp.json"
echo "REPRODUCE_COMPLETE $OUT"

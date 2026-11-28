#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="${1:-/tmp/seam/results}"
NAME="${2:-parent266}"
D="$DIR/$NAME"
V=/tmp/public266/google-verifiable-quantum-circuit-compilation/verifiers/dqi
export PYTHONPATH="/tmp/seam:$V" OPENBLAS_NUM_THREADS=1
C="$D.kmb"
# Preserve every result even if a prior stage finds an error.
set +e
python /tmp/seam/verify_raw.py "$C" "$D.raw.json" > "$D.raw.log" 2>&1
python /tmp/seam/verify_distribution.py "$C" "$D.distribution.json" > "$D.distribution.log" 2>&1
python /tmp/seam/verify_structured.py "$C" "$D.structured.json" > "$D.structured.log" 2>&1
python "$HERE/verify_captured.py" "$C" "$D.captured.json" "$HERE/captured_input.json" > "$D.captured.log" 2>&1
python "$V/verify_submission_dqi.py" "$C" --num-shots 102400 --batch-size 256 --max-workers 2 > "$D.official.json" 2>"$D.official.log"
python "$V/verify_submission_dqi.py" "$C" --num-shots 102400 --batch-size 256 --max-workers 2 --salt independent-266-regression > "$D.salt.json" 2>"$D.salt.log"
set -e
# Never accept a reduced panel or the verifier's nonzero error tolerance.
python "$HERE/strict_gate.py" "$D"

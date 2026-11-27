#!/usr/bin/env bash
set -euo pipefail
export OPENBLAS_NUM_THREADS=1
ROOT=/tmp/fusion
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/patch"
cd "$ROOT"
curl -fsSL https://codeload.github.com/maxoubvd/google-quantum-ai/tar.gz/a9effc375527bf0b6962c178530d353eb70a3fcb | tar -xz --strip-components=1
python3 -m venv venv
venv/bin/pip install kickmix==1.0.0 numpy scipy
cp "$HERE/"*.py "$ROOT/patch/"
cd "$ROOT/patch"
BASE=https://raw.githubusercontent.com/corcondor/gvqcc
curl -fsSL "$BASE/46a3b978c61771e65996b7a61fb8fb9b63874252/research/dqi_cf_fusion_20261127/apply_coefficient_fusion.py" -o apply_coefficient_fusion.py
curl -fsSL "$BASE/46a3b978c61771e65996b7a61fb8fb9b63874252/research/dqi_cf_fusion_20261127/transport42_lean.py" -o transport42_lean.py
curl -fsSL "$BASE/df7fcff10506f68f28355c073bd546ce198abd5f/research/dqi_cf_native_proof/cf_route.py" -o cf_route.py
curl -fsSL "$BASE/d442f72507472f5d4e1bce77a07f08ab1da2b16f/research/v81/field_scan.py" -o field_scan.py
curl -fsSL "$BASE/a52fe81aa92f19b907e3c85813e49998523e1eae/research/dqi316k_joint_crt/crt882.py" -o crt882.py
"$ROOT/venv/bin/python" field_scan.py > fftplan.log
"$ROOT/venv/bin/python" -u build_fusion.py | tee build_fusion.log
"$ROOT/venv/bin/python" -u verify_fusion.py full_fft.kmb | tee verify_fusion.log

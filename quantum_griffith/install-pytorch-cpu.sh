#!/usr/bin/env bash
# CPU-only PyTorch development/test environment for Quantum Griffith.
set -euo pipefail
python -m pip install --disable-pip-version-check --quiet "numpy==1.26.4"
python -m pip install --disable-pip-version-check --quiet "torch==2.5.1" --index-url https://download.pytorch.org/whl/cpu
python - <<'PY'
import numpy, torch
print("numpy:", numpy.__version__)
print("torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
# Fail if torch is missing or if this is not a tensor runtime.
assert float((torch.ones(2) @ torch.ones(2)).item()) == 2.0
PY

#!/bin/bash
set -euo pipefail
# Execute from extracted bundle root; example uses original tree structure.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python src/verify_affine_zero_t.py --source candidates/I_affine_3357/submission.npz --circuit_dir candidates/I_affine_3357/circuits --out /tmp/gvqcc_I_clean.json --seeds -1
python src/verify_affine_zero_t.py --source candidates/J_C45_joint/submission.npz --circuit_dir candidates/J_C45_joint/circuits --out /tmp/gvqcc_J_clean.json --seeds -1
# Model-only FeMoCo evaluation; not native KickMix:
python src/longtrain/physical_verify.py --npz candidates/I_affine_3357/submission.npz
python src/longtrain/physical_verify.py --npz candidates/J_C45_joint/submission.npz
# For exact G-series loader verification source tree must retain axis_old/src:
python src/verify_exact_ir.py --source candidates/G_global_fold/fold_value.npz --circuits candidates/G_global_fold/circuits --J 5 --banks 15 --out /tmp/gvqcc_G_exact.json
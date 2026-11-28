#!/usr/bin/env bash
# Rebuild exact #266, then transfer the public-mask gauge from #267.
# Run on an isolated Linux x86_64 runner with CPython 3.13 and C++17.
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-/tmp/seam/results}"
mkdir -p /tmp/source /tmp/seam /tmp/public266 "$OUT"
OUT="$(realpath "$OUT")"
BASE=https://raw.githubusercontent.com/corcondor/gvqcc
PUB=a9effc375527bf0b6962c178530d353eb70a3fcb
P261=bf87158c58b5f183f08798d6d449e42c10177019
P266=8e6cc269aab60ae533b9a0d62347494387e4197a
P267=b224d1979a55502988c0b0520de252863c7353f3
P264=2916deced346bb4b672ed8fe98d19d0081e6b605
P247=945c1a3ea8f34d0fb007dce04833a5a296842590
P243=310c4bb8da25a3fce0ab609dc609ad1b753bdfe2
P244=756605477e736183a041d43e91a3606c2ea2c854
get() { curl -fLsS --retry 2 "$BASE/$1/$2" -o "$3"; }
curl -fLsS --retry 2 'https://www.kaggle.com/api/v1/datasets/download/tonylica/quantum-ai-32-85306-task-generators?datasetVersionNumber=2' -o /tmp/source.zip
echo '2715ee84ce70d59c2e799ee397e11b253e9822e54fbe76fda51a8f274e555496  /tmp/source.zip' | sha256sum -c
unzip -q /tmp/source.zip -d /tmp/source
curl -fLsS --retry 2 "https://codeload.github.com/maxoubvd/google-quantum-ai/tar.gz/$PUB" | tar -xz --strip-components=1 -C /tmp/public266
TEAM=/tmp/public266/generators/dqi/src/team
ROOT=/tmp/public266/generators/dqi/src
V=/tmp/public266/google-verifiable-quantum-circuit-compilation/verifiers/dqi
# Preserve the official runtime/validator pins used by the generator.
ENGINE="$(find /tmp/source/runtime -name kickmix.so -print -quit)"
test -n "$ENGINE"
echo "c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e  $ENGINE" | sha256sum -c
echo "f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65  $V/verify_submission_dqi.py" | sha256sum -c
mkdir -p "$ROOT/pro1_controller_bundle/1_task/official" "$ROOT/pro1_controller_bundle/1_task/verifiers/dqi"
cp "$ENGINE" "$ROOT/pro1_controller_bundle/1_task/official/"
cp "$V/verify_submission_dqi.py" "$ROOT/pro1_controller_bundle/1_task/verifiers/dqi/"
# Original donor (not the modified shared-frame donor).
cd /tmp/source/dqi
PYTHONPATH="/tmp/source/runtime/kickmix:/tmp/source/dqi" python - <<'PY'
from pathlib import Path
import build,kickmix as km
with open('/tmp/seam/donor.kmx','wb') as f:build.write_assembly(f,False)
c=km.Circuit.from_file('/tmp/seam/donor.kmx',format='kmx')
c.to_file('/tmp/seam/donor.kmb',format='kmb')
PY
echo '4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52  /tmp/seam/donor.kmb' | sha256sum -c
rm /tmp/seam/donor.kmx
cd /tmp/seam
for f in crt882.py joint_crt.py narrow_crt.py g_guarded.py joint_phase.py native.hpp; do
  get "$P261" "research/dqi316k_joint_crt/$f" "$f"
done
get "$P244" research/dqi316k_joint_crt/general_scan.py general_scan.py
get "$P266" research/dqi263_rebase_hmr/core_direct_unit.py "$TEAM/core_direct_unit.py"
get "$P266" research/dqi263_rebase_hmr/core_rebase_hmr.py "$TEAM/core_rebase_hmr.py"
get "$P266" research/dqi263_rebase_hmr/splice_skip.cpp splice_skip.cpp
get "$P267" research/dqi316k_central_lambda/splice_gauge.cpp splice_gauge.cpp
get "$P247" research/dqi316k_joint_crt/direct_general.cpp direct_general.cpp
get "$P243" research/dqi316k_joint_crt/scope_keep_reset.cpp scope_keep_reset.cpp
get "$P261" research/dqi316k_direct_hermite/verify_raw.py verify_raw.py
get "$P264" research/dqi261_conditional_phase/verify_distribution.py verify_distribution.py
get "$P267" research/dqi316k_central_lambda/verify_structured.py verify_structured.py
export PYTHONPATH="/tmp/seam:$V"
python -c 'import kickmix; print(kickmix.__file__)'
cd "$ROOT"
python "$TEAM/core_rebase_hmr.py" /tmp/seam/core_rebase_hmr.kmb | tee "$OUT/core.log"
cd /tmp/seam
for f in splice_skip splice_gauge scope_keep_reset direct_general; do
  c++ -O3 -UNDEBUG -std=c++17 "$f.cpp" -o "$f"
done
./splice_skip donor.kmb core_rebase_hmr.kmb donor_rebase_hmr.kmb
sha256sum donor_rebase_hmr.kmb
./scope_keep_reset donor_rebase_hmr.kmb donor_hmr_scope.kmb
./direct_general donor_hmr_scope.kmb "$OUT/parent266.kmb"
echo '071453f46be0f6108a09edd5b7b1e34595d86ddfe49ed0c80f369f0a35f7a349  '"$OUT/parent266.kmb" | sha256sum -c
# New candidate: exact classical trace-dual gauge, same native core.
# No alteration to the verification masks or official verifier.
./splice_gauge donor.kmb core_rebase_hmr.kmb gauge_raw.kmb
./scope_keep_reset gauge_raw.kmb gauge_scope.kmb
./direct_general gauge_scope.kmb "$OUT/gauge266.kmb"
sha256sum "$OUT/"*.kmb | tee "$OUT/hashes.txt"

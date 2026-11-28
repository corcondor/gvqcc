#!/usr/bin/env bash
# Run after reconstructing the exact #259 joint_alias.kmb in /tmp/fusion/patch.
set -euo pipefail
cd /tmp/fusion/patch
PY=/tmp/fusion/venv/bin/python
echo '7c592390e55b713b190e73ebb18f5f0d04fb230089dc29de940460683bb4695c  joint_alias.kmb' | sha256sum -c
BASE=https://raw.githubusercontent.com/corcondor/gvqcc
curl -fsSL "$BASE/945c1a3ea8f34d0fb007dce04833a5a296842590/research/dqi316k_joint_crt/direct_general.cpp" -o direct_general.cpp
curl -fsSL "$BASE/310c4bb8da25a3fce0ab609dc609ad1b753bdfe2/research/dqi316k_joint_crt/scope_keep_reset.cpp" -o scope_keep_reset.cpp
sed -i 's/assert(r.Q==900)/assert(r.Q<=900)/g' direct_general.cpp scope_keep_reset.cpp
if command -v g++ >/dev/null; then CXX=(g++); else CXX=("$PY" -m ziglang c++); fi
"${CXX[@]}" -O3 -UNDEBUG -std=c++17 direct_general.cpp -o direct259
"${CXX[@]}" -O3 -UNDEBUG -std=c++17 scope_keep_reset.cpp -o scope259
./direct259 joint_alias.kmb alias_direct.kmb
./scope259 alias_direct.kmb alias_scope.kmb
p=alias_scope.kmb
for i in 1 2 3 4 5; do
  ./direct259 "$p" "round${i}_direct.kmb"
  ./scope259 "round${i}_direct.kmb" "round${i}_scope.kmb"
  rm "round${i}_direct.kmb"
  if cmp -s "$p" "round${i}_scope.kmb"; then rm "round${i}_scope.kmb"; break; fi
  if [[ "$p" != alias_scope.kmb ]]; then rm "$p"; fi
  p="round${i}_scope.kmb"
done
cp "$p" joint_monotone.kmb
echo '8db1fd9d2b03979e355659e8cf2df421c3938e44133a5b760c9e7242d5afe9b9  joint_monotone.kmb' | sha256sum -c
"$PY" verify_fusion.py joint_monotone.kmb
"$PY" verify_double_node259.py joint_monotone.kmb
"$PY" quotient_chart259.py

# Cutoff-zero native reconstruction (research; not a submission)

Independent Vercel experiment on public post-v3 v7 DQI generator at maxoubvd/google-quantum-ai commit a9effc375527bf0b6962c178530d353eb70a3fcb. This is NOT the frozen 316k donor from #247. The purpose is to isolate missing zero guards in a reproducible source-level decoder and use the results for the low-cost lineage. No substitution of submission binaries.

## Reproduction
Use CPython 3.13, NumPy 2.2.6, SciPy, KickMix 1.0.0 and the public source's bundled official engine and verifier. In a scratch clone of the pinned revision, with REPO the absolute source root:
```sh
cd "$REPO/generators/dqi"
bash team_build.sh 3 "$REPO/google-verifiable-quantum-circuit-compilation/kickmix" "$REPO/google-verifiable-quantum-circuit-compilation/verifiers" /tmp/j3-out
cd src
mkdir -p pro1_controller_bundle/1_task/official pro1_controller_bundle/1_task/verifiers/dqi
cp "$REPO/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so" pro1_controller_bundle/1_task/official/
cp "$REPO/google-verifiable-quantum-circuit-compilation/verifiers/dqi/verify_submission_dqi.py" pro1_controller_bundle/1_task/verifiers/dqi/
# copy the two root_zero*.py files in this directory to src/team/
python3 team/root_zero.py /tmp/root-zero.kmb
python3 team/root_zero_guarded.py /tmp/root-guarded.kmb
```
The first-three chart is incompatible with j_min=0. Replace its prefix and closing by the underlying generic Direct extractor, then replace only the specialized first-three record assertions with the original paired key interface. The second script additionally uses guarded=True for each CRT synthesis stage. Keep full source and native validator checks. The old specialized per-stage receipts are NOT applicable to the new tape.

Use verify_raw.py against each full KMB, without any host-selected chart or input remapping. It generates 332 independent legal supports with 3 mask cases each, checks raw S restoration, phase, ancilla and mask restoration; optional quick mode is 108 executions. The tests use the official field tables and ABI validator, not the official full scoring run. Stress-panel mean paid is not a leaderboard score.

The separate public kv_unfused5 baseline is generated with its kit/kv_unfused5/build.py. It is not a 316k replacement. Keep original donor and its certificates intact.

Vercel session sbx_0hXxFBGiXxlH0xH8ifMruaDvpmtp. Receipts recorded separately. No official score or universal correctness proof. Do not merge into main or submit.

# P0: install the native KickMix environment first

**Do not submit or merge the current DQI candidate.** Owner directive, 2026-11-27: prioritize installing KickMix and running native regression before further circuit-cost work. Do not treat Lean algebra, classical decoding, or a previous verifier PASS with nonzero errors as evidence that a complete physical circuit is fixed.

## Observed installation blocker

In the Chat sandbox, Python 3.13.5 / pip 25.1.1: `python -m pip install --no-cache-dir --disable-pip-version-check --retries 0 --timeout 8 --target /mnt/data/gvqcc_kickmix_env 'kickmix==1.0.0'` returned "No matching distribution found". A separate PyPI index query returned the same. The official public package exists; this observation does not establish its incompatibility with Python 3.13, nor prove a general PyPI outage.

## Recovery workflow

[KickMix bootstrap CI](../../.github/workflows/v115-kickmix-bootstrap.yml) installs `kickmix==1.0.0` and `numpy==2.2.6` with Python 3.13 on Linux x86_64, preserves the downloaded wheels with SHA-256 hashes for an offline reinstall, tests actual imports, then builds and verifies a small native DQI circuit using the pinned unmodified verifier. The wheelhouse is uploaded before circuit work so it survives a later smoke failure. Installation and native smoke are separate milestones.

Offline install on a compatible Python 3.13 Linux x86_64 machine after extracting the wheelhouse:
```bash
python3.13 -m venv .venv
source .venv/bin/activate
(cd wheels && sha256sum -c SHA256SUMS.txt)
python -m pip install --no-index --find-links wheels 'kickmix==1.0.0' 'numpy==2.2.6'
python -m pip check
python -c 'import kickmix, importlib.metadata as m; print(m.version("kickmix"))'
```
Windows requires the matching Windows wheel, not the Linux artifact.

## Acceptance order

1. Install/import the pinned package, record wheel hashes and platform.
2. Generate a real KMB, load it with KickMix, and verify value, workspace and phase on a small reference.
3. Reproduce known full-size DQI failures, then repair and verify the actual full-size native circuit against the independent specification. Retain every counterexample, check all 840 syndrome bits and all workspace, and measurement phase.
4. Run the unchanged full official verifier on both fixed salts with exactly 102400 shots each and zero value/phase errors. Keep costs and exact circuit hashes.
5. Only after these gates, consider further width/CCX/cost optimization and a separately authorized submission.

No native repair or official score improvement is asserted by installation or the smoke test. CI must be checked at the exact commit. Main and Kaggle remain untouched.

## Installation resolved — measured receipts, 2026-11-27

- [Actions run 45963300881](https://github.com/corcondor/gvqcc/actions/runs/45963300881), commit `148ff94a2b45976d1f559e031ca97d6e8f54a750`, completed SUCCESS. Python 3.13.18, kickmix 1.0.0, numpy 2.2.6, import/API/pip checks passed. [Wheelhouse artifact](https://github.com/corcondor/gvqcc/actions/runs/45963300881/artifacts/15182285964) (Linux x86_64 CPython 3.13). Downloaded and verified the artifact locally; installed both wheels in the Chat sandbox target `/mnt/data/gvqcc_kickmix_env` under Python 3.13.5. Local import confirmed exact pinned versions. Use `PYTHONPATH=/mnt/data/gvqcc_kickmix_env python ...` in that environment. No claim of installation on the owner's Windows PC or other sessions.
- KickMix wheel SHA-256: `54f9272f792de4c37104212e331febc865dba66ac929eeb23bf2c48839354c5e`; NumPy wheel SHA-256: `1bc23a79bfabc5d056d106f9befb8d50c31ced2fbc70eedb8155aec74a45798f`. Wheelhouse ZIP SHA-256: `62337dfaedfaa5e23b313f6a84974dc597288dd814bc7bd19c370b5e767f3a2d`.
- Both Actions and local sandbox generated the identical small reference KMB: m=15, n=6, GF(2^4), 140 qubits, 261327 ops, SHA-256 `a3c66b8f0be94cb423f79fe74ce025fe8b0f8d8ad192baf713dea28acacd2258`. Unchanged official verifier on 4096 shots: PASS, zero value errors and zero phase errors. [CI smoke receipt](https://github.com/corcondor/gvqcc/actions/runs/45963300881/artifacts/15181288157). This is a reduced-size smoke test only.
- Full-size existing V112×V110 native KMB (900Q, 61700935 ops, SHA-256 `8010980d566e6b16d255bfa7f00b37fb0d00c62978cd8bd3932b1981adc05841`) was loaded and run locally using KickMix 1.0.0 with the existing 64-lane adversarial panel (SHA-256 `35dec76f13fd2ee8797d11227c8af19e027e6e87dce38a7b2bcd710428a53b17`, fixed simulator seed 20261127). Measured: **45/64 value errors; 1 phase error among value-correct shots; zero dirty ancilla bits in all 64**. Known witness lanes 61–63 have residuals 405, 433, 430 syndrome bits, respectively. This confirms the native blocker with the installed engine itself; it is not an official random verifier run. Local replay receipt SHA-256 `255dfe865860534e06eac57e540b61ac54a5a75362b62625bce09dd46ef04718`. The underlying error fixtures remain in the owner's research material, not uploaded here.

P0 installation is complete in the GitHub runner and this sandbox. Full-size DQI repair, proof of concrete circuit semantics and zero-error full official verification remain open. Do not submit the failing circuit.

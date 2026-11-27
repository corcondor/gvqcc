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

# GVQCC cross-session native circuit reconciliation — 2026-11-27

> **Research-only checkpoint. Not a Kaggle submission and not a new leaderboard score.**  
> Sources: exact, previously saved V112 and V110-extended 18-member ZIP archives.  
> No KMB gate in any source component has been modified by the cross-session merge.

## Latest verified source components (instruction count, not paid cost)

| Task | Source | Native instructions | Q | Evidence state |
|---|---|---:|---:|---|
| Chemistry (`dfthcsos/`) | V112 | **299,691** | **405** overall, 128 angle loader | Source official verifier passed default and fresh salt, 78,016 shots each. Expected 3,262.5 Toffoli/pass. |
| Inverse square root (`invsqrt.kmb`) | V110 extended review | **27,533** | **37** | Source official verifier passed 3,133,452 legal inputs × 1 shot; no paid-gate improvement. |
| DQI (`dqi.kmb`) | V110 extended review | **61,700,935** | **900** | Native component and cross-session source archive were hashed and reviewed; **known restoration/value errors remain**. Official final PASS not obtained. |
| **Combined** | Per-task, byte-preserving composition | **62,028,159** | unchanged | 18 native submission members; ZIP CRC and SHA-256 verified. **Not independently passed through the official combined verifiers.** |

Differences: **−49,910 native instructions** versus the stand-alone V112 62,078,069-ops archive; **−1,984** versus the stand-alone V110-extended 62,030,143-ops archive. These reductions arise from selecting components already independently constructed, **not from a new circuit synthesis method**.

The source NPZ is byte-identical in both archives. The composite archive contains 15 angle loaders, `dfthcsos/submission.npz`, `invsqrt.kmb`, and `dqi.kmb` (18 files). All members are matched to their source reports by SHA-256 and byte counts. See `composition_manifest.json`.

## Source provenance (SHA-256 pinned)

- `GVQCC_V112_AllTasks_62078069_Verified_Rewrites_NOT_SUBMITTED.zip` — `030588b9ceeb604cc20406ac3c56ad54e89af555a2ce8d3b1c5bc78a0ad6ee39`
- `GVQCC_V110_Checked_Extended_62030143_AllTasks.zip` — `4e75bdf2a7b31c3ae70f91073eb15bd550ab1bd3137852e17581f7af9abd8919`
- `GVQCC_V112_Joint_Transport_Code_Proofs_and_Research.zip` — includes `FINAL_MANIFEST.json` and the original `replay_all.py` / proof files.
- `GVQCC_V110_Review_Results_and_Manifest.json` — the V110-extended file-level hash/official validation manifest.

The archives and reports are held in the owner's saved ChatGPT Library. The 75-MB full native ZIP is **not stored as a GitHub repository blob**; this GitHub checkpoint records exact file hashes, source scripts, and the replay recipe. Rebuilding locally requires obtaining the named source ZIPs from the owner. The cross-session archive is separately saved as `GVQCC_V112xV110_CrossSession_62028159_NOT_SUBMITTED.zip` (SHA-256 `344f259bbfeab3edff270dd6b191e3a9e4a99c648d1bab357be4c835193d93a6`). This avoids implying that a pointer is the binary itself.

## Reconstruct

```bash
python research/cross-session-latest-20261127/compose_native.py \
  --v112 GVQCC_V112_AllTasks_62078069_Verified_Rewrites_NOT_SUBMITTED.zip \
  --v110 GVQCC_V110_Checked_Extended_62030143_AllTasks.zip \
  --v112-research GVQCC_V112_Joint_Transport_Code_Proofs_and_Research.zip \
  --v110-manifest GVQCC_V110_Review_Results_and_Manifest.json \
  --out GVQCC_V112xV110_CrossSession_62028159_NOT_SUBMITTED.zip \
  --manifest cross_session_manifest_regenerated.json
```

The compiler copies each source member unchanged, checks that every source member matches its verified source manifest, verifies identical NPZ coefficients, and then verifies the 18-member output ZIP with CRC and SHA-256. The output ZIP SHA may be sensitive to Python/zlib version, but **member SHA hashes are authoritative**.

Original V112 orchestration and mathematical checks are retained in the `v112/` subdirectory for audit. The full separate research ZIP contains the remaining mathematical certificates and dependencies.

## What is *not* claimed

- No paid-gate reduction (Chemistry 3,262.5 expected Toffoli/pass; InvSqrt 37Q; DQI 900Q).
- No 36Q complete InvSqrt, 888Q DQI, or correction to the known DQI restoration error.
- No new successful DQI full official verification, and **no Kaggle submission**.
- The hypothetical 3,260 Toffoli/pass chemistry version is **unverified**: neither native circuit nor source validation receipt has been located. It is not included.
- **33.34224** is a preexisting expected estimate for a separately validated combination, **not** a new score from this package. **~33.3465** is a conditional projection *only if* a valid 3,260/pass file is supplied with the same Q and lambda, not an achieved score.
- The V112 official single-seed InvSqrt sample score difference is attributable to a shifted sampling stream following HMR cleanup, not proven expected-cost reduction.

## Related GitHub research

- [PR #179](https://github.com/corcondor/gvqcc/pull/179) (chemistry 3,267 Toffoli/pass official PASS on both salts; separate older task basis)
- [PR #180](https://github.com/corcondor/gvqcc/pull/180) (chemistry 3,271/pass + invsqrt official PASS; separate task basis)
- [PR #178](https://github.com/corcondor/gvqcc/pull/178) (36Q research has significantly more generic rotations and is not a paid-cost replacement for the 33-rotation InvSqrt)

**Revalidation gate before promotion:** run unchanged competition verifiers on the composite native ZIP, pin source and output checksums, retain DQI value/phase-error counts and exact seeds, recompute the joint cost/score, and only then consider any submission or merge to `main`.
# Step 1 failure report: V8 1,219×75, real-KMB measured (2026-11-23 JST)

**STRICT GATE: FAIL. Step 2 was NOT started.** No official Kaggle score claim.

## Inputs / provenance

- Source words from `v8_c46_angle_fixture_public.json` (1219 × 75, 7-bit), mirrored bit6→bit7 for signed-gauge 8-bit KickMix loader input; SHA on raw fixture `e17119791be643d66a992bfc7469223546146a86223f1b7e9a9a345b2878d870`.
- GitHub Actions: [K8 run #45061572998](https://github.com/corcondor/gvqcc/actions/runs/45061572998) and [all-bank run #45061929224](https://github.com/corcondor/gvqcc/actions/runs/45061929224).
- Rust binary: `manwithacat/kickmix-engine` pinned `166b61d2e0a7404ace8acf62a6f269105e6b97f1`, `cargo build --release -p qrom-plan`.
- Emitter: `experiments/oss_chained_angle/tensorqrom.py`; KickMix `1.0.0` native KMB writer; independent `third_party/manwithacat/kmsim.py`; additional bit-packed symbolic HMR coefficient checker.
- Exact k8 generated KMB SHA-256 `2f3509566c844e17c30383348463808a3fb34469e183ebf49fe94b283896d6e8`; original public k8 KMB SHA-256 `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`.

## Results (actual generated circuit; NOT modeled)

| Metric | Published reference | qrom-plan+tensorqrom |
|---|---:|---:|
| k8 Toffoli | **211** | **343** (+132) |
| k8 qubits | 128 | 119 |
| 15-loader Toffoli sum | **3357** | **5145** (+1788) |
| Every emitted loader width | ≤128 | **119** |
| 1219-address exact value/select/scratch, independent `kmsim.py` | PASS | **15/15 × 3 initial-word cases PASS** |
| Full 1219-address HMR **symbolic coefficient** cancellation, independent bit-parallel check | PASS | **15/15 × 3 initial-word cases PASS** |

**No Toffoli record**; error-check gate passes, cost gate fails. The KMB generation produced real binary KMBs and text KMXs for all 15 banks. Earlier original public KMBs were checked separately with forward 0..14 and backward 14..0 on all 1219 legal addresses (error=0 on value, select, scratch, HMR coefficient; round-trip zero words), not regenerated here.

## Differential anatomy (original vs new, k8)

The binary parser counted real `CCX` gates by output target:
- Public: 82 scratch-target, **129 word-target** (82 HMR, 211 CCX in total; 128Q).
- New: 75 scratch-target, **268 word-target** (80 HMR, 343 CCX in total; 119Q). The register reuse/measurement sites differ.
- The public circuit uses two scratch×scratch→scratch CCXs and additional scratch-dependent products, not a fixed monomial-cache template. In the new circuit, a zero-relation Lera-style decomposition uses 263 paired products plus 80 cache Toffolis =343.

For the identical source table, public k8 on a **zero initial 35-bit word register** makes 11,597 wrong output bits over 1219 addresses if compared to an address-only XOR oracle; random initial words make 17,355 wrong bits. On the previous bank's **actual input words B7**, public k8 yields **0 wrong bits**. Both cases have phase coefficient 0 and clean scratch. Therefore the public 211T circuit exploits the forward/reverse **reachable-state contract**; plain `tensorqrom.build_circuit` is a *stronger independent XOR loader*, requiring correctness on zero/previous/random initial words. The two circuits are not being synthesized to identical contracts. Do **not** treat the cost gap as merely random-seed underoptimization.

## Upstream qrom-plan limitations observed

Rust `qrom-plan` fixes `CACHE_TOFFOLIS = 89` for a 1363-row high-cache shape; the real 1219-address cached-monomial emitter uses **80**. Thus an upstream plan reported as 352 is an actual **343**.
The k8 mixed-feature tensor has 525 coordinates, `rank=76`, 167 single-slot annihilator relations. Zero relation is feasible, giving 263 paired products (352 modeled / 343 actual). Its `structured` method with target 240/270/300 relations only reaches 180 independent relations and returns `span_feasible=False`, **no plan emitted**. Other banks similarly fail constrained structural admission with these settings.
This is a **bounded failure of the employed OSS generation family**, not a proof that every 128Q circuit with <211T is impossible.

## Reproduction

```bash
# Workflow clones and compiles pinned upstream Rust qrom-plan, then:
python experiments/oss_chained_angle/run_step1.py \
  --qrom-plan external/kickmix-engine/target/release/qrom-plan \
  --banks all --counts 170,175,180,210,240 --seeds 2 --trials 6 --samples 12 \
  --out outputs/step1-all15
```

Exit code 3 means strict baseline reproduction not attained even if all generated KMBs pass independent correctness and Q cap.

## Next lawful Step1 action only

Use the original public k8/15 loaders' actual **reachability-dependent input-word controls** and nonlinear helper-node DAG as the recovery target. Extract and replay the exact *reachable* state mapping and HMR cleanup, rather than forcing a single-step arbitrary-word XOR interface. Any attempt that changes this structure must reconstruct full KMB with Q≤128 and independent full forward/backward reachable-state verification. No Step2 word/angle perturbations until baseline gate passes.

All numeric results above are actual source/KMB runs; no claimed official submission or score.


## Follow-up Step1 rerun: 15 banks 4,202T (still NOT reproduced)

[GitHub Actions run #45062135473](https://github.com/corcondor/gvqcc/actions/runs/45062135473) reused the unchanged V8 words and pinned Rust binary, but included **single-slot annihilator ranks** as explicit structured counts. It emitted and verified all 15 KMBs; this supersedes the initial 5,145T only for **best cost** (the 5,145T zero-relation result remains a valid separate baseline).

| k | Published T | New actual T | Q | Delta T |
|---:|---:|---:|---:|---:|
| 0 | 245 | 305 | 119 | +60 |
| 1 | 240 | 303 | 119 | +63 |
| 2 | 217 | 270 | 119 | +53 |
| 3 | 217 | 268 | 119 | +51 |
| 4 | 217 | 272 | 119 | +55 |
| 5 | 240 | 303 | 119 | +63 |
| 6 | 217 | 270 | 119 | +53 |
| 7 | 240 | 303 | 119 | +63 |
| 8 | 211 | **265** | **119** | **+54** |
| 9 | 217 | 270 | 119 | +53 |
| 10 | 217 | 272 | 119 | +55 |
| 11 | 240 | 303 | 119 | +63 |
| 12 | 217 | 271 | 119 | +54 |
| 13 | 211 | 265 | 119 | +54 |
| 14 | 211 | 262 | 119 | +51 |
| **sum** | **3357** | **4202** | **119 each** | **+845** |

K8 uses 167 independent single-slot relations and 185 paired products: cache 80 + 185 = **265 real Toffolis**, compared with the Rust planner's 274 cost (its 89-cache fixed offset). The k8 zero-relation candidate was 263 products + 80 = 343. This change drops **78 real T** on k8, **943 T** across the family relative to the previous zero-relation construction.

Checks: `kmsim.py` **45 of 45** (15 banks × 3 input classes; all 1219 addresses), independent bit-parallel HMR coefficient proof **45 of 45**, scratch/selection preserved, 128Q cap **15 of 15**. The generation/validation runs finished; the CI job's strict baseline gate correctly concludes **failure**. It does not start Step2.

Artifact: https://github.com/corcondor/gvqcc/actions/runs/45062135473/artifacts

**Important causal diagnosis:** The public k8 KMB maps the *reachable previous-bank word* to the next value (0 errors) but is not an arbitrary-target XOR oracle: 11,597 wrong output bits on zero target, 17,355 on random targets over 1219 addresses. The regenerated `tensorqrom` version computes the strictly more demanding independent XOR mapping on all three initial target cases; therefore neither 265T nor 211T is directly comparable as evidence of suboptimality at an identical input contract. The public construction has 82 temporary nonlinear scratch targets / 129 output-target CCX; the produced 265T circuit has a different cache/word schedule. Closing Step1 requires reachable-state-aware synthesis or faithful reconstruction of the public structure.

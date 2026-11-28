# Full-circuit applicability and direct mask adjoint (research only)

Baseline: PR #306 / #299 Joint, canonical KMB SHA256 a8b5c62e24e7e44818bd46d75f8fa00a2bb9de64965c8c07912637dd58d7ebea; 900Q, 87,704,819 ops, 311,202 CCX, 6,686 CCZ, 108 CSWAP, 317,996 static paid. Independent C++ 102400-shot mean from #306: 316126.4307519531, 0 observed errors; conditional aggregate 33.34244155360765, threshold 315627.53075 at fixed 900Q and other costs. Fresh local KickMix replay: distribution 256/256 clean, saved panel 225/256 union errors, dense 70/144 union errors. Known faults unchanged; no full candidate emitted.

## Exact whole-tape audit

Instruction bins (million-aligned, not claimed to be exact semantic boundaries): 0..41M 0 paid; 41..57M 126825 paid; 57..62M 44275 paid; 62M..end 146896 paid. New affine-conjugated common-output quadratic block search: 1136187 windows, 0 admissible reductions. Symbolic abstraction on all 317888 CCX/CCZ and 108 CSWAP, 966 product candidates with no new atom: no exact live-wire affine match, even extended to full linear-span elimination. Abstraction is conservative, NOT a global optimality proof.

## Native joint phase-only contraction

Original #300 joint product shapes, with a classical coefficient covector and a phase-only consumer. Baseline builds product into clean ancillas, phases, reverses. Candidate moves evaluation in place on input banks and pushes covector through interpolation, then uses actual conditional CZ field-product phase. No classical selection using quantum inputs. Tests cover 64 captured +128 freshly generated degree-bound examples, two seeds each; 384 shots per circuit, all four state/phase/scratch/mask counters zero.

| Shape | Q before/after | CCX before/after | ops before/after |
|---|---:|---:|---:|
| 2,9,3,8,k=6 | 360/264 | 1008/0 | 44770/11817 |
| 4,18,5,17,k=13 | 708/528 | 2184/0 | 206930/53061 |

Candidate SHA256 k=6 65e8415060fc28ef7a2d09af0cfd42a4af00fa919a0388f89296488ccb3f55df; k=13 b083101c628c6e4dabf56dbd978dc5e91a955e20eab93f684e850eb356ecae1a. Only valid if output polynomial is phase-only and covector is classical. Cannot simply delete value-producing products in full DQI.

## Direct raw mask phase reference

Let S_j=sum e_x*x^(j+1). Trace-dual encoding m_x is the field element satisfying Tr(e_x*m_x)=the bit mask pairing. For monic locator P and R interpolating m_x/x at roots, phase=Tr(sum R_j*S_j). Extract the locator from the first matrix row of #303 half-Padé, not from reverse continued-fraction reconstruction; no individual error amplitude calculated. Checked trace pairing bijection on all 4096 mask words. All 1440 saved cases (weights 0..35) phase exact. Root enumeration and interpolation are performed on host for this reference: this is not an allowed quantum runtime branch. Coherent mask-to-residue generation and width/cost are still open; this is the binding seam between #303 and #301.

Strict Lean 4.35.0 check 14/14 success, https://github.com/corcondor/gvqcc/actions/runs/46144556053. Scope is algebraic identities, not a verified complete compiled DQI.

Vercel Sandbox HTTP 402 Hobby quota exhausted until 2026-12-01 00:00 UTC; no plan upgrade. Local KickMix and GitHub Actions used instead. No new score, no main changes, no submission.
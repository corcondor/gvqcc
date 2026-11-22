# GVQCC k8 multi-pattern experiment: 2026-11-23

## Status
**No circuit below public 211 Toffoli was produced.** No new official Kaggle leaderboard score claimed.

The public 211T KMB was retrieved and SHA-pinned through [GitHub Actions #45047992163](https://github.com/corcondor/gvqcc/actions/runs/45047992163) and independently checked against the old integer words on all 1219 legal addresses, forward and reverse, with all scratch bits zero and symbolic HMR phases canceled.

Public k8 SHA256: `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`.

### Exact old 213T -> public 211T comparison

| | Old | Public |
|---|---:|---:|
| Total T | 213 | 211 |
| Scratch product T | 82 | 82 |
| Output product T | 131 | 129 |
| Scratch product functions shared, by multiset | 74/82 | 74/82 |
| Output product functions shared | 0 | 0 |

Only the **last eight** scratch product functions changed; the entire output nonlinear decomposition changed. This evidence motivates selecting the high cache and recompiling the complete output together. It is not by itself a proof of why the author obtained the improvement.

### Variants actually generated and tested, each 211 T

| Real KMB variant | CX | Result |
|---|---:|---|
| Original public k8 | 28935 | baseline |
| Adjacent CX cancellations | 28889 | both directions PASS |
| Provably commuting CX cancellations | 24183 | both directions PASS |
| Exact cache control rebase at scratch index 74 | 28938 | both directions PASS |
| Exact cache control rebase at scratch index 77 | 28938 | both directions PASS |
| Exact cache control rebase at scratch index 81 | 28938 | both directions PASS |
| Compound rebases at indices 74+77+81 | 28944 | both directions PASS |
| Compound + CX commutation | 24192 | both directions PASS |

A cache rebase uses `ab=a(b⊕c)⊕u` when `u=ac` has already been computed. We located 30 one-site candidate identities and built 3 single-site KMBs plus compound. All present changes are score-neutral.

### Failed score-relevant local searches

- Output tensor 5->4: 3439 five-fanout dependencies, 0 candidate substitutions.
- Output tensor 6->5: 29297 six-fanout dependencies; 28809 rank-5 independent cases, 0 candidate substitutions.
- Direct commuting CCX pair collapse: 0 in the published 211T and the commuting-CX-normalized 211T.

These are bounded negative searches with the scratch cache fixed; they do **not** prove 211 is globally minimal.

### Priority for next score-improving trial

1. **High-cache products, especially the last 8, jointly with global output multiplicative complexity** (highest causal evidence from real 213->211 diff).
2. Alternate nonlinear cache structures and delayed workspace scheduling, using our SHA-verified KMB seeds to test exactness.
3. Full code-aware integer angle table reparameterization with the high-bit borrowing / signed-gauge invariants; synthesize matching KMB before counting.
4. Deprioritize more standalone local output-tensor 5/6-term rewrites without changing cache (negative tests).

If k8 drops from 211 to 210 T per pass, with chemistry T_total=13214 and all other costs unchanged, the arithmetic score change from 33.17023 would be about +0.00167. One bank is a compiler development test, not a complete route to 33.5.

### Collaboration

See [CLAUDE_REVIEW_TASK.md](./CLAUDE_REVIEW_TASK.md). The assistant has not invoked Claude because the current connected tools have no authenticated Claude runtime. The handoff makes it possible for the user to run Claude Code or share the research bundle with Claude without repeating our failed scans.

### Limits

Checks use exact reachable 1219 integer-table addresses, two directions, scratch return and symbolic HMR phase tracking. They are not the unchanged official Kaggle verifier; no Kaggle submission was performed.

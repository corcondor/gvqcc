# HMR multi-measurement quotient: research only

This branch extends #293 phase-debt identities, but the actual input tape is
the available #295 pooled candidate, not the lower-static #293 or #294 tape.
No leaderboard improvement, no submission, no merge to main.

## Reproducer

```sh
sha256sum pool_global.kmb
# ddbd1d660cd7a0d9a8daccfbc3b41bc6e07ea0dc3a205bb9a0422aa148d11828
g++ -std=c++17 -O2 guard_joint.cpp -o guard_joint
./guard_joint pool_global.kmb candidate.kmb
sha256sum candidate.kmb
# 13c442726bc467ee3eaedc66b1f2405c7298b7e5a561b56f04f163ad0534fc2f
```

Adjacent guarded cubic pairs searched: 666. Successful exact rewrites: 6.
Each has rank-4 coordinates, with 16 assignments x 4 guard assignments
checked exhaustively, including lower-degree phase remainder, dirty-wire
restoration and affine coordinate checks. The two guard values are not
assumed independent. The private scratch classical bits are restored.
All six old/new intervals (0-indexed endpoints):
```
27426854 27426873
27596793 27596812
27761088 27761107
27926678 27926697
28095068 28095087
28264933 28264952
```

|Metric|Parent|Candidate|
|---|---:|---:|
|Q|900|900|
|Instructions|67471518|67471656|
|CCX|311509|311509|
|CCZ|6692|6686|
|CSWAP|108|108|
|Static paid|318309|318303|

Paired KickMix replay with common measurement seeds, 256-shot batches:
1024 ordinary, 622 saved counterexamples, 144 dense weight probes. All
four paired differences zero. Ordinary errors 0/1024 both;
ordinary mean paid 316100.3212890625 both. Saved union errors 411/622 both,
dense union errors 70/144 both. Those stress fixtures are not ordinary
distribution samples and do not estimate the competition error rate.
The six pairs are mutually exclusive on the actual guard structure;
no executed paid improvement, no new independent official verifier claim.

## Generalized debt transport

For original/candidate difference p*d (p=ab), CNOT transports d by
its binary linear map. HMR adds p*d_i*m_i to the phase difference and
removes that measured direction. If all value differences disappear,
all remaining debt is p times the XOR of recorded coefficients.
A compensation CZ controlled by that parity is exact if its two
control forms remain available and their semantics and scope agree.
The new Lean file proves these Boolean identities, arbitrary-list
aggregation and the full-space noninjective projection counterexample.
It is not a Lean proof of the full DQI tape.

Searches on the complete #295 tape:
- 42 additional co-active nonadjacent cubic candidates: zero accepted.
- 4882 CCX/phase bridge opportunities: zero accepted.
- 86563 eligible CCX single-debt transport starts: zero eliminations.
- 306590 CCX starts in quotient-fusion search: zero accepted.
These are bounded searches, not global lower bounds.

#292 archived InvSqrt and 15 ANGLE circuits were recovered and checked
against their source hashes. The new searches yielded no paid wins.
37-to-36Q affine packing on InvSqrt stops at original gate 302:
the projected update lacks a full-space reversible extension in this
simple model. A locally exact temp-removal rewrite at 7720..7728 reduces
nine operations to three, retains 37Q and 1507 static paid. No full
official verifier rerun or portfolio improvement is asserted.

Preserve the previously verified #292 submission baseline. #293/#294
exact KMBs were not available to this session. The candidate here is
research-only and should not replace them.

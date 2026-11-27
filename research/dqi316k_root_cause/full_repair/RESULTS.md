# 316K all-chart / coherent weight integration (NOT SUBMISSION)

Pinned parent SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52, 900Q, static paid 318972. KickMix 1.0.0.

## Native results
| KMB | Q | Static paid | Ops | Validation |
|---|---:|---:|---:|---|
| guard52 | 898 | 3112305 | 27099572 | 1664/1664 data/tag/dirty/phase clean |
| pole_free_fwd / rev (each) | 899 | 16556586 | 53691872 | 1792/1792 each value/dirty/phase clean; 864 legal rational checks |
| low3 | 877 | 4822 | 77202 | 1190+24 clean selector shots |
| high135 | 889 | 250182 | 10131502 | 754+20 clean selector shots |
| joint_weight902 | 902 | 6546114 | 221097324 | low 830/830 clean; high 90/414 value failures, 42 raw phase failures |

Full corrected later-chart panel: 40 inputs x 2 seeds; joint_weight902 has 44 value, 30 raw phase, 20 dirty, 0 mask errors (overlap). Earlier third-chart test recurrence was incorrect and is withdrawn as evidence of forced later poles. Correct recurrence f_next=(1/f+h)/g.

## Fixed donor native branches: all known tested counterexamples now pass
Classical **external** screen uses true legal weight and checks all finite Hermite charts from syndrome before choosing fixed scale of existing 18-extension-root pad (low), or fixed multiplicative rotation (high). Neither selector cost nor coherent integration is included here. Not a universal existence proof.

| Branch | Native shots | Errors (value, phase, dirty, mask) | Mean paid |
|---|---:|---|---:|
| high scale 1 |372|0,0,0,0|316089.8333333333|
| high scale 2 |194|0,0,0,0|316037.92783505155|
| low scale 1 |830|0,0,0,0|316113.07108433737|
| low scale 2 |48|0,0,0,0|315976.9583333333|

All 1444 shots on 722 inputs pass; per branch 900Q and 318972 static paid; mean paid 316092.46468144044 on this diagnostic panel. No official verifier/score.

## Algebra
For u≠0, (u*conj(u))*v=b*u² iff conj(u)*v=b*u. In characteristic 2, H(u,v)=conj(u)*v+b*u covers the union of first/second unsafe cases including u=0. H(u+t*p,v+t*q) is quadratic in t. For the chosen pad H(p,q)=3135926 ≠0, three distinct nonzero scales guarantee a safe first pair. Does NOT guarantee later pairs. Native stress tests forced low choice 3 in all 24 shots; high tests forced first 1,2,4,8,16 rotations invalid (20 shots, chosen 2,3,5,9,17, all clean). High selector is first-pair only and expensive.

The 52-moment guard reuses infinity-CF: denominator degree sum ≤17+35=52 excludes a legal low/high alias. Full 70-word infinity-CF encoder and inverse avoid finite chart poles but do not implement DQI phase oracle. Native unit-series reciprocal uses U^(3·5·17)=U^255=U^-1 for U^128=1. Lean FirstPole316 / AllChart316 prove local algebra, not whole physical circuit equivalence.

## Artifacts and hashes
guard52 621322f4b2592cbe91b2a36eaf74e4127fdee3708dc6e4c165408b1a8aba723d
pole_free_fwd 0b8b1ea906619b40cba033a2328de54b95ff23a7cd617470b82ccfca78c182d8
pole_free_rev 3dc45abe042cab31c78f509ec376056846c8bc8d70309ec4515d12effd8dbde5
joint_weight902 a7b16ab64bd0f044603c58507af916f20fc9daf4344e53db673b7ac7bf7fd0f9
low3 56be5f5757d2834fd5fc90d9ae24bdbe4d6cc77720b76e428a4fa15050bc8440
high135 766d47542e4e1139ea42f7329454e3acba4b24cc1e97817b44950750bff8aa13

Full generator dependencies, exact fixture and receipt files in conversation core research archive. The archive includes guard and local selectors; large encoder and joint binaries are reproducible from generators, not in core archive. For next native integration, reuse internal rank/chart state rather than expensive independent decoder, and implement coherent scan-index transformation (quantum-controlled classical mask assignment is not permitted by the gate interface). Need 900Q and cost recovery, universal chart availability/decoder correctness, full official verification and shadow rule audit. No submission, no main merge.

# 898Q HMR transport and factoring experiment

Research only. Parent V122 (#203) SHA256 `e77328088f5c6bda1028000d1158205a27d29f9f5c721ee3121aacb8d5a505f3`. Candidate SHA256 `69419eaf34cfbe364582aa42ef0894bcdcfe822e182654f501c078404b26848d`.

| | Parent | Candidate |
|---|---:|---:|
| Q | 898 | 898 |
| Mean paid, identical 4096 inputs | 417016.8513183594 | 416924.8513183594 |
| Static paid | 476009 | 475917 |
| Instructions | 51176598 | 51176778 |

88 terminal HMR transports and 4 same-target CCX factorizations. Native matched 1728, distribution/weight 4352, adversarial 230, emergency 384 shots: 6694 total, zero value/phase/workspace errors. No full official verification of the new candidate and no universal proof. Boolean identities are separate from the binary parser, reachability, and full quantum semantics.

Target mean <=344000 is NOT achieved: gap 72924.8513183594. Old 343998-class record has known failures; its incomplete source archive lacks dqi_build_patch_r4jt.py and dqi_int_pinvar.sh. Attempted rebuilding with available public arithmetic patches, but graph loading did not finish within the trial timeout. No gain claimed from these patches, no submission. Full binary, exact rewrite C++ sources and receipts are in the separately delivered research ZIP.

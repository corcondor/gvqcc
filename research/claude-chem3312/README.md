# Chemistry (dfthcsos) angle loaders at 3,312 Toffolis per pass

## 概要（日本語）
化学タスクの角度ローダー15本を、1パス **3,356 → 3,312 Toffoli** にしました（公式 dfthcsos 検証器 PASS、コスト
249,379,397）。群の先頭の5本は自作の構成、配線型の8本は「物理的に使われないセル」の値を置き直して作り直しています。
他者の回路・値はコピーしていません（土台は maoxin123 の公開ローダー、手法は goodpjw2008 を参照）。
クレジットは `NOTICE.md`（Original builder: **Syed Asad Ali**, Apache-2.0）。

## Result

| | before (ours) | now |
|---|---:|---:|
| loader Toffolis per pass | 3,356 | **3,312** |
| official chemistry cost | 251,051,553.94 | **249,379,397.06** |
| Toffoli count (verifier) | 13,212 | 13,124 |
| qubits | 405 | 405 |
| lambda_eff | 46.917982 | 46.917982 |

Per loader (k = 0..14): 244, 233, 217, 214, 218, 233, 217, 233, 211, 214, 214, 233, 214, 209, 208.

Local combined score with our invsqrt (cost 60,918.318) and the public DQI circuit used in our package: 33.247666
(previous package 33.173685). Kaggle submission ref 58942727 (scoring pending when this was published).
Neither the invsqrt nor the DQI circuit is included here.

## Contents
- `family_3312.zip` — `angle_k_0..14.kmb` and `submission.npz`, byte-identical to the chemistry members of the
  submitted package (member hashes in `verification/official_receipts.json`).
- `verification/official_receipts.json` — official verifier runs (unchanged verifier files, internet off): salts default,
  `notebook-verification` and a fresh salt, all PASS, 78,016 shots each; the previous family reproduced at 251,051,553.94.
- `verification/xcheck.cpp`, `xcheck_output_3312.txt` — independent exact checker (own .kmb parser, no kickmix).
  Every address 0..1218, every measurement outcome, forward and reverse: 0 failures, and each family's circuit outputs
  equal its own angle table. Its final line reads `VERDICT FAIL` only because it requires the old and new tables to be
  identical; the 1,127 entries that differ are exactly the re-valued unused cells (see below).
- `src/` — the construction scripts as run. They depend on earlier local tooling that is not included, so they document
  the method rather than form a one-command generator. Paths were replaced by `<ROOT>`.

## Method
1. **Group-start loaders (k = 0, 1, 5, 7, 11): own construction, 245/240 → 244/233.** The address is re-framed so the
   low part is (a4,a5,a6): 160 high values and 61 unreachable cells per output instead of 5. Partial columns become
   linear relations among the high functions; a matroid-parity planner gives covers with 95 word products; a
   sliding-window search with measurement uncomputation (CZ-only phase fixes) builds the cached functions.
2. **Wired loaders (k = 3, 4, 8, 9, 10, 12, 13, 14), rebuilt on maoxin123's 82-product cache.** Table words at cells
   whose weight is numerically zero (physically unused) are chosen freely; each block gets its own decomposition with
   a zero column and special-column closers. Method: goodpjw2008's public notebooks (no circuit or value copied).

## Caveats
- Addresses 1219..2047 are never presented by the algorithm and are treated as don't-cares (the verifier simulates
  0..1218). The public loaders this replaces are likewise unclean on 824 of those 829 addresses.
- Group-start loaders 1, 5, 7, 11 are exact for the word values the algorithm presents (batch k-1 forward, batch k
  reverse), not for arbitrary starting words; the loaders they replace and the wired loaders behave the same way.
- Re-valued unused cells move the decoded rotation vectors by at most 3.4e-16; W and H2_I are unchanged.

## Check it yourself
Unzip `family_3312.zip` into `DIR/`, then with the competition data run
`python verifiers/dfthcsos/verify.py DIR`.

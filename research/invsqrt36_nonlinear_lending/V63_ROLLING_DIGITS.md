# V63 — rolling conditional-clean canonical phase digits (NOT SUBMISSION)

Based on actual PR136 signed-coset plan and pinned representative assignment, informed by PR146 canonical streaming, PR147 live Horner partial and PR142 interval exchange. The first 12 or 15 dyadic leaves are rounded to an exact 29- or 30-bit phase grid, combined into a multi-output digit table, and emitted in rolling XOR frames. Others retain their original Fourier phase. No 37Q dependency. Not a complete low-rotation arithmetic evaluator.

|Q|PR136 CCX/R/ops|V63 rolling CCX/R/ops|fixed proxy decrease|
|---|---|---|---|
|32|2614/8541/78218|4124/8154/94282|2.0053%|
|35|1912/8541/75660|4947/7920/105148|2.2936%|
|36|1805/8541/75244|4782/7920/104674|2.3885%|

Proxy Q(CCX+(239.00391117857393/33)*generic rotations), not official cost. CCX and ops increase. Rotation costs dominate. Same-width comparison; still far above competitive incumbent. New whole circuit 36Q SHA256 e8f304f851ffbca8e7879cbd8f3abb2f9c372809bf96d16ec1e610cba3303cdf, 35Q 46bbac44004aa8e96be16cc9bccc1922d6a2edccb65c8aa422cd69d1bb28646f, 32Q b14c0ba73360dcfbbf597d45393749d4017c7144601a97fc4cfeb8377ea5fcc3. All five emitted variants actually serialized and independently checked on 4,194,304 inputs, input/scratch restoration, every HMR phase coefficient, Fourier residue contraction and rounded digit phase equality. Exact tolerance check at 95% of tolerance for all 3,133,452 legal inputs; worst ratio 0.920378552749753 at x384 for rolling35/36; 0.9311041124165058 for 32Q. No physical rotation synthesis or official score.

180 initial and 216 rolling screened configurations. Matched 36Q/k9/B29 screen body: 1848→1577 CCX, 19635→16354 ops, same 29 phase digits (26 generic), emission counts only; selected rolling full Q36 is k10/B30 (648 generic removed, 27 added). Prefix flag guards borrowed high input lines, and all inactive offsets restored. Only truly clean flags HMR-erased. Delta transition uses old XOR new instead of clearing all slots. Small portable core independently ran 32768 conditional-care regression cases. Lean local identities only, not a full KMB proof.

Paper: Khattar/Gidney, Rise of conditionally clean ancillae, https://doi.org/10.22331/q-2025-05-21-1752 . Applied conditional cleanliness to borrowed high input lines. Related SelectSwap QROM tradeoff: https://arxiv.org/abs/1812.00954 (not implemented). OpenAI/math asymptotic results are not implemented. Archive GVQCC_V63_RollingDigits_NOT_SUBMISSION.zip SHA256 d59cb25ebf82c1ba77e75b8b0781c83900eb58c3600e651e0b9f26eb5006a22d includes actual runnable full compilers, verifiers, five native KMBs, receipts, plans and SHA manifest. This PR carries dependency-free exact core and local Lean certificates. Main and Kaggle unchanged.
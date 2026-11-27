# Whole DQI weighted half-degree / additive FFT integration

Research-only complete native circuit. Do not submit: measured mean paid remains above 316k.

Source lineage: public kv_unfused5 revision a9effc375527bf0b6962c178530d353eb70a3fcb, the #187/#190 coefficient fusion and route, terminal-pole repair from V127, and #171 additive FFT. #246 is the algebraic motivation; its separate canonical H input codec is not concatenated. Instead, the native weighted Barnett/Bézout converter already produces the equivalent weighted residue V at the roots. The factor 1/(x U(x)) is moved to the classical phase mask; the 70 selected roots retain the baseline projection/restore route. The full circuit operates on 70 syndrome words, not externally decoded D,H. This is not an integration of the exact #247 frozen donor, and no claim is made that the #246 missing native S-to-H codec has been implemented.

Vercel KickMix 1.0.0 session sbx_xdrMxWzqR4pjIcRdA7no1Cm2Kzis. Full build: 899Q, 42,566,825 ops, 473,009 static paid, SHA256 4172a26e1bc065904c56faf113701d7bc04844578863adbbde2f6285735915fd. Independent native tests: 288 uniform weights, 35 constant numerator, 24 all-pole, 96 single-pole, 1024 distribution; all 1467 pass all four checks. Distribution mean paid 414215.373046875. See actual verification and stage receipts. These samples do not prove zero error on every input.

Important: the expensive extraction / inverse extraction, synthesis / inverse synthesis, and Bézout converter are retained; this is why the circuit does not meet the competitive cost goal. The generic weighted scan has 4025 leaves, 44275 static paid. Do not compare this total with chart-only or D,H-only components.

Reproduce with bash reproduce.sh on an isolated Linux environment (Python 3.14, KickMix 1.0.0, sufficient memory). Native CI uploads the complete reconstructed KMB. Local Lean source formalizes four weighted residue/FFT identities; it is not a full circuit proof. No main merge, no Kaggle submission.
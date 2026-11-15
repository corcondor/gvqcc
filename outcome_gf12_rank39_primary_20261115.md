# GF(2^12) rank 38–39 claim: primary-source check

Date: 2026-11-15. This is a source audit, not an optimization result.

## Finding

No explicit rank-38, rank-39, or rank-40 binary bilinear decomposition of GF(4096) multiplication was located. The assertion that 38–39 is a known achievable count is **unsubstantiated by the primary sources checked**. This search does not prove such a decomposition cannot exist, nor that rank 42 is optimal.

## Checkable sources

1. Ballet, Chaumine, Pieltant, Rambaud, Randriambololona, Rolland, *On the tensor rank of multiplication in finite extensions of finite fields and related issues in algebraic geometry*, arXiv:1906.07456v2 (2020; journal 2021). https://arxiv.org/pdf/1906.07456
   - Table 2, printed page 39 / PDF page index 38, lists binary **symmetric upper bounds**: degree 10: 33; degree 11: 39; degree 12: 42; degree 13: 48.
   - These are upper bounds, not exact ranks. Since unrestricted bilinear rank is at most symmetric rank, this supplies an unrestricted upper bound of 42 too; it does not rule out lower asymmetric rank.
   - The table is attributed to Cenk–Özbudak (2010), Table 1. Section 5.3 explicitly discusses symmetric versus unrestricted algorithms.

2. Khattar et al., Google Quantum AI, *Verifiable Quantum Advantage via Optimized DQI Circuits*, arXiv:2510.10967v1 (2025). https://arxiv.org/pdf/2510.10967
   - Appendix C, Table VII, printed page 39 / PDF page index 38, gives Toffoli counts for degrees 10, 11, 12 of **39, 47, 51**, respectively. Its parity-control count for degree 11 is 46.
   - Thus its 39 is for GF(2^10), not GF(2^12). The existing competition 42-count kernel already beats this paper's degree-12 count.

3. Primary implementation write-up, *Design Patterns for Optimizing Quantum Circuits, Dispatch 1*, Almond, 2026-11-11. https://almond.org/writing/quantum-circuit-design-patterns-1
   - Identifies the public Kaggle GF(4096) multiplication as seven six-Toffoli leaves: 42 total. Its bilinear-product measurement cleanup assumes unchanged factors and repairs the phase using conditional CZ operations.

## Consequence for this project

- Do not replace or advertise a replacement for the exact 42-CCX kernel on the strength of the 38–39 claim.
- A successful candidate needs explicit binary factors for the target multiplication tensor. Check all 144 bit-basis input pairs against modulus 0x1053; then verify accumulator behavior, wire restoration, conditional gates, and phase semantics in its circuit context.
- The already-tested GF8 and mixed-place GF4 constructions are concrete 42-count upper bounds. Unsuccessful searches below 42 are not global optimality certificates.
- The claimed rank-173 combined `(H D, H_hi D^2)` construction by Chih-Kai Wang was not independently located by indexed web search. No factors or downloadable code were obtained. This is an access/discovery limitation, not a refutation of the claim; the exact discussion URL or attachment remains necessary.

Subsequent investigation by the parent agent located the actual discussion and coefficient appendix at https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/discussion/759048 . The parent reports the author's warning that the 1,376 GF24 products in the newer circuit have separate operands and are not eligible for that combined rank-173 rewrite. The indexed-web-search limitation above describes this subtask's initial result, not the current project access state.

No candidate circuit, decomposition factors, new score, or full-circuit verification is produced by this audit.

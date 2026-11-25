# V58 joint coefficient tensor and phase consumer (research only)
Base PR138. Native exact verification on all 3,133,452 legal inputs, with independent measurement phase cancellation and restoration. Five PARTIAL KMBs, not a full inverse-square-root oracle.
| Variant | Q | CCX | E[CCX+CCZ] | ops | generic rotations | HMR |
|---|---:|---:|---:|---:|---:|---:|
| normalized two-stage |32|1085|1090|6211|742|928|
| normalized two-stage |34|1037|1040|6077|742|896|
| normalized two-stage |36|1033|1034|6185|707|893|
| scaled C0 only |36|543|544|2659|98|80|
| scaled C2 only |36|464|465|2173|85|73|
The first three emit actual phase for exactly the V57 signed truncated weighted stream modulo 2^32, but not exponent scaling or downstream stages. V57 30Q E1278.5 and 8614 ops emitted snapshots, not phase. Joint coefficient loader: high address care states 10,01,11, low features cached; A=a xor b xor c, B=b xor c, C=a xor c, output A xor hB xor kC. Share GF(2) rank factors across multiple coefficients; compare three high gauges. Reuse equal-weight square monomials and 3:2 compressors before multiplying by coefficient bits. The two separate scaled-coefficient diagnostics use conditional zeros in normalized input U=x<<2s to shift coefficient bits left by s=10-e, then remove inactive padding via baseline rotations. These are not additive full-oracle estimates.
SHA256 of verified Q36 two-stage KMB: 29742a1f28f4893f131c97e4452cf59cf61d86265cb3c00f280fbfc491f56732.
Reproduction archive delivered separately (not committed here): GVQCC_V58_JointTensor_PhaseConsumer_NOT_SUBMISSION.zip, SHA256 2dc8dc4bf7d0ee0b8c8564b75047ee18813f658dae1c42fefa0dc636e1df1029. Includes full Python sources, five KMBs, receipts/tags, supporting inputs, verification script and local Lean source. Run python v58_verify_existing.py.
No official verifier or score. At 36Q the incumbent 60927.56 gives total cost ceiling 1692.4322; E1034 leaves 658.4322 before 707 rotations and remaining stages. Do not submit. PR139's 214/1234 Booth numbers are estimates, not verified native multiplier integration. Local Lean identities are not a formal proof of the entire KMB.

# Liston DQI repair experiments (not submission-ready)

The current adopted combination remains **31.08110475** (local conversion using official component costs; B13 DQI unchanged). The 32.30740 result is a public reference, not our score. No online submission.

## Flag checkpoint: native integrated DQI

The forward extractor X-measures an old zero flag. The original reverse route assumes zero flags are monotonic; this is false for the fixed weight-32 trace with f25=1 and f27=0. Preserve the actual flags coherently until reverse instead of inferring them. This revision has **889→897 qubits**, **−8 Toffoli per shot** on matched panels and uses the same original HMRs. No seeds or tags were selected or changed.

Matched 1,337 shots (six panels): the failing weight-32 case no longer has an incorrect value or dirty auxiliary register, **but has one phase error**. The independent weight-29 value failure and 15 fixed low-weight failures are unchanged. No new failures on previously passing shots. Do not submit this revision as-is.

## Zero denominator: isolated native component

For forward map (N,P) ↦ qN+PD, if q divides D, replacing (N,P) by (N+J(D/q),P+J) leaves those forward words unchanged. Simply guarding division cannot recover P. The separate prototype preserves the old 24-bit head only on the zero-denominator branch. Standalone native tests: 768 shots across three seeds, including the actual weight-29 state and a collision companion, with no value, phase or dirty-work errors. The prototype is not integrated into the full decoder. Naïvely retaining a full 25-qubit bank could be too expensive.

## Reproduce the integrated diagnostic artifact

Fetch the public Apache-2.0 [Liston milestone dataset](https://www.kaggle.com/datasets/mliston/vqcc-milestone-set-32-30740) on Kaggle, extract set/dqi.kmb, and run:

    python build_native_escrow.py set/dqi.kmb dqi_escrow.kmb

Python 3.11+ and NumPy. The writer checks the input and each rewritten window, and compares untouched operation columns. Expected output SHA-256: f6290ade4b12b19e407109a1effc887edb727b5c7d186c2ad973dba8c1fa0c60. See receipt.json for matched outcomes. No competition inputs, binaries or credentials are in this archive.

The public baseline was released by Matt Liston and collaborators; its NOTICE, license and upstream credits accompany the public dataset. These changes are experimental additions in this repository.

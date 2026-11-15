# Exact-mode DQI submission worker

`score3_submit_worker.py` is a self-contained CPU notebook cell. It rebuilds the
exact independently verified DQI candidate and combines it with the 17 other
members of the submitted score2 portfolio. It does not submit to the competition.

## Kaggle inputs

Attach all three inputs to a new private Python notebook:

1. The official Google Quantum AI — Verifiable Quantum Circuit Compilation data.
2. The output of [GVQCC verified 480CCX gauge128, version 1](https://www.kaggle.com/code/geocpuresearch/gvqcc-verified-480ccx-gauge128?scriptVersionId=369627280).
3. The output of [GVQCC 821 score2 verified, version 1](https://www.kaggle.com/code/geocpuresearch/gvqcc-821-score2-verified?scriptVersionId=369715705).

Paste the worker into one code cell and use Save & Run All with CPU. The worker
does not use network access or credentials. The inputs must contain the named
notebook output directories and their `submission.zip` files.

## Exact candidate and qualification

- Input DQI SHA256: `e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`.
- Rebuilt DQI SHA256: `9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1`.
- Rebuilt DQI size: 522,345,615 bytes.
- Input score2 ZIP SHA256: `dfacbef6f0e0c6856cca66a8497740eb1ac88d46dfb08884d02ce6637d91565f`.
- Fresh independent qualification: `score3_full_20261115_verification.json`,
  SHA256 `e98986fc57fcc920b6275f26fdd9b9db4f9f72604a24802b5a21cf85e05df714`.

The qualification records PASS for 102,400 shots, zero value errors, zero phase
errors, seed None, empty salt, and log2_delta = -128. Its circuit SHA256 is the
exact rebuilt candidate. The worker requires these fields and the pinned
official verifier hash before constructing the archive. It does not rerun the
full quantum verification; it reconstructs the already qualified bytes and
requires an exact SHA256 match.

The qualification's DQI cost is 359,734,745,778.9876, mean Toffoli-equivalent
count 382,095.68779296876, and 889 qubits. These are component metrics, not a
Kaggle Public Score and not a claim of improvement over the best submission.

## Reproduction and integrity checks

The embedded source archive contains the 47 Python files imported by the
upstream adaptive-gauge source, five local builder/splice modules, the original
gauge boundary record, proof and native selector evidence, the fresh full DQI
receipt, and source notices/licenses. Every embedded file has a pinned hash.

The worker recreates the original gauge128 prefix and suffix using the existing
builder, checks their original hashes, and calls the unchanged
`score3_gauge_sort.build_and_splice`. This retains its exact operand-column
boundary comparisons. The final DQI checksum must match the qualified candidate.

The other 17 members are copied from the exact score2 ZIP. Their uncompressed
hashes are checked against the portfolio manifest. The archive has exactly 18
files and must pass ZIP CRC validation.

`score3_submit_worker_portability.json` records an isolated test of the embedded
source imports, gauge geometry, sorting network size, native builder ABI, and
qualification binding. The whole candidate was not rebuilt during that test;
the existing exact build report is retained as the derivation evidence.

## Output

- `/kaggle/working/submission.zip`: complete 18-member competition artifact.
- `/kaggle/working/score3_submit_receipt.json`: source, rebuild, member and ZIP hashes.
- `/kaggle/working/score3_full_20261115_verification.json`: independent qualification.
- Source notice and two Apache 2.0 license files.

The notebook must finish successfully before choosing `submission.zip` in the
competition submission dialog. Save the actual Kaggle Public Score separately.

## Source attribution

The adaptive-gauge code derives from Syed Asad Ali's Apache-2.0 public DQI source
release, with the original author and AI-assistance credits retained in
`SOURCE_NOTICE.md`. The source archive is embedded for reproduction; upstream
frozen certificates are not treated as verification of the modified candidate.
Qualtran format references retain the separate Apache 2.0 notice.

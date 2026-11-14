#!/usr/bin/env python3
"""Build and statically check the self-contained offline Kaggle score worker.

This generator reads already retrieved public artifacts. It performs no network
access, circuit generation, quantum simulation or Kaggle submission.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path
import zipfile


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
SCRIPTS = (
    "kmb_profile.py", "dqi_ccx_peephole.py", "kmb_splice.py",
    "dqi_gauge_expand.py", "dqi_gauge_expand_verify.py", "verify_dqi_candidate.py",
    "reproduce_dqi_candidate.py", "replace_dqi_submission.py",
)
INVERSE_SHA = "e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6"
CHEMISTRY_SHA = "809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5"
UPSTREAM_RECEIPT_SHA = "05f66547aef625e9bf03c0d1025cdc136a9e3c71ae8a612ea1b90fd22a386e3f"
BASE_CHEMISTRY_SHA = "3f864a7aeaa4d78984c8822761782b63be2d553b229f487e79640a73be147c44"
REFIT_SHA = "67f711e1a9656f1af9e630e11d491791009971a8c6ec30f95f092bad74ce6073"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_pinned(path, expected):
    data = Path(path).read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Unexpected source bytes: {path}")
    return data


def literal_assignment(path, target):
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == target for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"Missing literal {target}: {path}")


def main():
    import numpy as np
    entries = {}
    for name in SCRIPTS:
        raw = (HERE / name).read_bytes()
        compile(raw, name, "exec")
        entries[f"tools/{name}"] = raw
    for name in ("NOTICE.md", "third_party/Qualtran_Apache_2.0.txt", "third_party/Syed_DQI_Apache_2.0.txt"):
        entries[f"tools/{name}"] = (HERE / name).read_bytes()
    entries["material/invsqrt.kmb"] = read_pinned(WORKSPACE / "dqi_inputs/invsqrt_e46d90c36d1b.kmb", INVERSE_SHA)
    base_bytes = read_pinned(WORKSPACE / "dqi_inputs/chemistry_4033/submission.npz", BASE_CHEMISTRY_SHA)
    entries["material/asterios_refit.npz"] = read_pinned(WORKSPACE / "dqi_inputs/chemistry_4033/asterios_refit.npz", REFIT_SHA)
    with np.load(io.BytesIO(base_bytes), allow_pickle=False) as baseline:
        arrays = {name: np.array(baseline[name]) for name in baseline.files}
    with np.load(io.BytesIO(entries["material/asterios_refit.npz"]), allow_pickle=False) as refit:
        for name in ("W", "H2_I"):
            arrays[name] = np.array(refit[name])
    reconstructed = io.BytesIO()
    np.savez_compressed(reconstructed, **arrays)
    assert digest(reconstructed.getvalue()) == CHEMISTRY_SHA, "NPZ reconstruction is not byte exact"
    assert reconstructed.getvalue() == read_pinned(WORKSPACE / "dqi_inputs/chemistry_4033/submission_asterios_full.npz", CHEMISTRY_SHA)
    entries["material/invsqrt_upstream_receipt.json"] = read_pinned(
        WORKSPACE / "official_sources/atakan_v15_reused_receipt.json", UPSTREAM_RECEIPT_SHA)
    official = literal_assignment(WORKSPACE / "official_sources/atakan_v15_cell_04.py", "OFFICIAL")
    official_pins = {name: value for name, value in official.items()
                     if name.startswith(("kickmix/", "verifiers/dfthcsos/"))
                     or name in ("verifiers/dqi/verify_submission_dqi.py", "verifiers/dqi/__init__.py", "verifiers/LICENSE.txt")}
    published_members = literal_assignment(WORKSPACE / "official_sources/atakan_v15_cell_04.py", "MEMBERS")
    loaders = {}
    for number in range(15):
        name = f"angle_k_{number}.kmb"
        expected = published_members[f"dfthcsos/{name}"]
        read_pinned(WORKSPACE / "dqi_inputs/chemistry_4033" / name, expected)
        loaders[name] = expected
    notice = """# Sources and scope

This private offline worker builds the96-CCX plus128-label adaptive-gauge DQI
candidate, runs the unchanged official default102400-shot DQI verification,
runs the full official chemistry verification, and packages a submission ZIP.
It does not call any Kaggle submission API or access credentials/network.

DQI baseline821 and adaptive-gauge original sources:
https://www.kaggle.com/datasets/syed3000/vqcc-own-circuit-portfolio
https://www.kaggle.com/datasets/manwithacat/vqcc-apache-public-circuits
Copyright2026Syed Asad Ali, Apache-2.0. Original source archive and notices are
retained during the run; the exact archive SHA is pinned in the worker.

4033-Toffoli public chemistry loaders and underlying factorization:
https://www.kaggle.com/datasets/maoxin123/qcc-chemistry-4033-toffoli-loaders
https://www.kaggle.com/code/maoxin123/qcc-v27-4033-toffoli-coded-word-chemistry
The loader bytes are retained exactly. W/H2_I use Asterios Panoras's public
fixed-word refit, embedded in this worker. The full factorization is reconstructed
from the exact3f864a7a public4033 NPZ and embedded W/H2_I, preserving array order
with numpy.savez_compressed. The result must match full SHA
809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5 before use.

Unchanged inverse e46 and its public full-verification receipt:
https://www.kaggle.com/code/atakanaldemir/qcc-gap-3-residue-repair-and-c43-native-compiler
Public version15 embeds the exact circuit and reused receipt. The one-Toffoli
dead-write reduction is credited there to Asterios Panoras; inherited inverse
authors and lineage remain credited by that source. No new inverse verification
is claimed:200540928-shot evidence is explicitly reused from the public receipt.

Official competition, verifiers, Kickmix engine and reference data:
https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
https://github.com/quantumlib/Qualtran
Official files are hash-pinned and are not edited. Qualtran Apache-2.0 and Syed
Apache-2.0 license texts and the repository NOTICE are embedded in this notebook's
source payload under tools/third_party/ and tools/NOTICE.md.

New changes: exact commuting CCX fanout merges at eight24-operation blocks;
expansion of Syed's classical adaptive-gauge candidate set from64to128;
exact operand-column splicing with prefix/suffix checks; complete verification;
and replacement of DQI only in a separately assembled public baseline ZIP.
No frozen upstream certificate is claimed to certify the changed decoder.

Full verifier PASS establishes validity under the checked workload, not a
guaranteed leaderboard increase. DQI can retain a nonzero allowed error rate.
"""
    entries["SOURCE_NOTICE.md"] = notice.encode()
    manifest = {
        "schema": "gvqcc-offline-kaggle-worker-payload-v1",
        "files": {name: {"sha256": digest(data), "bytes": len(data)} for name, data in sorted(entries.items())},
        "official_pins": official_pins,
        "chemistry_loader_pins": loaders,
        "public_material": {
            "source_archive_sha256": "49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763",
            "inverse_sha256": INVERSE_SHA, "chemistry_npz_sha256": CHEMISTRY_SHA,
            "chemistry_base_npz_sha256": BASE_CHEMISTRY_SHA,
            "chemistry_embedded_refit_sha256": REFIT_SHA,
            "inverse_upstream_receipt_sha256": UPSTREAM_RECEIPT_SHA,
            "inverse_scope": "Unchanged bytes with reused public200540928-shot verification evidence",
        },
    }
    entries["payload_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zipped:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 14, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, data)
    packed = lzma.compress(archive.getvalue(), preset=6)
    encoded = base64.b64encode(packed).decode("ascii")
    template = (HERE / "kaggle_score_worker_template.py").read_text()
    worker = template.replace("__PAYLOAD_BASE64__", encoded).replace("__PAYLOAD_SHA256__", digest(packed))
    compile(worker, "kaggle_score_worker.py", "exec")
    # Independently decode the rendered worker's literal payload and compare
    # every member hash; do not execute main or the reproduction driver.
    worker_tree = ast.parse(worker)
    decoded_literal = next(ast.literal_eval(node.value) for node in worker_tree.body
                           if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
                           t.id == "EMBEDDED_PAYLOAD_B64" for t in node.targets))
    verified_archive = lzma.decompress(base64.b64decode(decoded_literal, validate=True))
    assert digest(base64.b64decode(decoded_literal)) == digest(packed)
    with zipfile.ZipFile(io.BytesIO(verified_archive)) as zipped:
        assert set(zipped.namelist()) == set(entries)
        for name, original in entries.items():
            assert zipped.read(name) == original, name
    output = HERE / "kaggle_score_worker.py"
    output.write_text(worker)
    result = {
        "worker": str(output), "worker_bytes": output.stat().st_size,
        "worker_sha256": digest(output.read_bytes()), "source_payload_sha256": digest(packed),
        "source_payload_compressed_bytes": len(packed), "embedded_files": len(entries),
        "embedded_file_hashes": manifest["files"], "chemistry_loader_pins": loaders,
        "official_pins": official_pins,
        "validation": {"worker_syntax": "PASS", "embedded_script_syntax": "PASS",
                       "rendered_payload_hashes": "PASS", "chemistry_npz_byte_exact_reconstruction": "PASS",
                       "local_numpy_version": np.__version__, "heavy_execution": "NOT_RUN"},
    }
    (HERE / "kaggle_score_worker_build.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ("embedded_file_hashes", "chemistry_loader_pins", "official_pins")}, indent=2))


if __name__ == "__main__":
    main()

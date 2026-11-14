#!/usr/bin/env python3
"""Replace only dqi.kmb in an existing submission ZIP, retaining all other bytes.

Requires a completed, original DQI verifier JSON for 102,400 shots at the
competition confidence setting. This tool checks the record's consistency and
the candidate hash; it does not execute the verifier or authenticate the JSON's
author. The original DQI is pinned to the user's 821bf8d157c0 baseline.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys
import tempfile
import unicodedata
import zipfile

import kmb_profile


BASELINE_DQI_SHA256 = "821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3"
REQUIRED_SHOTS = 102400
REQUIRED_LOG2_DELTA = -128
CHUNK_BYTES = 1 << 20
MAX_VERIFICATION_JSON_BYTES = 4 << 20


class PackageError(ValueError):
    """The input or proposed output cannot be packaged without ambiguity."""


def file_hash(path):
    with Path(path).open("rb") as stream:
        return stream_hash(stream)


def stream_hash(stream, output=None):
    digest = hashlib.sha256()
    size = 0
    while block := stream.read(CHUNK_BYTES):
        digest.update(block)
        size += len(block)
        if output is not None:
            output.write(block)
    return digest.hexdigest(), size


def stat_identity(path):
    info = Path(path).stat()
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def no_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PackageError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def reject_nonfinite_json(value):
    raise PackageError(f"Non-finite JSON number is not accepted: {value}")


def read_verification(path, candidate_profile):
    path = Path(path)
    with path.open("rb") as source:
        raw = source.read(MAX_VERIFICATION_JSON_BYTES + 1)
    if len(raw) > MAX_VERIFICATION_JSON_BYTES:
        raise PackageError("The verification JSON exceeds the 4 MiB limit")
    try:
        result = json.loads(raw, object_pairs_hook=no_duplicate_json_keys,
                            parse_constant=reject_nonfinite_json)
    except (UnicodeError, json.JSONDecodeError) as ex:
        raise PackageError(f"Invalid verification JSON: {ex}") from ex
    if not isinstance(result, dict):
        raise PackageError("The verifier result must be a JSON object at the top level")
    if result.get("status") != "PASS":
        raise PackageError("The completed verifier result must have status PASS")
    if type(result.get("verified_shots")) is not int or result["verified_shots"] != REQUIRED_SHOTS:
        raise PackageError("The verifier must report verified_shots=102400; a smoke run is insufficient")
    if "num_shots" in result and (type(result["num_shots"]) is not int or result["num_shots"] != REQUIRED_SHOTS):
        raise PackageError("The optional num_shots field disagrees with the required 102400 shots")
    confidence = result.get("log2_delta")
    if type(confidence) not in (int, float) or not math.isfinite(confidence) or confidence != REQUIRED_LOG2_DELTA:
        raise PackageError("The verifier must report the official log2_delta=-128 confidence setting")
    sha = result.get("circuit_sha256")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
        raise PackageError("The verifier must report a full circuit_sha256")
    if sha.lower() != candidate_profile["raw_kmb_sha256"]:
        raise PackageError("The verification circuit_sha256 does not match the new DQI file")
    for key in ("num_qubits", "num_bits", "num_ops"):
        if type(result.get(key)) is not int or result[key] != candidate_profile["header"][key]:
            raise PackageError(f"The verifier's {key} does not match the new KMB header")
    # Nonzero DQI error counts can be valid under the official statistical test.
    for key in ("value_errors", "phase_errors"):
        if type(result.get(key)) is not int or not 0 <= result[key] <= REQUIRED_SHOTS:
            raise PackageError(f"The verifier must report a valid {key} count")
    if result["value_errors"] + result["phase_errors"] > REQUIRED_SHOTS:
        raise PackageError("The total reported DQI errors exceed the verified shot count")
    score = result.get("score")
    if type(score) not in (int, float) or not math.isfinite(score) or score <= 0:
        raise PackageError("The verifier must report a finite, positive task cost in score")
    return result, hashlib.sha256(raw).hexdigest()


def inspect_members(archive):
    members = archive.infolist()
    seen = set()
    path_types = {}
    dqi = None
    for info in members:
        name = info.orig_filename
        if not name or "\x00" in name or "\\" in name or "//" in name:
            raise PackageError(f"Invalid ZIP member name: {name!r}")
        if name.startswith("/") or ":" in name:
            raise PackageError(f"Absolute/drive/alternate-stream ZIP path is not allowed: {name!r}")
        components = name.rstrip("/").split("/")
        if any(part in ("", ".", "..") for part in components):
            raise PackageError(f"Ambiguous or traversing ZIP path is not allowed: {name!r}")
        canonical = unicodedata.normalize("NFC", name.rstrip("/")).casefold()
        if canonical in seen:
            raise PackageError(f"Duplicate or ambiguous ZIP member: {name!r}")
        seen.add(canonical)
        path_types[canonical] = info.is_dir()
        if info.flag_bits & 1:
            raise PackageError(f"Encrypted ZIP member is not supported: {name!r}")
        mode = info.external_attr >> 16
        kind = stat.S_IFMT(mode)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise PackageError(f"ZIP links and special files are not allowed: {name!r}")
        if (kind == stat.S_IFDIR and not info.is_dir()) or (kind == stat.S_IFREG and info.is_dir()):
            raise PackageError(f"ZIP file/directory type disagrees with its name: {name!r}")
        if info.is_dir() and info.file_size:
            raise PackageError(f"Directory member has a nonempty payload: {name!r}")
        leaf = components[-1].casefold()
        if leaf == "dqi" or leaf.startswith("dqi."):
            if name != "dqi.kmb" or info.is_dir():
                raise PackageError(f"Only one root-level dqi.kmb is allowed; found {name!r}")
            dqi = info
    if dqi is None:
        raise PackageError("The baseline ZIP must contain exactly one root-level dqi.kmb")
    for name in path_types:
        parts = name.split("/")
        for count in range(1, len(parts)):
            ancestor = "/".join(parts[:count])
            if ancestor in path_types and not path_types[ancestor]:
                raise PackageError(f"A ZIP member is also used as a directory: {ancestor!r}")
    return members, dqi


def without_zip64_extra(extra):
    """Let zipfile regenerate size-dependent ZIP64 fields; retain other extras."""
    result = bytearray()
    cursor = 0
    while cursor < len(extra):
        if len(extra) - cursor < 4:
            raise PackageError("Malformed ZIP extra field")
        tag, size = struct.unpack_from("<HH", extra, cursor)
        end = cursor + 4 + size
        if end > len(extra):
            raise PackageError("Truncated ZIP extra field")
        if tag != 1:
            result.extend(extra[cursor:end])
        cursor = end
    return bytes(result)


def output_info(original, size):
    result = copy.copy(original)
    result.file_size = size
    result.extra = without_zip64_extra(original.extra)
    return result


def replace_dqi(baseline_zip, new_dqi, verification_json, output_zip, receipt_path=None, progress=False):
    paths = [Path(p).resolve() for p in (baseline_zip, new_dqi, verification_json, output_zip)]
    baseline_zip, new_dqi, verification_json, output_zip = paths
    receipt_path = Path(receipt_path).resolve() if receipt_path is not None else output_zip.with_suffix(".receipt.json")
    if len(set(paths + [receipt_path])) != 5:
        raise PackageError("Input ZIP, DQI, verification JSON, output ZIP and receipt must be separate paths")
    for destination in (output_zip, receipt_path):
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {destination}")
        if not destination.parent.is_dir():
            raise PackageError(f"Output parent directory does not exist: {destination.parent}")
    # These checks stream the KMB; no kickmix.Circuit object or simulator is used.
    identities = {p: stat_identity(p) for p in (baseline_zip, new_dqi, verification_json)}
    candidate = kmb_profile.profile(new_dqi, max_register_summaries=0, progress=progress)
    if candidate["source"]["container"] != "file":
        raise PackageError("The new DQI must be a raw KMB file, not an archive")
    verification, verification_sha = read_verification(verification_json, candidate)
    baseline_sha, baseline_size = file_hash(baseline_zip)
    candidate_sha, candidate_size = candidate["raw_kmb_sha256"], new_dqi.stat().st_size
    with zipfile.ZipFile(baseline_zip, "r") as original:
        members, old_dqi = inspect_members(original)
        for member in members:
            without_zip64_extra(member.extra)
        with original.open(old_dqi, "r") as source:
            old_dqi_sha, old_dqi_size = stream_hash(source)
        if old_dqi_sha != BASELINE_DQI_SHA256:
            raise PackageError(
                "The baseline ZIP's DQI is not the pinned 821bf8d157c0 circuit: " + old_dqi_sha
            )
        records = []
        with tempfile.TemporaryDirectory(prefix=".dqi-package-", dir=output_zip.parent) as temporary:
            temp_zip = Path(temporary) / "submission.zip"
            with zipfile.ZipFile(temp_zip, "w", allowZip64=True) as output:
                output.comment = original.comment
                for info in members:
                    replacement = info.filename == "dqi.kmb"
                    size = candidate_size if replacement else info.file_size
                    with output.open(output_info(info, size), "w", force_zip64=size >= zipfile.ZIP64_LIMIT) as target:
                        if replacement:
                            with new_dqi.open("rb") as source:
                                after_sha, after_size = stream_hash(source, target)
                            if (after_sha, after_size) != (candidate_sha, candidate_size):
                                raise PackageError("The candidate DQI changed while packaging")
                            before_sha, before_size = old_dqi_sha, old_dqi_size
                        else:
                            with original.open(info, "r") as source:
                                after_sha, after_size = stream_hash(source, target)
                            before_sha, before_size = after_sha, after_size
                    records.append({
                        "name": info.filename, "directory": info.is_dir(),
                        "before_sha256": before_sha, "after_sha256": after_sha,
                        "before_bytes": before_size, "after_bytes": after_size,
                        "action": "replaced_dqi" if replacement else "preserved_verbatim",
                        "changed": before_sha != after_sha,
                    })
            # Validate the generated directory/CRC/size table without a second
            # full decompression of the large candidate. Payload hashes above
            # were computed from the very buffers written to the output stream.
            with zipfile.ZipFile(temp_zip, "r") as check:
                written, _ = inspect_members(check)
                if [i.filename for i in written] != [i.filename for i in members]:
                    raise PackageError("The output ZIP's member order/names changed")
                for old, info, record in zip(members, written, records):
                    if info.file_size != record["after_bytes"]:
                        raise PackageError(f"Output size mismatch: {info.filename}")
                    if record["action"] == "preserved_verbatim" and info.CRC != old.CRC:
                        raise PackageError(f"Unchanged member CRC mismatch: {info.filename}")
            for path, identity in identities.items():
                if stat_identity(path) != identity:
                    raise PackageError(f"An input changed during packaging: {path}")
            output_sha, output_size = file_hash(temp_zip)
            receipt = {
                "schema": "gvqcc-dqi-replacement-v1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "baseline_archive": {"path": str(baseline_zip), "sha256": baseline_sha, "bytes": baseline_size},
                "output_archive": {"path": str(output_zip), "sha256": output_sha, "bytes": output_size},
                "dqi": {
                    "member": "dqi.kmb", "new_source_path": str(new_dqi),
                    "required_baseline_sha256": BASELINE_DQI_SHA256,
                    "before_sha256": old_dqi_sha, "after_sha256": candidate_sha,
                    "before_bytes": old_dqi_size, "after_bytes": candidate_size,
                    "new_kmb_header": candidate["header"],
                },
                "verification": {"path": str(verification_json), "json_sha256": verification_sha,
                                 "result": verification,
                                 "scope": "Consistency-checked supplied verifier record; verifier not rerun by packager"},
                "non_dqi_members_byte_identical": True,
                "preserved_file_count": sum(not r["directory"] and r["action"] == "preserved_verbatim" for r in records),
                "members": records,
                "archive_note": "Member payload bytes are preserved; ZIP container/compressed bytes may differ.",
            }
            # Publish with atomic create-only links, never replacement/rename
            # over an existing file. Both temporary files are on the respective
            # destination filesystem, including when the receipt is elsewhere.
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".dqi-receipt-",
                                             suffix=".json", dir=receipt_path.parent, delete=False) as handle:
                temp_receipt = Path(handle.name)
                json.dump(receipt, handle, indent=2, ensure_ascii=False, allow_nan=False)
                handle.write("\n")
            published_zip = published_receipt = False
            try:
                os.link(temp_zip, output_zip)
                published_zip = True
                os.link(temp_receipt, receipt_path)
                published_receipt = True
            except BaseException:
                if published_zip and output_zip.exists() and os.path.samefile(temp_zip, output_zip):
                    output_zip.unlink()
                if published_receipt and receipt_path.exists() and os.path.samefile(temp_receipt, receipt_path):
                    receipt_path.unlink()
                raise
            finally:
                temp_receipt.unlink(missing_ok=True)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="*", metavar="PATH",
                        help="Optional positional form: BASELINE_ZIP NEW_DQI VERIFICATION_JSON OUTPUT_ZIP")
    parser.add_argument("--baseline-zip", type=Path)
    parser.add_argument("--dqi", type=Path)
    parser.add_argument("--verification", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args(argv)
    flagged = [args.baseline_zip, args.dqi, args.verification, args.output]
    if any(path is not None for path in flagged):
        if args.paths or any(path is None for path in flagged):
            parser.error("Use all four named flags, or four positional paths; do not mix the forms")
        baseline_zip, new_dqi, verification_json, output_zip = flagged
    else:
        if len(args.paths) != 4:
            parser.error("Provide --baseline-zip, --dqi, --verification, --output (or four positional paths)")
        baseline_zip, new_dqi, verification_json, output_zip = args.paths
    try:
        receipt = replace_dqi(baseline_zip, new_dqi, verification_json,
                              output_zip, args.receipt, args.progress)
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as ex:
        print(f"Packaging refused: {ex}", file=sys.stderr)
        return 1
    print(json.dumps({
        "output": receipt["output_archive"]["path"],
        "output_sha256": receipt["output_archive"]["sha256"],
        "dqi_sha256": receipt["dqi"]["after_sha256"],
        "preserved_non_dqi_files": receipt["preserved_file_count"],
        "verified_shots": receipt["verification"]["result"]["verified_shots"],
        "receipt": str(args.receipt or output_zip.with_suffix(".receipt.json")),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

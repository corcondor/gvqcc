"""Assemble an unchanged-physics-IR 18-member GVQCC research candidate.

Combines a PRE-EXISTING fixed-angle H2-only coefficient update and current
formally verified CNOT-only KMB rewrites. This is a provenance-aware assembler
and checker, not a novel physical optimizer or official KickMix verifier.
The original baseline and the donor archives are never overwritten.

Run with actual public V8 and prior H2-only 18-file donor ZIPs:
    python experiments/assemble_18file_native_candidate.py \
      --original-v8 public_v8_chemistry_3375T_reference.zip \
      --donor-18 old_H2_only_18files.zip \
      --optimized-angles /path/to/new/dfthcsos \
      --physics-reference chem_gpu_inputs.npz \
      --out full18_RESEARCH_ONLY.zip --report receipt.json \
      --parent-reported-score 33.13521306472598

Requires numpy/scipy, all fifteen real parent and replacement ANGLE KMBs,
the actual reference tensor, and a provenance-matched 18-member archive.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, getcontext
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile

import numpy as np
from native_kmb.linear_opt import certify_source_candidate
from native_kmb.real_kmb import KMB
from griffith_qcc.physics import evaluate_factorization

ENTRIES = ["invsqrt.kmb", "dqi.kmb"] + [
    f"dfthcsos/angle_k_{k}.kmb" for k in range(15)
] + ["dfthcsos/submission.npz"]


def digest_file(p: Path) -> str:
    dig=hashlib.sha256()
    with p.open("rb") as s:
        for chunk in iter(lambda:s.read(4<<20),b""):
            dig.update(chunk)
    return dig.hexdigest()


def digest_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def assemble(*, original_v8: Path, donor_18: Path,
             optimized_angles: Path, physics_reference: Path,
             out: Path, report: Path, parent_reported_score: str | None = None):
    if out.exists() or report.exists():
        raise FileExistsError("Refusing to overwrite original or completed output")
    getcontext().prec = 40
    with zipfile.ZipFile(original_v8) as parent, \
         zipfile.ZipFile(donor_18) as donor, \
         tempfile.TemporaryDirectory() as tdir:
        if len(donor.namelist()) != len(ENTRIES) or \
           set(donor.namelist()) != set(ENTRIES):
            raise ValueError("Donor must contain exactly the official 18-member layout")
        if parent.testzip() is not None or donor.testzip() is not None:
            raise ValueError("Corrupt reference ZIP")
        work=Path(tdir)
        oldp=work/"parent.npz"
        candidatep=work/"candidate.npz"
        oldp.write_bytes(parent.read("dfthcsos/submission.npz"))
        candidatep.write_bytes(donor.read("dfthcsos/submission.npz"))
        with np.load(oldp, allow_pickle=False) as z:
            baseline={k:z[k] for k in z.files}
        with np.load(candidatep, allow_pickle=False) as z:
            candidate={k:z[k] for k in z.files}
        if set(baseline)!=set(candidate):
            raise ValueError("NPZ keys were added or removed")
        changed=[k for k in baseline if not np.array_equal(baseline[k],candidate[k])]
        if changed!=["H2_I"]:
            raise ValueError(
                "Only H2_I may change. Changed keys: "+repr(changed)
            )
        before=evaluate_factorization(oldp,physics_reference)
        after=evaluate_factorization(candidatep,physics_reference)
        if not before["passes_physical_gates"] or \
           not after["passes_physical_gates"] or \
           after["lambda_eff"]>=before["lambda_eff"]:
            raise ValueError("No verified independent FeMoCo numerical improvement")
        all_proofs=[]
        for k in range(15):
            name=f"dfthcsos/angle_k_{k}.kmb"
            old=parent.read(name)
            if donor.read(name)!=old:
                raise ValueError("H2 donor modified the ANGLE circuit: "+name)
            a=work/f"old_{k}.kmb"
            a.write_bytes(old)
            b=optimized_angles/f"angle_k_{k}.kmb"
            source=KMB.read(a)
            revised=KMB.read(b)
            if source.render()!=old or revised.render()!=b.read_bytes():
                raise ValueError("Original or changed KMB failed binary roundtrip")
            formal=certify_source_candidate(source,revised)
            if source.nq!=128 or revised.nq!=128 or \
               source.paid()!=revised.paid():
                raise ValueError("Width or paid CCX has changed")
            formal.update(bank=k,original_sha256=digest_bytes(old),
                          revised_sha256=digest_file(b))
            all_proofs.append(formal)

        entries=[]
        with zipfile.ZipFile(out,"x",compression=zipfile.ZIP_DEFLATED,
                             compresslevel=3,allowZip64=True) as result:
            for name in ENTRIES:
                if name.startswith("dfthcsos/angle_k_"):
                    source=(optimized_angles/name.rsplit("/",1)[-1]).open("rb")
                else:
                    source=donor.open(name)
                h=hashlib.sha256()
                total=0
                with source as infile,result.open(name,"w",force_zip64=True) as output:
                    for blob in iter(lambda:infile.read(4<<20),b""):
                        h.update(blob)
                        total+=len(blob)
                        output.write(blob)
                entries.append(dict(member=name,sha256=h.hexdigest(),bytes=total))

        with zipfile.ZipFile(out) as checked:
            if len(checked.namelist())!=18 or \
               set(checked.namelist())!=set(ENTRIES) or \
               checked.testzip() is not None:
                raise AssertionError("Written candidate ZIP integrity failure")
        oldcx=sum(p["old_CX"] for p in all_proofs)
        newcx=sum(p["new_CX"] for p in all_proofs)
        total_paid=sum(p["old_CCX"] for p in all_proofs)
        if total_paid!=3375 or oldcx<=newcx:
            raise AssertionError("Unexpected real baseline or no legal CX improvement")
        expected_score=None
        if parent_reported_score is not None:
            old_score=Decimal(parent_reported_score)
            expected_score=str(old_score*(
                Decimal(str(before["lambda_eff"])) /
                Decimal(str(after["lambda_eff"]))
            )**(Decimal(1)/Decimal(3)))
        receipt={
            "status":"RESEARCH_18FILE_INTEGRATED_NUMERICAL_PASS_NATIVE_OFFICIAL_UNVERIFIED",
            "official_KickMix_two_salt_verification":False,
            "official_or_public_leaderboard_score_improved":False,
            "source_public_V8_zip_sha256":digest_file(original_v8),
            "donor_original_18_sha256":digest_file(donor_18),
            "candidate_18_zip_sha256":digest_file(out),
            "candidate_18_zip_size_bytes":out.stat().st_size,
            "all_18_member_SHA256":entries,
            "only_npz_array_changed":changed,
            "physics_original":before,"physics_candidate":after,
            "native_ANGLE_exact_symbolic_CX_proofs":all_proofs,
            "native_ANGLE_total_old_CX":oldcx,
            "native_ANGLE_total_new_CX":newcx,
            "native_ANGLE_total_paid_CCX_original_and_rewrite":total_paid,
            "official_new_score":None,
            "conditional_score_if_all_official_conditions_hold":expected_score,
            "important_warning":(
                "This recycles a prior H2-only physical change; improvements "
                "are tiny and not a novel scoring result. Original and changed "
                "KMBs are formally exactly equal, but this tool does not "
                "execute native official two-panel KickMix verification."
            ),
        }
        report.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
        print(json.dumps({
            k:receipt[k] for k in (
                "status","candidate_18_zip_sha256",
                "native_ANGLE_total_old_CX","native_ANGLE_total_new_CX",
                "native_ANGLE_total_paid_CCX_original_and_rewrite",
                "conditional_score_if_all_official_conditions_hold",
            )
        },indent=2))
        return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("original-v8","donor-18","optimized-angles","physics-reference",
                "out","report"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--parent-reported-score")
    a=p.parse_args()
    assemble(original_v8=a.original_v8,donor_18=a.donor_18,
             optimized_angles=a.optimized_angles,
             physics_reference=a.physics_reference,
             out=a.out,report=a.report,parent_reported_score=a.parent_reported_score)


if __name__=="__main__":
    main()

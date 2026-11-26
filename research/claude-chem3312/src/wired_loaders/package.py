"""Candidate package (NOT submitted): our current b806 zip with only the chemistry members replaced by a family that
passed the official verifier.  usage: python package.py FAMILY_DIR KV_LABEL OUT_NAME"""
import hashlib, json, shutil, sys, zipfile
from pathlib import Path

root = Path(r"<ROOT>")
here = root / "w_push14" / "planner"
src_zip = root / "w_push13" / "submit_b806" / "submission_b806.zip"
fam = Path(sys.argv[1]).resolve()
label = sys.argv[2]
out_zip = here / "best" / sys.argv[3]
kv_zip = root / "w_push8" / "kg" / "runs" / label / "out" / "dfthcsos_candidate_PASSING_GATE.zip"
assert kv_zip.exists(), "no passing official artifact for this label"


def sha_stream(fp):
    h = hashlib.sha256()
    for chunk in iter(lambda: fp.read(1 << 20), b""):
        h.update(chunk)
    return h.hexdigest()


def sha_file(p):
    with open(p, "rb") as f:
        return sha_stream(f)


def member_shas(z):
    out = {}
    for info in z.infolist():
        with z.open(info) as s:
            out[info.filename] = sha_stream(s)
    return out


assert sha_file(src_zip).startswith("5c946e36"), "unexpected source package"
replace = {f"dfthcsos/angle_k_{k}.kmb": fam / f"angle_k_{k}.kmb" for k in range(15)}
replace["dfthcsos/submission.npz"] = fam / "submission.npz"
if out_zip.exists():
    raise SystemExit(f"refusing to overwrite {out_zip}")


def zi(info):
    z = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    z.compress_type = zipfile.ZIP_DEFLATED
    return z


with zipfile.ZipFile(src_zip) as zin, zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
    for info in zin.infolist():
        if info.filename in replace:
            zout.writestr(zi(info), replace[info.filename].read_bytes())
            continue
        with zin.open(info) as s, zout.open(zi(info), "w", force_zip64=True) as d:
            shutil.copyfileobj(s, d, 1 << 20)

with zipfile.ZipFile(src_zip) as a, zipfile.ZipFile(out_zip) as b, zipfile.ZipFile(kv_zip) as k:
    names = [i.filename for i in a.infolist()]
    assert names == [i.filename for i in b.infolist()]
    ha, hb, hk = member_shas(a), member_shas(b), member_shas(k)
    diff = [n for n in names if ha[n] != hb[n]]
    # every chemistry member must equal the officially verified artifact
    chem = [n for n in names if n.startswith("dfthcsos/")]
    kmap = {n: h for n, h in hk.items()}
    for n in chem:
        key = n if n in kmap else n.split("/")[-1]
        assert key in kmap and kmap[key] == hb[n], f"{n} differs from the verified artifact"
    assert all(n.startswith("dfthcsos/") for n in diff), diff
    print("members:", len(names), "changed:", diff)
    print("dqi", hb["dqi.kmb"][:8], "invsqrt", hb["invsqrt.kmb"][:8])
zsha = sha_file(out_zip)
rec = dict(zip=str(out_zip), sha256=zsha, bytes=out_zip.stat().st_size, source=str(src_zip), family=str(fam), kv_label=label,
           changed=diff)
json.dump(rec, open(str(out_zip) + ".json", "w"), indent=1)
print(json.dumps(rec, indent=1))

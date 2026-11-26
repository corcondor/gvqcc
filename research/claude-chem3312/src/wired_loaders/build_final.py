"""Full chain: design -> special-row solution -> loader -> exact evaluator -> KMB -> verify_one fwd+rev -> family dir.
usage: python build_final.py TAG PART7 PART14 NAME [BASE_FAMILY]"""
import hashlib, json, shutil, sys, time
from pathlib import Path
import numpy as np
from special import *

HERE = Path(__file__).resolve().parent
ROOT = Path(r"<ROOT>")
sys.path.append(str(ROOT / "w_push11" / "dc" / "prep"))
import deadlib as dl
from sp4lib import K

t0 = time.time()
tag, p7, p14, name = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
base_fam = Path(sys.argv[5]) if len(sys.argv) > 5 else ROOT / "w_push12" / "dc3356" / "family_merged"
cstag = Path(p7).name
meta = json.load(open(next((HERE / "designs" / tag).glob("cs_*_meta.json"))))
parts = {7: json.load(open(p7))["classes"], 14: json.load(open(p14))["classes"]}
s = meta["s"]
pub, F, d, prods, words = build_pub(tag, n_closers=s)
k = d["k"]
B = make_builder(pub, meta["gamma"], words)
r = p4build.build_candidate(B, parts, seed=0)
assert r["ok"], r.get("info")
print("special rows built:", r["info"], f"{time.time()-t0:.0f}s", flush=True)
W2 = r["words"]
bk = K.Bank(k, W2)
spec = K.build_spec(bk, r["scratch"], r["outputs"])
res = K.evaluate(spec, bk)
print(f"evaluate: ok={res.ok} toffoli={res.toffoli} peak width {res.peak_width}", flush=True)
assert res.ok, res.violations[:3]
out = HERE / "out" / name
out.mkdir(parents=True, exist_ok=True)
kmb = K.emit(spec, bk)
path = out / f"angle_k_{k}.kmb"
sha = K.write_kmb(kmb, path)
fwd = K.verify_kmb(path, k, words=W2, direction="forward")
print("verify_one forward:", fwd, f"{time.time()-t0:.0f}s", flush=True)
rev = K.verify_kmb(path, k, words=W2, direction="reverse") if k else None
print("verify_one reverse:", rev, f"{time.time()-t0:.0f}s", flush=True)
np.save(out / "words.npy", W2)
# ---- family directory = base family + this loader + submission.npz with the new words (U refreshed)
fam = out / "family"
fam.mkdir(exist_ok=True)
for i in range(15):
    src = base_fam / f"angle_k_{i}.kmb"
    dst = fam / f"angle_k_{i}.kmb"
    if i == k:
        shutil.copyfile(path, dst)
    else:
        shutil.copyfile(src, dst)
with np.load(base_fam / "submission.npz", allow_pickle=False) as z:
    npz = {key: z[key].copy() for key in z.files}
W0 = npz["angle_words"].astype(np.int64)
npz["angle_words"] = W2.astype(npz["angle_words"].dtype)
V = dl.decode(W2, npz["tree_edges"].astype(np.int64))
R, Bb, N = npz["U"].shape
npz["U"] = V[N:].reshape(R, Bb, N).astype(npz["U"].dtype)
np.savez(fam / "submission.npz", **npz)
diff = np.argwhere(W0 != W2)
mask = np.load(ROOT / "w_push11" / "dead" / "dead_mask_1e-13.npy")
dead_ok = bool(all(mask[a, c] for a, c in diff))
print(f"table: {len(diff)} words changed vs base family, all dead cells: {dead_ok}; batches {sorted(set(int(c)//5 for a, c in diff))}")
report = dict(name=name, bank=k, toffoli=res.toffoli, kmb_sha256=sha, forward=str(fwd), reverse=str(rev),
              words_changed=len(diff), all_dead=dead_ok, special=str(r["info"]), seconds=time.time() - t0)
json.dump(report, open(out / "report.json", "w"), indent=1)
print(json.dumps(report, indent=1))

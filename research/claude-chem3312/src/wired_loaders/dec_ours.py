"""Decode OUR loaders (w_push12/dc3356/family_merged, maoxin123 lineage) into exact function tables.
Own planner code. Uses k8lib (w_push11/k8/model) only as the exact KMB reader / evaluator.
Writes planner/data/dec_k<k>.npz : scratch functions, output L/M functions, fan-outs, target deltas.
"""
import os, sys, json, time
from pathlib import Path
ROOT = Path(r"<ROOT>")
FAM = ROOT / "w_push12" / "dc3356" / "family_merged"
os.environ["K8_PUBLIC_DIR"] = str(FAM)
os.environ["K8_NPZ"] = str(FAM / "submission.npz")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, str(ROOT / "w_push11" / "k8" / "model"))
sys.dont_write_bytecode = True
from k8lib import *
import numpy as np

OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

def f2a(f):
    return np.unpackbits(np.frombuffer(f.to_bytes(153, "little"), np.uint8), bitorder="little")[:1219]

def run(k):
    t0 = time.time()
    bk = Bank(k)
    spec = extract_spec(FAM / f"angle_k_{k}.kmb", k, bk)
    r = evaluate(spec, bk)
    d = decompose(spec, bk)
    ns = len(d["scratch"]); no = len(d["outputs"])
    # symbol functions
    fn = list(bk.base_fn) + [0] * (ns + no)
    def val(form):
        f = FULL if form & 1 else 0
        m = form >> 1
        while m:
            low = m & -m
            i = low.bit_length() - 1
            f ^= fn[i]
            m ^= low
        return f
    order = [t for t in d["timeline"] if t[0] in ("S", "O")]
    Lf = [0] * (ns + no); Mf = [0] * (ns + no)
    allp = list(d["scratch"]) + [(L, M) for L, M, v in d["outputs"]]
    for kind, i in order:
        idx = i if kind == "S" else ns + i
        L, M = allp[idx]
        Lf[idx] = val(L); Mf[idx] = val(M)
        fn[46 + idx] = Lf[idx] & Mf[idx]
    S = np.array([f2a(fn[46 + i]) for i in range(ns)], np.uint8)
    SL = np.array([f2a(Lf[i]) for i in range(ns)], np.uint8)
    SM = np.array([f2a(Mf[i]) for i in range(ns)], np.uint8)
    U = np.array([f2a(Lf[ns + o]) for o in range(no)], np.uint8)
    V = np.array([f2a(Mf[ns + o]) for o in range(no)], np.uint8)
    FAN = np.array([[(v >> n) & 1 for n in range(35)] for L, M, v in d["outputs"]], np.uint8)
    BASE = np.array([f2a(f) for f in bk.base_fn], np.uint8)
    TGT = np.array([f2a(f) for f in bk.target], np.uint8)
    scr_forms = [[hex(L), hex(M)] for L, M in d["scratch"]]
    out_forms = [[hex(L), hex(M), hex(v)] for L, M, v in d["outputs"]]
    np.savez_compressed(OUT / f"dec_k{k}.npz", S=S, SL=SL, SM=SM, U=U, V=V, FAN=FAN, BASE=BASE, TGT=TGT)
    json.dump({"scratch": scr_forms, "outputs": out_forms, "timeline": d["timeline"], "gauge": d["gauge"],
               "toffoli": r.toffoli, "ok": bool(r.ok), "ns": ns, "no": no}, open(OUT / f"dec_k{k}.json", "w"))
    print(f"bank {k}: ok={r.ok} toffoli={r.toffoli} scratch={ns} outputs={no} ({time.time()-t0:.1f}s)", flush=True)

if __name__ == "__main__":
    for k in [int(a) for a in sys.argv[1:]] or [2, 3, 4, 6, 8, 9, 10, 12, 13, 14]:
        try:
            run(k)
        except Exception as ex:
            print(f"bank {k}: FAILED {type(ex).__name__}: {ex}", flush=True)

"""verify_one forward and reverse for every loader of a family directory against its own submission.npz"""
import sys, json, time
from pathlib import Path
import numpy as np
sys.path.insert(0, r"<ROOT>\w_push11\dc\oracle")
sys.dont_write_bytecode = True
import k8lib as K
fam = Path(sys.argv[1])
W = np.load(fam / "submission.npz")["angle_words"].astype(np.int64)
t0 = time.time(); res = {}; tot = 0
for k in range(15):
    p = fam / f"angle_k_{k}.kmb"
    f = K.verify_kmb(p, k, words=W, direction="forward")
    r = K.verify_kmb(p, k, words=W, direction="reverse") if k else None
    ok = f["status"].startswith("PASS") and (r is None or r["status"].startswith("PASS"))
    res[k] = (ok, f["toffoli"])
    tot += f["toffoli"]
    print(k, "OK" if ok else "FAIL", f["toffoli"], f"{time.time()-t0:.0f}s", flush=True)
print("all pass:", all(v[0] for v in res.values()), "toffoli per pass:", tot)

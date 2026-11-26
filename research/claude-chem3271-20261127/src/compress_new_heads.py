"""V71 family (PR #179) with our four 232 group-start loaders, compressed the same way (compress_kmb from PR #179)."""
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\81808\.openclaw\gvqcc")
sys.path.insert(0, str(ROOT / "w_push19" / "theirs"))
import v71_compress as V  # noqa: E402

v71 = Path(sys.argv[1])
dst = ROOT / "w_push19" / "v71h"
dst.mkdir(exist_ok=True)
for p in v71.iterdir():
    shutil.copyfile(p, dst / p.name)
heads = {1: "out_a/t__angle_k_1_n95_f13_s510.kmb", 5: "out_a/t__angle_k_5_n95_f13_s550.kmb",
         7: "out_b/t__angle_k_7_n95_f13_s570.kmb", 11: "out_b/t__angle_k_11_n95_f13_s610.kmb"}
for k, rel in heads.items():
    i, o, ccx = V.compress_kmb(ROOT / "w_push19" / "heads" / rel, dst / f"angle_k_{k}.kmb")
    print(f"k={k}: ops {i} -> {o}, CCX {ccx}")

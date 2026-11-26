"""Compress the four new 232 heads with the affine-block resynthesis from PR #179 (read before use)."""
import sys
from pathlib import Path

ROOT = Path(r"<ROOT>")
sys.path.insert(0, str(ROOT / "w_push19" / "theirs"))
import v70_compress as V  # noqa: E402

src, dst = ROOT / "w_push19" / "f3271", ROOT / "w_push19" / "f3271c"
dst.mkdir(exist_ok=True)
for p in src.iterdir():
    (dst / p.name).write_bytes(p.read_bytes())
for k in (1, 5, 7, 11):
    i, o, ccx = V.compress_kmb(src / f"angle_k_{k}.kmb", dst / f"angle_k_{k}.kmb")
    print(f"k={k}: ops {i} -> {o}, CCX {ccx}")

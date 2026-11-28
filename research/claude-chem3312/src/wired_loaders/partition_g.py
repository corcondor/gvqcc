"""partition both special rows for a specgen export.  usage: python partition_g.py TAG NAME [NPROC] [SECS]"""
import json, subprocess, sys, os, time, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
tag, name = sys.argv[1], sys.argv[2]
nproc = sys.argv[3] if len(sys.argv) > 3 else "2"
secs = sys.argv[4] if len(sys.argv) > 4 else "60"
d = HERE / "designs" / tag
meta = json.load(open(d / f"{name}_meta.json"))
cap = meta["cap"]
CS = str(HERE / "tmp" / "cs2.exe")
CS3 = str(HERE / "tmp" / "cs3.exe")
for ri in (0, 1):
    luck = meta["luck"][ri]
    ex = max(luck, 0) // 5
    ok = False
    t0 = time.time()
    for seed in range(1, 40):
        for off in ((6, 4, 2, 0), (8, 6, 3, 0), (5, 5, 4, 3), (10, 8, 4, 0)):
            targets = ",".join(str(cap + ex + o) for o in off)
            out = d / f"{name}_row{ri}.json"
            env = dict(os.environ, FLOOR=str(cap + max(ex - 4, 1)))
            p = subprocess.run([sys.executable, "-X", "utf8", str(HERE / "tmp" / "part_driver.py"), str(d / f"{name}_row{ri}.txt"),
                                str(cap), targets, secs, str(seed * 97 + ri), nproc, str(out), CS], capture_output=True, text=True, env=env, timeout=1200)
            res = json.load(open(out)) if out.exists() else {}
            if res.get("ok"):
                print(f"row {ri}: partition found (seed {seed}, targets {targets}) weights {res['weights']} {time.time()-t0:.0f}s", flush=True)
                ok = True
                break
            print(f"row {ri}: seed {seed} targets {targets} failed at level {res.get('level')} ({time.time()-t0:.0f}s)", flush=True)
            if time.time() - t0 > float(os.environ.get("MAXROW", "900")):
                break
        if ok or time.time() - t0 > float(os.environ.get("MAXROW", "900")):
            break
    if not ok:
        print("no partition for row", ri)
        sys.exit(1)

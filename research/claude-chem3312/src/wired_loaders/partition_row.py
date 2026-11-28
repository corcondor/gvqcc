"""partition one special row (specgen export).  usage: python partition_row.py TAG NAME ROW NPROC SECS MAXTIME"""
import json, subprocess, sys, os, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
tag, name, ri, nproc, secs, maxt = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], float(sys.argv[6])
d = HERE / "designs" / tag
meta = json.load(open(d / f"{name}_meta.json"))
cap = meta["cap"]
luck = meta["luck"][ri]
ex = max(luck, 0) // 5
CS = str(HERE / "tmp" / "cs2.exe")
t0 = time.time()
seed = 1
while time.time() - t0 < maxt:
    for off in ((6, 4, 2, 0), (4, 3, 2, 1), (8, 5, 2, 0), (3, 3, 3, 3)):
        targets = ",".join(str(cap + ex + o) for o in off)
        out = d / f"{name}_row{ri}.json"
        env = dict(os.environ, FLOOR=str(cap + max(ex - 4, 1)))
        subprocess.run([sys.executable, "-X", "utf8", str(HERE / "tmp" / "part_driver.py"), str(d / f"{name}_row{ri}.txt"),
                        str(cap), targets, secs, str(seed * 1009 + ri), nproc, str(out), CS], capture_output=True, text=True, env=env)
        res = json.load(open(out)) if out.exists() else {}
        print(f"seed {seed} targets {targets}: ok={res.get('ok')} level={res.get('level')} ({time.time()-t0:.0f}s)", flush=True)
        if res.get("ok"):
            print("FOUND", res["weights"], flush=True)
            sys.exit(0)
        seed += 1
        if time.time() - t0 > maxt:
            break
print("NOT FOUND")
sys.exit(1)

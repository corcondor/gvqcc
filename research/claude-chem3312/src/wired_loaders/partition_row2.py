"""Partition one special row: greedy "take the heaviest consistent class found" for the first three classes,
then the 4th class must absorb what is left (cs2, then cs3).  usage: python partition_row2.py TAG NAME ROW NPROC MAXTIME"""
import json, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tmp"))
from part_driver import read_system, run_cs, consistent

tag, name, ri, nproc, maxt = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
d = HERE / "designs" / tag
meta = json.load(open(d / f"{name}_meta.json"))
cap = meta["cap"]
fn = d / f"{name}_row{ri}.txt"
out = d / f"{name}_row{ri}.json"
nb, nu, rows, wts = read_system(fn)
CS2 = str(HERE / "tmp" / "cs2.exe")
CS3 = str(HERE / "tmp" / "cs3.exe")
tmpdir = d
luck = sum(wts) - 5 * cap
t0 = time.time()
seed = 1
secs1 = float(os.environ.get("SECS1", "25"))
os.environ.setdefault("GAP", "9")
while time.time() - t0 < maxt:
    pool = list(range(nb))
    classes = []
    for lvl in range(3):
        os.environ["GAP"] = "9"
        for k in ("ELIG", "KCOMP", "HEAVY"):
            os.environ.pop(k, None)
        floor = cap + max(luck // 6, 4) if lvl else cap + max(luck // 4, 4)
        best, el = run_cs(CS2, fn, pool, floor, secs1, seed * 1009 + lvl * 131 + ri, cap, nproc, tmpdir, f"p{ri}_{name}", stopw=cap + luck // 5 + 12)
        if best is None:
            best, el = run_cs(CS2, fn, pool, cap + 1, secs1, seed * 1009 + lvl * 131 + ri + 7, cap, nproc, tmpdir, f"p{ri}_{name}", stopw=cap + luck // 5 + 12)
        if best is None:
            break
        classes.append(sorted(best[1]))
        w = sum(wts[b] for b in best[1])
        pool = [b for b in pool if b not in best[1]]
        print(f"seed {seed} level {lvl}: weight {w} (excess {w-cap}) {time.time()-t0:.0f}s", flush=True)
    if len(classes) == 3:
        need = sum(wts[b] for b in pool) - cap
        print(f"seed {seed}: level 3 needs weight {need} (excess {need-cap}) from {len(pool)} blocks", flush=True)
        if need - cap > int(os.environ.get("MAXLAST", "17")):
            seed += 1
            continue                       # the last class would need too much excess: restart instead
        best, el = run_cs(CS2, fn, pool, need, secs1 * 2, seed * 7919 + ri, cap, nproc, tmpdir, f"p{ri}_{name}", stopw=need)
        if best is None and need - cap <= luck // 4 + 6:
            os.environ["GAP"] = "30"; os.environ["ELIG"] = "19"; os.environ["KCOMP"] = "0"; os.environ["HEAVY"] = "19"
            best, el = run_cs(CS3, fn, pool, max(need, 200), float(os.environ.get("SECS3", "120")), 777 + seed, cap, nproc, tmpdir, f"p{ri}_{name}", stopw=max(need, 200))
        if best is not None:
            classes.append(sorted(best[1]))
            pool = [b for b in pool if b not in best[1]]
            classes.append(sorted(pool))
            cons = [consistent(rows, c) for c in classes]
            w = [sum(wts[b] for b in c) for c in classes]
            if all(cons):
                json.dump(dict(ok=True, classes=classes, consistent=cons, weights=w), open(out, "w"))
                print(f"FOUND weights {w} ({time.time()-t0:.0f}s)", flush=True)
                sys.exit(0)
            print("last class inconsistent", cons, w, flush=True)
    seed += 1
print("NOT FOUND")
sys.exit(1)

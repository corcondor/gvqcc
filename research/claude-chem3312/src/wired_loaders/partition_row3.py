"""Partition one special row.  Classes 0-2: heaviest consistent class found by cs2.  Class 3: stream every class cs2
prints (weight >= need - SLACK) and test whether the remainder (possibly above capacity by a few bits) is consistent.
usage: python partition_row3.py TAG NAME ROW NPROC MAXTIME"""
import json, os, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tmp"))
from part_driver import read_system, run_cs, consistent, hexmask

tag, name, ri, nproc, maxt = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
d = HERE / "designs" / tag
meta = json.load(open(d / f"{name}_meta.json"))
cap = meta["cap"]
fn = d / f"{name}_row{ri}.txt"
out = d / f"{name}_row{ri}.json"
nb, nu, rows, wts = read_system(fn)
CS2 = str(HERE / "tmp" / "cs2.exe")
luck = sum(wts) - 5 * cap
t0 = time.time()
seed = int(os.environ.get("SEED0", "1"))
secs1 = float(os.environ.get("SECS1", "30"))
SLACK = int(os.environ.get("SLACK", "12"))
tested_total = 0


def save(classes):
    cons = [consistent(rows, c) for c in classes]
    w = [sum(wts[b] for b in c) for c in classes]
    if all(cons):
        json.dump(dict(ok=True, classes=classes, consistent=cons, weights=w), open(out, "w"))
        print(f"FOUND weights {w} ({time.time()-t0:.0f}s)", flush=True)
        return True
    return False


while time.time() - t0 < maxt:
    pool = list(range(nb))
    classes = []
    for lvl in range(3):
        os.environ["GAP"] = "9"
        floor = cap + max(luck // 6, 4) if lvl else cap + max(luck // 4, 4)
        stop = cap + luck // 5 + 12
        best, el = run_cs(CS2, fn, pool, floor, secs1, seed * 1009 + lvl * 131 + ri, cap, nproc, d, f"q{ri}_{name}", stopw=stop)
        if best is None:
            best, el = run_cs(CS2, fn, pool, cap + 1, secs1, seed * 1009 + lvl * 131 + ri + 7, cap, nproc, d, f"q{ri}_{name}", stopw=stop)
        if best is None:
            break
        classes.append(sorted(best[1]))
        w = sum(wts[b] for b in best[1])
        pool = [b for b in pool if b not in best[1]]
        print(f"seed {seed} level {lvl}: weight {w} (excess {w-cap}) {time.time()-t0:.0f}s", flush=True)
    seed += 1
    if len(classes) < 3:
        continue
    need = sum(wts[b] for b in pool) - cap
    wmin = max(need - SLACK, cap - 6)
    if need - cap > int(os.environ.get("MAXNEED", "30")):
        print(f"   level 3 would need excess {need-cap}: restart", flush=True)
        continue
    print(f"seed {seed-1}: level 3 streaming classes >= {wmin} (need {need}) from {len(pool)} blocks", flush=True)
    outs = [d / f"stream_{ri}_{name}_{i}.txt" for i in range(nproc)]
    procs = []
    for i, o in enumerate(outs):
        if o.exists():
            o.unlink()
        cmd = [CS2, str(fn), hexmask(pool), str(wmin), os.environ.get("SECS3", "420"), str(seed * 7919 + i + ri), str(o), "9", "100000",
               "0", str(cap), "300", "0", "0"]
        procs.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    seen = set()
    offs = [0] * nproc
    found = False
    tested = 0
    while not found:
        alive = any(p.poll() is None for p in procs)
        time.sleep(1.0)
        for i, o in enumerate(outs):
            if not o.exists():
                continue
            with open(o) as fh:
                fh.seek(offs[i])
                chunk = fh.read()
            end = chunk.rfind("\n")
            if end < 0:
                continue
            offs[i] += len(chunk[:end + 1].encode())
            for line in chunk[:end].split("\n"):
                parts = list(map(int, line.split()))
                if len(parts) < 3:
                    continue
                cls = tuple(sorted(parts[2:]))
                if cls in seen:
                    continue
                seen.add(cls)
                rest = [b for b in pool if b not in cls]
                if sum(wts[b] for b in rest) - cap > SLACK:
                    continue
                tested += 1
                if consistent(rows, rest):
                    if save(classes + [list(cls), sorted(rest)]):
                        found = True
                        break
            if found:
                break
        if not alive:
            break
    for p in procs:
        if p.poll() is None:
            p.kill()
    for p in procs:
        p.wait()
    for o in outs:
        if o.exists():
            o.unlink()
    tested_total += tested
    print(f"   level 3: {len(seen)} classes, {tested} remainders tested ({time.time()-t0:.0f}s)", flush=True)
    if found:
        sys.exit(0)
print("NOT FOUND", tested_total)
sys.exit(1)

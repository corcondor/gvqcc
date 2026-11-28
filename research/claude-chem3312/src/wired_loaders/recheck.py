"""exact matroid-parity check of every dumped gs2 state of finished attempts (greedy IL is only a lower bound)"""
import glob, json, sys, random
from pathlib import Path
from design import *
from planes import all_planes, plane_vectors, parity_rank
tag = sys.argv[1]; need = int(sys.argv[2])
d = HERE / "designs" / tag

class Inst2:
    def __init__(self, txt, jsn):
        lines = open(txt).read().split("\n")
        q, w, nf, k = map(int, lines[0].split())
        md = json.load(open(jsn))
        self.q, self.w, self.m = q, w, md["m"]
        cols = {}
        for ln in lines[1:1 + nf]:
            a = list(map(int, ln.split()))
            cols[a[0]] = a[1:]
        self._c = cols
        self.zeta = md.get("zeta13")
        self.piv = self.zeta.bit_length() - 1
        self.keep = [t for t in range(13) if t != self.piv]

    def columns(self):
        return self._c

rng = random.Random(1)
for out in sorted(d.glob(f"{tag}_b3a*.gs2.out")):
    name = out.name[:-len(".gs2.out")]
    states = []
    for line in open(out):
        if line.startswith("STATE "):
            a = list(map(int, line.split()[1:]))
            states.append((a[0], a[1], a[2:]))
        elif line.startswith("BEST"):
            pass
    if not states:
        continue
    I = Inst2(d / f"{name}.txt", d / f"{name}.json")
    states.sort(key=lambda s: (-s[1], -s[0]))
    best = 0
    for L, IL, E in states[:30]:
        if L < need:
            continue
        planes = all_planes(I, E)
        nu = parity_rank([plane_vectors(I, p, I.m) for p in planes], rng)
        best = max(best, nu)
        if nu >= need:
            print(f"{name}: state L={L} greedy IL={IL} has EXACT parity {nu} with {len(planes)} lines")
            break
    print(f"{name}: best exact parity among L>={need} states: {best}", flush=True)

# Chip order from beam.exe (see beam.cpp); same interface as greedy_order.reorder.
import subprocess, os
from gf2 import Ech

HERE = os.path.dirname(os.path.abspath(__file__))


def reorder(B, order, head, seed, width=int(os.environ.get('BEAMW', '60'))):
    F = Ech([v for v, _ in B.free] + list(B.keep_always))
    piv = sorted(F.piv.items(), reverse=True)

    def red(v):
        for h, p in piv:
            if (v >> h) & 1:
                v ^= p
        return v

    def words(v):
        assert v < (1 << 192)
        m = (1 << 64) - 1
        return f'{v & m} {(v >> 64) & m} {(v >> 128) & m}'

    L = [red(v) for v, _ in B.L_elems()]
    C = Ech([v for v in L if v])
    for i in order[:head]:
        for j in (2 * i, 2 * i + 1):
            C.add(red(B.zrows[j]))
    base = [p for p in C.piv.values()]
    last = getattr(B, 'last_count', 0)
    todo = order[head:]
    nfirst = len(todo) - last
    cap = B.capacity() - F.n
    txt = [f'{len(base)} {len(todo)} {cap} {width} {nfirst}']
    txt += [words(v) for v in base]
    for i in todo:
        txt += [words(red(B.zrows[2 * i])), words(red(B.zrows[2 * i + 1]))]
    out = subprocess.run([os.path.join(HERE, 'beam.exe')], input='\n'.join(txt), capture_output=True, text=True,
                         check=True).stdout.split()
    excess, peak = int(out[0]), int(out[1])
    idx = [int(x) for x in out[2:]]
    print(f'  beam order: excess {excess} peak {peak + F.n} (capacity {B.capacity()})', flush=True)
    return order[:head] + [todo[i] for i in idx]

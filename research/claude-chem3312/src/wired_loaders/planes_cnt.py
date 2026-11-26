from planes import *
import json, sys
def load_inst(d, tag, m):
    md = json.load(open(f'{d}/{tag}.json'))
    lines = open(f'{d}/{tag}.txt').read().split('\n')
    q, w, nf, k = map(int, lines[0].split())
    class I: pass
    I = I(); I.q = q; I.w = w; I.m = m
    cols = {}
    for ln in lines[1:1 + nf]:
        a = list(map(int, ln.split())); cols[a[0]] = a[1:]
    I.columns = lambda: cols
    I.zeta = md.get('zeta13') if w == 12 else None
    I.piv = I.zeta.bit_length() - 1 if I.zeta else None
    I.keep = [t for t in range(13) if t != I.piv]
    return I
if __name__ == "__main__":
    d = sys.argv[1]; tag = sys.argv[2]
    for blk, m, res in [(1, 7, f'{tag}_b1_s1.res'), (2, 8, f'{tag}_b2.res')]:
        I = load_inst(d, f'{tag}_b{blk}', m)
        for nu, E in read_E(f'{d}/{res}')[:6]:
            pl = all_planes(I, E)
            print(res, 'nu', nu, 'planes', len(pl), 'fanouts', len(set(p[0] for p in pl)))

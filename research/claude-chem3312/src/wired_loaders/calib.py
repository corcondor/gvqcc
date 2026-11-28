"""Calibration instances only (not circuit targets): our table's slices with one low coordinate dropped."""
from inst import *
T = Target(14)
def calib(names, drop, kk, tag):
    mats = combo_mats(T, wires(*names))
    sl = block_slices_from_mixed(mats)
    m = len(names)
    if drop is not None:
        keep = [t for t in range(13) if t != drop]
        sl2 = []
        for s in sl:
            v = 0
            for o in range(m):
                row = (s >> (13 * o)) & 0x1FFF
                row &= ~(1 << drop)
                v |= row << (13 * o)
            sl2.append(v)
        I = Instance(sl2, m, zeta=1 << drop)
    else:
        I = Instance(sl, m)
    n, md = I.write(tag, kk, meta={"calibration_only": True}, outdir=Path("tmp"))
    print(tag, I.q, I.w, I.m, I.rankR, "n", n)
S7 = ['s2b1','s2b2','s2b3','s2b4','s2b5','s3b2','s3b3']
S8 = S7 + ['s3b4']
calib(S7, None, 1, 'c_7x13_38')
calib(S7, 5, 1, 'c_7x12_38')
calib(S8, 5, 9, 'c_8x12_42')
calib(S8, 5, 11, 'c_8x12_43')
calib(S8, 5, 7, 'c_8x12_41')

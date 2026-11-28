from inst import *
T = Target(14)
S9 = ['s2b1','s2b2','s2b3','s2b4','s2b5','s3b2','s3b3','s3b4','s3b5']
mats = combo_mats(T, wires(*S9))
sl = block_slices_from_mixed(mats)
drop = 5
sl2 = []
for s in sl:
    v = 0
    for o in range(9):
        row = (s >> (13*o)) & 0x1FFF
        row &= ~(1 << drop)
        v |= row << (13*o)
    sl2.append(v)
I = Instance(sl2, 9, zeta=1 << drop)
write_gs2(I, "tmp/c_9x12.gs2")
print(I.m, I.w, I.q, I.rankR)

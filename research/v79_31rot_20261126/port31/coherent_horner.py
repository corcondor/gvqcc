"""Connect the V61 odd-product ABI to an exact coherent first-Horner chart.

This is a native 36-qubit arithmetic integration, not the full invsqrt oracle.
The 21-bit chart retains rounding information; no measurement discards it.
Two independently generated constant-add decompositions are compiled and replayed.
"""
from pathlib import Path
import sys, json, time, hashlib, itertools
from collections import Counter
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "v61_sources"))
from emit_meet import NativeKMB, Op, pack, replay, N, tag
from normalize import mcx

SRC = ROOT / "v61_sources"
MODEL = np.load(SRC / "pr141/repaired_k12.npz")
C = MODEL["C"]
M = (C[:, 4] >> 14).astype(np.int64)
BASE = C[:, 3] // 32
ODD = np.array([int(m) // (int(m) & -int(m)) if m else 1 for m in M])
SHIFT = np.array([3 - ((int(m) & -int(m)).bit_length() - 1) if m else 0 for m in M])
CONSTANT = np.array([
    int(BASE[a]) * (1 << int(SHIFT[a]))
    + ((int(m)//2+4) >> (3-int(SHIFT[a]))) if m else 0
    for a, m in enumerate(M)
], np.int64)
WORD = list(range(5, 17)) + list(range(27, 31)) + [26, 31, 32, 33, 34]
FLAG = 35
WIDTH = len(WORD)
MOD = 1 << WIDTH


def naf(n):
    """Exact signed powers of two; residues beyond the word are immaterial."""
    out = []
    sign = -1 if n < 0 else 1
    n = abs(int(n)); j = 0
    while n:
        if n & 1:
            d = 2 - n % 4
            if j < WIDTH: out.append((j, sign*d))
            n -= d
        n //= 2; j += 1
    return out


def increment(bit, sign):
    # Descending controls are tested before lower word bits are toggled.
    ops = []
    if sign < 0:
        ops += [Op(17, (q,)) for q in WORD[bit:]]
    for j in range(WIDTH-1, bit, -1):
        ops += mcx([FLAG] + WORD[bit:j], WORD[j], 36)
    ops.append(Op(33, (FLAG, WORD[bit])))
    if sign < 0:
        ops += [Op(17, (q,)) for q in reversed(WORD[bit:])]
    return ops


def cube_table():
    best = {}
    for pat in itertools.product((-1, 0, 1), repeat=5):
        mask = sum(1 << a for a in range(24)
                   if all(v < 0 or (((a+8) >> j)&1) == v
                          for j, v in enumerate(pat)))
        if not mask: continue
        cs = [17+j for j,v in enumerate(pat) if v >= 0]
        neg = [Op(17, (17+j,)) for j,v in enumerate(pat) if v == 0]
        ops = neg + mcx(cs, FLAG, 36) + list(reversed(neg))
        score = (sum(o.raw == 49 for o in ops), len(ops), pat)
        if mask not in best or score < best[mask][0]: best[mask] = (score, ops)
    return best


CUBES = cube_table()
PAIRS = {0: ((0,0), [])}
for a, (sa, oa) in CUBES.items():
    for b, (sb, ob) in CUBES.items():
        z = a ^ b; sc = (sa[0]+sb[0], sa[1]+sb[1])
        if z not in PAIRS or sc < PAIRS[z][0]: PAIRS[z] = (sc, oa+ob)


def flag_ops(mask):
    if not mask: return []
    opts = []
    if mask in CUBES: opts.append((CUBES[mask][0][:2], CUBES[mask][1]))
    if mask in PAIRS: opts.append(PAIRS[mask])
    for a, (sc, ops) in CUBES.items():
        if mask ^ a in PAIRS:
            s, o = PAIRS[mask ^ a]
            opts.append(((sc[0]+s[0],sc[1]+s[1]),ops+o))
    if not opts:
        o = sum((CUBES[1 << a][1] for a in range(24) if (mask >> a)&1), [])
        opts.append(((sum(v.raw == 49 for v in o),len(o)),o))
    return min(opts,key=lambda p:p[0])[1]


def compile_adder(mode):
    groups = []
    if mode == "address_naf":
        for a, k in enumerate(CONSTANT):
            if k: groups.append((1 << a, naf(int(k))))
    elif mode == "shared_signed_digits":
        by = {}
        for a, k in enumerate(CONSTANT):
            for j, d in naf(int(k)): by[j,d] = by.get((j,d),0) | (1 << a)
        groups = [(mask,[(j,d)]) for (j,d),mask in sorted(by.items(),reverse=True)]
    else: raise ValueError(mode)
    # Transport the Boolean flag itself by its exact finite difference.
    old = 0; ops = []; witness = []
    for mask, digits in groups:
        delta = flag_ops(old ^ mask); ops += delta
        for j,d in digits: ops += increment(j,d)
        witness.append({"mask":mask,"digits":digits,"transport_ccx":sum(o.raw==49 for o in delta)})
        old = mask
    ops += flag_ops(old)
    return ops, witness


def commute_cancel(ops, window=512):
    """Cancel involutions only across gates with an exact commutation test."""
    result=[]; removed=0
    for o in ops:
        assert o.raw in (17,33,49)
        ct=set(o.wires[:-1]); t=o.wires[-1]; match=None
        for k in range(len(result)-1,max(-1,len(result)-1-window),-1):
            old=result[k]
            if old is None:continue
            if old==o:match=k;break
            oc=set(old.wires[:-1]); ot=old.wires[-1]
            if t in oc or ot in ct:break
        if match is None:result.append(o)
        else:result[match]=None;removed+=2
    return [o for o in result if o is not None],removed


def verify_whole(circuit, snapshot, original_snapshot):
    x = np.arange(1,N+1,dtype=np.uint32)
    e = np.zeros(N,np.uint32)
    for j in range(1,11): e[x >= 1 << (2*j)] = j
    shift = 10-e; U = x << (2*shift); addr = (U >> 17)-8; T = (U >> 5)&4095
    P = ODD[addr]*T
    A = P + CONSTANT[addr]
    encoded = A & (MOD-1)
    expected_v3 = BASE[addr] + ((M[addr]*T + M[addr]//2 + 4) >> 3)
    decoded = np.where(M[addr] == 0, BASE[addr], A >> SHIFT[addr])
    assert np.array_equal(decoded,expected_v3)
    assert A.min() >= -(1 << (WIDTH-1)) and A.max() < (1 << (WIDTH-1))
    one = (1 << N)-1
    s = [pack((x >> j)&1) for j in range(22)] + [0]*14
    orig = s[:]; checks = 0
    def cb(i,s,ph):
        nonlocal checks
        if i == original_snapshot:
            assert [s[q] for q in WORD[:16]] == [pack((P >> j)&1) for j in range(16)]
            assert not any(s[q] for q in WORD[16:]+[FLAG]) and not ph
            checks += 1
        if i == snapshot:
            assert [s[q] for q in WORD] == [pack((encoded >> j)&1) for j in range(WIDTH)]
            assert s[FLAG] == 0 and not ph
            # Independent ABI decoder: only physical word + retained address.
            act = np.zeros(N,np.int64)
            for j,q in enumerate(WORD):
                bits = np.unpackbits(np.frombuffer(s[q].to_bytes((N+7)//8,"little"),np.uint8),bitorder="little")[:N]
                act |= bits.astype(np.int64) << j
            act = np.where(act & (1 << (WIDTH-1)),act-MOD,act)
            da = np.zeros(N,np.uint32)
            for j,q in enumerate(range(17,22)):
                bits = np.unpackbits(np.frombuffer(s[q].to_bytes((N+7)//8,"little"),np.uint8),bitorder="little")[:N]
                da |= bits.astype(np.uint32) << j
            da -= 8
            result = np.where(M[da] == 0,BASE[da],act >> SHIFT[da])
            assert np.array_equal(result,expected_v3)
            # Full inverse recovers old odd product including dropped low bits.
            assert np.array_equal(act-CONSTANT[da],P)
            checks += 1
    replay(circuit.ops,s,one,cb)
    assert s == orig and checks == 2
    return {"legal_inputs":N,"serialized_native_replay":"PASS","encoded_Horner_word":"PASS",
            "decoder_uses_physical_word_and_retained_address":"PASS","rounding_residue_retained":"PASS",
            "all_independent_HMR_phase_coefficients":"PASS","all_input_and_work_restoration":"PASS",
            "decoded_word_sha256":hashlib.sha256(expected_v3.astype("<i8").tobytes()).hexdigest(),
            "encoding_signed_min":int(A.min()),"encoding_signed_max":int(A.max())}


def main(modes=("address_naf","shared_signed_digits","shared_signed_digits_commute"),suffix=""):
    t0=time.time();base=NativeKMB.read(SRC/"v61_pipeline_p1_r1_Q36_PARTIAL.kmb")
    meta=json.loads((SRC/"v61_pipeline_p1_r1_receipt.json").read_text());old_snapshot=meta["snapshot"]
    rows=[]
    for mode in modes:
        adder,witness=compile_adder(mode.removesuffix("_commute"))
        oldlen=len(adder)
        if mode.endswith("_commute"):
            for _ in range(8):
                adder,removed=commute_cancel(adder)
                if not removed:break
        mode += suffix
        ops=base.ops[:old_snapshot]+adder+list(reversed(adder))+base.ops[old_snapshot:]
        circ=NativeKMB(base.prefix16,base.header,base.sections,ops)
        out=ROOT/("coherent_first_horner_"+mode+"_Q36_PARTIAL.kmb")
        out.write_bytes(circ.to_bytes());circ=NativeKMB.read(out)
        stats=Counter(o.raw for o in circ.ops)
        rec={"variant":mode,"scope":"coherent first normalized Horner stage chart only; not full invsqrt or final31R oracle",
             "Q":36,"word_qubits":WORD,"word_width":WIDTH,"flag_qubit":FLAG,
             "constants":CONSTANT.tolist(),"shifts":SHIFT.tolist(),"zero_coefficient_chart":"keeps T; decoder returns C3/32",
             "snapshot":old_snapshot+len(adder),"original_snapshot":old_snapshot,
             "ccx":stats[49],"expected_paid":stats[49]+0.5*stats[176],"instructions":len(ops),
             "hmr":stats[80],"rotations":stats[19],"forward_connector_ccx":sum(o.raw==49 for o in adder),
             "forward_connector_instructions":len(adder),"groups":witness,"removed_instructions":oldlen-len(adder),"sha256":hashlib.sha256(out.read_bytes()).hexdigest()}
        print("EMITTED",mode,{k:rec[k] for k in ("ccx","instructions","forward_connector_ccx")},flush=True)
        rec["verification"]=verify_whole(circ,rec["snapshot"],old_snapshot)
        try:
            import kickmix as km
        except ImportError:
            rec["official_kickmix_binary_parser"]="not available in this regeneration run"
        else:
            km.Circuit.from_file(str(out))
            rec["official_kickmix_binary_parser"]="PASS (binary parser only; not full oracle score)"
        rec["seconds_total"]=time.time()-t0;rows.append(rec)
        (ROOT/("coherent_first_horner_"+mode+"_receipt.json")).write_text(json.dumps(rec,indent=2))
        print("PASS",mode,rec["verification"],flush=True)
    (ROOT/("coherent_horner_comparison"+suffix+".json")).write_text(json.dumps(rows,indent=2))

if __name__ == "__main__":main()

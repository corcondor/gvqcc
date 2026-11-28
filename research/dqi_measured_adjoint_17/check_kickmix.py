"""Native KickMix comparison in exact normalized input/output coordinates.
These are the two distinct extracted tensors, not the full 900Q tape.
The 101-product chart occurs once and the 67-product chart 16 times.
"""
import json
from pathlib import Path
import numpy as np
import kickmix as km
DATA67 = "1,2,1,287;4,8,2,c2c;10,20,4,77b;40,80,8,42d;100,200,10,ff8;400,800,20,460;5de,ba7,40,7ae;a79,7a7,80,815;fa7,9de,100,805;7ba,a5f,200,59f;986,f4b,400,390;c92,8f1,800,b8d;b28,e3c,5ba,19;7c2,d41,f96,93d;cd4,87c,92f,a15;b16,53d,848,80e;9e9,fbe,b33,324;1000,2000,1000,0;2003,3001,2000,0;4000,8000,4000,0;800c,c004,8000,0;10000,20000,10000,0;20030,30010,20000,0;40000,80000,40000,0;c0080,400c0,80000,0;100000,200000,100000,0;300200,100300,200000,0;400000,800000,400000,0;eaeb70,577ed0,800000,0;6aecd7,fd987e,5e5000,0;d772d0,aae370,39f000,0;1770a9,2ae0d7,a7a000,0;69b121,96d332,4f2000,0;745ec3,aca581,58d000,0;8b3421,4e2c13,295000,0;b1403c,e28014,e41000,0;2790d7,3a707e,dab000,0;9c1e03,643b02,72d000,0;cd4000,87c000,474000,0;b2a03c,515028,1ae000,0;d69480,7fe840,edd000,0;3561a9,1bd2d7,c2a000,0;1000000,2000000,1877,0;2000003,3000001,2876,0;4000000,8000000,4e27,0;800000c,c000004,8e25,0;10000000,20000000,103f5,0;20000030,30000010,203f1,0;40000000,80000000,4030e,0;c0000080,400000c0,80306,0;100000000,200000000,100509,0;300000200,100000300,200519,0;400000000,800000000,4001c0,0;eae000b70,577000ed0,8001a0,0;6ae000cd7,fd900087e,5e5160,0;d770002d0,aae000370,39f0e0,0;1770000a9,2ae0000d7,a7a1e0,0;69b000121,96d000332,4f29ba,0;745000ec3,aca000581,58dfba,0;8b3000421,4e2000c13,2953ba,0;b1400003c,e28000014,e41e00,0;2790000d7,3a700007e,dabbba,0;9c1000e03,643000b02,72da54,0;cd4000000,87c000000,474ced,0;b2a00003c,515000028,1aed8a,0;d69000480,7fe000840,eddef1,0;3560001a9,1bd0002d7,c2a5c2,0"
DATA101 = "1,2,1,0;4,8,2,0;10,20,4,0;40,80,8,0;100,200,10,0;400,800,20,0;5de,ba7,40,0;a79,7a7,80,0;fa7,9de,100,0;7ba,a5f,200,0;986,f4b,400,0;c92,8f1,800,0;b28,e3c,5ba,0;7c2,d41,f96,0;cd4,87c,92f,0;b16,53d,848,0;9e9,fbe,b33,0;1000,2000,1000,0;4000,8000,2000,0;10000,20000,4000,0;40000,80000,8000,0;100000,200000,10000,0;400000,800000,20000,0;5de000,ba7000,40000,0;a79000,7a7000,80000,0;fa7000,9de000,100000,0;7ba000,a5f000,200000,0;986000,f4b000,400000,0;c92000,8f1000,800000,0;b28000,e3c000,5ba000,0;7c2000,d41000,f96000,0;cd4000,87c000,92f000,0;b16000,53d000,848000,0;9e9000,fbe000,b33000,0;1000000,2000000,1000000,287;4000000,8000000,2000000,c2c;10000000,20000000,4000000,77b;40000000,80000000,8000000,42d;100000000,200000000,10000000,ff8;400000000,800000000,20000000,460;5de000000,ba7000000,40000000,7ae;a79000000,7a7000000,80000000,815;fa7000000,9de000000,100000000,805;7ba000000,a5f000000,200000000,59f;986000000,f4b000000,400000000,390;c92000000,8f1000000,800000000,b8d;b28000000,e3c000000,5ba000000,19;7c2000000,d41000000,f96000000,93d;cd4000000,87c000000,92f000000,a15;b16000000,53d000000,848000000,80e;9e9000000,fbe000000,b33000000,324;1000002,2000001,1000000000,0;1000001,2000003,2000000000,0;4000004,800000c,4000000000,0;400000c,8000008,8000000000,0;10000010,20000030,10000000000,0;10000030,20000020,20000000000,0;40000080,80000040,40000000000,0;400000c0,80000080,80000000000,0;100000300,200000200,100000000000,0;100000100,200000300,200000000000,0;400000800,800000400,400000000000,0;5de000e79,ba7000ba7,800000000000,0;a79000a79,7a7000dde,5e5000000000,0;fa7000fa7,9de000679,39f000000000,0;1de0003a7,279000279,a7a000000000,0;7ba000a5f,a5f0007ba,4f2000000000,0;986000986,f4b0006cd,58d000000000,0;c92000463,8f10008f1,295000000000,0;b28000514,e3c000e3c,e41000000000,0;2ae0002ae,3d9000177,dab000000000,0;7c20007c2,d41000a83,72d000000000,0;cd4000cd4,87c0004a8,474000000000,0;b1600053d,53d000b16,1ae000000000,0;9e9000fbe,fbe0009e9,edd000000000,0;2ff000195,36a00036a,c2a000000000,0;1002000,2001000,1877000000,0;1001000,2003000,2876000000,0;4004000,800c000,4e27000000,0;400c000,8008000,8e25000000,0;10010000,20030000,103f5000000,0;10030000,20020000,203f1000000,0;40080000,80040000,4030e000000,0;400c0000,80080000,80306000000,0;100300000,200200000,100509000000,0;100100000,200300000,200519000000,0;400800000,800400000,4001c0000000,0;5dee79000,ba7ba7000,8001a0000000,0;a79a79000,7a7dde000,5e5160000000,0;fa7fa7000,9de679000,39f0e0000000,0;1de3a7000,279279000,a7a1e0000000,0;7baa5f000,a5f7ba000,4f29ba000000,0;986986000,f4b6cd000,58dfba000000,0;c92463000,8f18f1000,2953ba000000,0;b28514000,e3ce3c000,e41e00000000,0;2ae2ae000,3d9177000,dabbba000000,0;7c27c2000,d41a83000,72da54000000,0;cd4cd4000,87c4a8000,474ced000000,0;b1653d000,53db16000,1aed8a000000,0;9e9fbe000,fbe9e9000,eddef1000000,0;2ff195000,36a36a000,c2a5c2000000,0"
def parse(s):
    return [tuple(int(x,16) for x in row.split(",")) for row in s.split(";")]
def bits(x):
    while x:
        y=x&-x
        yield y.bit_length()-1
        x^=y
def build(terms, m, adjoint):
    cb=km.CircuitBuilder()
    n=36+m+12
    cb.set_max_qubits(n)
    q=list(cb.create_quantum_register(n,'W'))
    mb=list(cb.alloc_bits(12))
    scratch=list(cb.alloc_bits(1))[0]
    def measure():
        cb.hmr(q[36+m:],mb)
    if adjoint:
        measure()
    for a,b,d,h in terms:
        p=next(bits(a))
        same=bool(b>>p&1)
        bb=b^a if same else b
        z=next(bits(bb))
        assert z!=p
        pre=[(q[j],q[p]) for j in bits(a^(1<<p))]
        pre += [(q[j],q[z]) for j in bits(bb^(1<<z))]
        if same:
            pre.append((q[p],q[z]))
        for u,v in pre:
            cb.cx(u,v)
        target=d if adjoint else d|(h<<m)
        if target:
            k=next(bits(target))
            fan=[(q[36+k],q[36+j]) for j in bits(target^(1<<k))]
            for u,v in fan: cb.cx(u,v)
            cb.ccx(q[p],q[z],q[36+k])
            for u,v in reversed(fan): cb.cx(u,v)
        if adjoint and h:
            cb.bit_store(scratch,False)
            for j in bits(h): cb.cx(mb[j],scratch)
            cb.ccz(q[p],q[z],scratch)
            cb.bit_store(scratch,False)
        for u,v in reversed(pre): cb.cx(u,v)
    if not adjoint:
        measure()
    cb.free([scratch])
    return cb.finish_circuit()
def check(data,m,sites):
    terms=parse(data)
    assert len(terms) in (67,101)
    assert sum(h!=0 for _,_,_,h in terms)==17
    n=36+m+12
    old=build(terms,m,False)
    new=build(terms,m,True)
    old.to_file(f"old{len(terms)}.kmb",format="kmb")
    new.to_file(f"new{len(terms)}.kmb",format="kmb")
    old=km.Circuit.from_file(f"old{len(terms)}.kmb")
    new=km.Circuit.from_file(f"new{len(terms)}.kmb")
    assert int(old.operation_statistics().num_toffoli_like)==len(terms)
    assert int(new.operation_statistics().num_toffoli_like)==len(terms)
    rng=np.random.default_rng(329)
    qs=km.array([km.q(i) for i in range(n)])
    for i in range(sites):
        for j in range(16):
            x=rng.integers(0,2,size=(n,64),dtype=np.uint8).astype(bool)
            results=[]
            for c in [old,new]:
                sim=km.Simulator(batch_size=64,seed=74123+i*101+j,debug_print=False,counting_operations=True)
                sim.use_same_registers_as(c)
                sim.write_across_shots(qs,x)
                sim.do(c)
                results.append((sim.read_across_shots(qs),sim.read_phase_flipped_across_shots()))
            assert np.array_equal(results[0][0],results[1][0]),("state",i,j)
            assert np.array_equal(results[0][1],results[1][1]),("phase",i,j)
    return dict(products=len(terms), sites=sites, Q=n, paired_shots=sites*1024,paid_old=len(terms),paid_new=len(terms),errors=0)
if __name__=="__main__":
    out=[check(DATA101,48,1),check(DATA67,24,16)]
    print(json.dumps(out,indent=2),flush=True)
    Path("receipt.json").write_text(json.dumps(out,indent=2))

import json
import pathlib
import numpy as np
import kickmix as k

d = pathlib.Path(__file__).parent
g = json.loads((d/'gates.json').read_text())
def line(op, *a):
    return op+' '+' '.join('q'+str(x) for x in a)
full = [line({49:'CCX',33:'CX',34:'SWAP'}[o],*( [a,b,t] if o==49 else [a,b])) for o,a,b,t in g['orig']]
quot = [line({'C':'CX','T':'CCX','S':'SWAP'}[o],*a) for o,*a in g['comp']]
cf = k.Circuit('\n'.join(full+['HMR q10 b0']))
cq = k.Circuit('\n'.join(['Z q0 if b0','Z q3 if b0']+quot))
def ser(c,name):
    p = str(d/(name+'.kmb'))
    c.to_file(p)
    return k.Circuit.from_file(p)
cf,cq = ser(cf,'block_full'),ser(cq,'block_quot')
cs = ser(k.Circuit('HMR q0 b0'),'outcome')
q14,q13 = [k.q(i) for i in range(14)],[k.q(i) for i in range(13)]
s = k.Simulator(batch_size=256,seed=961)
t = k.Simulator(batch_size=256,seed=961)
p = k.Simulator(batch_size=256,seed=55)
m=k.b(0)
uses=[0,0]
for i in range(0,8192,128):
    x0 = np.arange(i,i+128)
    x = np.tile(x0,2)
    u = ((x[None,:]>>np.arange(13)[:,None])&1).astype(bool)
    v = np.insert(u,10,False,axis=0)
    s.clear_for_shot()
    s.write_across_shots(q14,v)
    s.do(cf)
    r = s.read_across_shots(m)
    w = s.read_across_shots(q14)
    base = u[0]^u[3]
    assert not w[10].any()
    assert np.all(s.read_phase_flipped_across_shots()==(r&base))
    # Cover both outcomes on every input by driving relocated phase with a supplied bit.
    for b in (r,~r):
        t.clear_for_shot()
        t.write_across_shots(q13,u)
        t.write_across_shots(m,b)
        t.do(cq)
        assert np.all(t.read_across_shots(m)==b)
        w2 = np.delete(w,10,axis=0) ^ (base[None,:]&(((2632>>np.arange(13))&1)[:,None].astype(bool)))
        assert np.array_equal(t.read_across_shots(q13),w2)
        assert np.array_equal(t.read_phase_flipped_across_shots(),b&base)
    p.clear_for_shot()
    p.do(cs)
    z=p.read_across_shots(m)
    assert not p.read_phase_flipped_across_shots().any()
    uses[0]+=int(np.count_nonzero(~z))
    uses[1]+=int(np.count_nonzero(z))
print('all 8192 inputs and both HMR outcomes match native restored phase and projected values; widths:',cf.num_qubits,cq.num_qubits,'clean presample outcomes',uses)

# Extend through the actual successor operations 41,425,268..41,425,652.
# No quantum-value observer sees the difference, and precisely one Z
# reads a direction component on the identical first HMR result.
seam = [list(map(int,s.split())) for s in (d/'seam.tsv').read_text().splitlines()]
actual = {}
for (_,o,a,b,t,*_), (oo,aa,bb,tt) in zip(seam,g['orig']):
    assert o==oo
    for phys,loc in zip((a,b,t) if o==49 else (a,b),(aa,bb,tt) if o==49 else (aa,bb)):
        assert actual.setdefault(loc,phys)==phys
assert len(actual)==14 and actual[10]==340
tail = [list(map(int,s.split())) for s in (d/'after.tsv').read_text().splitlines()]
assert tail[0][:6]==[41425267,80,340,0,0,49612]
tail = [r for r in tail if 41425268 <= r[0] < 41425653]
assert len(tail)==385
external = sorted({q for i,o,a,b,t,z,c in tail for q in ((a,b) if o&48==32 else (a,))}-set(actual.values()))
fm = {p:i for i,p in actual.items()} | {p:i for i,p in enumerate(external,14)}
cm = {p:(i-(i>10)) for p,i in fm.items() if i!=10}
delta = {46,104,294,631}
hits=[]
for i,o,a,b,t,z,c in tail:
    if o==33 and a in delta:
        delta.symmetric_difference_update({b})
    elif o==34 and ((a in delta)!=(b in delta)):
        delta.symmetric_difference_update({a,b})
    elif o==144 and a in delta:
        assert c==49612
        hits.append(i)
    elif o==160:
        assert not delta.intersection({a,b})
    assert o in {33,34,144,160}
assert hits==[41425649]
def translate(qmap, r):
    i,o,a,b,t,z,c=r
    s=line({33:'CX',34:'SWAP',144:'Z',160:'CZ'}[o],*( (qmap[a],qmap[b]) if o&48==32 else (qmap[a],)))
    return s + (' if b0' if o&128 else '')
caps = len(fm)
assert delta=={46,104,294,631}
full_readout = ser(k.Circuit('\n'.join(full+['HMR q10 b0']+[translate(fm,r) for r in tail])),'through_full')
quot_readout = ser(k.Circuit('\n'.join(quot+[translate(cm,r) for r in tail])),'through_quot')
S = k.Simulator(batch_size=256,seed=516)
T = k.Simulator(batch_size=256,seed=718)
rng=np.random.default_rng(908)
for i in range(0,8192,128):
    x = np.tile(np.arange(i,i+128),2)
    u = ((x[None,:]>>np.arange(13)[:,None])&1).astype(bool)
    env=rng.integers(0,2,size=(len(external),256),dtype=np.uint8).astype(bool)
    qf=[k.q(j) for j in range(caps)]
    qc=[k.q(j) for j in range(caps-1)]
    S.clear_for_shot(); T.clear_for_shot()
    S.write_across_shots(qf,np.vstack((np.insert(u,10,False,axis=0),env)))
    S.do(full_readout)
    T.write_across_shots(qc,np.vstack((u,env)))
    T.write_across_shots(m,S.read_across_shots(m))
    T.do(quot_readout)
    ref = np.delete(S.read_across_shots(qf),10,axis=0)
    ref[[cm[q] for q in sorted(delta)]] ^= u[0]^u[3]
    assert np.array_equal(ref,T.read_across_shots(qc))
    assert np.array_equal(S.read_phase_flipped_across_shots(),T.read_phase_flipped_across_shots())
print('native successor 385 ops verified, old HMR phase cancels conditional Z46; projected frame retained at',full_readout.num_qubits,quot_readout.num_qubits)

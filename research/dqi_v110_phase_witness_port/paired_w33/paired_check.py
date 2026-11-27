import sys, json, hashlib
from pathlib import Path
import numpy as np
import kickmix as km
from dqi import verify_submission_dqi as V

def mul(a,b):
    acc=0
    while b:
        if b&1: acc ^= a
        b>>=1;a<<=1
        if a&4096:a^=0x1053
    return acc

def he(n): return hashlib.sha256(n).hexdigest()
def bits_to_words(y):
    return (y.T.reshape(y.shape[1],-1,12).astype(np.uint16) * (1<<np.arange(12,dtype=np.uint16))).sum(-1)
def count(a): return int(np.count_nonzero(a))
f=json.loads(Path(sys.argv[1]).read_text())
phased=Path(sys.argv[2]);original=Path(sys.argv[3])
assert hashlib.file_digest(original.open('rb'),'sha256').hexdigest()=='8010980d566e6b16d255bfa7f00b37fb0d00c62978cd8bd3932b1981adc05841'
archived=next(x for x in f['native_rows'] if x['circuit']=='V110 Extended')
mags=dict(zip(f['error_indices'],f['error_values']))
pos=list(mags)+[j for j in [0,1,2,3,4,5,128,255,1024,2048,3000,4094] if j not in mags]
n=len(pos)*12; seed=3011
I=V.to_bits(np.repeat(np.array(archived['input'])[None,:],n,axis=0),12)
m=np.zeros((n,4095),dtype=np.int64)
for i,k in enumerate(pos):m[i*12:(i+1)*12,k]=1<<np.arange(12)
M=V.to_bits(m,12); empty=np.zeros_like(M)
b0,h=map(int,Path('layout.txt').read_text().split())
def run(path):
    c=km.Circuit.from_file(str(path));q,b,anc=V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance());Path('qids.txt').write_text(' '.join(str(i)[1:] for i in q));Path('bids.txt').write_text(' '.join(str(i)[1:] for i in b));q,b=km.array(q),km.array(b)
    obs=[]
    for m in [empty,M]:
        s=km.Simulator(batch_size=n,seed=seed);s.use_same_registers_as(c)
        s.write_across_shots(q,I);s.write_across_shots(b,m);s.do(c)
        row=dict(phase=np.asarray(s.read_phase_flipped_across_shots()),output=s.read_across_shots(q))
        assert np.array_equal(s.read_across_shots(b),m) and not s.read_across_shots(anc).any()
        if path==phased:
            row['raw']=np.concatenate([np.packbits(s.read_across_shots(km.array([km.b(i) for i in range(b0+lo,b0+min(2*h,lo+8192))])),axis=1,bitorder='little') for lo in range(0,2*h,8192)])
        obs.append(row)
    return obs
plain=run(original); paired=run(phased)
for old,new in zip(plain,paired):
    for k in ('phase','output'): np.testing.assert_equal(old[k],new[k])
v,z=paired
for i,row in enumerate((v,z)):
    row['raw'].tofile(f'mask_{i}.raw')
    np.packbits(row['phase'],bitorder='little').tofile(f'phase_{i}.raw')
np.packbits(I.T[0],bitorder='little').tofile('input.raw')
Path('probe_order.txt').write_text(' '.join(map(str,pos)))
print('activation_bit_diffs',count(np.unpackbits(v['raw'][0::2]^z['raw'][0::2],axis=1)),file=sys.stderr)
print('outcome_diffs_both_active',count(np.unpackbits((v['raw'][1::2]^z['raw'][1::2]) & v['raw'][0::2] & z['raw'][0::2],axis=1)),file=sys.stderr)

words=bits_to_words(v['output'])
np.testing.assert_equal(words,np.repeat(np.array(archived['output'])[None,:],n,axis=0))
np.testing.assert_equal(v['output'],z['output'])
r=[int(x)^int(y) for x,y in zip(archived['input'],words[0])]
assert sum(x.bit_count() for x in r)==423 and r==archived['residual']
a=mul(3519,3519); assert a==2890
for x in range(4096):
    xx=mul(x,x);assert mul(xx,xx)^xx^a
assert all(r[i+4]^r[i+2]^mul(a,r[i])==0 for i in range(66))
phase_words=bits_to_words((v['phase']^z['phase']).reshape(-1,1)).ravel()
obs={k:int(x) for k,x in zip(pos,phase_words) if x}
assert {k:x for k,x in obs.items() if k in mags}=={2610:1233,501:2450}
expected=np.array([mags.get(k,0) for k in pos],dtype=np.int64)
print(json.dumps(dict(seed=seed,pairs=n,measurement_sites=h,mismatching_activation=count(np.unpackbits(v['raw'][0::2]^z['raw'][0::2])),mismatching_draws=count(np.unpackbits(v['raw'][1::2]^z['raw'][1::2])),mismatching_draws_both_active=count(np.unpackbits((v['raw'][1::2]^z['raw'][1::2]) & v['raw'][0::2] & z['raw'][0::2])),active_sha256=he(v['raw'][0::2].tobytes()),outcome_sha256=he(v['raw'][1::2].tobytes()),resident_matches=True,restoration_error_bits=423,annihilator=[2890,0,1,0,1],recurrence_equations=66,field_roots=0,phase_words_nonzero=obs,phase_error_bits=sum(int(x).bit_count() for x in expected^phase_words.astype(np.int64))),indent=2))

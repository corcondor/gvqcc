#!/usr/bin/env python3
"""Independent finite truth tables and native checks for discovery fingerprints.

This never rewrites a submitted circuit.  Scanner positives must match exact
Boolean truth tables on these small fixtures.  A false same_guard flag is only
an absence of a fingerprint equality proof, not proof of unequal predicates.
"""
import itertools,json,pathlib,subprocess,hashlib
import numpy as np
import kickmix as km

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'dqi_next_conditional_phase_fixture_data'

def fixture(name,body,must=(),counts=None,measure_bits=()):
    return {'name':name,'body':body.strip().splitlines(),'must':list(must),'counts':counts,'measure_bits':list(measure_bits)}

FIXTURES=[]
for op in ['X q0','CX q0 q1','SWAP q0 q1','CSWAP q3 q0 q1','CCX q0 q1 q2']:
    FIXTURES.append(fixture('roundtrip_'+op.split()[0].lower(),f'''CCZ q0 q1 q2
{op} if b0
CCZ q0 q1 q2
{op} if b0
CCZ q0 q1 q2''',must=[(0,4,True)]))
FIXTURES.extend([
fixture('different_guards','''CCZ q0 q1 q2 if b0
CCZ q0 q1 q2 if b1''',must=[(0,1,False)],counts=(1,0)),
fixture('invert_guard_roundtrip','''CCZ q0 q1 q2 if b0
BIT_INVERT b0
CCZ q0 q1 q2 if b0
BIT_INVERT b0
CCZ q0 q1 q2 if b0''',must=[(0,2,False),(2,4,False)],counts=(2,0)),
fixture('stores_and_zero_guards','''BIT_STORE0 b0
CCZ q0 q1 q2 if b0
BIT_STORE1 b0
CCZ q0 q1 q2 if b0
BIT_STORE0 b0
CCZ q0 q1 q2 if b0
BIT_STORE1 b0
CCZ q0 q1 q2 if b0''',must=[(3,7,True)],counts=(1,0)),
fixture('irrelevant_conditional_bit_updates','''CCZ q0 q1 q2 if b1
BIT_STORE0 b0 if b1
BIT_STORE1 b0 if b1
BIT_INVERT b0 if b1
CCZ q0 q1 q2 if b1''',must=[(0,4,True)],counts=(1,0)),
fixture('captured_stack_invert','''PUSH_CONDITION if b0
BIT_INVERT b0
CCZ q0 q1 q2
BIT_INVERT b0
CCZ q0 q1 q2
POP_CONDITION''',must=[(2,4,True)],counts=(1,0)),
fixture('captured_stack_store','''PUSH_CONDITION if b0
BIT_STORE0 b0
CCZ q0 q1 q2
BIT_STORE1 b0
CCZ q0 q1 q2
POP_CONDITION''',must=[(2,4,True)],counts=(1,0)),
fixture('nested_captured_stack','''PUSH_CONDITION if b0
PUSH_CONDITION if b1
BIT_STORE0 b0
BIT_STORE0 b1
CCZ q0 q1 q2
CX q0 q1
CCZ q0 q1 q2
CX q0 q1
CCZ q0 q1 q2
POP_CONDITION
POP_CONDITION''',must=[(4,8,True)]),
fixture('hmr_new_guards','''CCZ q0 q1 q2 if b0
HMR q3 b0
CCZ q0 q1 q2 if b0
HMR q3 b1
CCZ q0 q1 q2 if b1''',must=[(0,2,False),(2,4,False)],counts=(2,0),measure_bits=(0,1)),
fixture('hmr_destroys_factor','''CCZ q0 q1 q2
HMR q0 b2
CCZ q0 q1 q2''',counts=(0,1),measure_bits=(2,)),
fixture('conditional_hmr','''CCZ q0 q1 q2
HMR q0 b2 if b0
CCZ q0 q1 q2''',counts=(0,0),measure_bits=(2,)),
fixture('reset_destroys_factor','''CCZ q0 q1 q2
R q0
CCZ q0 q1 q2''',counts=(0,1),measure_bits=(3,)),
fixture('equal_factors','''CX q0 q4
CCZ q0 q1 q4''',counts=(0,1)),
fixture('complement_factors','''CX q0 q4
X q4
CCZ q0 q1 q4''',counts=(0,1)),
fixture('affine_rank2_zero','''CX q0 q4
CX q1 q4
CCZ q0 q1 q4''',counts=(0,1)),
fixture('affine_rank2_one','''CX q0 q4
CX q1 q4
X q4
CCZ q0 q1 q4''',counts=(0,1)),
fixture('zero_factor','''CCZ q0 q1 q4''',counts=(0,1)),
fixture('constant_one','''X q4
CCZ q0 q1 q4''',counts=(0,1)),
])

def simulate(body,qin,bin_,outcomes):
    q=list(qin)+[0];b=list(bin_);stack=[True];phase=0;mi=0;ccz={}
    for pos,line in enumerate(body):
        w=line.split();name=w[0]
        if name=='PUSH_CONDITION':stack.append(stack[-1] and b[int(w[-1][1:])]);continue
        if name=='POP_CONDITION':stack.pop();continue
        g=stack[-1]
        if 'if' in w:
            ix=w.index('if');g=g and b[int(w[ix+1][1:])];w=w[:ix]
        qs=[int(x[1:]) for x in w[1:] if x.startswith('q')]
        if name=='CCZ':ccz[pos]={'factors':[q[x] for x in qs],'guard':int(g),'value':q[qs[0]]&q[qs[1]]&q[qs[2]]}
        if name in ('HMR','R'):
            m=outcomes[mi];mi+=1
            if g:
                phase^=m&q[qs[0]];q[qs[0]]=0
                if name=='HMR':b[int(w[2][1:])]=m
            continue
        if not g:continue
        if name=='X':q[qs[0]]^=1
        elif name=='CX':q[qs[1]]^=q[qs[0]]
        elif name=='CCX':q[qs[2]]^=q[qs[0]]&q[qs[1]]
        elif name=='SWAP':q[qs[0]],q[qs[1]]=q[qs[1]],q[qs[0]]
        elif name=='CSWAP':
            if q[qs[0]]:q[qs[1]],q[qs[2]]=q[qs[2]],q[qs[1]]
        elif name=='CCZ':phase^=q[qs[0]]&q[qs[1]]&q[qs[2]]
        elif name=='BIT_STORE0':b[int(w[1][1:])]=0
        elif name=='BIT_STORE1':b[int(w[1][1:])]=1
        elif name=='BIT_INVERT':b[int(w[1][1:])]^=1
        else:raise ValueError(line)
    assert len(stack)==1
    return q,b,phase,ccz

def semantic_checks(f,scan):
    nm=len(f['measure_bits']);states=[]
    for vals in itertools.product((0,1),repeat=6+nm):
        states.append(simulate(f['body'],vals[:4],list(vals[4:6])+[0,0],vals[6:]))
    pairs=[];reductions=[]
    for row in scan['opportunities']:
        if row['kind']=='repeated_phase':
            a=row['first'];b=row['second'];assert all(s[3][a]['value']==s[3][b]['value'] for s in states),(f['name'],row,'phase mismatch')
            exact_guard=all(s[3][a]['guard']==s[3][b]['guard'] for s in states)
            assert not row['same_guard'] or exact_guard,(f['name'],row,'incorrect same_guard')
            pairs.append({'first':a,'second':b,'fingerprint_same_guard':row['same_guard'],'truth_table_same_guard':exact_guard})
        elif row['kind']=='reduced_phase':
            factors=np.array([s[3][row['index']]['factors'] for s in states],dtype=np.uint8);r=row['reason']
            conditions={
                'zero_factor':any(not factors[:,j].any() for j in range(3)),
                'constant_one':any(factors[:,j].all() for j in range(3)),
                'equal_factors':any(np.array_equal(factors[:,j],factors[:,k]) for j in range(3) for k in range(j+1,3)),
                'complement_factors':any(np.array_equal(factors[:,j]^1,factors[:,k]) for j in range(3) for k in range(j+1,3)),
                'affine_rank2_zero':not np.bitwise_xor.reduce(factors,axis=1).any(),
                'affine_rank2_one':bool(np.bitwise_xor.reduce(factors,axis=1).all()),
            }
            assert conditions[r],(f['name'],row,'incorrect reduction');reductions.append(row)
    for a,b,g in f['must']:
        assert any(r['first']==a and r['second']==b and r['same_guard']==g for r in scan['opportunities'] if r['kind']=='repeated_phase'),(f['name'],'missing opportunity',(a,b,g),scan)
    if f['counts'] is not None:assert (scan['repeated_phases'],scan['reduced_phases'])==f['counts'],(f['name'],'count mismatch',scan)
    return {'truth_table_cases':len(states),'pairs':pairs,'reduced':reductions}

def native_checks(f,c):
    assignments=list(itertools.product((0,1),repeat=6));assignments=(assignments*4)
    qin=np.array([a[:4] for a in assignments],dtype=np.bool_).T
    bin_=np.array([list(a[4:6])+[0,0] for a in assignments],dtype=np.bool_).T
    total=0
    for seed in (202611151,202611152):
        sim=km.Simulator(batch_size=256,seed=seed,counting_operations=True)
        for j in range(4):sim.write_across_shots(km.q(j),qin[j]);sim.write_across_shots(km.b(j),bin_[j])
        sim.do(c)
        qout=sim.read_across_shots([km.q(j) for j in range(5)]).astype(np.uint8).T
        bout=sim.read_across_shots([km.b(j) for j in range(4)]).astype(np.uint8).T
        observed_bout=bout
        if f['name']=='reset_destroys_factor':
            # R hides its random phase outcome. A same-seed HMR companion
            # records that outcome. Compare native R and HMR phases/values
            # before using the independent Boolean oracle with that outcome.
            instrumented=km.Circuit('\n'.join('HMR q0 b3' if s=='R q0' else s for s in f['body']))
            observer=km.Simulator(batch_size=256,seed=seed,counting_operations=True)
            for j in range(4):observer.write_across_shots(km.q(j),qin[j]);observer.write_across_shots(km.b(j),bin_[j])
            observer.do(instrumented)
            observed_bout=observer.read_across_shots([km.b(j) for j in range(4)]).astype(np.uint8).T
            assert np.array_equal(observer.read_across_shots([km.q(j) for j in range(5)]).T,qout)
            assert all(observer.read_shot_phase(i)==sim.read_shot_phase(i) for i in range(256))
        for i,a in enumerate(assignments):
            outcomes=[int(observed_bout[i,j]) for j in f['measure_bits']]
            eq,eb,ep,_=simulate(f['body'],a[:4],list(a[4:6])+[0,0],outcomes)
            assert np.array_equal(qout[i],eq),(f['name'],seed,i,'q',qout[i],eq)
            assert np.array_equal(bout[i],eb),(f['name'],seed,i,'b',bout[i],eb)
            assert int(sim.read_shot_phase(i))%2==ep,(f['name'],seed,i,'phase',sim.read_shot_phase(i),ep)
        total+=256
    return {'native_cases':total,'seeds':[202611151,202611152],'quantum_errors':0,'classical_errors':0,'phase_errors':0}

def main():
    DATA.mkdir(exist_ok=True);src=ROOT/'dqi_next_conditional_phase_scan.cpp';exe=ROOT.parent/'dqi_next_conditional_phase_fixture_scanner'
    subprocess.run(['g++','-O3','-std=c++17',str(src),'-o',str(exe)],check=True)
    report={'status':'RUNNING','scope':'Finite small fixtures; discovery only; no production rewrite or proof of completeness','scanner_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'fixtures':[]}
    for f in FIXTURES:
        # q4 is unregistered, initially clean. All other quantum inputs are ABI.
        header='\n'.join([f'APPEND_TO_REGISTER q{j} r0' for j in range(4)]+['REGISTER r0 "qinputs"']+[f'APPEND_TO_REGISTER b{j} r1' for j in range(4)]+['REGISTER r1 "cbits"'])
        text=header+'\n'+'\n'.join(f['body'])+'\n';kmx=DATA/(f['name']+'.kmx');kmb=DATA/(f['name']+'.kmb');kmx.write_text(text);c=km.Circuit(text);c.to_file(str(kmb),format='kmb')
        sp=DATA/(f['name']+'.discovery.json');r=subprocess.run([str(exe),str(kmb),str(sp)],capture_output=True,text=True);assert r.returncode==0,(f['name'],r.stderr)
        scan=json.loads(sp.read_text());truth=semantic_checks(f,scan);native=native_checks(f,c)
        row={'name':f['name'],'kmx':str(kmx.relative_to(ROOT)),'kmb_sha256':hashlib.sha256(kmb.read_bytes()).hexdigest(),'scanner_repeated':scan['repeated_phases'],'scanner_reduced':scan['reduced_phases'],**truth,**native};report['fixtures'].append(row)
        print(f['name'],'PASS',scan['repeated_phases'],scan['reduced_phases'],flush=True)
        (ROOT/'dqi_next_conditional_phase_fixture_results.json').write_text(json.dumps(report,indent=2))
    report.update(status='PASS',fixture_count=len(report['fixtures']),native_cases=sum(x['native_cases'] for x in report['fixtures']),truth_table_cases=sum(x['truth_table_cases'] for x in report['fixtures']))
    (ROOT/'dqi_next_conditional_phase_fixture_results.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='fixtures'}),flush=True)

if __name__=='__main__':main()

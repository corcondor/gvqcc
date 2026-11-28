"""Reconstruct a CF route on the pinned PUBLIC kit, NOT the private 344k chain.

The upstream pdrfix doc explicitly describes the missing (C,F) correction.
Keep original route and lower/CG untouched in 'fixed'; then compare 'fused'
using the exact AST adapter from PR187. No promotion without independent
unpaired forward equality and round-trip tests.
"""
import argparse, os, sys, pathlib, importlib, types, json, hashlib, gc
import numpy as np
import kickmix as km

def install_route_fix(fix, P):
    old = fix._route_rest
    def corrected(b, ar, U, c, X, Bq, Cq, Fq, C2q):
        old(b, ar, U, c, X, Bq, Cq, Fq, C2q)
        # Public v2 doc: when B=C2=0 and C=F=1,
        # replace s_(U-3) by q0'_(U-3)*s_(U-3)+s_(U-4).
        lits = [(Bq, True), (Cq, False), (Fq, False), (C2q, True)]
        h = P.flag_and(b, lits)
        q = c[U-3]['f'][-2]
        z = P.masked_word(b, h, q)
        b.cx(h, z[0])
        for x, s, t in zip(X, P.tops(U-3), P.tops(U-4)):
            ar.mul_xor0(b, z, s, x)
            for j in range(12):
                b.ccx(h, t[j], x[j])
        b.cx(h, z[0])
        P.erase_masked_word(b, h, q, z)
        P.erase_flag_and(b, h, lits)
    fix._route_rest = corrected

def install(kit, tools, mode):
    sys.modules['circ'] = km
    sys.path[:0] = [str(tools), str(kit), str(kit/'exp/new/root'),
                   str(kit/'exp/new/a01'), str(kit/'exp/round7/root'),
                   str(kit/'exp/next/carry')]
    os.environ['DQI_BUILD_SOURCE'] = str(kit)
    os.environ['Z2_PDR_BLOCKS'] = '15,13,11'
    os.environ['Z2_PDR_RBLOCKS'] = '15,13,11'
    os.environ['Z2_PDR_REV'] = '1'
    os.environ['Z2_PDR_LOCAL'] = '1'
    os.environ['Z2_PDR_SHARE'] = '1'
    os.environ['Z2_PDR_LIVEB'] = '1'
    os.environ['PDRFIX_BC'] = '1'
    os.environ['PDRFIX_ROUTE'] = '1'
    import loader_cache
    loader_cache.install()
    import walk_bound
    # Public kit's final decoder, no missing private line installers.
    import decode_next_best
    import decode_trace_merged_completed_return
    decode = decode_trace_merged_completed_return.decode
    print('decode',decode.__module__,decode.__name__,flush=True)
    if 'g' not in decode.__globals__ or 'convert_safe' not in decode.__globals__['g']:
        raise RuntimeError('public kit decoder does not expose expected converter')
    if mode != 'ref':
        P = importlib.import_module('dqi_z2_pdr')
        print('PDR install',P.install(km,types.SimpleNamespace(decode=decode)),flush=True)
        fix = importlib.import_module('dqi_int_pdrfix')
        if mode in ('fused','fused510'):
            from apply_coefficient_fusion import rewrite
            orig = pathlib.Path(fix.__file__).read_text()
            new = rewrite(orig)
            exec(compile(new,fix.__file__+':fusion','exec'),fix.__dict__)
        if mode in ('fixed','fused'):
            install_route_fix(fix,P)
        if mode == 'fused510':
            import cf_route
            cf_route.P = P
            fix._route_rest = cf_route._route_rest
        print('PDRFIX install',fix.install(km,types.SimpleNamespace(decode=decode)),flush=True)
        if mode == 'fused510':
            from transport42_lean import install_for_pdr
            stats = install_for_pdr(P)
            decode.__globals__['_transport42_stats'] = stats
    # Do not use loader_prune unless all dynamic wrapper scopes retain dependencies.
    # Its pruning may remove the external references needed in these experiments.
    return decode

def make_chart(CT, rng, n, drop):
    # Reconstruct exact degree sequence with a degree-3 drop. The skipped
    # degrees are (drop-1, drop-2), unlike gap_charts's degree-2 drop.
    d=[17]
    while d[-1]>0:
        d.append(d[-1] - (3 if d[-1]==drop else 1))
    r=[None]*len(d)
    r[-1]=CT.rand_poly(rng,n,0);r[-2]=CT.rand_poly(rng,n,d[-2])
    for k in range(len(d)-2,0,-1):
        q=CT.rand_poly(rng,n,d[k-1]-d[k])
        v=CT.pmul(q,r[k]);lo=r[k+1]
        v[:,:lo.shape[1]]^=lo
        r[k-1]=v[:,:d[k-1]+1]
    O,R0=r[0],r[1]
    lam=CT.inv0(O[:,17])
    O=np.stack([CT.mul(lam,O[:,i]) for i in range(18)],1)
    R0=np.stack([CT.mul(lam,R0[:,i]) for i in range(R0.shape[1])],1)
    c=rng.integers(0,4096,size=n,dtype=np.int64)
    E=np.stack([CT.mul(c,O[:,i]) for i in range(18)],1)
    E[:,:R0.shape[1]]^=R0
    B=np.zeros((n,36),dtype=np.int64)
    B[:,0::2]=CT.mul(E,E);B[:,1::2]=CT.mul(O,O)
    A=rng.integers(0,4096,size=(n,35),dtype=np.int64)
    return A,B[:,:35]

def panel(CT):
    rng=np.random.default_rng(20261127)
    n=32
    rows=[('random',rng.integers(0,4096,(n,35),dtype=np.int64),
           rng.integers(0,4096,(n,35),dtype=np.int64))]
    for d in range(15,8,-1):
        A,B=make_chart(CT,rng,n,d);rows.append((f'degree3_drop_{d}',A,B))
    return rows

def build(CT,decode,mode):
    conv=decode.__globals__['g']['convert_safe']
    # Exact cache reference via original graph walker; avoid global guesses.
    saved=CT.hankel_saved(decode)
    return CT.build(conv,mode,saved)

def filehash(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run(kit,tools,mode,out,full=False):
    decode=install(kit,tools,mode)
    import dqi_int_convtest as CT
    rows=panel(CT)
    report={'mode':mode,'public_kit':str(kit),'full_private_chain':False,'runs':{}}
    out.mkdir(parents=True,exist_ok=True)
    for direction in ('fwd','round'):
        circ,Areg,Breg,peak,_=build(CT,decode,direction)
        print('built',mode,direction,'width',circ.num_qubits,'peak',peak,'ops',len(circ),flush=True)
        result=[]
        for i,(label,A,B) in enumerate(rows):
            R=CT.run(circ,Areg,Breg,A,B,2026112700+i)
            clean=(R[0]==A).all(1)&(R[1]==B).all(1)&~R[2]&~R[3]
            result.append({'label':label,'n':len(A),'clean':int(clean.sum()),
                           'phase_errors':int(np.asarray(R[2]).sum()),'dirty':int(np.asarray(R[3]).sum()),
                           'mean_paid':float(R[4])})
            if direction=='fwd':
                np.savez_compressed(out/(label+'.npz'),A=R[0],B=R[1])
            print(mode,direction,result[-1],flush=True)
        report['runs'][direction]={'Q':circ.num_qubits,'peak':peak,'ops':len(circ),
             'static_paid':circ.operation_statistics().num_toffoli_like,'cases':result}
        if direction=='round' and mode in ('fixed','fused','fused510'):
            path=out/'converter_round.kmb';circ.to_file(str(path),format='kmb')
            report['runs'][direction]['sha256']=filehash(path)
        (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
        del circ,Areg,Breg
        gc.collect()
    if mode == 'fused510':
        report['transport42_stats'] = decode.__globals__['_transport42_stats']
        (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    if full:
        # NOT the private 344k chain; reconstruct the public kit full oracle.
        b=km.CircuitBuilder()
        S=[b.alloc_qubits(12) for _ in range(70)]
        E=[b.alloc_bits(12) for _ in range(4095)]
        decode(b,S,E)
        metadata=[]
        for i in range(70):
            metadata.append(f'REGISTER r{i} "S{i}"')
            metadata.extend(f'APPEND_TO_REGISTER q{12*i+j} r{i}' for j in range(12))
        for i in range(4095):
            metadata.append(f'REGISTER r{70+i} "E{i}"')
            metadata.extend(f'APPEND_TO_REGISTER b{12*i+j} r{70+i}' for j in range(12))
        c=km.Circuit('\n'.join(metadata))+b.finish_circuit()
        path=out/'dqi.kmb';c.to_file(str(path),format='kmb')
        report['full_public_kit']={'Q':c.num_qubits,'ops':len(c),
            'static_paid':c.operation_statistics().num_toffoli_like,'sha256':filehash(path)}
        (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('upstream',type=pathlib.Path)
    p.add_argument('mode',choices=['ref','old','fixed','fused','fused510'])
    p.add_argument('out',type=pathlib.Path)
    p.add_argument('--full',action='store_true')
    a=p.parse_args()
    base=a.upstream.resolve()/'third_party/thembones-milestone-generators-v2/dqi'
    run(base/'kit/kv_unfused5',base/'tools',a.mode,a.out,a.full)

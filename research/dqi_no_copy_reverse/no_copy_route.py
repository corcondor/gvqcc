# Insert this tested block after the width dispatcher and before
# b=km.CircuitBuilder() in the prior build_fast.py. Its globals are the
# imported actual decoder graph, os, walk_bound, ar and G.
from narrow_gauge import divide_pair_and_invert
from exp.arithmetic.division import phase_zero

def without_R(original):
    g=original.__globals__;ref=g['ref'];combine=g['combine'];inv=g['inv'];scalepair=g['scalepair'];cx=g['cx']
    def route(b,words,gi,reverse=False,token=None,normalizer=None):
        if not (reverse and gi in set(map(int,os.environ.get('NOREPLAY_NODES','16').split(',')))):
            return original(b,words,gi,reverse,token,normalizer)
        print('NO_R node',gi,'live',b.num_allocated_qubits,flush=True)
        gn=ref.groups[gi]
        N=combine(words[gn['word']:gn['word']+2]);L=combine(words[gn['word']+2:gn['word']+4])
        heads=[words[2*i:2*i+2] for i in range(2*gi)]
        params=[];c=0
        for i in range(2*gi):
            q=ref.ks[i]^gn['kap'];params.append((q,c));c^=inv(q)
        assert c==0
        pole=token['pole'];D=b.alloc_qubits(24);b.x(D[0]);b.cx(pole,N[0]);b.cx(pole,D[0])
        for head,(q,c) in reversed(list(zip(heads,params))[1:]):
            ref.external_chain_step(b,head,N,D,L,q,gn['c'],c,True)
        q0=params[0][0];scalepair(b,N,inv(q0));b.swap(N,D);scalepair(b,L,inv(q0))
        with b.mark('no_R_normalize'):
            mask=token['norm'].pop('inv_norm')
            ar._phase_norm(b,D,mask,ref.K);b.free(mask)
            ref.external_square24(b,L,True)
            divide_pair_and_invert(b,[N,L],D)
            ref.external_square24(b,L)
            a,h=heads[0];cx(b,h,a,gn['c']);b.cx(combine(heads[0]),N);cx(b,h,a,gn['c']);b.cx(h,L[:12])
            b.cz(D,token['norm']['gauge']);b.free(token['norm']['gauge'])
            m=b.alloc_bits(24);b.hmr(D,m);b.free(D)
        with b.mark('no_R_replay'):
            D=b.alloc_qubits(24);b.x(D[0])
            for i,(head,(q,c)) in enumerate(zip(heads,params)):
                ref.external_scalar_step(b,head,N,D,q,gn['c'],False,first=i==0)
            b.cswap(pole,N,D);b.cz(D,m);b.free(m);b.cswap(pole,N,D)
            pm=b.alloc_bits(1);b.hmr(pole,pm[0]);b.free(pole);phase_zero(b,D,pm[0]);b.free(pm)
            for i in reversed(range(len(heads))):
                ref.external_scalar_step(b,heads[i],N,D,params[i][0],gn['c'],True,first=i==0)
            b.x(D[0]);b.free(D)
        print('NO_R node',gi,'done',b.num_allocated_qubits,flush=True)
    return route

seen=set();rebound=[]
for fn in walk_bound.functions(G['extraction']):
    gg=fn.__globals__
    if '_a18_deferred_original' in gg and id(gg) not in seen:
        seen.add(id(gg));old=gg['_a18_deferred_original'];gg['_a18_deferred_original']=without_R(old)
        rebound.append(old.__code__.co_filename)
assert rebound
print('NO_R bindings',rebound,flush=True)

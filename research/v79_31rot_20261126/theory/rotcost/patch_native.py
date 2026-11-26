"""Exact bounded direct/toggle conversion in an existing native KMB.

Preserves the nonlinear scheduler and identifies controls/free scratch from
full 2**22 truth tables. Flag constants are merged into an existing rotation
or inserted at the first matching predicate. Temporary gates restore data.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from select_and_emit import select, DONOR, ROOT, MOD, W, NativeKMB, write_hmr
from native_kmb import Op
sys.path.insert(0, str(ROOT/'theory'))
from audit_v79 import input_tables


def group_key(tag):
    _, s, d, p, V, H = tag[:6]
    return d, p, tuple(V), tuple(H)


def patch(source, stem, selected):
    start = time.time()
    metadata = json.loads(source.with_suffix('.json').read_text())
    circuit = NativeKMB.read(source.with_suffix('.kmb'))
    tags, angles = metadata['tags'], list(map(int, metadata['angles']))
    assert len(tags) == len(angles) == circuit.header[10]
    direct, sums, remove, group_add = {}, defaultdict(int), set(), defaultdict(int)
    for ri, (tag, angle) in enumerate(zip(tags, angles)):
        if tag[0] == 'direct':
            direct.setdefault(group_key(tag), ri)
        if tag[0] == 'toggle' and tag[1] in selected:
            sums[tag[1]] += angle
            group_add[group_key(tag)] += angle
    for ri, (tag, angle) in enumerate(zip(tags, angles)):
        if tag[0] == 'parity' and tag[1] in selected:
            assert (angle+sums[tag[1]]) % MOD == 0
            remove.add(ri)
    assert len(remove) == len(selected)
    updated, added_groups = {}, {}
    for key, amount in group_add.items():
        if key in direct:
            ri = direct[key]
            updated[ri] = (angles[ri]+amount) % MOD
        elif amount % MOD:
            added_groups[key]=amount % MOD
    length = 1 << W; ones = (1<<length)-1
    inputs = input_tables(W)
    state = inputs + [0]*(circuit.header[1]-W)
    parity_cache, flag_cache = {}, {}
    def parity(mask):
        if mask not in parity_cache:
            result=0
            for q in range(W):
                if mask >> q & 1:
                    result ^= inputs[q]
            parity_cache[mask]=result
        return parity_cache[mask]
    def flag(tag):
        key=group_key(tag)
        if key not in flag_cache:
            d,p,V,H=key;value=ones
            for q in range(W-d,W):
                value &= inputs[q] if p>>(q-W+d)&1 else ones^inputs[q]
            for v,h in zip(V,H):
                value &= ones^parity(v) if h==1 else parity(v)
            flag_cache[key]=value
        return flag_cache[key]
    out, new_tags, new_angles, choices = [], [], [], []
    dirty_compensation = defaultdict(int)
    ri, debt = 0, None
    for index, op in enumerate(circuit.ops):
        w,g=op.wires,op.raw
        if g==17:state[w[0]]^=ones
        elif g==33:state[w[1]]^=state[w[0]]
        elif g==49:state[w[2]]^=state[w[0]]&state[w[1]]
        elif g==80:
            assert debt is None and op.measurement==0
            debt=state[w[0]];state[w[0]]=0
        elif g in (144,160):
            correction=state[w[0]] if g==144 else state[w[0]]&state[w[1]]
            assert debt==correction and op.condition==0
            debt=None
        elif g==19:
            assert debt is None
            tag,angle=tags[ri],angles[ri]
            if tag[0]=='toggle' and tag[1] in selected:
                f=flag(tag);q=w[0];s=tag[1]
                assert state[q]==parity(s)^f
                candidates=[j for j in range(W,len(state)) if j!=q and state[j]==f]
                if not candidates:
                    candidates=[j for j in range(W) if j!=q and state[j]==f]
                assert candidates,(index,tag,'flag unavailable')
                guard=candidates[0]
                temp=next((j for j in range(W,len(state))
                           if j not in (q,guard) and state[j]==0),None)
                key=group_key(tag)
                if key in added_groups:
                    out.append(Op(19,(guard,)))
                    new_tags.append(('direct',0,*tag[2:6]))
                    new_angles.append(added_groups.pop(key))
                if temp is not None:
                    out.extend([Op(33,(guard,q)),Op(49,(guard,q,temp)),Op(19,(temp,)),
                                Op(80,(temp,),measurement=0),
                                Op(160,(guard,q),condition=0),Op(33,(guard,q))])
                    new_tags.append(('product',*tag[1:6],str(angle)))
                    new_angles.append((-2*angle)%MOD)
                    mode='clean'
                else:
                    temp=W-1;d,p=tag[2],tag[3];b=(p>>(d-1))&1
                    assert d>0 and temp not in (guard,q)
                    assert (f&inputs[temp])==(f if b else 0)
                    beta=-2*angle*(1-2*b)
                    out.extend([Op(33,(guard,q)),Op(49,(guard,q,temp)),Op(19,(temp,)),
                                Op(49,(guard,q,temp)),Op(33,(guard,q))])
                    new_tags.append(('borrow',*tag[1:6],str(angle),temp))
                    new_angles.append(beta%MOD)
                    dirty_compensation[temp]-=beta
                    mode='dirty'
                choices.append(dict(instruction=index,rotation=ri,frequency=s,
                                    flag=guard,parity=q,temporary=temp,mode=mode))
            elif ri not in remove:
                angle=updated.get(ri,angle)
                if angle:
                    out.append(op);new_tags.append(tag);new_angles.append(angle)
            ri+=1
            continue
        else:raise ValueError(g)
        out.append(op)
    assert debt is None and state==inputs+[0]*(len(state)-W) and not added_groups
    for q,angle in sorted(dirty_compensation.items()):
        angle%=MOD
        if angle:
            out.append(Op(19,(q,)))
            new_tags.append(('parity',1<<q,0,0,[],[]));new_angles.append(angle)
    write_hmr(circuit,stem.with_suffix('.kmb'),out,new_angles,circuit.header[1],True)
    counts=Counter(o.raw for o in out)
    generic=sum(a%(1<<125)!=0 for a in new_angles)
    tbase=sum(a%(1<<125)==0 and a%(1<<126)!=0 for a in new_angles)
    margin=138112178
    rotation_t=.56*math.log2((1<<64)*generic/(math.pi*margin))+5.3
    stats=dict(width=circuit.header[1],ops=len(out),ccx=counts[49],cx=counts[33],
               rotations=len(new_angles),generic=generic,t_base=tbase,hmr=counts[80],
               selected_frequencies=len(selected),converted_occurrences=len(choices),
               direct_clean_terms=sum(c['mode']=='clean' for c in choices),
               direct_dirty_terms=sum(c['mode']=='dirty' for c in choices),
               source_sha256=hashlib.sha256(source.with_suffix('.kmb').read_bytes()).hexdigest(),
               sha256=hashlib.sha256(stem.with_suffix('.kmb').read_bytes()).hexdigest(),
               formula_cost_assuming_exact_phase=circuit.header[1]*(counts[49]+(tbase+generic*rotation_t)/4),
               full_cube_control_and_temp_check=length,seconds=time.time()-start)
    stem.with_suffix('.json').write_text(json.dumps(dict(stats=stats,tags=new_tags,
                 angles=[str(a) for a in new_angles]),separators=(',',':')))
    stem.with_suffix('.patch.json').write_text(json.dumps(dict(stats=stats,choices=choices),indent=2)+'\n')
    print(json.dumps(stats,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--stem',type=Path,required=True)
    p.add_argument('--budget',type=int,default=36)
    p.add_argument('--selection',type=Path)
    a=p.parse_args();a.source=a.source.resolve();a.stem=a.stem.resolve()
    a.stem.parent.mkdir(parents=True,exist_ok=True)
    selected=(set(json.loads(a.selection.read_text())['frequencies']) if a.selection
              else select(a.source,'adaptive',8.28,a.stem.with_suffix('.selection.json'),a.budget))
    patch(a.source,a.stem,selected)

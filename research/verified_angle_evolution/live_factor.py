"""Exact 1220-address forward/reverse property test of each CCX's inputs.

Potential replacements must hold in BOTH reachable contexts for the same
serialized ANGLE circuit. A hit is only a prefilter; independent whole-family
proof is still mandatory.
"""
from exact_angle import N, MASK, ADDR,verify
from kmb_v2 import Circuit

def scan(circuits):
    _,ref=verify(circuits)
    dead=[];affine=[];activity=[]
    for k,c in enumerate(circuits):
        fwd=ref[k-1] if k else [0]*40
        bwd=ref[k]
        all_hits={};all_activities={}
        for direction,source in [('forward',fwd),('reverse',bwd)]:
            state=ADDR+source.copy()+[0]*(c.nqubits-51)
            for pos,g in enumerate(c.ops):
                op=g.name; q=g.q
                if op=='CCX':
                    a,b,t=q;andmask=state[a]&state[b]
                    key=(k,pos)
                    all_hits.setdefault(key,[]).append((direction,andmask,tuple(state)))
                    all_activities.setdefault(key,[]).append(andmask.bit_count())
                    state[t]^=andmask
                elif op=='CX':state[q[1]]^=state[q[0]]
                elif op=='X':state[q[0]]^=MASK
                elif op=='HMR':state[q[0]]=0
                elif op in ('CZ_IF','R'):pass
                else:raise ValueError((k,op))
        for key,v in all_hits.items():
            assert len(v)==2
            activity.append(sum(all_activities[key]))
            if all(x[1]==0 for x in v):dead.append(key)
            for source in range(c.nqubits):
                if source in c.ops[key[1]].q:continue
                if all(x[1]==x[2][source] for x in v):affine.append((key,source))
    return {'ccx_checked':len(activity),'dead':dead,'live_wire_equivalences':affine,
            'minimum_combined_activity':min(activity),'total_combined_activity':sum(activity)}

"""Joint fanout and measured-phase adjoint of shared tensor factors.
Rank-one fanout is fused across commuting gates. A same-guard CCX pair
around an affine/phase word is removed by transporting its Boolean
covectors and emitting the missing phase directly. No new scratch qubit.
"""
from v39_tensor_integrate import *
from v39_tensor_lifetime import affine_ops
from v38_fuse import fuse_safe

def phase_product(A,B,w,flag,condition,t):
    opts=[]
    for a,b in [(A,B),(B,A)]:
        for p in range(37):
            if p in (w,t) or not a>>(p+1)&1 or b>>(p+1)&1:continue
            for q in range(37):
                if q in (p,w,t)or not b>>(q+1)&1:continue
                aa=a^(b^(1<<(q+1)))if a>>(q+1)&1 else a
                pre=affine_ops(b,q)+affine_ops(aa,p)
                o=Op((32 if w is None else 48)|flag,(p,q)if w is None else (p,q,w),condition=condition)
                opts.append(pre+[o]+pre[::-1])
    return min(opts,key=len) if opts else None

def transport(L,o):
    g=o.raw&127
    if g==17 and L>>(o.wires[0]+1)&1:return L^1
    if g==33 and L>>(o.wires[1]+1)&1:return L^(1<<(o.wires[0]+1))
    return L

def adjoint_pair(ops):
    best=None
    for i,x in enumerate(ops):
        if x.raw&127!=49:continue
        a,b,t=x.wires;A=1<<(a+1);B=1<<(b+1);add={};flag=x.raw&128;cond=x.condition
        for j in range(i+1,min(i+100,len(ops))):
            y=ops[j];g=y.raw&127;w=y.wires
            if y==x and {A,B}=={1<<(a+1),1<<(b+1)}:
                paid=sum(z.raw&127 in PAID for v in add.values()for z in v)
                if paid<2:
                    mid=[]
                    for k in range(i+1,j):mid += [ops[k]]+add.get(k,[])
                    cand=ops[:i]+mid+ops[j+1:]
                    rec=dict(i=i,j=j,source=pack(x),corrections={str(k):list(map(pack,v))for k,v in add.items()},static_saved=2-paid,condition=cond)
                    if best is None or (rec['static_saved'],-len(cand))>(best[1]['static_saved'],-len(best[0])):best=(cand,rec)
                break
            if y.raw in (129,1) or g in (19,64,65,66,80,34,50,49):break
            if g in(17,33):
                if g==33 and w[0]==t:break
                if w[-1]==t:continue
                if y.raw&128 and y.condition!=cond:
                    if (A|B)>>(w[-1]+1)&1:break
                    continue
                A=transport(A,y);B=transport(B,y)
            elif g in(0,16,32,48):
                if t not in w:continue
                if len(w)>2:break
                if (y.raw&128) and flag and y.condition!=cond:break
                cf=flag or (y.raw&128);cc=cond if flag else y.condition
                z=phase_product(A,B,next((u for u in w if u!=t),None),cf,cc,t)
                if z is None:break
                add[j]=z
            else:break
    return best

def joint_paid(ops):
    out=ops;history=[]
    for _ in range(12):
        cand,r=fuse_safe(out)
        # fuse_safe is scope-aware but only works on unconditional gates.
        if sum(z.raw&127 in PAID for z in cand)<sum(z.raw&127 in PAID for z in out):
            out=compress(cand);history.append(dict(kind='fanout',changes=r))
        a=adjoint_pair(out)
        if a:
            out=compress(a[0]);history.append(dict(kind='phase_adjoint',change=a[1]));continue
        if not r:break
    return out,history

def rewrite(src,G,out,receipt):
    K=NativeKMB.read(src);new=[];pos=0;stats=[]
    for g in G:
        h=dict(g);old=list(map(unpack,h['replacement']));off=h['fragment_offset'];body=old[off:];z,hist=joint_paid(body)
        if z!=body:
            # determine exact expected cost later from original source event alignment;
            # each fanout is unconditional; phase-adjoint changes have original guard.
            # Run exact replay with a computed delta instead of assuming static=expected.
            h['replacement']=list(map(pack,old[:off]+z));p=h['omit'];ff=[Op(o.raw,tuple(q-(q>p)for q in o.wires),o.measurement,o.condition)for o in z];F=NativeKMB.read(h['fragment']);name=h['fragment'].replace('tensor_fragment','tensor_fused_fragment');Path(name).write_bytes(byte_emit(F,ff,36));h['fragment']=name;h['fragment_sha']=sha(name);h['delta']=None;h['body_after_compact']=len(z)
            stats.append(dict(core_a=h['core_a'],ops_before=len(body),ops_after=len(z),paid_before=sum(o.raw&127 in PAID for o in body),paid_after=sum(o.raw&127 in PAID for o in z),history=hist))
        new.append(h)
    ops=[];pos=0
    for g in new:ops+=K.ops[pos:g['a']]+list(map(unpack,g['replacement']));pos=g['b']
    ops+=K.ops[pos:];Path(out).write_bytes(byte_emit(K,ops,37));assert NativeKMB.read(out).ops==ops
    Path(receipt+'.groups.json').write_text(json.dumps(new,indent=2));Path(receipt+'.fusion.json').write_text(json.dumps(stats,indent=2));print('FUSION',[(x['core_a'],x['ops_before'],x['ops_after'],x['paid_before'],x['paid_after'])for x in stats],flush=True)
    d=replay(src,out,new,receipt+'.replay.json');Path(receipt+'.groups.json').write_text(json.dumps(new,indent=2));return d
if __name__=='__main__':rewrite('v39_advance.kmb',json.load(open('v39_tensor_joint.groups.json')),'v39_tensor_fused_NOT_SUBMISSION.kmb','v39_tensor_fused')

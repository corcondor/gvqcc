"""Transport evaluation frames between additive-subspace points.
No source coefficient is reread after its block writes it; no extra field word.
"""
from functools import lru_cache
from collections import defaultdict
import multipoint_guard247 as M
import grouped_guard247 as G
import fft_plan247 as P
import invariant247 as Base
import crt882 as C
import joint_phase as J

def div(a,b):return C.m(a,C.inv(b)) if a else 0

def transition(b,a,p,old,new):
    assert old[p] and new[p]
    c=div(new[p],old[p]);M.frame(b,a[p],c)
    for k in sorted(set(old)|set(new)):
        if k!=p:
            v=new.get(k,0)^C.m(c,old.get(k,0))
            if v:M.addlin(b,a[k],a[p],v)
def output_change(b,a,old,new,t):
    # Coordinates F_w: p = y_t / w_t, y_i' = y_i + w_i p.
    assert old[t] and new[t]
    c=div(old[t],new[t])
    for k in sorted(set(old)|set(new)):
        if k!=t:
            z=old.get(k,0)^C.m(c,new.get(k,0))
            if z:M.addlin(b,a[t],a[k],z)
    M.frame(b,a[t],c)
def out_enter(b,a,w,t):
    M.frame(b,a[t],C.inv(w[t]))
    for k,z in w.items():
        if k!=t and z:M.addlin(b,a[t],a[k],z)
def out_exit(b,a,w,t):
    for k,z in reversed(list(w.items())):
        if k!=t and z:M.addlin(b,a[t],a[k],z)
    M.frame(b,a[t],w[t])
@lru_cache(None)
def scale_cost(c):
    return 0 if c==1 else len(C.lin_ops(M.cols(c)))
@lru_cache(None)
def xor_cost(c):
    return sum(x.bit_count() for x in M.cols(c)) if c else 0
def tr_cost(old,new,p):
    c=div(new[p],old[p])
    return scale_cost(c)+sum(xor_cost(new.get(k,0)^C.m(c,old.get(k,0))) for k in set(old)|set(new) if k!=p)
def out_cost(w,t):
    return scale_cost(w[t])+sum(xor_cost(z) for k,z in w.items() if k!=t)
def out_tr_cost(old,new,t):
    c=div(old[t],new[t])
    return scale_cost(c)+sum(xor_cost(old.get(k,0)^C.m(c,new.get(k,0))) for k in set(old)|set(new) if k!=t)
@lru_cache(None)
def frame_plan(key):
    forms=M.eval_forms(*key)
    # x=0 can have dependent forms. Retain its independently verified frame.
    rest=[(i,u,v,w) for i,(u,v,w) in enumerate(forms) if i and any(w.values())]
    if not rest:return (),None,None,()
    u0,v0=rest[0][1:3]
    pp=set(k for k,z in u0.items() if z)-set(v0)
    qq=set(k for k,z in v0.items() if z)-set(u0)
    assert pp and qq
    def pivot_cost(j,k):
        s={j:1};z=0
        for r in rest:z+=tr_cost(s,r[k],j);s=r[k]
        return z+tr_cost(s,{j:1},j)
    p=min(pp,key=lambda j:(pivot_cost(j,1),j))
    q=min(qq,key=lambda j:(pivot_cost(j,2),j))
    dp={}
    prev=None
    for i,u,v,w in rest:
        nex={}
        for t,z in w.items():
            if not z:continue
            if prev is None:nex[t]=(out_cost(w,t),(t,))
            else:
                opts=[]
                for k,(c,ts) in dp.items():
                    if k==t:cost=out_tr_cost(prev,w,t)
                    else:cost=out_cost(prev,k)+out_cost(w,t)
                    opts.append((c+cost,ts+(t,)))
                nex[t]=min(opts)
        dp=nex;prev=w
    _,ts=min((c+out_cost(prev,t),ts) for t,(c,ts) in dp.items())
    return tuple(rest),p,q,ts

def shared_eval(self,a,active,tmp,key):
    d=key[0];b=self.b
    forms=M.eval_forms(*key)
    if forms:M.add_product(self,a,active,tmp,*forms[0],d)
    rest,p,q,ts=frame_plan(key)
    if not rest:return
    uold={p:1};vold={q:1};old=None;told=None
    for (_,u,v,w),t in zip(rest,ts):
        transition(b,a,p,uold,u);transition(b,a,q,vold,v)
        uold=u;vold=v
        if old is None:out_enter(b,a,w,t)
        elif told==t:output_change(b,a,old,w,t)
        else:out_exit(b,a,old,told);out_enter(b,a,w,t)
        M.masked_copy(b,a,active,tmp,q,1,d)
        self.mul(a[p],tmp,a[t])
        M.masked_copy(b,a,active,tmp,q,1,d,True)
        old=w;told=t
    out_exit(b,a,old,told)
    transition(b,a,p,uold,{p:1});transition(b,a,q,vold,{q:1})

def unit_power(self,a,active,tmp,d):
    b=self.b
    def copy(j):M.masked_copy(b,a,active,tmp,j,1,d)
    def clear(j):M.masked_copy(b,a,active,tmp,j,1,d,True)
    for lo,hi in P.plan(len(a),d)[1]:
        s,g=G.one_block(lo,hi,d)
        for i,j,t in s:
            if t==0:
                M.frame(b,a[j],1,d=d)
                for x,y in zip(a[j],a[i]):b.ccx(active,x,y)
                M.frame(b,a[j],1,True,d=d)
            else:copy(j);self.mul(a[t],tmp,a[i]);clear(j)
        _,rr=P.block_cost(lo,hi,d)
        if rr is None:
            for j,items in g.items():
                copy(j)
                for i,t in items:self.mul(a[t],tmp,a[i])
                clear(j)
        else:
            for ev,r,h0,h1,j0,j1,u0,u1 in rr:
                if ev:shared_eval(self,a,active,tmp,(d,r,h0,h1,j0,j1,u0,u1))
                else:
                    for j in range(j0,j1+1):
                        copy(j)
                        for h in range(max(h0,u0+j),min(h1,u1+j)+1):
                            self.mul(a[d*(h-j)+r],tmp,a[d*h+r])
                        clear(j)
if __name__=='__main__':
    M.reference_check()
    G.unit_power=unit_power
    Base.Guard.reciprocal=G.reciprocal
    Base.main()

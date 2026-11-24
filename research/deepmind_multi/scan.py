#!/usr/bin/env python3
"""Multi-task local reversible/phase window search, with Lean certificate emitter.

Input: genuine KickMix 2 KMB (`invsqrt`, `dqi`, or ANGLE). Non-mutating by default.
Every proposed window replaces *two* CCX by one (plus CX), potentially across
X/CX/CCX/Z/CZ/CCZ instructions. Exhaustively verifies the entire window on all
2^n assignments (n<=6), including its diagonal phase sign; emits kernel-checkable
Lean source. All HMR/R, classical conditions, Z_POW and other gates are barriers.

A local identity certificate does NOT imply the full circuit has been natively
verified; the resulting KMB must be emitted, independently checked and scored.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, mmap, os, struct, time
from dataclasses import dataclass
from pathlib import Path

MAGIC = bytes.fromhex('d750c7d5c329d326e3cc9f6834f2b8bf')
HDR = struct.Struct('<16s4I9Q'); PKT = struct.Struct('<QQ'); U32=struct.Struct('<I')
# Unconditional gate opcodes; all remaining operations are hard barriers.
GATES = {0x11:'x',0x21:'cx',0x31:'ccx',0x10:'z',0x20:'cz',0x30:'ccz'}
ARITY = {'x':1,'cx':2,'ccx':3,'z':1,'cz':2,'ccz':3}

@dataclass(frozen=True)
class Op:
    idx:int
    name:str
    qubits:tuple[int,...]
    def to_json(self): return {'idx':self.idx,'op':self.name,'q':list(self.qubits)}

class KMB:
    def __init__(self,p:Path):
        self.p=p; self.f=p.open('rb'); self.mm=mmap.mmap(self.f.fileno(),0,access=mmap.ACCESS_READ)
        h=HDR.unpack_from(self.mm,0)
        if h[0]!=MAGIC or h[1]!=2: raise ValueError('not KickMix v2')
        self.q=h[2]; self.nops=h[5]; self.original_sha256=None
        offset=HDR.size
        for _ in range(h[4]):
            kind,n=PKT.unpack_from(self.mm,offset)
            if kind!=0:raise ValueError('bad register packet')
            offset+=PKT.size+n
        self.packets={}
        for kind in range(1,12):
            k,n=PKT.unpack_from(self.mm,offset)
            if k!=kind:raise ValueError('bad packet order')
            self.packets[kind]=(offset+PKT.size,n)
            offset+=PKT.size+n
        if offset!=len(self.mm):raise ValueError('extra bytes')
        if self.packets[1][1]!=self.nops:raise ValueError('opcode length')
    def close(self):self.mm.close();self.f.close()
    def sha(self):
        if self.original_sha256 is None:
            h=hashlib.sha256();self.mm.seek(0)
            for i in range(0,len(self.mm),1<<20):h.update(self.mm[i:i+(1<<20)])
            self.original_sha256=h.hexdigest()
        return self.original_sha256
    def ops(self,max_ops,start=0):
        offset=self.packets[1][0];p={k:0 for k in range(2,11)}
        if start:
            prior=self.mm[offset:offset+start]
            # C-speed 256-byte maps; qubit ranks are the same in all arity columns.
            def rank(pred):
                tbl=bytes(int(bool(pred(i))) for i in range(256))
                return prior.translate(tbl).count(1)
            c3=rank(lambda x:(x&0x30)==0x30)
            c2=rank(lambda x:(x&0x30)==0x20)
            c1=rank(lambda x:(x&0x30)==0x10)
            for k in (2,3,4):p[k]=c3
            for k in (5,6):p[k]=c2
            p[7]=c1
            p[8]=rank(lambda x:x&0x40)
            p[9]=rank(lambda x:x&0x80)
            p[10]=rank(lambda x:(x&0x7F)==0x13)
        for j in range(start,min(start+max_ops,self.nops)):

            opcode=self.mm[offset+j];a=(opcode&0x30)>>4
            q=[]
            cols={0:(),1:(7,),2:(5,6),3:(2,3,4)}[a]
            for k in cols:
                off=self.packets[k][0]+p[k]*4;q.append(U32.unpack_from(self.mm,off)[0]);p[k]+=1
            if opcode&0x40:p[8]+=1
            if opcode&0x80:p[9]+=1
            if opcode&0x7f==0x13:p[10]+=1
            name=GATES.get(opcode,'barrier')
            yield Op(j,name,tuple(q))


def eval_ops(ops:list[Op],controls:list[int]):
    idx={q:i for i,q in enumerate(controls)};n=len(controls)
    result=[]
    for word in range(1<<n):
        s=word;phase=0
        for op in ops:
            q=[idx[i] for i in op.qubits];v=[(s>>j)&1 for j in q]
            if op.name=='x':s^=1<<q[0]
            elif op.name=='cx':s^=(v[0]<<q[1])
            elif op.name=='ccx':s^=((v[0]&v[1])<<q[2])
            elif op.name=='z':phase^=v[0]
            elif op.name=='cz':phase^=v[0]&v[1]
            elif op.name=='ccz':phase^=v[0]&v[1]&v[2]
            else:raise ValueError(op)
        result.append((s,phase))
    return result

def template(a:Op,b:Op):
    if a.name!='ccx' or b.name!='ccx':return []
    ac,bc,at=a.qubits[:2],b.qubits[:2],a.qubits[2]
    bt=b.qubits[2];out=[]
    if set(ac)==set(bc) and at!=bt and at not in bc and bt not in ac:
        out.append(('shared_controls',[( 'cx',(at,bt)),('ccx',(*ac,at)),('cx',(at,bt))]))
        out.append(('shared_controls_reversed',[( 'cx',(bt,at)),('ccx',(*ac,bt)),('cx',(bt,at))]))
    if at==bt and len(set(ac).intersection(bc))==1:
        common=next(iter(set(ac).intersection(bc)))
        p=next(x for x in ac if x!=common);q=next(x for x in bc if x!=common)
        if len({common,p,q,at})==4:
            out.append(('shared_factor', [('cx',(p,q)),('ccx',(common,q,at)),('cx',(p,q))]))
            out.append(('shared_factor_reversed', [('cx',(q,p)),('ccx',(common,p,at)),('cx',(q,p))]))
    return out

def cand_to_ops(idx,ops):return [Op(idx+i,n,tuple(q)) for i,(n,q) in enumerate(ops)]

def commute_ccx_and(op:Op,g:Op)->bool:
    # Sufficient syntactic rule, for arbitrary basis/phase state.
    if op.name!='ccx':return False
    a,b,t=op.qubits
    if g.name=='x':return g.qubits[0] not in (a,b)
    if g.name in ('cx','ccx'):
        return g.qubits[-1] not in (a,b) and t not in g.qubits[:-1]
    if g.name in ('z','cz','ccz'):
        return t not in g.qubits
    return False

def find(kmb:KMB,max_ops:int,window:int=24,max_support:int=6,max_hits:int=20,start:int=0):
    recent=collections.deque();tried=collections.Counter();hits=[]
    ccx=0;seen=0
    for op in kmb.ops(max_ops,start):
        seen+=1
        if op.name=='barrier':recent.clear();continue
        while recent and op.idx-recent[0].idx>window:recent.popleft()
        if op.name=='ccx':
            ccx+=1
            for ii,a in enumerate(recent):
                if a.name!='ccx':continue
                cases=template(a,op)
                middle=list(recent)[ii+1:]
                old=[a]+middle+[op]
                if set(a.qubits[:2])==set(op.qubits[:2]) and a.qubits[2]==op.qubits[2]:
                    # Both endpoints are the same reversible gate. If everything
                    # between commutes with it, remove *both*, not just one.
                    if all(commute_ccx_and(a,m) for m in middle):
                        cases.append(('commuting_inverse',[]))
                    # More generally, commute across safe non-phase ops; conjugate
                    # each Z/CZ on the CCX target in place, keeping exact phases.
                    correction=[];valid=True
                    ca,cb,t=a.qubits
                    for m in middle:
                        if m.name in ('x','cx','ccx'):
                            if not commute_ccx_and(a,m):valid=False;break
                            correction.append((m.name,m.qubits))
                        elif m.name in ('z','cz','ccz'):
                            correction.append((m.name,m.qubits))
                            if t in m.qubits:
                                if m.name=='z':correction.append(('cz',(ca,cb)))
                                elif m.name=='cz':
                                    others=[x for x in m.qubits if x!=t]
                                    if not others:valid=False;break
                                    c=others[0]
                                    correction.append(('cz',(ca,cb)) if c in (ca,cb) else ('ccz',(ca,cb,c)))
                                else:valid=False;break
                        else:valid=False;break
                    if valid and any(t in m.qubits for m in middle if m.name in ('z','cz')):
                        cases.append(('phase_echo',correction))
                # A; diagonal(mid); A folds into the diagonal and its
                # conjugation correction, possibly replacing 2 CCX by one CCZ.
                if set(a.qubits)==set(op.qubits) and a.qubits[2]==op.qubits[2] and all(m.name in {'z','cz','ccz'} for m in middle):
                    ca,cb,t=a.qubits
                    corrections=[];possible=True
                    for m in middle:
                        if t not in m.qubits:continue
                        if m.name=='z':corrections.append(('cz',(ca,cb)))
                        elif m.name=='cz':
                            other=next(q for q in m.qubits if q!=t)
                            if other in (ca,cb):corrections.append(('cz',(ca,cb)))
                            else:corrections.append(('ccz',(ca,cb,other)))
                        else:possible=False;break
                    if possible: cases.append(('diagonal_conjugation', [('z',(ca,))]))  # placeholder, handled separately below
                if not cases:continue
                support=sorted(set(q for g in old for q in g.qubits))
                if len(support)>max_support:
                    tried['support_rejected']+=1;continue
                oldres=eval_ops(old,support)
                for rule,tmpl in cases:
                    if rule=='diagonal_conjugation':
                        replacements=[('phase',middle+cand_to_ops(a.idx,corrections))]
                    elif rule=='commuting_inverse':
                        replacements=[('cancel',middle)]
                    elif rule=='phase_echo':
                        replacements=[('conjugate',cand_to_ops(a.idx,tmpl))]
                    else:
                        replacements=[('left',cand_to_ops(a.idx,tmpl)+middle),('right',middle+cand_to_ops(a.idx,tmpl))]
                    for pos,new in replacements:
                        tried['checked']+=1
                        if eval_ops(new,support)!=oldres:continue
                        tried['pass']+=1
                        # Need exact boundaries (the entire original range must be consecutive).
                        if op.idx-a.idx+1!=len(old):
                            tried['nonconsecutive']+=1;continue
                        def cost(ops):return sum(g.name in ('ccx','ccz') for g in ops)
                        savings=cost(old)-cost(new)
                        if savings<=0:
                            tried['nonpositive_tof_saving']+=1;continue
                        hits.append(dict(rule=rule,placement=pos,begin=a.idx,end=op.idx+1,
                            before=[g.to_json() for g in old],after=[g.to_json() for g in new],
                            active_qubits=support,saved_nonclifford=savings,delta_cx=sum(g.name=='cx' for g in new)-sum(g.name=='cx' for g in old)))
                        if len(hits)>=max_hits:return {'scanned_ops':seen,'scanned_ccx':ccx,'counters':dict(tried),'hits':hits}
        recent.append(op)
    return {'scanned_ops':seen,'scanned_ccx':ccx,'counters':dict(tried),'hits':hits}

def lean_source(hit):
    wires=hit['active_qubits']; windex={q:i for i,q in enumerate(wires)}; n=len(wires)
    if n>6:raise ValueError('lean proof size cap exceeded')
    def expr(op):
        name=op['op'];args=' '.join(str(windex[i]) for i in op['q']);return f'Gate.{name} {args}'
    old=', '.join(expr(o) for o in hit['before']);new=', '.join(expr(o) for o in hit['after'])
    names=[f'x{i}' for i in range(n)];var=' '.join(names)
    cases=' <;> '.join('cases '+x for x in names)+' <;> decide'
    return f'''import GVQCCMicro
namespace GVQCCLean
private def original : List Gate := [{old}]
private def candidate : List Gate := [{new}]
-- Full arbitrary-input state AND phase equivalence (not just legal addresses).
theorem candidate_exact ({var} : Bool) :
  run original (init [{', '.join(names)}]) = run candidate (init [{', '.join(names)}]) := by
  {cases}

theorem candidate_cost_reduction : nonCliffordCost original = nonCliffordCost candidate + {hit['saved_nonclifford']} := by
  decide
end GVQCCLean
'''

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--task',choices=['dqi','invsqrt','angle'],required=True)
    p.add_argument('--kmb',type=Path,required=True)
    p.add_argument('--max-ops',type=int,default=150000)
    p.add_argument('--start',type=int,default=0)
    p.add_argument('--window',type=int,default=24)
    p.add_argument('--max-support',type=int,default=6)
    p.add_argument('--max-hits',type=int,default=20)
    p.add_argument('--out-dir',type=Path,required=True)
    a=p.parse_args();t=time.monotonic()
    k=KMB(a.kmb)
    try:
        result=find(k,a.max_ops,a.window,a.max_support,a.max_hits,a.start)
        result.update(task=a.task,path=str(a.kmb),sha256=k.sha(),nops=k.nops,qubits=k.q,start=a.start,
                      seconds=round(time.monotonic()-t,3),formal_status='Lean certificates emitted only; must run lake build')
    finally:k.close()
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/(a.task+'_scan.json')).write_text(json.dumps(result,indent=2)+'\n')
    for i,hit in enumerate(result['hits']):
        (a.out_dir/(f'{a.task}_candidate_{i:03}.lean')).write_text(lean_source(hit))
    print(json.dumps({key:result[key] for key in ['task','nops','qubits','scanned_ops','scanned_ccx','counters','seconds'] }|{'hits':len(result['hits'])},indent=2))

if __name__=='__main__':main()

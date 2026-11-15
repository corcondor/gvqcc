"""Compute the exact executed Toffoli expectation under independent HMR bits."""
import argparse
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import kickmix as km

PAID={'CCX','CCZ','CSWAP'}
BASE='684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'
BEST='4b905da1d96c805946aa79f9214a490a616b182dd8b6890956f1bf55fd857d53'

class OutcomeBDD:
    def __init__(self):
        self.nodes=[(-1,0,0),(-1,1,1)]
        self.indices={}
    def insert(self,variable,lo,hi):
        if lo==hi:
            return lo
        entry=(variable,lo,hi)
        if entry in self.indices:
            return self.indices[entry]
        code=len(self.nodes)
        self.nodes.append(entry)
        self.indices[entry]=code
        return code
    @lru_cache(maxsize=None)
    def binary(self,op,a,b):
        if max(a,b)<2:
            return a&b if op=='and' else a^b
        if a==b:
            return a if op=='and' else 0
        if a>b:
            return self.binary(op,b,a)
        if not a:
            return 0 if op=='and' else b
        if a==1 and op=='and':
            return b
        va,al,ah=self.nodes[a]
        vb,bl,bh=self.nodes[b]
        top=max(va,vb)
        if va!=top:
            al=ah=a
        if vb!=top:
            bl=bh=b
        return self.insert(top,self.binary(op,al,bl),self.binary(op,ah,bh))
    @lru_cache(maxsize=None)
    def probability(self,v):
        if v<2:
            return Fraction(v)
        _,lo,hi=self.nodes[v]
        return (self.probability(lo)+self.probability(hi))/2
    def neg(self,node):
        return self.binary('xor',node,1)
    def when(self,cond,high,low):
        yes=self.binary('and',cond,high)
        no=self.binary('and',self.neg(cond),low)
        return self.binary('xor',yes,no)

def count(path):
    bdd=OutcomeBDD()
    variables={}
    outcome=0
    conditions=[]
    active=1
    paid=Fraction(0)
    for line in str(km.Circuit.from_file(path,format='kmb')).splitlines():
        ins=line.split()
        op=ins[0]
        if op=='PUSH_CONDITION':
            conditions.append(active)
            active=bdd.binary('and',active,variables[ins[-1]])
            continue
        if op=='POP_CONDITION':
            active=conditions.pop()
            continue
        live=active
        if len(ins)>=3 and ins[-2]=='if':
            live=bdd.binary('and',live,variables[ins[-1]])
        if op=='HMR':
            key=ins[2]
            outcome+=1
            var=bdd.insert(outcome,0,1)
            variables[key]=bdd.when(live,var,variables.get(key,0))
        elif op=='BIT_STORE0':
            key=ins[1]
            variables[key]=bdd.when(live,0,variables.get(key,0))
        elif op=='BIT_INVERT':
            key=ins[1]
            variables[key]=bdd.binary('xor',live,variables.get(key,0))
        elif op in PAID:
            paid+=bdd.probability(live)
    assert not conditions
    return paid,outcome,len(bdd.nodes)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    assert sha256(args.baseline.read_bytes()).hexdigest()==BASE
    assert sha256(args.candidate.read_bytes()).hexdigest()==BEST
    a,m,n=count(args.baseline)
    b,p,q=count(args.candidate)
    assert a-b==Fraction(99,64)
    out=dict(before=str(a),after=str(b),saving=str(a-b),hmr_sites=(m,p),bdd_nodes=(n,q))
    print(out,flush=True)
    args.out.write_text(json.dumps(out,indent=2)+chr(10))

if __name__=='__main__':
    main()

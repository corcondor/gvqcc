#!/usr/bin/env python3
"""Exact-expression probe of repeated field operands across measurement gaps.

This is a conservative symbolic identity engine: fresh opaque AND atoms have
exact definitions, so equality is sufficient, while inequality is inconclusive.
Classical controls are independent symbolic bits; HMR outcomes are fresh bits.
No input distribution or scoring seed is used.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from collections import Counter
from pathlib import Path
from dqi_ccx_peephole import BinaryCircuit
import kmb_profile as kp

ZERO=frozenset(); ONE=frozenset((0,))


class Exact:
    def __init__(self,nq):
        self.q=[frozenset((i+1,)) for i in range(nq)]
        self.b={};self.next=nq+1;self.products={};self.stack=[ONE]
    def fresh(self):
        out=frozenset((self.next,));self.next+=1;return out
    def bit(self,b):
        if b not in self.b:self.b[b]=self.fresh()
        return self.b[b]
    def mul(self,a,b):
        if not a or not b:return ZERO
        if a==ONE:return b
        if b==ONE or a==b:return a
        key=tuple(sorted((a,b),key=lambda x:tuple(sorted(x))))
        if key not in self.products:self.products[key]=self.fresh()
        return self.products[key]
    def step(self,o):
        op=o.opcode&127;qs=o.qubits
        if o.opcode==0x81:
            self.stack.append(self.mul(self.stack[-1],self.bit(o.condition)));return
        if o.opcode==0x01:
            if len(self.stack)==1:raise ValueError('exits inherited condition')
            self.stack.pop();return
        guard=self.stack[-1]
        if o.condition is not None:guard=self.mul(guard,self.bit(o.condition))
        if op in (0x00,0x10,0x13,0x20,0x30):return
        if op==0x11:self.q[qs[0]]^=guard
        elif op==0x21:self.q[qs[1]]^=self.mul(guard,self.q[qs[0]])
        elif op==0x31:self.q[qs[2]]^=self.mul(guard,self.mul(self.q[qs[0]],self.q[qs[1]]))
        elif op in (0x22,0x32):
            if op==0x32:guard=self.mul(guard,self.q[qs[0]])
            a,b=qs[-2:];v=self.mul(guard,self.q[a]^self.q[b]);self.q[a]^=v;self.q[b]^=v
        elif op in (0x12,0x50):
            if op==0x50:
                self.b[o.bit]=self.bit(o.bit)^self.mul(guard,self.bit(o.bit)^self.fresh())
            self.q[qs[0]]^=self.mul(guard,self.q[qs[0]])
        elif op in (0x40,0x41,0x42):
            before=self.bit(o.bit)
            after=ZERO if op==0x40 else ONE if op==0x41 else before^ONE
            self.b[o.bit]=before^self.mul(guard,before^after)
        else:raise ValueError(f'unsupported opcode {o.opcode:x}')


def blocks(repo,shift):
    cert=json.loads((repo/'inverse_v2_actual_eea_product_certificate.json').read_text())
    allblocks=json.loads((repo/'theory_bilinear_full_build.json').read_text())['blocks']
    rows=[]
    for row in allblocks:
        mapping={int(k):v for k,v in row['wire_mapping'].items()}
        if row['template']=='gf12_multiplication':
            kind='gf12';left=range(12);right=range(12,24);target=range(24,36)
        elif row['template']=='gf24_multiplication':
            kind='gf24';left=cert['input_left'];right=cert['input_right'];target=cert['output_qubits_in_field_order']
        else:raise ValueError(row['template'])
        rows.append(dict(kind=kind,start=row['start']+shift,end=row['end']+shift,
                         left=[mapping[x] for x in left],right=[mapping[x] for x in right],
                         target=[mapping[x] for x in target],depth=row['inherited_condition_stack_depth']))
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-gap',type=int,default=20000);args=p.parse_args();began=time.monotonic()
    repo=Path(__file__).parent
    prof=kp.profile(args.input,max_register_summaries=0)
    assert prof['raw_kmb_sha256']=='9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1'
    (args.out.with_suffix('.profile.json')).write_text(json.dumps(prof,indent=2)+'\n')
    c=BinaryCircuit(args.input,prof);rows=blocks(repo,-529949)
    counters=Counter();matches=[];examples=[]
    for a,b in zip(rows,rows[1:]):
        if a['kind']!=b['kind']:continue
        regset=lambda x:{tuple(x['left']),tuple(x['right'])}
        if regset(a)!=regset(b):continue
        counters['same_input_pairs']+=1
        lo,hi=a['end'],b['start']
        if hi-lo>args.max_gap:counters['too_long']+=1;continue
        if a['depth']!=b['depth']:counters['different_depth']+=1;continue
        ops=list(c.operations(lo,hi));s=Exact(prof['header']['num_qubits']);entry=s.q[:]
        try:
            for o in ops:s.step(o)
        except ValueError as ex:
            counters[str(ex)]+=1;continue
        if len(s.stack)!=1:counters['stack_not_restored']+=1;continue
        controls=a['left']+a['right']
        same=[q for q in controls if s.q[q]==entry[q]]
        counters['symbolically_checked']+=1
        if len(same)==len(controls):
            counters['all_inputs_formally_return']+=1
            rec=dict(first=a,second=b,gap_ops=hi-lo,gap_families=dict(Counter(kp.OPCODES[o.opcode] for o in ops)))
            matches.append(rec);print(json.dumps(dict(event='same_operand_return',first=a['start'],second=b['start'],gap=hi-lo)),flush=True)
        elif len(examples)<8:examples.append(dict(first=a['start'],second=b['start'],same=len(same),inputs=len(controls),gap=hi-lo))
    c.close();result=dict(status='COMPLETE',input_sha256=prof['raw_kmb_sha256'],counts=dict(counters),matches=matches,examples=examples,seconds=time.monotonic()-began,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(counts=result['counts'],seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()

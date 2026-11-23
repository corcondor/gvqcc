#!/usr/bin/env python3
"""Exact small-circuit regressions for all three relation optimizations."""
from itertools import product
from reachable_multioutput import optimize_text,parse_kmx,apply,pack,insert,reduce
import unittest


def prepare(lines,inputs,data):
    text='\n'.join(lines)+'\n'
    n=max(int(x[1:]) for line in lines for x in line.split()[1:])+1
    return text,[pack(bits[i] for bits in inputs) for i in range(n)], (1<<len(inputs))-1,data


def check(old, new, patterns):
    _,before=parse_kmx(old)
    _,after=parse_kmx(new)
    for row in patterns:
        x=list(row);y=list(row)
        for _,gate in before:
            a=[v<<0 for v in x]
            x=[v for v in x]
            apply(x,gate,1)
        for _,gate in after:
            apply(y,gate,1)
        assert x==y,(row,x,y)


class RelationalTests(unittest.TestCase):
    def test_exact_three_to_two_directions(self):
        old=['CCX q0 q1 q3', 'CCX q0 q2 q4',
             'CX q3 q4', 'CCX q1 q2 q3','CX q3 q4']
        states=list(product((0,1),repeat=5))
        text,init,ones,data=prepare(old,states,(3,4))
        new,receipt=optimize_text(text,init,ones,data)
        self.assertEqual(receipt['derived_ccx_saving'],1)
        self.assertEqual(new.count('CCX'),2)
        check(text,new,states)

    def test_five_tag_reachable_only(self):
        def tags(a0,a1,a2,a3):
            return (a0&a1,a0&a2,a1&a2,a0&a3,a1&a3)
        old=['CCX q0 q1 q5','CCX q1 q2 q6']
        states=[tags(*a)+(x,y) for a in product((0,1),repeat=4)
                              for x,y in product((0,1),repeat=2)]
        text,init,ones,data=prepare(old,states,(5,6))
        new,receipt=optimize_text(text,init,ones,data)
        self.assertEqual(receipt['derived_ccx_saving'],1)
        self.assertEqual(new.count('CCX'),1)
        check(text,new,states)
        # Rule is *not* an unconditional 5-bit identity. Exactly 64/128
        # full control+target states fail; detector requires a domain witness.
        all_states=list(product((0,1),repeat=7))
        bad=0
        _,p=parse_kmx(text);_,q=parse_kmx(new)
        for s in all_states:
            st=list(s);tt=list(s)
            for _,g in p:apply(st,g,1)
            for _,g in q:apply(tt,g,1)
            bad += st!=tt
        self.assertGreater(bad,0)

    def test_free_product_zero(self):
        # Reachable condition c=a&b, so CCX(a,b,target) is a CNOT.
        old=['CCX q0 q1 q3','CX q2 q4','CCX q0 q2 q4']
        states=[(a,b,a&b,y,z) for a,b,y,z in product((0,1),repeat=4)]
        text,init,ones,data=prepare(old,states,(3,4))
        new,r=optimize_text(text,init,ones,data)
        self.assertGreaterEqual(r['derived_ccx_saving'],1)
        check(text,new,states)

    def test_counterexample_blocks_bad_relation(self):
        old=['CCX q0 q1 q3','CCX q1 q2 q4']
        states=list(product((0,1),repeat=5))
        text,init,ones,data=prepare(old,states,(3,4))
        new,r=optimize_text(text,init,ones,data)
        self.assertEqual(r['derived_ccx_saving'],0)
        self.assertEqual(text,new)

if __name__=='__main__':unittest.main(verbosity=2)
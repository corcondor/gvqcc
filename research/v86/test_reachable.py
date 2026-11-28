#!/usr/bin/env python3
"""Independent exhaustive Boolean replay of emitted substitutions."""
import itertools
import random
import unittest
from reachable import Domain

def parity(mask, x):
    return ((mask >> 1 & x).bit_count() ^ (mask & 1)) & 1

class Tests(unittest.TestCase):
    def test_all_affine_products(self):
        # All affine forms in four variables; independently evaluate the
        # canonical cached nonlinear symbol as its defining product.
        d = Domain(4, range(4))
        for a,b in itertools.product(range(32), repeat=2):
            p, _ = d.product(a,b)
            for x in range(16):
                vals = x
                for (u,v), symbol in d.cache.items():
                    vals |= (parity(u,x)&parity(v,x)) << (symbol.bit_length()-2)
                self.assertEqual(parity(p,vals), parity(a,x)&parity(b,x))

    def test_real_gate_sequence(self):
        # 2 CCX -> 1, with both arbitrary inputs and an arbitrary accumulator.
        d = Domain(5, [0,1,4])
        gates = [(0x31,0,1,2),(0x21,0,1,-1),
                 (0x31,0,1,4),(0x21,0,1,-1)]
        reps = [d.step(*g) for g in gates]
        self.assertIsNone(reps[0][0])
        # (a+b)*a = a*b+a; the prior product lives on wire 2.
        self.assertEqual(set(reps[2][0][1]), {0,2})
        self.assertEqual(reps[2][0][0],0)
        self.assertEqual(d.stats["CCX_removed_cached"],1)
        for x in range(8):
            a,b,z = [(x>>i)&1 for i in range(3)]
            self.assertEqual(z ^ (a & (a^b)), z ^ (a&b) ^ a)

    def test_bilinear_span(self):
        d = Domain(7, [0,1,2,6])
        d.step(0x31,0,1,3)
        d.step(0x31,0,2,4)
        d.step(0x21,1,2)
        rep, kind = d.step(0x31,0,2,6)
        self.assertEqual(kind, "dependent")
        self.assertEqual(rep[0], 0)
        self.assertEqual(set(rep[1]), {3,4})
        # A cached product distributed across three live rows.
        d = Domain(7, [0,1,2,3])
        d.step(0x31,0,1,4)
        d.step(0x21,2,4)
        d.step(0x21,3,4)
        rep, kind = d.step(0x31,0,1,5)
        self.assertEqual(kind, "cached")
        self.assertEqual(rep[0], 0)
        self.assertEqual(set(rep[1]), {2,3,4})

    def test_branch_join_and_compaction(self):
        d = Domain(6, [0,1])
        d.step(0x31,0,1,2)
        d.push()
        d.step(0x11,2)
        d.pop()
        self.assertIsNone(d.step(0x31,0,1,3)[0])
        d.step(0x50,3)
        d.step(0x21,0,3)
        d.step(0x21,1,3)
        d.compact()
        self.assertEqual(d.rows[3],d.rows[0]^d.rows[1])

    def test_random_guarded_circuits(self):
        rng=random.Random(861)
        # Exhaustively compare all 4 input bits and 4 independent guard bits.
        for _ in range(30):
            d=Domain(8, range(4), limit=28)
            seq=[]
            depth=0
            for i in range(120):
                t=rng.choice([0x21,0x21,0x31,0x31,0x11,0x50,0x22,0x32,0x81,1])
                if t==1 and not depth:t=0x31
                if t==0x81 and depth>=2:t=0x31
                if t==0x81:depth+=1
                if t==1:depth-=1
                a,b,c=rng.sample(range(8),3)
                if t not in (1,0x81) and rng.randrange(3)==0:t|=128
                g=rng.randrange(4)
                ans=d.step(t,a,b,c)
                seq.append((t,a,b,c,g,ans[0] if ans is not None else None))
            while depth:
                d.step(1);seq.append((1,0,0,0,0,None));depth-=1
            for x in range(16):
                for guards in range(16):
                    q=[(x>>i)&1 for i in range(8)]
                    z=q[:];active=[True]
                    for t,a,b,c,g,rep in seq:
                        if t==0x81:
                            active.append(active[-1] and bool(guards>>g&1));continue
                        if t==1:
                            active.pop();continue
                        if not active[-1] or (t&128 and not guards>>g&1):continue
                        op=t&127
                        for w,replace in ((q,False),(z,True)):
                            if op==0x21:w[b]^=w[a]
                            elif op==0x11:w[a]^=1
                            elif op==0x50:w[a]=0
                            elif op==0x22:w[a],w[b]=w[b],w[a]
                            elif op==0x32:
                                if w[a]:w[b],w[c]=w[c],w[b]
                            elif op==0x31:
                                if replace and rep is not None:
                                    k,cs=rep
                                    for j in cs:k^=w[j]
                                    w[c]^=k
                                else:w[c]^=w[a]&w[b]
                        self.assertEqual(q,z)
if __name__=="__main__":
    unittest.main()

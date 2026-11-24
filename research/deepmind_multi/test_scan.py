"""Exhaustive positive/negative regression for the multi-task KMB/Lean bridge."""
import json, tempfile, struct, unittest
from pathlib import Path
from scan import KMB, Op, eval_ops, find, lean_source, MAGIC, HDR, PKT, GATES

# Deliberately independent tiny KMB v2 writer, NOT used in production.
R = {v:k for k,v in GATES.items()}
C = {1:(7,),2:(5,6),3:(2,3,4)}

def fixture(ops):
    b={i:bytearray() for i in range(1,12)}
    for op in ops:
        code=R.get(op.name,0x50)
        b[1].append(code)
        for col,q in zip(C.get((code&0x30)>>4,()),op.qubits):
            b[col].extend(struct.pack('<I',q))
    n3=len(b[2])//4;n2=len(b[5])//4;n1=len(b[7])//4
    nqs=1+max((q for op in ops for q in op.qubits),default=0)
    data=bytearray(HDR.pack(MAGIC,2,nqs,0,0,len(ops),n3,n2,n1,0,0,0,0,0))
    for kind in range(1,12):
        if kind==11:b[kind].extend(struct.pack('<Q',0))
        data+=PKT.pack(kind,len(b[kind]));data+=b[kind]
    return bytes(data)

def op(name,*q):return Op(0,name,q)

class ExactTests(unittest.TestCase):
    def test_phase_echo_and_cost(self):
        for mid,expected in [([op('z',2)],2),([op('cz',2,3)],1)]:
            seq=[op('ccx',0,1,2),*mid,op('ccx',0,1,2)]
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'t.kmb';p.write_bytes(fixture(seq))
                k=KMB(p)
                try:r=find(k,30,window=20,max_support=6)
                finally:k.close()
            hits=[x for x in r['hits'] if x['rule']=='phase_echo']
            self.assertTrue(hits)
            h=hits[0];self.assertEqual(h['saved_nonclifford'],expected)
            self.assertIn('theorem candidate_exact',lean_source(h))
            self.assertIn('candidate_cost_reduction',lean_source(h))
    def test_cross_target(self):
        self.find_saved([op('ccx',0,1,2),op('ccx',0,1,3)],1)
    def test_shared_factor(self):
        self.find_saved([op('ccx',0,1,3),op('ccx',0,2,3)],1)
    def test_commuting_cancellation(self):
        self.find_saved([op('ccx',0,1,2),op('x',3),op('ccx',0,1,2)],2)
    def test_classical_phases_preserved(self):
        old=[op('ccx',0,1,2),op('cz',2,3),op('ccx',0,1,2)]
        new=[op('cz',2,3),op('ccz',0,1,3)]
        self.assertEqual(eval_ops(old,list(range(4))),eval_ops(new,list(range(4))))
        self.assertNotEqual(eval_ops(old,list(range(4))),eval_ops([op('cz',2,3)],list(range(4))))
    def test_negative_noncommuting(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.kmb';p.write_bytes(fixture([op('ccx',0,1,2),op('cx',2,0),op('ccx',0,1,2)]))
            k=KMB(p)
            try:r=find(k,30,window=20,max_support=6)
            finally:k.close()
        self.assertFalse(r['hits'])
    def test_native_kmb_emission(self):
        from emit import emit
        seq=[op('ccx',0,1,2),op('cz',2,3),op('ccx',0,1,2)]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'original.kmb';q=Path(tmp)/'candidate.kmb'
            p.write_bytes(fixture(seq));original=p.read_bytes()
            k=KMB(p)
            try:r=find(k,30)
            finally:k.close()
            hit=next(h for h in r['hits'] if h['rule']=='phase_echo')
            receipt=emit(p,hit,q)
            self.assertEqual(p.read_bytes(),original)
            self.assertEqual(receipt['saved_nonclifford'],1)
            self.assertEqual(receipt['source_qubits'],receipt['output_qubits'])
            emitted=KMB(q)
            try:decoded=list(emitted.ops(40))
            finally:emitted.close()
            self.assertEqual(eval_ops(seq,list(range(4))),eval_ops(decoded,list(range(4))))
            with self.assertRaises(FileExistsError):emit(p,hit,q)

    def test_midstream_column_rank(self):
        seq=[op('cx',0,2),op('x',1),op('ccx',0,1,2),op('z',2),op('ccx',0,1,2)]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'start.kmb';p.write_bytes(fixture(seq))
            k=KMB(p)
            try:r=find(k,3,start=2,window=20)
            finally:k.close()
        self.assertTrue(any(h['rule']=='phase_echo' for h in r['hits']))
    def find_saved(self,seq,saving):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'t.kmb';p.write_bytes(fixture(seq))
            k=KMB(p)
            try:r=find(k,40,window=20,max_support=6)
            finally:k.close()
        self.assertTrue(any(h['saved_nonclifford']==saving for h in r['hits']),r)

if __name__=='__main__':unittest.main(verbosity=2)

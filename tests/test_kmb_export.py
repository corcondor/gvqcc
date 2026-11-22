"""Smoke-test KMB-v2 round-trip header and operation-class counts.

Full byte-stream independently parsed in the reproducibility bundle via
qhdl_kmb.py; native KickMix execution is a separate uncompleted gate.
"""
import struct
import unittest

from griffith_qcc.kmb_export import encode_kmb, MAGIC
from griffith_qcc.reversible_blocks import add_three_mod, csa_three


class KmbArithmeticExportTest(unittest.TestCase):
    def test_header_counts(self):
        for n in range(1,6):
            for make in (add_three_mod,csa_three):
                gates,regs=make(n)
                result=encode_kmb(gates,regs)
                self.assertEqual(result[:16],MAGIC)
                ver,nq,nb,nregs=struct.unpack_from("<4I",result,16)
                self.assertEqual(ver,2)
                self.assertEqual(nq,max(max(v) for v in regs.values())+1)
                self.assertEqual(nb,0)
                self.assertEqual(nregs,len(regs))
                ct=struct.unpack_from("<9Q",result,32)
                self.assertEqual(ct[0],len(gates))
                self.assertEqual(ct[1],sum(g[0]=="CCX" for g in gates))
                self.assertEqual(ct[2],sum(g[0]=="CX" for g in gates))

    def test_fails_closed(self):
        with self.assertRaises(ValueError):
            encode_kmb([("HMR",0,1)],{"a":[0]})
        with self.assertRaises(ValueError):
            encode_kmb([("Z_POW",0,0.25)],{"a":[0]})


if __name__=="__main__":
    unittest.main()

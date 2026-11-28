"""Source-independent regression for nonlinear register lending, arbitrary phase."""
import itertools, unittest
from build_prefix36 import toggle_cached_predicate


def do_gates(state, gates):
    s=list(state)
    for g in gates:
        op,w=g.raw,g.wires
        if op==0x11:s[w[0]]^=1
        elif op==0x21:s[w[1]]^=s[w[0]]
        elif op==0x31:s[w[2]]^=s[w[0]]&s[w[1]]
        else:raise AssertionError(op)
    return s

class LoanTests(unittest.TestCase):
    def test_clear_and_reconstruct_exhaustive(self):
        gate=toggle_cached_predicate()
        self.assertEqual(sum(g.raw==0x31 for g in gate),1)
        for a,b,c,guest in itertools.product((0,1),repeat=4):
            s=[0]*37
            s[2],s[19],s[34],s[36]=a,b,c,guest
            s[22]=(not b) and (not (a^c))
            s[22]=int(s[22])
            cleared=do_gates(s,gate)
            self.assertEqual(cleared[22],0)
            self.assertEqual([cleared[x] for x in (2,19,34)],[a,b,c])
            # Arbitrary classical measurement outcome: old and new phase
            # exponent m AND measured bit are identical when guest is mapped.
            for m in (0,1):
                oldphase=m&guest
                borrowed=cleared.copy();borrowed[22]^=guest
                self.assertEqual(oldphase,m&borrowed[22])
                borrowed[22]=0
                restored=do_gates(borrowed,gate)
                self.assertEqual(restored[:36],s[:36])

if __name__=='__main__':unittest.main()

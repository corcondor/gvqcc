import unittest
from griffith_qcc.train import train_xag

class TestTrain(unittest.TestCase):
    def test_shared_gate_warmstart_and_hard_proof(self):
        try:import torch
        except ImportError:self.skipTest('Optional torch missing')
        targets=[]
        for j in range(2):
            f=0
            for a in range(8):
                v=((a&1)&((a>>1)&1)) ^ (((a>>2)&1) if j else 0)
                f|=v<<a
            targets.append(f)
        c,report=train_xag(targets,num_inputs=3,products=1,trials=2,steps=10,seed=17)
        self.assertEqual(report['status'],'EXACT')
        self.assertIsNotNone(c)
        c.assert_exact(targets)

if __name__=='__main__':unittest.main()

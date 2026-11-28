import unittest
import numpy as np
from rank_e2_lbfgs import E2GramOracle

class TestE2Oracle(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(17)
        r,b,c=2,5,3
        v=rng.normal(size=(r,b,9))
        w0=rng.normal(size=(r,b,c))*0.01
        class F:pass
        m=F();m.G4=np.einsum("rik,sjk->rsij",v,v)
        m.P0=w0@w0.transpose(0,2,1)
        a=rng.normal(size=(r,b,b))
        m.A=(a+a.transpose(0,2,1))/2;m.e20=1.0
        self.o=E2GramOracle(m);self.w=w0
    def test_analytic_gradient(self):
        rng=np.random.default_rng(23)
        w=self.w+0.015*rng.normal(size=self.w.shape)
        d=rng.normal(size=w.shape);d/=np.linalg.norm(d)
        h=1e-5
        value,grad=self.o.loss_and_gradient(w)
        fd=(self.o.loss_and_gradient(w+h*d)[0]-self.o.loss_and_gradient(w-h*d)[0])/(2*h)
        self.assertAlmostEqual(fd,float(np.sum(grad*d)),delta=2e-9)
    def test_lbfgs_never_exceeds_start(self):
        w=self.w+0.03
        initial,_=self.o.loss_and_gradient(w)
        fitted,log=self.o.minimize(w,iterations=60,seconds=5)
        final,_=self.o.loss_and_gradient(fitted)
        self.assertLessEqual(final,initial+1e-9)
        self.assertIsInstance(log["error2"],float)
    def test_shape_guard(self):
        with self.assertRaises(ValueError):
            self.o.loss_and_gradient(np.zeros((2,4,3)))

if __name__=="__main__":unittest.main()

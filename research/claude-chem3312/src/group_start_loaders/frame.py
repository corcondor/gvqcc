# Frame data for a head loader: low bits X (3), high bits Y (8), care structure, mixed columns.
import numpy as np, itertools
from common import *
words = K.load_words()
A = np.arange(1219)
TAGS = [(0,1),(0,2),(1,2),(0,3),(1,3)]
def delta_bits(k, w=None):
    w = words if w is None else w
    new = w[:,5*k:5*k+5]
    old = w[:,5*(k-1):5*(k-1)+5] if k else np.zeros_like(new)
    d = new ^ old
    return np.stack([((d[:,j]>>b)&1) for j in range(5) for b in range(6)]).astype(np.uint8)  # (30, 1219)

class Frame:
    def __init__(self, k, X=(4,5,6), w=None):
        self.k = k; self.X = list(X); self.Y = [b for b in range(11) if b not in X]
        D = delta_bits(k, w); self.D = D
        xv = np.zeros(1219,int); yv = np.zeros(1219,int)
        for i,b in enumerate(self.X): xv |= ((A>>b)&1)<<i
        for i,b in enumerate(self.Y): yv |= ((A>>b)&1)<<i
        self.nx = 1 << len(self.X)
        ys, inv = np.unique(yv, return_inverse=True)
        self.yval = ys; self.ny = len(ys); self.yidx = inv
        G = -np.ones((self.nx, self.ny), int); G[xv, inv] = A; self.G = G
        self.xv, self.yv = xv, yv
        self.care = G >= 0
        assert self.care[0].all()
        self.carex = [tuple(np.nonzero(self.care[:,y])[0].tolist()) for y in range(self.ny)]
        self.full = [y for y in range(self.ny) if len(self.carex[y]) == self.nx]
        GG = np.where(self.care, G, 0)
        self.Dg = D[:, GG] * self.care[None,:,:]     # (30, nx, ny)
        # y bit functions and tag functions on the ny columns
        yfull = ys
        self.ybits = np.array([((yfull >> i) & 1) for i in range(len(self.Y))], np.uint8)
        # address bit functions on columns (for bits in Y)
        def addrbit(b):
            return np.array([(self.yval[y] >> self.Y.index(b)) & 1 for y in range(self.ny)], np.uint8)
        self.tags_hi = [t for t in TAGS if t[0] in self.Y and t[1] in self.Y] if k else []
        self.tags_lo = [t for t in TAGS if t[0] in self.X and t[1] in self.X] if k else []
        self.tagf = [addrbit(i) & addrbit(j) for i,j in self.tags_hi]
        # anchor column: y index 0 (value 0)
        assert self.yval[0] == 0
        # normalised mixed part: N(o,x,y) = D(x,y)+D(0,y)+D(x,0)+D(0,0), x=1..nx-1
        Dg = self.Dg
        N = (Dg[:,1:,:] ^ Dg[:,:1,:] ^ Dg[:,1:,:1] ^ Dg[:,:1,:1]) & self.care[None,1:,:]
        self.N = N       # (30, nx-1, ny)
        self.NX = self.nx - 1
    def col_int(self, y, xs=None):
        # 30*(nx-1)-bit int, bit o*NX + (x-1)
        v = self.N[:,:,y].reshape(-1)
        return int.from_bytes(np.packbits(v, bitorder='little').tobytes(), 'little')
    def care_mask(self, y):
        m = 0
        for o in range(30):
            for x in self.carex[y]:
                if x: m |= 1 << (o*self.NX + x - 1)
        return m

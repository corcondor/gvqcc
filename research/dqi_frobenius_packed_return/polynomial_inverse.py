"""In-place polynomial reciprocal via reversed Euclidean continuants.
Fixed degree charts, no host selection on data. All source polynomial words
are recycled. No separate Bezout bank. Scalar normalization is computed once
at the packed boundary and the same reciprocal is shared across all quotients.
"""
import json,random,hashlib
from pathlib import Path
import numpy as np
import kickmix as km
from packed_quotient import Packed, inverse_ops, emit, mul, inv, bits
from reference_solve import add, mul as pmul, rem, egcd, scale
DIR=Path(__file__).parent

class Continuant(Packed):
    def divide_pack(self,X,Y):
        n,k=len(X)-1,len(Y)-1
        assert n>k>=0
        l=Y[-1];r=self.work[0]
        self.inverse_add(l,r)
        for j in range(n,k-1,-1):
            self.word_scale(X[j],r,l)
            for i in range(k):self.madd(X[j],Y[i],X[j-k+i])
        self.inverse_add(l,r)
    def unpack(self,X,Y):
        s=len(self.ops);self.divide_pack(X,Y)
        self.ops[s:]=list(inverse_ops(self.ops[s:]))
    def permute(self,src,dst):
        assert len(src)==len(dst) and set(src)==set(dst)
        # Move values at src[i] into dst[i]; all words are disjoint.
        cur=list(dst);want=list(src)
        for i,w in enumerate(want):
            j=cur.index(w)
            if i!=j:self.swapword(dst[i],dst[j]);cur[i],cur[j]=cur[j],cur[i]
    def reciprocal(self,B,A,profile):
        n=len(B)-1;assert len(A)==n and profile[-1]==0
        assert 0<=profile[0]<n
        qs=[];zeros=list(A[profile[0]+1:])
        X=list(B);Y=list(A[:profile[0]+1])
        for i,k in enumerate(profile):
            assert len(Y)==k+1
            self.divide_pack(X,Y)
            qs.append(X[k:]);R=X[:k]
            if not k:break
            kk=profile[i+1];assert 0<=kk<k
            zeros.extend(R[kk+1:]);X,Y=Y,R[:kk+1]
        g=Y[0];r=self.work[0]
        # Original product M(q0)...M(qL-1). Transpose reverses order.
        # Adjust alternating quotients by g² / g^-² so the reconstructed
        # numerator stays B and the other coordinate becomes A^-1 mod B.
        self.inverse_add(g,r)
        self.frob(g,1);self.frob(r,1)
        L=len(qs)
        for i,q in enumerate(qs):
            even=(L-1-i)%2==0
            for w in q:self.word_scale(w,g if even else r,r if even else g)
        self.frob(g,-1);self.frob(r,-1)
        self.inverse_add(g,r)
        if L%2:
            self.inverse_add(g,r);self.swapword(g,r);self.inverse_add(g,r)
        Y=[g];R=[]
        for q in qs:
            k=len(Y)-1
            assert len(R)<=k and len(zeros)>=k-len(R)
            need=k-len(R);X=R+zeros[:need]+q;zeros=zeros[need:]
            self.unpack(X,Y);R,Y=Y,X
        assert len(Y)==n+1 and len(R)+len(zeros)==n
        self.permute(Y+R+zeros,list(B)+list(A))

def make(m,profile,rng):
    Y=[rng.randrange(1,4096)];X=[]
    deg=[m]+list(profile)
    for i in range(len(deg)-2,-1,-1):
        gap=deg[i]-deg[i+1]
        q=[rng.randrange(4096) for _ in range(gap)]+[rng.randrange(1,4096)]
        X,Y=Y,add(pmul(q,Y),X)
    B=Y;A=X
    h,_,u=egcd(B,A,two=False)
    assert h==[1] and rem(pmul(A,u),B)==[1]
    return B+A+[0]*(m-len(A))+[0]*4, B+u+[0]*(m-len(u))+[0]*4

def build(m,profile,measured,rev=False):
    Q=12*(2*m+5)
    w=[tuple(range(12*i,12*i+12)) for i in range(2*m+5)]
    B=w[:m+1];A=w[m+1:2*m+1];work=w[2*m+1:]
    work=list(work)+[work[1]] # scratch for scalar multiplication shares reciprocal work
    t=Continuant(work);t.reciprocal(B,A,profile)
    b=km.CircuitBuilder();b.set_max_qubits(Q);q=list(b.create_quantum_register(Q,'W'))
    emit(b,q,inverse_ops(t.ops) if rev else t.ops,work,measured)
    return b.finish_circuit(),t
def check(m,profile,measured,rows,targets):
    c,t=build(m,profile,measured);ic,_=build(m,profile,measured,True)
    Q=12*(2*m+5);assert c.num_qubits==Q and ic.num_qubits==Q
    path=DIR/(f'continuant_m{m}_'+','.join(map(str,profile))+f'_h{int(measured)}.kmb')
    c.to_file(str(path),format='kmb');c=km.Circuit.from_file(str(path))
    def packed(r):return ((np.array(r,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(r),Q).T.astype(bool)
    A,B=packed(rows),packed(targets);q=km.array([km.q(i) for i in range(Q)])
    for seed in (7,121):
        for i in range(0,len(rows),32):
            n=min(32,len(rows)-i)
            for circ,a,b,off in ((c,A,B,0),(ic,B,A,7001)):
                s=km.Simulator(batch_size=n,seed=seed+i+off,debug_print=False,counting_operations=True)
                s.use_same_registers_as(circ);s.write_across_shots(q,a[:,i:i+n]);s.do(circ)
                assert np.array_equal(s.read_across_shots(q),b[:,i:i+n]),(m,profile,measured,off)
                assert not np.any(s.read_phase_flipped_across_shots())
    rec=dict(m=m,profile=profile,measured=measured,Q=Q,paid=int(c.operation_statistics().num_toffoli_like),ops=len(c),shots=4*len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    print(json.dumps(rec),flush=True);return rec

def main():
    rng=random.Random(3281024);out=[]
    for m,profile in [(3,[2,1,0]),(5,[3,1,0]),(8,list(range(7,-1,-1))),(17,list(range(16,-1,-1))),(17,[14,9,5,2,0])]:
        a,b=zip(*(make(m,profile,rng) for _ in range(32)))
        for measured in (False,True):out.append(check(m,profile,measured,a,b))
    (DIR/'continuant_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()

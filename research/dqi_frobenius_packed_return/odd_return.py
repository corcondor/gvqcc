"""Interleaved odd Toeplitz return: fixed-degree component, not full DQI."""
import json, random
from pathlib import Path
from functools import lru_cache
import packed_return as P
import kickmix as km

@lru_cache(None)
def schedule(n):
    if n <= 1:
        return 0, 0
    out = []
    for l in range(1,n):
        y = [sum(i%2==p for i in range(l)) for p in (0,1)]
        x = [sum(i%2==p for i in range(l,n)) for p in (0,1)]
        cost = sum(min(y[p]*x[1-p],y[p]+x[1-p]-1)
                   for p in (0,1) if y[p] and x[1-p])
        out.append((schedule(l)[0]+schedule(n-l)[0]+cost,l))
    return min(out)

class OddTape(P.Tape):
    def couple(self,t,g,h,c,blocked=True):
        w=[c]+[u for a,b in zip(g,h) for u in (a,b)]
        covered=[]
        def rec(lo,hi):
            if hi-lo<=1:return
            mid=lo+schedule(hi-lo)[1]
            rec(lo,mid)
            for p in (0,1):
                y=[i for i in range(lo,mid) if i%2==p]
                x=[i for i in range(mid,hi) if i%2!=p]
                if y and x:
                    self.toeplitz(t,[w[j] for j in x],[w[i] for i in y],
                                  (x[0]-y[0]-1)//2,-1,1,True)
                    covered.extend((i,j) for i in y for j in x)
            rec(mid,hi)
        rec(0,len(w))
        assert sorted(covered)==[(i,j) for i in range(len(w))
                                  for j in range(i+1,len(w)) if (i+j)%2]

def generate(m,blocked):
    assert blocked
    tape=OddTape();Q=12*(4*m+2)
    w=[tuple(range(12*i,12*i+12)) for i in range(4*m+2)]
    a=w[:m+1];b=w[m+1:2*m+1];g=w[2*m+1:3*m+1];h=w[3*m+1:4*m+1];c=w[-1]
    t=a[::-1][:m]
    tape.divide(t,b[::-1],True)
    end=len(tape.ops);count=tape.products
    tape.couple(t,g,h,c,True)
    tape.ops.extend(reversed(tape.ops[:end]));tape.products+=count
    assert tape.products==2*P.schedule(m)[0]+schedule(2*m+1)[0]
    assert sum(o[0]==1 for o in tape.ops)==42*tape.products
    cb=km.CircuitBuilder();cb.set_max_qubits(Q)
    qs=list(cb.create_quantum_register(Q,'W'))
    for op,*a in tape.ops:
        if op==0:cb.cx(qs[a[0]],qs[a[1]])
        else:cb.ccx(qs[a[0]],qs[a[1]],qs[a[2]])
    return tape,cb.finish_circuit()

if __name__=='__main__':
    P.check_rank42()
    original=P.generate
    rng=random.Random(316089674);out=[]
    for m in range(1,18):
        n=4*m+2
        rows=[[rng.randrange(4096) for _ in range(n)] for _ in range(126)]
        rows += [[0]*n,[4095]*n]
        rec=dict(m=m)
        for label,f in [('old',original),('odd',generate)]:
            P.generate=f
            rec[label]=P.verify(m,True,rows)
            p=Path(P.DIR)/f'return_m{m}_blocked.kmb'
            if m in (4,8,17):p.rename(p.with_name(f'return_m{m}_{label}.kmb'))
            else:p.unlink()
        assert rec['odd']['CCX']<=rec['old']['CCX']
        out.append(rec)
    assert out[-1]['old']['CCX']==10500 and out[-1]['odd']['CCX']==9954
    (P.DIR/'odd_return_receipt.json').write_text(json.dumps(out,indent=2)+'\n')

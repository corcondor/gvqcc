"""Native emitter for the fixed 59-CCX tape with an existing dirty wire.
All 11 clean scratch wires are returned. Requires s*t=1.
The archive also contains a 95-CCX no-borrow alternative.
"""
import kickmix as km
from fixed_transport import make,expand
TAPE=expand(make())
def emit(b,x,s,t,dirty):
    x,s,t=map(list,(x,s,t));data=x+s+t+[dirty]
    assert len(x)==len(s)==len(t)==12 and len(set(map(str,data)))==37
    entry=b.num_allocated_qubits;out=list(b.alloc_qubits(11));mask=list(b.alloc_bits(11));w=x+s+t+out+[dirty]
    with b.mark('uniform_scale_transport'):
        for op,*a in TAPE:
            if op=='HMR':b.hmr(w[a[0]],mask[a[1]])
            elif op=='CZ_IF':b.ccz(w[a[0]],w[a[1]],mask[a[2]])
            else:getattr(b,op.lower())(*(w[q] for q in a))
    b.free(mask);b.free(out);assert b.num_allocated_qubits==entry

def at_width(b,x,a,ai,divide=True):
    import dqi_int_convtest as CT
    live=set(CT.TR['live']);exclude={int(str(q)[1:]) for q in list(x)+list(a)+list(ai)}
    assert len(live)==b.num_allocated_qubits and exclude<=live and live-exclude
    emit(b,x,ai if divide else a,a if divide else ai,km.q(min(live-exclude)))

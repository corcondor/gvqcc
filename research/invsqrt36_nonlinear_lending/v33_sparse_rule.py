"""Deterministic V33 replay recipe, run beside the archived V32 affine_reset.py.
Reachability premises are NOT inferred from the index list: use the full exact
checker in the V33 companion archive before adopting any new parent.
"""
from affine_reset import *
PARENT = "006debfefa0a566a9de3a61581b3b34296750cf58c14fdecb7bb1612efc958bd"
RESULT = "8c3960d02d7c32dadbf307590ed7b8281bdd0aaabfa36dd86d95cce57bbabcb0"
SCRATCH = 1018
ROWS = {
    33657: ((2,15,24), (5,11,22,32)),
    34411: ((0,2,24), ()),
    35358: ((15,21,14), ()),
    36190: ((0,2,14), ()),
    39208: ((0,10,14), ()),
    39816: ((0,10,16), ()),
    42318: ((2,18,0), ()),
    42699: ((10,34,6), (15,32)),
    44267: ((1,19,15), ()),
    45350: ((11,28,6), ()),
}

def emit(src,dst):
    src,dst=Path(src),Path(dst)
    assert hashlib.sha256(src.read_bytes()).hexdigest()==PARENT
    K=NativeKMB.read(src)
    assert all(SCRATCH not in (o.condition,o.measurement) for o in K.ops)
    out=[]
    for i,o in enumerate(K.ops):
        if i==36276:
            assert o==Op(49,(30,28,8))
            out.append(Op(33,(24,8)))
        elif i in ROWS:
            (a,b,t),terms=ROWS[i]
            assert o==Op(49,(a,b,t))
            out += [Op(80,(t,),SCRATCH),Op(160,(a,b),condition=SCRATCH)]
            out += [Op(144,(q,),condition=SCRATCH) for q in terms]
            out += [Op(64,(),SCRATCH)]
            out += [Op(33,(q,t)) for q in terms]
        else:
            out.append(o)
    dst.write_bytes(byte_emit(K,out,37))
    assert NativeKMB.read(dst).ops==out
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==RESULT
    print("Reproduced bytes, not a new independent proof",RESULT)

if __name__=="__main__":
    emit(*sys.argv[1:])

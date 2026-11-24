"""Correct KMB v2 three-operand row count, preserving every other byte."""
import argparse, hashlib, json, struct
from pathlib import Path
HEADER=struct.Struct('<4I9Q'); SECTION=struct.Struct('<QQ')
def repair(raw):
    h=list(HEADER.unpack_from(raw,16)); assert h[0]==2
    i=16+HEADER.size; cols={}
    while i<len(raw):
        kind,n=SECTION.unpack_from(raw,i); i+=SECTION.size
        assert kind not in cols and i+n<=len(raw)
        cols[kind]=raw[i:i+n]; i+=n
    assert i==len(raw) and set(range(1,12))<=cols.keys()
    op=cols[1]; n3=sum((g>>4)&3==3 for g in op)
    n2=sum((g>>4)&3==2 for g in op); n1=sum((g>>4)&3==1 for g in op)
    assert h[4]==len(op) and h[6]==n2 and h[7]==n1
    for k in (2,3,4): assert len(cols[k])==4*n3
    for k in (5,6): assert len(cols[k])==4*n2
    assert len(cols[7])==4*n1
    assert len(cols[8])==4*h[8]==4*sum(bool(g&64)for g in op)
    assert len(cols[9])==4*h[9]==4*sum(bool(g&128)for g in op)
    assert len(cols[10])==16*h[10]==16*sum((g&127)==19 for g in op)
    old=h[5]; h[5]=n3; result=raw[:16]+HEADER.pack(*h)+raw[16+HEADER.size:]
    assert len(result)==len(raw) and raw[:40]==result[:40] and raw[48:]==result[48:]
    return result,{'old_header_arity3':old,'actual_arity3':n3,'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),'official_verifier':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    assert a.input.resolve()!=a.output.resolve()
    fixed,rec=repair(a.input.read_bytes());a.output.write_bytes(fixed);print(json.dumps(rec,indent=2))

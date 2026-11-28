"""Emit native #266 raw-key prefix and return with a reversible seam marker."""
import sys,json,hashlib
from pathlib import Path
import kickmix as km
from core_direct_unit import Pipeline, U
def ids(words):
    return [int(q.id) for w in words for q in w]
def main():
    b=km.CircuitBuilder(); b.set_max_qubits(900)
    S=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
    E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
    key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda _:None)
    D,N=key['D'],key['N']
    assert len(D)==36 and len(N)==35 and b.num_allocated_qubits==865
    dn=ids(list(D)+list(N))
    retained=list(key['carry'][12:])+[key['gauge'].flag]
    rid=[int(q.id) for q in retained]
    assert len(set(dn+rid))==865
    scratch=b.alloc_qubits(35);sid=[int(q.id) for q in scratch]
    assert set(dn+rid+sid)==set(range(900))
    for _ in range(128):b.x(scratch[0])
    # Identity pairs force the entire physical mapping into the KMB header.
    for q in scratch[1:]: b.x(q);b.x(q)
    b.free(scratch)
    Pipeline.emit_key_closing(b,key,stage=lambda _:None)
    assert b.num_allocated_qubits==840
    c=b.finish_circuit();out=Path(sys.argv[1]);c.to_file(str(out),format='kmb')
    assert c.num_qubits==900
    r=dict(Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),
       sha256=hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),
       dn=dn,retained=rid,scratch=sid,E=ids(E),U=list(U),sentinel_q=sid[0],sentinel_count=128)
    out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
    print({k:v for k,v in r.items() if not isinstance(v,list)},flush=True)
if __name__=='__main__':main()

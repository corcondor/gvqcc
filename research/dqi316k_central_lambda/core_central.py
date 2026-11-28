"""#263 + #264 + shared lexical bindings for the pad and affine product frames."""
import sys, pathlib, json, hashlib
sys.path.insert(0,'/tmp/seam')
import core_unitzero
sys.modules['core_direct']=core_unitzero
import core_rebase as R
import central_schedule as CS
from core_unitzero import *
def pad_open(b,D,N):
 flags=[]
 for w in range(6):
  f=b.alloc_qubits(1)[0];R.marker(b,D,R.MARK[w],f)
  for words,n in [(D,w+1),(N,w)]:
   if not n:continue
   ops=R.basis_ops(w,n);R.change(b,words,ops)
   for i in range(n):
    for a,z in zip(words[i],words[n+i]):b.cx(a,z);b.ccx(f,z,a);b.cx(a,z)
   R.change(b,words,ops,True)
  flags.append(f)
 return flags
def pad_close(b,D,N,flags):
 for w in range(5,-1,-1):
  f=flags[w]
  for words,n in [(D,w+1),(N,w)]:
   if not n:continue
   ops=R.basis_ops(w,n);R.change(b,words,ops)
   for i in range(n):
    for a,z in zip(words[i],words[n+i]):b.cx(a,z);b.ccx(f,z,a);b.cx(a,z)
   R.change(b,words,ops,True)
  R.marker(b,D,R.MARK[w],f);b.free(f)
def main():
 b=km.CircuitBuilder();b.set_max_qubits(900)
 S=[b.create_quantum_register(12,f'S{i}') for i in range(70)];E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
 CS.install(Pipeline.P.Synthesis)
 key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda _:None)
 N=[list(x) for x in key['N']];D=[list(x) for x in key['D']]
 print('KEY',b.num_allocated_qubits,flush=True);flags=pad_open(b,D,N);print('PAD_LIVE',b.num_allocated_qubits,flush=True)
 DD=[km.array(x) for x in D];NN=[km.array(x) for x in N]
 outer=Pipeline.NewOuter.emit_prefix(b,DD,NN,gauge_flag=key['gauge'].flag,gauge_other=key['carry'][12:],fused=False,stage=lambda x:print('OUTER',x,b.num_allocated_qubits,flush=True))
 finish=Pipeline.P.Finish.emit_prefix(b,DD,NN)
 R.fft_magnitude(b,D,N,E)
 rec=Pipeline.P.Finish.emit_closing_keep_inverse(b,DD,NN,finish)
 Pipeline.P.Seam.outer_closing_with_inverse(outer.lender,DD,NN,outer,rec,stage=lambda _:None)
 pad_close(b,D,N,flags);Pipeline.emit_key_closing(b,key,stage=lambda _:None)
 assert b.num_allocated_qubits==840
 c=b.finish_circuit();p=pathlib.Path(sys.argv[1]);c.to_file(str(p),format='kmb')
 print('CORE',json.dumps(dict(Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())),flush=True)
if __name__=='__main__':main()


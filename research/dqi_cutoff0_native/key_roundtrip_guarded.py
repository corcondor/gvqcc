from pathlib import Path
import sys, inspect, hashlib, json, time
from build_team import Pipeline, install_j_min, ORIGINAL_J_MIN, TEAM
import build_team
Pipeline.configure()
# Preserve the same low-level arithmetic and phase routines. Replace paired first-three fast chart with generic zero-safe rolling extractor, both directions.
src=inspect.getsource(install_j_min)
assert src.count('assert 3 <= j_min < 35')==1
exec(src.replace('assert 3 <= j_min < 35','assert 0 <= j_min < 35').replace('guarded=False','guarded=True'),build_team.__dict__)
Pipeline.First3.emit_prefix=Pipeline.BaseExtractor.Direct.emit_prefix
Pipeline.First3.emit_closing=Pipeline.BaseExtractor.Direct.emit_closing
build_team.install_j_min(0)
Pipeline.emit_key_prefix=Pipeline.P.emit_key_prefix
Pipeline.emit_key_closing=Pipeline.P.emit_key_closing
import kickmix as km
b=km.CircuitBuilder()
b.set_max_qubits(900)
S=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
start=time.monotonic()
def stage(x):
 if not isinstance(x,dict) or x.get('stage') not in ('extract_prefix','synthesis_prefix','extract_closing','synthesis_closing'):
  print('STAGE',str(x)[:240],b.num_allocated_qubits,flush=True)
key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=stage)
Pipeline.emit_key_closing(b,key,stage=stage)
assert b.num_allocated_qubits==840
c=b.finish_circuit()
assert c.num_qubits<=900
p=sys.argv[1]
c.to_file(p,format='kmb')
r=dict(Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest(),seconds=time.monotonic()-start,cutoff=0)
print(json.dumps(r),flush=True);Path(p+'.json').write_text(json.dumps(r))


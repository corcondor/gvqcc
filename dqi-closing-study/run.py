from pathlib import Path
import hashlib
import json
import lzma
import re
import shutil
import subprocess
import sys
from time import monotonic
from zipfile import ZipFile,ZIP_DEFLATED

import numpy as np
import kickmix as km

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"dqi-regression-ci"))
import verify_submission_dqi as V

def sha(path):
    with path.open("rb") as handle: return hashlib.file_digest(handle,"sha256").hexdigest()

def extract_source(name,expected,dest):
    with lzma.open(HERE/(name+".kmb.xz"),"rb") as source,dest.open("wb") as out:
        shutil.copyfileobj(source,out,4<<20)
    assert sha(dest)==expected

work=Path(sys.argv[1])
work.mkdir()
archive=HERE.parent/"dqi-regression-ci/v7.zip"
v7=work/"v7.kmb"
with ZipFile(archive) as z,z.open("dqi.kmb") as inp,v7.open("wb") as out:
    shutil.copyfileobj(inp,out,4<<20)
v7_sha=sha(v7)
assert v7_sha=="204f1c0c1fe51513f55ebef0a651e33fab83fcfb2297e23e0445920876ac5f6e"
a,b=(work/(x+".kmb") for x in ("dqi_d54d3387","dqi_66b4f18b"))
extract_source(a.stem,"d54d338753757cf024c6acd5ffbbd9a8254a9d9ab56b84f06feff768041b79c8",a)
extract_source(b.stem,"66b4f18b85273bdc0b325500c43a810aba2772275b977f371731cfc400a315c2",b)
new=work/"dqi.kmb"
script=HERE/"tools/analysis/ir/stream_diff.py"
cmd=[sys.executable,"-u",str(script),str(a),str(b),"--list","6","--transplant",str(v7),str(new),"--from-b","66,0"]
proc=subprocess.run(cmd,capture_output=True,text=True,check=False)
print(proc.stdout,flush=True)
(work/"transplant.log").write_text(proc.stdout+"\n"+proc.stderr)
if proc.returncode: raise RuntimeError(proc.stderr)
sha_candidate=sha(new)
c=km.Circuit.from_file(new,format="kmb")
static=int(c.operation_statistics().num_toffoli_like)
spec=V.ProblemSpecDQI.benchmark_instance()
bs=V.DEFAULT_BATCH_SIZE
seed=V._initial_seed(v7_sha,"notebook-verification")
seeds=np.random.SeedSequence(seed,pool_size=8).generate_state(8*(spec.num_shots//bs),dtype=np.uint64).reshape(-1,2,4)
batch,index=divmod(60600,bs)
rng_seed,sim_seed=(int.from_bytes(x,"little") for x in seeds[batch])
syndromes,masks,phase=V.sample_shots(spec,V.FieldTables(km.GF2Field(spec.degree)),np.random.default_rng(rng_seed),bs)
syndrome,mbuc,ancilla=V.validate_registers(c,spec)
sim=km.Simulator(batch_size=bs,debug_print=False,counting_operations=True,seed=sim_seed)
sim.use_same_registers_as(c)
data=V.to_bits(syndromes,spec.degree)
sim.write_across_shots(km.array(syndrome),data)
sim.write_across_shots(km.array(mbuc),V.to_bits(masks,spec.degree))
sim.do(c)
different=sim.read_across_shots(km.array(syndrome))^data
junk=sim.read_across_shots(ancilla)
value=different.any(axis=0)|junk.any(axis=0)
observed=sim.read_phase_flipped_across_shots()
phase_error=(phase^observed)&~value
record={"v7_sha256":v7_sha,"candidate_sha256":sha_candidate,"candidate_qubits":c.num_qubits,
        "candidate_static_toffoli":static,"static_toffoli_saved":368191-static,
        "original_v7_matched_batch_value_errors":int(value.sum()),"original_v7_matched_batch_phase_errors":int(phase_error.sum()),
        "case_60600_value_error":bool(value[index]),"case_60600_observed_phase":bool(observed[index]),
        "case_60600_expected_phase":bool(phase[index]),"official_full":[]}
if not value.any() and not phase_error.any() and static<368191:
    for salt in ("","notebook-verification"):
        start=monotonic()
        result=V.verify(c,spec,salt=salt)
        record["official_full"].append({"salt":salt,"result":result,"seconds":monotonic()-start})
(work/"result.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2),flush=True)
if static<368191:
    with ZipFile(work/"dqi_only.zip","w",ZIP_DEFLATED,compresslevel=5) as z:
        z.write(new,"dqi.kmb")

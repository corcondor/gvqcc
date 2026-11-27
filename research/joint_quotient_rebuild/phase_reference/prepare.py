import hashlib,os,sys
from pathlib import Path
import kickmix as km
sys.path.insert(0,os.environ['DQI_VERIFIER_DIR'])
import verify_submission_dqi as V
p=Path(sys.argv[1])
assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60'
c=km.Circuit.from_file(str(p))
q,b,anc=V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance())
assert len(q)==840 and len(b)==49140 and len(anc)==60
Path('qids.txt').write_text('\n'.join(str(x)[1:] for x in q)+'\n')
Path('mask_ids.txt').write_text('\n'.join(str(x)[1:] for x in b)+'\n')

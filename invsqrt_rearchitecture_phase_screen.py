#!/usr/bin/env python3
"""Build seven NUMERICAL-ONLY arithmetic probes of the actual e46 circuit.
These deliberately break deferred measurement cleanup and are NOT submission
circuits. They ask whether a changed forward Boolean phase basis can meet the
error constraint before implementing reversible arithmetic and all outcomes.
Run from the workspace parent containing gvqcc_repo/.
"""
import argparse,hashlib,json,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('names',nargs='*');a=p.parse_args()
basepath=pathlib.Path('gvqcc_repo/invsqrt_structural_e46.kmx')
assert hashlib.sha256(basepath.read_bytes()).hexdigest()=='69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1'
base=basepath.read_text().splitlines();out=pathlib.Path('invsqrt_rearchitecture_phase_work');out.mkdir(exist_ok=True)
assert base[7600:7626]==['X q'+str(q) for q in [9,34,36,30,32,28,35,33,31,29,26,27,37,38,6,41,5,4,3,2,1,0,39,43,40,8]]
probes={
 'drop1':{'freeze_zero_before_line_7601':[41]},
 'drop2':{'freeze_zero_before_line_7601':[41,40]},
 'drop3':{'freeze_zero_before_line_7601':[41,40,43]},
 'carry1':{'delete_original_lines':[7548]},
 'carry2':{'delete_original_lines':[7554]},
 'carry12':{'delete_original_lines':[7548,7554]},
 'carry3':{'delete_original_lines':[7559]},
}
for name in a.names or probes:
 recipe=probes[name];s=base.copy()
 if 'freeze_zero_before_line_7601' in recipe:
  # A fresh HMR record with outcome forced to zero is an analysis intervention.
  # It neither implements a valid reset nor pays the resulting phase debt.
  s[7600:7600]=[f'HMR q{q} b{9000+i}' for i,q in enumerate(recipe['freeze_zero_before_line_7601'])]
 else:
  ids=recipe['delete_original_lines'];assert all(base[i-1].startswith('CCX ') for i in ids)
  s=[l for i,l in enumerate(base,1) if i not in ids]
 kmx=out/f'analysis_only_{name}.kmx';kmx.write_text('\n'.join(s)+'\n')
 r=subprocess.run([sys.executable,'gvqcc_repo/invsqrt_structural_extract.py','--kmx',str(kmx),'--out',str(out/name)],capture_output=True,text=True)
 assert (out/name/'basis.u64').exists(),r.stderr
 print(json.dumps({'name':name,'recipe':recipe,'not_a_valid_circuit':True,'extractor_stdout':r.stdout.strip(),'returncode':r.returncode}),flush=True)
(out/'interventions.json').write_text(json.dumps(probes,indent=2))

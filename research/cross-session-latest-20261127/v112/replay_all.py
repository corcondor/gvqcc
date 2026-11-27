#!/usr/bin/env python3
"""Rebuild all 18 V112 deliverable files from the exact V111 baseline.

Requires Python 3, NumPy (native chemistry audit), and a C++17 compiler.
The baseline ZIP is checked before extraction. A directory of baseline files
may be supplied instead; every member is still checked against the pinned hash.
Search is not rerun: saved order witnesses and literal rewrite certificates
reproduce the exact bytes and are checked independently during replay.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'ordering'))
from native_kmb import NativeKMB
import relaxed_schedule as schedule
from verify_virtual_patches import verify as verify_virtual

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1<<20), b''): h.update(part)
    return h.hexdigest()

def run(args):
    p=subprocess.run(list(map(str,args)), text=True, capture_output=True)
    if p.returncode: raise RuntimeError(f'Command failed ({p.returncode}): {args}\n{p.stdout}\n{p.stderr}')
    return p.stdout.strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--work',type=Path)
    p.add_argument('--compiler',default=os.environ.get('CXX','g++'))
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    assert not any(a.out.iterdir()), 'Output directory must be empty'
    baseline=json.loads((ROOT/'baseline/V111_BASELINE.json').read_text())
    final=json.loads((ROOT/'FINAL_MANIFEST.json').read_text())
    work=a.work or a.out.parent/(a.out.name+'_replay_work')
    work.mkdir(parents=True,exist_ok=True)
    if a.baseline.is_file():
        assert digest(a.baseline)==baseline['zip_sha256']
        source=work/'baseline';source.mkdir(exist_ok=True)
        with zipfile.ZipFile(a.baseline) as z:
            assert set(z.namelist())==set(baseline['files'])
            for name in baseline['files']:
                target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(name) as f,target.open('wb') as g: shutil.copyfileobj(f,g,1<<20)
    else: source=a.baseline
    for name,info in baseline['files'].items(): assert digest(source/name)==info['sha256'],name
    exe={}
    for name,code in (
        ('zero',ROOT/'ordering/zero_width_all.cpp'),
        ('apply',ROOT/'ordering/vendor/apply_proof.cpp'),
        ('stream',ROOT/'ordering/vendor/verify_stream.cpp'),
        ('dqi_apply',ROOT/'dqi/patch_dqi_joint.cpp'),
        ('dqi_stream',ROOT/'dqi/check_dqi_joint.cpp'),
        ('dqi_clean',ROOT/'dqi/audit_shear_entry.cpp')):
        exe[name]=work/name
        run([a.compiler,'-O2','-std=c++17',code,'-o',exe[name]])
    records=[]
    for name in baseline['files']:
        if not name.endswith('.kmb') or name=='dqi.kmb': continue
        tag=Path(name).stem; src=source/name; dst=a.out/name;dst.parent.mkdir(parents=True,exist_ok=True)
        zeros=work/(tag+'_zeros.txt'); run([exe['zero'],src,zeros])
        assert zeros.read_bytes()==(ROOT/'ordering/zero_intervals'/f'{tag}.txt').read_bytes()
        c=NativeKMB.read(src); m=schedule.model(c,zeros)
        order=json.loads((ROOT/'ordering/orders'/f'{tag}.json').read_text())
        succ,_=schedule.graph(c,m,'commute',True)
        assert schedule.verify_permutation(c,m,order,succ)
        assert [i for i in order if c.ops[i].raw&127==80]==[i for i,o in enumerate(c.ops) if o.raw&127==80]
        c.ops=[c.ops[i] for i in order];reordered=work/(tag+'_ordered.kmb');reordered.write_bytes(c.to_bytes())
        proof=ROOT/'ordering/proofs'/f'{tag}.proof'
        result=work/(tag+'_synth.kmb');run([exe['apply'],reordered,proof,result])
        stream=json.loads(run([exe['stream'],reordered,result,proof]))
        if tag=='invsqrt':
            intermediate=work/'invsqrt_private_virtual.kmb'
            first=verify_virtual(result,json.loads((ROOT/'ordering/VIRTUAL_PATCHES.json').read_text()),emit=intermediate)
            second=verify_virtual(intermediate,json.loads((ROOT/'ordering/PUBLIC_VIRTUAL_PATCHES.json').read_text()),emit=dst)
            virtual=[first,second]
        else: shutil.copyfile(result,dst);virtual=None
        assert digest(dst)==final['files'][name]['sha256']
        records.append(dict(file=name,order_check='PASS',stream=stream,virtual=virtual))
    dst=a.out/'dfthcsos/submission.npz';dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source/'dfthcsos/submission.npz',dst)
    journal=ROOT/'dqi/dqi_selected_journal.txt'
    dqi_emit=run([exe['dqi_apply'],source/'dqi.kmb',journal,a.out/'dqi.kmb',work/'dqi_hmr_map.txt'])
    dqi_stream=run([exe['dqi_stream'],source/'dqi.kmb',a.out/'dqi.kmb',journal])
    dqi_clean=run([exe['dqi_clean'],source/'dqi.kmb'])
    # The local exhaustive checker reads only the supplied literal plans.
    local=run([sys.executable,ROOT/'dqi/verify_shear_exhaustive.py'])
    anf=run([sys.executable,ROOT/'ordering/vendor/verify_anf.py',*sorted((ROOT/'ordering/proofs').glob('*.proof'))])
    for name,info in final['files'].items(): assert digest(a.out/name)==info['sha256'],name
    receipt=dict(status='EXACT_ALL_18_REPLAY_PASS',files=18,baseline_zip_sha256=baseline['zip_sha256'],
                 final_total_instructions=final['total_instructions'],records=records,
                 dqi_emit=dqi_emit,dqi_stream=dqi_stream,dqi_clean=dqi_clean,dqi_local=local,anf=anf,
                 scope='Exact hash-pinned rebuild and rewrite proof checks. Official receipts and full-program DQI paired simulations are separate. Global quantum width remains 405/37/900.')
    (a.out/'REPLAY_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('records','dqi_emit','dqi_stream','dqi_clean','dqi_local','anf')}))

if __name__=='__main__':main()
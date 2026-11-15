#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export immutable research evidence, not a new competition submission."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

README='''# score7 phase-rewrite research evidence

This archive is research code and verification evidence. It is not a Kaggle
submission. No new competition circuit or score improvement was accepted.
The retained local score is 27.324751494620457, as recorded by score6_scorecard.

Read code/score7_results.md for the Japanese report and the detailed reports
for the exact scope of every test. MANIFEST.json binds all payloads by SHA256.
The 6T CCCZ circuits are checked with exact integer ring arithmetic; native
fixture improvements are controls, not production improvements.

## Runtime

Python 3.11+; NumPy and Kickmix for the native/chemistry checks; g++ with C++17
for the DQI scanners. The exact CCCZ checker uses only the standard library.
The supplied official verifier files are unchanged dependencies, not new runs.
Legacy report paths record the original environment. Use the relative inputs
and overrides below when reproducing elsewhere.

From code/, for the exact CCCZ proof:

    python score7_reproduce.py cccz --output /new/path/cccz.json

For invsqrt extraction, exact Walsh resynthesis and the native positive control:

    python score7_reproduce.py invsqrt --output /new/path/invsqrt

For the chemistry value/phase and 2--6-CCX window rank screen:

    python score7_chem_window_rank.py --loaders ../inputs/chemistry \\
      --table ../inputs/chemistry/submission.npz \\
      --output /new/path/chemistry.json --max-window 6

For whole-phase DQI discovery:

    g++ -O3 -std=c++17 score7_dqi_phase_resub.cpp -o /new/path/phase_resub
    /new/path/phase_resub /path/to/retained/dqi.kmb /new/path/resub.json

The other DQI checks take their arguments from --help or the C++ usage text.
No giant DQI binary is duplicated here. Use dqi.kmb from the retained
score6_local_candidate.zip (whole ZIP SHA256 below), or the equivalent retained
binary, and require its SHA256 before interpreting any result.

DQI SHA256:
e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355
Retained candidate ZIP SHA256:
938e08143c113817ca1c3749a361911a0f60b2db745735d4f8f4b1fc0a1e2b71

The independent CCCZ review also needs the primary TeX archive from
https://arxiv.org/src/2410.00910v2 (archive SHA256
39573ecf56e11380c7a50c009c84467e411c51d9a1285f9c225270a9a6af8de3).
The paper itself is not redistributed. Pass its path with --paper, the exact
code/receipt with --exact / --receipt, and ../official_sources with
--official-root. See score7_cccz_independent_review.py --help.

The inherited DQI finite-shot qualification is not a universal correctness
proof; the known numerator-zero limitation remains documented in score6.
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).parent)
    p.add_argument('--official-root',type=Path,required=True)
    p.add_argument('--chemistry',type=Path,required=True)
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--invsqrt',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    repo=a.repo.resolve()
    names={x.name for x in repo.glob('score7_*') if x.is_file()}
    names.update(['score6_scorecard.json','score6_chem_transfer_full_verification.json',
                  'score5_dqi_final_full_verification.json','score3_invsqrt_full_verification.json',
                  'score3_invsqrt_cache.kmx','NOTICE.md'])
    # Include local Python imports recursively, without inspecting data files.
    pending=[x for x in names if x.endswith('.py')];done=set()
    while pending:
        n=pending.pop()
        if n in done:continue
        done.add(n)
        for node in ast.walk(ast.parse((repo/n).read_text())):
            modules=[]
            if isinstance(node,ast.Import):modules=[v.name for v in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:modules=[node.module]
            for module in modules:
                dep=module.split('.')[0]+'.py'
                if (repo/dep).is_file() and dep not in names:
                    names.add(dep);pending.append(dep)
    payload={f'code/{n}':(repo/n).read_bytes() for n in sorted(names)}
    payload['README.md']=README.encode()
    for task in ('invsqrt','dqi','dfthcsos'):
        folder=a.official_root/'Inzainos/verifiers'/task
        for f in sorted(folder.rglob('*.py')):
            payload['official_sources/'+str(f.relative_to(a.official_root))]=f.read_bytes()
    assert sha(a.chemistry)=='16ee9ad3716309385aa9ce48c1f714e59484b79126ac6fe60591d3ba8bd7ebcf'
    assert sha(a.invsqrt)=='684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'
    payload['inputs/chemistry/submission.npz']=a.chemistry.read_bytes()
    payload['inputs/invsqrt.kmb']=a.invsqrt.read_bytes()
    for i in range(15):
        f=a.loaders/f'angle_k_{i}.kmb'
        payload[f'inputs/chemistry/{f.name}']=f.read_bytes()
    manifest={'type':'research_evidence_not_submission','score_improvement':0,
        'retained_local_score':27.324751494620457,
        'files':[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(payload.items())]}
    payload['MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    out=a.out/'score7_phase_rewrite_evidence.zip'
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n,b in sorted(payload.items()):
            info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,b)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(payload)
        for n,b in payload.items():assert z.read(n)==b
    # Inputs and source evidence must not change during packaging.
    for n in names:assert (repo/n).read_bytes()==payload[f'code/{n}']
    report=a.out/'score7_results.md';shutil.copyfile(repo/report.name,report)
    receipt={'status':'PASS','artifact':str(out),'bytes':out.stat().st_size,'sha256':sha(out),
        'members':len(payload),'all_crc_sha_and_payload_checks':'PASS',
        'repo_files':sorted(names),'report_path':str(report),'report_sha256':sha(report),
        'manifest_sha256':hashlib.sha256(payload['MANIFEST.json']).hexdigest()}
    (a.out/'score7_export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (a.out/'score7_payload_manifest.json').write_bytes(payload['MANIFEST.json'])
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()

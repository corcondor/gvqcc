#!/usr/bin/env python3
"""Persist the completed, noncompetitive J4 circuit fixtures and raw evidence.

This is deliberately not a competition submission archive. Production
score8 payloads are neither replaced nor included as a full portfolio.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,default=Path('/workspace/scratch/3815fb5fae06'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.receipt.exists():raise FileExistsError('Use fresh output paths')
    selected=[];joint=a.work/'score9_rebatch_synth/joint';alt=a.work/'score9_rebatch_alt'
    for f in sorted(joint.iterdir()):
        if f.is_file() and (f.suffix in ('.kmb','.npz','.npy') or f.name=='result.json' or f.name.endswith('_result.json')):
            selected.append(('joint/'+f.name,f))
    for rel in ['compiled.json','partitions.csv','partitions.json','coefficients.u32','verification.json']:
        selected.append(('alternative/'+rel,alt/rel))
    for f in sorted(alt.rglob('*.kmb')):
        selected.append(('alternative/'+f.relative_to(alt).as_posix(),f))
    for sub in ['care1039','care1219']:
        selected.append(('alternative/'+sub+'/compiled.json',alt/sub/'compiled.json'))
    selected.append(('matrix/matrix_bridge_k5.kmb',a.work/'score9_rebatch_synth/matrix_bridge_k5.kmb'))
    payloads=[];members=[]
    for name,path in selected:
        data=path.read_bytes();payloads.append((name,data))
        members.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source=str(path)))
    payloads.append(('README.txt',('RESEARCH FIXTURES; NOT A SUBMISSION\n\n'
        'The J=4 family is exactly correct under the recorded checks, but costs\n'
        '5197 loader Toffoli per pass and is worse than the accepted score8.\n'
        'It was not adopted or submitted. The retained local score is\n'
        '27.32784222155277; the requested target28 was not reached.\n\n'
        'Source, mathematical scope, and independent reviews:\n'
        'https://github.com/corcondor/gvqcc/pull/6\n'
        'Entry point: score9_rebatch_results.md\n').encode()))
    payloads.append(('MANIFEST.json',(json.dumps(dict(status='NONCOMPETITIVE_RESEARCH_FIXTURES',files=members),indent=2)+'\n').encode()))
    with zipfile.ZipFile(a.out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(payloads):
            info=zipfile.ZipInfo(name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
    with zipfile.ZipFile(a.out) as z:
        assert z.testzip() is None
        for row in members:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    receipt=dict(status='NONCOMPETITIVE_RESEARCH_ARCHIVE_SAVED',path=str(a.out),bytes=a.out.stat().st_size,
        sha256=hashlib.sha256(a.out.read_bytes()).hexdigest(),members=len(payloads),all_member_sha256_and_crc_pass=True,
        production_score_unchanged=27.32784222155277,submission_performed=False,files=members)
    a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))

if __name__=='__main__':main()

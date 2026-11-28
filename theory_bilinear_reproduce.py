#!/usr/bin/env python3
"""Reproduce the pinned Polytof bridge, routes and independent block certificates.

Requires Python >=3.10, git, and a C++20 compiler. The normal reproduction
uses only Python's standard library and Polytof's vendored headers. Optional
extraction from the historical source tree is in theory_bilinear_prepare.py
and additionally requires its original kickmix environment.

The author checkout is read-only. Build products, generated routes and proof
records go under --work-dir. This script does not run the competition verifier.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PIN='0dcac107d15adc34dc646242d222f21ae7d32699'
URL='https://github.com/ZIB-IOL/polytof'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(path,n,terms):
    assert all(len(t)==3 and all(0<x<(1<<n) for x in t) for t in terms)
    path.write_text(f'{n} {len(terms)}\n'+''.join(' '.join(map(str,t))+'\n' for t in terms))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work-dir',type=Path,required=True)
    ap.add_argument('--polytof-dir',type=Path)
    ap.add_argument('--compiler',default='g++')
    ap.add_argument('--prepare-only',action='store_true')
    ap.add_argument('--with-search',action='store_true',help='Also repeat both finite bounded rank searches')
    args=ap.parse_args();repo=Path(__file__).resolve().parent
    work=args.work_dir.resolve();work.mkdir(parents=True,exist_ok=True)
    commands=[]
    def run(argv):
        argv=list(map(str,argv));commands.append(argv)
        print(json.dumps({'command':argv}),flush=True)
        subprocess.run(argv,check=True)
    certificate=repo/'theory_bilinear_input_certificate.json'
    data=json.loads(certificate.read_text())
    shutil.copyfile(certificate,work/'input_certificate.json')
    for record in data['records']:
        n=record['degree'];target=work/f'gf{n}_input.txt'
        emit(target,n,record['terms'])
        assert digest(target)==record['input_sha256']
    actual_path=repo/'inverse_v2_actual_tensor99.json'
    actual=json.loads(actual_path.read_text())
    assert len(actual)==99
    # C(a0+a1*t)=(a0+a1)+a1*t; dual action changes the HIGH coefficient half.
    # Every U coefficient is the dual conjugate of its V coefficient.
    assert all((u^((u&4095)<<12))==v for u,v,w in actual)
    emit(work/'gf24_actual_input.txt',24,actual)
    emit(work/'gf24_actual_symmetric_input.txt',24,[(v,v,w) for u,v,w in actual])
    manifest={'polytof_repository':URL,'polytof_commit':PIN,
              'source_roles':{'author_unmodified':'Polytof cpd::BASE and cnot::cpr_abc headers',
                              'new_work':'Deterministic drivers, tensor bridge, conjugation normalization, exact proofs, placement matcher and KMB splice'},
              'inputs':{p.name:digest(p) for p in (certificate,actual_path)},
              'generated_inputs':{p.name:digest(p) for p in sorted(work.glob('*input.txt'))},
              'commands':commands}
    if args.prepare_only:
        manifest['status']='PREPARED_EXACT_HASH_MATCHING_INPUTS'
    else:
        if args.polytof_dir is None:ap.error('--polytof-dir is required unless --prepare-only is used')
        poly=args.polytof_dir.resolve()
        got=subprocess.check_output(['git','-C',str(poly),'rev-parse','HEAD'],text=True).strip()
        if got!=PIN:raise RuntimeError(f'Expected pinned author commit {PIN}; got {got}')
        subprocess.run(['git','-C',str(poly),'diff','--quiet','HEAD','--'],check=True)
        manifest['compiler']=subprocess.check_output([args.compiler,'--version'],text=True).splitlines()[0]
        bins=work/'bin';bins.mkdir(exist_ok=True)
        def compile_driver(name,words,base=False):
            command=[args.compiler,'-O3','-std=c++20',f'-DVEC_WORDS={words}']
            if base:command.append('-DBASE')
            command+=['-I',poly/'src','-I',poly/'third_party',repo/f'theory_bilinear_{name}.cpp','-o',bins/name]
            run(command)
            return bins/name
        cpr=compile_driver('cpr',2)
        cases=[('gf12',32,'gf12_cpr_local'),('gf12',1024,'gf12_cpr1024_local'),
               ('gf24_actual',32,'gf24_actual_cpr_local'),
               ('gf24_actual',1024,'gf24_actual_cpr1024_local'),
               ('gf24_actual_symmetric',1024,'gf24_actual_symmetric_cpr1024_local')]
        for source,width,name in cases:
            run([cpr,work/f'{source}_input.txt',work/f'{name}.kmx',work/f'{name}_meta.json',width])
        proofdir=work/'verified';proofdir.mkdir(exist_ok=True)
        run([sys.executable,repo/'theory_bilinear_verify.py','--run-dir',work,
             '--repo-dir',repo,'--output-dir',proofdir])
        hashes={name:digest(proofdir/name) for name in ('theory_bilinear_actual_cpr.kmx','theory_bilinear_gf12_cpr.kmx')}
        assert all(h==digest(repo/name) for name,h in hashes.items()),'Kernel bytes differ from the recorded route'
        manifest['exact_reproduced_kernel_sha256']=hashes
        if args.with_search:
            base=compile_driver('polytof',1,True)
            depth=compile_driver('depth',1,True)
            for n,seed in ((12,2026111501),(24,2026111502)):
                run([base,work/f'gf{n}_input.txt',work/f'gf{n}_search.json',32,1000000,50000,seed])
                run([depth,work/f'gf{n}_input.txt',work/f'gf{n}_depth6.json',32,200000,2000,6,seed+2])
        manifest['status']='REPRODUCED_EXACT_KERNEL_BYTES_AND_ARBITRARY_ACCUMULATOR_PROOFS'
    output=work/'reproduction.json'
    output.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':manifest['status'],'manifest':str(output)}))


if __name__=='__main__':main()

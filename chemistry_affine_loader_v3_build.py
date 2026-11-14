#!/usr/bin/env python3
"""Patch4033 loaders with address-affine X/CX gates, proving both traversals.

coefficients.shape=(75,8), uint16 in[0,4095]. For each angle/output bit,
coefficient bit0 is a constant; coefficient bit1..11 selects address bit0..10.
The physical angle words are XORed with that affine Boolean function.

For batch k, apply delta[k-1] BEFORE the original loader and delta[k] AFTER.
The same patched loader is used in the reverse pass. This does not follow
from forward correctness alone: a mandatory exact reachable-subspace proof
checks all1220 addresses, both traversals, all40 outputs and everyHMR branch.
No physics/chemistry accuracy claim is made by a successful loader proof.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_LOADERS=ROOT/'dqi_inputs/chemistry_4033'
DEFAULT_TABLE=DEFAULT_LOADERS/'submission_asterios_full.npz'


def normalize_coefficients(coefficients):
    a=np.asarray(coefficients)
    if a.shape!=(75,8) or not np.issubdtype(a.dtype,np.integer):
        raise ValueError('coefficients must be an integer array of shape(75,8)')
    if np.any(a<0) or np.any(a>=4096):
        raise ValueError('each affine coefficient must fit12bits')
    return a.astype(np.uint16,copy=True)


def patch_words(words,coefficients):
    """Pure numpy interface, usable without importing kickmix."""
    coefficients=normalize_coefficients(coefficients)
    words=np.asarray(words)
    if words.shape!=(1220,75) or not np.issubdtype(words.dtype,np.integer):
        raise ValueError('expected integer angle_words shape(1220,75)')
    if np.any(words<0) or np.any(words>=256):raise ValueError('8bit words required')
    out=words.copy();addresses=np.arange(1220,dtype=np.uint16)
    for col,bit in np.argwhere(coefficients):
        mask=int(coefficients[col,bit]);value=np.full(1220,bool(mask&1),dtype=bool)
        for a in range(11):
            if mask>>(a+1)&1:value^=((addresses>>a)&1).astype(bool)
        out[:,col]^=value.astype(out.dtype)<<int(bit)
    return out


def tag_profile_sufficient(coefficients):
    """Conservative sufficient test from the separately proved4033 tag law.

    Bits0..5 are unrestricted. Bits6 XOR7 must change by the same affine
    function in everybatch for each of the five word slots. The exact proof,
    not this quick test, remains the acceptance criterion.
    """
    c=normalize_coefficients(coefficients).reshape(15,5,8)
    tags=c[:,:,6]^c[:,:,7]
    return bool(np.all(tags==tags[0]))


def patch_lines(batch_coefficients):
    out=[]
    for slot in range(5):
        for bit in range(8):
            mask=int(batch_coefficients[slot,bit]);target=11+8*slot+bit
            if mask&1:out.append(f'X q{target}')
            for a in range(11):
                if mask>>(a+1)&1:out.append(f'CX q{a} q{target}')
    return out


def build_affine_family(coefficients,*,source_dir=DEFAULT_LOADERS,table_path=DEFAULT_TABLE,output_dir=None,native_seeds=()):
    import kickmix as km
    from chemistry_reachable_exact_proof import prove_one,pack
    coefficients=normalize_coefficients(coefficients);source_dir=Path(source_dir);table_path=Path(table_path)
    if output_dir is not None and Path(output_dir).exists():raise FileExistsError('Use a new output directory')
    start=time.monotonic();data=dict(np.load(table_path,allow_pickle=False));old=data['angle_words'];new=patch_words(old,coefficients)
    if data['W'].shape[:2]!=(8,143) or data['U'].shape[-1]!=76:raise ValueError('pinned4033 layout required')
    expected_registers={'selection':list(range(11)),**{f'word_{j}':list(range(11+8*j,19+8*j)) for j in range(5)}}
    addresses=np.arange(1220,dtype=np.uint64);address_bits=[pack((addresses>>j)&1) for j in range(11)];zero=np.zeros((1220,5),dtype=np.uint64)
    c=coefficients.reshape(15,5,8);circuits=[];rows=[];checks=[];source_bytes=[]
    for k in range(15):
        path=source_dir/f'angle_k_{k}.kmb';raw=path.read_bytes();source=km.Circuit.from_file(path)
        actual={name:[int(str(q)[1:]) for q in arr] for name,arr in source.register_data.items()}
        if actual!=expected_registers:raise ValueError(f'Unexpected register mapping in batch{k}: {actual}')
        pre=patch_lines(c[k-1]) if k else [];post=patch_lines(c[k])
        if pre or post:
            lines=str(source).splitlines();split=next(i for i,line in enumerate(lines) if line.split() and line.split()[0] not in {'REGISTER','APPEND_TO_REGISTER'})
            text='\n'.join(lines[:split]+pre+lines[split:]+post)+'\n';candidate=km.Circuit(text)
        else:candidate=source
        if candidate.num_qubits!=source.num_qubits or candidate.num_qubits>128:raise AssertionError('Q/cap changed')
        before=source.operation_statistics().num_toffoli_like;after=candidate.operation_statistics().num_toffoli_like
        if before!=after:raise AssertionError('Toffoli changed')
        previous=new[:,5*(k-1):5*k] if k else zero;current=new[:,5*k:5*(k+1)]
        for direction,inc,want in [('forward',previous,current),('reverse',current,previous)]:
            checks.append(prove_one(candidate,inc.astype(np.uint64),want.astype(np.uint64),address_bits,f'k={k}/{direction}'))
        rows.append(dict(batch=k,source_sha256=hashlib.sha256(raw).hexdigest(),source_num_ops=len(source),patched_num_ops=len(candidate),num_qubits=candidate.num_qubits,toffoli_per_pass=int(after),pre_gates=pre,post_gates=post))
        circuits.append(candidate);source_bytes.append(raw)
    native=[]
    if native_seeds:
        import sys
        sys.path.insert(0,str(ROOT/'official_sources/Inzainos/verifiers'))
        from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
        for seed in native_seeds:
            recovered,layout,t=recover_words_from_circuits(circuits,num_vectors=1220,num_angles=75,shots_per_address=1,seed=int(seed))
            if not np.array_equal(recovered,new):raise AssertionError('native decoded words mismatch')
            if t!=8066:raise AssertionError(('native Toffoli mismatch',t))
            native.append(dict(seed=int(seed),shots_per_address=1,addresses=1220,both_passes=True,toffoli_forward_and_reverse=t,status='PASS_LOADER_ONLY'))
    total=sum(row['toffoli_per_pass'] for row in rows)
    if total!=4033:raise AssertionError(('source family differs from4033',total))
    report=dict(status='EXACT_AFFINE_PATCH_REACHABLE_PASS',coefficient_shape=[75,8],coefficient_encoding='bit0=constant; bits1..11=address bits0..10',coefficients=coefficients.tolist(),tag_profile_sufficient=tag_profile_sufficient(coefficients),changed_words=int(np.count_nonzero(new!=old)),changed_word_bits=int(sum(int(a^b).bit_count() for a,b in zip(old.ravel(),new.ravel()))),angle_shape=list(new.shape),source_factorization_sha256=hashlib.sha256(table_path.read_bytes()).hexdigest(),toffoli_per_pass=total,toffoli_forward_and_reverse=2*total,max_loader_qubits=max(x.num_qubits for x in circuits),address_transition_cases=1220*15*2,output_bits_per_transition=40,HMR_formal_variables_cancelled=sum(x['HMR_formal_variables_cancelled'] for x in checks),all_classical_measurement_branches_covered=True,first_forward_input_and_last_reverse_output_zero=True,source_circuits_preserved_inside_patch=True,checks=checks,circuits=rows,native_checks=native,full_competition_shots_run=False,chemistry_physical_accuracy_tested=False,score_improvement_claimed=False,seconds=time.monotonic()-start)
    if output_dir is not None:
        output_dir=Path(output_dir);output_dir.mkdir(parents=True)
        # No files are written until all exact and requested native checks pass.
        for k,(circuit,row,raw) in enumerate(zip(circuits,rows,source_bytes)):
            dest=output_dir/f'angle_k_{k}.kmb'
            if row['pre_gates'] or row['post_gates']:circuit.to_file(dest,format='kmb')
            else:dest.write_bytes(raw)
            row['candidate_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
        outdata=dict(data);outdata['angle_words']=new
        dest=output_dir/'submission.npz';np.savez_compressed(dest,**outdata)
        report['candidate_factorization_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();report['other_factorization_arrays_preserved']=all(np.array_equal(outdata[k],data[k]) for k in data if k!='angle_words')
        np.save(output_dir/'coefficients.npy',coefficients,allow_pickle=False)
        report['builder_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (output_dir/'proof.json').write_text(json.dumps(report,indent=2)+'\n')
    return circuits,new,report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--coefficients',type=Path);p.add_argument('--source-dir',type=Path,default=DEFAULT_LOADERS);p.add_argument('--table',type=Path,default=DEFAULT_TABLE);p.add_argument('--out',type=Path,required=True);p.add_argument('--native-seeds',default='20261115,20261116');a=p.parse_args()
    if a.coefficients is None:
        coefficients=np.zeros((75,8),dtype=np.uint16);coefficients[0,0]=2
    elif a.coefficients.suffix=='.json':coefficients=np.asarray(json.loads(a.coefficients.read_text()))
    else:coefficients=np.load(a.coefficients,allow_pickle=False)
    _,_,report=build_affine_family(coefficients,source_dir=a.source_dir,table_path=a.table,output_dir=a.out,native_seeds=tuple(int(x) for x in a.native_seeds.split(',') if x))
    print(json.dumps({k:v for k,v in report.items() if k not in ('coefficients','checks','circuits')},indent=2))


if __name__=='__main__':main()

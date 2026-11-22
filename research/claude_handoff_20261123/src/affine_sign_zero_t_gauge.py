#!/usr/bin/env python3
"""Nonlocal Givens sign-frame gauge implemented on the ORIGINAL 3357-T KMBs.
Every free internal frame is an affine function of the selection register;
all 75 7-bit angles are reparameterized by 64*(s_out xor s_in).
The entire correction is selection->word CX/X, scored zero Toffoli, Q unchanged.
Patches conjugate each public bank: restore its original input angle frame before
the source operations, and install the new angle frame after all measurements.
Thus even banks depending nonlinearly on previous words are protected.
Do not claim scoring improvement from this zero-T gauge alone.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from longtrain.physical_verify import Physical,decode
from givens_gauge_global import tree_info
from qhdl_kmb import read,write_kmb,condition_depth

def mask_list(edges,scheme):
    info,slots=tree_info(edges);src=[];last={0:None}
    signs=[]
    for k,(p,q,fp,fq) in enumerate(info):
        old=last[p]
        src.append(signs[old] if old is not None else 0)
        if fp and fq:
            if scheme=='wide':
                j=(k*7+3)%11;l=(k*3+1)%11
                mask=(1<<j)^(1<<l)^( (1<<11) if (k%7)==0 else 0)
            elif scheme=='bank':
                j=(k//5)%11;mask=1<<j
            elif scheme=='row_gray':
                j=k%10;mask=(1<<j)^(1<<(j+1))
            else:raise ValueError(scheme)
        else:mask=0
        signs.append(mask)
        last[p]=k;last[q]=k
    diff=[a^b for a,b in zip(signs,src)]
    return diff,signs

def bitfield(mask,addresses):
    b=np.zeros(len(addresses),dtype=np.uint8)
    for j in range(11):
        if (mask>>j)&1:b^=((addresses>>j)&1).astype(np.uint8)
    if (mask>>11)&1:b^=1
    return b

def patch_one(src,dst,pre_masks,post_masks):
    k=read(str(src))
    assert k.num_qubits<=128
    assert int(condition_depth(k.op_types)[-1])==0
    registers=[(name,[(is_q,x) for is_q,x,pos in cont]) for name,cont in k.registers]
    words=[x for name,x in registers if name.startswith('word_')]
    assert len(words)==5
    def linear_segment(corrections):
        ops=[];q1=[];q20=[];q21=[];added={'X':0,'CX':0}
        for j,mask in enumerate(corrections):
            isq,target=words[j][6]
            assert isq
            if (mask>>11)&1:
                ops.append(0x11);q1.append(target);added['X']+=1
            for sel in range(11):
                if (mask>>sel)&1:
                    ops.append(0x21);q20.append(sel);q21.append(target);added['CX']+=1
        return np.array(ops,dtype=np.uint8),q1,q20,q21,added
    pre,p1,p20,p21,addpre=linear_segment(pre_masks)
    post,s1,s20,s21,addpost=linear_segment(post_masks)
    stream={name:np.array(k.stream(name),copy=True) for name in ['qqq0','qqq1','qqq2','qq0','qq1','q0','b0','bc']}
    stream['q0']=np.concatenate([np.array(p1,dtype=np.uint32),stream['q0'],np.array(s1,dtype=np.uint32)])
    stream['qq0']=np.concatenate([np.array(p20,dtype=np.uint32),stream['qq0'],np.array(s20,dtype=np.uint32)])
    stream['qq1']=np.concatenate([np.array(p21,dtype=np.uint32),stream['qq1'],np.array(s21,dtype=np.uint32)])
    assert not k.counts['angle'] and not k.counts['info_tags']
    write_kmb(str(dst),np.concatenate([pre,np.array(k.op_types,copy=True),post]),stream,registers=registers,num_qubits=k.num_qubits,num_bits=k.num_bits)
    new=read(str(dst))
    assert new.counts['qqq']==k.counts['qqq']
    assert new.num_qubits==k.num_qubits and new.num_bits==k.num_bits
    assert new.counts['ops']==k.counts['ops']+len(pre)+len(post)
    return {'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'Toffoli':int(new.counts['qqq']),'qubits':int(new.num_qubits),'HMR':int(new.counts['b']),'added_ops':{'X':addpre['X']+addpost['X'],'CX':addpre['CX']+addpost['CX']},'total_ops':int(new.counts['ops']),'original_target_frame_restored_before_backend':True}

def produce(src_npz,refdir,mode,outdir,data):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    with np.load(src_npz) as z:orig={k:np.array(z[k]) for k in z.files}
    old=orig['angle_words'].astype(np.uint8);edges=orig['tree_edges'];masks,states=mask_list(edges,mode)
    addr=np.arange(len(old),dtype=np.uint16)
    new=old.copy()
    for k,mask in enumerate(masks):new[:,k]^=bitfield(mask,addr)<<6
    dv=float(np.max(np.abs(decode(old,edges)-decode(new,edges))))
    assert dv<1e-14
    d=dict(orig);d['angle_words']=new.astype(np.int64)
    phys=Physical(data);p0=phys.evaluate(orig);p1=phys.evaluate(d)
    assert abs(p1['lambda_eff']-p0['lambda_eff'])<1e-8 and abs(p1['error_1']-p0['error_1'])<1e-8 and abs(p1['error_2']-p0['error_2'])<1e-8
    dest=outdir/'submission.npz';np.savez_compressed(dest,**d)
    circ=outdir/'circuits';circ.mkdir(exist_ok=True)
    receipts=[]
    for bank in range(15):
        post=[masks[bank*5+j] for j in range(5)]
        pre=[masks[(bank-1)*5+j] for j in range(5)] if bank>0 else [0]*5
        r=patch_one(Path(refdir)/f'candidate_angle_k_{bank}.kmb',circ/f'angle_k_{bank}.kmb',pre,post)
        r.update(bank=bank,pre_correction_masks=pre,post_correction_masks=post)
        receipts.append(r)
        print('BANK',bank,'T',r['Toffoli'],'Q',r['qubits'],'added CX',r['added_ops']['CX'],'X',r['added_ops']['X'],flush=True)
    report={'scheme':mode,'algorithm':'Givens frame signs sampled from affine selection masks; each original 3357 KMB conjugated by pre/post free CX/X transformations','angle_word_changes':int(np.count_nonzero(old!=new)),'angle_columns_changed':int(np.count_nonzero(np.any(old!=new,axis=0))),'max_abs_decode_diff':dv,'baseline_phys':p0,'new_phys':p1,'input_SHA256':hashlib.sha256(Path(src_npz).read_bytes()).hexdigest(),'output_npz_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'original_total_Toffoli':sum(x['Toffoli'] for x in receipts),'modified_total_Toffoli':sum(x['Toffoli'] for x in receipts),'max_qubits':max(x['qubits'] for x in receipts),'total_new_CX':sum(x['added_ops']['CX'] for x in receipts),'total_new_X':sum(x['added_ops']['X'] for x in receipts),'KMBs':receipts,'official_KickMix_executed':False,'note':'No scoring benefit from this transformation alone; useful for direct nonlocal angle-table change without losing public compiler quality'}
    (outdir/'build_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--refdir',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--scheme',choices=['wide','bank','row_gray'],default='wide');a=ap.parse_args()
    produce(a.source,a.refdir,a.scheme,a.out,a.data)
if __name__=='__main__':main()
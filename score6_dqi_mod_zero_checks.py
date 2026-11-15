#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tiny positive/negative controls for the bounded MBU discovery scanners."""
import argparse,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
from kmb_profile import MAGIC,HEADER,PACKET

def fixture(path,ops):
    cols={i:bytearray() for i in range(1,12)};counts=[0]*9;counts[0]=len(ops)
    for code,qs,bit,cond in ops:
        ar=(code>>4)&3;assert ar==len(qs);cols[1].append(code)
        if ar:counts[4-ar]+=1
        for j,q in enumerate(qs):cols[2+j if ar==3 else 5+j if ar==2 else 7].extend(struct.pack('<I',q))
        if code&64:assert bit is not None;cols[8].extend(struct.pack('<I',bit));counts[4]+=1
        if code&128:assert cond is not None;cols[9].extend(struct.pack('<I',cond));counts[5]+=1
    data=HEADER.pack(MAGIC,2,4,1,0,*counts)
    for kind in range(1,12):data+=PACKET.pack(kind,len(cols[kind]))+cols[kind]
    path.write_bytes(data)
def op(code,*qs,bit=None,cond=None):return(code,qs,bit,cond)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--binary-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    tests={
      'zero_uncompute':[op(0x12,2),op(0x31,0,1,2),op(0x31,0,1,2)],
      'one_uncompute':[op(0x12,2),op(0x11,2),op(0x31,0,1,2),op(0x31,0,1,2)],
      'dirty_accumulator':[op(0x31,0,1,2),op(0x31,0,1,2)],
      'executed_branch':[op(0x12,2),op(0x41,bit=0),op(0x81,cond=0),op(0x31,0,1,2),op(0x31,0,1,2),op(0x01)],
      'fredkin_pair':[op(0x12,2),op(0x31,0,1,2),op(0x32,0,1,3),op(0x32,0,1,3),op(0x31,0,1,2)],
      'changed_control':[op(0x12,2),op(0x31,0,1,2),op(0x21,3,0),op(0x31,0,1,2)]}
    results=[]
    with tempfile.TemporaryDirectory(prefix='score6_mod_control_') as temp:
        root=Path(temp)
        for mode in ['scan','truth','branch','cswap']:
            binary=args.binary_dir/f'score6_dqi_mod_zero_{mode}'
            for name,ops in tests.items():
                source=root/(name+'.kmb');out=root/(name+'_'+mode+'.json');fixture(source,ops)
                subprocess.run([str(binary),str(source),str(out)],check=True,capture_output=True)
                got=json.loads(out.read_text());indices=[r['index'] for r in got['candidates']]
                expected={'zero_uncompute':[2],'one_uncompute':[3],'dirty_accumulator':[],
                          'executed_branch':[4] if mode in ('branch','cswap') else [],
                          'fredkin_pair':[4] if mode=='cswap' else [],'changed_control':[]}[name]
                assert indices==expected,(mode,name,indices,expected)
                results.append(dict(mode=mode,fixture=name,candidate_indices=indices,expected=expected,pass_check=True))
    result={'status':'PASS','scope':'24 tiny scanner controls only; no production circuit rewrite or native verification',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':results}
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()

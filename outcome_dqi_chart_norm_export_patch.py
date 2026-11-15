#!/usr/bin/env python3
"""Export a compact, exact byte patch from the audited two-block splice.

Only standard-library code is needed to apply the result. Old and new whole
file hashes, each replacement's old/new hashes, and a virtual reconstruction
bind every byte. The raw replacement operands are included in the payload.
"""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parent
HEADER=struct.Struct('<16s4I9Q')
PACKET=struct.Struct('<QQ')
CHUNK=4<<20


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def sections(path):
    with Path(path).open('rb') as f:
        header=f.read(HEADER.size)
        fields=HEADER.unpack(header)
        for _ in range(fields[4]):
            kind,size=PACKET.unpack(f.read(PACKET.size))
            assert kind==0
            f.seek(size,1)
        register_end=f.tell()
        packets={}
        for expected in range(1,12):
            at=f.tell();kind,size=PACKET.unpack(f.read(PACKET.size))
            assert kind==expected
            packets[kind]={'header_offset':at,'payload_offset':f.tell(),'size':size}
            f.seek(size,1)
        assert f.tell()==Path(path).stat().st_size
        f.seek(packets[1]['payload_offset']);ops=f.read(packets[1]['size'])
    return header,register_end,packets,ops


TABLES={
  2:(bytes(int((x&0x30)>>4==3) for x in range(256)),4),
  5:(bytes(int((x&0x30)>>4==2) for x in range(256)),4),
  7:(bytes(int((x&0x30)>>4==1) for x in range(256)),4),
  8:(bytes(int(bool(x&0x40)) for x in range(256)),4),
  9:(bytes(int(bool(x&0x80)) for x in range(256)),4),
  10:(bytes(int((x&0x7f)==0x13) for x in range(256)),16),
}
TABLES[3]=TABLES[4]=TABLES[2]
TABLES[6]=TABLES[5]


def bounds(ops,kind,start,end):
    if kind==1:return start,end
    table,width=TABLES[kind]
    a=ops[:start].translate(table).count(1)*width
    return a,a+ops[start:end].translate(table).count(1)*width


def main():
    report=json.loads((ROOT/'outcome_dqi_chart_norm_splice_report.json').read_text())
    matches=json.loads((ROOT/'outcome_dqi_chart_norm_matches.json').read_text())
    old=Path(matches['matches']['9a82']['path']);new=Path(report['output_path'])
    assert digest(old)==report['input_sha256']
    assert digest(new)==report['output_sha256']
    oh,oe,op,oo=sections(old);nh,ne,np,no=sections(new)
    assert oe==ne
    replacements=[]
    with old.open('rb') as f,new.open('rb') as g:
        f.seek(HEADER.size);g.seek(HEADER.size)
        assert f.read(oe-HEADER.size)==g.read(ne-HEADER.size)
        def append(offset,old_size,new_offset,new_size,role):
            f.seek(offset);before=f.read(old_size)
            g.seek(new_offset);after=g.read(new_size)
            assert len(before)==old_size and len(after)==new_size
            if before==after:return
            replacements.append({'input_offset':offset,'input_bytes':old_size,
                'input_sha256':hashlib.sha256(before).hexdigest(),
                'replacement_bytes':new_size,'replacement_sha256':hashlib.sha256(after).hexdigest(),
                'replacement_b64':base64.b64encode(after).decode(),'role':role})
        append(0,HEADER.size,0,HEADER.size,'kmb_header')
        shift=0
        ranges=[]
        for i,block in enumerate(report['blocks']):
            start=block['start']+shift
            ranges.append((block['start'],block['end'],start,start+block['new_ops']))
            shift+=block['new_ops']-block['old_ops']
        for kind in range(1,12):
            append(op[kind]['header_offset'],PACKET.size,np[kind]['header_offset'],PACKET.size,
                   f'packet_{kind}_header')
            if kind<=10:
                for i,(a,b,c,d) in enumerate(ranges):
                    x,y=bounds(oo,kind,a,b);u,v=bounds(no,kind,c,d)
                    append(op[kind]['payload_offset']+x,y-x,np[kind]['payload_offset']+u,v-u,
                           f'{"prefix" if i==0 else "return"}_column_{kind}')
    replacements.sort(key=lambda r:r['input_offset'])
    h=hashlib.sha256();count=0;cursor=0
    with old.open('rb') as f:
        for row in replacements:
            remaining=row['input_offset']-cursor
            assert remaining>=0
            while remaining:
                data=f.read(min(CHUNK,remaining));assert data
                h.update(data);count+=len(data);remaining-=len(data)
            before=f.read(row['input_bytes'])
            assert hashlib.sha256(before).hexdigest()==row['input_sha256']
            after=base64.b64decode(row['replacement_b64'],validate=True)
            h.update(after);count+=len(after)
            cursor=row['input_offset']+row['input_bytes']
        for data in iter(lambda:f.read(CHUNK),b''):
            h.update(data);count+=len(data)
    assert h.hexdigest()==report['output_sha256'] and count==new.stat().st_size
    payload={'schema':'gvqcc-exact-byte-patch-v1','input_sha256':report['input_sha256'],
        'input_bytes':old.stat().st_size,'output_sha256':report['output_sha256'],
        'output_bytes':new.stat().st_size,'output_kmb_header':report['header'],
        'source_blocks':report['blocks'],'fresh_classical_bit_range':report['fresh_classical_bit_range'],
        'shared_child_mask_ids':report['new_shared_child_mask_ids'],
        'replacements':replacements,'virtual_stream_reconstruction_sha256':h.hexdigest(),
        'scope':'Exact audited two-block third-pivot projective repair; no arbitrary binary rewrite.'}
    raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    compressed=gzip.compress(raw,compresslevel=9,mtime=0)
    path=ROOT/'outcome_dqi_chart_norm_patch.json.gz';path.write_bytes(compressed)
    export={'status':'EXACT_VIRTUAL_RECONSTRUCTION_VERIFIED','patch_file':path.name,
        'patch_bytes':len(compressed),'patch_sha256':hashlib.sha256(compressed).hexdigest(),
        'uncompressed_patch_bytes':len(raw),'replacements':len(replacements),
        'input_sha256':payload['input_sha256'],'output_sha256':payload['output_sha256'],
        'output_bytes':count,'raw_replacement_bytes':sum(r['replacement_bytes'] for r in replacements)}
    (ROOT/'outcome_dqi_chart_norm_patch_export.json').write_text(json.dumps(export,indent=2)+'\n')
    print(json.dumps(export,indent=2))


if __name__=='__main__':main()

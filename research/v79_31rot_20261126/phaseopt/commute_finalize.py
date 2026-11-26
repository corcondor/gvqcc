"""Cancel commuting X/CX involution pairs with the donor's conservative law."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'recovered'/'V79'))
from native_kmb import NativeKMB
from affine_transport import cancel

def run(stem,out):
    k=NativeKMB.read(str(stem)+'.kmb')
    meta=json.loads(Path(str(stem)+'.json').read_text())
    ops,pairs=cancel(k.ops)
    z=NativeKMB(k.prefix16,k.header,k.sections,ops)
    p=Path(str(out)+'.kmb');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.to_bytes())
    assert NativeKMB.read(p).ops==ops
    c=collections.Counter(o.raw for o in ops)
    record={'source':str(stem),'source_sha256':hashlib.sha256(Path(str(stem)+'.kmb').read_bytes()).hexdigest(),'source_ops':len(k.ops),'ops':len(ops),'ccx':c[49],'cx':c[33],'rotations':c[19],'width':k.header[1],'commuting_pairs_removed':pairs,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    meta['stats'].update(record)
    Path(str(out)+'.json').write_text(json.dumps(meta,separators=(',',':')))
    Path(str(out)+'.commute.json').write_text(json.dumps(record,indent=2));print(record)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stem');p.add_argument('outstem');a=p.parse_args();run(a.stem,a.outstem)

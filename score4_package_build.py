#!/usr/bin/env python3
"""Generate the self-contained score4 Kaggle cell from exact local sources."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recipe',type=Path)
    p.add_argument('--candidate-dqi',type=Path)
    p.add_argument('--source-manifest',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    root=Path(__file__).resolve().parent
    manifest_path=args.source_manifest or root/'score3_submission_manifest.json'
    manifest_raw=manifest_path.read_bytes()
    manifest=json.loads(manifest_raw)
    recipe_path=args.recipe or root/'score4_package_recipe.json'
    recipe_raw=recipe_path.read_bytes()
    recipe=json.loads(recipe_raw)
    assert recipe['source_sha256']=='9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1'
    assert recipe['candidate_sha256']=='5a60d66233198be8ce05d9710bd35a7d2d6700bbced87560d405651070ae8194'
    assert manifest['archive']['sha256']=='5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882'
    modules={}
    for name in ['kmb_profile','dqi_ccx_peephole']:
        raw=(root/(name+'.py')).read_bytes()
        modules[name]={'source':raw.decode(),'sha256':sha(raw)}
    def operation_bytes(op):
        return (1+4*len(op['qubits'])+4*(op['bit'] is not None)
                +4*(op['condition'] is not None)+len(bytes.fromhex(op['angle_hex'])))
    delta=sum(sum(operation_bytes(op) for op in e['new'])-operation_bytes(e['old'])
              for e in recipe['edits'])
    candidate_bytes=next(row['bytes'] for row in manifest['members'] if row['name']=='dqi.kmb')+delta
    assert delta==80 and candidate_bytes==522345695
    if args.candidate_dqi:
        assert args.candidate_dqi.stat().st_size==candidate_bytes
    payload=dict(version=1,modules=modules,recipe=recipe,recipe_sha256=sha(recipe_raw),
                 source_manifest_sha256=sha(manifest_raw),
                 source_zip_sha256=manifest['archive']['sha256'],
                 source_dqi_sha256=recipe['source_sha256'],
                 candidate_dqi_sha256=recipe['candidate_sha256'],
                 candidate_dqi_bytes=candidate_bytes,
                 members=[{k:row[k] for k in ['name','sha256','bytes']} for row in manifest['members']])
    raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    encoded=base64.b64encode(zlib.compress(raw,9)).decode()
    template=(root/'score4_package_template.py').read_text()
    assert template.count('__SCORE4_PAYLOAD_B64__')==1 and template.count('__SCORE4_PAYLOAD_SHA256__')==1
    code=template.replace('__SCORE4_PAYLOAD_B64__',encoded).replace('__SCORE4_PAYLOAD_SHA256__',sha(raw))
    compile(code,'score4_package_cell.py','exec')
    output=args.output or root/'score4_package_cell.py'
    output.write_text(code)
    record=dict(status='SELF_CONTAINED_OFFLINE_CELL_BUILT',file=output.name,bytes=output.stat().st_size,
                sha256=sha(output.read_bytes()),payload_bytes=len(raw),payload_sha256=sha(raw),
                compressed_payload_bytes=len(base64.b64decode(encoded)),
                module_sha256={n:m['sha256'] for n,m in modules.items()},
                recipe_sha256=sha(recipe_raw),source_manifest_sha256=sha(manifest_raw),
                source_zip_sha256=payload['source_zip_sha256'],candidate_dqi_sha256=payload['candidate_dqi_sha256'],
                candidate_dqi_bytes=payload['candidate_dqi_bytes'],stdlib_only=True,
                network_required=False,official_verifier_run=False)
    (root/'score4_package_cell_build.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()

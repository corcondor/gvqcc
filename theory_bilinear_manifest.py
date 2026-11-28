#!/usr/bin/env python3
"""Derive compact placements and a deterministic gzip from the full build proof."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('full_report',type=Path)
    ap.add_argument('manifest',type=Path)
    ap.add_argument('--gzip-output',type=Path)
    args=ap.parse_args()
    raw=args.full_report.read_bytes()
    full=json.loads(raw)
    placements=[[b['template'],b['start'],b['end'],b['removed_CX']]
                for b in full['blocks']]
    assert len(placements)==full['rewritten_blocks']
    assert sum(p[3] for p in placements)==full['removed_CX']
    compact={k:v for k,v in full.items() if k!='blocks'}
    compact['full_report_sha256']=hashlib.sha256(raw).hexdigest()
    compact['full_report_bytes']=len(raw)
    compact['placement_columns']=['template','original_op_start','original_op_end_exclusive','removed_CX']
    compact['placements']=placements
    compact['placement_scope']='Offsets refer to the original pinned input. Wire maps and inherited condition depths are reproduced by the exact matcher; the full report records them.'
    if args.gzip_output:
        compressed=gzip.compress(raw,compresslevel=9,mtime=0)
        args.gzip_output.write_bytes(compressed)
        compact['full_report_gzip_sha256']=hashlib.sha256(compressed).hexdigest()
        compact['full_report_gzip_bytes']=len(compressed)
    args.manifest.write_text(json.dumps(compact,separators=(',',':'))+'\n')
    print(json.dumps({'manifest':str(args.manifest),'manifest_bytes':args.manifest.stat().st_size,
                      'full_report_bytes':len(raw),'full_report_sha256':compact['full_report_sha256'],
                      'gzip_bytes':compact.get('full_report_gzip_bytes')}))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Bind exact native inverse-phase templates to the actual e4 DQI tape."""
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json
import sys


def bind(tape, fixture, name, matcher):
    pattern = fixture.opcodes
    ops = list(fixture.operations(0, len(pattern)))
    pos=0
    exact=[]
    raw=0
    while True:
        i=tape.opcodes.find(pattern,pos)
        if i<0: break
        pos=i+1
        raw+=1
        match=matcher(ops,tape.operations(i,i+len(pattern)))
        if match is None:continue
        q,b=match
        assert set(range(12)).issubset(q)
        helpers={a:v for a,v in q.items() if a>=19}
        assert 12 == len(helpers)
        exact.append(dict(name=name,start=i,end=i+len(pattern),
                          qmap=q,bmap=b,helpers=sorted(helpers.values()),
                          max_helper=max(helpers.values())))
    return dict(name=name,template_operations=len(pattern),opcode_matches=raw,
                exact_matches=len(exact),helper_max_histogram=dict(Counter(m['max_helper'] for m in exact)),
                matches=exact)


def main(args):
    sys.path.insert(0,str(args.repo))
    import kmb_splice
    from outcome_inverse65_template_scan import match
    c=kmb_splice.open_circuit(args.circuit,args.profile)
    assert c.profile['raw_kmb_sha256']=='e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355'
    results=[]
    try:
        for name in ('fixed','masked'):
            old=kmb_splice.open_circuit(args.pieces/f'{name}_original.kmb')
            try:result=bind(c,old,name,match)
            finally:old.close()
            results.append(result)
            print(json.dumps({k:v for k,v in result.items() if k!='matches'}),flush=True)
    finally:
        c.close()
    args.output.write_text(json.dumps(dict(status='EXACT_BOUND', records=results),indent=2)+'\n')


if __name__=='__main__':
    p=ArgumentParser()
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--circuit',type=Path,required=True)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--pieces',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())

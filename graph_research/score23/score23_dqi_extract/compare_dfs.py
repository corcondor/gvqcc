"""Measure the actual whole-tape width change after exact DFS splices."""

from argparse import ArgumentParser
from csv import DictReader
import json
from pathlib import Path

import numpy as np


def width(path,n):
    count=np.zeros(n+1,dtype=np.int16)
    with path.open() as stream:
        for r in DictReader(stream,delimiter="\t"):
            count[int(r["first"])]+=1
            count[int(r["last"])]-=1
    np.cumsum(count,dtype=np.int16,out=count)
    return count[:n]


def main():
    p=ArgumentParser(description=__doc__)
    for key in ("old","new","splice","verify","out"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    test=json.loads(a.verify.read_text())
    report=json.loads(a.splice.read_text())
    assert test["circuit_sha256"]==report["candidate_sha256"]
    assert test["status"]=="PASS" and test["verified_shots"]==1024
    assert not test["phase_errors"] and not test["value_errors"]
    old,new=(width(p,test["num_ops"]) for p in (a.old,a.new))
    local=[]
    for r in report["spliced"]:
        lo,hi=r["start"],r["end"]
        local.append(dict(range=[lo,hi],width=[int(old[lo:hi].max()),int(new[lo:hi].max())],
                          positions_889=[int(np.count_nonzero(x[lo:hi]==889)) for x in (old,new)]))
    result=dict(whole_width=[int(old.max()),int(new.max())],
                whole_positions_889=[int(np.count_nonzero(x==889)) for x in (old,new)],
                splice_count=len(local),static_paid=test["max_toffoli_count"],
                verifier_shots=test["verified_shots"],local=local)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print({k:v for k,v in result.items() if k!="local"})


if __name__=="__main__":
    main()

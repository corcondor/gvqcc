"""Exact GF(4096) diagnostic on native #257 output. Not a repair."""
import json
from pathlib import Path
from audit import direct_codec as F
NODES={3:[3257,3134,3302,3431,3592,3671,3727,3792],
       5:[3134,3302,3431,3592,3671,3727,3792],
       7:[3302,3431,3592,3671,3727,3792],
       9:[3431,3592,3671,3727,3792],13:[3431,3592,3792],
       15:[3431,3592],17:[3431]}
def recurrence(s,p):
    for i in range(len(s)-len(p)+1):
        v=0
        for j,c in enumerate(p):v^=F.mul(c,s[i+j])
        if v:return False
    return True
def main():
    rows=json.loads(Path('value_probe.json').read_text())
    report=[]
    for w,nodes in NODES.items():
        p=[1]
        for k in nodes:p=F.pmul(p,[F.mul(k,k),0,1,0,1])
        cases=[r for r in rows if r['w']==w]
        assert len(cases)==4
        for r in cases:
            assert r['diff']==[a^b for a,b in zip(r['s'],r['out'])]
            assert r['numwrong']>0 and recurrence(r['diff'],p)
            d=F.locator_of(map(int,r['e']))
            assert recurrence(r['s'],d)
            assert recurrence(r['out'],F.pmul(d,p))
        report.append(dict(weight=w,nodes=nodes,degree=len(p)-1,shots=len(cases),matches=len(cases),distinct_differences=len({tuple(r['diff']) for r in cases})))
    print(json.dumps(report,indent=2))
    Path('return_recurrence_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

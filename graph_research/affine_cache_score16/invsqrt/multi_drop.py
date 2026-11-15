"""Try dropping each paid operation in coherent low-span windows."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from rankone import trace, select, re, OPS, PAID, SOURCE_SHA, MAX_X
from measure_linear import affine_basis, solve, advance
from drop_reconcile import encode_common

def scan(lines,xs,rows):
    keys={(r['start'],0) for r in rows}|{(r['end'],1) for r in rows}
    states=trace(lines,xs,keys)
    pattern=re.compile(r'\bq(\d+)\b')
    gates=[(line.split()[0],tuple(map(int,pattern.findall(line)))) for line in lines]
    mask=(1<<len(xs))-1
    tries=0; good=[]
    for r in rows:
        start,end=r['start'],r['end']
        entry,output=states[start,0],states[end,1]
        basis=affine_basis(output)
        incoming=affine_basis(entry)
        upper=affine_basis([*entry,*output])
        if len(upper)-len(incoming)>=r['paid']:continue
        for i in r.get('skip',[j for j in range(start,end+1) if gates[j][0] in PAID]):
            tries+=1
            state=entry[1:].copy()
            assert gates[i][0] in PAID
            for j in range(start,end+1):
                if j!=i:advance(*gates[j],state,mask)
            post=affine_basis([mask,*state])
            if len(post)!=len(basis) or any(solve(post,v) is None for v,_ in basis.values()):continue
            r=dict(r,skip=[i])
            good.append((r,state,output))
            print('match',len(xs),r,flush=True)
    return tries,good

def main():
    p=argparse.ArgumentParser()
    for key in ('source','out','windows'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    assert hashlib.sha256(a.source.read_bytes()).hexdigest()==SOURCE_SHA
    import kickmix as km
    lines=str(km.Circuit.from_file(a.source,format='kmb')).splitlines()
    rows=json.loads(a.windows.read_text())['hits']
    rng=np.random.default_rng(50188)
    xs=np.unique(np.r_[np.arange(1,5600),rng.integers(1,MAX_X+1,2300),MAX_X]).astype(np.uint32)
    tries,hits=scan(lines,xs,rows)
    print('sample',tries,len(hits),flush=True)
    cert=[]
    if hits:
      _,all_hits=scan(lines,np.arange(1,MAX_X+1,dtype=np.uint32),[r for r,*_ in hits])
      for r,state,output in all_hits:
        code=encode_common(output,[output[0],*state],None)
        actual=state.copy()
        for l in code:advance(l.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',l))),actual,output[0])
        assert actual==output[1:]
        cert.append(dict(r,affine_gates=code))
      if cert:
        c=min(cert,key=lambda x:(x['depth'],len(x['affine_gates'])))
        k=c['skip'][0]; j=c['end']
        result=km.Circuit('\n'.join(lines[:k]+lines[k+1:j+1]+c['affine_gates']+lines[j+1:])+'\n')
        result.to_file(a.out.with_suffix('.kmb'),format='kmb')
    a.out.write_text(json.dumps(dict(window_count=len(rows),samples=len(xs),queries=tries,hits=[h[0] for h in hits],certified=cert),indent=2)+'\n')
if __name__=='__main__':main()

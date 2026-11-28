"""Compact, reproducible receipts; lane inputs stay in pinned fixture archive."""
import collections,hashlib,json
from pathlib import Path

def record(path):
    p=Path(path);d=json.loads(p.read_text());R=d['rows']
    G=collections.defaultdict(list)
    for r in R:G[r['batch'],r['lane']].append(r)
    assert all(len(v)==2 for v in G.values())
    assert all(a['delta_wrong']==b['delta_wrong'] for a,b in G.values())
    return dict(sha=d['sha'],distinct=len(G),paired=len(R),
        paired_errors=[[sum(r['arms'][a][k] for r in R) for k in range(4)] for a in range(4)],
        same_return=sum(r['same_dense_return'] for r in R),
        return_stable_two_seeds=sum(a['residual_dense']==b['residual_dense'] for a,b in G.values()),
        unique_value_failures=sum(a[0]['arms'][2][0] for a in G.values()),
        delta_wrong=sum(r['delta_wrong'] for r in R),
        delta_wrong_coordinates=[list(k)+[r[0]['weight']] for k,r in G.items() if r[0]['delta_wrong']],
        phase_only_dense=sum(r['arms'][2][1] and not r['arms'][2][0] for r in R),
        sha256_raw=hashlib.sha256(p.read_bytes()).hexdigest())

def main():
    ret=dict(paired=[record('results/'+x+'.json') for x in ('saved','synthetic')])
    R=json.loads(Path('residuals.json').read_text())['rows']
    by_case=collections.Counter()
    by_family=collections.Counter()
    for r in R:
        by_case[(r['input_weight'],str(r['degree']))]+=1
        if r.get('unaccounted_degree')==0:
            by_family[(r['input_weight'],tuple(r['multiplicity'].items()))]+=1
    ret['residual']=dict(n=len(R),complete_pole_support=sum(r.get('unaccounted_degree')==0 for r in R),
        by_weight_degree=[list(k)+[v] for k,v in sorted(by_case.items())],
        complete_pole_families=[list(k)+[v] for k,v in sorted(by_family.items())],
        sha256_raw=hashlib.sha256(Path('residuals.json').read_bytes()).hexdigest())
    Path('paired_receipt.json').write_text(json.dumps(ret,indent=2)+'\n')

if __name__=='__main__':main()

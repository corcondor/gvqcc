"""Compact scale covariances by native lane, not a distribution estimate."""
import collections,hashlib,json
from pathlib import Path

def lab(data):
    if data['poles'] and data['unaccounted_degree']==0:return 'chart'
    return str(data['degree'])

def report(p):
    d=json.loads(p.read_text());shifts=list(map(str,d['exponent_shifts']))
    hist=collections.Counter();metrics={}
    same_internal=[0]*(len(shifts)-1)
    zero_outer=[0]*(len(shifts)-1)
    chart_degree=collections.Counter()
    for b in d['batches']:
        for key,B in b['arms'].items():
            v=metrics.setdefault(key,[0]*7)
            v[0]+=B['paid']
            for r in B['cases']:
                for i,k in enumerate(('value','phase','dirty','mask'),1):v[i]+=r[k]
                v[5]+=int(any(r[k] for k in ('value','phase','dirty','mask')))
                v[6]+=bool(r['recurrence_transport_checked'])
        for cases in zip(*(b['arms'][k]['cases'] for k in shifts),strict=True):
            seq=tuple(lab(r['inside']) for r in cases);hist[seq]+=1
            if seq[0]=='chart':
                r0=cases[0]['inside']
                chart_degree[(cases[0]['weight'],r0['degree'])]+=1
                for i,r in enumerate(cases[1:]):
                    if lab(r['inside'])!='chart':continue
                    same_internal[i]+=r0['multiplicity']==r['inside']['multiplicity']
                    zero_outer[i]+=not r['outside']['poles']
    return dict(sha=d['circuit_sha'],width=d['qubits'],ops=d['ops'],static_paid=d['static_paid'],
                lanes=sum(b['lanes'] for b in d['batches']),metrics=metrics,
                transitions={','.join(k):n for k,n in hist.items()},
                repeated_or_simple_base=[[k[0],k[1],v] for k,v in sorted(chart_degree.items())],
                same_factor_multiplicity_in_native_frame=same_internal,chart_support_gone_after_outer_unscale=zero_outer,
                raw_receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':
    a,b,c=[Path(n) for n in ('result257.json','result279.json','result_wrapper279.json')]
    d={'metrics_order':['total_executed_paid','value','raw_phase','dirty','mask','union','nonzero_recurrence_transport_checked']}
    for p in (a,b,c):d[p.stem]=report(p)
    d['wrapper_equivalence']=json.loads(Path('wrapper_equality.json').read_text())
    assert json.loads(a.read_text())['batches']==json.loads(b.read_text())['batches']
    d['base_receipts_match_by_lane']=True
    Path('scale_receipt.json').write_text(json.dumps(d,indent=2)+'\n')

#!/usr/bin/env python3
"""Independent finite check of nested-care completion and estimator/compiler."""
from __future__ import annotations
import csv,hashlib,itertools,json,time
from pathlib import Path
from score9_rebatch_alt_compile import complete_nested_columns,geometry,initial_terms
from score9_rebatch_alt_partitions import coefficients,deltas

OUT=Path('/workspace/scratch/3815fb5fae06/score9_rebatch_alt')

def gf2_rank(columns):
    # Full elimination, independent of the synthesis factorization routine.
    a=list(columns);r=0
    for bit in range(max(a,default=0).bit_length()):
        found=next((j for j in range(r,len(a)) if a[j]>>bit&1),None)
        if found is None:continue
        a[r],a[found]=a[found],a[r]
        for j in range(len(a)):
            if j!=r and a[j]>>bit&1:a[j]^=a[r]
        r+=1
    return r

def main():
    start=time.monotonic();patterns=0;assignments=0;completions=0
    for prefixes in itertools.product(range(4),repeat=3):
        if list(prefixes)!=sorted(prefixes,reverse=True):continue
        masks=[(1<<p)-1 for p in prefixes];best={};patterns+=1
        # Enumerate every full matrix, then project to its visible entries.
        # This obtains true minima without using the completion algorithm.
        for full in itertools.product(range(8),repeat=3):
            key=tuple(v&m for v,m in zip(full,masks));r=gf2_rank(full)
            best[key]=min(best.get(key,4),r);completions+=1
        for specified,minimum in best.items():
            got=complete_nested_columns(specified,masks)
            assert tuple(v&m for v,m in zip(got,masks))==specified
            assert gf2_rank(got)==minimum,(prefixes,specified,minimum,got)
            assignments+=1
    wanted_partitions={15,23,31,1039,1051,1137,1201,1219}
    selected=[]
    with (OUT/'partitions.csv').open() as f:
        for row in csv.DictReader(f):
            if int(row['partition']) in wanted_partitions and int(row['batch']) in (0,5,18):selected.append(row)
    tables=deltas();checked=0
    for row in selected:
        low,high,lm,hm=geometry(int(row['partition']));c=coefficients(tables[int(row['batch'])])
        terms,stats=initial_terms(c,lm,hm,True,True)
        assert stats['original_ranks']==[int(v) for v in row['ranks'].split()]
        assert stats['completion_ranks']==[int(v) for v in row['completion_ranks'].split()]
        assert len(terms)+int(row['bank'])==int(row['completion_joint'])
        checked+=1
    result=dict(status='PASS',exhaustive_small_matrix_check=dict(matrix_shape=[3,3],nested_care_patterns=patterns,
                  full_matrices_enumerated=completions,distinct_partial_matrices=assignments,all_minimal=True),
                cpp_python_actual_table_comparisons=checked,outputs_per_comparison=32,seconds=time.monotonic()-start,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

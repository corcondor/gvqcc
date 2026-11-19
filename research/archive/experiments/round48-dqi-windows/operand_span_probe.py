"""Ground whether adjacent 42T kernels share the same operand linear subspace."""
from relation_rank_search import windows,rank,bitpos
from collections import Counter
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1])
out=[];counts=Counter()
for s,e,g in windows(p):
    if len(g)!=42 or any(len(ps)!=2 for ps in g.values()):continue
    # g appends in program order, hence block-1 factor then block-2 factor.
    x=[[ps[b][c] for ps in g.values()] for b in range(2) for c in range(2)]
    r=[rank(v) for v in x]
    inter={f'{i}-{j}':r[i]+r[j]-rank(x[i]+x[j]) for i in [0,1] for j in [2,3]}
    full=rank(x[0]+x[1])+rank(x[2]+x[3])-rank(x[0]+x[1]+x[2]+x[3])
    counts[(tuple(r),tuple(inter.values()),full)]+=1
    out.append(dict(first_start=s,second_start=e,operand_ranks=r,operand_pair_intersection_ranks=inter,full_input_intersection_rank=full))
print(json.dumps(dict(sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),
   scope='Cut-local linear forms, all entry wires independent; detector verifies motif spans and full-window opcode contract',
   classes=[dict(operand_ranks=list(r),intersection_ranks=list(cs),full_input_intersection=f,count=n) for (r,cs,f),n in counts.items()],
   cases=out),indent=2))

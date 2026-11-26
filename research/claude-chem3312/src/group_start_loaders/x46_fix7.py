import pickle, random, sys, subprocess
from frame import *
from order_util import early_order
from x44_extract95 import run
k=int(sys.argv[1]); e=int(sys.argv[2])
F=Frame(k)
for trial in range(12):
    if trial:
        out=subprocess.run(f'timeout 200 ./d20.exe 20 150 {100+trial} 3 < perp_k{k}.txt > d20_k{k}_t{trial}.out 2> d20_k{k}_t{trial}.err',shell=True)
        f=f'd20_k{k}_t{trial}.out'
    else: f=f'd20_k{k}.out'
    for es in [1,2,3]:
        cov=run(k,f,seed=es)
        try:
            early_order(F,cov,e,random.Random(1),tries=100)
        except RuntimeError:
            print('  trial',trial,'extract seed',es,'no early set',flush=True); continue
        pickle.dump(cov,open(f'cover95_k{k}_s1.pkl','wb'))
        print('saved cover for loader',k,'trial',trial,'extract seed',es); sys.exit(0)
sys.exit(1)

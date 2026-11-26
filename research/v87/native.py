#!/usr/bin/env python3
"""V87: native reconstruction and joint quotient resynthesis of V20.
All public inputs are pinned; no scoring seeds are searched.
"""
import argparse, ast, base64, hashlib, io, json, random, struct, urllib.request, urllib.parse, zipfile
from pathlib import Path
from collections import Counter
import numpy as np
import zlib
ROOT=Path(__file__).resolve().parents[2]
NV=1219; FULL=(1<<NV)-1
DONOR="https://raw.githubusercontent.com/Acceleratorer/quantum-circuit-compilation-clean/89538d3c5f92974b426ba74a435cab9f9d7c7121/experiments/exp-074/"
DS="https://www.kaggle.com/api/v1/datasets/download/manwithacat/vqcc-apache-public-circuits/"
TABLE_SHA="ec85d969811623b5b4c7e3fff26fef2151bafedaa9a4741cb978e56ff34fbba1"
PINS={"module/payload/v20_loader_programs.b85":"ebc25b69b55299313a82b0f32fb460741c4e9a00a366fdf0097915ea94717f0a","module/payload/chemistry_weights.b85":"4c91ad004ed90595fdc83bae462a88da9fcbf5952ce5c47be9aa9da702d82808"}
SEL=list(range(11)); WQ=list(range(11,46)); OUT=[WQ[7*j+i] for j in range(5) for i in range(6)]
def sha(x): return hashlib.sha256(x).hexdigest()
def get(url):
    print("GET",url,flush=True)
    with urllib.request.urlopen(url,timeout=90) as f:return f.read()
def ds(path):return get(DS+urllib.parse.quote(path,safe=""))
def get_table(out):
    p=out/"base.npz"
    if p.exists(): b=p.read_bytes()
    else:
        b=ds("factorizations/"+TABLE_SHA[:12]+".npz"); assert sha(b)==TABLE_SHA,sha(b);p.write_bytes(b)
    assert sha(b)==TABLE_SHA
    return np.load(p,allow_pickle=False)
def donor(out):
    for path in ["module/build_chemistry.py",*PINS]:
        p=out/path;p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(get(DONOR+path))
        if path in PINS:assert sha(p.read_bytes())==PINS[path]
    # Extract the actual source functions and packed descriptions, omitting
    # the upstream portfolio orchestration, SDK, and floating point verifier.
    p=out/"module/build_chemistry.py";tree=ast.parse(p.read_text())
    f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_chemistry")
    nodes=f.body
    start=next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(a,ast.Name) and a.id=="NV" for a in t.elts) for t in n.targets))
    stop=next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="W_OLD" for t in n.targets))
    body=nodes[start:stop]
    # take() uses nonlocal pos; preserve function scope.
    wrapper=ast.parse("def extracted():\n    pass\n").body[0]
    wrapper.body=body+[ast.Return(value=ast.Tuple(elts=[ast.Name(id=x,ctx=ast.Load()) for x in ["LOADER","build_loader","build_window"]],ctx=ast.Load()))]
    ns={"np":np,"base64":base64,"zlib":zlib,"Path":Path,"__file__":str(p),"shab":sha}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),str(p),"exec"),ns)
    return ns["extracted"]()
def pack(x):
    return int.from_bytes(np.packbits(np.asarray(x,dtype=bool),bitorder="little").tobytes(),"little")
A=[pack((np.arange(NV)>>i)&1) for i in range(11)]
def words(W,k):
    if k<0:return [0]*35
    return [pack((W[:,5*k+j]>>b)&1) for j in range(5) for b in range(7)]
def unpack(v):return np.unpackbits(np.frombuffer(v.to_bytes((NV+7)//8,"little"),dtype=np.uint8),bitorder="little")[:NV]
def store(W,k,ws):
    for j in range(5): W[:,5*k+j]=sum(unpack(ws[7*j+b]).astype(W.dtype)<<b for b in range(7))
def rank_basis(vs):
    B={}
    for i,v in enumerate(vs):
        c=1<<i
        while v:
            k=v.bit_length()-1
            if k not in B:B[k]=(v,c);break
            u,t=B[k];v^=u;c^=t
    return B
def solve(B,v):
    c=0
    while v:
        k=v.bit_length()-1
        if k not in B:return None
        u,t=B[k];v^=u;c^=t
    return c
def replay(ops,ws,check_phase=True):
    q=A+ws[:]+[0]*82; debt=0;hm=0
    for op in ops:
        t,*r=op
        if t=="X":q[r[0]]^=FULL
        elif t=="CX":q[r[1]]^=q[r[0]]
        elif t=="CCX":q[r[2]]^=q[r[0]]&q[r[1]]
        elif t=="HMR":
            if check_phase:assert debt in (0,FULL),("HMR phase",hm)
            debt=q[r[0]];q[r[0]]=0;hm+=1
        elif t=="CZ":debt^=q[r[0]]&q[r[1]]
        elif t=="Z":debt^=q[r[0]]
        else:raise ValueError(op)
    if check_phase:assert debt in (0,FULL),"terminal phase"
    assert q[:11]==A and not any(q[46:]),"restoration"
    return q[11:46],hm
def count(ops):return sum(t[0]=="CCX" for t in ops)
def features(P):
    B=np.arange(NV)>>4;L=np.arange(NV)&15
    QUADS=[(0,1),(0,2),(1,2),(0,3),(1,3)]
    f=[FULL,*A,*[A[a]&A[b] for a,b in QUADS]]
    g=[sum(((x>>i)&1)<<x for x in range(77)) for i in range(7)]
    for row in P["ands"]:
        a=b=0
        for i in row[:3]:
            if i<255:a^=g[i]
        for i in row[3:]:
            if i<255:b^=g[i]
        g.append(a&b);f.append(pack([(a&b)>>int(x)&1 for x in B]))
    f += [A[2]&A[3],A[0]&A[1]&A[2],A[0]&A[1]&A[3],A[0]&A[2]&A[3],A[1]&A[2]&A[3],A[0]&A[1]&A[2]&A[3]]
    for i,row in enumerate(P["B"]):f.append(pack((L==P["cols"][i//4])&row[B]))
    assert len(f)==99
    return f
def linear(row,f):
    v=0
    for i in np.flatnonzero(row):v^=f[i]
    return v
def encode(row,n):
    return np.array([(row>>i)&1 for i in range(n)],dtype=np.uint8)
def quotient(P, ws, goal, care, seed):
    """Joint sparse support over the actual nonlinear dictionary.
    Every candidate removal is tested against every restricted output equation;
    rows are re-solved, not merely deleted. Only regular V20 banks here."""
    f=features(P);products=[linear(u,f)&linear(v,f) for u,v in zip(P["U"],P["V"])]
    # After encoding bit6 ^= bit5, all output differences are on six low bits.
    targets=[ws[7*(j//6)+j%6]^goal[7*(j//6)+j%6] for j in range(30)]
    masks=[care[j//6] for j in range(30)]
    active=list(range(len(products)));rng=random.Random(seed);rng.shuffle(active)
    def fit(ids):
        cols=f+[products[i] for i in ids]
        bases={m:rank_basis([x&m for x in cols]) for m in set(masks)}
        solutions=[solve(bases[m],v&m) for m,v in zip(masks,targets)]
        return None if any(s is None for s in solutions) else solutions
    s=fit(active)
    if s is None:return None
    # Prioritize low fanout then seeded order, but permit global coefficient changes.
    active.sort(key=lambda i:int(P["M"][i].sum()))
    for i in active[:]:
        nxt=[j for j in active if i!=j]
        z=fit(nxt)
        if z is not None:active=nxt;s=z
    s=fit(active);assert s is not None
    Q=dict(P);Q["U"]=P["U"][active];Q["V"]=P["V"][active]
    Q["M"]=np.zeros((len(active),30),np.uint8);Q["R"]=np.zeros((30,99),np.uint8)
    for j,v in enumerate(s):
        Q["R"][j]=encode(v,99)
        Q["M"][:,j]=encode(v>>99,len(active))
    return Q
def live_rewrite(ops,ws):
    # Native exact Boolean-domain product recovery across physical basis
    # changes, including cache lifetimes. Never use word bits as new controls.
    q=A+ws[:]+[0]*82;out=[];n=0
    for op in ops:
        t,*r=op
        if t=="CCX":
            a,b,c=r;p=q[a]&q[b]
            wires=[j for j in range(128) if j!=c and (j<11 or j>=46)]
            B=rank_basis([FULL]+[q[j] for j in wires])
            v=solve(B,p)
            if v is not None and v.bit_count()<=24:
                if v&1:out.append(("X",c))
                for i,j in enumerate(wires):
                    if v>>(i+1)&1:out.append(("CX",j,c))
                n+=1
            else:out.append(op)
            q[c]^=p
        else:
            out.append(op)
            if t=="CX":q[r[1]]^=q[r[0]]
            elif t=="X":q[r[0]]^=FULL
            elif t=="HMR":q[r[0]]=0
    return out,n
def write_kmb(path,ops):
    C=[bytearray() for _ in range(12)]
    def add(k,x):C[k].extend(struct.pack("<I",x))
    code={"X":17,"CX":33,"CCX":49,"HMR":80,"CZ":160,"Z":144}
    for t,*r in ops:
        v=code[t];C[1].append(v); ar=(v>>4)&3
        for k,x in zip({1:[7],2:[5,6],3:[2,3,4]}[ar],r):add(k,x)
        if v&64:add(8,0)
        if v&128:add(9,0)
    n=[len(C[1]),len(C[2])//4,len(C[5])//4,len(C[7])//4,len(C[8])//4,len(C[9])//4,0,0,0]
    with path.open("wb") as f:
        f.write(struct.pack("<16s4I9Q",bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf"),2,128,1,6,*n))
        for name,w in [("selection",SEL)]+[(f"word_{j}",WQ[7*j:7*j+7]) for j in range(5)]:
            b=name.encode();d=struct.pack("<II",len(b),len(w))+b+struct.pack("<"+"I"*len(w),*[x|(1<<31) for x in w])
            f.write(struct.pack("<QQ",0,len(d))+d)
        for k in range(1,11):f.write(struct.pack("<QQ",k,len(C[k]))+C[k])
        f.write(struct.pack("<QQQ",11,8,0))
def read_kmb(path):
    d=path.read_bytes();h=struct.unpack_from("<16s4I9Q",d);assert h[1]==2 and h[2]<=128
    pos=104;c={};regs={}
    while pos<len(d):
        k,n=struct.unpack_from("<QQ",d,pos);pos+=16;s=d[pos:pos+n];pos+=n
        if k==0:
            l,w=struct.unpack_from("<II",s);name=s[8:8+l].decode()
            regs[name]=[x&0x7fffffff for x in struct.unpack_from("<"+"I"*w,s,8+l)]
        else:c[k]=s
    assert regs=={"selection":SEL,**{f"word_{j}":WQ[7*j:7*j+7] for j in range(5)}},regs
    it={k:iter(x[0] for x in struct.iter_unpack("<I",c[k])) for k in range(2,10)}
    names={17:"X",33:"CX",49:"CCX",80:"HMR",160:"CZ",144:"Z"}
    ops=[]
    for t in c[1]:
        assert t in names,t
        ar=(t>>4)&3
        r=[next(it[k]) for k in {1:[7],2:[5,6],3:[2,3,4]}[ar]]
        if t&64:assert next(it[8])==0
        if t&128:assert next(it[9])==0
        ops.append((names[t],*r))
    assert len(ops)==h[5]
    return ops
def base0(out,W):
    # Prefer pinned source-built loader if present in the public catalogue.
    p=out/"base0.kmb"
    if p.exists():return read_kmb(p)
    # Manifest used solely to locate published circuit families, not to infer equivalence.
    manifest=ds("manifest.csv").decode("utf-8");(out/"manifest.csv").write_text(manifest)
    import re
    families=list(dict.fromkeys(re.findall(r"circuits/chemistry/([0-9a-f]{12})/angle_k_0\.kmb",manifest)))
    families+=list(dict.fromkeys(re.findall(r"circuits/chemistry/([0-9a-f]{12})",manifest)))
    families=list(dict.fromkeys(families))
    print("manifest header:",manifest.splitlines()[:2], "families",len(families),flush=True)
    # Search catalogue for a compatible k0; equality on every legal address
    # is required, not merely equal counts. Prefer cheapest independently tested.
    best=None;bestb=None
    for fam in families[:100]:
        try:
            b=ds("circuits/chemistry/"+fam+"/angle_k_0.kmb")
            p.write_bytes(b);ops=read_kmb(p)
            r,_=replay(ops,[0]*35)
            if r!=words(W,0):continue
            assert replay(ops,r)[0]==[0]*35
            if best is None or count(ops)<count(best):best=ops;bestb=b;print("compatible k0",fam,count(ops),sha(b),flush=True)
            if count(best)<=237:break
        except Exception as e:print("skip k0",fam,str(e)[:160],flush=True)
    if best is None:p.unlink(missing_ok=True);raise RuntimeError("No compatible published bank0 found")
    p.write_bytes(bestb);return best
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--seeds",type=int,default=2);a=p.parse_args()
    out=a.out;out.mkdir(exist_ok=True,parents=True);P,build,window=donor(out);data=get_table(out)
    W=data["angle_words"].copy();E=data["tree_edges"];initial=W.copy()
    assert W.shape==(NV,75)
    # Exact structural zeros in a rooted Givens tree: no floating threshold.
    alive=[FULL]+[0]*75;care=[]
    for j,(p,c) in enumerate(E):
        assert alive[c]==0
        care.append(alive[p]);v=W[:,j]
        alive[c]=alive[p]&pack((v%64)!=0);alive[p]&=pack((v%64)!=32)
    k0=base0(out,W);ws=[0]*35;ref=[k0];refwords=[words(W,0)]
    assert replay(k0,ws)[0]==refwords[0]
    for k in range(1,15):
        pp=P[k];ops=window(pp,WQ) if isinstance(pp,bytes) else build(pp,SEL,WQ)
        r,_=replay(ops,refwords[-1]);assert replay(ops,r)[0]==refwords[-1]
        goal=words(W,k)
        for j in range(5):
            for b in range(7):assert not ((r[7*j+b]^goal[7*j+b])&care[5*k+j]),(k,j,b)
        ref.append(ops);refwords.append(r)
    old=sum(map(count,ref));print("actual reconstructed counts",[count(x) for x in ref],old,flush=True)
    # Strict exact reconstruction first. A second family uses only globally
    # dead suffix slots as care freedom, so no new active word can change.
    best=ref;bestwords=refwords;bestreport=[]
    for mode in ["exact","global_dead_suffix"]:
        cand=[];rows=[];records=[];ws=[0]*35
        for k,ops0 in enumerate(ref):
            goal=refwords[k];ops=ops0;baseline,hm=replay(ops,ws)
            if mode=="exact":masks=[FULL]*5
            else:
                masks=[]
                for j in range(5):
                    m=0
                    for t in range(k,15):m|=care[5*t+j]
                    masks.append(m)
            def admissible(op):
                try:
                    r,_=replay(op,ws)
                    if replay(op,r)[0]!=ws:return None
                    if any((r[7*j+b]^goal[7*j+b])&masks[j] for j in range(5) for b in range(7)):return None
                    return r
                except AssertionError:return None
            chosen=admissible(ops)
            if k in P and not isinstance(P[k],bytes):
                for seed in range(a.seeds):
                    pp=quotient(P[k],ws,goal,masks,seed)
                    if pp is None:continue
                    trial=build(pp,SEL,WQ)
                    r=admissible(trial)
                    if r is not None and count(trial)<count(ops):ops,chosen=trial,r
            trial,removed=live_rewrite(ops,ws)
            r=admissible(trial)
            if r is not None and count(trial)<count(ops):ops,chosen=trial,r
            if chosen is None:break
            cand.append(ops);rows.append(chosen);ws=chosen
            records.append({"bank":k,"before":count(ops0),"after":count(ops),"hmr":hm})
            print(mode,records[-1],flush=True)
        if len(cand)==15 and sum(map(count,cand))<sum(map(count,best)):
            best,bestwords,bestreport=cand,rows,records
    for name,ops,rows in [("reference",ref,refwords),("candidate",best,bestwords)]:
        d=out/name;d.mkdir(exist_ok=True);W=initial.copy();prev=[0]*35
        for k,(o,r) in enumerate(zip(ops,rows)):
            f=d/f"angle_k_{k}.kmb";write_kmb(f,o);op=read_kmb(f)
            assert replay(op,prev)[0]==r and replay(op,r)[0]==prev
            for j in range(5):
                for b in range(7):assert not ((r[7*j+b]^words(initial,k)[7*j+b])&care[5*k+j])
            store(W,k,r);prev=r
        # Keep numerical weights unchanged except for the explicitly published V20 refit.
        import lzma
        raw=lzma.decompress(base64.b85decode((out/"module/payload/chemistry_weights.b85").read_text().strip()))
        assert sha(raw)=="5b63a8f6d0be88249a8b0bdd2d56bc42e9c456e3936dfa35e5e066fb0886d2c1"
        arrays={k:data[k] for k in ("U","W","H2_I","H1_I","Hsym_lower","tree_edges","angle_words")}
        n=9*127*46*8;arrays["W"]=np.frombuffer(raw[:n],dtype="<f8").reshape(9,127,46);arrays["H2_I"]=np.frombuffer(raw[n:],dtype="<f8").reshape(9,46);arrays["angle_words"]=W
        np.savez(d/"submission.npz",**arrays)
    result={"reference_counts":[count(x) for x in ref],"candidate_counts":[count(x) for x in best],"reference_paid":old,"candidate_paid":sum(map(count,best)),"independent_serialized_replay":True,"address_count":NV,"qubit_cap":128,"bank_reports":bestreport,"official_verifier":"not_run","arbitrary_target_xor":"not_proved: original donor uses live word tags", "status":"RESEARCH_ONLY"}
    (out/"receipt.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result),flush=True)
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Step-1 strict pipeline: qrom-plan -> tensorqrom -> real KMB -> kmsim + phase proof."""
from __future__ import annotations
import argparse,base64,hashlib,json,subprocess,sys,time,zlib
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"third_party"/"manwithacat"))
import tensorqrom as tq
import kmsim
import kickmix as km

PUBLIC=[245,240,217,217,217,240,217,240,211,217,217,240,217,211,211]
GROUPS=[[3,7,11,15],[5,6,13,14],[9,10,12]]
GRP="3,7,11,15;5,6,13,14;9,10,12"

def cmd(argv,timeout=300):
    t=time.monotonic()
    try:
        p=subprocess.run(list(map(str,argv)),capture_output=True,text=True,timeout=timeout)
        try: v=json.loads(p.stdout)
        except ValueError:v={"stdout_tail":p.stdout[-1000:]}
        return {"rc":p.returncode,"sec":round(time.monotonic()-t,2),"result":v,"stderr":p.stderr[-800:]}
    except Exception as e:return {"rc":-1,"sec":round(time.monotonic()-t,2),"result":{},"stderr":str(e)}

def fixture(path):
    j=json.loads(path.read_text())
    assert j["shape_words"]==[1219,75] and j["shape_edges"]==[75,2]
    raw=zlib.decompress(base64.b85decode(j["payload"]))
    assert hashlib.sha256(raw).hexdigest()==j["raw_sha256"]
    w=np.frombuffer(raw[:1219*75],dtype=np.uint8).reshape(1219,75).copy()
    assert np.all(w<=127)
    w|=((w>>6)&1)<<7
    return w,j["raw_sha256"]

def coded_columns(w):
    affine={sum((((mask&i).bit_count()&1)^c)<<i for i in range(16))
            for mask in range(16) for c in range(2)}
    return {j for j in range(75) if all(
        sum((int(w[a+i,j])&1)<<i for i in range(16)) in affine
        for a in range(0,1219-1219%16,16))}

def delta_of(w,coded,k):
    d=w[:,5*k:5*k+5].copy()
    if k:d^=w[:,5*k-5:5*k]
    co=[i for i in range(5) if 5*k+i in coded and (k==0 or 5*k-5+i in coded)]
    d=tq.pad_affine(d,co) if co else np.pad(d,((0,-len(d)%16),(0,0)))
    return d,co

def plan_search(qrom,words,k,work,counts,seed_count,trials,samples):
    work.mkdir(parents=True,exist_ok=True)
    attempts=[];best=None
    for mode,count in [("pair",None)]+[("structured",c) for c in counts]:
        tag=mode+(str(count) if count is not None else "")
        template=work/(tag+".template.txt")
        template.write_text(f"k {k}\ngroups {GRP}\n"+(f"count {count}\n" if count is not None else ""))
        prefix=work/tag
        rr=cmd([qrom,"replan",words,template,mode,0,seed_count,trials,samples,0,prefix],timeout=300)
        item={"tag":tag,"upstream":rr}
        plan=work/(tag+"_best.txt")
        if rr["rc"]==0 and plan.exists():
            ck=cmd([qrom,"check-plan",words,plan],timeout=180)
            item["check_plan"]=ck
            if ck["rc"]==0 and ck["result"].get("ok"):
                terms=[]
                for line in plan.read_text().splitlines():
                    t=line.split()
                    if t and t[0]=="term":terms.append(tuple(map(int,t[1:6])))
                if terms:
                    T=80+len(terms) # Rust qrom-plan reports 89+len(terms) (for 1363 rows).
                    item.update({"terms":len(terms),"corrected_model_T":T})
                    if best is None or T<best["model_T"]:
                        best={"model_T":T,"terms":terms,"plan":str(plan),"strategy":tag}
        attempts.append(item)
    return best,attempts

def kmsim_check(kmx,delta,k,words):
    ops,regs=kmsim.parse(kmx)
    names=kmsim.register_names(kmx)
    Q,B=kmsim.sizes(ops,regs)
    sq=regs[names["selection"]]
    wq=[regs[names[f"word_{j}"]] for j in range(5)]
    assert len(sq)==11 and all(len(w)==8 for w in wq)
    sel=np.arange(1219,dtype=np.int64)
    active=set(sq)|{x for w in wq for x in w}
    scratch=[q for q in range(Q) if q not in active]
    out=[]
    for mode,seed in [("zero",0),("previous",11),("current",19),("random",29)]:
        rng=np.random.default_rng(seed+k)
        if mode=="zero":initial=np.zeros((1219,5),np.uint8)
        elif mode=="previous":initial=(words[:,5*(k-1):5*k].copy() if k else np.zeros((1219,5),np.uint8))
        elif mode=="current":initial=words[:,5*k:5*k+5].copy()
        else:initial=rng.integers(0,128,(1219,5),dtype=np.uint8)
        initial|=((initial>>6)&1)<<7
        s=kmsim.Sim(ops,Q,B,1219,seed+k)
        for i,q in enumerate(sq):s.q[q]=((sel>>i)&1).astype(bool)
        for j in range(5):
            for i,q in enumerate(wq[j]):s.q[q]=((initial[:,j]>>i)&1).astype(bool)
        s.run()
        got=np.zeros_like(initial)
        for j in range(5):
            for i,q in enumerate(wq[j]):got[:,j]|=s.q[q].astype(np.uint8)<<i
        errors=int(np.count_nonzero(got != (initial^delta[:1219])))
        dirty=int(np.count_nonzero(s.q[scratch]))
        phases=int(np.count_nonzero(s.ph))
        resets=int(np.count_nonzero(s.bad_reset))
        selok=all(np.array_equal(s.q[q],((sel>>i)&1).astype(bool)) for i,q in enumerate(sq))
        out.append(dict(mode=mode,addresses=1219,incorrect_word_values=errors,dirty_bits=dirty,
                        bad_phase_shots=phases,bad_resets=resets,selection_ok=selok,
                        pass_all=bool(selok and not(errors or dirty or phases or resets))))
    return out,ops,regs,names

def symbolic_hmr(ops,regs,names,delta,k,words):
    # Strict proof of every HMR measurement *branch* for the tensorqrom DEL_AND
    # instruction subset; a supported measurement result may not control a
    # change of a quantum bit, only Z/CZ phase correction.
    N=1219; full=(1<<N)-1
    selq=regs[names["selection"]];wq=[regs[names[f"word_{j}"]] for j in range(5)]
    addr=np.arange(N,dtype=np.uint16)
    selbits=[sum(((a>>i)&1)<<a for a in range(N)) for i in range(11)]
    nq=kmsim.sizes(ops,regs)[0]
    active_qubits=set(selq)|{q for w in wq for q in w}
    rows=[]
    for mode in ("zero","previous","current","random"):
        if mode=="zero":initial=np.zeros((N,5),np.uint8)
        elif mode=="previous":initial=(words[:,5*(k-1):5*k].copy() if k else np.zeros((N,5),np.uint8))
        elif mode=="current":initial=words[:,5*k:5*k+5].copy()
        else:initial=np.random.default_rng(9222+k).integers(0,128,(N,5),dtype=np.uint8)
        initial|=((initial>>6)&1)<<7
        qs=[0]*nq
        for i,q in enumerate(selq):qs[q]=selbits[i]
        for j in range(5):
            for i,q in enumerate(wq[j]):
                qs[q]=sum(((int(initial[a,j])>>i)&1)<<a for a in range(N))
        phase={};active={};n_hmr=0;resets=0
        for oi,(name,q,b,cond,angle) in enumerate(ops):
            if name=="X" and cond is None:qs[q[0]]^=full
            elif name=="CX" and cond is None:qs[q[1]]^=qs[q[0]]
            elif name=="CCX" and cond is None:qs[q[2]]^=qs[q[0]] & qs[q[1]]
            elif name=="HMR" and cond is None:
                key=(b[0],n_hmr);n_hmr+=1;active[b[0]]=key
                phase[key]=qs[q[0]];qs[q[0]]=0
            elif name=="Z" and cond in active:phase[active[cond]]^=qs[q[0]]
            elif name=="CZ" and cond in active:phase[active[cond]]^=qs[q[0]]&qs[q[1]]
            elif name=="R" and cond is None:resets+=qs[q[0]].bit_count();qs[q[0]]=0
            elif name=="INFO_TAG":pass
            else:raise ValueError(f"unsupported phase operation {oi}: {name}, cond={cond}")
        e=initial^delta[:N]
        word_err=0
        for j in range(5):
            for i,q in enumerate(wq[j]):
                expected=sum(((int(e[a,j])>>i)&1)<<a for a in range(N))
                word_err+=(qs[q]^expected).bit_count()
        selection_errors=sum((qs[q]^selbits[i]).bit_count() for i,q in enumerate(selq))
        scratch_errors=sum(x.bit_count() for i,x in enumerate(qs) if i not in active_qubits)
        phase_errors=sum(x.bit_count() for x in phase.values())
        passed=not any((word_err,selection_errors,scratch_errors,phase_errors,resets))
        rows.append(dict(mode=mode,addresses=N,hmr_events=n_hmr,phase_coeff_error=phase_errors,
                         word_error_bits=word_err,selection_error_bits=selection_errors,
                         scratch_error_bits=scratch_errors,bad_reset=resets,pass_all=passed))
    return rows

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--qrom-plan",required=True)
    pa.add_argument("--banks",default="8")
    pa.add_argument("--counts",default="240,270")
    pa.add_argument("--seeds",type=int,default=1)
    pa.add_argument("--trials",type=int,default=3)
    pa.add_argument("--samples",type=int,default=8)
    pa.add_argument("--out",type=Path,default=Path("outputs/step1"))
    a=pa.parse_args();t0=time.monotonic()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    w,raw_sha=fixture(HERE/"v8_c46_angle_fixture_public.json")
    words=out/"v8_words_signed_int64.npy";np.save(words,w.astype(np.int64))
    cc=coded_columns(w)
    bank_ids=list(range(15)) if a.banks=="all" else [int(v) for v in a.banks.split(",")]
    report=dict(status="STEP1_RUNNING",source_raw_sha=raw_sha,public_T=3357,coded_columns=sorted(cc),
                banks=[],qrom_plan_fixed_cache=89,actual_monomial_cache=80,
                reference_public_T=PUBLIC)
    for k in bank_ids:
        b0=time.monotonic()
        row=dict(k=k,public_T=PUBLIC[k],public_Q=128,pass_reproduce=False)
        try:
            delta,coded=delta_of(w,cc,k)
            row.update(coded_words=coded,addressed_rows=len(delta),
                       qrom_info=cmd([a.qrom_plan,"info",words,k],timeout=180))
            best,attempts=plan_search(a.qrom_plan,words,k,out/f"k{k}",
                                      [int(v) for v in a.counts.split(",")],
                                      a.seeds,a.trials,a.samples)
            row["attempts"]=attempts
            if best is not None:
                terms=best["terms"]; row["chosen_plan"]={key:val for key,val in best.items() if key!="terms"}
                cir=tq.build_circuit(delta,terms,11,8,4,groups=GROUPS,scratch=True)
                folder=out/f"k{k}";folder.mkdir(exist_ok=True)
                kmb=folder/f"angle_k_{k}.kmb";kmx=folder/f"angle_k_{k}.kmx"
                cir.to_file(str(kmb),format="kmb");cir.to_file(str(kmx),format="kmx")
                T=int(cir.operation_statistics().num_toffoli_like);Q=int(cir.num_qubits)
                row.update(real_T=T,real_Q=Q,T_delta=T-PUBLIC[k],
                           KMB_SHA256=hashlib.sha256(kmb.read_bytes()).hexdigest(),KMB=str(kmb),
                           within_128Q=Q<=128)
                rr,ops,regs,names=kmsim_check(kmx,delta,k,w);row["kmsim"]=rr
                ph=symbolic_hmr(ops,regs,names,delta,k,w);row["symbolic_hmr"]=ph
                row["pass_logic"]=all(x["pass_all"] for x in rr+ph)
                row["pass_reproduce"]=row["pass_logic"] and Q<=128 and T==PUBLIC[k]
            else:row["reason"]="No valid qrom-plan produced"
        except Exception as ex:row["error"]=type(ex).__name__+": "+str(ex)
        row["sec"]=round(time.monotonic()-b0,2);report["banks"].append(row)
        (out/"receipt.json").write_text(json.dumps(report,indent=2)+"\n")
        print("STEP1",k,"T/Q",row.get("real_T"),row.get("real_Q"),
              "public",PUBLIC[k],"logic",row.get("pass_logic"),"error",row.get("error"),flush=True)
    report["generated_banks"]=sum("real_T" in r for r in report["banks"])
    report["generated_total_T"]=sum(r["real_T"] for r in report["banks"]) if report["generated_banks"]==15 else None
    report["reproduce_all"]=len(report["banks"])==15 and all(r["pass_reproduce"] for r in report["banks"])
    report["status"]="STEP1_ALL_PASS" if report["reproduce_all"] else "STEP1_GATE_FAILED_NO_STEP2"
    report["duration_s"]=round(time.monotonic()-t0,2)
    (out/"receipt.json").write_text(json.dumps(report,indent=2)+"\n")
    print("RESULT",report["status"],"generated",report["generated_banks"],flush=True)
    return 0 if report["reproduce_all"] else 3

if __name__=="__main__":raise SystemExit(main())

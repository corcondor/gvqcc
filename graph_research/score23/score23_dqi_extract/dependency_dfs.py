"""Reschedule exact extractor windows by traversal of their gate DAGs."""

from argparse import ArgumentParser
from bisect import bisect_right
from collections import defaultdict
from csv import DictReader
from heapq import heappop, heappush
import json
import mmap
from pathlib import Path
from shutil import copyfileobj
import sys

import kickmix as km
import numpy as np


XOR = {0x11, 0x21, 0x31}
MEASURE = {0x12, 0x50}
DIAGONAL = {0x10, 0x20, 0x30}
SWAP = {0x22, 0x32}
ALLOWED = XOR | MEASURE | DIAGONAL | SWAP


def access(op):
    kind=op.opcode & 127
    q=op.qubits
    write=set(q[-1:]) if kind in XOR | MEASURE else set(q[-2:]) if kind in SWAP else set()
    read=set(q)-write if kind in XOR else set(q)
    # The bit IDs are in a distinct namespace. HMR/R order is pinned so
    # that the same random stream can be used in paired native execution.
    if op.condition is not None:
        read.add(1_000_000+op.condition)
    if op.bit is not None:
        assert kind==0x50
        write.add(1_000_000+op.bit)
    if kind in MEASURE:
        write.add(-1)
    return read,write


def dependency(ops):
    previous={}
    previous_reads=defaultdict(set)
    pred=[]
    successors=[[] for _ in ops]
    for i,op in enumerate(ops):
        read,write=access(op)
        ancestors={previous[q] for q in read|write if q in previous}
        for q in write:
            ancestors.update(previous_reads[q])
        for q in write:
            previous[q]=i
            previous_reads[q].clear()
        for q in read-write:
            previous_reads[q].add(i)
        pred.append(ancestors)
        for older in ancestors:
            successors[older].append(i)
    return pred,successors


def cleanup_first(ops,pred,succ,mode):
    n=len(ops)
    distance=[n+1]*n
    for i in range(n-1,-1,-1):
        if ops[i].opcode & 127 in MEASURE:
            distance[i]=0
        else:
            distance[i]=min((distance[j]+1 for j in succ[i]),default=n+1)
    if mode=="dfs":
        order=[]
        visited=set()
        roots=sorted(range(n),key=lambda i:(ops[i].opcode & 127 not in MEASURE,i))
        for root in roots:
            stack=[(root,False)]
            while stack:
                i,finished=stack.pop()
                if i in visited:
                    continue
                if finished:
                    visited.add(i)
                    order.append(i)
                else:
                    stack.append((i,True))
                    stack.extend((j,False) for j in sorted(pred[i],reverse=True)
                                 if j not in visited)
        return order
    counts=[len(p) for p in pred]
    pending=[]
    for i,count in enumerate(counts):
        if not count:
            heappush(pending,(distance[i],i))
    order=[]
    while pending:
        _,i=heappop(pending)
        order.append(i)
        for j in succ[i]:
            counts[j]-=1
            if not counts[j]:
                heappush(pending,(distance[j],j))
    assert len(order)==n
    return order


def evaluate(order,ops,entered):
    value=[2 if q in entered else 0 for q in range(889)]
    live=set(entered)
    widths=[]
    known=lambda x,y:x^y if x<2 and y<2 else 2
    for ix in order:
        op=ops[ix]
        base=op.opcode&127
        q=op.qubits
        live.update(q)
        widths.append(len(live))
        prev=[value[j] for j in q]
        out={}
        if base in MEASURE:
            out[q[0]]=0
        elif base==0x11:
            out[q[0]]=known(prev[0],1)
        elif base==0x21:
            out[q[1]]=known(*prev)
        elif base==0x31:
            p=0 if not prev[0] or not prev[1] else 1 if prev[:2]==[1,1] else 2
            out[q[2]]=known(prev[2],p)
        elif base==0x22:
            out={q[0]:prev[1],q[1]:prev[0]}
        elif base==0x32:
            if prev[0]==1:
                out={q[1]:prev[2],q[2]:prev[1]}
            elif prev[0]==2 and prev[1]!=prev[2]:
                out={q[1]:2,q[2]:2}
        for j,v in out.items():
            value[j]=2 if op.condition is not None and value[j]!=v else v
        for j in q:
            if value[j]==0 and j>=840:
                live.discard(j)
    return dict(peak=max(widths), high_positions=sum(w>=889 for w in widths),
                high_881_positions=sum(w>=881 for w in widths)), value


def build(ops,order):
    b=km.CircuitBuilder()
    q=b.create_quantum_register(889,"domain")
    keys=sorted({k for o in ops for k in (o.bit,o.condition) if k is not None})
    bit=b.create_classical_register(len(keys),"classical")
    lookup=dict(zip(keys,bit))
    for idx in order:
        op=ops[idx]
        gate=op.opcode&127
        args=tuple(q[i] for i in op.qubits)
        if op.condition is not None:
            b.push_condition(lookup[op.condition])
        if gate==0x50:
            b.hmr(*args,lookup[op.bit])
        else:
            name={0x11:"x",0x21:"cx",0x31:"ccx",0x22:"swap",0x32:"cswap",
                  0x12:"reset",0x10:"z",0x20:"cz",0x30:"ccz"}[gate]
            getattr(b,name)(*args)
        if op.condition is not None:
            b.pop_condition()
    return b.finish_circuit(),len(keys)


def compare(ops, orders, entered, seed=72):
    rng=np.random.default_rng(seed)
    cases=1024
    initial=rng.integers(0,2,size=(889,cases),dtype=np.uint8).astype(bool)
    for q in set(range(889))-entered:
        initial[q]=False
    reference=None
    for order in orders:
        circuit,n=build(ops,order)
        data=circuit.register_data["domain"]
        control=circuit.register_data["classical"]
        sim=km.Simulator(batch_size=cases,seed=103)
        sim.use_same_registers_as(circuit)
        sim.write_across_shots(data,initial)
        if n:
            # Reinitialize both circuits from the same external bits.
            bit_array=np.random.default_rng(seed+1).integers(0,2,size=(n,cases),
                                                            dtype=np.uint8).astype(bool)
            sim.write_across_shots(control,bit_array)
        sim.do(circuit)
        state=(sim.read_across_shots(data),sim.read_phase_flipped_across_shots())
        if n:
            state+= (sim.read_across_shots(control),)
        if reference is None:
            reference=state
        else:
            assert all(np.array_equal(a,b) for a,b in zip(reference,state))
    return cases


def splice_selected(base,blocks,output,encode):
    """Choose disjoint improvements and retain every untouched column byte."""
    blocks=sorted(blocks,key=lambda row:row[1])
    ends=[row[1] for row in blocks]
    dp=[(0,())]
    for ix,row in enumerate(blocks):
        earlier=bisect_right(ends,row[0],0,ix)
        candidate=(dp[earlier][0]+row[2],(*dp[earlier][1],ix))
        dp.append(max(dp[-1],candidate))
    selected=[blocks[ix] for ix in dp[-1][1]]
    if not selected:
        return []
    with base.path.open("rb") as src, output.open("xb") as dst:
        copyfileobj(src,dst,length=1<<20)
    with output.open("r+b") as stream, mmap.mmap(stream.fileno(),0) as dst:
        for lo,hi,_,original,new in selected:
            a,b=encode(original),encode(new)
            for kind in range(1,11):
                left,right=base.column_range(kind,lo,hi)
                offset=base.packets[kind]["payload_offset"]
                assert len(a[kind])==len(b[kind])==right-left
                assert dst[offset+left:offset+right]==a[kind]
                dst[offset+left:offset+right]=b[kind]
    return [{"start":a,"end":b,"predicted_positions_retired":c} for a,b,c,_,_ in selected]


def main():
    p=ArgumentParser(description=__doc__)
    for name in ("circuit","peaks","lifetimes","repo","central","out"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--emit",type=Path)
    a=p.parse_args()
    sys.path[:0]=[str(a.repo),str(a.central)]
    from census import open_columns,digest
    from dqi_ccx_peephole import BinaryCircuit
    import kmb_profile as fmt
    from outcome_dqi_chart_splice_norm import encode

    tape=open_columns(a.circuit,BinaryCircuit,fmt)
    by_family=defaultdict(list)
    with a.peaks.open() as f:
        for row in DictReader(f,delimiter="\t"):
            caller=row["caller"]
            if caller.startswith("extractor."):
                by_family[caller].append((int(row["start"]),int(row["stop_exclusive"])))
    windows=[]
    for label,selected in by_family.items():
        positions={0,1,len(selected)//4,len(selected)//2,3*len(selected)//4,len(selected)-1}
        positions.update(sorted(range(len(selected)),key=lambda i:selected[i][1]-selected[i][0],
                                reverse=True)[:5])
        for i in sorted(positions):
            start,stop=selected[i]
            a0,b0=max(0,start-2048),min(len(tape.opcodes),stop+2048)
            # Split at PUSH/POP or external classical writes. Such gates
            # and locks remain untouched by this local transformation.
            block=list(tape.operations(a0,b0))
            start0=next((j+1 for j in range(start-a0-1,-1,-1)
                         if block[j].opcode&127 not in ALLOWED),0)
            end0=next((j for j in range(stop-a0,len(block))
                       if block[j].opcode&127 not in ALLOWED),len(block))
            ops=block[start0:end0]
            if all(x.opcode&127 in ALLOWED for x in ops):
                windows.append((a0+start0,a0+end0,label,ops))
    start_ids={begin:set(range(840)) for begin,_,_,_ in windows}
    with a.lifetimes.open() as f:
        for row in DictReader(f,delimiter="\t"):
            q,l,r=(int(row[k]) for k in ("q","first","last"))
            if q>=840:
                for begin,live in start_ids.items():
                    if l<begin<=r:
                        live.add(q)
    records=[]
    winners=[]
    for lo,hi,label,ops in windows:
        prev,succ=dependency(ops)
        orders=[list(range(len(ops))),cleanup_first(ops,prev,succ,"dfs"),
                cleanup_first(ops,prev,succ,"priority")]
        for order in orders:
            positions={v:i for i,v in enumerate(order)}
            assert all(positions[j]<positions[i] for i,pred in enumerate(prev) for j in pred)
        entered=start_ids[lo]
        metrics=[evaluate(order,ops,entered)[0] for order in orders]
        verified=compare(ops,orders,entered)
        best=min(range(len(orders)),key=lambda j:(metrics[j]["peak"],metrics[j]["high_positions"],
                                                 metrics[j]["high_881_positions"]))
        saved=metrics[0]["high_positions"]-metrics[best]["high_positions"]
        if saved>0:
            winners.append((lo,hi,saved,ops,[ops[ix] for ix in orders[best]]))
        records.append(dict(range=[lo,hi],caller=label,edges=sum(map(len,prev)),
                            metrics=dict(zip(("original","dfs","cleanup_priority"),metrics)),
                            shots_per_schedule=verified))
        print(records[-1],flush=True)
    report=dict(source_sha256=digest(a.circuit),records=records)
    if a.emit is not None:
        report["spliced"]=splice_selected(tape,winners,a.emit,encode)
        if report["spliced"]:
            report["candidate_sha256"]=digest(a.emit)
    tape.close()
    a.out.write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    main()

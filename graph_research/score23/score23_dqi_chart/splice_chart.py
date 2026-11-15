"""Bind the saved 877-wire third chart and splice it into the latest DQI tape."""
from argparse import ArgumentParser
from bisect import bisect_left
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

import dqi_ccx_peephole as binary
import kmb_profile as kp
import kmb_splice as splice
from outcome_dqi_chart_match import match
from outcome_dqi_chart_splice_norm import encode
from splice_phase_peaks import HEADER_COUNTS, bit_accesses, classical_abi, condition_scopes

BASE = "3e50000e18f2f1746de3270cf88c10d7b6ea3f577988a3cd13ba1f90a8da48e2"
FULL_WORD = "9888d2b455cdf4e22f2e0dd5af1e8032c6370e644f44e5ac5b071641b68793e0"
E4 = "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"
SIX_A = "6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02"
PREVIOUS_SPANS = [(17097498,17126973),(54178102,54213318)]


def forward_range(first, last, patches):
    delta = 0
    for old_lo,old_hi,new_lo,new_hi in sorted(patches):
        assert old_hi <= first or last <= old_lo, (first,last,old_lo,old_hi)
        if old_hi <= first:
            delta += (new_hi-new_lo) - (old_hi-old_lo)
    return first+delta, last+delta


def hmr_trace(op):
    return op.opcode, list(op.qubits), op.bit, op.condition, (op.angle or b"").hex()


def hmr_saved(op):
    return op["opcode"], op["qubits"], op["bit"], op["condition"], op["angle_hex"]


def tape_spans(root, original, latest_dir, latest_sha):
    p=root/"dqi_phase_peak"/"splice_all.json"
    phase_data=json.loads(p.read_text())["output"]
    p=root/"score22_dqi_crt_phase"/"splice.json"
    crt_data=json.loads(p.read_text())
    loan_data=json.loads((latest_dir/"loan_splice.json").read_text())
    assert phase_data["sha256"]==crt_data["input_sha256"]
    assert crt_data["output_sha256"]==loan_data["input_sha256"]
    assert loan_data["output_sha256"]==latest_sha
    hmr_data=json.loads((original/"patch.json").read_text())
    assert hmr_data["source_sha256"]==SIX_A and hmr_data["candidate_sha256"]==E4
    hmr_edits={x["index"]:x for x in hmr_data["edits"]}
    hmr_ranges=[]; plus=0
    for start,edit in sorted(hmr_edits.items()):
        stop=start+len(edit["new"])
        hmr_ranges.append((start,start+1,start+plus,stop+plus))
        plus += stop-start-1
    phases=[tuple(x[i] for i in ("old_start","old_end","new_start","new_end")) for x in phase_data["sites"]]
    crt=[tuple(x[i] for i in ("old_start","old_end","new_start","new_end")) for x in crt_data["splices"]]
    loans=[tuple(x[i] for i in ("start","end","new_start","new_end")) for x in loan_data["splice"]]
    spans=[]
    for first,end in PREVIOUS_SPANS:
        offset=sum((d-c)-(b-a) for a,b,c,d in hmr_ranges if b<=first)
        span=(first+offset,first+offset+(end-first)+sum(
            len(hmr_edits[i]["new"])-1 for i in hmr_edits if first<=i<end))
        for edits in (phases,crt,loans):
            span=forward_range(*span,edits)
        spans.append(span)
    return spans,hmr_edits


def load_lifetimes(path):
    table=defaultdict(list)
    with path.open() as stream:
        for entry in csv.DictReader(stream,delimiter="\t"):
            table[int(entry["q"])].append((int(entry["first"]),int(entry["last"])))
    return {q:sorted(values) for q,values in table.items()}


def clean(q, at, life):
    intervals=life[q]
    i=bisect_left(intervals,(at,0))
    return i==0 or intervals[i-1][1]<=at


def prove_dead_old_bits(circuit, removed):
    """Every removed write dies before any surviving read of its old physical ID."""
    ops=np.frombuffer(circuit.opcodes,dtype=np.uint8)
    top, dominates=condition_scopes(ops)
    changes=defaultdict(list)
    for start,end in removed:
        for op in circuit.operations(start,end):
            if op.bit is not None:
                changes[op.bit].append((start,end))
    assert not set(changes).intersection(classical_abi(circuit,kp))
    accesses=bit_accesses(circuit,ops,set(changes))
    proofs=[]
    for bit,segments in changes.items():
        segment_list=sorted(set(segments))
        for k,(start,end) in enumerate(segment_list):
            writes=set()
            candidates=accesses[bit]
            inspected=0
            until=segment_list[k+1][0] if k+1<len(segment_list) else len(ops)
            for position, flag in candidates[bisect_left(candidates,(end,0)):]:
                if position>=until:
                    break
                if any(a<=position<b for a,b in removed):
                    continue
                inspected+=1
                scope=top(position)
                if flag==0x40 and ops[position] in (0x40,0x41,0x50):
                    if scope==-1:
                        break
                    writes.add(scope)
                    continue
                if not any(dominates(writer,scope) for writer in writes):
                    raise AssertionError(f"Removed b{bit} is live at op {position}, source range {start}:{end}")
            proofs.append((bit,start,inspected))
    return len(changes),len(proofs)


def qualify_hmr(circuit, scan):
    """Prove each measured-target removal separately on the new chart tape."""
    top,_=condition_scopes(np.frombuffer(circuit.opcodes,dtype=np.uint8))
    candidates=scan["candidates"]
    assert len(candidates)==2
    for candidate in candidates:
        first,last=candidate["start"],candidate["hmr"]
        interval=list(circuit.operations(first,last+1))
        ccx,hmr=interval[0],interval[-1]
        assert ccx.opcode==0x31 and hmr.opcode==0x50
        assert top(first)==top(last)==-1
        assert ccx.qubits[2]==hmr.qubits[0]==candidate["target"]
        assert all(candidate["target"] not in op.qubits for op in interval[1:-1])
    return candidates


def rebind(new, nfirst, nlast, physical, fresh, initialize, hmr_edits):
    operations=[]
    bits=new.profile["header"]["num_bits"]
    if initialize:
        for b in range(bits):
            operations.append(binary.Operation(0x40,(),fresh+b,None,b""))
    first={c["start"]:fresh+bits+j for j,c in enumerate(hmr_edits)}
    last={c["hmr"]:fresh+bits+j for j,c in enumerate(hmr_edits)}
    for op in new.operations(nfirst,nlast):
        qubits=tuple(physical[q] for q in op.qubits)
        bit=None if op.bit is None else op.bit+fresh
        condition=None if op.condition is None else op.condition+fresh
        if op.source_index in first:
            measurement=first[op.source_index]
            operations.append(binary.Operation(0x50,(qubits[2],),measurement,None,b""))
            operations.append(binary.Operation(0xa0,qubits[:2],None,measurement,b""))
        elif op.source_index in last:
            measurement=last[op.source_index]
            operations.append(binary.Operation(0x40,(),bit,None,b""))
            operations.append(binary.Operation(0xc2,(),bit,measurement,b""))
        else:
            operations.append(binary.Operation(op.opcode,qubits,bit,condition,op.angle))
    return operations

def write(base, changes, fresh_count, path):
    columns={k:[] for k in range(1,11)}
    for start,end,ops in changes:
        buffers=encode(ops)
        for i in columns:
            lo,hi=base.column_range(i,start,end)
            columns[i].append((lo,hi,buffers[i]))
    sizes={k:p["payload_bytes"] for k,p in base.packets.items()}
    for k, intervals in columns.items():
        sizes[k]+=sum(len(data)-(hi-lo) for lo,hi,data in intervals)
    header=dict(base.profile["header"])
    header["num_bits"]+=fresh_count
    for field, col, length in HEADER_COUNTS:
        header[field]=sizes[col]//length
    with path.open("xb") as out:
        out.write(kp.HEADER.pack(kp.MAGIC,*(header[k] for k in kp.HEADER_FIELDS)))
        binary.copy_range(base.data,out,kp.HEADER.size,base.packets[1]["header_offset"])
        for col,size in sizes.items():
            out.write(kp.PACKET.pack(col,size))
            offset=base.packets[col]["payload_offset"]
            cursor=0
            for first,last,data in columns.get(col,()):
                assert cursor<=first<=last
                binary.copy_range(base.data,out,offset+cursor,offset+first)
                out.write(data)
                cursor=last
            binary.copy_range(base.data,out,offset+cursor,offset+base.packets[col]["payload_bytes"])
    with path.open("rb") as stream:
        sha=hashlib.file_digest(stream,"sha256").hexdigest()
    return header,sha


def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument("workspace",type=Path)
    p.add_argument("six_a",type=Path)
    p.add_argument("e4_directory",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--hmr-scan",type=Path)
    p.add_argument("--latest-dir",type=Path,
                   help="input KMB and its disjoint loan-splice and lifetime receipts")
    args=p.parse_args()
    root=args.workspace.resolve()
    latest_dir=args.latest_dir or root/"score22_dqi_crt_phase"/"loan8_production"
    assert args.out.is_dir()
    newest=splice.open_circuit(latest_dir/"dqi.kmb")
    six=splice.open_circuit(args.six_a)
    newest_sha=newest.profile["raw_kmb_sha256"]
    assert newest_sha in {BASE,FULL_WORD}
    assert six.profile["raw_kmb_sha256"]==SIX_A
    chart=root/"score19_dqi_frobenius"/"native"
    meta=json.loads((chart/"component.json").read_text())["rows"]
    old_meta=meta["original"]["third_pivot_chart"]
    new_meta=meta["borrow_norm"]["third_pivot_chart"]
    old=splice.open_circuit(chart/"original_chart.kmb")
    new=splice.open_circuit(chart/"borrow_norm_chart.kmb")
    assert old.profile["raw_kmb_sha256"]==old_meta["sha256"]
    assert new.profile["raw_kmb_sha256"]==new_meta["sha256"]
    ranges,hmr=tape_spans(root,args.e4_directory,latest_dir,newest_sha)
    hmr_edits=qualify_hmr(new,json.loads(args.hmr_scan.read_text())) if args.hmr_scan else []
    preexisting=load_lifetimes(latest_dir/"loans_lifetime.tsv")
    fresh=newest.profile["header"]["num_bits"]
    changes=[];sites=[];shift=0
    for j,((oa,ob),(na,nb)) in enumerate(zip(
            ((0,old_meta["prefix_ops"]),(old_meta["prefix_ops"],old_meta["operations"])),
            ((0,new_meta["prefix_ops"]),(new_meta["prefix_ops"],new_meta["operations"])))):
        s,t=PREVIOUS_SPANS[j]
        original=list(old.operations(oa,ob))
        matched=list(six.operations(s,t))
        mapping=match(original,matched)
        assert mapping is not None and len(matched)==len(original)==t-s
        expect=[]
        for op in matched:
            if op.source_index in hmr:
                edit=hmr[op.source_index]
                assert hmr_trace(op)==hmr_saved(edit["old"])
                expect.extend(hmr_saved(row) for row in edit["new"])
            else:
                expect.append(hmr_trace(op))
        start,end=ranges[j]
        assert expect==[hmr_trace(x) for x in newest.operations(start,end)]
        qmap={q:mapping["qubits"][q] for q in mapping["qubits"] if q<=864}
        assert all(qmap[q]==q for q in qmap if q<864)
        # The 24 carry bits are existing caller-owned storage in exactly
        # the old chart's mapped positions. On the return, conservative
        # lifetimes retain them across reversible cleanup. The original
        # extractor guarantees its clean-carry seam before this chart.
        assert clean(qmap[864],start,preexisting)
        selected=[q for q in range(864,889) if q not in qmap.values()
                   and clean(q,start,preexisting)]
        assert len(selected)>=12
        qmap.update(zip(range(865,877),selected[:12]))
        replacement=rebind(new,na,nb,qmap,fresh,initialize=j==0,hmr_edits=hmr_edits)
        changes.append((start,end,replacement))
        sites.append(dict(old_start=start,old_end=end,new_start=start+shift,
                          new_end=start+shift+len(replacement),new_helpers=selected[:12],
                          original_flag_qubit=qmap[864],
                          carry_bank_entry="unchanged original third-chart contract",
                          carry_physically_mapped=list(range(840,864))))
        shift+=len(replacement)-(end-start)
    dead_bits, scopes=prove_dead_old_bits(newest,ranges)
    output=args.out/"dqi_chart.kmb"
    fresh_count=new_meta["bits"]+len(hmr_edits)
    header,digest=write(newest,changes,fresh_count,output)
    added=header["num_ops_with_3_target_qubits"]-newest.profile["header"]["num_ops_with_3_target_qubits"]
    assert added==182-len(hmr_edits)
    print(json.dumps(dict(source_sha256=newest_sha,output_sha256=digest,static_T_delta=added,
                          old_bits_dead=dead_bits,checked_lifetimes=scopes,
                          new_fresh_bits=fresh_count,restored_hmr_fusions=hmr_edits,sites=sites,header=header),
                     indent=2))
    for circuit in (newest,six,old,new):
        circuit.close()


if __name__=="__main__":
    main()

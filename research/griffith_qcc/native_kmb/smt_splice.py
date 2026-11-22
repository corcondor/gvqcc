"""Z3-certified all-input nonlinear in-place splice for KMB v2 ANGLE.

Restrict cut and replacement to phase-free, unconditional X/CX/CCX. Prove their
complete Boolean permutations are identical on ALL initial physical-wire
states, rather than just on the 1219 legal addresses. Since those gates have
no relative phase, SMT UNSAT proves unitary equality on all superpositions.
The untouched prefix and suffix, including every HMR/conditional phase gate,
then implement exactly the same quantum instrument, even for post-HMR cuts.

UNKNOWN/timeout, SAT counterexample, source SHA mismatch, and no strictly
lower paid CCX cost all fail closed. A candidate must be supplied; this is
a certifier, not a search for the candidate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from .real_kmb import KMB, Op

PURE = {0x11:1, 0x21:2, 0x31:3}
GATES = {"X":0x11, "CX":0x21, "CCX":0x31}


class UnprovedRewrite(ValueError):
    """Refuse a physical KMB transformation without a full exact certificate."""


def validate(gates:Sequence[Op], nq:int):
    for i,op in enumerate(gates):
        if op.code not in PURE or op.bits or op.cond or op.angle:
            raise UnprovedRewrite(f"Only unconditional X/CX/CCX permitted at {i}")
        if len(op.wires)!=PURE[op.code] or len(set(op.wires))!=len(op.wires):
            raise UnprovedRewrite(f"Bad gate arity or repeated wires at {i}")
        if any(q<0 or q>=nq for q in op.wires):
            raise UnprovedRewrite(f"Out-of-range physical wire at {i}")


def simulate_symbolic(gates, inputs):
    from z3 import Xor, And, Not
    state=list(inputs)
    for op in gates:
        if op.code==0x11:
            q,=op.wires
            state[q]=Not(state[q])
        elif op.code==0x21:
            a,t=op.wires
            state[t]=Xor(state[t],state[a])
        else:
            a,b,t=op.wires
            state[t]=Xor(state[t],And(state[a],state[b]))
    return state


def prove_all_inputs(old:Sequence[Op],new:Sequence[Op],nq:int,timeout_ms=60000):
    """Prove exact unitary action for arbitrary dirty controls/targets (SMT UNSAT)."""
    from z3 import Bool, Xor, Or, Solver, is_true, sat, unsat
    if nq<1 or timeout_ms<1:
        raise ValueError("Invalid proof dimensions")
    validate(old,nq)
    validate(new,nq)
    active=sorted({q for op in (*old,*new) for q in op.wires})
    if not active:
        return {"proved":True,"active_qubits":0,"physical_qubits":nq,
                "all_input_states":True,"smt_result":"TRIVIAL"}
    index={q:i for i,q in enumerate(active)}
    def narrow(gates):
        return [Op(o.code,tuple(index[q] for q in o.wires)) for o in gates]
    x=[Bool(f"input_q{q}") for q in active]
    left=simulate_symbolic(narrow(old),x)
    right=simulate_symbolic(narrow(new),x)
    solver=Solver()
    solver.set("timeout",timeout_ms)
    solver.add(Or(*(Xor(a,b) for a,b in zip(left,right))))
    result=solver.check()
    if result==unsat:
        return {"proved":True,"physical_qubits":nq,"active_qubits":len(active),
                "all_input_states":True,"smt_result":"UNSAT",
                "phase_safe_by_exact_X_CX_CCX_alphabet":True}
    if result==sat:
        model=solver.model()
        counterexample={
            str(q):int(is_true(model.eval(x[i],model_completion=True)))
            for i,q in enumerate(active)
        }
        raise UnprovedRewrite("SAT counterexample: "+json.dumps(counterexample))
    raise UnprovedRewrite("SMT UNKNOWN/timeout: "+solver.reason_unknown())


def splice_kmb(kmb:KMB,start:int,stop:int,candidate:Sequence[Op],
               *,timeout_ms=60000):
    if not 0<=start<stop<=len(kmb.ops):
        raise UnprovedRewrite("Invalid KMB instruction interval")
    old=kmb.ops[start:stop]
    validate(old,kmb.nq)
    validate(candidate,kmb.nq)
    old_t=sum(o.code==0x31 for o in old)
    new_t=sum(o.code==0x31 for o in candidate)
    if new_t>=old_t:
        raise UnprovedRewrite("Not a strict paid-Toffoli saving")
    formal=prove_all_inputs(old,candidate,kmb.nq,timeout_ms)
    replacement=KMB(kmb.origin,kmb.version,kmb.nq,kmb.nb,kmb.nregs,
                    kmb.registers,
                    list(kmb.ops[:start])+list(candidate)+list(kmb.ops[stop:]),
                    kmb.tag)
    proof={
        "status":"ALL_INPUT_EXACT_UNITARY_PROOF_UNSAT",
        "start":start,"stop":stop,
        "old_paid_CCX":old_t,"new_paid_CCX":new_t,"paid_CCX_saved":old_t-new_t,
        "source_physical_qubits":kmb.nq,
        "post_HMR_cut":any(o.code==0x50 for o in kmb.ops[:start]),
        "all_prefix_suffix_instructions_identical":True,
        "native_KickMix_official_verified":False,
        "official_score_gain":None,
        "formal_proof":formal,
    }
    return replacement,proof


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-kmb",required=True,type=Path)
    parser.add_argument("--proposal",required=True,type=Path)
    parser.add_argument("--output-kmb",required=True,type=Path)
    parser.add_argument("--receipt",required=True,type=Path)
    parser.add_argument("--timeout-ms",type=int,default=60000)
    a=parser.parse_args(argv)
    if a.output_kmb.exists() or a.receipt.exists():
        raise FileExistsError("Never overwrite existing circuit/receipt")
    source=a.original_kmb.read_bytes()
    kmb=KMB.read(a.original_kmb)
    if kmb.render()!=source:
        raise UnprovedRewrite("Original binary failed roundtrip")
    proposal=json.loads(a.proposal.read_text())
    source_hash=hashlib.sha256(source).hexdigest()
    if proposal.get("expected_source_sha256")!=source_hash:
        raise UnprovedRewrite("Original baseline SHA256 is not pinned/matching")
    candidate=[]
    for step in proposal["replace"]:
        if step["opcode"] not in GATES:
            raise UnprovedRewrite("Unsupported opcode in proposal")
        candidate.append(Op(GATES[step["opcode"]],tuple(map(int,step["wires"]))))
    changed,proof=splice_kmb(kmb,int(proposal["start"]),int(proposal["stop"]),
                             candidate,timeout_ms=a.timeout_ms)
    proof["source_sha256"]=source_hash
    proof["output_sha256"]=hashlib.sha256(changed.render()).hexdigest()
    a.output_kmb.write_bytes(changed.render())
    a.receipt.write_text(json.dumps(proof,indent=2)+"\n")
    print(json.dumps(proof,indent=2))
    return proof


if __name__=="__main__":
    main()

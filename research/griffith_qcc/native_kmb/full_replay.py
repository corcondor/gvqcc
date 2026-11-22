"""Full real 15-bank bit-parallel forward/reverse loader replay.

This separately compares the actual public ANGLE oracle value contract on
all 1219 legal addresses in both forward and reverse calls, testing all 128
physical wires. This checker ignores diagonal Z/CZ gates *only when updating
classical bits*. Phase/instrument equivalence of a modified full KMB comes
from independent GF(2) symbolic proof (linear_opt.certify_source_candidate),
not from this classical check alone.

Run:
  python -m native_kmb.full_replay --old /path/original/dfthcsos \
      --new /path/rewritten/dfthcsos --npz /path/submission.npz \
      --report replay.json
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .real_kmb import KMB
from .native_splice import initial_legal_states
from .linear_opt import certify_source_candidate


def replay_bits(ops,start,ncases):
    wires=list(start)
    ones=(1<<ncases)-1
    measurements=0
    for op in ops:
        code=op.code;qs=op.wires
        if code==0x31:
            a,b,t=qs;wires[t]^=wires[a]&wires[b]
        elif code==0x21:
            a,b=qs;wires[b]^=wires[a]
        elif code==0x11:
            wires[qs[0]]^=ones
        elif code==0x50:
            wires[qs[0]]=0;measurements+=1
        elif code in (0x10,0x20,0x90,0xa0):
            # Z/CZ diagonal; no classical computational-basis bit action.
            pass
        else:
            raise ValueError(f"Unsupported native ANGLE instruction {code:#x}")
    return wires,measurements


def expected_output(words,bank,source_state):
    n=len(words)
    expected=list(source_state)
    for j in range(5):
        for bit in range(7):
            change=0
            for a in range(n):
                target=int(words[a][5*bank+j])
                previous=int(words[a][5*(bank-1)+j]) if bank else 0
                if ((target^previous)>>bit)&1:change|=1<<a
            expected[11+7*j+bit]^=change|(change<<n)
    return expected


def replay_all(original_dir,rewrite_dir,npz_path):
    import numpy as np
    with np.load(npz_path,allow_pickle=False) as z:
        words=z['angle_words']
    if words.shape!=(1219,75):
        raise ValueError("Expect original V8 1219 x 75 angle words")
    report={"status":"FULL_15_NATIVE_COMPUTATIONAL_REPLAY_PASS",
            "scope":"both full forward/reverse legal inputs, all 128 physical wires",
            "phase_checked_by_classical_replay":False,
            "total_basis_states":0,"banks":[]}
    for bank in range(15):
        name=f"angle_k_{bank}.kmb"
        source=KMB.read(Path(original_dir)/name)
        candidate=KMB.read(Path(rewrite_dir)/name)
        proof=certify_source_candidate(source,candidate)
        if source.nq>128:raise ValueError("ANGLE cap exceeded")
        states,ncases=initial_legal_states(words,bank,source.nq)
        expected=expected_output(words,bank,states)
        orig,mo=replay_bits(source.ops,states,ncases)
        modified,mn=replay_bits(candidate.ops,states,ncases)
        errors_old=sum((x^y).bit_count() for x,y in zip(orig,expected))
        errors_new=sum((x^y).bit_count() for x,y in zip(modified,expected))
        errors_pair=sum((x^y).bit_count() for x,y in zip(orig,modified))
        if errors_old or errors_new or errors_pair or mo!=mn:
            raise AssertionError((bank,errors_old,errors_new,errors_pair,mo,mn))
        report["banks"].append({
            "bank":bank,"legal_forward_reverse_states":ncases,
            "qubits":source.nq,"num_hmr":mn,
            "original_and_rewritten_match_target_all_wires":True,
            "formal_exact_cnot_run_proof":proof,
        })
        report["total_basis_states"]+=ncases
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old",required=True,type=Path)
    p.add_argument("--new",required=True,type=Path)
    p.add_argument("--npz",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    args=p.parse_args()
    report=replay_all(args.old,args.new,args.npz)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print("PASS",report["total_basis_states"],"exact computational-basis states")


if __name__=="__main__":
    main()

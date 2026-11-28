"""Fail-closed *in-place* nonlinear XAG/KMB replacement before the first HMR.

This closes a former integration gap: candidate X/CX/CCX operations are inserted
into a real physical-wire KMB segment, with a per-bit proof on the *complete*
legal forward/reverse address support. The original KMB and NPZ stay untouched.

Restricted scope:
  * start/stop must be strictly before the first measurement
  * no changed measurement, phase, reset or conditional instruction
  * old and new segment both use phase-free X/CX/CCX permutations
  * each output of every physical wire must match on the given exact support
  * a strictly lower CCX count is required for promotion by default

Because the unmodified prefix has no measurement and the changed gates are
phase-free permutations, equality at the cut on every reachable basis state
extends by linearity to superpositions/entanglement supported on that space.
All subsequent HMR branches/phase operations are left byte-identical. This
does NOT prove an arbitrary-target contract on states outside the supplied
reachable support. Post-HMR splicing requires a separate phase-transcript
proof and is rejected here.
"""
from __future__ import annotations
from .real_kmb import KMB,Op

PURE={0x11,0x21,0x31}
DIAGONAL={0x10,0x20,0x90,0xa0}


def initial_legal_states(words,bank,nq):
    """Packed 1219-address forward/reverse known-legal boundary states.

    words: sequence of rows, 75 7-bit words per row. This is the actual
    published 11 selection bits, 5x7 target bits, and zero scratch layout.
    """
    n=len(words)
    if nq<46 or not 1<=n<=2048 or not 0<=bank<15:
        raise ValueError("invalid real 128Q loader domain")
    s=[0]*nq
    for a in range(n):
        if len(words[a])!=75:raise ValueError("expected 75 angle words")
        both=(1<<a)|(1<<(n+a))
        for j in range(11):
            if a>>j&1:s[j]|=both
        for word in range(5):
            if bank:
                previous=int(words[a][5*(bank-1)+word])
                if not 0<=previous<128:raise ValueError("not a 7-bit word")
                for bit in range(7):
                    if previous>>bit&1:s[11+word*7+bit]|=1<<a
            value=int(words[a][5*bank+word])
            if not 0<=value<128:raise ValueError("not a 7-bit word")
            for bit in range(7):
                if value>>bit&1:s[11+word*7+bit]|=1<<(n+a)
    return s,2*n


def _basis_replay(ops,wires,case_count):
    s=list(wires)
    ones=(1<<case_count)-1
    for op in ops:
        code=op.code;w=op.wires
        if code==0x21:
            a,b=w;s[b]^=s[a]
        elif code==0x31:
            a,b,t=w;s[t]^=s[a]&s[b]
        elif code==0x11:
            s[w[0]]^=ones
        elif code in DIAGONAL:
            # Diagonal phases are harmless only in an *unchanged prefix*.
            pass
        else:
            raise ValueError(f"unsupported or post-HMR opcode in slice: {code:#x}")
    return s


def splice_pre_hmr(
    source:KMB,start:int,stop:int,replacement:list[Op],
    legal_input_bitsets:list[int],num_basis_states:int,*,require_paid_gain:bool=True
):
    """Return a new uncommitted KMB only when the *real* splice is valid."""
    if not (0<=start<stop<=len(source.ops)):
        raise ValueError("bad instruction boundaries")
    if len(legal_input_bitsets)!=source.nq or num_basis_states<1:
        raise ValueError("full physical-wire legal-state basis required")
    if any(v<0 or v.bit_length()>num_basis_states for v in legal_input_bitsets):
        raise ValueError("malformed packed legal-state bits")
    if any(o.code==0x50 for o in source.ops[:stop]):
        raise ValueError("Nonlinear splice after first HMR not supported")
    if any(o.code not in PURE|DIAGONAL for o in source.ops[:start]):
        raise ValueError("Unsupported prefix operation")
    old=source.ops[start:stop]
    if any(o.code not in PURE for o in old):
        raise ValueError("only phase-free X/CX/CCX may be replaced")
    if any(o.code not in PURE for o in replacement):
        raise ValueError("candidate must be X/CX/CCX only")
    for op in replacement:
        if any(w<0 or w>=source.nq for w in op.wires):
            raise ValueError("replacement uses out-of-range physical wire")
        if len(op.wires)!={0x11:1,0x21:2,0x31:3}[op.code]:
            raise ValueError("replacement gate arity invalid")
    before=sum(o.code==0x31 for o in old)
    after=sum(o.code==0x31 for o in replacement)
    if require_paid_gain and after>=before:
        raise ValueError("Not a strict native-Toffoli improvement")
    incoming=_basis_replay(source.ops[:start],legal_input_bitsets,num_basis_states)
    old_out=_basis_replay(old,incoming,num_basis_states)
    new_out=_basis_replay(replacement,incoming,num_basis_states)
    if old_out!=new_out:
        differences=sum((a^b).bit_count() for a,b in zip(old_out,new_out))
        raise AssertionError(f"Candidate fails physical cut, mismatches={differences}")
    revised=KMB(
        source.origin,source.version,source.nq,source.nb,source.nregs,
        source.registers,source.ops[:start]+list(replacement)+source.ops[stop:],
        source.tag
    )
    return revised,{
        "status":"EXACT_REACHABLE_PRE_HMR_CUT",
        "original_paid_CCX_in_cut":before,"candidate_paid_CCX_in_cut":after,
        "strict_paid_saving":before-after,
        "physical_qubits":source.nq,"all_physical_output_wires_checked":source.nq,
        "full_basis_states_checked":num_basis_states,
        "no_HMR_or_phase_changes_inside_cut":True,
        "all_following_ops_preserved":True,
        "limitation":"Not an all-input 128-wire equivalence claim outside legal support",
        "native_KickMix_official_verified":False,
    }

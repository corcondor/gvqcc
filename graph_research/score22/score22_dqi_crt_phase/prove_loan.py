#!/usr/bin/env python3
"""Prove g implies an exact zero lender on every bound production route."""
from argparse import ArgumentParser
from bisect import bisect_left
from collections import defaultdict
from csv import DictReader
import ctypes
import json
from pathlib import Path
import sys


class BooleanTape:
    def __init__(self, canonical=False):
        self.canonical = canonical
        self.expressions = {}
        self.lookup = {}
        self.variables = 2

    def literal(self):
        var = self.variables
        self.variables += 1
        self.expressions[var] = None
        return var

    def make(self, kind, args):
        key = kind, tuple(args)
        if key not in self.lookup:
            var = self.literal()
            self.lookup[key] = var
            self.expressions[var] = key
        return self.lookup[key]

    def invert(self, a):
        return 1-a if a <= 1 and a >= 0 else -a

    def pair(self, kind, a, b):
        if kind == 'xor':
            if a == 0 or b == 0:
                return b if a == 0 else a
            if a == 1 or b == 1:
                return self.invert(b if a == 1 else a)
            if a == b:
                return 0
            if a == -b:
                return 1
            if self.canonical:
                flipped = (a<0) ^ (b<0)
                terms = []
                for x in (abs(a),abs(b)):
                    prior = self.expressions.get(x)
                    if prior and prior[0]=='xor':
                        terms.append(set(prior[1]))
                    else:
                        terms.append({x})
                parity = sorted(terms[0] ^ terms[1])
                if not parity:
                    return int(flipped)
                result = parity[0] if len(parity)==1 else self.make('xor',parity)
                return self.invert(result) if flipped else result
            for x,y in ((a,b),(b,a)):
                composed = self.expressions.get(x)
                if composed and composed[0]=='xor' and y in composed[1]:
                    left,right = composed[1]
                    return left if y==right else right
        elif kind == 'and':
            if a == 0 or b == 0 or a == -b:
                return 0
            if a == 1 or b == 1:
                return b if a == 1 else a
            if a == b:
                return a
        return self.make(kind, sorted((a,b)))

    def choose(self, active, yes, no):
        if active == 0 or yes == no:
            return no
        if active == 1:
            return yes
        return self.make('ite',(active,yes,no))


def write_qubit(op):
    base = op.opcode & 0x7f
    if base in (0x11,0x12,0x50,0x21,0x31):
        return op.qubits[-1:]
    if base in (0x22,0x32):
        return op.qubits[-2:]
    return ()


def scan(operations, zero_word, flag, witness, canonical=False):
    algebra = BooleanTape(canonical)
    quantum = defaultdict(algebra.literal)
    classical = defaultdict(algebra.literal)
    quantum.update({q:0 for q in zero_word})
    assert flag not in quantum
    quantum[flag] = 1
    top = [1]
    for op in operations:
        code = op.opcode
        base = code & 0x7f
        if code == 0x81:
            top.append(algebra.pair('and',top[-1],classical[op.condition]))
            continue
        if code == 0x01:
            top.pop()
            continue
        if base in (0x00,0x10,0x13,0x20,0x30):
            continue
        active = top[-1]
        if op.condition is not None:
            active = algebra.pair('and',active,classical[op.condition])
        if base in (0x40,0x41,0x42,0x50):
            bit = op.bit
            value = (algebra.invert(classical[bit]) if base==0x42 else
                     algebra.literal() if base==0x50 else base-0x40)
            classical[bit] = algebra.choose(active,value,classical[bit])
        dest = write_qubit(op)
        if not dest:
            assert base in (0x40,0x41,0x42), op
            continue
        assert flag not in dest, op
        if base in (0x12,0x50):
            q = dest[0]
            quantum[q] = algebra.choose(active,0,quantum[q])
        elif base in (0x11,0x21,0x31):
            parity = 1 if base==0x11 else quantum[op.qubits[0]]
            if base == 0x31:
                parity = algebra.pair('and',parity,quantum[op.qubits[1]])
            src = algebra.pair('and',active,parity)
            q = dest[0]
            quantum[q] = algebra.pair('xor',quantum[q],src)
        else:
            a,b = dest
            if base == 0x32:
                active = algebra.pair('and',active,quantum[op.qubits[0]])
            quantum[a],quantum[b] = (algebra.choose(active,quantum[b],quantum[a]),
                                    algebra.choose(active,quantum[a],quantum[b]))
    assert top==[1]
    if isinstance(witness,int):
        return algebra, quantum[witness]
    clean = 1
    for lane in witness:
        clean=algebra.pair('and',clean,algebra.invert(quantum[lane]))
    return algebra,algebra.invert(clean)


def smt(algebra, target, max_time=2000):
    if target in (0,1):
        return ('unsat' if target==0 else 'sat'),0

    def variable(i):
        if i == 1:return 'true'
        if i == 0:return 'false'
        return f'(not n{-i})' if i < 0 else f'n{i}'

    reachable = set()
    pending = [abs(target)]
    while pending:
        index = pending.pop()
        if index > 1 and index not in reachable:
            reachable.add(index)
            row = algebra.expressions[index]
            if row:
                pending += [abs(i) for i in row[1]]
    query = [f"(set-option :timeout {max_time})", "(set-logic QF_UF)"]
    for index in sorted(reachable):
        row = algebra.expressions[index]
        if row is None:
            query.append(f"(declare-fun n{index} () Bool)")
        else:
            kind,args = row
            query.append(f"(define-fun n{index} () Bool ({kind} {' '.join(map(variable,args))}))")
    query.append(f"(assert {variable(target)})")
    query.append("(check-sat)")
    api = ctypes.CDLL('libz3.so.4')
    api.Z3_mk_config.restype = ctypes.c_void_p
    api.Z3_mk_context.argtypes = [ctypes.c_void_p]
    api.Z3_mk_context.restype = ctypes.c_void_p
    for func in (api.Z3_del_context, api.Z3_del_config):
        func.argtypes = [ctypes.c_void_p]
    api.Z3_eval_smtlib2_string.argtypes = [ctypes.c_void_p,ctypes.c_char_p]
    api.Z3_eval_smtlib2_string.restype = ctypes.c_char_p
    config = api.Z3_mk_config()
    context = api.Z3_mk_context(config)
    api.Z3_del_config(config)
    try:
        value = api.Z3_eval_smtlib2_string(context,'\n'.join(query).encode())
        return value.decode().strip(),len(reachable)
    finally:
        api.Z3_del_context(context)


def all_lives(tsv):
    rows = defaultdict(list)
    with tsv.open() as stream:
        for row in DictReader(stream,delimiter='\t'):
            rows[int(row['q'])].append((int(row['first']),int(row['last'])))
    return rows


def clean_start(rows,q,p):
    lives = rows[q]
    i = bisect_left(lives,(p,0))
    return i==0 or lives[i-1][1]<=p


def build_predicate(km, toggle, dest):
    builder = km.CircuitBuilder()
    word = builder.create_quantum_register(12,'word')
    flag = builder.create_quantum_register(1,'flag')[0]
    toggle(builder,word,flag)
    builder.finish_circuit().to_file(dest,format='kmb')


def timeline(circuit):
    import numpy as np
    ops = np.frombuffer(circuit.opcodes,dtype=np.uint8)
    positions = np.flatnonzero(np.isin(ops,[0x81,0x01]))
    changes = np.where(ops[positions]==0x81,1,-1)
    depths = np.cumsum(changes,dtype=np.int8)
    def depth(p):
        i=positions.searchsorted(p)-1
        return int(depths[i]) if i>=0 else 0
    return depth


def main(args):
    sys.path[:0] = [str(args.central),str(args.repo),
                    str(args.source/"after_c5/extractor_width")]
    import ew_paths # noqa: F401
    import kickmix as km
    from coherent_border import toggle_zero
    import census
    import dqi_ccx_peephole as binary
    import kmb_profile as kp
    from outcome_dqi_chart_match import match

    receipt=json.loads(args.binds.read_text())
    assert census.digest(args.circuit)==receipt["tape_sha256"]
    c=census.open_columns(args.circuit,binary.BinaryCircuit,kp)
    predicate=args.out.with_name("toggle_zero12.kmb")
    build_predicate(km,toggle_zero,predicate)
    ref=census.open_columns(predicate,binary.BinaryCircuit,kp)
    template_ops=tuple(ref.operations(0,len(ref.opcodes)))
    pattern=ref.opcodes
    ref.close()
    lives=all_lives(args.life)
    depth=timeline(c)
    results=[]
    cached = {}
    if args.retry is not None:
        cached = {row["start"]:row for row in json.loads(args.retry.read_text())["sites"]}
    for family in receipt["families"]:
        for row in family["matches"]:
            start,flag = row["start"],row["flag"]
            witness = row["coefficient_lead"][0] if args.lanes==1 else row["coefficient_lead"][:args.lanes]
            if start in cached and cached[start].get("value_counterexample") != "unknown":
                results.append(cached[start])
                continue
            site=dict(points=family["points"],start=start,flag=flag,witness=witness,
                      scratch_clean=all(clean_start(lives,q,start) for q in row["scratch"]))
            begin=max(0,start-150_000)
            end=start
            while (left:=c.opcodes.rfind(pattern,begin,end))>=0:
                end=left+len(pattern)-1
                right=left+len(pattern)
                qm=match(template_ops,c.operations(left,right))
                if qm is None or qm["qubits"][12]!=flag:
                    continue
                tested = [qm["qubits"][q] for q in range(12)]
                if not clean_start(lives,flag,left) or depth(left)!=0 or depth(start)!=0:
                    continue
                inter=tuple(c.operations(right,start))
                if any(flag in write_qubit(op) for op in inter):
                    continue
                algebra,output=scan(inter,tested,flag,witness,args.canonical_xor)
                proof,cone=smt(algebra,output,args.timeout_ms)
                site.update(query=[left,right],value_counterexample=proof,reachable_SAT_nodes=cone,
                            tested=tested)
                break
            results.append(site)
            print(json.dumps(site),flush=True)
    c.close()
    counts=defaultdict(int)
    for row in results:
        counts[(row.get("value_counterexample","missing"),row["scratch_clean"])]+=1
    args.out.write_text(json.dumps({"input_sha256":receipt["tape_sha256"],"lanes":args.lanes,"sites":results,
                                   "totals":[[proof,clean,n] for (proof,clean),n in counts.items()]},indent=2)+"\n")


if __name__=='__main__':
    p=ArgumentParser(description=__doc__)
    for key in ("central","repo","source","circuit","life","binds","out"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--lanes",choices=[1,8],default=1,type=int)
    p.add_argument("--canonical-xor",action="store_true")
    p.add_argument("--timeout-ms",default=2000,type=int)
    p.add_argument("--retry",type=Path)
    main(p.parse_args())

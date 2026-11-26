#!/usr/bin/env python3
"""V86: conservative reachable-state bilinear reduction of actual DQI KMB v2.

Input ABI: arbitrary S registers, arbitrary classical inputs, all other qubits
zero. Track affine forms in independent *abstract* Boolean symbols. Each new
nonlinear product is a fresh symbol, with exact canonical reuse identities.
Unknown guards and branch joins overapproximate, never assume a sampled state.
Only replace CCX by an equivalent XOR of <=32 live controls and a constant.
All other instructions (including phase, HMR, conditions) are copied verbatim.
"""
import argparse
import hashlib
import json
import struct
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import kmb_profile as kp
from dqi_ccx_peephole import BinaryCircuit, Operation, write_rewritten

class Domain:
    def __init__(self, q, inputs, limit=4096):
        self.rows = [0] * q
        self.n = 1
        self.limit = limit
        self.epoch = 0
        self.cache = {}
        self.factor_bases = {}
        self.stack = []
        self.stats = Counter()
        for i in inputs:
            self.rows[i] = self.fresh()

    def fresh(self):
        x = 1 << self.n
        self.n += 1
        return x

    def compact(self):
        # Exact change of abstract coordinates on the live affine row space.
        # Drop old nonlinear cache; snapshots from older epochs are not compared.
        pivots = {}
        rows = []
        n = 1
        for old in self.rows:
            r, out = old & ~1, old & 1
            while r:
                k = r.bit_length() - 1
                if k not in pivots:
                    c = 1 << n
                    n += 1
                    pivots[k] = (r, c)
                    out ^= c
                    break
                p, c = pivots[k]
                r ^= p
                out ^= c
            rows.append(out)
        self.rows = rows
        self.n = n
        self.cache.clear()
        self.factor_bases.clear()
        self.epoch += 1
        self.stats["compactions"] += 1

    def put(self, i, x, guarded=False):
        if x == self.rows[i]:
            return
        self.rows[i] = self.fresh() if guarded else x
        if self.stack:
            self.stack[-1][2] |= 1 << i

    def push(self):
        self.stack.append([self.epoch, self.rows[:], 0])

    def pop(self):
        epoch, before, changed = self.stack.pop()
        if self.stack:
            self.stack[-1][2] |= changed
        while changed:
            bit = changed & -changed
            i = bit.bit_length() - 1
            changed ^= bit
            if epoch != self.epoch or self.rows[i] != before[i]:
                self.rows[i] = self.fresh()

    def factor_basis(self, u):
        # Multiplication by a fixed homogeneous Boolean form is linear.
        # Include u*u=u; all basis values are exact product expressions.
        return self.factor_bases.setdefault(u, {u.bit_length()-1: (u, u)})

    def factor_lookup(self, u, v):
        basis = self.factor_basis(u)
        out = 0
        while v:
            entry = basis.get(v.bit_length()-1)
            if entry is None:
                return None
            r, p = entry
            v ^= r
            out ^= p
        return out

    def factor_insert(self, u, v, value):
        basis = self.factor_basis(u)
        while v:
            k = v.bit_length()-1
            if k not in basis:
                basis[k] = (v, value)
                return
            r, p = basis[k]
            v ^= r
            value ^= p
        # Two expressions may agree on the concrete state but not in the
        # overapproximation. Keep the existing basis; never assert equality.

    def product(self, a, b):
        # Boolean affine offsets and GL(2,F2) canonicalization of the
        # homogeneous factors: u*(u+v) = u*v+u, u*u = u.
        u, v = a & ~1, b & ~1
        out = (v if a & 1 else 0) ^ (u if b & 1 else 0) ^ (a & b & 1)
        if not u or not v:
            return out, "linear"
        if u == v:
            return out ^ u, "linear"
        p, q = sorted((u, v, u ^ v))[:2]
        if {u, v} != {p, q}:
            out ^= next(iter({u, v} & {p, q}))
        key = (p, q)
        if key in self.cache:
            return out ^ self.cache[key], "cached"
        value = self.factor_lookup(p, q)
        if value is None:
            value = self.factor_lookup(q, p)
        if value is None:
            value = self.factor_lookup(p ^ q, p)
            if value is not None:
                value ^= p
        kind = "dependent"
        if value is None:
            value = self.fresh()
            self.cache[key] = value
            kind = "new"
        self.factor_insert(p, q, value)
        self.factor_insert(q, p, value)
        self.factor_insert(p ^ q, p, value ^ p)
        return out ^ value, kind

    def representation(self, p, target, a, b, kind):
        # Return (constant, controls), never use target as a control.
        if p <= 1:
            return p, ()
        if kind == "new":
            return None
        for i in (a, b):
            if self.rows[i] == p:
                return 0, (i,)
            if self.rows[i] == p ^ 1:
                return 1, (i,)
        lookup = {}
        for i, r in enumerate(self.rows):
            if i == target or r <= 1:
                continue
            if r == p:
                return 0, (i,)
            lookup.setdefault(r, i)
        if p ^ 1 in lookup:
            return 1, (lookup[p ^ 1],)
        for r, i in lookup.items():
            for c in (0, 1):
                j = lookup.get(r ^ p ^ c)
                if j is not None and i != j:
                    return c, (i, j)
        # Exact live-row span, not only one- or two-wire matches.
        basis = {0: (1, 1)}
        for i, r in enumerate(self.rows):
            if i == target:
                continue
            code = 1 << (i+1)
            while r:
                k = r.bit_length()-1
                if k not in basis:
                    basis[k] = (r, code)
                    break
                rr, cc = basis[k]
                r ^= rr
                code ^= cc
        r, code = p, 0
        while r:
            entry = basis.get(r.bit_length()-1)
            if entry is None:
                return None
            rr, cc = entry
            r ^= rr
            code ^= cc
        if code.bit_count() > 32:
            return None
        return code & 1, tuple(i for i in range(len(self.rows)) if code >> (i+1) & 1)

    def step(self, t, a=-1, b=-1, c=-1):
        if self.n > self.limit:
            self.compact()
        guarded = bool(t & 128)
        op = t & 127
        r = self.rows
        if t == 0x81:
            self.push()
        elif t == 1:
            self.pop()
        elif op == 0x21:
            self.put(b, r[b] ^ r[a], guarded)
        elif op == 0x11:
            self.put(a, r[a] ^ 1, guarded)
        elif op in (0x12, 0x50):
            self.put(a, 0, guarded)
        elif op == 0x22:
            x, y = r[a], r[b]
            self.put(a, y, guarded)
            self.put(b, x, guarded)
        elif op == 0x32:
            x, y = r[b], r[c]
            if r[a] != 0 and x != y:
                unknown = guarded or r[a] != 1
                self.put(b, y, unknown)
                self.put(c, x, unknown)
        elif op == 0x31:
            self.stats["CCX_scanned"] += 1
            p, kind = self.product(r[a], r[b])
            self.stats["product_" + kind] += 1
            rep = self.representation(p, c, a, b, kind)
            if rep is not None:
                k, controls = rep
                check = k
                for i in controls:
                    assert i != c
                    check ^= r[i]
                assert check == p
                self.stats["CCX_removed_" + kind] += 1
                self.stats["CX_added"] += len(controls)
                self.stats["X_added"] += k
            self.put(c, r[c] ^ p, guarded)
            return rep, kind
        elif op in (0, 0x10, 0x13, 0x20, 0x30, 0x40, 0x41, 0x42,
                    0x06, 0x07, 0x17, 0x47):
            pass  # diagonal, classical, or non-mutating debug instructions
        else:
            raise ValueError(f"Unsupported opcode {t:#x}")
        return None

def input_wires(c):
    # Parse actual register declarations, not hard-coded physical wire IDs.
    pos = kp.HEADER.size
    end = c.packets[1]["header_offset"]
    names, wires = set(), set()
    while pos < end:
        kind, size = kp.PACKET.unpack_from(c.data, pos)
        pos += kp.PACKET.size
        assert kind == 0 and size >= 8
        length, width = struct.unpack_from("<II", c.data, pos)
        assert size == 8 + length + 4 * width and width == 12
        name = c.data[pos+8:pos+8+length].decode("ascii")
        assert name not in names
        names.add(name)
        targets = struct.unpack_from("<12I", c.data, pos+8+length)
        if name.startswith("S"):
            assert all(x >> 31 for x in targets)
            for x in targets:
                q = x & 0x7fffffff
                assert q not in wires and q < c.profile["header"]["num_qubits"]
                wires.add(q)
        else:
            assert name.startswith("E") and all(not (x >> 31) for x in targets)
        pos += size
    assert pos == end
    assert names == {f"S{i}" for i in range(70)} | {f"E{i}" for i in range(4095)}
    assert len(wires) == 840
    return sorted(wires)

def scan(c, limit):
    d = Domain(c.profile["header"]["num_qubits"], input_wires(c), limit)
    views = {}
    for k in range(2, 8):
        packet = c.packets[k]
        off = packet["payload_offset"]
        views[k] = memoryview(c.data)[off:off+packet["payload_bytes"]].cast("I")
    pos = [0]*4
    changes = []
    # Hot path: unguarded CX (including inside an active implicit branch).
    # This does not allocate per-instruction Operation objects.
    try:
        for i, t in enumerate(c.opcodes):
            n = (t >> 4) & 3
            j = pos[n]
            if n:
                pos[n] += 1
            if t == 0x21:
                a, b = views[5][j], views[6][j]
                d.put(b, d.rows[b] ^ d.rows[a])
            else:
                a = b = z = -1
                if n == 1:
                    a = views[7][j]
                elif n == 2:
                    a, b = views[5][j], views[6][j]
                elif n == 3:
                    a, b, z = views[2][j], views[3][j], views[4][j]
                ans = d.step(t, a, b, z)
                if ans is not None and ans[0] is not None:
                    rep, reason = ans
                    changes.append((i, rep, reason))
            if i and i % 10000000 == 0:
                print(json.dumps({"scanned":i,"rewrites":len(changes)}), flush=True)
        assert not d.stack
        assert pos[1] == len(views[7]) and pos[2] == len(views[5]) and pos[3] == len(views[2])
    finally:
        for v in views.values():
            v.release()
    return changes, dict(d.stats)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--expected-sha", required=True)
    ap.add_argument("--symbol-limit", type=int, default=4096)
    args = ap.parse_args()
    assert sys.byteorder == "little"
    assert args.symbol_limit >= 2048
    if args.output.exists() or args.source.resolve() == args.output.resolve():
        raise FileExistsError(args.output)
    start = time.monotonic()
    profile = kp.profile(args.source, max_register_summaries=0)
    assert profile["raw_kmb_sha256"] == args.expected_sha
    assert profile["header"]["num_info_tags"] == 0
    c = BinaryCircuit(args.source, profile)
    records = []
    try:
        changes, stats = scan(c, args.symbol_limit)
        old_count = profile["raw_gate_families"]["CCX"]["total"]
        assert stats["CCX_scanned"] == old_count
        blocks = []
        for i, (constant, controls), reason in changes:
            before = list(c.operations(i, i+1))
            old = before[0]
            assert old.is_ccx
            target = old.qubits[-1]
            flag = old.opcode & 128
            after = [Operation(0x21 | flag, (q, target), condition=old.condition)
                     for q in controls]
            if constant:
                after.append(Operation(0x11 | flag, (target,), condition=old.condition))
            blocks.append((i, i+1, before, after))
            records.append({"op":i,"reason":reason,"old":list(old.qubits),
                            "condition":old.condition,"constant":constant,"controls":list(controls)})
        if blocks:
            write_rewritten(c, args.output, blocks)
    finally:
        c.close()
    result = {"source_sha256":args.expected_sha, "source_CCX":old_count,
              "static_CCX_reduction":len(records), "stats":stats,
              "symbol_limit":args.symbol_limit, "rewrites":records,
              "scope":"All syndrome values, zero ancillas, arbitrary classical conditions and measurement outcomes; no sampled reachability assumptions.",
              "official_verification":"not_run", "status":"NO_REDUCTION"}
    if records:
        p = kp.profile(args.output, max_register_summaries=0)
        assert p["raw_gate_families"]["CCX"]["total"] == old_count - len(records)
        assert p["header"]["num_qubits"] == profile["header"]["num_qubits"]
        assert p["header"]["num_bits"] == profile["header"]["num_bits"]
        result.update(status="SERIALIZED_REQUIRES_OFFICIAL_VERIFICATION",
                      output_sha256=p["raw_kmb_sha256"], output_CCX=old_count-len(records),
                      output_ops=p["header"]["num_ops"], source_ops=profile["header"]["num_ops"])
    result["seconds"] = time.monotonic()-start
    args.output.with_suffix(".json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="rewrites"}), flush=True)

if __name__ == "__main__":
    main()

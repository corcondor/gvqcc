"""The instruction-stream IR for kickmix circuits.

A circuit is struct-of-arrays, as in the .kmb file itself: `types` (one opcode byte per instruction) and the operand
arrays each kind of instruction draws from in order (qqq0-2, qq0-1, q0, b0, bc, angles), plus registers and info
tags. Which arrays an instruction draws from is a function of its opcode bits alone (OP_HAS_*), so every operation
below is a numpy pass over `types`: no per-instruction Python. Round trip with the file is byte-exact.

    c = ir.Circuit.read(path)            c.write(path) -> sha256 of the bytes written
    c = ir.Circuit.from_ops(ops, regs)   a circuit from (name, qubits, bits) instructions (builders, plants)
    c.slice(a, b)                        instructions [a, b) as a Circuit with the same registers
    c.pieces(cuts)                       the slices between consecutive cuts, in one pass: (a, b, slice)
    c.tags()                             (instruction index, text) of every INFO_TAG
    c.decode(a, b)                       instructions [a, b) as (index, name, qubits, target bit, condition bit)
    c.static_counts()                    count per instruction name
    c.mean_toffolis()                    mean Toffoli-like (CCX, CCZ, CSWAP) executed per shot, exact or sampled
    c.liveness()                         first/last instruction of each qubit, live count along the stream
"""
from __future__ import annotations

import hashlib
import struct
import sys
from dataclasses import dataclass, field

import numpy as np

sys.dont_write_bytecode = True

MAGIC = bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
HAS_1Q, HAS_2Q, HAS_1B, HAS_COND = 0x10, 0x20, 0x40, 0x80
NAMES = {0x00: "NEG", 0x01: "POP_CONDITION", 0x10: "Z", 0x11: "X", 0x12: "R", 0x13: "Z_POW", 0x50: "HMR",
         0x20: "CZ", 0x21: "CX", 0x22: "SWAP", 0x30: "CCZ", 0x31: "CCX", 0x32: "CSWAP",
         0x40: "BIT_STORE0", 0x41: "BIT_STORE1", 0x42: "BIT_INVERT", 0x06: "INFO_TAG", 0x07: "DEBUG_PRINT_EMPTY",
         0x47: "DEBUG_PRINT_C", 0x17: "DEBUG_PRINT_Q"}
NAMES[0x81] = "PUSH_CONDITION"  # PUSH_CONDITION is 0x1 | COND; the generic "_IF" rule names the rest
OPCODE = {n: k for k, n in NAMES.items()}
TOFFOLI_BASE = {0x30, 0x31, 0x32}
WRITERS = {0x50, 0x40, 0x41, 0x42}  # the base opcodes that write a bit: HMR, BIT_STORE0, BIT_STORE1, BIT_INVERT


def name(t: int) -> str:
    if t == 0x81:
        return NAMES[0x81]
    base = t & ~HAS_COND
    return NAMES[base] + ("_IF" if t & HAS_COND else "")


def _lut(pred) -> np.ndarray:
    return np.array([pred(t) for t in range(256)], dtype=bool)


L3Q = _lut(lambda t: t & 0x30 == 0x30)
L2Q = _lut(lambda t: t & 0x30 == 0x20)
L1Q = _lut(lambda t: t & 0x30 == 0x10)
L1B = _lut(lambda t: bool(t & HAS_1B))
LCOND = _lut(lambda t: bool(t & HAS_COND))
LANGLE = _lut(lambda t: t & 0x7F == 0x13)
LTAG = _lut(lambda t: t == 0x06)
LTOF = _lut(lambda t: (t & 0x7F) in TOFFOLI_BASE)
LWRITER = _lut(lambda t: (t & 0x7F) in WRITERS)
LPUSH = _lut(lambda t: t == 0x81)
LPOP = _lut(lambda t: t == 0x01)
VALID = _lut(lambda t: (t & 0x7F) in NAMES or t == 0x81)
VALID[0x81] = True

_PACKETS = ["qqq0", "qqq1", "qqq2", "qq0", "qq1", "q0", "b0", "bc", "angles"]  # payload types 2..10


def _lut_of(arr: str) -> np.ndarray:
    return L3Q if arr.startswith("qqq") else L2Q if arr.startswith("qq") else L1Q if arr == "q0" else \
        L1B if arr == "b0" else LCOND if arr == "bc" else LANGLE


@dataclass
class Circuit:
    types: np.ndarray                      # uint8 [n]
    qqq0: np.ndarray; qqq1: np.ndarray; qqq2: np.ndarray   # uint32, one entry per 3-qubit instruction
    qq0: np.ndarray; qq1: np.ndarray                       # uint32, per 2-qubit instruction
    q0: np.ndarray                                         # uint32, per 1-qubit instruction (incl. HMR)
    b0: np.ndarray                                         # uint32, per target-bit instruction (incl. HMR)
    bc: np.ndarray                                         # uint32, per condition-bit instruction (incl. PUSH)
    angles: np.ndarray                                     # uint64 [m, 2]: turns = w0/2^128 + w1/2^64 (w1 = 2^63: half a turn)
    registers: list = field(default_factory=list)          # [(name, uint32 ids, qubit ids have bit 31 set)]
    tag_ends: np.ndarray = None                            # uint64 [num_info_tags]
    tag_chars: bytes = b""
    version: int = 2

    # ---- the file ----
    @classmethod
    def read(cls, path) -> "Circuit":
        buf = np.memmap(path, dtype=np.uint8, mode="r")
        if bytes(buf[:16]) != MAGIC:
            raise ValueError("not a kmb file")
        version, nq, nb, nreg, nops = struct.unpack("<IIIIQ", bytes(buf[16:40]))
        if version != 2:
            raise ValueError(f"kmb version {version}")
        hdr = struct.unpack("<8Q", bytes(buf[40:104]))
        pos = 104
        regs = []
        for _ in range(nreg):
            ptype, plen = struct.unpack("<QQ", bytes(buf[pos:pos + 16]))
            assert ptype == 0
            nl, rl = struct.unpack("<II", bytes(buf[pos + 16:pos + 24]))
            nm = bytes(buf[pos + 24:pos + 24 + nl]).decode()
            ids = np.frombuffer(buf, dtype=np.uint32, count=rl, offset=pos + 24 + nl).copy()
            regs.append((nm, ids))
            pos += 16 + plen

        def packet(expect):
            nonlocal pos
            ptype, plen = struct.unpack("<QQ", bytes(buf[pos:pos + 16]))
            if ptype != expect:
                raise ValueError(f"packet {ptype}, expected {expect}")
            off = pos + 16
            pos += 16 + plen
            return off, plen

        off, plen = packet(1)
        assert plen == nops
        types = np.frombuffer(buf, dtype=np.uint8, count=nops, offset=off)
        arrs = {}
        for k, nm in enumerate(_PACKETS):
            off, plen = packet(2 + k)
            if nm == "angles":
                arrs[nm] = np.frombuffer(buf, dtype=np.uint64, count=plen // 8, offset=off).reshape(-1, 2)
            else:
                arrs[nm] = np.frombuffer(buf, dtype=np.uint32, count=plen // 4, offset=off)
        off, plen = packet(11)
        ntag = struct.unpack("<Q", bytes(buf[off:off + 8]))[0]
        ends = np.frombuffer(buf, dtype=np.uint64, count=ntag, offset=off + 8).copy()
        chars = bytes(buf[off + 8 + 8 * ntag: off + plen])
        c = cls(types=types, registers=regs, tag_ends=ends, tag_chars=chars, version=version, **arrs)
        c._check(hdr, nq, nb)
        return c

    @classmethod
    def from_ops(cls, ops, registers=()) -> "Circuit":
        """A circuit from instructions, the inverse of the file's layout. Each op is (name, qubits, bits) with name as
        in NAMES; a trailing '_IF' takes its condition bit as the last of `bits`; HMR and BIT_* write bits[0];
        PUSH_CONDITION takes bits[0]; Z_POW takes a 4th item, the angle's two uint64 words; INFO_TAG takes its text
        as the 4th item. registers: (name, ids) with qubit ids marked by bit 31, as in the file."""
        types, arrs, tags = [], {nm: [] for nm in _PACKETS}, []
        for op in ops:
            nm, qs, bs = op[0], tuple(op[1]), list(op[2])
            cond = nm.endswith("_IF")
            t = 0x81 if nm == "PUSH_CONDITION" else OPCODE[nm[:-3] if cond else nm] | (HAS_COND if cond else 0)
            types.append(t)
            if L3Q[t]:
                arrs["qqq0"].append(qs[0]); arrs["qqq1"].append(qs[1]); arrs["qqq2"].append(qs[2])
            elif L2Q[t]:
                arrs["qq0"].append(qs[0]); arrs["qq1"].append(qs[1])
            elif L1Q[t]:
                arrs["q0"].append(qs[0])
            if L1B[t]:
                arrs["b0"].append(bs[0])
            if LCOND[t]:
                arrs["bc"].append(bs[-1])
            if LANGLE[t]:
                arrs["angles"].append(op[3])
            if LTAG[t]:
                tags.append(op[3].encode())
        kw = {nm: np.array(v, dtype=np.uint32) for nm, v in arrs.items() if nm != "angles"}
        kw["angles"] = np.array(arrs["angles"], dtype=np.uint64).reshape(-1, 2)
        ends = np.cumsum([len(x) for x in tags], dtype=np.uint64) if tags else np.zeros(0, np.uint64)
        regs = [(n, np.asarray(ids, dtype=np.uint32)) for n, ids in registers]
        return cls(types=np.array(types, dtype=np.uint8), registers=regs, tag_ends=ends, tag_chars=b"".join(tags),
                   **kw)

    def _check(self, hdr=None, nq=None, nb=None):
        """The format's validation rules 2-13 against the header (when read) and the arrays."""
        want = self.header_counts()
        if hdr is not None and tuple(hdr) != want:
            raise ValueError(f"header counts {hdr} != computed {want}")
        if nq is not None and (nq, nb) != (self.num_qubits, self.num_bits):
            raise ValueError(f"num_qubits/num_bits {(nq, nb)} != {(self.num_qubits, self.num_bits)}")
        bc = _bincount(self.types)
        if bc[~VALID].any():
            raise ValueError("unknown opcode")
        for nm in _PACKETS:
            if len(getattr(self, nm)) != int(bc[_lut_of(nm)].sum()):
                raise ValueError(f"{nm} length")

    def header_counts(self):
        bc = _bincount(self.types)
        return (int(bc[L3Q].sum()), int(bc[L2Q].sum()), int(bc[L1Q].sum()), int(bc[L1B].sum()), int(bc[LCOND].sum()),
                int(bc[LANGLE].sum()), int(bc[LTAG].sum()), len(self.tag_chars))

    @property
    def num_ops(self) -> int:
        return len(self.types)

    def _max_id(self, qubit: bool) -> int:
        m = -1
        if qubit:
            for nm in ("qqq0", "qqq1", "qqq2", "qq0", "qq1", "q0"):
                a = getattr(self, nm)
                if len(a):
                    m = max(m, int(a.max()))
            for _, ids in self.registers:
                q = ids[ids >> 31 == 1] & 0x7FFFFFFF
                if len(q):
                    m = max(m, int(q.max()))
        else:
            for nm in ("b0", "bc"):
                a = getattr(self, nm)
                if len(a):
                    m = max(m, int(a.max()))
            for _, ids in self.registers:
                q = ids[ids >> 31 == 0]
                if len(q):
                    m = max(m, int(q.max()))
        return m

    @property
    def num_qubits(self) -> int:
        return self._max_id(True) + 1

    @property
    def num_bits(self) -> int:
        return self._max_id(False) + 1

    def chunks(self):
        """The file's bytes, canonical, as an iterator of buffers (so a writer streams and a hash needs no copy)."""
        yield MAGIC + struct.pack("<IIIIQ", self.version, self.num_qubits, self.num_bits, len(self.registers),
                                  self.num_ops) + struct.pack("<8Q", *self.header_counts())
        for nm, ids in self.registers:
            nmb = nm.encode()
            yield struct.pack("<QQII", 0, 8 + len(nmb) + 4 * len(ids), len(nmb), len(ids)) + nmb
            yield np.ascontiguousarray(ids, dtype="<u4")
        yield struct.pack("<QQ", 1, self.num_ops)
        yield self.types
        for k, nm in enumerate(_PACKETS):
            a = getattr(self, nm)
            yield struct.pack("<QQ", 2 + k, a.nbytes)
            yield np.ascontiguousarray(a)
        yield struct.pack("<QQQ", 11, 8 * (len(self.tag_ends) + 1) + len(self.tag_chars), len(self.tag_ends))
        yield np.ascontiguousarray(self.tag_ends, dtype="<u8")
        yield self.tag_chars

    def write(self, path_or_file) -> str:
        """Write the canonical .kmb; returns the sha256 of the bytes written."""
        h = hashlib.sha256()
        f = open(path_or_file, "wb") if isinstance(path_or_file, (str, bytes)) or hasattr(path_or_file, "__fspath__") \
            else path_or_file
        try:
            for ch in self.chunks():
                mv = _view(ch)
                h.update(mv)
                f.write(mv)
        finally:
            if f is not path_or_file:
                f.close()
        return h.hexdigest()

    def sha256(self) -> str:
        h = hashlib.sha256()
        for ch in self.chunks():
            h.update(_view(ch))
        return h.hexdigest()

    # ---- slicing ----
    def _before(self, a: int) -> dict:
        """How many operands of each array the first a instructions consumed (one pass, counts per opcode)."""
        bc = _bincount(self.types[:a])
        return {nm: int(bc[_lut_of(nm)].sum()) for nm in _PACKETS} | {"tags": int(bc[LTAG].sum())}

    def depth(self, a: int) -> int:
        """Condition-stack depth before instruction a (POP on an empty stack does nothing)."""
        _, clamped = _depth_events(self.types[:a])
        return int(clamped[-1]) if len(clamped) else 0

    def slice(self, a: int, b: int, allow_open: bool = False) -> "Circuit":
        """Instructions [a, b) with the same registers. The condition stack is simulator state: a boundary inside a
        PUSH/POP block is refused unless allow_open (a stage cut should sit at depth 0)."""
        if not allow_open and (self.depth(a) or self.depth(b)):
            raise ValueError("slice boundary inside a condition block")
        return self._piece(a, b, self._before(a), self._before(b))

    def pieces(self, cuts, allow_open: bool = False):
        """The slices between consecutive cuts (0 and num_ops added), in one pass over the stream rather than one per
        cut: yields (a, b, slice). Refuses a cut inside a condition block unless allow_open, as slice does."""
        cuts = sorted({0, self.num_ops, *(int(x) for x in cuts)})
        if not allow_open:
            ev, clamped = _depth_events(self.types)
            k = np.searchsorted(ev, cuts, side="left")  # events before each cut
            if len(ev) and np.where(k > 0, clamped[np.maximum(k - 1, 0)], 0).any():
                raise ValueError("a cut inside a condition block")
        off = {nm: 0 for nm in _PACKETS} | {"tags": 0}
        for a, b in zip(cuts, cuts[1:]):
            bc = _bincount(self.types[a:b])
            nxt = {nm: off[nm] + int(bc[_lut_of(nm)].sum()) for nm in _PACKETS} | {"tags": off["tags"] + int(bc[LTAG].sum())}
            yield a, b, self._piece(a, b, off, nxt)
            off = nxt

    @classmethod
    def concat(cls, parts) -> "Circuit":
        """The instructions of parts in order (pieces of one circuit with replacements between them: a rewrite in
        pieces, so a 53M-instruction file is never decoded whole). Registers and version from the first part."""
        parts = list(parts)
        kw = {nm: np.concatenate([getattr(p, nm) for p in parts]) for nm in _PACKETS if nm != "angles"}
        kw["angles"] = np.concatenate([p.angles.reshape(-1, 2) for p in parts]).astype(np.uint64)
        ends, off = [], 0
        for p in parts:
            e = (p.tag_ends if p.tag_ends is not None else np.zeros(0, np.uint64)).astype(np.uint64)
            ends.append(e + np.uint64(off))
            off += len(p.tag_chars)
        return cls(types=np.concatenate([p.types for p in parts]).astype(np.uint8), registers=parts[0].registers,
                   tag_ends=np.concatenate(ends) if ends else np.zeros(0, np.uint64),
                   tag_chars=b"".join(p.tag_chars for p in parts), version=parts[0].version, **kw)

    def keep(self, mask) -> "Circuit":
        """The instructions where mask is True, in order, with their operands and tags (a deletion's rewrite)."""
        mask = np.asarray(mask, bool)
        t = self.types
        kw = {nm: getattr(self, nm)[mask[_lut_of(nm)[t]]] for nm in _PACKETS}
        ends = self.tag_ends.astype(np.int64)
        starts = np.concatenate([[0], ends[:-1]])
        kept = mask[LTAG[t]]
        chars = b"".join(self.tag_chars[a:b] for a, b, k in zip(starts, ends, kept) if k)
        new_ends = np.cumsum((ends - starts)[kept]).astype(np.uint64)
        return Circuit(types=t[mask], registers=self.registers, tag_ends=new_ends, tag_chars=chars,
                       version=self.version, **kw)

    def _piece(self, a: int, b: int, ca: dict, cb: dict) -> "Circuit":
        kw = {nm: getattr(self, nm)[ca[nm]:cb[nm]] for nm in _PACKETS}
        ends = self.tag_ends[ca["tags"]:cb["tags"]]
        lo = int(self.tag_ends[ca["tags"] - 1]) if ca["tags"] else 0
        hi = int(self.tag_ends[cb["tags"] - 1]) if cb["tags"] else 0
        return Circuit(types=self.types[a:b], registers=self.registers, tag_ends=ends - np.uint64(lo),
                       tag_chars=self.tag_chars[lo:hi], version=self.version, **kw)

    def decode(self, a: int = 0, b: int | None = None) -> list:
        """Instructions [a, b) as (index, name, qubits, target bit, condition bit) tuples, names as name() gives them
        (with _IF). A Python list: for windows of up to a few million instructions (passes, scans)."""
        b = self.num_ops if b is None else b
        t = self.types
        ca, cb_ = self._before(a), self._before(b)
        k3 = k2 = k1 = kb = kc = 0
        q30, q31, q32 = (getattr(self, nm)[ca["qqq0"]:cb_["qqq0"]].tolist() for nm in ("qqq0", "qqq1", "qqq2"))
        q20, q21 = (getattr(self, nm)[ca["qq0"]:cb_["qq0"]].tolist() for nm in ("qq0", "qq1"))
        q10 = self.q0[ca["q0"]:cb_["q0"]].tolist()
        b0, bc = self.b0[ca["b0"]:cb_["b0"]].tolist(), self.bc[ca["bc"]:cb_["bc"]].tolist()
        l3, l2, l1, lb, lc = L3Q.tolist(), L2Q.tolist(), L1Q.tolist(), L1B.tolist(), LCOND.tolist()
        names = [name(x) if VALID[x] else "?" for x in range(256)]
        out = []
        for i, op in enumerate(t[a:b].tolist(), start=a):
            if l3[op]:
                qs = (q30[k3], q31[k3], q32[k3]); k3 += 1
            elif l2[op]:
                qs = (q20[k2], q21[k2]); k2 += 1
            elif l1[op]:
                qs = (q10[k1],); k1 += 1
            else:
                qs = ()
            tb = cb = None
            if lb[op]:
                tb = b0[kb]; kb += 1
            if lc[op]:
                cb = bc[kc]; kc += 1
            out.append((i, names[op], qs, tb, cb))
        return out

    def tags(self) -> list:
        """(instruction index, text) of every INFO_TAG, in stream order."""
        ends = self.tag_ends.astype(np.int64)
        starts = np.concatenate([[0], ends[:-1]])
        return [(int(p), self.tag_chars[a:b].decode()) for p, a, b in zip(np.flatnonzero(LTAG[self.types]), starts, ends)]

    def valid_cuts(self) -> np.ndarray:
        """Boundaries i in [0, n] at which the condition stack is empty (a cut there is safe), int32."""
        ev, clamped = _depth_events(self.types)
        lo = np.concatenate([[0], ev + 1])                      # boundary ranges between events: [lo, hi]
        hi = np.concatenate([ev, [self.num_ops]])
        depth = np.concatenate([[0], clamped])
        return np.concatenate([np.arange(a, b + 1, dtype=np.int32) for a, b, d in zip(lo, hi, depth) if d == 0] +
                              [np.zeros(0, np.int32)])

    # ---- counts ----
    def static_counts(self) -> dict:
        bc = _bincount(self.types)
        return {name(t): int(bc[t]) for t in range(256) if bc[t]}

    def toffoli_like(self) -> int:
        return int(_bincount(self.types)[LTOF].sum())

    def firing_probabilities(self, free_bits=None, max_vars: int = 24, max_terms: int = 1 << 20):
        """Exact probability that each Toffoli-like instruction executes (in stream order), when the bits in
        `free_bits` start as independent fair bits (default: every bit in a register, the verifier's inputs) and
        every HMR outcome is an independent fair bit. Bits are polynomials over GF(2) in those variables; a gate
        fires when the polynomials on the condition stack and its own condition are all 1. One pass in Python over
        the instructions that write a bit, push, pop or are Toffoli-like (the rest cannot change a condition);
        only each bit's current polynomial is kept. Returns (probs, n_variables, info)."""
        t = self.types
        if free_bits is None:
            free_bits = {int(x) for _, ids in self.registers for x in ids[ids >> 31 == 0]}
        free_bits = set(free_bits)
        ev = np.flatnonzero(LWRITER[t] | LPUSH[t] | LPOP[t] | LTOF[t])
        cpos = np.cumsum(LCOND[t], dtype=np.int32)         # conditions consumed through instruction i
        kind = t[ev]
        has_c = LCOND[kind]
        cbit = np.where(has_c, self.bc[np.clip(cpos[ev] - 1, 0, max(len(self.bc) - 1, 0))].astype(np.int64) if len(self.bc) else 0, -1)
        del cpos
        bpos = np.cumsum(L1B[t], dtype=np.int32)
        tbit = np.where(L1B[kind], self.b0[np.clip(bpos[ev] - 1, 0, max(len(self.b0) - 1, 0))].astype(np.int64) if len(self.b0) else 0, -1)
        del bpos
        kind, cbit, tbit = kind.tolist(), cbit.tolist(), tbit.tolist()
        cur, stack, memo, probs = {}, [], {}, []
        nvar = hm = 0

        def get(b):
            p = cur.get(b)
            if p is None:
                p = cur[b] = frozenset([frozenset([("in", b)])]) if b in free_bits else ZERO
            return p

        for k in range(len(ev)):
            op = kind[k]
            if op == 0x81:
                stack.append(get(cbit[k])); continue
            if op == 0x01:
                if stack:
                    stack.pop()
                continue
            ps = stack + [get(cbit[k])] if cbit[k] >= 0 else stack
            if (op & 0x7F) in TOFFOLI_BASE:
                if not ps:
                    probs.append(1.0); continue
                key = frozenset(ps)
                pr = memo.get(key)
                if pr is None:
                    if len(memo) > 200000:
                        memo.clear()
                    pr = memo[key] = prob_all(ps, max_vars)
                probs.append(pr); continue
            g = ONE
            for c in ps:
                g = pmul(g, c)
            bit = tbit[k]
            old = get(bit)
            base = op & 0x7F
            if base == 0x50:
                new = frozenset([frozenset([("hmr", hm)])]); hm += 1
                cur[bit] = new if g == ONE else pxor(pmul(g, new), pmul(pxor(ONE, g), old))
            elif base == 0x40:
                cur[bit] = ZERO if g == ONE else pmul(old, pxor(ONE, g))
            elif base == 0x41:
                cur[bit] = ONE if g == ONE else pxor(old, pmul(g, pxor(ONE, old)))
            else:
                cur[bit] = pxor(old, g)
            if len(cur[bit]) > max_terms:
                raise ValueError(f"a bit's polynomial passed {max_terms} terms at instruction {int(ev[k])}: sample instead")
        return np.array(probs), hm + len(free_bits), {"events": len(ev), "free_bits": len(free_bits), "hmr": hm, "live_terms": sum(len(p) for p in cur.values()), "max_terms": max((len(p) for p in cur.values()), default=0)}

    def mean_toffolis(self, free_bits=None, shots: int = 1 << 16, seed: int = 1, exact_ops: int = 2_000_000):
        """Mean Toffoli-like gates executed per shot: (mean, se, info). Exact (se 0) while every bit's polynomial
        stays small; otherwise sampled by `sample_toffolis` (the classical trajectory only, bit-parallel)."""
        try:
            if self.num_ops > exact_ops:
                raise ValueError(f"{self.num_ops} instructions > {exact_ops}: the exact pass costs ~0.1 ms per instruction on dqi")
            p, nvar, info = self.firing_probabilities(free_bits)
            return float(p.sum()), 0.0, info | {"method": "exact", "static": self.toffoli_like()}
        except ValueError as e:
            m, se, info = self.sample_toffolis(free_bits, shots, seed)
            return m, se, info | {"method": f"sampled ({e})", "static": self.toffoli_like()}

    def sample_toffolis(self, free_bits=None, shots: int = 1 << 16, seed: int = 1, per_gate: bool = False):
        """The classical part of kickmix (bits, condition stack) run on `shots` shots at once, 64 per uint64 word:
        free bits and HMR outcomes are fair random bits, every other instruction cannot change a condition.
        Returns (mean, se, info); se is across words of 64 shots. per_gate: info["probs"] holds each Toffoli-like's
        firing frequency on the shots (stream order, firing_probabilities' order), for a circuit whose exact pass
        passes its term cap."""
        t = self.types
        if free_bits is None:
            free_bits = {int(x) for _, ids in self.registers for x in ids[ids >> 31 == 0]}
        free_bits = set(free_bits)
        W = shots // 64
        rng = np.random.default_rng(seed)
        rand = lambda: rng.integers(0, 1 << 64, size=W, dtype=np.uint64, endpoint=False)
        ev = np.flatnonzero(LWRITER[t] | LPUSH[t] | LPOP[t] | LTOF[t])
        cpos = np.cumsum(LCOND[t], dtype=np.int32)
        kind = t[ev]
        cbit = np.where(LCOND[kind], self.bc[np.clip(cpos[ev] - 1, 0, max(len(self.bc) - 1, 0))].astype(np.int64) if len(self.bc) else 0, -1)
        del cpos
        bpos = np.cumsum(L1B[t], dtype=np.int32)
        tbit = np.where(L1B[kind], self.b0[np.clip(bpos[ev] - 1, 0, max(len(self.b0) - 1, 0))].astype(np.int64) if len(self.b0) else 0, -1)
        del bpos
        kind, cbit, tbit = kind.tolist(), cbit.tolist(), tbit.tolist()
        ONES = np.full(W, np.uint64(0xFFFFFFFFFFFFFFFF))
        zero = np.zeros(W, dtype=np.uint64)
        cur, cum = {}, [ONES]
        tally = np.zeros(W, dtype=np.int64)
        gate = []

        def get(b):
            v = cur.get(b)
            if v is None:
                v = cur[b] = rand() if b in free_bits else zero
            return v

        for k in range(len(ev)):
            op = kind[k]
            if op == 0x81:
                cum.append(cum[-1] & get(cbit[k])); continue
            if op == 0x01:
                if len(cum) > 1:
                    cum.pop()
                continue
            g = cum[-1] & get(cbit[k]) if cbit[k] >= 0 else cum[-1]
            base = op & 0x7F
            if base in TOFFOLI_BASE:
                fired = np.bitwise_count(g); tally += fired
                if per_gate:
                    gate.append(int(fired.sum()))
                continue
            bit = tbit[k]; old = get(bit)
            if base == 0x50:
                cur[bit] = (rand() & g) | (old & ~g)
            elif base == 0x40:
                cur[bit] = old & ~g
            elif base == 0x41:
                cur[bit] = old | g
            else:
                cur[bit] = old ^ g
        per_word = tally / 64.0
        info = {"events": len(ev), "shots": shots}
        if per_gate:
            info["probs"] = np.array(gate, dtype=np.float64) / (64 * W)
        return float(per_word.mean()), float(per_word.std(ddof=1) / np.sqrt(W)), info

    # ---- liveness ----
    def liveness(self):
        """first[q], last[q] (instruction index; -1 for an unused qubit), live[t] = qubits whose [first, last]
        interval contains t (int32), and the peak. Registers' qubits are not extended: the stream's own span."""
        t = self.types
        n = len(t)
        nq = self.num_qubits
        first = np.full(nq, n, dtype=np.int64)
        last = np.full(nq, -1, dtype=np.int64)
        CH = 1 << 22
        for lut, names in ((L3Q, ("qqq0", "qqq1", "qqq2")), (L2Q, ("qq0", "qq1")), (L1Q, ("q0",))):
            idx = np.flatnonzero(lut[t]).astype(np.int32)
            for nm in names:
                arr = getattr(self, nm)
                for i in range(0, len(arr), CH):
                    q = arr[i:i + CH].astype(np.int64); ix = idx[i:i + CH]
                    f = np.full(nq, n, dtype=np.int64); f[q[::-1]] = ix[::-1]
                    l = np.full(nq, -1, dtype=np.int64); l[q] = ix
                    first, last = np.minimum(first, f), np.maximum(last, l)
            del idx
        used = last >= 0
        d = np.bincount(first[used], minlength=n + 1).astype(np.int32)
        d -= np.bincount(last[used] + 1, minlength=n + 1).astype(np.int32)
        live = np.cumsum(d, dtype=np.int32)[:n]
        first[~used] = -1
        return first, last, live, int(live.max()) if n else 0


def _view(ch):
    """A chunk as bytes-like (an empty array has no buffer to cast)."""
    if isinstance(ch, (bytes, bytearray)):
        return ch
    a = np.ascontiguousarray(ch)
    return a.reshape(-1).view(np.uint8) if a.size else b""


def _bincount(types: np.ndarray) -> np.ndarray:
    """Opcode histogram in chunks (np.bincount would copy the stream to intp)."""
    out = np.zeros(256, dtype=np.int64)
    for i in range(0, len(types), 1 << 24):
        out += np.bincount(types[i:i + (1 << 24)], minlength=256)
    return out


def _depth_events(types: np.ndarray):
    """The PUSH/POP positions and the condition-stack depth just after each (a POP on an empty stack leaves it empty:
    the running sum reflected at 0, depth = run - min(0, running min of run))."""
    ev = np.flatnonzero(LPUSH[types] | LPOP[types])
    run = np.cumsum(np.where(LPUSH[types[ev]], 1, -1))
    return ev, run - np.minimum(np.minimum.accumulate(run), 0)


# ---- polynomials over GF(2): frozenset of monomials, a monomial a frozenset of variables ----
ONE = frozenset([frozenset()])
ZERO = frozenset()


def pxor(a, b):
    return a ^ b


def pmul(a, b):
    out = set()
    for m in a:
        for n in b:
            out ^= {m | n}
    return frozenset(out)


def prob_all(polys, max_vars=24):
    """P(every polynomial == 1) with the variables independent fair bits. Affine forms by GF(2) rank (2^-rank, or 0
    when inconsistent); otherwise by enumeration over the union of variables."""
    if any(p == ZERO for p in polys):
        return 0.0
    if all(all(len(m) <= 1 for m in p) for p in polys):
        idx, rows = {}, []
        for p in polys:
            mask, c = 0, 0
            for m in p:
                if m:
                    v = next(iter(m)); mask |= 1 << idx.setdefault(v, len(idx))
                else:
                    c = 1
            rhs = 1 ^ c
            for pm, pr, piv in rows:
                if mask >> piv & 1:
                    mask ^= pm; rhs ^= pr
            if mask == 0:
                if rhs:
                    return 0.0
                continue
            rows.append((mask, rhs, mask.bit_length() - 1))
        return 2.0 ** -len(rows)
    vs = sorted({v for p in polys for m in p for v in m}, key=repr)
    n = len(vs)
    if n > max_vars:
        raise ValueError(f"{n} variables in one condition set: sample with Simulator instead")
    pos = {v: i for i, v in enumerate(vs)}
    a = np.arange(1 << n, dtype=np.uint32)
    ok = np.ones(1 << n, bool)
    for p in polys:
        val = np.zeros(1 << n, bool)
        for m in p:
            tt = np.ones(1 << n, bool)
            for v in m:
                tt &= ((a >> pos[v]) & 1).astype(bool)
            val ^= tt
        ok &= val
    return float(ok.mean())

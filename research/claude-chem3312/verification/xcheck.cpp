// xcheck.cpp - second independent exact checker for the ANGLE_k loaders (verify_unwired).
// Reads the .kmb bytes directly (own parser, no kickmix), simulates every address one by one.
// Phase is kept exactly as an affine GF(2) function of all HMR outcomes of the circuit:
//   phase = c0 XOR sum_v L[v]*outcome_v .  "Clean" means c0 = 0 and L = 0, i.e. for every outcome string.
// Traversal is the official one (forward k=0..14 from words 0 / previous batch, reverse k=14..0 from batch k).
// usage: xcheck OLD_DIR NEW_DIR [--mutate N] [--dump-ops FILE_PREFIX]
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <array>
#include <bitset>
#include <map>
#include <random>
#include <algorithm>
#include <stdexcept>

static const int NADDR = 1219, NSEL = 11, NALL = 2048, K = 15, J = 5, BROT = 7;
typedef std::bitset<512> VarSet;

struct Op { uint8_t code; int q0, q1, q2; int bit, cond; };
struct Circ {
    std::string path;
    uint32_t version, nq, nbits, nregs;
    uint64_t hdr[9];
    std::vector<Op> ops;
    std::map<std::string, std::vector<int>> regs;
    int n_ccx = 0, n_ccx_cond = 0, n_hmr = 0, maxq = -1;
    std::map<std::string, int> kinds;
};

static void die(const std::string &s) { fprintf(stderr, "FATAL: %s\n", s.c_str()); exit(1); }

static std::vector<uint8_t> slurp(const std::string &p) {
    FILE *f = fopen(p.c_str(), "rb");
    if (!f) die("cannot open " + p);
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    std::vector<uint8_t> v(n);
    if (n && fread(v.data(), 1, n, f) != (size_t)n) die("short read " + p);
    fclose(f);
    return v;
}
static uint32_t u32(const std::vector<uint8_t> &d, size_t o) { uint32_t x; if (o + 4 > d.size()) die("eof"); memcpy(&x, &d[o], 4); return x; }
static uint64_t u64(const std::vector<uint8_t> &d, size_t o) { uint64_t x; if (o + 8 > d.size()) die("eof"); memcpy(&x, &d[o], 8); return x; }

static const char *kind_name(uint8_t c) {
    switch (c & 127) {
        case 0x00: return "NEG"; case 0x01: return "POP"; case 0x10: return "Z"; case 0x11: return "X"; case 0x12: return "R";
        case 0x20: return "CZ"; case 0x21: return "CX"; case 0x22: return "SWAP"; case 0x30: return "CCZ"; case 0x31: return "CCX";
        case 0x32: return "CSWAP"; case 0x40: return "BIT_STORE0"; case 0x41: return "BIT_STORE1"; case 0x42: return "BIT_INVERT";
        case 0x50: return "HMR"; default: return "?";
    }
}

static Circ load(const std::string &path) {
    std::vector<uint8_t> d = slurp(path);
    Circ c; c.path = path;
    if (d.size() < 104) die("too small " + path);
    c.version = u32(d, 16); c.nq = u32(d, 20); c.nbits = u32(d, 24); c.nregs = u32(d, 28);
    for (int i = 0; i < 9; i++) c.hdr[i] = u64(d, 32 + 8 * i);
    if (c.version != 2) die("unexpected version");
    std::map<uint64_t, std::pair<size_t, uint64_t>> sec;
    size_t pos = 104;
    int nreg_seen = 0;
    while (pos < d.size()) {
        uint64_t idx = u64(d, pos), n = u64(d, pos + 8); pos += 16;
        if (pos + n > d.size()) die("section overruns file");
        if (idx == 0) {
            uint32_t nl = u32(d, pos), cnt = u32(d, pos + 4);
            if (8ull + nl + 4ull * cnt != n) die("register record length");
            std::string name((const char *)&d[pos + 8], nl);
            std::vector<int> ids;
            for (uint32_t i = 0; i < cnt; i++) {
                uint32_t e = u32(d, pos + 8 + nl + 4 * i);
                if (!(e & 0x80000000u)) die("register holds a classical bit");
                ids.push_back((int)(e & 0x7fffffffu));
            }
            if (c.regs.count(name)) die("duplicate register");
            c.regs[name] = ids; nreg_seen++;
        } else {
            if (sec.count(idx)) die("duplicate section");
            sec[idx] = {pos, n};
        }
        pos += n;
    }
    if (pos != d.size()) die("trailing bytes");
    if ((uint32_t)nreg_seen != c.nregs) die("register count differs from header");
    for (auto &kv : sec) if (kv.first > 11) die("unknown section id");
    if (sec.count(10) && sec[10].second) die("section 10 not empty");
    if (sec.count(11)) for (uint64_t i = 0; i < sec[11].second; i++) if (d[sec[11].first + i]) die("section 11 not zero");
    uint64_t nops = sec.count(1) ? sec[1].second : 0;
    if (nops != c.hdr[0]) die("op count differs from header");
    size_t cur[10] = {0};
    auto next = [&](int s) -> int {
        if (!sec.count(s) || (cur[s] + 1) * 4 > sec[s].second) die("operand section exhausted");
        uint32_t v = u32(d, sec[s].first + 4 * cur[s]); cur[s]++; return (int)v;
    };
    c.ops.reserve(nops);
    for (uint64_t i = 0; i < nops; i++) {
        uint8_t code = d[sec[1].first + i];
        Op o{code, -1, -1, -1, -1, -1};
        int cat = (code & 48) >> 4;
        if (cat == 1) { o.q0 = next(7); }
        else if (cat == 2) { o.q0 = next(5); o.q1 = next(6); }
        else if (cat == 3) { o.q0 = next(2); o.q1 = next(3); o.q2 = next(4); }
        if (code & 64) o.bit = next(8);
        if (code & 128) o.cond = next(9);
        int base = code & 127;
        // accept only the instruction kinds whose semantics are implemented below; anything else is fatal
        bool classical_gate = base == 0x11 || base == 0x21 || base == 0x31;
        bool phase_gate = base == 0x00 || base == 0x10 || base == 0x20 || base == 0x30;
        bool hmr = base == 0x50;
        if (!(classical_gate || phase_gate || hmr)) die(std::string("instruction kind not accepted: ") + kind_name(code) + " in " + path);
        if (classical_gate && (code & 128)) die("conditioned classical gate (outcome dependent values) in " + path);
        if (hmr && (code & 128)) die("conditioned HMR in " + path);
        int arity = base == 0x00 ? 0 : (base == 0x10 || base == 0x11 || hmr) ? 1 : (base == 0x20 || base == 0x21) ? 2 : 3;
        if (arity != cat && !(hmr && cat == 1)) die("operand count mismatch");
        for (int q : {o.q0, o.q1, o.q2}) if (q >= 0) { if (q >= (int)c.nq) die("qubit id beyond header"); c.maxq = std::max(c.maxq, q); }
        if (arity >= 2 && (o.q0 == o.q1 || (arity == 3 && (o.q0 == o.q2 || o.q1 == o.q2)))) die("repeated operand");
        if (o.bit >= (int)c.nbits || o.cond >= (int)c.nbits) die("bit id beyond header");
        if (base == 0x31 || base == 0x30) { c.n_ccx++; if (code & 128) c.n_ccx_cond++; }
        if (hmr) c.n_hmr++;
        c.kinds[std::string(kind_name(code)) + ((code & 128) ? " if" : "")]++;
        c.ops.push_back(o);
    }
    for (int s = 2; s <= 9; s++) { uint64_t n = sec.count(s) ? sec[s].second : 0; if (cur[s] * 4 != n) die("operand section not fully consumed"); }
    if ((uint64_t)c.n_ccx != c.hdr[1]) die("toffoli count differs from header");
    return c;
}

struct Res { bool selok, workok, phaseok; uint64_t words; };

// words: J words of BROT bits packed little endian (word j at bit 7j)
static Res run(const Circ &c, int address, uint64_t words, int drop_op = -1) {
    uint8_t q[256]; memset(q, 0, sizeof q);
    const std::vector<int> &sel = c.regs.at("selection");
    for (int i = 0; i < NSEL; i++) q[sel[i]] = (address >> i) & 1;
    const std::vector<int> *w[J];
    for (int j = 0; j < J; j++) { w[j] = &c.regs.at("word_" + std::to_string(j)); for (int b = 0; b < BROT; b++) q[(*w[j])[b]] = (words >> (j * BROT + b)) & 1; }
    int c0 = 0; VarSet L; std::vector<int> bitvar(c.nbits, -1); int nvar = 0;
    const int n = (int)c.ops.size();
    for (int i = 0; i < n; i++) {
        if (i == drop_op) continue;
        const Op &o = c.ops[i];
        switch (o.code & 127) {
            case 0x11: q[o.q0] ^= 1; break;
            case 0x21: q[o.q1] ^= q[o.q0]; break;
            case 0x31: q[o.q2] ^= q[o.q0] & q[o.q1]; break;
            case 0x50: { if (nvar >= 512) die("too many HMR"); int v = nvar++; if (q[o.q0]) L.flip(v); q[o.q0] = 0; bitvar[o.bit] = v; break; }
            default: {
                int m = 1;
                if ((o.code & 127) == 0x10) m = q[o.q0];
                else if ((o.code & 127) == 0x20) m = q[o.q0] & q[o.q1];
                else if ((o.code & 127) == 0x30) m = q[o.q0] & q[o.q1] & q[o.q2];
                if (o.code & 128) {
                    int v = bitvar[o.cond];
                    if (v < 0) { if (drop_op >= 0) break; die("condition on a never written bit"); }
                    if (m) L.flip(v);
                } else c0 ^= m;
            }
        }
    }
    Res r; r.selok = true; r.workok = true; r.phaseok = (c0 == 0) && L.none();
    for (int i = 0; i < NSEL; i++) if (q[sel[i]] != ((address >> i) & 1)) r.selok = false;
    uint8_t pub[256]; memset(pub, 0, sizeof pub);
    for (int s : sel) pub[s] = 1;
    r.words = 0;
    for (int j = 0; j < J; j++) for (int b = 0; b < BROT; b++) { pub[(*w[j])[b]] = 1; r.words |= (uint64_t)q[(*w[j])[b]] << (j * BROT + b); }
    for (int i = 0; i < (int)c.nq; i++) if (!pub[i] && q[i]) r.workok = false;
    return r;
}

struct FamilyOut { std::vector<std::vector<uint64_t>> batch; long fail_fwd = 0, fail_rev = 0, out_of_range_dirty[K] = {0}; };

static std::vector<Circ> family(const std::string &dir) {
    std::vector<Circ> f;
    for (int k = 0; k < K; k++) f.push_back(load(dir + "/angle_k_" + std::to_string(k) + ".kmb"));
    for (int k = 1; k < K; k++) {
        if (f[k].regs.at("selection") != f[0].regs.at("selection")) die("selection register differs between circuits");
        for (int j = 0; j < J; j++) if (f[k].regs.at("word_" + std::to_string(j)) != f[0].regs.at("word_" + std::to_string(j))) die("word register differs");
    }
    if (f[0].regs.size() != 1 + J) die("unexpected registers");
    if (f[0].regs.at("selection").size() != NSEL) die("selection width");
    std::vector<int> all = f[0].regs.at("selection");
    for (int j = 0; j < J; j++) { auto &w = f[0].regs.at("word_" + std::to_string(j)); if (w.size() != BROT) die("word width"); all.insert(all.end(), w.begin(), w.end()); }
    std::sort(all.begin(), all.end());
    if (std::adjacent_find(all.begin(), all.end()) != all.end()) die("public registers overlap");
    return f;
}

static FamilyOut traverse(const std::vector<Circ> &f, const char *name) {
    FamilyOut o; o.batch.assign(K, std::vector<uint64_t>(NALL, 0));
    for (int a = 0; a < NALL; a++) {
        uint64_t prev = 0;
        for (int k = 0; k < K; k++) {
            Res r = run(f[k], a, prev);
            bool ok = r.selok && r.workok && r.phaseok;
            o.batch[k][a] = r.words; prev = r.words;
            if (a < NADDR) { if (!ok) { o.fail_fwd++; if (o.fail_fwd <= 5) printf("  %s FAIL forward k=%d a=%d sel=%d work=%d phase=%d\n", name, k, a, r.selok, r.workok, r.phaseok); } }
            else if (!ok) o.out_of_range_dirty[k]++;
        }
        for (int k = K - 1; k >= 0; k--) {
            Res r = run(f[k], a, o.batch[k][a]);
            bool ok = r.selok && r.workok && r.phaseok && r.words == (k ? o.batch[k - 1][a] : 0);
            if (a < NADDR) { if (!ok) { o.fail_rev++; if (o.fail_rev <= 5) printf("  %s FAIL reverse k=%d a=%d sel=%d work=%d phase=%d words=%d\n", name, k, a, r.selok, r.workok, r.phaseok, r.words == (k ? o.batch[k - 1][a] : 0)); } }
        }
    }
    return o;
}

int main(int argc, char **argv) {
    if (argc < 3) die("usage: xcheck OLD_DIR NEW_DIR [--mutate N] [--dump-ops PREFIX]");
    std::vector<Circ> A = family(argv[1]), B = family(argv[2]);
    if (A[0].regs != B[0].regs) die("old and new register maps differ");
    int mutate = 0; std::string dump;
    for (int i = 3; i < argc; i++) {
        if (!strcmp(argv[i], "--mutate") && i + 1 < argc) mutate = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--dump-ops") && i + 1 < argc) dump = argv[++i];
    }
    if (!dump.empty()) {
        // text form in kickmix style, for a cross check of this parser against kickmix's own printer
        for (int side = 0; side < 2; side++) for (int k = 0; k < K; k++) {
            const Circ &c = (side ? B : A)[k];
            FILE *f = fopen((dump + (side ? "new_" : "old_") + std::to_string(k) + ".txt").c_str(), "w");
            if (!f) die("cannot write dump");
            for (const Op &o : c.ops) {
                fprintf(f, "%s", kind_name(o.code));
                for (int q : {o.q0, o.q1, o.q2}) if (q >= 0) fprintf(f, " q%d", q);
                if (o.bit >= 0) fprintf(f, " b%d", o.bit);
                if (o.cond >= 0) fprintf(f, " if b%d", o.cond);
                fprintf(f, "\n");
            }
            fclose(f);
        }
    }
    printf("selection qubits:"); for (int q : A[0].regs.at("selection")) printf(" %d", q); printf("\n");
    for (int side = 0; side < 2; side++) {
        const std::vector<Circ> &F = side ? B : A;
        long tof = 0; int qmax = 0;
        printf("%s family:\n", side ? "NEW" : "OLD");
        for (int k = 0; k < K; k++) {
            const Circ &c = F[k];
            printf("  k=%2d qubits_header=%u max_used=%d bits=%u ops=%zu toffoli=%d conditioned_toffoli=%d hmr=%d kinds:", k, c.nq, c.maxq + 1, c.nbits, c.ops.size(), c.n_ccx, c.n_ccx_cond, c.n_hmr);
            for (auto &kv : c.kinds) printf(" %s=%d", kv.first.c_str(), kv.second);
            printf("\n");
            tof += c.n_ccx; qmax = std::max(qmax, (int)c.nq);
        }
        printf("  toffoli per pass = %ld, max header qubits = %d\n", tof, qmax);
        // how the public registers are used (a pure XOR oracle never reads a word qubit)
        std::vector<int> isw(256, 0), iss(256, 0);
        for (int j = 0; j < J; j++) for (int q : F[0].regs.at("word_" + std::to_string(j))) isw[q] = 1;
        for (int q : F[0].regs.at("selection")) iss[q] = 1;
        for (int k = 0; k < K; k++) {
            long wread = 0, whmr = 0, starget = 0;
            for (const Op &o : F[k].ops) {
                int base = o.code & 127;
                if (base == 0x21) { wread += isw[o.q0]; starget += iss[o.q1]; }
                else if (base == 0x31) { wread += isw[o.q0] + isw[o.q1]; starget += iss[o.q2]; }
                else if (base == 0x11) starget += iss[o.q0];
                else if (base == 0x50) whmr += isw[o.q0] + iss[o.q0];
                else if (base == 0x10 || base == 0x20 || base == 0x30) for (int q : {o.q0, o.q1, o.q2}) if (q >= 0) wread += isw[q];
            }
            if (wread || whmr || starget) printf("  k=%2d word_qubit_reads=%ld public_HMR=%ld selection_targets=%ld\n", k, wread, whmr, starget);
        }
    }
    FamilyOut oa = traverse(A, "OLD"), ob = traverse(B, "NEW");
    printf("OLD: failing (address,circuit) pairs forward=%ld reverse=%ld over %d addresses\n", oa.fail_fwd, oa.fail_rev, NADDR);
    printf("NEW: failing (address,circuit) pairs forward=%ld reverse=%ld over %d addresses\n", ob.fail_fwd, ob.fail_rev, NADDR);
    long diff = 0, nonzero_pad = 0; long diffk[K] = {0};
    for (int a = 0; a < NADDR; a++) for (int k = 0; k < K; k++) for (int j = 0; j < J; j++) {
        int x = (oa.batch[k][a] >> (j * BROT)) & 127, y = (ob.batch[k][a] >> (j * BROT)) & 127;
        if (x != y) { diff++; diffk[k]++; }
    }
    printf("word table entries compared: %d x %d = %d ; differing entries: %ld\n", NADDR, K * J, NADDR * K * J, diff);
    for (int k = 0; k < K; k++) if (diffk[k]) printf("  batch %d differs in %ld entries\n", k, diffk[k]);
    long nz = 0; for (int a = 0; a < NADDR; a++) for (int k = 0; k < K; k++) nz += ob.batch[k][a] != 0;
    printf("nonzero batches in new table: %ld of %d\n", nz, NADDR * K);
    printf("out-of-range addresses 1219..2047 (829 of them) that are NOT clean in the forward pass, per circuit k:\n  old:");
    for (int k = 0; k < K; k++) printf(" %ld", oa.out_of_range_dirty[k]);
    printf("\n  new:");
    for (int k = 0; k < K; k++) printf(" %ld", ob.out_of_range_dirty[k]);
    printf("\n");
    long odiff[K] = {0};
    for (int a = NADDR; a < NALL; a++) for (int k = 0; k < K; k++) odiff[k] += oa.batch[k][a] != ob.batch[k][a];
    printf("out-of-range addresses whose cumulative batch value differs old vs new, per k:"); for (int k = 0; k < K; k++) printf(" %ld", odiff[k]); printf("\n");
    // write the word table (u8, NADDR x 75) for later checks
    FILE *f = fopen("xwords_old.bin", "wb"); FILE *g = fopen("xwords_new.bin", "wb");
    if (!f || !g) die("cannot write words");
    for (int a = 0; a < NADDR; a++) for (int k = 0; k < K; k++) for (int j = 0; j < J; j++) { fputc((oa.batch[k][a] >> (j * BROT)) & 127, f); fputc((ob.batch[k][a] >> (j * BROT)) & 127, g); }
    fclose(f); fclose(g);
    if (mutate) {
        std::mt19937 rng(20261126);
        printf("mutation test (drop one instruction, forward run of that circuit on all %d addresses):\n", NADDR);
        for (int k : {0, 1, 5, 7, 11}) {
            std::map<std::string, std::vector<int>> pool;
            for (int i = 0; i < (int)B[k].ops.size(); i++) {
                const Op &o = B[k].ops[i]; int base = o.code & 127;
                if (o.code & 128) pool["conditioned phase fix"].push_back(i);
                else if (base == 0x31) pool["CCX"].push_back(i);
                else if (base == 0x21) pool["CX"].push_back(i);
            }
            printf("  k=%2d", k);
            for (auto &kv : pool) {
                int det = 0, trials = std::min(mutate, (int)kv.second.size());
                std::vector<int> v = kv.second; std::shuffle(v.begin(), v.end(), rng);
                for (int t = 0; t < trials; t++) {
                    bool bad = false;
                    for (int a = 0; a < NADDR && !bad; a++) {
                        uint64_t prev = k ? ob.batch[k - 1][a] : 0;
                        Res r = run(B[k], a, prev, v[t]);
                        if (!(r.selok && r.workok && r.phaseok && r.words == ob.batch[k][a])) bad = true;
                    }
                    det += bad;
                }
                printf("  %s: %d/%d detected", kv.first.c_str(), det, trials);
            }
            printf("\n");
        }
    }
    bool ok = !ob.fail_fwd && !ob.fail_rev && !oa.fail_fwd && !oa.fail_rev && !diff;
    printf("VERDICT %s\n", ok ? "PASS: both families exact on all addresses/outcomes forward+reverse, identical words" : "FAIL");
    return ok ? 0 : 2;
}

// Bit-sliced simulator core for the invsqrt kickmix circuits (64 lanes per word).
// Semantics follow the track's verified Python simulator (inv37/u/fastsim.py).
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <cstring>
#include <algorithm>

typedef uint64_t u64;

enum Opc { X_, CX_, CCX_, CCZ_, CSWAP_, SWAP_, Z_, CZ_, HMR_, ZPOW_, NEG_, BINV_, BST0_, BST1_, PUSH_, POP_ };

struct Ins { int op, a, b, c, cond; u64 ang; };

static const int NQMAX = 40;
static const int NBMAX = 4096;
static const u64 NINPUT = 3133452ULL;

inline std::vector<Ins> load_ops(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(1); }
    int n = 0;
    if (fscanf(f, "%d", &n) != 1) exit(1);
    std::vector<Ins> v(n);
    for (int i = 0; i < n; i++) {
        unsigned long long ang;
        if (fscanf(f, "%d %d %d %d %d %llu", &v[i].op, &v[i].a, &v[i].b, &v[i].c, &v[i].cond, &ang) != 6) {
            fprintf(stderr, "parse error at op %d\n", i); exit(1);
        }
        v[i].ang = ang;
    }
    fclose(f);
    return v;
}

inline u64 splitmix(u64 z) {
    z += 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

inline u64 coin_word(u64 seed, u64 batch, u64 opidx) {
    return splitmix(splitmix(seed * 1000003ULL + batch) ^ (opidx * 0x2545F4914F6CDD1DULL));
}

struct State {
    u64 Q[NQMAX];
    u64 B[NBMAX];
    u64 sign;
    u64 rot[64];
    u64 cur;
    int sp;
    u64 stack[64];
    long long toff;  // executed Toffoli-like count over lanes
};

inline void init_state(State& s, const u64* xs) {
    memset(s.Q, 0, sizeof(s.Q));
    memset(s.B, 0, sizeof(s.B));
    memset(s.rot, 0, sizeof(s.rot));
    s.sign = 0; s.cur = ~0ULL; s.sp = 0; s.toff = 0;
    for (int i = 0; i < 22; i++) {
        u64 w = 0;
        for (int l = 0; l < 64; l++) w |= ((xs[l] >> i) & 1ULL) << l;
        s.Q[i] = w;
    }
}

// Execute one instruction. coin = random word for HMR (ignored otherwise).
inline void step(State& s, const Ins& I, u64 coin, u64 lane_mask) {
    u64 m = s.cur;
    if (I.cond >= 0) m &= s.B[I.cond];
    switch (I.op) {
    case X_: s.Q[I.a] ^= m; break;
    case CX_: s.Q[I.b] ^= s.Q[I.a] & m; break;
    case CCX_: s.Q[I.c] ^= s.Q[I.a] & s.Q[I.b] & m; s.toff += __builtin_popcountll(m & lane_mask); break;
    case CCZ_: s.sign ^= s.Q[I.a] & s.Q[I.b] & s.Q[I.c] & m; s.toff += __builtin_popcountll(m & lane_mask); break;
    case CSWAP_: { u64 d = (s.Q[I.b] ^ s.Q[I.c]) & s.Q[I.a] & m; s.Q[I.b] ^= d; s.Q[I.c] ^= d;
        s.toff += __builtin_popcountll(m & lane_mask); } break;
    case SWAP_: { u64 d = (s.Q[I.a] ^ s.Q[I.b]) & m; s.Q[I.a] ^= d; s.Q[I.b] ^= d; } break;
    case Z_: s.sign ^= s.Q[I.a] & m; break;
    case CZ_: s.sign ^= s.Q[I.a] & s.Q[I.b] & m; break;
    case HMR_: { u64 out = coin & m; s.sign ^= out & s.Q[I.a]; s.Q[I.a] &= ~m; s.B[I.b] = (s.B[I.b] & ~m) | out; } break;
    case ZPOW_: { u64 t = s.Q[I.a] & m; while (t) { int l = __builtin_ctzll(t); s.rot[l] += I.ang; t &= t - 1; } } break;
    case NEG_: s.sign ^= m; break;
    case BINV_: s.B[I.a] ^= m; break;
    case BST0_: s.B[I.a] &= ~m; break;
    case BST1_: s.B[I.a] |= m; break;
    case PUSH_: s.stack[s.sp++] = s.cur; s.cur = s.cur & s.B[I.cond]; break;
    case POP_: s.cur = s.stack[--s.sp]; break;
    default: fprintf(stderr, "bad op %d\n", I.op); exit(1);
    }
}

inline void batch_inputs(u64 batch, u64* xs, u64& lane_mask) {
    lane_mask = 0;
    for (int l = 0; l < 64; l++) {
        u64 x = batch * 64 + l + 1;
        if (x <= NINPUT) { xs[l] = x; lane_mask |= 1ULL << l; }
        else xs[l] = 1;
    }
}

inline u64 nbatches() { return (NINPUT + 63) / 64; }

inline int nthreads() {
    int n = (int)std::thread::hardware_concurrency();
    const char* e = getenv("QSIM_THREADS");
    if (e) n = atoi(e);
    return n > 0 ? n : 4;
}

// Phase 1 of the sliding window: build `cap` y-functions, each a product of earlier ones, whose span (on the
// constrained columns) contains the early chips' high functions.
// Input: ny nfree nann nE cap p nfc ; free basis (3 u64 each); relation functionals; E rows; free column indices.
// Free columns: their values are unconstrained (delta vectors are added to the span and independence space).
// Stage A: products satisfying the relations until p products.  Stage B: products inside T = span(C, E, delta) .
// Output: count, then (u_lo u_hi v_lo v_hi) coefficient masks over the evolving basis.
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <random>
#include <thread>
#include <atomic>
#include <mutex>
#include <chrono>
#include <immintrin.h>
typedef uint64_t u64;
typedef unsigned __int128 u128;
static const int W = 3;
struct B {
  u64 w[W] = {0, 0, 0};
  B operator^(const B& o) const { B r; for (int i = 0; i < W; i++) r.w[i] = w[i] ^ o.w[i]; return r; }
  B operator&(const B& o) const { B r; for (int i = 0; i < W; i++) r.w[i] = w[i] & o.w[i]; return r; }
  bool zero() const { return !(w[0] | w[1] | w[2]); }
  int top() const { for (int i = W - 1; i >= 0; i--) if (w[i]) return 64 * i + 63 - __builtin_clzll(w[i]); return -1; }
  bool bit(int i) const { return w[i >> 6] >> (i & 63) & 1; }
  void set(int i) { w[i >> 6] |= 1ULL << (i & 63); }
};
static inline int par(const B& a, const B& b) {
  return (__builtin_popcountll(a.w[0] & b.w[0]) ^ __builtin_popcountll(a.w[1] & b.w[1]) ^ __builtin_popcountll(a.w[2] & b.w[2])) & 1;
}
static int ny;
struct Ech {
  std::vector<B> piv; std::vector<char> has; int n = 0;
  Ech() : piv(192), has(192, 0) {}
  B reduce(B v) const { for (;;) { int h = v.top(); if (h < 0 || !has[h]) return v; v = v ^ piv[h]; } }
  bool add(B v) { v = reduce(v); int h = v.top(); if (h < 0) return false; piv[h] = v; has[h] = 1; n++; return true; }
};
static std::vector<B> annih(const std::vector<B>& vs) {
  Ech e; for (auto& v : vs) e.add(v);
  std::vector<B> piv = e.piv;
  for (int h = 0; h < ny; h++) if (e.has[h]) for (int h2 = 0; h2 < ny; h2++) if (h2 != h && e.has[h2] && piv[h2].bit(h)) piv[h2] = piv[h2] ^ piv[h];
  std::vector<B> out;
  for (int f = 0; f < ny; f++) if (!e.has[f]) { B v; v.set(f); for (int h = 0; h < ny; h++) if (e.has[h] && piv[h].bit(f)) v.set(h); out.push_back(v); }
  return out;
}
static B readB() { unsigned long long a, b, c; if (scanf("%llu %llu %llu", &a, &b, &c) != 3) exit(2); B x; x.w[0] = a; x.w[1] = b; x.w[2] = c; return x; }
struct Prod { u128 u, v; };

static const char* PROG = 0;
static void prog(const char* fmt, double a, double b, double c) { if (!PROG) return; FILE* f = fopen(PROG, "a"); if (f) { fprintf(f, fmt, a, b, c); fclose(f); } }
static std::vector<B> C;       // real basis functions (free + products)
static Ech Ce;                 // independence space: C plus delta vectors
static const int NTH = 3;

static B comb(u128 um) { B u; for (size_t j = 0; j < C.size(); j++) if ((um >> j) & 1) u = u ^ C[j]; return u; }

// given u (as coefficient mask) find v with u&v satisfying all functionals and independent
static bool solve_v(const std::vector<B>& ann, u128 um, std::mt19937_64& R, B& outf, u128& vout) {
  int m = C.size(); B u = comb(um);
  if (u.zero()) return false;
  std::vector<u128> cl(m);
  int na = ann.size();
  std::vector<u64> col0(m, 0), col1(m, 0);
  for (int j = 0; j < m; j++) { B f = u & C[j]; for (int k = 0; k < na; k++) if (par(ann[k], f)) { if (k < 64) col0[j] |= 1ULL << k; else col1[j] |= 1ULL << (k - 64); } }
  u64 p0[192], p1[192]; u128 pc[192]; unsigned char has[192] = {0};
  std::vector<u128> null;
  for (int j = 0; j < m; j++) {
    u64 a = col0[j], b = col1[j]; u128 c = ((u128)1) << j;
    for (;;) {
      int h = b ? 127 - __builtin_clzll(b) : (a ? 63 - __builtin_clzll(a) : -1);
      if (h < 0) { null.push_back(c); break; }
      if (!has[h]) { has[h] = 1; p0[h] = a; p1[h] = b; pc[h] = c; break; }
      a ^= p0[h]; b ^= p1[h]; c ^= pc[h];
    }
  }
  if (null.size() <= 2) return false;
  for (int tries = 0; tries < 64; tries++) {
    u128 vm = 0; for (auto& n : null) if (R() & 1) vm ^= n;
    B v = comb(vm); B f = u & v;
    if (f.zero()) continue;
    if (Ce.reduce(f).zero()) continue;
    bool ok = true; for (auto& a : ann) if (par(a, f)) { ok = false; break; }
    if (!ok) continue;
    outf = f; vout = vm; return true;
  }
  return false;
}

// plain random search (used when solutions are plentiful)
static long search_plain(const std::vector<B>& ann, B& outf, Prod& outp, std::mt19937_64& R) {
  int m = C.size(); long t = 0;
  while (true) {
    u128 um = ((u128)R() << 64) | R(); um &= (((u128)1) << m) - 1;
    t++;
    B f; u128 vm;
    if (solve_v(ann, um, R, f, vm)) { outf = f; outp = {um, vm}; return t; }
    if (t > 200000) return -1;
  }
}

// bit-sliced search, 256 lanes, m <= 64
#define CS 64
template <int R>
__attribute__((noinline)) static void batch_nullity(__m256i* __restrict M, int m, __m256i* __restrict S) {
  const __m256i ones = _mm256_set1_epi64x(-1);
  __m256i* used = S; __m256i* sel = S + 64; __m256i* elim = S + 128;    // heap scratch: aligned (stack AVX arrays are not safe on Win64 GCC)
  for (int r = 0; r < R; r++) used[r] = _mm256_setzero_si256();
  __m256i d1 = _mm256_setzero_si256(), d2 = _mm256_setzero_si256();
  for (int c = 1; c < m; c++) {
    __m256i* Mc = M + c * CS;
    __m256i found = _mm256_setzero_si256();
#pragma GCC unroll 64
    for (int r = 0; r < R; r++) {
      __m256i x = Mc[r];
      __m256i s = _mm256_andnot_si256(_mm256_or_si256(used[r], found), x);
      sel[r] = s; found = _mm256_or_si256(found, s); elim[r] = _mm256_andnot_si256(s, x); used[r] = _mm256_or_si256(used[r], s);
    }
    __m256i nopiv = _mm256_andnot_si256(found, ones);
    d2 = _mm256_or_si256(d2, _mm256_and_si256(d1, nopiv)); d1 = _mm256_or_si256(d1, nopiv);
    for (int k = c + 1; k < m; k++) {
      __m256i* Mk = M + k * CS;
      __m256i P = _mm256_setzero_si256();
#pragma GCC unroll 64
      for (int r = 0; r < R; r++) P = _mm256_or_si256(P, _mm256_and_si256(sel[r], Mk[r]));
#pragma GCC unroll 64
      for (int r = 0; r < R; r++) Mk[r] = _mm256_xor_si256(Mk[r], _mm256_and_si256(elim[r], P));
    }
  }
  _mm256_store_si256(S + 192, d2);
}

typedef void (*BatchFn)(__m256i*, int, __m256i*);
static BatchFn pick(int R) {
  switch (R) {
    case 36: return batch_nullity<36>; case 38: return batch_nullity<38>; case 40: return batch_nullity<40>;
    case 42: return batch_nullity<42>; case 44: return batch_nullity<44>; case 46: return batch_nullity<46>;
    case 48: return batch_nullity<48>; case 50: return batch_nullity<50>; case 52: return batch_nullity<52>;
    case 54: return batch_nullity<54>; case 56: return batch_nullity<56>; case 58: return batch_nullity<58>;
    case 60: return batch_nullity<60>; case 62: return batch_nullity<62>; case 64: return batch_nullity<64>;
    default: return 0;
  }
}

static int NTHREADS = 3;
static int RADD = 10;

static long search_bs(const std::vector<B>& ann, B& outf, Prod& outp, u64 seed, double limit_s, const std::vector<B>& skip) {
  const int m = C.size();
  const int na = ann.size();
  int R = m + RADD; if (R > na) R = na; if (R > 64) R = 64; if (R & 1) R++; if (R > na) R -= 2; if (R < 36) R = 36;
  BatchFn fn = pick(R);
  if (!fn || R > na) { fprintf(stderr, "no kernel for R=%d na=%d\n", R, na); exit(9); }
  static u64 T[64][64];
  for (int j = 0; j < m; j++) for (int c = 0; c < m; c++) { B f = C[j] & C[c]; u64 x = 0; for (int r = 0; r < R; r++) x |= (u64)par(ann[r], f) << r; T[j][c] = x; }
  const int nlo = (m - 1 < 8) ? m - 1 : 8;
  __m256i* Lo = (__m256i*)_mm_malloc((size_t)64 * CS * sizeof(__m256i), 64);
  for (int c = 1; c < m; c++) for (int r = 0; r < R; r++) {
    alignas(32) u64 w[4] = {0, 0, 0, 0};
    for (int l = 0; l < 256; l++) { u64 b = 0; for (int j = 0; j < nlo; j++) if (l >> j & 1) b ^= (T[1 + j][c] >> r) & 1; w[l >> 6] |= b << (l & 63); }
    Lo[c * CS + r] = _mm256_loadu_si256((__m256i*)w);
  }
  std::atomic<bool> done(false);
  std::atomic<long> batches(0);
  std::mutex mu;
  auto t0 = std::chrono::steady_clock::now();
  std::vector<std::thread> th;
  const int nhi = m - 1 - nlo;
  const u64 space = nhi >= 40 ? (1ULL << 40) : (1ULL << nhi);
  std::atomic<u64> next(0);
  std::mt19937_64 so(seed ^ 0x9E3779B97F4A7C15ULL);
  const u64 offset = so() & (space - 1);
  const u64 CHUNK = 256;
  for (int t = 0; t < NTHREADS; t++) th.emplace_back([&, t]() {
    std::mt19937_64 rng(seed + 7919 * t + 13);
    __m256i* M = (__m256i*)_mm_malloc((size_t)64 * CS * sizeof(__m256i), 64);
    __m256i* S = (__m256i*)_mm_malloc(200 * sizeof(__m256i), 64);
    long local = 0;
    u64 cur = 0, end = 0;
    u64 Hi[64]; u64 prevuh = ~0ULL;
    while (!done.load(std::memory_order_relaxed)) {
      if (cur == end) { cur = next.fetch_add(CHUNK); end = cur + CHUNK; if (cur >= space) break; }
      u64 uh = (offset ^ cur) & (space - 1); cur++;
      if (prevuh == ~0ULL) { for (int c = 1; c < m; c++) { u64 h = 0; u64 q = uh; while (q) { int j = __builtin_ctzll(q); q &= q - 1; h ^= T[1 + nlo + j][c]; } Hi[c] = h; } }
      else { u64 q = uh ^ prevuh; while (q) { int j = __builtin_ctzll(q); q &= q - 1; for (int c = 1; c < m; c++) Hi[c] ^= T[1 + nlo + j][c]; } }
      prevuh = uh;
      for (int c = 1; c < m; c++) { const __m256i* L = Lo + c * CS; __m256i* Mc = M + c * CS; u64 h = Hi[c];
        for (int r = 0; r < R; r++) Mc[r] = _mm256_xor_si256(L[r], _mm256_set1_epi64x(-(long long)((h >> r) & 1))); }
      fn(M, m, S);
      local++;
      const u64* d2w = (const u64*)(S + 192);
      if (d2w[0] | d2w[1] | d2w[2] | d2w[3]) {
        u64 w[4] = {d2w[0], d2w[1], d2w[2], d2w[3]};
        for (int word = 0; word < 4 && !done; word++) {
          u64 q = w[word];
          while (q) {
            int l = 64 * word + __builtin_ctzll(q); q &= q - 1;
            u128 um = ((u128)uh << (1 + nlo)) | ((u128)l << 1);
            if (uh == 0 && l == 0) continue;
            B f; u128 vm;
            std::mt19937_64 R2(rng());
            if (solve_v(ann, um, R2, f, vm)) {
              bool old = false;     // a product already tried at this level (modulo the current span)
              for (auto& t : skip) if (Ce.reduce(f ^ t).zero()) { old = true; break; }
              if (old) continue;
              std::lock_guard<std::mutex> g(mu);
              if (!done) { done = true; outf = f; outp = {um, vm}; }
              break;
            }
          }
        }
      }
      if ((local & 255) == 0) {
        batches += 256;
        if (limit_s > 0 && std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count() > limit_s) done = true;
      }
    }
    batches += (local & 255);
    _mm_free(M);
    _mm_free(S);
  });
  for (auto& x : th) x.join();
  _mm_free(Lo);
  if (outf.zero()) return -1;
  return batches.load() * 256;
}

int main(int argc, char** argv) {
  int nfree, nann, nE, cap, p, nfc;
  if (scanf("%d %d %d %d %d %d %d", &ny, &nfree, &nann, &nE, &cap, &p, &nfc) != 7) return 1;
  u64 seed = argc > 1 ? strtoull(argv[1], 0, 10) : 1;
  double limit = argc > 2 ? atof(argv[2]) : 0;
  PROG = argc > 3 ? argv[3] : 0;
  if (argc > 4) NTHREADS = atoi(argv[4]);
  if (argc > 5) RADD = atoi(argv[5]);
  for (int i = 0; i < nfree; i++) C.push_back(readB());
  std::vector<B> annH; for (int i = 0; i < nann; i++) annH.push_back(readB());
  std::vector<B> E; for (int i = 0; i < nE; i++) E.push_back(readB());
  std::vector<B> delta; for (int i = 0; i < nfc; i++) { int y; if (scanf("%d", &y) != 1) return 2; B v; v.set(y); delta.push_back(v); }
  for (auto& d : delta) Ce.add(d);
  for (auto& v : C) if (!Ce.add(v)) { fprintf(stderr, "free basis dependent mod delta\n"); return 3; }
  std::vector<Prod> prods;
  std::mt19937_64 R(seed * 1000003 + 5);
  auto push = [&](const B& f, const Prod& pr) { if (!Ce.add(f)) { fprintf(stderr, "dependent?!\n"); exit(4); } C.push_back(f); prods.push_back(pr); };
  for (int i = 0; i < p; i++) { B f; Prod pr; long tr = search_plain(annH, f, pr, R); if (tr < 0) { fprintf(stderr, "stage A failed\n"); return 6; } push(f, pr); }
  fprintf(stderr, "stage A: %d products\n", p);
  // T = span(delta, C, E, padding in H)
  Ech Te; std::vector<B> Tv;
  for (auto& d : delta) { Te.add(d); Tv.push_back(d); }
  for (auto& v : C) { Te.add(v); Tv.push_back(v); }
  for (auto& v : E) if (Te.add(v)) Tv.push_back(v);
  int target = cap + nfc;
  if (Te.n > target) { fprintf(stderr, "T too large %d > %d\n", Te.n, target); return 5; }
  { std::vector<B> hb = annih(annH); std::mt19937_64 Rp(seed + 5);
    while (Te.n < target) { B v; for (auto& x : hb) if (Rp() & 1) v = v ^ x; if (Te.add(v)) Tv.push_back(v); } }
  std::vector<B> annT = annih(Tv);
  fprintf(stderr, "T dim %d (incl %d delta), annihilator K=%zu, m=%zu\n", Te.n, nfc, annT.size(), C.size());
  auto t0 = std::chrono::steady_clock::now();
  const int m0 = C.size();
  std::vector<std::vector<B>> tried(cap + 1);
  std::vector<int> backs(cap + 1, 0);
  while ((int)C.size() < cap) {
    const int m = C.size();
    B f; Prod pr; long tr;
    if (m <= 63 && (int)annT.size() - m >= 8) {
      double lim = limit;       // per level: about 2.5 times the expected time, halving per level
      if (limit > 0) { lim = limit / (double)(1 << std::min(10, m - m0)); if (lim < 45) lim = 45; }
      tr = search_bs(annT, f, pr, R(), lim, tried[m]);
      if (tr < 0) {
        fprintf(stderr, "stage B: no solution found within limit at m=%d\n", m);
        if (m > m0 && ++backs[m - 1] <= 4) {      // backtrack: choose another product at the previous level
          tried[m].clear();
          C.pop_back(); prods.pop_back();
          Ce = Ech(); for (auto& d : delta) Ce.add(d); for (auto& v : C) Ce.add(v);
          prog("  backtrack to m=%.0f (%.0f, %.0fs)\n", (double)C.size(), (double)backs[m - 1], std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
          continue;
        }
        return 7;
      }
    } else {
      tr = search_plain(annT, f, pr, R);
      if (tr < 0) { fprintf(stderr, "stage B plain failed at m=%zu\n", C.size()); return 8; }
    }
    tried[m].push_back(f);
    push(f, pr);
    prog("  reached m=%.0f (trials %.3g, %.0fs)\n", (double)C.size(), (double)tr, std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
    if (C.size() % 8 == 0 || tr > 2000000) fprintf(stderr, "  stage B m=%zu (last trials %ld, %.0fs)\n", C.size(), tr, std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
  }
  fprintf(stderr, "phase1 done in %.0fs\n", std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
  printf("%zu\n", prods.size());
  for (auto& pr : prods) printf("%llu %llu %llu %llu\n", (unsigned long long)(u64)pr.u, (unsigned long long)(u64)(pr.u >> 64), (unsigned long long)(u64)pr.v, (unsigned long long)(u64)(pr.v >> 64));
  return 0;
}

// Local search over annihilator designs (dim d) for covers of a loader target with (210 - d)/2 chips.
// Input: nperp, then nperp lines "lo hi top mid" = 210-bit Psi (bit o*7+m), 4 x 64-bit words.
// A design is a list of items (kind, u, v, size): kind 0 = random elements of {Psi: Psi u = 0},
// kind 1 = of {Psi: Psi u = 0 and Psi v = 0}.  Score = matroid parity number of (sampled) chip pool.
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <random>
#include <algorithm>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cstring>
typedef uint64_t u64;
static const int NO = 30, NX = 7, NB = 210;
struct Psi { u64 w[4] = {0, 0, 0, 0}; void x(const Psi& o) { for (int i = 0; i < 4; i++) w[i] ^= o.w[i]; } };
static inline int bit(const Psi& p, int i) { return p.w[i >> 6] >> (i & 63) & 1; }
// Psi u -> 30-bit vector
static inline uint32_t psi_u(const Psi& p, int u) {
  uint32_t out = 0;
  for (int o = 0; o < NO; o++) {
    int base = o * NX; unsigned row = (unsigned)((p.w[base >> 6] >> (base & 63)));
    if ((base & 63) > 57) row |= (unsigned)(p.w[(base >> 6) + 1] << (64 - (base & 63)));
    out |= (uint32_t)(__builtin_popcount(row & u & 127) & 1) << o;
  }
  return out;
}
// GF(2) nullspace of rows over n<=64 vars
static std::vector<u64> nullsp(const std::vector<u64>& rows, int n) {
  u64 piv[64]; u64 has = 0;
  for (u64 r : rows) { while (r) { int h = 63 - __builtin_clzll(r); if (!(has >> h & 1)) { has |= 1ULL << h; piv[h] = r; break; } r ^= piv[h]; } }
  for (int h = 0; h < n; h++) if (has >> h & 1) for (int h2 = 0; h2 < n; h2++) if (h2 != h && (has >> h2 & 1) && (piv[h2] >> h & 1)) piv[h2] ^= piv[h];
  std::vector<u64> out;
  for (int f = 0; f < n; f++) if (!(has >> f & 1)) { u64 v = 1ULL << f; for (int h = 0; h < n; h++) if ((has >> h & 1) && (piv[h] >> f & 1)) v |= 1ULL << h; out.push_back(v); }
  return out;
}
static uint16_t EXPT[4 * 65536]; static int LOGT[65536];
static void gf_init() {
  unsigned x = 1;
  for (int i = 0; i < 65535; i++) { EXPT[i] = (uint16_t)x; LOGT[x] = i; x <<= 1; if (x & 0x10000) x ^= 0x1002D; }
  for (int i = 65535; i < 2 * 65535; i++) EXPT[i] = EXPT[i - 65535];
}
static int rank_gf(std::vector<uint16_t>& M, int n) {
  int r = 0;
  for (int c = 0; c < n && r < n; c++) {
    int p = -1; for (int i = r; i < n; i++) if (M[i * n + c]) { p = i; break; }
    if (p < 0) continue;
    if (p != r) for (int k = c; k < n; k++) std::swap(M[p * n + k], M[r * n + k]);
    int inv = 65535 - LOGT[M[r * n + c]];
    for (int k = c; k < n; k++) if (M[r * n + k]) M[r * n + k] = EXPT[LOGT[M[r * n + k]] + inv];
    for (int i = r + 1; i < n; i++) {
      uint16_t f = M[i * n + c]; if (!f) continue; int lf = LOGT[f];
      uint16_t* Mi = &M[i * n]; const uint16_t* Mr = &M[r * n];
      for (int k = c; k < n; k++) if (Mr[k]) Mi[k] ^= EXPT[lf + LOGT[Mr[k]]];
    }
    r++;
  }
  return r;
}
struct Chip { uint32_t s; uint8_t u1, u2; };
static void chip_vec(uint32_t s, int u, int* idx, int& n) { n = 0; while (s) { int o = __builtin_ctz(s); s &= s - 1; int q = u; while (q) { int m = __builtin_ctz(q); q &= q - 1; idx[n++] = o * NX + m; } } }
static int parity_number(const std::vector<Chip>& chips, std::mt19937_64& rng) {
  std::vector<uint16_t> M(NB * NB, 0);
  int a[256], b[256], na, nb;
  for (auto& c : chips) {
    uint16_t x = (uint16_t)(rng() % 65535 + 1);
    chip_vec(c.s, c.u1, a, na); chip_vec(c.s, c.u2, b, nb);
    for (int i = 0; i < na; i++) for (int j = 0; j < nb; j++) { M[a[i] * NB + b[j]] ^= x; M[b[j] * NB + a[i]] ^= x; }
  }
  return rank_gf(M, NB) / 2;
}
static std::vector<Psi> PERP;
static std::vector<Psi> kernel_of(int u, int v) {  // basis of {Psi in span(PERP): Psi u = 0 (and Psi v = 0)}
  int m = PERP.size();
  std::vector<u64> rows;
  std::vector<uint32_t> iu(m), iv(m);
  for (int a = 0; a < m; a++) { iu[a] = psi_u(PERP[a], u); iv[a] = v ? psi_u(PERP[a], v) : 0; }
  for (int o = 0; o < NO; o++) { u64 r1 = 0, r2 = 0; for (int a = 0; a < m; a++) { r1 |= (u64)((iu[a] >> o) & 1) << a; r2 |= (u64)((iv[a] >> o) & 1) << a; } rows.push_back(r1); if (v) rows.push_back(r2); }
  auto ns = nullsp(rows, m);  // m = 67 > 64 handled by caller
  std::vector<Psi> out;
  for (u64 c : ns) { Psi w; for (int a = 0; a < m; a++) if (c >> a & 1) w.x(PERP[a]); out.push_back(w); }
  return out;
}
// nullspace for up to 128 variables
static std::vector<std::pair<u64, u64>> nullsp128(const std::vector<std::pair<u64, u64>>& rows, int n) {
  std::pair<u64, u64> piv[128]; bool has[128] = {0};
  auto top = [](const std::pair<u64, u64>& r) { return r.second ? 127 - __builtin_clzll(r.second) : (r.first ? 63 - __builtin_clzll(r.first) : -1); };
  auto bit2 = [](const std::pair<u64, u64>& r, int h) { return h < 64 ? (r.first >> h & 1) : (r.second >> (h - 64) & 1); };
  for (auto r : rows) { for (;;) { int h = top(r); if (h < 0) break; if (!has[h]) { has[h] = 1; piv[h] = r; break; } r.first ^= piv[h].first; r.second ^= piv[h].second; } }
  for (int h = 0; h < n; h++) if (has[h]) for (int h2 = 0; h2 < n; h2++) if (h2 != h && has[h2] && bit2(piv[h2], h)) { piv[h2].first ^= piv[h].first; piv[h2].second ^= piv[h].second; }
  std::vector<std::pair<u64, u64>> out;
  for (int f = 0; f < n; f++) if (!has[f]) { std::pair<u64, u64> v(0, 0); auto set = [&](int h) { if (h < 64) v.first |= 1ULL << h; else v.second |= 1ULL << (h - 64); }; set(f); for (int h = 0; h < n; h++) if (has[h] && bit2(piv[h], f)) set(h); out.push_back(v); }
  return out;
}
static std::vector<Psi> kernel128(int u, int v) {
  int m = PERP.size();
  std::vector<uint32_t> iu(m), iv(m);
  for (int a = 0; a < m; a++) { iu[a] = psi_u(PERP[a], u); iv[a] = v ? psi_u(PERP[a], v) : 0; }
  std::vector<std::pair<u64, u64>> rows;
  for (int o = 0; o < NO; o++) {
    std::pair<u64, u64> r1(0, 0), r2(0, 0);
    for (int a = 0; a < m; a++) { if (iu[a] >> o & 1) { if (a < 64) r1.first |= 1ULL << a; else r1.second |= 1ULL << (a - 64); } if (iv[a] >> o & 1) { if (a < 64) r2.first |= 1ULL << a; else r2.second |= 1ULL << (a - 64); } }
    rows.push_back(r1); if (v) rows.push_back(r2);
  }
  auto ns = nullsp128(rows, m);
  std::vector<Psi> out;
  for (auto& c : ns) { Psi w; for (int a = 0; a < m; a++) if (a < 64 ? (c.first >> a & 1) : (c.second >> (a - 64) & 1)) w.x(PERP[a]); out.push_back(w); }
  return out;
}
struct Item { int kind, u, v, size; };
static std::vector<std::vector<Psi>> KV(128);
static std::vector<std::vector<std::vector<Psi>>> KZ(128, std::vector<std::vector<Psi>>(128));
static bool independent_add(std::vector<Psi>& basis_piv, std::vector<char>& has, Psi v) {
  for (;;) {
    int h = -1; for (int i = 3; i >= 0; i--) if (v.w[i]) { h = 64 * i + 63 - __builtin_clzll(v.w[i]); break; }
    if (h < 0) return false;
    if (!has[h]) { has[h] = 1; basis_piv[h] = v; return true; }
    v.x(basis_piv[h]);
  }
}
int main(int argc, char** argv) {
  gf_init();
  int d = argc > 1 ? atoi(argv[1]) : 20;
  double seconds = argc > 2 ? atof(argv[2]) : 600;
  u64 seed = argc > 3 ? strtoull(argv[3], 0, 10) : 1;
  int nth = argc > 4 ? atoi(argv[4]) : 3;
  int need = (NB - d) / 2;
  int m; if (scanf("%d", &m) != 1) return 1;
  PERP.resize(m);
  for (auto& p : PERP) for (int i = 0; i < 4; i++) { unsigned long long x; if (scanf("%llu", &x) != 1) return 2; p.w[i] = x; }
  for (int u = 1; u < 128; u++) KV[u] = kernel128(u, 0);
  for (int u = 1; u < 128; u++) for (int v = u + 1; v < 128; v++) { KZ[u][v] = kernel128(u, v); KZ[v][u] = KZ[u][v]; }
  fprintf(stderr, "perp %d, kernel dims e.g. %zu %zu\n", m, KV[1].size(), KZ[1][2].size());
  std::vector<std::pair<int, int>> allU;
  for (int a = 1; a < 128; a++) for (int b = a + 1; b < 128; b++) if ((a ^ b) > b) allU.push_back({a, b});
  std::mutex mu; int gbest = 0; std::atomic<bool> found(false);
  auto t0 = std::chrono::steady_clock::now();
  auto worker = [&](int tid) {
    std::mt19937_64 R(seed * 7919 + tid * 104729 + 1);
    auto rnd = [&](int n) { return (int)(R() % n); };
    int units[7] = {1, 2, 4, 8, 16, 32, 64};
    auto rand_vec = [&](std::vector<int>& base) { if (R() % 10 < 6 && !base.empty()) { int a = base[rnd(base.size())]; if (R() & 1) a ^= base[rnd(base.size())]; return a ? a : units[rnd(7)]; } return 1 + rnd(127); };
    auto random_design = [&]() {
      std::vector<int> base; for (int i = 0; i < 4; i++) base.push_back(units[rnd(7)]);
      std::vector<Item> it; int left = d;
      while (left > 0) {
        if (R() % 100 < 40) { int u = rand_vec(base), v = rand_vec(base); while (v == u) v = rand_vec(base); int s = std::min(left, 4 + rnd(4)); it.push_back({1, u, v, s}); left -= s; }
        else { int s = std::min(left, 2 + rnd(5)); it.push_back({0, rand_vec(base), 0, s}); left -= s; }
      }
      return it;
    };
    auto mutate = [&](std::vector<Item> it) {
      std::vector<int> all; for (auto& x : it) { all.push_back(x.u); if (x.kind) all.push_back(x.v); }
      int t = rnd(100), i = rnd(it.size());
      if (t < 45) { if (it[i].kind == 0) it[i].u = rand_vec(all); else { if (R() & 1) it[i].u = rand_vec(all); int v = rand_vec(all); if (v != it[i].u) it[i].v = v; else it[i].v = it[i].u ^ (units[rnd(7)] == it[i].u ? 3 : units[rnd(7)]); if (it[i].v == 0 || it[i].v == it[i].u) it[i].v = (it[i].u % 127) + 1; } }
      else if (t < 70 && it.size() > 1) { int j = rnd(it.size()); if (i != j && it[i].size > 1) { it[i].size--; it[j].size++; } }
      else if (t < 85) { if (it[i].size >= 3) { int a = 1 + rnd(it[i].size - 1); it[i].size -= a; if (R() & 1) it.push_back({0, rand_vec(all), 0, a}); else { int u = rand_vec(all), v = rand_vec(all); if (u != v) it.push_back({1, u, v, a}); else it[i].size += a; } } }
      else if (it.size() > 2) { int j = rnd(it.size()); if (i != j) { it[j].size += it[i].size; it.erase(it.begin() + i); } }
      return it;
    };
    auto evaluate = [&](const std::vector<Item>& it, u64 aseed, std::vector<Chip>& chips, long& total) {
      std::mt19937_64 r(aseed);
      std::vector<Psi> A; std::vector<Psi> piv(256); std::vector<char> has(256, 0);
      for (auto& x : it) {
        const std::vector<Psi>& B = x.kind == 0 ? KV[x.u] : KZ[x.u][x.v];
        int got = 0;
        for (int tries = 0; got < x.size && tries < 40 && (int)A.size() < d; tries++) { Psi w; for (auto& p : B) if (r() & 1) w.x(p); if (independent_add(piv, has, w)) { A.push_back(w); got++; } }
      }
      for (int tries = 0; (int)A.size() < d && tries < 300; tries++) { Psi w; for (auto& p : PERP) if (r() & 1) w.x(p); if (independent_add(piv, has, w)) A.push_back(w); }
      std::vector<std::vector<uint32_t>> img(128, std::vector<uint32_t>(A.size()));
      for (int u = 1; u < 128; u++) for (size_t a = 0; a < A.size(); a++) img[u][a] = psi_u(A[a], u);
      std::vector<std::pair<int, std::vector<u64>>> pool; total = 0;
      for (size_t k = 0; k < allU.size(); k++) {
        auto U = allU[k];
        u64 piv30[30]; u64 hs = 0; int rank = 0;
        for (int pass = 0; pass < 2 && rank < 30; pass++) { int u = pass ? U.second : U.first; for (size_t a = 0; a < A.size() && rank < 30; a++) { u64 x = img[u][a]; while (x) { int h = 63 - __builtin_clzll(x); if (!(hs >> h & 1)) { hs |= 1ULL << h; piv30[h] = x; rank++; break; } x ^= piv30[h]; } } }
        if (rank >= 30) continue;
        std::vector<u64> rows; for (int h = 0; h < 30; h++) if (hs >> h & 1) rows.push_back(piv30[h]);
        auto ns = nullsp(rows, 30);
        total += (1L << std::min<size_t>(ns.size(), 20)) - 1;
        pool.push_back({(int)k, ns});
      }
      chips.clear();
      // per U enough random kernel elements to span the kernel (2t+4), exhaustive when small
      for (auto& pr : pool) { auto U = allU[pr.first]; int t = pr.second.size(); u64 cnt = (1ULL << std::min(t, 20)) - 1; u64 take = std::min<u64>(cnt, 2 * t + 4);
        for (u64 j = 0; j < take; j++) { u64 mask = cnt == take ? j + 1 : 1 + r() % cnt; u64 s = 0; for (int i = 0; i < t; i++) if (mask >> i & 1) s ^= pr.second[i]; if (s) chips.push_back({(uint32_t)s, (uint8_t)U.first, (uint8_t)U.second}); } }
      if (chips.size() > 4000) { std::shuffle(chips.begin(), chips.end(), r); chips.resize(4000); }
      if (chips.empty()) return 0;
      return parity_number(chips, r);
    };
    std::vector<Item> cur = random_design(); std::vector<Chip> chips; long total = 0;
    int cs = evaluate(cur, R(), chips, total); int since = 0; long n = 0;
    while (!found && std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count() < seconds) {
      n++;
      if (since > 600 || cs < 40) { cur = random_design(); cs = evaluate(cur, R(), chips, total); since = 0; continue; }
      std::vector<Item> cand = mutate(cur);
      u64 as = R();
      int s = evaluate(cand, as, chips, total);
      since++;
      if (s >= cs) { if (s > cs) since = 0; cur = cand; cs = s; }
      std::lock_guard<std::mutex> g(mu);
      if (s > gbest) {
        gbest = s;
        fprintf(stderr, "t%d n %ld nu %d pool-total %ld chips %zu seed %llu design", tid, n, s, total, chips.size(), (unsigned long long)as);
        for (auto& x : cand) fprintf(stderr, " (%d,%d,%d,%d)", x.kind, x.u, x.v, x.size);
        fprintf(stderr, " (%.0fs)\n", std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
        fflush(stderr);
      }
      if (s >= need) {
        found = true;
        printf("FOUND %llu %zu\n", (unsigned long long)as, cand.size());
        for (auto& x : cand) printf("%d %d %d %d\n", x.kind, x.u, x.v, x.size);
        printf("%zu\n", chips.size());
        for (auto& c : chips) printf("%u %d %d\n", c.s, c.u1, c.u2);
      }
    }
  };
  std::vector<std::thread> th;
  for (int t = 0; t < nth; t++) th.emplace_back(worker, t);
  for (auto& x : th) x.join();
  fprintf(stderr, "best nu %d of %d\n", gbest, need);
  return 0;
}

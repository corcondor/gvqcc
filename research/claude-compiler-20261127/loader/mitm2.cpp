// Two five-care columns: enumerate every orbit state that satisfies one column (meet-in-the-middle on its 30
// bits), then test all candidates of another column at once.  Same stdin as mitm.cpp.
// Elements of a group with identical contributions for every column and candidate are merged first.
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <functional>
#include <thread>
#include <atomic>
#include <chrono>
#include <algorithm>
#include <map>
#include <cmath>
#include <cstdlib>
typedef uint64_t u64;
typedef uint32_t u32;

struct Chip { u64 a[3], b[3]; u32 s; };

static std::vector<std::vector<u32>> gl(int m) {
    std::vector<std::vector<u32>> out;
    std::vector<u32> rows(m);
    std::function<void(int, std::vector<u32>&)> rec = [&](int r, std::vector<u32>& span) {
        if (r == m) { out.push_back(rows); return; }
        for (u32 v = 1; v < (1u << m); v++) {
            if (std::find(span.begin(), span.end(), v) != span.end()) continue;
            rows[r] = v;
            std::vector<u32> s2 = span;
            for (u32 x : span) s2.push_back(x ^ v);
            rec(r + 1, s2);
        }
    };
    std::vector<u32> span{0};
    rec(0, span);
    return out;
}
static std::vector<u32> inverse_transpose(const std::vector<u32>& M) {
    const int m = M.size();
    std::vector<u32> A = M, I(m);
    for (int i = 0; i < m; i++) I[i] = 1u << i;
    for (int c = 0; c < m; c++) {
        int p = c;
        while (!((A[p] >> c) & 1)) p++;
        std::swap(A[p], A[c]);
        std::swap(I[p], I[c]);
        for (int r = 0; r < m; r++)
            if (r != c && ((A[r] >> c) & 1)) { A[r] ^= A[c]; I[r] ^= I[c]; }
    }
    std::vector<u32> T(m, 0);
    for (int i = 0; i < m; i++)
        for (int j = 0; j < m; j++)
            if ((I[j] >> i) & 1) T[i] |= 1u << j;
    return T;
}
static inline int par3(const u64* x, const u64* S) {
    return __builtin_parityll((x[0] & S[0]) ^ (x[1] & S[1]) ^ (x[2] & S[2]));
}

int main() {
    int ng, ncol, nc;
    if (scanf("%d %d %d", &ng, &ncol, &nc) != 3) return 2;
    auto rd = [&]() { unsigned long long x; if (scanf("%llu", &x) != 1) exit(2); return (u64)x; };
    std::vector<std::vector<Chip>> groups(ng);
    for (auto& g : groups) {
        g.resize(rd());
        for (auto& c : g) {
            for (int k = 0; k < 3; k++) c.a[k] = rd();
            for (int k = 0; k < 3; k++) c.b[k] = rd();
            c.s = rd();
        }
    }
    std::vector<std::vector<u64>> S(ncol, std::vector<u64>(3 * nc));
    std::vector<std::vector<u32>> base(ncol, std::vector<u32>(nc));
    for (int y = 0; y < ncol; y++)
        for (int c = 0; c < nc; c++) {
            for (int k = 0; k < 3; k++) S[y][3 * c + k] = rd();
            base[y][c] = rd();
        }
    double limit = rd();
    rd();
    int nth = rd();
    auto t0 = std::chrono::steady_clock::now();
    auto secs = [&]() { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };

    struct Elem { std::vector<u32> v; std::vector<u32> IT; };
    std::vector<std::vector<Elem>> E(ng);
    std::vector<Elem> idelem(ng);
    std::vector<std::vector<u32>> T = base;
    for (int g = 0; g < ng; g++) {
        const int m = groups[g].size();
        std::map<std::vector<u32>, int> seen;
        for (const auto& M : gl(m)) {
            auto IT = inverse_transpose(M);
            std::vector<u32> v((size_t)ncol * nc, 0);
            for (int i = 0; i < m; i++) {
                u64 a[3] = {0, 0, 0}, b[3] = {0, 0, 0};
                u32 s = 0;
                for (int j = 0; j < m; j++) {
                    if ((M[i] >> j) & 1)
                        for (int k = 0; k < 3; k++) { a[k] ^= groups[g][j].a[k]; b[k] ^= groups[g][j].b[k]; }
                    if ((IT[i] >> j) & 1) s ^= groups[g][j].s;
                }
                u64 ab[3] = {a[0] & b[0], a[1] & b[1], a[2] & b[2]};
                for (int y = 0; y < ncol; y++)
                    for (int c = 0; c < nc; c++) {
                        const u64* Sc = &S[y][3 * c];
                        if ((par3(a, Sc) & par3(b, Sc)) ^ par3(ab, Sc)) v[(size_t)y * nc + c] ^= s;
                    }
            }
            bool isid = true;
            for (int i = 0; i < m; i++) isid &= M[i] == (1u << i);
            if (isid) idelem[g] = {v, IT};
            if (isid)
                for (int y = 0; y < ncol; y++)
                    for (int c = 0; c < nc; c++) T[y][c] ^= v[(size_t)y * nc + c];
            if (!seen.count(v)) {
                seen[v] = E[g].size();
                E[g].push_back({v, IT});
            }
        }
    }
    // vary only as many groups (largest first) as needed for an orbit of about 2^TARGET; the others stay fixed
    {
        const double target = getenv("ORBIT") ? atof(getenv("ORBIT")) : 44.0;
        std::vector<int> by(ng);
        for (int g = 0; g < ng; g++) by[g] = g;
        std::sort(by.begin(), by.end(), [&](int a, int b) { return E[a].size() > E[b].size(); });
        double lg = 0;
        for (int g : by) {
            const double l = log2((double)E[g].size());
            if (lg + l <= target + 0.5) { lg += l; continue; }
            std::vector<Elem> keep{idelem[g]};
            E[g] = keep;
        }
    }
    // bit slices of every element for the all-candidate test
    const int W = (nc + 63) / 64;
    std::vector<std::vector<std::vector<u64>>> slices(ng);
    for (int g = 0; g < ng; g++) {
        slices[g].resize(E[g].size());
        for (size_t e = 0; e < E[g].size(); e++) {
            auto& sl = slices[g][e];
            sl.assign((size_t)ncol * 30 * W, 0);
            for (int y = 0; y < ncol; y++)
                for (int c = 0; c < nc; c++)
                    for (u32 v = E[g][e].v[(size_t)y * nc + c]; v; v &= v - 1)
                        sl[((size_t)y * 30 + __builtin_ctz(v)) * W + c / 64] |= 1ULL << (c % 64);
        }
    }
    std::vector<u64> Tsl((size_t)ncol * 30 * W, 0), lastmask(W, ~0ULL);
    if (nc % 64) lastmask[W - 1] = (1ULL << (nc % 64)) - 1;
    for (int y = 0; y < ncol; y++)
        for (int c = 0; c < nc; c++)
            for (u32 v = T[y][c]; v; v &= v - 1) Tsl[((size_t)y * 30 + __builtin_ctz(v)) * W + c / 64] |= 1ULL << (c % 64);
    // split the groups into two halves with balanced products
    std::vector<int> ord(ng);
    for (int g = 0; g < ng; g++) ord[g] = g;
    std::sort(ord.begin(), ord.end(), [&](int a, int b) { return E[a].size() > E[b].size(); });
    std::vector<int> half[2];
    double prod[2] = {1, 1};
    for (int g : ord) {
        const int h = prod[0] <= prod[1] ? 0 : 1;
        half[h].push_back(g);
        prod[h] *= E[g].size();
    }
    fprintf(stderr, "orbit %.3g = %.0f x %.0f; states satisfying one candidate expected %.2f (%.0fs)\n", prod[0] * prod[1],
            prod[0], prod[1], prod[0] * prod[1] / 1073741824.0, secs());
    std::atomic<int> next(0);
    std::atomic<bool> found(false);
    std::atomic<long long> hits1(0);
    int fy1 = 0, fc1 = 0, fy2 = 0, fc2 = 0;
    std::vector<int> fchoice(ng);
    auto enumerate = [&](const std::vector<int>& gs, int y, int c, std::vector<std::pair<u32, u32>>& out) {
        out.assign(1, {0u, 0u});
        std::vector<std::pair<u32, u32>> nxt;
        u32 mult = 1;
        for (int g : gs) {
            const int ne = E[g].size();
            nxt.resize(out.size() * ne);
            size_t p = 0;
            for (int e = 0; e < ne; e++) {
                const u32 v = E[g][e].v[(size_t)y * nc + c];
                for (const auto& s : out) nxt[p++] = {s.first ^ v, s.second + e * mult};
            }
            out.swap(nxt);
            mult *= ne;
        }
    };
    auto work = [&]() {
        std::vector<std::pair<u32, u32>> A, B;
        std::vector<u32> head, link;
        std::vector<u64> O((size_t)30 * W);
        while (!found) {
            const int idx = next++;
            if (idx >= ncol * nc || secs() > limit) break;
            const int y1 = idx / nc, c1 = idx % nc;
            enumerate(half[0], y1, c1, A);
            enumerate(half[1], y1, c1, B);
            // hash A by value
            const int HB = 21;
            head.assign(1u << HB, ~0u);
            link.assign(A.size(), ~0u);
            auto hs = [&](u32 v) { return (v * 0x9E3779B1u) >> (32 - HB); };
            for (u32 i = 0; i < A.size(); i++) {
                const u32 h = hs(A[i].first);
                link[i] = head[h];
                head[h] = i;
            }
            for (const auto& b : B) {
                const u32 want = b.first ^ T[y1][c1];
                for (u32 i = head[hs(want)]; i != ~0u; i = link[i]) {
                    if (A[i].first != want) continue;
                    hits1++;
                    std::vector<int> choice(ng, 0);
                    u32 x = A[i].second;
                    for (int g : half[0]) { choice[g] = x % E[g].size(); x /= E[g].size(); }
                    x = b.second;
                    for (int g : half[1]) { choice[g] = x % E[g].size(); x /= E[g].size(); }
                    for (int y2 = 0; y2 < ncol; y2++) {
                        if (y2 == y1) continue;
                        std::copy(Tsl.begin() + (size_t)y2 * 30 * W, Tsl.begin() + (size_t)(y2 + 1) * 30 * W, O.begin());
                        for (int g = 0; g < ng; g++) {
                            const u64* sl = &slices[g][choice[g]][(size_t)y2 * 30 * W];
                            for (int k = 0; k < 30 * W; k++) O[k] ^= sl[k];
                        }
                        for (int w = 0; w < W; w++) {
                            u64 acc = 0;
                            for (int k = 0; k < 30; k++) acc |= O[(size_t)k * W + w];
                            const u64 z = lastmask[w] & ~acc;
                            if (z && !found.exchange(true)) {
                                fy1 = y1; fc1 = c1; fy2 = y2; fc2 = w * 64 + __builtin_ctzll(z);
                                fchoice = choice;
                            }
                        }
                    }
                }
            }
        }
    };
    std::vector<std::thread> th;
    for (int t = 0; t < nth; t++) th.emplace_back(work);
    for (auto& t : th) t.join();
    fprintf(stderr, "one-column states examined %lld (%.0fs)\n", (long long)hits1, secs());
    if (found) {
        printf("FOUND %d %d %d %d 0\n", fy1, fc1, fy2, fc2);
        for (int g = 0; g < ng; g++) {
            const int m = groups[g].size();
            const auto& IT = E[g][fchoice[g]].IT;
            for (int i = 0; i < m; i++) {
                u32 s = 0;
                for (int j = 0; j < m; j++)
                    if ((IT[i] >> j) & 1) s ^= groups[g][j].s;
                printf("%u ", s);
            }
            printf("\n");
        }
        return 0;
    }
    printf("NOTFOUND %d\n", (int)std::min<long long>(next.load(), (long long)ncol * nc));
    return 1;
}

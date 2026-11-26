// Beam search over the order of the chips after the window search, minimising the live dimension.
// Held after a set X of chips = rank(L0 + rows of X) + rank(rows of the others) - rank(L0 + all rows)
// (vectors already reduced modulo the always-live space).  Before chip i runs it needs held + (new dims of
// its two rows) <= cap.  Two segments keep the anchor-supporting chips last.
// stdin: nL nchips cap width nfirst ; nL vectors ; nchips pairs of vectors (3 u64 each)
// stdout: peak excess, then the order (indices 0..nchips-1)
#include <cstdio>
#include <cstdint>
#include <vector>
#include <algorithm>
#include <random>
#include <cstring>
typedef uint64_t u64;

struct V { u64 w[3]; };
static inline bool is0(const V& v) { return !(v.w[0] | v.w[1] | v.w[2]); }
static inline int top(const V& v) {
    if (v.w[2]) return 191 - __builtin_clzll(v.w[2]);
    if (v.w[1]) return 127 - __builtin_clzll(v.w[1]);
    return 63 - __builtin_clzll(v.w[0]);
}
struct Basis {
    std::vector<V> piv;
    std::vector<int> has;
    int n = 0;
    Basis() : piv(192), has(192, 0) {}
    bool add(V v) {
        while (!is0(v)) {
            int h = top(v);
            if (!has[h]) { has[h] = 1; piv[h] = v; n++; return true; }
            for (int k = 0; k < 3; k++) v.w[k] ^= piv[h].w[k];
        }
        return false;
    }
};

struct State {
    Basis C;
    std::vector<char> used;
    std::vector<int> order;
    int held = 0;
    int excess = 0;       // sum of overflow
    int peak = 0;
    double tie = 0;
};

int main() {
    int nL, n, cap, width, nfirst;
    if (scanf("%d %d %d %d %d", &nL, &n, &cap, &width, &nfirst) != 5) return 1;
    auto readv = []() {
        V v;
        unsigned long long a, b, c;
        if (scanf("%llu %llu %llu", &a, &b, &c) != 3) exit(2);
        v.w[0] = a; v.w[1] = b; v.w[2] = c;
        return v;
    };
    std::vector<V> L(nL), R(2 * n);
    for (auto& v : L) v = readv();
    for (auto& v : R) v = readv();
    Basis total;
    for (auto& v : L) total.add(v);
    for (auto& v : R) total.add(v);
    const int T = total.n;
    std::mt19937_64 rng(12345);
    auto rankN = [&](const std::vector<char>& used, int skip) {
        Basis N;
        for (int i = 0; i < n; i++)
            if (!used[i] && i != skip) { N.add(R[2 * i]); N.add(R[2 * i + 1]); }
        return N.n;
    };
    State s0;
    for (auto& v : L) s0.C.add(v);
    s0.used.assign(n, 0);
    s0.held = s0.C.n + rankN(s0.used, -1) - T;
    std::vector<State> beam{s0};
    for (int step = 0; step < n; step++) {
        std::vector<std::pair<std::pair<long long, double>, std::pair<int, int>>> cand;  // key, (state, chip)
        for (int b = 0; b < (int)beam.size(); b++) {
            const State& s = beam[b];
            int lo = 0, hi = n;
            int doneFirst = 0;
            for (int i = 0; i < nfirst; i++) doneFirst += s.used[i];
            if (doneFirst < nfirst) { lo = 0; hi = nfirst; } else { lo = nfirst; hi = n; }
            for (int i = lo; i < hi; i++) {
                if (s.used[i]) continue;
                Basis C2 = s.C;
                int need = C2.add(R[2 * i]) + C2.add(R[2 * i + 1]);
                std::vector<char> u2 = s.used;
                u2[i] = 1;
                int held2 = C2.n + rankN(u2, -1) - T;
                int before = s.held + need;
                int over = std::max(0, before - cap) + std::max(0, held2 - cap);
                long long key = (long long)(s.excess + over) * 1000000 + std::max({s.peak, before, held2}) * 1000 + held2;
                cand.push_back({{key, (double)(rng() % 1000000)}, {b, i}});
            }
        }
        std::sort(cand.begin(), cand.end());
        std::vector<State> next;
        std::vector<std::vector<char>> seen;
        for (auto& c : cand) {
            if ((int)next.size() >= width) break;
            const State& s = beam[c.second.first];
            int i = c.second.second;
            std::vector<char> u2 = s.used;
            u2[i] = 1;
            if (std::find(seen.begin(), seen.end(), u2) != seen.end()) continue;
            seen.push_back(u2);
            State t = s;
            int need = t.C.add(R[2 * i]) + t.C.add(R[2 * i + 1]);
            int before = s.held + need;
            t.used = u2;
            t.held = t.C.n + rankN(t.used, -1) - T;
            t.excess = s.excess + std::max(0, before - cap) + std::max(0, t.held - cap);
            t.peak = std::max({s.peak, before, t.held});
            t.order.push_back(i);
            next.push_back(std::move(t));
        }
        beam.swap(next);
        if (step % 10 == 0) fprintf(stderr, "step %d best excess %d peak %d (cap %d)\n", step, beam[0].excess, beam[0].peak, cap);
    }
    printf("%d %d\n", beam[0].excess, beam[0].peak);
    for (int i : beam[0].order) printf("%d ", i);
    printf("\n");
}

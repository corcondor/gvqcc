// One-CCZ representation search: is  v_e  in  F + l1*l2*l3  with affine l_i at one cut ?
//   v_e : value measured by the HMR at file index e (zero branch)
//   F   : span of {1, w_i, w_i w_j} over all top-level cuts in [tmin, tmax]
// usage: ccz ops.txt e tmin tmax W w1 w2 [maxhits] [statestep] [threads]
#include "lib.h"
#include <algorithm>

struct StateRec { int k; std::vector<int> wid; };  // wid[i] = value id of wire i (-1 unusable)

int main(int argc, char** argv) {
    if (argc < 8) { fprintf(stderr, "usage: ccz ops e tmin tmax W w1 w2 [maxhits] [step] [threads]\n"); return 2; }
    auto ops = load_ops(argv[1]);
    const int n = (int)ops.size();
    const int e = atoi(argv[2]);
    int tmin = atoi(argv[3]);
    if (tmin <= e) { tmin = e + 1; fprintf(stderr, "tmin raised to %d (after the measurement)\n", tmin); }
    const int tmax = std::min(n, atoi(argv[4]));
    const int W = atoi(argv[5]);
    const int w1 = atoi(argv[6]), w2 = atoi(argv[7]);
    const int maxhits = argc > 8 ? atoi(argv[8]) : 5;
    const int sstep = argc > 9 ? atoi(argv[9]) : 1;
    const int nth = argc > 10 ? atoi(argv[10]) : 2;
    auto xs = strat_samples(W, 99);

    // traces
    Trace z(ops, xs), r(ops, xs);
    std::vector<Vec> vals;                       // distinct wire values
    std::unordered_map<u64, std::vector<int>> vhash;
    auto intern = [&](const u64* p) {
        u64 h = 1469598103934665603ULL;
        for (int w = 0; w < W; w++) h = (h ^ p[w]) * 1099511628211ULL;
        for (int id : vhash[h]) if (!memcmp(vals[id].data(), p, 8 * W)) return id;
        vals.emplace_back(p, p + W); vhash[h].push_back((int)vals.size() - 1); return (int)vals.size() - 1;
    };
    std::vector<StateRec> states;
    Vec target;
    std::vector<int> prev;
    bool dirty = true;
    for (int k = 0; k <= n; k++) {
        if (k == e) {
            if (ops[k].op != HMR_) { fprintf(stderr, "op %d is not HMR\n", k); return 1; }
            target.assign(z.q(ops[k].a), z.q(ops[k].a) + W);
        }
        if (k >= tmin && k <= tmax && z.depth == 0 && dirty) {
            dirty = false;
            std::vector<int> id(NQ, -1);
            bool changed = prev.empty();
            for (int q = 0; q < NQ; q++) {
                const u64* a = z.q(q);
                bool nz = false; for (int w = 0; w < W; w++) if (a[w]) { nz = true; break; }
                bool dep = memcmp(a, r.q(q), 8 * W) != 0;
                if (nz && !dep) id[q] = intern(a);
            }
            if (changed || id != prev) { states.push_back({k, id}); prev = id; }
        }
        if (k == n) break;
        z.step(k, 0); r.step(k, 12345);
        if (ops[k].op == CCX_ || ops[k].op == CSWAP_ || ops[k].op == HMR_) dirty = true;
    }
    fprintf(stderr, "states %zu distinct wire values %zu\n", states.size(), vals.size());

    // F
    Basis B(W);
    Vec tmp(W);
    auto add = [&](const u64* v) {
        Vec x(v, v + W);
        int p = B.reduce(x.data(), nullptr);
        if (p >= 0) B.insert_reduced(x.data(), nullptr, p);
    };
    { Vec one(W, ~0ULL); add(one.data()); }
    std::vector<int> last(NQ, -1);
    std::unordered_set<u64> seenpair;
    std::unordered_set<int> seenval;
    for (size_t s = 0; s < states.size(); s++) {
        const auto& id = states[s].wid;
        // which wires got a value that is not a linear combination of earlier ones
        std::vector<int> fresh;
        if (s == 0) { for (int q = 0; q < NQ; q++) fresh.push_back(q); }
        else {
            for (int k = states[s - 1].k; k < states[s].k; k++) {
                if (ops[k].op == CCX_) fresh.push_back(ops[k].c);
                if (ops[k].op == CSWAP_) { fresh.push_back(ops[k].b); fresh.push_back(ops[k].c); }
            }
            for (int q = 0; q < NQ; q++) if (last[q] < 0 && id[q] >= 0) fresh.push_back(q);
            // wire values moved by CX/SWAP after the nonlinear op: follow them
            std::sort(fresh.begin(), fresh.end()); fresh.erase(std::unique(fresh.begin(), fresh.end()), fresh.end());
        }
        for (int q : fresh) {
            if (id[q] < 0 || !seenval.insert(id[q]).second) continue;
            add(vals[id[q]].data());
            for (int j = 0; j < NQ; j++) {
                if (j == q || id[j] < 0) continue;
                u64 a = std::min(id[q], id[j]), b = std::max(id[q], id[j]);
                if (!seenpair.insert(a * 1000003ULL + b).second) continue;
                for (int w = 0; w < W; w++) tmp[w] = vals[id[q]][w] & vals[id[j]][w];
                add(tmp.data());
            }
        }
        last = id;
        if (s % 500 == 0) fprintf(stderr, "state %zu rank %d\n", s, B.rank);
        if (B.rank > W * 64 - 160) { fprintf(stderr, "rank %d too close to sample count; increase W\n", B.rank); return 1; }
    }
    fprintf(stderr, "F rank %d of %d samples\n", B.rank, W * 64);
    {
        Vec x = target;
        int p = B.reduce(x.data(), nullptr);
        if (p < 0) { printf("TARGET IS FREE (in F)\n"); return 0; }
    }
    Annih A(B, 7);
    Sig sv = A.sig(target.data());
    printf("rank %d sig %llx %llx\n", B.rank, (unsigned long long)sv[0], (unsigned long long)sv[1]);
    if (iszero(sv)) { printf("signature zero\n"); return 0; }

    // constant id
    Vec one(W, ~0ULL);
    int one_id = intern(one.data());

    std::atomic<size_t> next(0);
    std::atomic<int> hits(0);
    std::mutex mu;
    auto worker = [&](int tid) {
        std::unordered_map<u64, Sig> cache;
        std::vector<Sig> T(38 * 38 * 38);
        std::vector<u64> prod(W), prod2(W);
        for (;;) {
            size_t s = next.fetch_add(sstep);
            if (s >= states.size() || hits.load() >= maxhits) break;
            const auto& id = states[s].wid;
            std::vector<int> g; std::vector<int> gq;
            g.push_back(one_id); gq.push_back(-1);
            for (int q = 0; q < NQ; q++) if (id[q] >= 0) { g.push_back(id[q]); gq.push_back(q); }
            int m = (int)g.size();
            std::fill(T.begin(), T.end(), Sig{0, 0});
            for (int i = 0; i < m; i++)
                for (int j = i + 1; j < m; j++) {
                    bool have = false;
                    for (int k = j + 1; k < m; k++) {
                        std::array<int, 3> t{g[i], g[j], g[k]};
                        std::sort(t.begin(), t.end());
                        u64 key = ((u64)t[0] << 42) | ((u64)t[1] << 21) | (u64)t[2];
                        auto it = cache.find(key);
                        Sig sg;
                        if (it != cache.end()) sg = it->second;
                        else {
                            if (!have) { for (int w = 0; w < W; w++) prod[w] = vals[g[i]][w] & vals[g[j]][w]; have = true; }
                            for (int w = 0; w < W; w++) prod2[w] = prod[w] & vals[g[k]][w];
                            sg = A.sig(prod2.data());
                            cache.emplace(key, sg);
                        }
                        int idx[3] = {i, j, k};
                        for (int a = 0; a < 3; a++) for (int b = 0; b < 3; b++) for (int c = 0; c < 3; c++)
                            if (a != b && b != c && a != c) T[(idx[a] * 38 + idx[b]) * 38 + idx[c]] = sg;
                    }
                }
            if (cache.size() > 3000000) cache.clear();
            // combos
            auto combos = [&](int wmax) {
                std::vector<u64> out;
                for (int i = 0; i < m; i++) out.push_back(1ULL << i);
                if (wmax >= 2) for (int i = 0; i < m; i++) for (int j = i + 1; j < m; j++) out.push_back((1ULL << i) | (1ULL << j));
                if (wmax >= 3) for (int i = 0; i < m; i++) for (int j = i + 1; j < m; j++) for (int k = j + 1; k < m; k++) out.push_back((1ULL << i) | (1ULL << j) | (1ULL << k));
                return out;
            };
            std::vector<u64> C1 = combos(w1), C2 = combos(w2);
            std::vector<Sig> Am((size_t)m * m);
            bool found = false;
            for (size_t a = 0; a < C1.size() && !found; a++) {
                u64 l1 = C1[a];
                std::fill(Am.begin(), Am.end(), Sig{0, 0});
                for (u64 t = l1; t; t &= t - 1) {
                    int i = __builtin_ctzll(t);
                    for (int j = 0; j < m; j++) for (int k = 0; k < m; k++) Am[j * m + k] = Am[j * m + k] ^ T[(i * 38 + j) * 38 + k];
                }
                size_t b0 = (w1 == w2) ? a + 1 : 0;
                for (size_t b = b0; b < C2.size(); b++) {
                    u64 l2 = C2[b];
                    Sig M[40];
                    int j0 = __builtin_ctzll(l2);
                    for (int k = 0; k < m; k++) M[k] = Am[j0 * m + k];
                    for (u64 t = l2 & (l2 - 1); t; t &= t - 1) {
                        int j = __builtin_ctzll(t);
                        for (int k = 0; k < m; k++) M[k] = M[k] ^ Am[j * m + k];
                    }
                    u64 l3;
                    if (solve128(M, m, sv, l3)) {
                        found = true;
                        std::lock_guard<std::mutex> lk(mu);
                        hits++;
                        printf("HIT state %zu op %d :", s, states[s].k);
                        for (u64 l : {l1, l2, l3}) {
                            printf(" [");
                            for (u64 t = l; t; t &= t - 1) { int i = __builtin_ctzll(t); if (gq[i] < 0) printf("1,"); else printf("q%d,", gq[i]); }
                            printf("]");
                        }
                        printf("\n"); fflush(stdout);
                        break;
                    }
                }
            }
            if (s % 100 == 0) fprintf(stderr, "searched state %zu (op %d) m=%d cache %zu\n", s, states[s].k, m, cache.size());
        }
    };
    std::vector<std::thread> th;
    for (int t = 0; t < nth; t++) th.emplace_back(worker, t);
    for (auto& t : th) t.join();
    printf("done hits %d\n", hits.load());
    return 0;
}

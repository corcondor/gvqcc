// Can a Toffoli be moved under a condition that is already known at that point (lazy evaluation)?
// For every Toffoli-class op k: skip it, compare the final data/phase/rotation with the reference
// (same inputs, same measurement coins), and keep every classical bit b (value at op k) such that
// all differing lanes have b = 1 (or all have b = 0).  Then op k is only needed under b.
// Also tries "b1 OR b2" over the recently written bits.  usage: sinktest ops.txt [words] [seed]
#include "qsim.h"
#include <random>
#include <cmath>

int main(int argc, char** argv) {
    auto ops = load_ops(argv[1]);
    const int W = argc > 2 ? atoi(argv[2]) : 64;
    const u64 seed = argc > 3 ? strtoull(argv[3], 0, 10) : 11;
    const int n = (int)ops.size();
    std::vector<int> tk;
    for (int k = 0; k < n; k++)
        if (ops[k].op == CCX_ || ops[k].op == CCZ_ || ops[k].op == CSWAP_) tk.push_back(k);
    const int T = (int)tk.size();
    int nb = 0;
    for (auto& I : ops) {
        if (I.cond >= 0) nb = std::max(nb, I.cond + 1);
        if (I.op == HMR_) nb = std::max(nb, I.b + 1);
        if (I.op == BINV_ || I.op == BST0_ || I.op == BST1_) nb = std::max(nb, I.a + 1);
    }
    // bits written before each Toffoli
    std::vector<int> written;           // order of first write
    std::vector<int> nwritten(T, 0);
    std::vector<std::vector<int>> recent(T);
    {
        std::vector<char> seen(nb, 0);
        std::vector<int> hist;
        int t = 0;
        for (int k = 0; k < n && t < T; k++) {
            if (k == tk[t]) {
                nwritten[t] = (int)written.size();
                std::vector<int> r;
                for (int j = (int)hist.size() - 1; j >= 0 && (int)r.size() < 24; j--)
                    if (std::find(r.begin(), r.end(), hist[j]) == r.end()) r.push_back(hist[j]);
                recent[t] = r;
                t++;
            }
            const Ins& I = ops[k];
            int b = -1;
            if (I.op == HMR_) b = I.b;
            else if (I.op == BINV_ || I.op == BST0_ || I.op == BST1_) b = I.a;
            if (b >= 0) {
                hist.push_back(b);
                if (!seen[b]) { seen[b] = 1; written.push_back(b); }
            }
        }
    }
    const int NW = (int)written.size();
    std::vector<std::vector<u64>> posOK(T), negOK(T);
    for (int t = 0; t < T; t++) { posOK[t].assign((nwritten[t] + 63) / 64, ~0ULL); negOK[t] = posOK[t]; }
    std::vector<std::vector<u64>> orOK(T);   // pairs of recent bits, 4 polarities
    std::vector<std::vector<long long>> orN(T);  // measured probability of each OR
    for (int t = 0; t < T; t++) {
        int m = (int)recent[t].size();
        orOK[t].assign((m * m * 4 + 63) / 64, ~0ULL);
        orN[t].assign(m * m * 4, 0);
    }
    std::vector<long long> ndiff(T, 0), nact(T, 0), nlane(1, 0);
    std::vector<std::vector<long long>> ones(T);
    for (int t = 0; t < T; t++) ones[t].assign(nwritten[t], 0);

    std::mutex mu;
    std::atomic<int> nextw(0);
    auto work = [&]() {
        while (true) {
            int w = nextw++;
            if (w >= W) break;
            u64 xs[64];
            std::mt19937_64 rng(seed * 7919 + w);
            for (int l = 0; l < 64; l++) xs[l] = (w == 0 && l < 32) ? l + 1 : 1 + rng() % NINPUT;
            State* ref = new State; init_state(*ref, xs);
            for (int k = 0; k < n; k++) step(*ref, ops[k], coin_word(seed, w, k), ~0ULL);
            State* pre = new State; init_state(*pre, xs);
            State* alt = new State;
            int at = 0;
            std::vector<u64> diffs(T), acts(T);
            std::vector<std::vector<u64>> bv(T);
            for (int t = 0; t < T; t++) {
                while (at < tk[t]) { step(*pre, ops[at], coin_word(seed, w, at), ~0ULL); at++; }
                u64 m = pre->cur;
                if (ops[tk[t]].cond >= 0) m &= pre->B[ops[tk[t]].cond];
                acts[t] = m;
                bv[t].resize(nwritten[t]);
                for (int j = 0; j < nwritten[t]; j++) bv[t][j] = pre->B[written[j]];
                memcpy(alt, pre, sizeof(State));
                for (int k = tk[t] + 1; k < n; k++) step(*alt, ops[k], coin_word(seed, w, k), ~0ULL);
                u64 d = alt->sign ^ ref->sign;
                for (int q = 0; q < NQMAX; q++) d |= alt->Q[q] ^ ref->Q[q];
                for (int l = 0; l < 64; l++) if (alt->rot[l] != ref->rot[l]) d |= 1ULL << l;
                diffs[t] = d;
            }
            std::lock_guard<std::mutex> g(mu);
            nlane[0] += 64;
            for (int t = 0; t < T; t++) {
                u64 d = diffs[t];
                ndiff[t] += __builtin_popcountll(d);
                nact[t] += __builtin_popcountll(acts[t]);
                for (int j = 0; j < nwritten[t]; j++) {
                    u64 b = bv[t][j];
                    ones[t][j] += __builtin_popcountll(b);
                    if (d & ~b) posOK[t][j >> 6] &= ~(1ULL << (j & 63));
                    if (d & b) negOK[t][j >> 6] &= ~(1ULL << (j & 63));
                }
                int m = (int)recent[t].size();
                std::vector<u64> rv(m);
                for (int a = 0; a < m; a++) {
                    int j = (int)(std::find(written.begin(), written.end(), recent[t][a]) - written.begin());
                    rv[a] = j < nwritten[t] ? bv[t][j] : 0;
                }
                for (int a = 0; a < m; a++)
                    for (int c = a + 1; c < m; c++)
                        for (int s = 0; s < 4; s++) {
                            u64 u = ((s & 1) ? ~rv[a] : rv[a]) | ((s & 2) ? ~rv[c] : rv[c]);
                            int id = (a * m + c) * 4 + s;
                            orN[t][id] += __builtin_popcountll(u);
                            if (d & ~u) orOK[t][id >> 6] &= ~(1ULL << (id & 63));
                        }
            }
            delete ref; delete pre; delete alt;
        }
    };
    std::vector<std::thread> th;
    for (int i = 0; i < nthreads(); i++) th.emplace_back(work);
    for (auto& x : th) x.join();

    const double L = (double)nlane[0];
    int dead = 0, single = 0, orpair = 0;
    double save1 = 0, save2 = 0;
    long long totact = 0;
    for (int t = 0; t < T; t++) {
        totact += nact[t];
        if (!ndiff[t]) { dead++; printf("DEAD op %d (type %d) never matters in %lld lanes\n", tk[t], ops[tk[t]].op, nlane[0]); continue; }
        double pact = nact[t] / L;
        // best single bit: the condition with the smallest probability
        double best = 2; int bj = -1, bneg = 0;
        for (int j = 0; j < nwritten[t]; j++) {
            double p1 = ones[t][j] / L;
            if (posOK[t][j >> 6] >> (j & 63) & 1) if (p1 < best) { best = p1; bj = j; bneg = 0; }
            if (negOK[t][j >> 6] >> (j & 63) & 1) if (1 - p1 < best) { best = 1 - p1; bj = j; bneg = 1; }
        }
        // only a real gain if the condition is rarer than the op's own execution guard
        if (bj >= 0 && best < pact - 0.01 && ndiff[t] * -std::log(std::max(1e-9, best)) >= 22.0) {
            single++; save1 += pact - std::min(pact, best);
            printf("SINK op %d (type %d, active %.3f, matters %.3f) under %sbit %d (p=%.3f)\n", tk[t], ops[tk[t]].op, pact,
                   ndiff[t] / L, bneg ? "NOT " : "", written[bj], best);
            continue;
        }
        int m = (int)recent[t].size();
        for (int a = 0; a < m; a++)
            for (int c = a + 1; c < m; c++)
                for (int s = 0; s < 4; s++) {
                    int id = (a * m + c) * 4 + s;
                    if (!(orOK[t][id >> 6] >> (id & 63) & 1)) continue;
                    int ja = (int)(std::find(written.begin(), written.end(), recent[t][a]) - written.begin());
                    int jc = (int)(std::find(written.begin(), written.end(), recent[t][c]) - written.begin());
                    if (ja >= nwritten[t] || jc >= nwritten[t]) continue;
                    double pu = orN[t][id] / L;      // measured, bits may be correlated
                    if (pu < pact - 0.05 && ndiff[t] * -std::log(std::max(1e-9, pu)) >= 30.0) {
                        orpair++; save2 += pact - pu;
                        printf("OR-SINK op %d (type %d, active %.3f) under %sbit %d OR %sbit %d (p~%.3f)\n", tk[t], ops[tk[t]].op,
                               pact, (s & 1) ? "NOT " : "", recent[t][a], (s & 2) ? "NOT " : "", recent[t][c], pu);
                        a = m; c = m; break;
                    }
                }
    }
    printf("toffoli-class ops %d, bits %d, lanes %lld, mean executed %.4f\n", T, NW, nlane[0], totact / L);
    printf("never-matters %d, single-bit sinkable %d (saves %.3f mean), OR-pair sinkable %d (saves %.3f mean)\n",
           dead, single, save1, orpair, save2);
}

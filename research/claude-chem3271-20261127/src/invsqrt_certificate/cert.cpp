// Certificate extraction: v_e + sum CCZ-terms  =  sum of free monomials (Z/CZ at recorded cuts)
// usage: cert ops e tmin tmax W seed out [k:l1:l2:l3 ...]
//   l = comma list of wires (q3,q7,...) and/or "1"; k = op index of the cut where the CCZ is applied.
// Output lines:  MONO k i j      (NEG if i<0 ; Z q_i if j<0 ; CZ q_i q_j)  at boundary k
//                CCZ k l1 l2 l3
#include "rec.h"
#include <sstream>
static std::vector<int> parse_l(const std::string& s) {
    std::vector<int> r; std::stringstream ss(s); std::string t;
    while (std::getline(ss, t, ',')) { if (t.empty()) continue; if (t == "1") r.push_back(-1); else r.push_back(atoi(t.c_str() + 1)); }
    return r;
}
int main(int argc, char** argv) {
    if (argc < 8) { fprintf(stderr, "usage\n"); return 2; }
    auto ops = load_ops(argv[1]);
    const int e = atoi(argv[2]);
    int tmin = atoi(argv[3]); if (tmin <= e) tmin = e + 1;
    const int tmax = std::min((int)ops.size(), atoi(argv[4]));
    const int W = atoi(argv[5]);
    const u64 seed = strtoull(argv[6], 0, 10);
    auto xs = strat_samples(W, seed);
    Recorder R; R.run(ops, xs, e, tmin, tmax);
    fprintf(stderr, "states %zu\n", R.states.size());

    struct Mon { int k, i, j; };
    std::vector<Mon> mons;
    const int TB = std::min(W * 64, 40000);
    Basis B(W, TB);
    std::vector<u64> tg(B.T);
    R.generators(ops, [&](int s, int i, int j, const u64* v) {
        Vec x(v, v + W);
        std::fill(tg.begin(), tg.end(), 0);
        int p = B.reduce(x.data(), tg.data());
        if (p >= 0) {
            int g = (int)mons.size();
            if (g >= TB) { fprintf(stderr, "too many generators\n"); exit(1); }
            mons.push_back({R.states[s].k, i, j});
            tg[g >> 6] ^= 1ULL << (g & 63);
            B.insert_reduced(x.data(), tg.data(), p);
        }
    });
    fprintf(stderr, "rank %d of %d\n", B.rank, W * 64);

    Vec t = R.target;
    struct Term { int k; std::vector<int> l[3]; };
    std::vector<Term> terms;
    for (int a = 8; a < argc; a++) {
        std::stringstream ss(argv[a]); std::string p; Term T;
        std::getline(ss, p, ':'); T.k = atoi(p.c_str());
        for (int i = 0; i < 3; i++) { std::getline(ss, p, ':'); T.l[i] = parse_l(p); }
        const StateRec* st = nullptr;
        for (auto& s : R.states) if (s.k == T.k) st = &s;
        if (!st) { fprintf(stderr, "no state at op %d\n", T.k); return 1; }
        Vec prod(W, ~0ULL);
        for (int i = 0; i < 3; i++) {
            Vec l(W, 0);
            for (int q : T.l[i]) {
                if (q < 0) { for (int w = 0; w < W; w++) l[w] ^= ~0ULL; continue; }
                if (st->wid[q] < 0) { fprintf(stderr, "wire q%d unusable at %d (treated as zero)\n", q, T.k); continue; }
                for (int w = 0; w < W; w++) l[w] ^= R.vals[st->wid[q]][w];
            }
            for (int w = 0; w < W; w++) prod[w] &= l[w];
        }
        for (int w = 0; w < W; w++) t[w] ^= prod[w];
        terms.push_back(T);
    }
    std::fill(tg.begin(), tg.end(), 0);
    int p = B.reduce(t.data(), tg.data());
    if (p >= 0) { printf("NOT IN SPAN\n"); return 1; }
    FILE* f = fopen(argv[7], "w");
    int cnt = 0;
    for (int g = 0; g < (int)mons.size(); g++)
        if ((tg[g >> 6] >> (g & 63)) & 1) { fprintf(f, "MONO %d %d %d\n", mons[g].k, mons[g].i, mons[g].j); cnt++; }
    for (auto& T : terms) {
        fprintf(f, "CCZ %d", T.k);
        for (int i = 0; i < 3; i++) {
            fprintf(f, " ");
            for (size_t a = 0; a < T.l[i].size(); a++) { if (a) fprintf(f, ","); if (T.l[i][a] < 0) fprintf(f, "1"); else fprintf(f, "q%d", T.l[i][a]); }
        }
        fprintf(f, "\n");
    }
    fclose(f);
    printf("certificate with %d free monomials and %zu CCZ terms\n", cnt, terms.size());
    return 0;
}

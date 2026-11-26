// C++ port of the move loop of fivecols.py: make several five-care columns relation columns at once.
// Input (text, from fc2.py): n nstates npairs; pairs; a[i] b[i] (3 words each); s[i];
//   per state: C W; member[144] (W words each); aS[n], bS[n] (W words each); O[30] (W words each).
// Strategy: walk until one open column has a zero candidate, restrict that column to it (its delta must stay 0),
// continue for the next; restart from the saved start state if the next one is not found within M moves.
// Output: "FOUND moves", then s[i] for all i, then "state candidate" for each fixed column.
// usage: fc2 input want M_per_stage restarts seed
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <random>
#include <chrono>
typedef uint64_t u64;

struct State {
    int C, W;
    std::vector<u64> mem, aS, bS, O;       // mem: 144*W, aS/bS: n*W, O: 30*W
    std::vector<u64> last;
};
struct Fixed {                             // a state restricted to one candidate
    int state, cand;
    std::vector<uint8_t> mem, aS, bS;
};

int main(int argc, char** argv) {
    if (argc < 6) return 2;
    FILE* f = fopen(argv[1], "r");
    int want = atoi(argv[2]);
    long long M = atoll(argv[3]);
    int restarts = atoi(argv[4]);
    unsigned long long seed = strtoull(argv[5], 0, 10);
    int n, ns, np;
    if (fscanf(f, "%d %d %d", &n, &ns, &np) != 3) return 2;
    std::vector<std::pair<int, int>> pairs(np);
    for (auto& p : pairs) if (fscanf(f, "%d %d", &p.first, &p.second) != 2) return 2;
    auto rd = [&]() { unsigned long long x; if (fscanf(f, "%llu", &x) != 1) exit(2); return (u64)x; };
    std::vector<u64> a0(n * 3), b0(n * 3), s0(n);
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < 3; k++) a0[i * 3 + k] = rd();
        for (int k = 0; k < 3; k++) b0[i * 3 + k] = rd();
    }
    for (int i = 0; i < n; i++) s0[i] = rd();
    std::vector<State> st0(ns);
    for (auto& s : st0) {
        if (fscanf(f, "%d %d", &s.C, &s.W) != 2) return 2;
        s.mem.resize(144 * s.W);
        s.aS.resize(n * s.W);
        s.bS.resize(n * s.W);
        s.O.resize(30 * s.W);
        for (auto* v : {&s.mem, &s.aS, &s.bS, &s.O})
            for (auto& x : *v) x = rd();
        s.last.assign(s.W, ~0ULL);
        if (s.C % 64) s.last[s.W - 1] = (1ULL << (s.C % 64)) - 1;
    }
    fclose(f);
    auto zero_of = [&](const State& s) -> int {
        for (int w = 0; w < s.W; w++) {
            u64 acc = 0;
            for (int o = 0; o < 30; o++) acc |= s.O[o * s.W + w];
            u64 z = s.last[w] & ~acc;
            if (z) return w * 64 + __builtin_ctzll(z);
        }
        return -1;
    };
    std::mt19937_64 rng(seed);
    auto t0 = std::chrono::steady_clock::now();
    auto secs = [&]() { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };
    std::vector<u64> delta, B;
    long long total = 0;
    int bestfixed = 0;
    for (int r = 0; r < restarts; r++) {
        std::vector<u64> a = a0, b = b0, s = s0;
        std::vector<State> st = st0;
        std::vector<Fixed> fx;
        std::vector<char> isfixed(ns, 0);
        // random pre-walk so that restarts start from different covers
        for (int pre = 0; pre < 2000 * (r > 0); pre++) {
            auto [i, j] = pairs[rng() % np];
            u64 c[3];
            for (int k = 0; k < 3; k++) c[k] = (a[i * 3 + k] & b[j * 3 + k]) ^ (a[j * 3 + k] & b[i * 3 + k]);
            for (auto& S : st) {
                const int W = S.W;
                for (int w = 0; w < W; w++) {
                    u64 Bv = 0;
                    for (int k = 0; k < 3; k++)
                        for (u64 m = c[k]; m; m &= m - 1) Bv ^= S.mem[(k * 64 + __builtin_ctzll(m)) * W + w];
                    u64 d = (S.aS[i * W + w] & S.bS[j * W + w]) ^ (S.aS[j * W + w] & S.bS[i * W + w]) ^ Bv;
                    for (u64 m = s[i]; m; m &= m - 1) S.O[__builtin_ctzll(m) * W + w] ^= d;
                    S.aS[i * W + w] ^= S.aS[j * W + w];
                    S.bS[i * W + w] ^= S.bS[j * W + w];
                }
            }
            for (int k = 0; k < 3; k++) { a[i * 3 + k] ^= a[j * 3 + k]; b[i * 3 + k] ^= b[j * 3 + k]; }
            s[j] ^= s[i];
        }
        long long stage = 0, moves = 0;
        while ((int)fx.size() < want && stage < M) {
            auto [i, j] = pairs[rng() % np];
            u64 c[3];
            for (int k = 0; k < 3; k++) c[k] = (a[i * 3 + k] & b[j * 3 + k]) ^ (a[j * 3 + k] & b[i * 3 + k]);
            // fixed columns must not change
            bool bad = false;
            for (auto& F : fx) {
                uint8_t Bv = 0;
                for (int k = 0; k < 3; k++)
                    for (u64 m = c[k]; m; m &= m - 1) Bv ^= F.mem[k * 64 + __builtin_ctzll(m)];
                if (((F.aS[i] & F.bS[j]) ^ (F.aS[j] & F.bS[i]) ^ Bv) & 1) { bad = true; break; }
            }
            stage++;
            if (bad) continue;
            moves++;
            const u64 si = s[i];
            int found = -1, fc = -1;
            for (int q = 0; q < ns; q++) {
                if (isfixed[q]) continue;
                State& S = st[q];
                const int W = S.W;
                delta.assign(W, 0);
                for (int k = 0; k < 3; k++)
                    for (u64 m = c[k]; m; m &= m - 1) {
                        const u64* mm = &S.mem[(k * 64 + __builtin_ctzll(m)) * W];
                        for (int w = 0; w < W; w++) delta[w] ^= mm[w];
                    }
                u64* Ai = &S.aS[i * W];
                u64* Aj = &S.aS[j * W];
                u64* Bi = &S.bS[i * W];
                u64* Bj = &S.bS[j * W];
                u64 any = 0;
                for (int w = 0; w < W; w++) {
                    delta[w] ^= (Ai[w] & Bj[w]) ^ (Aj[w] & Bi[w]);
                    Ai[w] ^= Aj[w];
                    Bi[w] ^= Bj[w];
                    any |= delta[w];
                }
                if (any) {
                    for (u64 m = si; m; m &= m - 1) {
                        u64* Oo = &S.O[__builtin_ctzll(m) * W];
                        for (int w = 0; w < W; w++) Oo[w] ^= delta[w];
                    }
                    int z = zero_of(S);
                    if (z >= 0 && found < 0) { found = q; fc = z; }
                }
            }
            for (auto& F : fx) { F.aS[i] ^= F.aS[j]; F.bS[i] ^= F.bS[j]; }
            for (int k = 0; k < 3; k++) { a[i * 3 + k] ^= a[j * 3 + k]; b[i * 3 + k] ^= b[j * 3 + k]; }
            s[j] ^= s[i];
            if (found >= 0) {
                const State& S = st[found];
                const int W = S.W;
                Fixed F;
                F.state = found;
                F.cand = fc;
                F.mem.resize(144);
                F.aS.resize(n);
                F.bS.resize(n);
                for (int p = 0; p < 144; p++) F.mem[p] = (S.mem[p * W + fc / 64] >> (fc % 64)) & 1;
                for (int x = 0; x < n; x++) {
                    F.aS[x] = (S.aS[x * W + fc / 64] >> (fc % 64)) & 1;
                    F.bS[x] = (S.bS[x * W + fc / 64] >> (fc % 64)) & 1;
                }
                fx.push_back(std::move(F));
                isfixed[found] = 1;
                if ((int)fx.size() > bestfixed) {
                    bestfixed = (int)fx.size();
                    fprintf(stderr, "restart %d: %zu column(s) fixed after %lld moves (%.0fs)\n", r, fx.size(), moves, secs());
                }
                stage = 0;
            }
        }
        total += moves;
        if ((int)fx.size() >= want) {
            printf("FOUND %lld\n", total);
            for (int x = 0; x < n; x++) printf("%llu ", (unsigned long long)s[x]);
            printf("\n");
            for (auto& F : fx) printf("%d %d\n", F.state, F.cand);
            return 0;
        }
        if (r % 20 == 19) fprintf(stderr, "restart %d done, total moves %lld (%.0fs), best fixed %d\n", r, total, secs(), bestfixed);
    }
    printf("NOTFOUND %lld\n", total);
    return 1;
}

// Exhaustive check: remove each listed op and compare data/phase/rotation on every input x in [1, NINPUT].
// usage: deadcheck ops.txt seed op1 [op2 ...]
#include "qsim.h"

int main(int argc, char** argv) {
    auto ops = load_ops(argv[1]);
    const u64 seed = strtoull(argv[2], 0, 10);
    std::vector<int> cut;
    for (int i = 3; i < argc; i++) cut.push_back(atoi(argv[i]));
    const int n = (int)ops.size(), C = (int)cut.size();
    std::vector<std::atomic<long long>> bad(C);
    for (auto& b : bad) b = 0;
    std::atomic<u64> next(0);
    auto work = [&]() {
        State* ref = new State;
        State* alt = new State;
        while (true) {
            u64 w = next++;
            if (w >= nbatches()) break;
            u64 xs[64], lm;
            batch_inputs(w, xs, lm);
            init_state(*ref, xs);
            for (int k = 0; k < n; k++) step(*ref, ops[k], coin_word(seed, w, k), lm);
            for (int c = 0; c < C; c++) {
                init_state(*alt, xs);
                for (int k = 0; k < n; k++)
                    if (k != cut[c]) step(*alt, ops[k], coin_word(seed, w, k), lm);
                u64 d = alt->sign ^ ref->sign;
                for (int q = 0; q < NQMAX; q++) d |= alt->Q[q] ^ ref->Q[q];
                for (int l = 0; l < 64; l++) if (alt->rot[l] != ref->rot[l]) d |= 1ULL << l;
                bad[c] += __builtin_popcountll(d & lm);
            }
        }
        delete ref;
        delete alt;
    };
    std::vector<std::thread> th;
    for (int i = 0; i < nthreads(); i++) th.emplace_back(work);
    for (auto& x : th) x.join();
    for (int c = 0; c < C; c++) printf("op %d: differing inputs %lld of %llu\n", cut[c], bad[c].load(), NINPUT);
}

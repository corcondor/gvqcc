// For each listed phase op, count over every input how often it actually fires (condition and all operands 1).
// usage: opval ops.txt seed op1 [op2 ...]
#include "qsim.h"

int main(int argc, char** argv) {
    auto ops = load_ops(argv[1]);
    const u64 seed = strtoull(argv[2], 0, 10);
    std::vector<int> at;
    for (int i = 3; i < argc; i++) at.push_back(atoi(argv[i]));
    const int n = (int)ops.size(), C = (int)at.size();
    std::vector<std::atomic<long long>> fire(C), pairfire(C), act(C);
    for (int c = 0; c < C; c++) { fire[c] = 0; pairfire[c] = 0; act[c] = 0; }
    std::atomic<u64> next(0);
    auto work = [&]() {
        State* s = new State;
        while (true) {
            u64 w = next++;
            if (w >= nbatches()) break;
            u64 xs[64], lm;
            batch_inputs(w, xs, lm);
            init_state(*s, xs);
            for (int k = 0; k < n; k++) {
                for (int c = 0; c < C; c++)
                    if (at[c] == k) {
                        const Ins& I = ops[k];
                        u64 m = s->cur;
                        if (I.cond >= 0) m &= s->B[I.cond];
                        u64 abc = s->Q[I.a] & s->Q[I.b] & s->Q[I.c];
                        fire[c] += __builtin_popcountll(abc & m & lm);
                        pairfire[c] += __builtin_popcountll(abc & lm);
                        act[c] += __builtin_popcountll(m & lm);
                    }
                step(*s, ops[k], coin_word(seed, w, k), lm);
            }
        }
        delete s;
    };
    std::vector<std::thread> th;
    for (int i = 0; i < nthreads(); i++) th.emplace_back(work);
    for (auto& x : th) x.join();
    for (int c = 0; c < C; c++)
        printf("op %d (type %d, qubits %d %d %d, cond %d): fires %lld, operand product 1 on %lld inputs, active %.4f\n", at[c],
               ops[at[c]].op, ops[at[c]].a, ops[at[c]].b, ops[at[c]].c, ops[at[c]].cond, fire[c].load(), pairfire[c].load(),
               (double)act[c].load() / NINPUT);
}

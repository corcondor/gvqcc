// shared state recording for the search / certificate tools
#pragma once
#include "lib.h"
#include <algorithm>
struct StateRec { int k; std::vector<int> wid; };
struct Recorder {
    int W;
    std::vector<Vec> vals;
    std::unordered_map<u64, std::vector<int>> vhash;
    std::vector<StateRec> states;
    Vec target;
    int intern(const u64* p) {
        u64 h = 1469598103934665603ULL;
        for (int w = 0; w < W; w++) h = (h ^ p[w]) * 1099511628211ULL;
        for (int id : vhash[h]) if (!memcmp(vals[id].data(), p, 8 * W)) return id;
        vals.emplace_back(p, p + W); vhash[h].push_back((int)vals.size() - 1); return (int)vals.size() - 1;
    }
    // record top-level states after nonlinear changes in [tmin,tmax]; target = wire of HMR e (or none)
    void run(const std::vector<Ins>& ops, const std::vector<u64>& xs, int e, int tmin, int tmax) {
        const int n = (int)ops.size();
        W = (int)xs.size() / 64;
        Trace z(ops, xs), r(ops, xs);
        std::vector<int> prev;
        bool dirty = true;
        for (int k = 0; k <= n; k++) {
            if (k == e) {
                if (ops[k].op != HMR_) { fprintf(stderr, "op %d is not HMR\n", k); exit(1); }
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
            if (k == n || (k >= tmax && k > e)) break;
            z.step(k, 0); r.step(k, 12345);
            if (ops[k].op == CCX_ || ops[k].op == CSWAP_ || ops[k].op == HMR_) dirty = true;
            if (k + 1 == tmin) dirty = true;
        }
    }
    // generator monomials of F in time order: callback(state index, i, j, vector)  (j=-1: single wire; i=-1: constant)
    template <class Fn> void generators(const std::vector<Ins>& ops, Fn&& cb) {
        Vec tmp(W), one(W, ~0ULL);
        cb(0, -1, -1, one.data());
        std::vector<int> last(NQ, -1);
        std::unordered_set<u64> seenpair;
        std::unordered_set<int> seenval;
        for (size_t s = 0; s < states.size(); s++) {
            const auto& id = states[s].wid;
            std::vector<int> fresh;
            if (s == 0) { for (int q = 0; q < NQ; q++) fresh.push_back(q); }
            else {
                for (int k = states[s - 1].k; k < states[s].k; k++) {
                    if (ops[k].op == CCX_) fresh.push_back(ops[k].c);
                    if (ops[k].op == CSWAP_) { fresh.push_back(ops[k].b); fresh.push_back(ops[k].c); }
                }
                for (int q = 0; q < NQ; q++) if (last[q] < 0 && id[q] >= 0) fresh.push_back(q);
                for (int q = 0; q < NQ; q++) if (id[q] >= 0 && id[q] != last[q]) fresh.push_back(q);
                std::sort(fresh.begin(), fresh.end()); fresh.erase(std::unique(fresh.begin(), fresh.end()), fresh.end());
            }
            for (int q : fresh) {
                if (id[q] < 0 || !seenval.insert(id[q]).second) continue;
                cb((int)s, q, -1, vals[id[q]].data());
                for (int j = 0; j < NQ; j++) {
                    if (j == q || id[j] < 0) continue;
                    u64 a = std::min(id[q], id[j]), b = std::max(id[q], id[j]);
                    if (!seenpair.insert(a * 1000003ULL + b).second) continue;
                    for (int w = 0; w < W; w++) tmp[w] = vals[id[q]][w] & vals[id[j]][w];
                    cb((int)s, q, j, tmp.data());
                }
            }
            last = id;
        }
    }
};

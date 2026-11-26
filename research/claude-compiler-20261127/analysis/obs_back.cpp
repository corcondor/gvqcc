// Backward predicated-observability (partial dead code) for large KMB circuits.
// For every CCX, the condition under which the value it adds to its target is ever observed later
// (as a conjunction of classical literals).  CCX needed only under extra, already-known conditions are
// candidates for moving inside them.  Conservative: HMR observes, XOR chains keep the weakest condition.
// usage: obs_back circuit.kmb
#include "kmbs.h"
#include <map>
#include <cmath>
#include <array>

typedef std::vector<u64> Set;
static const u64 CHUNK = 1ULL << 22;

struct Pool {
    std::vector<Set> sets;
    std::map<Set, int> ids;
    std::unordered_map<u64, int> meetMemo, joinMemo;
    Pool() { sets.push_back(Set()); sets.push_back(Set()); ids[Set()] = 1; }  // 0 = TOP (never observed), 1 = always
    int id(const Set& s) {
        auto it = ids.find(s);
        if (it != ids.end()) return it->second;
        int k = (int)sets.size();
        sets.push_back(s);
        ids[s] = k;
        return k;
    }
    int meet(int a, int b) {  // weakest condition covering both (intersection of literals)
        if (a == 0) return b;
        if (b == 0) return a;
        if (a == b || a == 1) return a;
        if (b == 1) return 1;
        u64 key = ((u64)std::min(a, b) << 32) | std::max(a, b);
        auto it = meetMemo.find(key);
        if (it != meetMemo.end()) return it->second;
        Set r;
        std::set_intersection(sets[a].begin(), sets[a].end(), sets[b].begin(), sets[b].end(), std::back_inserter(r));
        return meetMemo[key] = id(r);
    }
    int join(int a, int g) {  // observed under a AND executed under g (union of literals)
        if (a == 0) return 0;
        if (g == 1 || a == g) return a;
        if (a == 1) return g;
        u64 key = ((u64)a << 32) | g;
        auto it = joinMemo.find(key);
        if (it != joinMemo.end()) return it->second;
        Set r;
        std::set_union(sets[a].begin(), sets[a].end(), sets[g].begin(), sets[g].end(), std::back_inserter(r));
        return joinMemo[key] = id(r);
    }
};

struct ChunkInfo {
    u64 off[10];
    std::vector<u32> curpos;       // bit -> 1 + op index of its current value
    std::vector<char> coin;        // bit -> current value is a measurement outcome
    std::vector<int> stack;        // cumulative guard set ids
};

int main(int argc, char** argv) {
    KmbS K;
    K.parse(argv[1]);
    const u32 NQ = K.H.nq, NB = K.H.nb;
    const u64 N = K.H.nops;
    Pool P;
    auto mklit = [&](u32 b, bool neg, const std::vector<u32>& cp, const std::vector<char>& coin) {
        return ((u64)cp[b] << 23) | ((u64)b << 2) | ((u64)(coin[b] ? 1 : 0) << 1) | (neg ? 1 : 0);
    };
    // ---------- forward pass: record chunk starts ----------
    std::vector<ChunkInfo> chunks;
    {
        std::vector<u32> curpos(NB + 16, 0);
        std::vector<char> coin(NB + 16, 0);
        std::vector<int> stack;
        u64 used[10] = {0};
        SDec d(K);
        SOp o;
        while (d.next(o)) {
            if (o.i % CHUNK == 0) {
                ChunkInfo c;
                memcpy(c.off, used, sizeof used);
                c.curpos = curpos;
                c.coin = coin;
                c.stack = stack;
                chunks.push_back(std::move(c));
            }
            used[1] += 1;
            if (o.cat == 3) { used[2] += 4; used[3] += 4; used[4] += 4; }
            else if (o.cat == 2) { used[5] += 4; used[6] += 4; }
            else if (o.cat == 1) used[7] += 4;
            if (o.hasbit) used[8] += 4;
            if (o.hascond) used[9] += 4;
            if (o.base == 1) {
                if (o.op & 128) {
                    int top = stack.empty() ? 1 : stack.back();
                    int lit = P.id(Set{mklit(o.cond & 0x7fffffff, o.cond >> 31, curpos, coin)});
                    stack.push_back(P.join(top, lit));
                } else stack.pop_back();
            } else if (o.base == 0x40 || o.base == 0x41 || o.base == 0x42) {
                curpos[o.bit] = (u32)(o.i + 1);
                coin[o.bit] = 0;
            } else if (o.base == 0x50) {
                curpos[o.bit] = (u32)(o.i + 1);
                coin[o.bit] = 1;
            }
        }
        K.end();
    }
    fprintf(stderr, "forward done: %zu chunks, %zu guard sets\n", chunks.size(), P.sets.size());
    // ---------- backward pass ----------
    std::vector<int> obs(NQ, 1);   // everything observed at the end
    u64 nccx = 0, ndead = 0, ncand = 0, ncoin = 0;
    double saving = 0;
    std::map<std::pair<int, int>, u64> hist;   // (extra literals, extra coin literals)
    std::vector<std::string> samples;
    for (int c = (int)chunks.size() - 1; c >= 0; c--) {
        ChunkInfo& ci = chunks[c];
        const u64 lo = (u64)c * CHUNK, hi = std::min(N, lo + CHUNK);
        std::vector<u8> ob(hi - lo);
        std::vector<std::array<u32, 3>> qs(hi - lo);
        std::vector<int> gid(hi - lo);
        {
            Stream st[10];
            for (int s = 1; s <= 9; s++) st[s].open(K.path.c_str(), K.secoff[s] + ci.off[s], K.secsz[s] - ci.off[s], 1 << 20);
            std::vector<u32> curpos = ci.curpos;
            std::vector<char> coin = ci.coin;
            std::vector<int> stack = ci.stack;
            for (u64 i = lo; i < hi; i++) {
                u8 op = st[1].get8();
                u8 base = op & 127, cat = (op >> 4) & 3;
                std::array<u32, 3> q = {0, 0, 0};
                if (cat == 3) { q[0] = st[2].get32(); q[1] = st[3].get32(); q[2] = st[4].get32(); }
                else if (cat == 2) { q[0] = st[5].get32(); q[1] = st[6].get32(); }
                else if (cat == 1) q[0] = st[7].get32();
                u32 bit = (op & 64) ? st[8].get32() : 0;
                u32 cond = (op & 128) ? st[9].get32() : 0;
                int top = stack.empty() ? 1 : stack.back();
                int g = top;
                if (base == 1) {
                    if (op & 128) stack.push_back(P.join(top, P.id(Set{mklit(cond & 0x7fffffff, cond >> 31, curpos, coin)})));
                    else stack.pop_back();
                } else if (op & 128) g = P.join(top, P.id(Set{mklit(cond & 0x7fffffff, cond >> 31, curpos, coin)}));
                if (base == 0x40 || base == 0x41 || base == 0x42) { curpos[bit] = (u32)(i + 1); coin[bit] = 0; }
                else if (base == 0x50) { curpos[bit] = (u32)(i + 1); coin[bit] = 1; }
                ob[i - lo] = base;
                qs[i - lo] = q;
                gid[i - lo] = g;
            }
            for (int s = 1; s <= 9; s++) st[s].close();
        }
        for (u64 j = hi - lo; j-- > 0;) {
            const u8 base = ob[j];
            const auto& q = qs[j];
            const int g = gid[j];
            const u64 i = lo + j;
            switch (base) {
                case 0x10: obs[q[0]] = P.meet(obs[q[0]], g); break;
                case 0x11: break;
                case 0x12: if (g == 1) obs[q[0]] = 0; break;
                case 0x20: obs[q[0]] = P.meet(obs[q[0]], g); obs[q[1]] = P.meet(obs[q[1]], g); break;
                case 0x21: obs[q[0]] = P.meet(obs[q[0]], P.join(obs[q[1]], g)); break;
                case 0x22:
                    if (g == 1) std::swap(obs[q[0]], obs[q[1]]);
                    else {
                        int a = P.meet(obs[q[0]], P.join(obs[q[1]], g)), b = P.meet(obs[q[1]], P.join(obs[q[0]], g));
                        obs[q[0]] = a;
                        obs[q[1]] = b;
                    }
                    break;
                case 0x30:
                    for (int k = 0; k < 3; k++) obs[q[k]] = P.meet(obs[q[k]], g);
                    break;
                case 0x31: {
                    nccx++;
                    const int ot = obs[q[2]];
                    if (ot == 0) {
                        ndead++;
                        if (samples.size() < 20) {
                            char buf[160];
                            snprintf(buf, sizeof buf, "  dead CCX at op %llu (%u,%u->%u)", (unsigned long long)i, q[0], q[1], q[2]);
                            samples.push_back(buf);
                        }
                    } else if (ot != 1) {
                        int nlit = 0, ncl = 0;
                        for (u64 l : P.sets[ot]) {
                            if ((l >> 23) > i) continue;                    // value not yet known at the CCX
                            if (std::binary_search(P.sets[g].begin(), P.sets[g].end(), l)) continue;
                            nlit++;
                            if (l & 2) ncl++;
                        }
                        if (nlit) {
                            ncand++;
                            if (ncl) ncoin++;
                            hist[{nlit, ncl}]++;
                            int coincg = 0;
                            for (u64 l : P.sets[g]) if (l & 2) coincg++;
                            saving += std::pow(0.5, coincg) * (1 - std::pow(0.5, ncl));
                            if (samples.size() < 20 && ncl) {
                                char buf[160];
                                snprintf(buf, sizeof buf, "  CCX op %llu (%u,%u->%u) extra literals %d (coin %d)", (unsigned long long)i,
                                         q[0], q[1], q[2], nlit, ncl);
                                samples.push_back(buf);
                            }
                        }
                    }
                    if (ot != 0) {
                        int u = P.join(ot, g);
                        obs[q[0]] = P.meet(obs[q[0]], u);
                        obs[q[1]] = P.meet(obs[q[1]], u);
                    }
                } break;
                case 0x32: {
                    int m = P.meet(obs[q[1]], obs[q[2]]);
                    if (m != 0) obs[q[0]] = P.meet(obs[q[0]], P.join(m, g));
                    obs[q[1]] = m;
                    obs[q[2]] = m;
                } break;
                case 0x50: obs[q[0]] = (g == 1) ? 1 : P.meet(obs[q[0]], g); break;   // HMR observes (phase)
                case 0x00: case 0x01: case 0x40: case 0x41: case 0x42: break;
                default:
                    if (((base >> 4) & 3) == 1) obs[q[0]] = P.meet(obs[q[0]], g);
                    else { fprintf(stderr, "unknown base %u\n", base); return 3; }
            }
        }
        fprintf(stderr, "chunk %d done, guard sets %zu\n", c, P.sets.size());
    }
    printf("CCX %llu  never observed %llu  observed only under extra known conditions %llu (with coin literal %llu)\n",
           (unsigned long long)nccx, (unsigned long long)ndead, (unsigned long long)ncand, (unsigned long long)ncoin);
    for (auto& kv : hist)
        printf("  extra literals %d, of which coin %d : %llu\n", kv.first.first, kv.first.second, (unsigned long long)kv.second);
    printf("estimated mean Toffoli saved counting coin literals only: %.2f\n", saving);
    for (auto& s : samples) printf("%s\n", s.c_str());
}

// Streaming predicated-liveness census (C++ port of pred_sink.py) for large KMB circuits.
// usage: pred_sink circuit.kmb synd_qids.txt|- [n_input_if_-]
#include "kmbs.h"
#include <map>
#include <cmath>
#include <fstream>

typedef std::vector<u64> Set;   // sorted condition literals (bit, version, negated)

static Set meet(const Set& a, const Set& b) {
    Set r;
    std::set_intersection(a.begin(), a.end(), b.begin(), b.end(), std::back_inserter(r));
    return r;
}
static bool subset(const Set& a, const Set& b) { return std::includes(b.begin(), b.end(), a.begin(), a.end()); }

struct Gad {
    u64 i; u32 a, b, t; Set cg, ug; bool hasUse = false, impure = false;
    i64 first = -1, opw = -1; u64 nr = 0; bool live = false;
};

int main(int argc, char** argv) {
    KmbS K; K.parse(argv[1]);
    const u32 NQ = K.H.nq, NB = K.H.nb;
    std::vector<char> isIn(NQ, 0);
    if (std::string(argv[2]) == "-") { for (u32 q = 0; q < (u32)atoi(argv[3]) && q < NQ; q++) isIn[q] = 1; }
    else { std::ifstream f(argv[2]); int x; while (f >> x) if (x >= 0 && (u32)x < NQ) isIn[x] = 1; }
    std::vector<u32> ver(NB + 16, 0);
    std::vector<i64> wposLast(NB + 16, -1);
    std::unordered_map<u64, i64> wpos;          // (bit, ver) -> op that created this version
    std::vector<char> kind(NB + 16, 0);          // 'H' coin, 'S' stored
    std::vector<Set> stack;                      // cumulative condition sets
    std::vector<char> clean(NQ, 1);
    std::vector<Set> dirty(NQ);
    for (u32 q = 0; q < NQ; q++) if (isIn[q]) clean[q] = 0;
    std::vector<Gad*> gad(NQ, nullptr);
    std::vector<std::vector<Gad*>> opnd(NQ);
    u64 npair = 0, nccx = 0, nccz = 0, ngad = 0, npure = 0, ndead = 0, ncand = 0, nmov = 0;
    double saving = 0;
    std::map<std::pair<std::string, int>, u64> hist;
    std::vector<std::string> samples;

    auto bitof = [](u64 lit) { return (u32)((lit >> 1) & 0xffffff); };
    auto verof = [](u64 lit) { return (u32)(lit >> 25); };
    auto lit = [&](u32 b, bool neg) { return ((u64)ver[b] << 25) | ((u64)b << 1) | (neg ? 1 : 0); };

    auto finalize = [&](Gad* g, i64 I, bool released) {
        for (u32 w : {g->a, g->b}) {
            auto& v = opnd[w];
            v.erase(std::remove(v.begin(), v.end(), g), v.end());
        }
        if (!g->impure && released) {
            npure++;
            if (!g->hasUse) ndead++;
            else {
                Set extra;
                std::set_difference(g->ug.begin(), g->ug.end(), g->cg.begin(), g->cg.end(), std::back_inserter(extra));
                if (!extra.empty()) {
                    ncand++;
                    i64 lo = (i64)g->i;
                    std::string kinds;
                    int coin = 0, coincg = 0;
                    for (u64 l : extra) {
                        auto it = wpos.find(((u64)verof(l) << 32) | bitof(l));
                        i64 p = it == wpos.end() ? -1 : it->second;
                        lo = std::max(lo, p + 1);
                        kinds += kind[bitof(l)] ? kind[bitof(l)] : '?';
                        if (kind[bitof(l)] == 'H') coin++;
                    }
                    for (u64 l : g->cg) if (kind[bitof(l)] == 'H') coincg++;
                    i64 hi = g->first;
                    if (g->opw >= 0) hi = std::min(hi, g->opw);
                    bool mov = lo <= hi;
                    std::sort(kinds.begin(), kinds.end());
                    if (kinds.size() > 6) kinds.resize(6);
                    hist[{kinds, (int)mov}]++;
                    if (mov) {
                        nmov++;
                        double pc = std::pow(0.5, coincg);
                        saving += pc - pc * std::pow(0.5, coin);
                    }
                    if (samples.size() < 30) {
                        char buf[256];
                        snprintf(buf, sizeof buf, "  ccx op %llu (%u,%u->%u) first %lld opw %lld end %lld reads %llu extra %zu mov %d kinds %s",
                                 (unsigned long long)g->i, g->a, g->b, g->t, (long long)g->first, (long long)g->opw, (long long)I,
                                 (unsigned long long)g->nr, extra.size(), mov, kinds.c_str());
                        samples.push_back(buf);
                    }
                }
            }
        }
        delete g;
    };

    SDec d(K);
    SOp o;
    while (d.next(o)) {
        const i64 I = (i64)o.i;
        if (o.base == 1) {
            if (o.op & 128) {
                u32 b = o.cond & 0x7fffffff;
                Set s = stack.empty() ? Set() : stack.back();
                s.push_back(lit(b, o.cond >> 31));
                std::sort(s.begin(), s.end());
                s.erase(std::unique(s.begin(), s.end()), s.end());
                stack.push_back(s);
            } else stack.pop_back();
            continue;
        }
        Set g = stack.empty() ? Set() : stack.back();
        if (o.hascond) {
            u64 l = lit(o.cond & 0x7fffffff, o.cond >> 31);
            g.insert(std::upper_bound(g.begin(), g.end(), l), l);
        }
        auto read = [&](u32 q) {
            Gad* x = gad[q];
            if (!x) return;
            if (!x->hasUse) { x->ug = g; x->hasUse = true; x->first = I; }
            else x->ug = meet(x->ug, g);
            x->nr++;
        };
        auto touchopnd = [&](u32 q) { for (Gad* x : opnd[q]) if (x->opw < 0 && I > (i64)x->i) x->opw = I; };
        auto write = [&](u32 q) {
            touchopnd(q);
            if (gad[q]) gad[q]->impure = true;
            if (clean[q]) { clean[q] = 0; dirty[q] = g; } else dirty[q] = meet(dirty[q], g);
        };
        auto reset = [&](u32 q) {
            Gad* x = gad[q];
            if (x) {
                gad[q] = nullptr;
                if (!g.empty() && !subset(g, dirty[q])) x->impure = true;
                finalize(x, I, true);
            }
            if (!clean[q] && subset(g, dirty[q])) clean[q] = 1;
        };
        switch (o.base) {
            case 0x10: read(o.q[0]); break;                        // Z
            case 0x11: write(o.q[0]); break;                       // X
            case 0x12: reset(o.q[0]); break;                       // R
            case 0x20: read(o.q[0]); read(o.q[1]); break;          // CZ
            case 0x21: read(o.q[0]); write(o.q[1]); break;         // CX
            case 0x22: {                                            // SWAP
                u32 a = o.q[0], b = o.q[1];
                if (g.empty()) {
                    touchopnd(a); touchopnd(b);
                    std::swap(gad[a], gad[b]);
                    if (gad[a]) gad[a]->t = a;
                    if (gad[b]) gad[b]->t = b;
                    std::swap(clean[a], clean[b]);
                    std::swap(dirty[a], dirty[b]);
                } else { read(a); read(b); write(a); write(b); }
            } break;
            case 0x30: nccz++; read(o.q[0]); read(o.q[1]); read(o.q[2]); break;  // CCZ
            case 0x31: {                                            // CCX
                nccx++;
                u32 a = o.q[0], b = o.q[1], t = o.q[2];
                read(a); read(b);
                {   // a second identical CCX with unchanged operands uncomputes the gadget (reversible release)
                    Gad* x = gad[t];
                    if (x && !x->impure && x->opw < 0 && g == x->cg && ((x->a == a && x->b == b) || (x->a == b && x->b == a))) {
                        gad[t] = nullptr;
                        npair++;
                        touchopnd(t);
                        finalize(x, I, true);
                        clean[t] = 1;
                        break;
                    }
                }
                bool fresh = clean[t] && !gad[t];
                write(t);
                if (fresh) {
                    ngad++;
                    Gad* x = new Gad;
                    x->i = I; x->a = a; x->b = b; x->t = t; x->cg = g;
                    gad[t] = x;
                    opnd[a].push_back(x);
                    opnd[b].push_back(x);
                }
            } break;
            case 0x32: read(o.q[0]); read(o.q[1]); read(o.q[2]); write(o.q[1]); write(o.q[2]); break;  // CSWAP
            case 0x40: case 0x41: case 0x42: {                      // BIT_STORE0/1, BIT_INVERT
                u32 b = o.bit;
                ver[b]++;
                wpos[((u64)ver[b] << 32) | b] = I;
                kind[b] = 'S';
            } break;
            case 0x50: {                                            // HMR q -> bit
                u32 b = o.bit;
                ver[b]++;
                wpos[((u64)ver[b] << 32) | b] = I;
                kind[b] = 'H';
                reset(o.q[0]);
            } break;
            case 0x00: break;                                       // NEG
            default:
                if (o.cat == 1) { read(o.q[0]); break; }             // other single-qubit phase (rotation)
                fprintf(stderr, "unknown opcode %u at %llu\n", o.op, (unsigned long long)o.i);
                return 3;
        }
        if ((I & ((1 << 23) - 1)) == 0) fprintf(stderr, "op %lld / %llu\n", (long long)I, (unsigned long long)K.H.nops);
    }
    for (u32 q = 0; q < NQ; q++)
        if (gad[q]) { finalize(gad[q], (i64)K.H.nops, false); gad[q] = nullptr; }
    printf("qubits %u bits %u ops %llu CCX %llu CCZ %llu\n", NQ, NB, (unsigned long long)K.H.nops, (unsigned long long)nccx,
           (unsigned long long)nccz);
    printf("released by a second identical CCX: %llu\n", (unsigned long long)npair);
    printf("AND gadgets %llu  pure released %llu  never read %llu  read only under extra conditions %llu (movable %llu)\n",
           (unsigned long long)ngad, (unsigned long long)npure, (unsigned long long)ndead, (unsigned long long)ncand,
           (unsigned long long)nmov);
    for (auto& kv : hist)
        printf("  extra kinds %-6s movable %d : %llu\n", kv.first.first.c_str(), kv.first.second, (unsigned long long)kv.second);
    printf("estimated mean Toffoli saved (coin bits only, movable): %.2f\n", saving);
    for (auto& s : samples) printf("%s\n", s.c_str());
}

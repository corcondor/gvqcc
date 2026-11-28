#include "joint_work/audit/common.hpp"
L projection(Gate g) {
    // Discard only classical IDs. Quantum operands are bounded by 900.
    assert(g.a < 1024 && g.b < 1024 && g.t < 1024);
    return g.op | (L(g.a) << 8) | (L(g.b) << 18) | (L(g.t) << 28);
}
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    Reader a(argv[1]), b(argv[2]);
    const L cut = 36287888, n = 1024, base = 257;
    vector<L> key;
    L want = 0, pow = 1, h = 0;
    for (L i = 0; i < cut+n/2; ++i) {
        L x = projection(a.read(i));
        if (i >= cut-n/2) { key.push_back(x); want = want*base+x; pow *= base; }
    }
    L ring[n] = {}, matches = 0;
    for (L i = 0; i < b.counts[0]; ++i) {
        auto x = projection(b.read(i));
        auto &y = ring[i%n];
        h = h*base + x - y*pow; y = x;
        if (i+1 >= n && h == want) {
            L j=0;
            while (j<n && ring[(i+1+j)%n] == key[j]) ++j;
            if (j==n) { cout << (i+1-n/2) << '\n'; ++matches; }
        }
    }
    return matches == 1 ? 0 : 3;
}

// Search exact controlled-affine windows by the rank of their relative linear map.
#include <algorithm>
#include <array>
#include <bitset>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace {
constexpr unsigned max_width = 900;
using Row = std::bitset<max_width>;
struct Gate { unsigned op; std::array<unsigned, 3> q; };
struct Window {
    uint64_t first, last;
    unsigned control, paid;
    Row selector;
};

uint64_t little(const uint8_t* p, unsigned n) {
    uint64_t x = 0;
    for (unsigned i = 0; i < n; ++i) x |= uint64_t(p[i]) << (8 * i);
    return x;
}
Row basis(unsigned i) {
    Row result;
    result.set(i);
    return result;
}
unsigned relative_rank(const std::vector<Gate>& region, uint64_t base, const Window& w, unsigned nq) {
    std::array<std::vector<Row>, 2> state;
    for (unsigned value = 0; value < 2; ++value) {
        state[value].resize(nq);
        for (unsigned q = 0; q < nq; ++q)
            if (q != w.control) state[value][q] = basis(q);
        auto xor_wire = [&](unsigned a, unsigned b) {
            state[value][b] ^= state[value][a];
        };
        auto swap_wire = [&](unsigned a, unsigned b) {
            std::swap(state[value][a], state[value][b]);
        };
        // Keep exact affine constants even for wires with nonconstant rows.
        std::vector<bool> parity(nq, false);
        parity[w.control] = value;
        for (uint64_t i = w.first; i <= w.last; ++i) {
            const auto& g = region[i - base];
            const auto [a, b, c] = g.q;
            if (g.op == 0x11) parity[a] = !parity[a];
            if (g.op == 0x21) {
                xor_wire(a, b);
                parity[b] = parity[a] != parity[b];
            }
            if (g.op == 0x22) {
                swap_wire(a, b);
                bool old = parity[a]; parity[a] = parity[b]; parity[b] = old;
            }
            if (g.op == 0x31) {
                bool first = state[value][a].none();
                unsigned pin = first ? a : b, input = first ? b : a;
                if (state[value][pin].any()) throw std::logic_error("uncontrolled CCX");
                if (parity[pin]) {
                    xor_wire(input, c);
                    parity[c] = parity[input] != parity[c];
                }
            }
            if (g.op == 0x32) {
                if (state[value][a].any()) throw std::logic_error("uncontrolled SWAP");
                if (parity[a]) {
                    swap_wire(b, c);
                    bool old = parity[b]; parity[b] = parity[c]; parity[c] = old;
                }
            }
        }
    }
    std::vector<Row> pivots(nq);
    unsigned rank = 0;
    for (unsigned q = 0; q < nq; ++q) {
        Row row = state[0][q] ^ state[1][q];
        for (int j = nq - 1; j >= 0 && row.any(); --j) {
            if (!row.test(j)) continue;
            if (pivots[j].none()) { pivots[j] = row; ++rank; break; }
            row ^= pivots[j];
        }
    }
    return rank;
}
}  // namespace

int main(int argc, char** argv) try {
    if (argc != 3) throw std::runtime_error("usage: controlled_linear_scan input.kmb output.tsv");
    int fd = open(argv[1], O_RDONLY);
    struct stat st {};
    if (fd < 0 || fstat(fd, &st)) throw std::runtime_error("open");
    auto* data = static_cast<const uint8_t*>(mmap(nullptr, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0));
    if (data == MAP_FAILED || st.st_size < 104 || little(data + 16, 4) != 2)
        throw std::runtime_error("expected KMB v2");
    unsigned nq = little(data + 20, 4);
    if (nq > max_width) throw std::runtime_error("wire limit exceeded");
    uint64_t nr = little(data + 28, 4), n = little(data + 32, 8), offset = 104;
    std::array<uint64_t, 12> pos{}, end{};
    for (uint64_t i = 0; i < nr + 11; ++i) {
        if (offset + 16 > uint64_t(st.st_size)) throw std::runtime_error("packet");
        auto type = little(data + offset, 8), len = little(data + offset + 8, 8);
        offset += 16;
        if (type != (i < nr ? 0 : i - nr + 1) || len > uint64_t(st.st_size) - offset)
            throw std::runtime_error("packet extent");
        if (type) { pos[type] = offset; end[type] = offset + len; }
        offset += len;
    }
    auto take = [&](unsigned c, unsigned bytes) {
        if (bytes > end[c] - pos[c]) throw std::runtime_error("column overflow");
        auto v = little(data + pos[c], bytes);
        pos[c] += bytes;
        return v;
    };
    std::vector<Window> windows;
    std::vector<Gate> region;
    uint64_t base = 0, examined = 0, kept = 0, paid_seen = 0, max_paid = 0;
    std::ofstream out(argv[2]);
    out << "first\tlast_exclusive\tcontrol\tpaid\trank\n";
    auto check = [&](const Window& w) {
        if (w.paid < 2) return;
        ++examined;
        max_paid = std::max<uint64_t>(max_paid, w.paid);
        auto rank = relative_rank(region, base, w, nq);
        if (rank < w.paid) {
            ++kept;
            out << w.first << '\t' << w.last + 1 << '\t' << w.control << '\t'
                << w.paid << '\t' << rank << '\n';
        }
    };
    for (uint64_t i = 0; i < n; ++i) {
        unsigned op = take(1, 1), code = op & 127, arity = (op >> 4) & 3;
        Gate g{code, {}};
        for (unsigned j = 0; j < arity; ++j) {
            g.q[j] = take(arity == 3 ? 2 + j : arity == 2 ? 5 + j : 7, 4);
            if (g.q[j] >= nq) throw std::runtime_error("invalid operand");
        }
        if (op & 64) take(8, 4);
        if (op & 128) take(9, 4);
        if (code == 0x13) { take(10, 8); take(10, 8); }
        const auto [a, b, c] = g.q;
        unsigned controls = code == 0x31 ? 2 : code == 0x32 ? 1 : 0;
        if ((op & 128) || (!controls && code != 0x11 && code != 0x21 && code != 0x22)) {
            for (const auto& w : windows) check(w);
            windows.clear();
            region.clear();
            continue;
        }
        if (windows.empty() && controls == 0) continue;
        if (region.empty()) base = i;
        region.push_back(g);
        if (controls) {
            ++paid_seen;
            std::array<bool, 2> found{};
            windows.erase(std::remove_if(windows.begin(), windows.end(), [&](Window& w) {
                for (unsigned j = 0; j < controls; ++j)
                    if (w.selector == basis(g.q[j])) {
                        found[j] = true; w.last = i; ++w.paid; return false;
                    }
                check(w);
                return true;
            }), windows.end());
            for (unsigned j = 0; j < controls; ++j)
                if (!found[j]) windows.push_back({i,i,g.q[j],1,basis(g.q[j])});
        } else {
            for (auto& w : windows) {
                if (code == 0x21 && w.selector.test(b)) w.selector.flip(a);
                if (code == 0x22 && w.selector.test(a) != w.selector.test(b)) {
                    w.selector.flip(a); w.selector.flip(b);
                }
            }
        }
        if (region.size() >= 16384) {
            for (const auto& w : windows) check(w);
            windows.clear();
            region.clear();
        }
    }
    for (const auto& w : windows) check(w);
    std::cout << "{\"operations\":" << n << ",\"paid_seen\":" << paid_seen
              << ",\"windows\":" << examined << ",\"max_paid_in_window\":" << max_paid
              << ",\"rank_reductions\":" << kept << "}\n";
    munmap(const_cast<uint8_t*>(data), st.st_size);
    close(fd);
    return 0;
} catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
}

// Find a basis for the quadratic terms of phase-transparent affine/Toffoli windows.
#include <algorithm>
#include <array>
#include <bitset>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>

namespace {
constexpr unsigned width = 900;
constexpr unsigned capacity = 128;
using Affine = std::bitset<width + 1>;
using ProductMask = std::bitset<capacity>;
using Monomials = std::vector<unsigned>;
struct Wire {
    Affine affine, inverse_column;
    ProductMask products;
    unsigned epoch = 0;
};
struct Product {
    uint64_t at;
    Affine left, right;
    Affine output;
};

uint64_t little(const uint8_t* bytes, unsigned count) {
    uint64_t result = 0;
    for (unsigned i = 0; i < count; ++i) result |= uint64_t(bytes[i]) << (8 * i);
    return result;
}
Monomials quadratic_part(const Affine& left, const Affine& right) {
    std::vector<unsigned> a, b;
    for (unsigned i = 0; i < width; ++i) {
        if (left.test(i)) a.push_back(i);
        if (right.test(i)) b.push_back(i);
    }
    Monomials terms;
    for (const auto i : a) for (const auto j : b) {
        if (i != j) terms.push_back(std::min(i,j) * width + std::max(i,j));
    }
    std::sort(terms.begin(), terms.end());
    Monomials reduced;
    for (const auto term : terms) {
        if (!reduced.empty() && reduced.back() == term) reduced.pop_back();
        else reduced.push_back(term);
    }
    return reduced;
}
std::vector<uint64_t> dependence(const std::vector<Product>& products) {
    std::unordered_map<unsigned, std::pair<Monomials, ProductMask>> pivot;
    std::vector<uint64_t> dependencies;
    for (size_t i = 0; i < products.size(); ++i) {
        auto row = quadratic_part(products[i].left, products[i].right);
        ProductMask combination;
        combination.set(i);
        while (!row.empty()) {
            auto prior = pivot.find(row.back());
            if (prior == pivot.end()) break;
            Monomials difference;
            std::set_symmetric_difference(row.begin(), row.end(), prior->second.first.begin(),
                                          prior->second.first.end(), std::back_inserter(difference));
            row.swap(difference);
            combination ^= prior->second.second;
        }
        if (row.empty()) dependencies.push_back(products[i].at);
        else {
            const unsigned leading = row.back();
            pivot.emplace(leading, std::make_pair(std::move(row), combination));
        }
    }
    return dependencies;
}
bool rank_insert(std::array<Affine, width>& pivots, Affine row) {
    for (unsigned i = 0; i < width; ++i) {
        if (!row.test(i)) continue;
        if (pivots[i].none()) {
            pivots[i] = row;
            return true;
        }
        row ^= pivots[i];
    }
    return false;
}
unsigned polar_rank(const std::vector<Product>& products, const std::vector<size_t>& indices) {
    Monomials polynomial;
    for (const auto i : indices) {
        auto update = quadratic_part(products[i].left, products[i].right);
        Monomials next;
        std::set_symmetric_difference(polynomial.begin(), polynomial.end(), update.begin(),
                                      update.end(), std::back_inserter(next));
        polynomial.swap(next);
    }
    std::array<Affine, width> rows{};
    for (const auto monomial : polynomial) {
        const auto a = monomial / width, b = monomial % width;
        rows[a].set(b);
        rows[b].set(a);
    }
    std::array<Affine, width> pivots{};
    unsigned rank = 0;
    for (const auto& row : rows) {
        if (row.any() && rank_insert(pivots, row)) ++rank;
    }
    return rank;
}

bool merges(const Product& a, const Product& b) {
    const std::array<Affine, 3> a_plane{a.left, a.right, a.left ^ a.right};
    const std::array<Affine, 3> b_plane{b.left, b.right, b.left ^ b.right};
    unsigned intersection = 0;
    for (const auto& u : a_plane) for (const auto& v : b_plane)
        intersection += u == v;
    return intersection == 3 || (intersection && a.output == b.output);
}
bool compatible(const Product& a, const Product& b) {
    return ((a.left & b.output).count() % 2 == 0 &&
            (a.right & b.output).count() % 2 == 0 &&
            (b.left & a.output).count() % 2 == 0 &&
            (b.right & a.output).count() % 2 == 0);
}
void scan_stars(const std::vector<Product>& products, uint64_t& tested_input, uint64_t& tested_output,
                uint64_t& input_hits, uint64_t& output_hits, uint64_t& flip_tests,
                uint64_t& flip_hits, std::ostream& stars) {
    std::unordered_map<Affine, std::vector<std::pair<size_t, Affine>>> on_input;
    std::unordered_map<Affine, std::vector<size_t>> on_output;
    for (size_t j = 0; j < products.size(); ++j) {
        auto a = products[j].left, b = products[j].right;
        a.reset(width); b.reset(width);
        const auto sum = a ^ b;
        for (const auto& [selector, other] :
             std::array<std::pair<Affine, Affine>, 3>{{{a,b},{b,a},{sum,a}}}) {
            if (selector.any()) on_input[selector].emplace_back(j, other);
        }
        on_output[products[j].output].push_back(j);
    }
    const auto emit = [&](const char* kind, unsigned rank, const auto& indices) {
        stars << products.front().at << '\t' << products.back().at + 1
              << '\t' << kind << '\t' << rank << '\t';
        for (const auto i : indices) stars << products[i].at << ' ';
        stars << '\n';
    };

    // Try one rank-preserving regrouping followed by contraction with a third atom.
    // Pairwise compatibility makes all three source products commute.
    const auto flip_and_merge = [&](size_t a, size_t b, Product new_a, Product new_b) {
        if (!compatible(products[a], products[b])) return;
        ++flip_tests;
        for (size_t c = 0; c < products.size(); ++c) {
            if (c == a || c == b) continue;
            Product other = products[c];
            other.left.reset(width);
            other.right.reset(width);
            if (!compatible(products[a], other) || !compatible(products[b], other))
                continue;
            if (merges(new_a, other) || merges(new_b, other)) {
                ++flip_hits;
                emit("flip-merge", 2, std::array<size_t,3>{a,b,c});
            }
        }
    };
    for (const auto& [selector, terms] : on_input) {
        if (terms.size() < 2) continue;
        ++tested_input;
        unsigned pivot = 0;
        while (!selector.test(pivot)) ++pivot;
        std::array<Affine, width> rows{}, pivots{};
        for (const auto& [i, other] : terms) {
            auto remainder = other;
            if (remainder.test(pivot)) remainder ^= selector;
            for (unsigned j = 0; j < width; ++j)
                if (products[i].output.test(j)) rows[j] ^= remainder;
        }
        unsigned rank = 0;
        for (const auto& row : rows) {
            if (row.any() && rank_insert(pivots, row)) ++rank;
        }
        if (rank == terms.size()) {
            for (const auto& [i, a] : terms) for (const auto& [j, b] : terms) {
                if (i == j) continue;
                const auto left_output = products[i].output, right_output = products[j].output;
                flip_and_merge(i, j, {products[i].at, selector, a ^ b, left_output},
                               {products[j].at, selector, b, left_output ^ right_output});
            }
        }
        if (rank < terms.size()) {
            ++input_hits;
            std::vector<size_t> indices;
            for (const auto& [i, other] : terms) indices.push_back(i);
            emit("input", rank, indices);
        }
    }
    for (const auto& [direction, indices] : on_output) {
        if (indices.size() < 2) continue;
        ++tested_output;
        unsigned rank = polar_rank(products, indices) / 2;
        if (rank == indices.size()) {
            for (const auto i : indices) for (const auto j : indices) {
                if (i >= j) continue;
                auto a = products[i].left, b = products[i].right;
                auto c = products[j].left, d = products[j].right;
                a.reset(width); b.reset(width); c.reset(width); d.reset(width);
                const std::array<Affine,3> first{a,b,a^b}, second{c,d,c^d};
                for (unsigned x = 0; x < 3; ++x) for (unsigned y = 0; y < 3; ++y)
                    for (unsigned z = 1; z <= 2; ++z) for (unsigned w = 1; w <= 2; ++w)
                        flip_and_merge(i, j,
                            {products[i].at, first[x] ^ second[y], first[(x+z)%3], direction},
                            {products[j].at, second[y], second[(y+w)%3] ^ first[(x+z)%3], direction});
            }
        }
        if (rank < indices.size()) {
            ++output_hits;
            emit("output", rank, indices);
        }
    }
}

}  // namespace

int main(int argc, char** argv) try {
    if (argc != 3) throw std::runtime_error("usage: quadratic_window source.kmb hits.tsv");
    int fd = open(argv[1], O_RDONLY);
    struct stat st {};
    if (fd < 0 || fstat(fd, &st)) throw std::runtime_error("open source");
    auto* data = static_cast<const uint8_t*>(mmap(nullptr, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0));
    if (data == MAP_FAILED || st.st_size < 104 || little(data + 16, 4) != 2)
        throw std::runtime_error("expected KMB v2");
    unsigned nq = little(data + 20, 4);
    if (nq > width) throw std::runtime_error("qubit limit exceeded");
    uint64_t registers = little(data + 28, 4), n = little(data + 32, 8), offset = 104;
    std::array<uint64_t, 12> pos{}, end{};
    for (uint64_t i = 0; i < registers + 11; ++i) {
        if (offset + 16 > uint64_t(st.st_size)) throw std::runtime_error("packet");
        auto type = little(data + offset, 8), len = little(data + offset + 8, 8);
        offset += 16;
        if (type != (i < registers ? 0 : i - registers + 1) || len > uint64_t(st.st_size) - offset)
            throw std::runtime_error("packet extent");
        if (type) { pos[type] = offset; end[type] = offset + len; }
        offset += len;
    }
    auto take = [&](unsigned column, unsigned bytes) {
        if (bytes > end[column] - pos[column]) throw std::runtime_error("column overflow");
        auto val = little(data + pos[column], bytes);
        pos[column] += bytes;
        return val;
    };
    std::ofstream hits(argv[2]);
    hits << "first\tlast_exclusive\tpaid\tovercomplete\tdependent_ops\n";
    std::ofstream stars(std::string(argv[2]) + ".stars");
    stars << "first\tlast_exclusive\ttype\trank\tpaid_ops\n";
    std::vector<Product> products;
    std::array<Wire, width> wires;
    unsigned epoch = 1;
    uint64_t last = 0, paid = 0, covered = 0, windows = 0, largest = 0, saved = 0;
    uint64_t phase_crossed = 0, nonlinear_cut = 0, capped = 0;
    uint64_t input_stars = 0, output_stars = 0, input_hits = 0, output_hits = 0;
    uint64_t flip_tests = 0, flip_hits = 0;
    auto wire = [&](unsigned q) -> Wire& {
        Wire& w = wires.at(q);
        if (w.epoch != epoch) {
            w.epoch = epoch;
            w.affine.reset(); w.affine.set(q);
            w.inverse_column = w.affine;
            w.products.reset();
        }
        return w;
    };
    auto clear = [&]() {
        if (products.size() >= 2) {
            ++windows;
            covered += products.size();
            largest = std::max<uint64_t>(largest, products.size());
            auto removable = dependence(products);
            scan_stars(products, input_stars, output_stars, input_hits, output_hits, flip_tests, flip_hits, stars);
            if (!removable.empty()) {
                saved += removable.size();
                hits << products.front().at << '\t' << last + 1 << '\t' << products.size()
                     << '\t' << removable.size() << '\t';
                for (const auto index : removable) hits << index << ' ';
                hits << '\n';
            }
        }
        products.clear();
        ++epoch;
    };
    for (uint64_t i = 0; i < n; ++i) {
        unsigned op = take(1, 1), code = op & 127, arity = (op >> 4) & 3;
        std::array<unsigned, 3> operand{};
        for (unsigned j = 0; j < arity; ++j) {
            operand[j] = take(arity == 3 ? 2 + j : arity == 2 ? 5 + j : 7, 4);
            if (operand[j] >= nq) throw std::runtime_error("invalid operand");
        }
        if (op & 64) take(8, 4);
        if (op & 128) take(9, 4);
        if (code == 0x13) { take(10, 8); take(10, 8); }
        const auto [a,b,c] = operand;
        const bool is_paid = code == 0x31 || code == 0x32;
        if (is_paid) ++paid;
        if (products.empty() && !is_paid) continue;
        const bool diagonal = code == 0x0 || code == 0x10 || code == 0x20 || code == 0x30;
        if (diagonal) {
            bool transparent = true;
            for (unsigned j = 0; j < arity; ++j)
                if (wire(operand[j]).products.any()) transparent = false;
            if (transparent) { ++phase_crossed; continue; }
        }
        if ((op & 128) || (code != 0x11 && code != 0x21 && code != 0x22 && !is_paid)) {
            clear();
            continue;
        }
        if (is_paid) {
            bool dependent = wire(a).products.any() || (code == 0x31 ?
                wire(b).products.any() : (wire(b).products ^ wire(c).products).any());
            if (dependent || products.size() == capacity) {
                if (dependent) ++nonlinear_cut;
                if (products.size() == capacity) ++capped;
                clear();
            }
            Affine left = wire(a).affine;
            Affine right = wire(b).affine;
            Affine direction = wire(c).inverse_column;
            if (code == 0x32) {
                right ^= wire(c).affine;
                direction ^= wire(b).inverse_column;
            }
            wire(c).products.set(products.size());
            if (code == 0x32) wire(b).products.set(products.size());
            products.push_back({i,left,right,direction});
            last = i;
        }
        if (code == 0x11) wire(a).affine.flip(width);
        if (code == 0x21) {
            wire(b).affine ^= wire(a).affine;
            wire(b).products ^= wire(a).products;
            wire(a).inverse_column ^= wire(b).inverse_column;
        }
        if (code == 0x22) {
            wire(a); wire(b);
            std::swap(wires[a], wires[b]);
        }
    }
    clear();
    std::cout << "{\"operations\":" << n << ",\"paid_seen\":" << paid
              << ",\"multi_windows\":" << windows << ",\"paid_covered\":" << covered
              << ",\"max_paid_in_window\":" << largest << ",\"rank_reduction\":" << saved
              << ",\"phase_gates_crossed\":" << phase_crossed << ",\"nonlinear_cuts\":"
              << nonlinear_cut << ",\"capacity_cuts\":" << capped << ",\"input_stars\":" << input_stars
              << ",\"output_stars\":" << output_stars << ",\"input_rank_reduction\":" << input_hits
              << ",\"output_rank_reduction\":" << output_hits << ",\"reversible_flips_tested\":" << flip_tests
              << ",\"flip_merge_detections\":" << flip_hits << "}\n";
    munmap(const_cast<uint8_t*>(data), st.st_size);
    close(fd);
    return 0;
} catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
}

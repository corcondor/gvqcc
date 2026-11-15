#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <vector>

using Byte = uint8_t;
using Matrix = std::array<Byte, 6>;
using Term = std::array<int, 3>;

constexpr Matrix active = {1, 3, 3, 5, 7, 7};
Matrix frame;
std::array<Byte, 64> forward, inverse;
uint64_t frames = 0, plausible = 0, intersections = 0;

int multiply(int a, int b) {
    int result = 0;
    while (b) {
        if (b & 1) result ^= a;
        b >>= 1;
        a <<= 1;
        if (a & 8) a ^= 11;
    }
    return result;
}

Byte times2(Byte v) {
    return multiply(2, v & 7) | (multiply(2, v >> 3) << 3);
}

uint64_t space(const Matrix& columns) {
    uint64_t values = 1;
    for (const auto col : columns) {
        if (values >> col & 1) continue;
        const uint64_t known = values;
        for (uint64_t remaining = known; remaining; remaining &= remaining - 1) {
            values |= uint64_t{1} << (std::countr_zero(remaining) ^ col);
        }
    }
    return values;
}

Matrix transpose(const Matrix& columns) {
    Matrix out = {};
    for (int j = 0; j < 6; ++j) {
        for (int i = 0; i < 6; ++i) out[i] |= ((columns[j] >> i) & 1) << j;
    }
    return out;
}

Matrix plus_rank_one(Matrix columns, int v, int u) {
    for (int j = 0; j < 6; ++j) if (u >> j & 1) columns[j] ^= v;
    return columns;
}

void expand(std::vector<Term>& terms, int factor, const Matrix& columns) {
    std::array<Byte, 4> support = {};
    int size = 1;
    for (const auto col : columns) {
        bool already = false;
        for (int i = 0; i < size; ++i) already |= support[i] == col;
        if (already) continue;
        if (size >= 4) std::abort();
        for (int i = 0; i < size; ++i) support.at(i + size) = support[i] ^ col;
        size *= 2;
    }
    for (int t = 1; t < size; t <<= 1) {
        int form = 0;
        for (int j = 0; j < 6; ++j) {
            for (int i = 0; i < size; ++i) if (support[i] == columns[j] && (i & t)) form |= 1 << j;
        }
        terms.push_back({factor, form, support[t]});
    }
}

int parity(int v) { return std::popcount(unsigned(v)) & 1; }

bool inspect() {
    ++frames;
    Matrix m, n, p;
    for (int j = 0; j < 6; ++j) {
        const Byte b = times2(frame[j]);
        m[j] = inverse[b] ^ ((active[j] & 2) ? 1 << j : 0);
        n[j] = inverse[times2(b)] ^ ((active[j] & 4) ? 1 << j : 0);
        p[j] = m[j] ^ n[j];
    }
    if (std::popcount(space(m)) > 16) return false;
    const uint64_t nc = space(n), pc = space(p);
    if (std::popcount(nc) != 8 || std::popcount(pc) != 8) return false;
    ++plausible;
    const uint64_t cols = nc & pc & ~uint64_t{1};
    if (!cols) return false;
    const uint64_t rows = space(transpose(n)) & space(transpose(p)) & ~uint64_t{1};
    if (!rows) return false;
    ++intersections;
    for (uint64_t vs = cols; vs; vs &= vs - 1) {
        int v = std::countr_zero(vs);
        for (uint64_t us = rows; us; us &= us - 1) {
            int u = std::countr_zero(us);
            Matrix q = plus_rank_one(n, v, u);
            Matrix r = plus_rank_one(p, v, u);
            if (std::popcount(space(q)) != 4 || std::popcount(space(r)) != 4) continue;
            std::vector<Term> terms;
            for (int i = 0; i < 6; ++i) terms.push_back({active[i], 1 << i, 1 << i});
            terms.push_back({4, u, v});
            expand(terms, 6, q);
            expand(terms, 2, r);
            for (auto& [left, right, out] : terms) {
                int converted = 0;
                for (int i = 0; i < 6; ++i) converted |= parity(right & inverse[1 << i]) << i;
                right = converted;
                out = forward[out];
            }
            for (int a = 0; a < 8; ++a) {
                for (int yz = 0; yz < 64; ++yz) {
                    int actual = 0;
                    for (const auto& [x, y, w] : terms) if (parity(a & x) && parity(yz & y)) actual ^= w;
                    if (actual != (multiply(a, yz & 7) | (multiply(a, yz >> 3) << 3))) std::abort();
                }
            }
            std::cout << "{\"products\":[";
            for (size_t i = 0; i < terms.size(); ++i) {
                const auto& [a, b, c] = terms[i];
                if (i) std::cout << ',';
                std::cout << '[' << a << ',' << b << ',' << c << ']';
            }
            std::cout << "],\"frames\":" << frames << ",\"truth_table_cases\":512}\n";
            return true;
        }
    }
    return false;
}

bool enumerate(int depth, bool independent_over_field, uint64_t known) {
    if (depth == 6) return inspect();
    const int width = 1 << depth;
    for (int w = 1; w < 64; ++w) {
        if (known >> w & 1) continue;
        if (!independent_over_field && w >= 8 && w != 8) continue;
        frame[depth] = w;
        uint64_t span = known;
        for (int i = 0; i < width; ++i) {
            Byte next = forward[i] ^ w;
            forward[i + width] = next;
            inverse[next] = i + width;
            span |= uint64_t{1} << next;
        }
        if (enumerate(depth + 1, independent_over_field || w >= 8, span)) return true;
    }
    return false;
}

int main() {
    frame[0] = forward[1] = inverse[1] = 1;
    if (!enumerate(1, false, 3)) {
        std::cout << "{\"products\":null,\"frames\":" << frames << ",\"plausible\":" << plausible
                  << ",\"nonzero_row_and_column_intersections\":" << intersections << "}\n";
    }
}

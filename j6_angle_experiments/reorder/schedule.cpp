// Search legal disjoint-edge schedules with paired-factorization costs.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

constexpr int edges = 75;
constexpr int batch_width = 6;
constexpr int padded = 78;
constexpr int zero_word = 75;
using Schedule = std::array<int, edges>;

int cost(const Schedule &order, const int pair_cost[edges + 1][edges + 1]) {
    int score = 0;
    for (int pos = 0; pos != padded; ++pos) {
        int current = pos < edges ? order[pos] : zero_word;
        int previous = pos >= batch_width ? order[pos - batch_width] : zero_word;
        score += pair_cost[current][previous];
    }
    return score;
}

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    std::ifstream source(argv[1]);
    int count;
    source >> count;
    if (count != edges) return 2;
    bool before[edges][edges] = {};
    for (int child = 0; child < edges; ++child) {
        uint64_t masks[2];
        source >> masks[0] >> masks[1];
        for (int parent = 0; parent < child; ++parent) {
            if ((masks[parent / 64] >> (parent % 64)) & 1) {
                before[parent][child] = true;
                for (int ancestor = 0; ancestor < parent; ++ancestor) {
                    before[ancestor][child] |= before[ancestor][parent];
                }
            }
        }
    }
    int pair_cost[edges + 1][edges + 1];
    for (auto &row : pair_cost)
        for (int &entry : row) source >> entry;
    if (!source) return 2;
    const int64_t proposals = std::stoll(argv[2]);
    std::mt19937_64 random(std::stoull(argv[3]));
    Schedule best;
    std::iota(best.begin(), best.end(), 0);
    int initial_cost = cost(best, pair_cost);
    int best_cost = initial_cost;
    auto current = best;
    int current_cost = best_cost;
    size_t legal = 0;
    size_t accepted = 0;
    for (int64_t step = 0; step < proposals; ++step) {
        constexpr int period = 300000;
        if (step % period == 0) {
            current = best;
            current_cost = best_cost;
        }
        auto trial = current;
        const int i = random() % edges;
        const int j = random() % edges;
        if (i == j) continue;
        bool valid = true;
        for (int k = std::min(i,j); k <= std::max(i,j); ++k) {
            if (k == i) continue;
            if (i < j ? before[current[i]][current[k]] : before[current[k]][current[i]]) {
                valid = false;
                break;
            }
        }
        if (!valid) continue;
        ++legal;
        if (i < j) std::rotate(trial.begin()+i,trial.begin()+i+1,trial.begin()+j+1);
        else std::rotate(trial.begin()+j,trial.begin()+i,trial.begin()+i+1);
        const int objective = cost(trial,pair_cost);
        const double cooling = 1.0 - static_cast<double>(step % period) / period;
        const double temperature = 0.07 + 3.0 * cooling * cooling;
        if (objective <= current_cost ||
            std::generate_canonical<double,53>(random) < std::exp((current_cost-objective)/temperature)) {
            ++accepted;
            current = trial;
            current_cost = objective;
            if (objective < best_cost) {
                best = current;
                best_cost = objective;
            }
        }
    }
    std::cout << "{\"initial_ccx_rank_sum\":"<<initial_cost << ",\"best_ccx_rank_sum\":"<<best_cost
              << ",\"proposals\":"<<proposals<<",\"legal_proposals\":"<<legal<<",\"accepts\":"<<accepted
              << ",\"permutation\":[";
    for (int i = 0; i < edges; ++i) {
        std::cout << (i == 0 ? "" : ",") << best[i];
    }
    std::cout << "]}\n";
}

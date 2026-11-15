#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <queue>
#include <tuple>
#include <unordered_map>
#include <vector>

using Mask = std::array<uint64_t, 5>;
using Dependency = std::array<uint64_t, 2>;

struct Pair {
    int first, second;
    Mask cover{};
    bool initial, terminal;
};

struct State {
    Mask remaining{};
    int id;
    bool operator==(const State&) const = default;
};

struct Hash {
    size_t operator()(const State& s) const {
        uint64_t h = s.id;
        for (uint64_t w : s.remaining)
            h ^= (w + 0x9e3779b97f4a7c15ull + (h << 6) + (h >> 2));
        return h;
    }
};

struct Record {
    State state;
    int paid, parent;
};
using Key = std::tuple<int,int,int,int>;

int main() {
    int n, terms, width, weight, initial_best;
    if (!(std::cin >> n >> terms >> width >> weight >> initial_best))
        return 1;
    const int words = (terms + 63) / 64;
    if (words > 5 || n >= 65535)
        return 2;
    std::vector<Pair> pairs(n);
    for (Pair& p : pairs) {
        std::cin >> p.first >> p.second >> p.initial >> p.terminal;
        for (int w = 0; w < words; ++w)
            std::cin >> p.cover[w];
    }
    std::array<std::vector<Dependency>, 126> recipes;
    int recipe_lanes;
    std::cin >> recipe_lanes;
    for (int i = 0; i < recipe_lanes; ++i) {
        int lane, size;
        std::cin >> lane >> size;
        auto& deps = recipes.at(lane);
        deps.resize(size);
        for (auto& d : deps)
            std::cin >> d[0] >> d[1];
    }

    auto gate_ok = [&](int q, Dependency avoid) {
        for (const auto& d : recipes[q])
            if (!(d[0] & avoid[0]) && !(d[1] & avoid[1]))
                return true;
        return false;
    };
    auto member = [](const Pair& p, int q) { return p.first == q || p.second == q; };
    auto avoid_pair = [](Dependency& m, const Pair& p) {
        for (int q : {p.first, p.second})
            m[q / 64] |= uint64_t(1) << (q % 64);
    };
    auto cost = [&](int i, int j) {
        const auto& a = pairs[i]; const auto& b = pairs[j];
        return int(!member(b, a.first)) + int(!member(b, a.second));
    };
    std::vector<std::vector<std::pair<uint16_t,uint8_t>>> edges(n);
    for (int i = 0; i < n; ++i) {
        for (int j = i; j < n; ++j) {
            const auto& a = pairs[i]; const auto& b = pairs[j];
            Dependency avoid{};
            avoid_pair(avoid, a); avoid_pair(avoid, b);
            if ((!member(b, a.first) && !gate_ok(a.first, avoid)) ||
                (!member(b, a.second) && !gate_ok(a.second, avoid)) ||
                (!member(a, b.first) && !gate_ok(b.first, avoid)) ||
                (!member(a, b.second) && !gate_ok(b.second, avoid)))
                continue;
            const int d = cost(i, j);
            edges[i].emplace_back(j, d);
            if (i != j)
                edges[j].emplace_back(i, d);
        }
    }

    // Minimum cost to any terminal, allowing intermediate states with no products.
    std::priority_queue<std::pair<int,int>, std::vector<std::pair<int,int>>,
                        std::greater<>> distance_queue;
    std::vector<int> distance(n, 100000), end_next(n, -1);
    for (int i = 0; i < n; ++i) {
        if (pairs[i].terminal) {
            distance[i] = 0;
            distance_queue.emplace(0, i);
        }
    }
    while (!distance_queue.empty()) {
        const auto [d, i] = distance_queue.top();
        distance_queue.pop();
        if (d != distance[i])
            continue;
        for (const auto& [j, weight] : edges[i]) {
            if (d + weight < distance[j]) {
                distance[j] = d + weight;
                end_next[j] = i;
                distance_queue.emplace(distance[j], j);
            }
        }
    }

    Mask all{};
    for (int i = 0; i < terms; ++i)
        all[i / 64] |= uint64_t(1) << (i % 64);
    std::vector<int> initial;
    for (int i = 0; i < n; ++i)
        if (pairs[i].initial && distance[i] < 100000)
            initial.push_back(i);
    auto count = [words](const Mask& m) {
        int c = 0;
        for (int i = 0; i < words; ++i)
            c += std::popcount(m[i]);
        return c;
    };
    std::sort(initial.begin(), initial.end(), [&](int a, int b) {
        return std::tuple(-count(pairs[a].cover), distance[a], a) <
               std::tuple(-count(pairs[b].cover), distance[b], b);
    });
    std::vector<Record> history;
    std::vector<int> beam;
    for (int i : initial) {
        history.push_back({{all, i}, 0, -1});
        beam.push_back(history.size() - 1);
        if (int(beam.size()) == width)
            break;
    }

    int best = initial_best, best_end = -1, best_parent = -1;
    for (int depth = 0; depth < terms && !beam.empty(); ++depth) {
        // Restore only the best width states, replacing duplicates with better parents.
        std::unordered_map<State, int, Hash> best_state;
        std::priority_queue<std::pair<Key,int>> queue;
        std::vector<Record> candidates;
        int accepted = 0;
        auto clear_stale = [&] {
            while (!queue.empty()) {
                const int k = queue.top().second;
                const auto p = best_state.find(candidates[k].state);
                if (p != best_state.end() && p->second == k)
                    break;
                queue.pop();
            }
        };
        for (int base : beam) {
            const auto& root = history[base];
            for (const auto& [j, step] : edges[root.state.id]) {
                const int paid = root.paid + step;
                if (paid + distance[j] >= best)
                    continue;
                State s{{}, j};
                bool changed = false;
                for (int w = 0; w < words; ++w) {
                    s.remaining[w] = root.state.remaining[w] & ~pairs[j].cover[w];
                    changed |= s.remaining[w] != root.state.remaining[w];
                }
                if (!changed)
                    continue;
                const int left = count(s.remaining);
                if (left == 0) {
                    best = paid + distance[j];
                    best_end = j;
                    best_parent = base;
                    continue;
                }
                const Key key{paid * 1000 + left * weight, left, distance[j], j};
                auto old = best_state.find(s);
                if (old != best_state.end() && candidates[old->second].paid <= paid)
                    continue;
                if (old == best_state.end() && accepted == width) {
                    clear_stale();
                    if (!(key < queue.top().first))
                        continue;
                    best_state.erase(candidates[queue.top().second].state);
                    queue.pop();
                    --accepted;
                }
                if (old == best_state.end())
                    ++accepted;
                const int k = candidates.size();
                candidates.push_back({s, paid, base});
                best_state[s] = k;
                queue.emplace(key, k);
            }
        }
        beam.clear();
        while (true) {
            clear_stale();
            if (queue.empty())
                break;
            const Record& record = candidates[queue.top().second];
            history.push_back(record);
            beam.push_back(history.size() - 1);
            queue.pop();
        }
        std::reverse(beam.begin(), beam.end());
    }
    if (best_end < 0) {
        std::cout << "no improvement\n";
        return 0;
    }
    std::vector<int> path;
    for (int k = best_parent; k >= 0; k = history[k].parent)
        path.push_back(history[k].state.id);
    std::reverse(path.begin(), path.end());
    const int start = path.front();
    path.erase(path.begin());
    path.push_back(best_end);
    int terminal = best_end;
    while (end_next[terminal] >= 0)
        terminal = end_next[terminal];
    std::cout << best << ' ' << start << ' ' << terminal << '\n';
    for (int i : path)
        std::cout << i << ' ';
    for (int i = end_next[best_end]; i >= 0 && i != terminal; i = end_next[i])
        std::cout << i << ' ';
    std::cout << '\n';
}

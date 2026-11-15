// Discover exact rematerialization gaps for zero-initialized scratch wires.
// At each gap, the wire is a quadratic expression in the live controls at
// each endpoint. Follow basis changes along a gap when the form stays small.
#define main endpoint_relaxation_main
#include "../score28_dqi/phase_schedule.cpp"
#undef main
#include <bitset>
#include <set>

namespace {
constexpr unsigned no_control = 0xffff;
constexpr unsigned max_terms = 24;
using Term = array<unsigned, 2>;
struct Polynomial {
    bool known = false;
    set<Term> terms;
};
struct Gap {
    uint64_t begin = 0;
    set<Term> initial;
};
}

int main(int argc, char** argv) {
  try {
    if (argc != 4) throw runtime_error("usage KMB ABI_WIDTH OUTPUT.tsv");
    Tape tape(argv[1]);
    const unsigned abi = stoul(argv[2]);
    if (abi > tape.nq || tape.nq >= no_control) throw runtime_error("invalid ABI");
    vector<Polynomial> polynomials(tape.nq);
    vector<Gap> gaps(tape.nq);
    vector<set<unsigned>> readers(tape.nq);
    vector<set<unsigned>> dependencies(tape.nq);
    ofstream output(argv[3]);
    output << "begin\tend\tq\tquadratics\tinitial_terms\tfinal_terms\n";
    uint64_t count = 0, quadratic_free = 0, widest = 0;
    unsigned depth = 0;

    auto finish_gap = [&](unsigned q, uint64_t stop) {
        auto& gap = gaps[q];
        if (gap.initial.empty()) return;
        if (stop >= gap.begin + 4) {
            const auto& final = polynomials[q].terms;
            unsigned paid = 0;
            for (const auto& term : final) paid += term[1] != no_control;
            output << gap.begin << '\t' << stop << '\t' << q << '\t' << paid << '\t';
            for (const auto [a,b] : gap.initial) output << a << ',' << b << ';';
            output << '\t';
            for (const auto [a,b] : final) output << a << ',' << b << ';';
            output << '\n';
            ++count;
            quadratic_free += paid == 0;
            widest = max(widest, stop-gap.begin);
        }
        gap.initial.clear();
    };
    auto detach = [&](unsigned q) {
        for (const auto control : dependencies[q]) readers[control].erase(q);
        dependencies[q].clear();
    };
    auto assign = [&](unsigned q, Polynomial value) {
        if (q < abi) return;
        detach(q);
        auto& p = polynomials[q];
        p = std::move(value);
        if (!p.known) return;
        for (const auto& term : p.terms) {
            for (auto control : term) {
                if (control == no_control) continue;
                if (control == q) throw runtime_error("self-dependent polynomial");
                readers[control].insert(q);
                dependencies[q].insert(control);
            }
        }
    };
    auto overwrite = [&](unsigned control, uint64_t pos) {
        while (!readers[control].empty()) {
            const auto q = *readers[control].begin();
            finish_gap(q, pos);
            assign(q, {});
        }
    };
    auto toggle = [](set<Term>& terms, const Term& term) {
        if (!terms.erase(term)) terms.insert(term);
    };
    auto conjugate = [&](unsigned target, Term delta, uint64_t pos) {
        // Writing target ^= delta changes the basis in which scratch values
        // are described. Every dependent form is pulled back by that XOR.
        vector<unsigned> affected(readers[target].begin(), readers[target].end());
        for (const auto q : affected) {
            auto original = polynomials[q];
            auto result = original;
            for (auto term : original.terms) {
                if (term[0] != target && term[1] != target) continue;
                array<unsigned,3> factors{delta[0], delta[1],
                                          term[0] == target ? term[1] : term[0]};
                sort(factors.begin(), factors.end());
                const auto stop = unique(factors.begin(), factors.end());
                auto used = find(factors.begin(), stop, no_control) - factors.begin();
                if (used > 2 || find(factors.begin(), stop, q) != stop) {
                    result = {};
                    break;
                }
                toggle(result.terms, {used ? factors[0] : no_control,
                                      used == 2 ? factors[1] : no_control});
            }
            if (result.terms.size() > max_terms) result = {};
            if (!result.known || result.terms.empty()) finish_gap(q, pos);
            assign(q, std::move(result));
        }
    };
    auto rename_two = [&](Polynomial value, unsigned p, unsigned q) {
        Polynomial renamed{value.known, {}};
        for (auto term : value.terms) {
            for (auto& factor : term)
                if (factor == p) factor = q;
                else if (factor == q) factor = p;
            if (term[0] > term[1]) swap(term[0], term[1]);
            renamed.terms.insert(term);
        }
        return renamed;
    };
    auto open_gap = [&](unsigned q, uint64_t pos) {
        if (q < abi || depth) return;
        const auto& p = polynomials[q];
        if (!p.known || p.terms.empty()) return;
        gaps[q] = {pos, p.terms};
    };
    for (unsigned q = abi; q < tape.nq; ++q) assign(q, {true, {}});
    for (uint64_t pos = 0; pos < tape.n; ++pos) {
        const auto op = tape.step();
        if (op.code == 0x81) {
            if (!depth)
                for (unsigned q = abi; q < tape.nq; ++q) finish_gap(q, pos);
            ++depth;
            continue;
        }
        if (op.code == 0x01) {
            if (!depth) throw runtime_error("unbalanced classical scope");
            if (!--depth)
                for (unsigned q = abi; q < tape.nq; ++q) open_gap(q, pos + 1);
            continue;
        }
        const auto [p,q,r] = op.qubits;
        for (unsigned i = 0; i < op.count; ++i) finish_gap(op.qubits[i], pos);
        const bool unconditional = depth == 0 && op.cond < 0;
        if (op.base == 0x50 || op.base == 0x12) {
            overwrite(p, pos);
            assign(p, {unconditional, {}});
        } else if (op.base == 0x22 || op.base == 0x32) {
            const unsigned one = op.base == 0x22 ? p : q;
            const unsigned two = op.base == 0x22 ? q : r;
            if (!unconditional || op.base != 0x22) {
                overwrite(one, pos);
                overwrite(two, pos);
                assign(one, {});
                assign(two, {});
            } else {
                auto a = rename_two(polynomials[one], one, two);
                auto b = rename_two(polynomials[two], one, two);
                set<unsigned> affected = readers[one];
                affected.insert(readers[two].begin(), readers[two].end());
                for (const auto q : affected)
                    if (q != one && q != two)
                        assign(q, rename_two(polynomials[q], one, two));
                assign(one, std::move(b));
                assign(two, std::move(a));
            }
        } else if (op.base == 0x11 || op.base == 0x21 || op.base == 0x31) {
            const unsigned target = op.qubits[op.count - 1];
            Term term{no_control, no_control};
            if (op.base == 0x21) term[0] = p;
            if (op.base == 0x31) term = {min(p,q), max(p,q)};
            if (unconditional) conjugate(target, term, pos);
            else overwrite(target, pos);
            if (target >= abi) {
                auto value = polynomials[target];
                if (!unconditional) value = {};
                if (value.known) {
                    toggle(value.terms, term);
                    if (value.terms.size() > max_terms) value = {};
                }
                assign(target, std::move(value));
            }
        } else if (op.count && op.base != 0x10 && op.base != 0x20 && op.base != 0x30) {
            throw runtime_error("unhandled quantum instruction");
        }
        for (unsigned i = 0; i < op.count; ++i) open_gap(op.qubits[i], pos + 1);
    }
    if (depth) throw runtime_error("unbalanced classical scope");
    for (unsigned q = abi; q < tape.nq; ++q) finish_gap(q, tape.n);
    cout << "{\"ops\":" << tape.n << ",\"gaps\":" << count
         << ",\"affine_gaps\":" << quadratic_free << ",\"longest_gap\":" << widest << "}\n";
    return 0;
  } catch (const exception& error) {
    cerr << error.what() << '\n';
    return 1;
  }
}

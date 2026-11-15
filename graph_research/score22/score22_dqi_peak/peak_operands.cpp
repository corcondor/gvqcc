// Enumerate per-interval reads and writes of scratch operands in the pinned
// production KMB. Treat syntactically conditional writes as possible writes.
#define main endpoint_schedule_main
#include "../score28_dqi/phase_schedule.cpp"
#undef main

namespace {
struct Span {
    uint64_t begin, end;
};

void print_qubits(ostream& out, const vector<uint64_t>& counts, unsigned begin,
                  bool report_nonzero) {
    bool comma = false;
    for (unsigned q = begin; q < counts.size(); ++q) {
        if (bool(counts[q]) != report_nonzero) continue;
        if (comma) out << ',';
        out << q;
        comma = true;
    }
}

bool write_operand(const Op& op, unsigned index) {
    switch (op.base) {
        case 0x11: case 0x12: case 0x21: case 0x31: case 0x50:
            return index + 1 == op.count;
        case 0x22: case 0x32:
            return index + 2 >= op.count;
        default:
            return false;
    }
}
}

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw runtime_error("usage KMB PEAK889.tsv OUTPUT.tsv");
        Tape tape(argv[1]);
        if (tape.nq != 889) throw runtime_error("expected 889 physical qubits");
        ifstream input(argv[2]);
        if (!input) throw runtime_error("open peak list");
        vector<Span> spans;
        unsigned width;
        Span range;
        while (input >> range.begin >> range.end >> width) {
            if (width != tape.nq || range.begin >= range.end || range.end > tape.n ||
                (!spans.empty() && range.begin <= spans.back().end))
                throw runtime_error("bad peak list");
            spans.push_back(range);
        }
        if (spans.empty()) throw runtime_error("empty peak list");

        ofstream output(argv[3]);
        if (!output) throw runtime_error("open result");
        output << "start\tstop_exclusive\tscratch_touched\tscratch_written\tscratch_idle\n";
        vector<uint64_t> touched(tape.nq), written(tape.nq), total_touched(tape.nq),
                         total_written(tape.nq), touched_middle(tape.nq), writes_middle(tape.nq);
        unsigned abi = 840;
        uint64_t examined = 0;
        auto next = spans.begin();
        for (uint64_t pos = 0; pos < tape.n; ++pos) {
            const auto op = tape.step();
            const bool middle = pos >= spans.front().begin && pos < spans.back().end;
            const bool in_peak = next != spans.end() && pos >= next->begin && pos < next->end;
            for (unsigned j = 0; j < op.count; ++j) {
                unsigned q = op.qubits[j];
                bool is_write = write_operand(op, j);
                if (middle) {
                    ++touched_middle[q];
                    writes_middle[q] += is_write;
                }
                if (in_peak) {
                    ++touched[q];
                    written[q] += is_write;
                    ++total_touched[q];
                    total_written[q] += is_write;
                }
            }
            if (!in_peak) continue;
            ++examined;
            if (pos + 1 == next->end) {
                output << next->begin << '\t' << next->end << '\t';
                print_qubits(output, touched, abi, true);
                output << '\t';
                print_qubits(output, written, abi, true);
                output << '\t';
                print_qubits(output, touched, abi, false);
                output << '\n';
                fill(touched.begin(), touched.end(), 0);
                fill(written.begin(), written.end(), 0);
                ++next;
            }
        }
        if (next != spans.end()) throw runtime_error("unvisited peak");
        cout << "{\"peak_positions\":" << examined << ",\"per_scratch_wire\":[";
        for (unsigned q = abi; q < tape.nq; ++q) {
            if (q != abi) cout << ',';
            cout << "{\"q\":" << q << ",\"touches_at_peak\":" << total_touched[q]
                 << ",\"writes_at_peak\":" << total_written[q]
                 << ",\"touches_between_first_and_last_peak\":" << touched_middle[q]
                 << ",\"writes_between_first_and_last_peak\":" << writes_middle[q] << '}';
        }
        cout << "]}\n";
        return 0;
    } catch (const exception& error) {
        cerr << error.what() << '\n';
        return 1;
    }
}

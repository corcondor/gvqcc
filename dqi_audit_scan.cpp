// KMB v2 column-stream scanner. Run through gvqcc_dqi_audit.py, which
// validates the full binary format before this conservative state analysis.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;

static uint64_t le(const unsigned char* p, int n) {
    uint64_t value = 0;
    for (int k = 0; k < n; ++k) value |= uint64_t(p[k]) << (8 * k);
    return value;
}
static uint64_t number(const string& s) {
    if (s.empty() || s[0] == '-') throw runtime_error("Expected a nonnegative integer");
    size_t end = 0;
    auto value = stoull(s, &end);
    if (end != s.size()) throw runtime_error("Invalid integer");
    return value;
}
struct Column {
    array<char, 65536> buffer{};
    ifstream file;
    uint64_t length, used = 0;
    Column(const string& path, uint64_t offset, uint64_t count): length(count) {
        file.rdbuf()->pubsetbuf(buffer.data(), buffer.size());
        file.open(path, ios::binary);
        if (!file) throw runtime_error("Cannot open KMB column");
        file.seekg(offset);
        if (!file) throw runtime_error("Cannot seek KMB column");
    }
    void read(unsigned char* p, size_t n) {
        if (n > length - used) throw runtime_error("KMB column exhausted");
        file.read(reinterpret_cast<char*>(p), n);
        if (!file) throw runtime_error("Truncated KMB column");
        used += n;
    }
    uint64_t next(int n) {
        unsigned char p[8];
        read(p, n);
        return le(p, n);
    }
    void skip(uint64_t n) {
        if (n > length - used) throw runtime_error("KMB column skip past end");
        file.seekg(n, ios::cur);
        if (!file) throw runtime_error("KMB column seek failed");
        used += n;
    }
};
static string hex_bytes(const unsigned char* p, size_t n) {
    const char* digits = "0123456789abcdef";
    string result;
    result.reserve(2 * n);
    for (size_t i = 0; i < n; ++i) {
        result += digits[p[i] >> 4];
        result += digits[p[i] & 15];
    }
    return result;
}
static array<string, 256> op_names() {
    array<string, 256> names{};
    for (auto item : vector<pair<int, string>>{
        {0x00,"NEG"},{0x10,"Z"},{0x11,"X"},{0x12,"R"},{0x13,"Z_POW"},
        {0x50,"HMR"},{0x20,"CZ"},{0x21,"CX"},{0x22,"SWAP"},
        {0x30,"CCZ"},{0x31,"CCX"},{0x32,"CSWAP"},{0x40,"BIT_STORE0"},
        {0x41,"BIT_STORE1"},{0x42,"BIT_INVERT"},{0x07,"DEBUG_PRINT_EMPTY"},
        {0x47,"DEBUG_PRINT_C"},{0x17,"DEBUG_PRINT_Q"}}) {
        names[item.first] = item.second;
        names[item.first | 0x80] = item.second + "_IF";
    }
    names[0x01] = "POP_CONDITION";
    names[0x81] = "PUSH_CONDITION";
    names[0x06] = "INFO_TAG";
    return names;
}
static bool legacy_skipped(int op) {
    int base = op & 0x7f;
    return base == 1 || base == 6 || base == 7 || base == 0x17 || base == 0x47;
}
static void histogram_json(ostream& out, const array<uint64_t, 256>& counts,
                           const array<string, 256>& names) {
    out << '{';
    bool first = true;
    for (int op = 0; op < 256; ++op) if (counts[op]) {
        if (!first) out << ',';
        first = false;
        out << '"' << names[op] << "\":" << counts[op];
    }
    out << '}';
}

int main(int argc, char** argv) {
    try {
        if (argc != 12) throw runtime_error("Use the Python audit wrapper");
        string path = argv[1], out_dir = argv[9];
        uint64_t scratch_start = number(argv[2]);
        bool initial_zero = number(argv[3]) != 0;
        bool legacy_mode = number(argv[4]) != 0;
        set<uint64_t> requested_snapshots;
        string token;
        istringstream snapshot_input(argv[5]);
        while (getline(snapshot_input, token, ',')) if (!token.empty())
            requested_snapshots.insert(number(token));
        uint64_t window_start = number(argv[6]), window_end = number(argv[7]);
        uint64_t window_limit = number(argv[8]);
        uint64_t region_start = number(argv[10]), region_end = number(argv[11]);

        ifstream header_file(path, ios::binary);
        unsigned char h[104];
        header_file.read(reinterpret_cast<char*>(h), 104);
        const unsigned char magic[16] = {
            0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,
            0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
        if (!header_file || !equal(begin(magic), end(magic), h) || le(h+16,4) != 2)
            throw runtime_error("Invalid KMB v2 header");
        uint64_t nq = le(h+20,4), nreg = le(h+28,4), nops = le(h+32,8);
        uint64_t ntags = le(h+88,8), tag_chars = le(h+96,8);
        if (nq > 1000000 || scratch_start > nq || nq - scratch_start > 10000)
            throw runtime_error("Unsupported qubit/scratch range; max 1M qubits, 10K scratch");
        array<uint64_t, 12> offsets{}, lengths{};
        for (uint64_t i = 0; i < nreg + 11; ++i) {
            unsigned char p[16];
            header_file.read(reinterpret_cast<char*>(p), 16);
            if (!header_file) throw runtime_error("Truncated packet header");
            uint64_t kind = le(p,8), size = le(p+8,8);
            uint64_t expected = i < nreg ? 0 : i - nreg + 1;
            if (kind != expected) throw runtime_error("Wrong packet order");
            if (kind) {
                offsets[kind] = uint64_t(header_file.tellg());
                lengths[kind] = size;
            }
            header_file.seekg(size, ios::cur);
            if (!header_file) throw runtime_error("Truncated packet");
        }
        header_file.close();
        array<unique_ptr<Column>, 11> col;
        for (int k = 1; k <= 10; ++k)
            col[k] = make_unique<Column>(path, offsets[k], lengths[k]);
        Column tag_offsets(path, offsets[11] + 8, 8 * ntags);
        Column tag_text(path, offsets[11] + 8 + 8 * ntags, tag_chars);

        auto names = op_names();
        array<uint64_t, 256> counts{}, region_counts{};
        vector<uint8_t> possible(nq, 1), touched(nq, 0);
        vector<int64_t> last_touch(nq - scratch_start, -1);
        if (initial_zero) fill(possible.begin() + scratch_start, possible.end(), 0);
        uint64_t possible_count = initial_zero ? 0 : nq - scratch_start;
        uint64_t touched_count = 0, peak_possible = possible_count, peak_touched = 0;
        int64_t peak_possible_op = -1, peak_touched_op = -1;
        uint64_t legacy_index = 0, depth = 0, max_depth = 0, empty_pops = 0;
        vector<pair<uint64_t, uint64_t>> active_pushes;
        uint64_t explicit_ops = 0, implicit_ops = 0, conditioned_ops = 0;
        uint64_t region_peak_possible = 0, region_peak_touched = 0, region_ops = 0;
        uint64_t window_written = 0, window_eligible = 0, stage_written = 0, peaks_written = 0;
        uint64_t stages_seen = 0, previous_tag_end = 0, stage_length = 0;
        int64_t stage_index = -1;
        string stage_hex, current_angle_hex, current_info_hex;
        uint64_t current_info_length = 0;
        ofstream events(out_dir + "/events.jsonl", ios::binary);
        if (!events) throw runtime_error("Cannot create events.jsonl");

        auto set_possible = [&](uint64_t q, bool value) {
            if (q >= nq) throw runtime_error("Qubit ID out of bounds");
            if (q >= scratch_start && bool(possible[q]) != value) {
                if (value) ++possible_count; else --possible_count;
            }
            possible[q] = value;
        };
        auto set_touched = [&](uint64_t q, bool value) {
            if (q >= scratch_start && bool(touched[q]) != value) {
                if (value) ++touched_count; else --touched_count;
            }
            touched[q] = value;
        };
        auto stage_json = [&](ostream& out) {
            out << "{\"info_tag_index\":" << stage_index
                << ",\"byte_length\":" << stage_length
                << ",\"prefix_hex\":\"" << stage_hex << "\"}";
        };
        auto state_json = [&](ostream& out) {
            out << "{\"possibly_nonzero_count\":" << possible_count
                << ",\"touched_since_unconditional_reset_count\":" << touched_count
                << ",\"possibly_nonzero_qubits\":[";
            bool first = true;
            for (uint64_t q = scratch_start; q < nq; ++q) if (possible[q]) {
                if (!first) out << ',';
                first = false; out << q;
            }
            out << "],\"touched_since_unconditional_reset_qubits\":[";
            first = true;
            for (uint64_t q = scratch_start; q < nq; ++q) if (touched[q]) {
                if (!first) out << ',';
                first = false; out << q;
            }
            out << "],\"last_quantum_touch_kmb_index\":{";
            first = true;
            for (uint64_t q = scratch_start; q < nq; ++q) if (last_touch[q-scratch_start] >= 0) {
                if (!first) out << ',';
                first = false;
                out << '"' << q << "\":" << last_touch[q-scratch_start];
            }
            out << "}}";
        };
        auto event = [&](const string& kind, const string& timing, uint64_t raw,
                         uint64_t legacy, int op, const array<uint64_t,3>& qs,
                         int arity, int64_t bit, int64_t condition) {
            events << "{\"event\":\"" << kind << "\",\"timing\":\"" << timing
                   << "\",\"kmb_index\":" << raw << ",\"legacy_v4_gate_index\":" << legacy
                   << ",\"opcode\":\"" << (op >= 0 ? names[op] : "EOF")
                   << "\",\"condition_stack_depth\":" << depth
                   << ",\"active_pushed_conditions\":[";
            for (size_t k = 0; k < active_pushes.size(); ++k) {
                if (k) events << ',';
                events << "{\"source_bit_id\":" << active_pushes[k].first
                       << ",\"push_kmb_index\":" << active_pushes[k].second << '}';
            }
            events << "],\"quantum_targets\":[";
            for (int k = 0; k < arity; ++k) { if (k) events << ','; events << qs[k]; }
            events << "],\"classical_target\":" << bit << ",\"explicit_condition_bit\":"
                   << condition << ",\"rotation_angle_le_hex\":\"" << current_angle_hex
                   << "\",\"info_tag_payload_prefix_hex\":\"" << current_info_hex
                   << "\",\"info_tag_payload_bytes\":" << current_info_length << ",\"stage\":";
            stage_json(events);
            events << ",\"scratch\":";
            if (kind == "window") {
                events << "{\"possibly_nonzero_count\":" << possible_count
                       << ",\"touched_since_unconditional_reset_count\":" << touched_count << '}';
            } else {
                state_json(events);
            }
            events << "}\n";
        };

        for (uint64_t raw = 0; raw < nops; ++raw) {
            int op = int(col[1]->next(1));
            if (names[op].empty()) throw runtime_error("Unknown opcode");
            int base = op & 0x7f, arity = (op >> 4) & 3;
            array<uint64_t,3> qs{};
            for (int k = 0; k < arity; ++k) {
                int column = arity == 3 ? 2+k : arity == 2 ? 5+k : 7;
                qs[k] = col[column]->next(4);
                if (qs[k] >= nq) throw runtime_error("Qubit ID out of bounds");
            }
            int64_t bit = op & 0x40 ? int64_t(col[8]->next(4)) : -1;
            int64_t condition = op & 0x80 ? int64_t(col[9]->next(4)) : -1;
            current_angle_hex.clear(); current_info_hex.clear(); current_info_length = 0;
            if (base == 0x13) {
                unsigned char angle[16];
                col[10]->read(angle, 16);
                current_angle_hex = hex_bytes(angle, 16);
            }
            if (op == 0x06) {
                uint64_t end = tag_offsets.next(8);
                if (end < previous_tag_end || end > tag_chars)
                    throw runtime_error("Invalid info-tag offset");
                current_info_length = end - previous_tag_end;
                unsigned char prefix[256];
                size_t sample = min<uint64_t>(256, current_info_length);
                tag_text.read(prefix, sample);
                tag_text.skip(current_info_length - sample);
                current_info_hex = hex_bytes(prefix, sample);
                previous_tag_end = end;
            }
            bool skipped = legacy_skipped(op);
            bool selected_index = !legacy_mode || !skipped;
            uint64_t index = legacy_mode ? legacy_index : raw;
            if (selected_index && requested_snapshots.erase(index))
                event("snapshot", "before", raw, legacy_index, op, qs, arity, bit, condition);
            if (selected_index && index >= region_start && index < region_end) {
                region_peak_possible = max(region_peak_possible, possible_count);
                region_peak_touched = max(region_peak_touched, touched_count);
            }

            ++counts[op];
            bool conditioned = condition >= 0 || depth > 0;
            if (!skipped) {
                if (condition >= 0) ++explicit_ops;
                if (depth > 0) ++implicit_ops;
                if (conditioned) ++conditioned_ops;
            }
            // Preserve metadata/control/classical/CX operations in windows.
            // In legacy mode skipped operations share the next legacy gate index.
            if (index >= window_start && index < window_end) {
                ++window_eligible;
                if (window_written < window_limit) {
                    event("window", "before", raw, legacy_index, op, qs, arity, bit, condition);
                    ++window_written;
                }
            }
            if (op == 0x81) {
                if (active_pushes.size() >= 65536)
                    throw runtime_error("Condition stack exceeds supported depth 65536");
                active_pushes.emplace_back(uint64_t(condition), raw);
                ++depth; max_depth = max(max_depth, depth);
            } else if (op == 0x01) {
                if (depth) { --depth; active_pushes.pop_back(); } else ++empty_pops;
            } else if (op == 0x06) {
                stage_length = current_info_length;
                stage_hex = current_info_hex;
                stage_index = int64_t(stages_seen++);
                if (stage_written < 128) {
                    event("info_tag", "after", raw, legacy_index, op, qs, arity, bit, condition);
                    ++stage_written;
                }
            } else if (!skipped) {
                bool reset = base == 0x12 || base == 0x50;
                for (int k = 0; k < arity; ++k) {
                    set_touched(qs[k], !(reset && !conditioned));
                    if (qs[k] >= scratch_start) last_touch[qs[k]-scratch_start] = int64_t(raw);
                }
                if (reset) {
                    if (!conditioned) set_possible(qs[0], false);
                } else if (base == 0x11) {
                    set_possible(qs[0], true);
                } else if (base == 0x21) {
                    set_possible(qs[1], possible[qs[1]] || possible[qs[0]]);
                } else if (base == 0x31) {
                    set_possible(qs[2], possible[qs[2]] || (possible[qs[0]] && possible[qs[1]]));
                } else if (base == 0x22) {
                    bool a = possible[qs[0]], b = possible[qs[1]];
                    set_possible(qs[0], conditioned ? a || b : b);
                    set_possible(qs[1], conditioned ? a || b : a);
                } else if (base == 0x32 && possible[qs[0]]) {
                    bool joined = possible[qs[1]] || possible[qs[2]];
                    set_possible(qs[1], joined); set_possible(qs[2], joined);
                }
                // Z, CZ, CCZ, Z_POW, NEG, and classical instructions do not
                // turn a computational-basis zero into a nonzero qubit.
            }
            if (possible_count > peak_possible) {
                peak_possible = possible_count; peak_possible_op = int64_t(raw);
                if (peaks_written < 64) {
                    event("new_possible_peak", "after", raw, legacy_index, op, qs, arity, bit, condition);
                    ++peaks_written;
                }
            }
            if (touched_count > peak_touched) {
                peak_touched = touched_count; peak_touched_op = int64_t(raw);
            }
            if (selected_index && index >= region_start && index < region_end) {
                ++region_counts[op]; ++region_ops;
                region_peak_possible = max(region_peak_possible, possible_count);
                region_peak_touched = max(region_peak_touched, touched_count);
            }
            if (!skipped) ++legacy_index;
        }
        uint64_t final_index = legacy_mode ? legacy_index : nops;
        current_angle_hex.clear(); current_info_hex.clear(); current_info_length = 0;
        if (requested_snapshots.erase(final_index))
            event("snapshot", "before", nops, legacy_index, -1, {}, 0, -1, -1);
        for (int k = 1; k <= 10; ++k)
            if (col[k]->used != col[k]->length) throw runtime_error("Unconsumed column data");
        if (stages_seen != ntags || previous_tag_end != tag_chars)
            throw runtime_error("Unconsumed info-tag data");
        events.flush();
        if (!events) throw runtime_error("Could not write events");

        ofstream result(out_dir + "/scan.json");
        result << "{\"schema\":\"dqi-conservative-audit-v1\",\"num_qubits\":" << nq
               << ",\"scratch_start\":" << scratch_start << ",\"scratch_count\":" << nq-scratch_start
               << ",\"scratch_initial\":\"" << (initial_zero ? "zero" : "unknown")
               << "\",\"index_mode\":\"" << (legacy_mode ? "legacy-v4" : "kmb")
               << "\",\"num_kmb_operations\":" << nops
               << ",\"num_legacy_v4_gate_operations\":" << legacy_index
               << ",\"opcode_histogram\":";
        histogram_json(result, counts, names);
        result << ",\"condition_tracking\":{\"max_stack_depth\":" << max_depth
               << ",\"final_stack_depth\":" << depth << ",\"empty_stack_pop_noops\":" << empty_pops
               << ",\"explicit_condition_operations\":" << explicit_ops
               << ",\"inside_condition_stack_operations\":" << implicit_ops
               << ",\"conditioned_operations_union\":" << conditioned_ops
               << "},\"peak_possibly_nonzero_scratch\":" << peak_possible
               << ",\"peak_possibly_nonzero_first_after_kmb_index\":" << peak_possible_op
               << ",\"peak_touched_since_unconditional_reset_scratch\":" << peak_touched
               << ",\"peak_touched_first_after_kmb_index\":" << peak_touched_op
               << ",\"window\":{\"start_inclusive\":" << window_start << ",\"end_exclusive\":" << window_end
               << ",\"eligible_operations\":" << window_eligible << ",\"recorded\":" << window_written
               << ",\"excluded_gate_families\":[]}"
               << ",\"region\":{\"start_inclusive\":" << region_start << ",\"end_exclusive\":" << region_end
               << ",\"operation_count\":" << region_ops << ",\"peak_possibly_nonzero\":" << region_peak_possible
               << ",\"peak_touched_since_unconditional_reset\":" << region_peak_touched
               << ",\"opcode_histogram\":";
        histogram_json(result, region_counts, names);
        result << "},\"info_tags_seen\":" << stages_seen << ",\"info_tag_events_recorded\":" << stage_written
               << ",\"missing_snapshot_indices\":[";
        bool first = true;
        for (auto i : requested_snapshots) { if (!first) result << ','; first = false; result << i; }
        result << "],\"final_scratch\":";
        state_json(result);
        result << "}\n";
        result.flush();
        if (!result) throw runtime_error("Could not write scan summary");
        return 0;
    } catch (const exception& e) {
        cerr << "dqi_audit_scan: " << e.what() << '\n';
        return 2;
    }
}

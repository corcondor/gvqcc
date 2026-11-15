// Count operand use of scratch and syndrome wires across complete caller
// subroutines and across only their certified maximum-width intervals.
#define main endpoint_schedule_main
#include "../score28_dqi/phase_schedule.cpp"
#undef main
#include <set>
#include <sstream>

namespace {
struct Event {
    uint64_t pos;
    unsigned family, mode;
    int change;
    bool operator<(const Event& other) const { return pos < other.pos; }
};
struct Counts {
    string label;
    uint64_t positions[2]{};
    vector<uint64_t> counts[2];
};
}

int main(int argc,char** argv) {
    try {
        if (argc != 5) throw runtime_error("usage KMB CALLERS.tsv MEMBERSHIP.tsv OUTPUT.json");
        Tape tape(argv[1]);
        vector<Counts> families;
        vector<Event> events;
        map<string,unsigned> labels;
        for (unsigned mode = 0; mode < 2; ++mode) {
            ifstream src(argv[2+mode]);
            if (!src) throw runtime_error("open range list");
            string row;
            if (mode) getline(src,row);
            while (getline(src,row)) {
                istringstream fields(row);
                uint64_t begin,end;
                string label;
                if (!(fields>>begin>>end>>label) || begin>=end || end>tape.n)
                    throw runtime_error("invalid range");
                const auto result = labels.try_emplace(label, families.size());
                unsigned family = result.first->second;
                if (result.second) {
                    families.emplace_back();
                    auto& item=families.back();
                    item.label=label;
                    for (auto& counters:item.counts) counters.assign(tape.nq,0);
                }
                events.push_back({begin,family,mode,1});
                events.push_back({end,family,mode,-1});
            }
        }
        sort(events.begin(),events.end());
        vector<array<int,2>> depth(families.size());
        set<pair<unsigned,unsigned>> active;
        auto it=events.begin();
        for (uint64_t pos=0;pos<tape.n;++pos) {
            const auto op=tape.step();
            while (it!=events.end() && it->pos==pos) {
                unsigned family=it->family, mode=it->mode;
                int& level=depth[family][mode];
                level+=it->change;
                if (level>0) active.insert({family,mode});
                else active.erase({family,mode});
                ++it;
            }
            for (auto [family,mode]:active) {
                auto& records=families[family];
                ++records.positions[mode];
                for (unsigned j=0;j<op.count;++j)
                    ++records.counts[mode][op.qubits[j]];
            }
        }
        ofstream out(argv[4]);
        if (!out) throw runtime_error("open output");
        out<<"{\n";
        bool later_family=false;
        for (const auto& row:families) {
            if (!row.positions[1]) continue;
            if (later_family) out<<",\n";
            later_family=true;
            out<<"  \""<<row.label<<"\": {";
            for (unsigned mode=0;mode<2;++mode) {
                if (mode) out<<",";
                out<<"\""<<(mode?"at_peak":"entire_phase")<<"\": {\"positions\": "
                   <<row.positions[mode];
                for (auto [key,lo,hi]:{tuple{"idle_data",0u,840u},
                                      tuple{"idle_scratch",840u,unsigned(tape.nq)}}) {
                    out<<", \""<<key<<"\": [";
                    bool comma=false;
                    for (unsigned q=lo;q<hi;++q) if (!row.counts[mode][q]) {
                        if (comma) out<<',';
                        out<<q;
                        comma=true;
                    }
                    out<<']';
                }
                out<<'}';
            }
            out<<'}';
        }
        out<<"\n}\n";
        return 0;
    } catch (const exception& error) {
        cerr<<error.what()<<'\n';
        return 1;
    }
}

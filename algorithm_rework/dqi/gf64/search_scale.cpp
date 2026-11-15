// Search for an ancilla-free GF(8) scaler, using rank-one updates.
#include <array>
#include <bit>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <unordered_map>
#include <vector>

struct Gate {
    unsigned mask, v, w;
    std::array<int, 6> active;
    std::array<unsigned, 512> table;
};

using State = uint64_t;
constexpr unsigned identity = 1 | (2 << 3) | (4 << 6);
std::vector<Gate> gates;

void build_gates() {
    for (unsigned mask=1; mask<8; ++mask)
      for (unsigned v=1; v<8; ++v)
        for (unsigned w=1; w<8; ++w) {
            if (std::popcount(v&w)%2) continue;
            Gate g{};
            g.mask=mask; g.v=v; g.w=w;
            for (unsigned a=2; a<8; ++a)
                g.active[a-2]=std::popcount(mask&(a^1))%2;
            for (unsigned matrix=0; matrix<512; ++matrix) {
                g.table[matrix]=matrix;
                for (unsigned j=0; j<3; ++j)
                    if (std::popcount(w & ((matrix>>(3*j))&7))%2)
                        g.table[matrix]^=v<<(3*j);
            }
            gates.push_back(g);
        }
}

State apply(State s, const Gate& g) {
    State r=s;
    for (unsigned i=0; i<6; ++i) {
        if (!g.active[i]) continue;
        const unsigned old=(s>>(9*i))&511;
        r^=uint64_t(old^g.table[old])<<(9*i);
    }
    return r;
}

constexpr unsigned radix=148;
std::unordered_map<State, unsigned> before;
std::array<unsigned, 4> path;
State goal=0;
uint64_t tested=0;

void forward(State s, unsigned code, unsigned depth, unsigned max_depth, int previous=-1) {
    before.try_emplace(s,code);
    if (depth==max_depth) return;
    for (unsigned i=0; i<gates.size(); ++i) if (int(i)!=previous)
        forward(apply(s,gates[i]),code*radix+i+1,depth+1,max_depth,i);
}

bool backward(State s, unsigned depth, unsigned max_depth, int previous=-1) {
    ++tested;
    if (const auto hit=before.find(s); hit!=before.end()) {
        auto code=hit->second;
        std::vector<unsigned> solution;
        for (; code; code/=radix) solution.push_back(code%radix-1);
        for (auto i=solution.rbegin(); i!=solution.rend(); ++i) {
            auto &g=gates[*i];std::cout<<g.mask<<" "<<g.v<<" "<<g.w<<"\n";
        }
        while(depth) {
            auto &g=gates[path[--depth]];std::cout<<g.mask<<" "<<g.v<<" "<<g.w<<"\n";
        }
        return true;
    }
    if (depth==max_depth) return false;
    for (unsigned i=0; i<gates.size(); ++i) if (int(i)!=previous) {
        path[depth]=i;
        if (backward(apply(s,gates[i]),depth+1,max_depth,i)) return true;
    }
    return false;
}

int main(int argc,char**argv) {
    if (argc!=2) return 2;
    goal=std::strtoull(argv[1],nullptr,16);
    build_gates();
    State start=0;
    for (unsigned i=0; i<6; ++i) start|=uint64_t(identity)<<(9*i);
    before.reserve(3'200'000);
    forward(start,0,0,3);
    std::cerr<<before.size()<<" distinct prefix states\n";
    for(unsigned d=0; d<=4; ++d)
        if(backward(goal,0,d)) {
            std::cerr<<tested<<" backward states until match\n";return 0;
        }
    std::cerr<<tested<<" states, no depth-seven decomposition\n";
    return 1;
}

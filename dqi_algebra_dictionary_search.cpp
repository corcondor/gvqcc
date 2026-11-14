// Exact binary-matroid basis exchange over the 255 GF16 evaluation forms.
// Changes output coefficients through exact dependencies; no tensor flips.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>
using Row = std::array<uint64_t, 9>;
struct State { std::vector<int> basis; std::vector<uint32_t> weight; std::vector<Row> rep; };
int main(int argc, char** argv) {
    if (argc != 5) return 2;
    std::ifstream in(argv[1]); int n, r, ns; in >> n >> r >> ns;
    if (!((n == 255 && r == 142) || (n == 3825 && r == 240) || (n == 65025 && r == 576)) || ns < 1) return 3;
    const int words=(r+63)/64;
    std::vector<uint32_t> forms(n); for (auto& v: forms) in >> v;
    std::vector<uint32_t> right=forms;
    if(n!=255)for(auto& v:right)in>>v;
    std::vector<State> starts(ns);
    for (auto& s: starts) {
        s.basis.resize(r); s.weight.resize(r); s.rep.resize(n);
        for (auto& v: s.basis) in >> v;
        for (auto& v: s.weight) in >> v;
        for (auto& row: s.rep) for (int k=0;k<words;k++) in >> row[k];
    }
    if (!in) return 4;
    double seconds = std::stod(argv[3]); std::mt19937_64 rng(std::stoull(argv[4]));
    auto begin = std::chrono::steady_clock::now();
    uint64_t proposals=0, accepts=0, neutral=0, down=0, restarts=0, visits99=0;
    int best=99, maxrank=99, rank=99, steps=0;
    State s=starts[0]; std::vector<int> position(n,-1);
    auto tensor=[&](const State& state){
        std::array<uint32_t,576> out{};
        for(int k=0;k<r;k++)if(state.weight[k]){
            uint32_t a=forms[state.basis[k]],b=right[state.basis[k]];
            while(a){int i=__builtin_ctz(a);a&=a-1;uint32_t v=b;while(v){int j=__builtin_ctz(v);v&=v-1;out[24*i+j]^=state.weight[k];}}
        }
        return out;
    };
    const auto expected=tensor(s);uint64_t exact_checks=1;
    auto check=[&](){++exact_checks;if(tensor(s)!=expected){std::cerr<<"EXACT_TENSOR_IDENTITY_FAILURE"<<std::endl;std::exit(5);}};
    auto rebuild=[&](){std::fill(position.begin(),position.end(),-1);for(int i=0;i<r;i++)position[s.basis[i]]=i;};
    rebuild();
    for (;;) {
        if ((proposals & 4095) == 0 && std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count() >= seconds) break;
        if (++steps > 180000) { s=starts[rng()%ns]; rank=99;steps=0;++restarts;rebuild(); }
        int j=rng()%n; if(position[j]>=0) continue;
        ++proposals;
        Row row=s.rep[j]; std::vector<int> entries, zeros;
        for(int k=0;k<words;k++){uint64_t v=row[k];while(v){int i=64*k+__builtin_ctzll(v);entries.push_back(i);if(!s.weight[i])zeros.push_back(i);v&=v-1;}}
        int pivot;
        if(!zeros.empty() && rng()%100<40) pivot=zeros[rng()%zeros.size()];
        else pivot=entries[rng()%entries.size()];
        uint32_t w=s.weight[pivot];
        int delta=0;
        if(w) for(int i:entries) if(i!=pivot)delta+=int((s.weight[i]^w)!=0)-int(s.weight[i]!=0);
        int cap=99+2+(restarts%5)*3;
        double phase=double(steps%30000)/30000.0;
        double temp=0.12+(1.0-phase)*(0.35+0.18*(restarts%5));
        if(rank+delta>cap) continue;
        if(delta>0 && std::generate_canonical<double,53>(rng)>=std::exp(-delta/temp)) continue;
        ++accepts;if(delta==0)++neutral;if(delta<0)++down;
        for(int i:entries)if(i!=pivot)s.weight[i]^=w;
        Row adjustment=row; adjustment[pivot/64]^=uint64_t(1)<<(pivot%64);
        for(auto& v:s.rep) if((v[pivot/64]>>(pivot%64))&1)for(int k=0;k<words;k++)v[k]^=adjustment[k];
        position[s.basis[pivot]]=-1;position[j]=pivot;s.basis[pivot]=j;rank+=delta;
        if((accepts&8191)==0)check();
        if(rank==99)++visits99;maxrank=std::max(maxrank,rank);
        if(rank<best){
            best=rank;std::ofstream out(argv[2]);out<<"{\"status\":\"UNVERIFIED_SEARCH_CANDIDATE\",\"rank\":"<<rank<<",\"terms\":[";
            bool comma=false;for(int i=0;i<r;i++)if(s.weight[i]){if(comma)out<<",";comma=true;out<<"["<<forms[s.basis[i]]<<","<<right[s.basis[i]]<<","<<s.weight[i]<<"]";}out<<"]}\n";
            std::cout<<"NEW_BEST "<<best<<" proposals "<<proposals<<std::endl;break;
        }
    }
    check();
    double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    std::cout<<"{\"status\":\""<<(best<99?"CANDIDATE_FOUND":"NO_IMPROVEMENT_IN_BOUNDED_SEARCH")<<"\",\"best_rank\":"<<best<<",\"proposals\":"<<proposals<<",\"accepted\":"<<accepts<<",\"neutral_moves\":"<<neutral<<",\"rank_decreasing_moves\":"<<down<<",\"restarts\":"<<restarts<<",\"visits_rank99\":"<<visits99<<",\"maximum_visited_rank\":"<<maxrank<<",\"exact_tensor_checks\":"<<exact_checks<<",\"elapsed_seconds\":"<<elapsed<<"}"<<std::endl;
}

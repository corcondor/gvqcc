// Deterministic bounded driver around the author's unmodified Polytof Scheme.
// Compile with -D BASE -D VEC_WORDS=1 and -I polytof/src -I polytof/third_party.
// Source: https://github.com/ZIB-IOL/polytof (MIT).
#include "cpd/config.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <limits>
#include <vector>
#include <array>
#include <cstdint>

bool identical(const std::vector<BitArr>& scheme, const std::vector<uint64_t>& table, int n) {
    for(int i=0;i<n;++i) for(int j=0;j<n;++j) {
        uint64_t value=0;
        for(size_t k=0;k<scheme.size();k+=3)
            if(scheme[k].test(i) && scheme[k+1].test(j)) value ^= scheme[k+2][0];
        if(value != table[i*n+j]) return false;
    }
    return true;
}

int main(int argc, char**argv) {
    if(argc!=7) {std::cerr << "input output-json attempts path-limit plus-interval seed\n"; return 2;}
    std::ifstream in(argv[1]);
    int n, rank; in>>n>>rank;
    if(!in || n>64 || n<1 || rank<2) return 3;
    std::vector<BitArr> initial;
    for(int k=0;k<3*rank;++k) {uint64_t w; in>>w; BitArr v{};v[0]=w;initial.push_back(v);}
    if(!in) return 4;
    const int attempts=std::stoi(argv[3]), limit=std::stoi(argv[4]), plus_limit=std::stoi(argv[5]);
    const uint64_t seed=std::stoull(argv[6]);
    std::vector<uint64_t> table(n*n);
    for(int i=0;i<n;++i)for(int j=0;j<n;++j)for(int k=0;k<3*rank;k+=3)
        if(initial[k].test(i) && initial[k+1].test(j))table[i*n+j]^=initial[k+2][0];
    uint64_t flips=0, plus=0, reductions=0, verify=0, stale=0;
    int best=rank, max_rank=rank, completed=0;
    std::vector<BitArr> best_data=initial;
    const auto start=std::chrono::steady_clock::now();
    for(int run=0;run<attempts;++run) {
        cpd::Scheme scheme(initial,{n,n,n},seed+run);
        int since_plus=0;
        for(int step=0;step<limit;++step) {
            if(scheme.flip()) ++flips;
            else {++stale; if(scheme.plus()){++plus;since_plus=0;}}
            if(++since_plus>=plus_limit) {if(scheme.plus()) ++plus; since_plus=0;}
            if((step+1)%10000==0)while(scheme.reduce())++reductions;
            int r=scheme.get_rank();
            if(r>max_rank)max_rank=r;
            if(r<best) {best=r;best_data=scheme.get_data();}
            if(r<rank)break;
        }
        if(!identical(scheme.get_data(),table,n)) {
            std::cerr<<"Tensor identity failure run "<<run<<"\n"; return 10;
        }
        verify+=n*n;
        ++completed;
        if(best<rank)break;
    }
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::ofstream out(argv[2]);
    out<<"{\n  \"status\": \"COMPLETE\",\n  \"degree\": "<<n
       <<",\n  \"initial_rank\": "<<rank<<",\n  \"best_rank\": "<<best
       <<",\n  \"max_visited_rank\": "<<max_rank<<",\n  \"seed\": "<<seed
       <<",\n  \"attempts_completed\": "<<completed<<",\n  \"path_limit\": "<<limit
       <<",\n  \"plus_interval\": "<<plus_limit<<",\n  \"reduce_interval\": 10000"
       <<",\n  \"successful_flips\": "<<flips<<",\n  \"plus_moves\": "<<plus
       <<",\n  \"reduce_calls_successful\": "<<reductions<<",\n  \"no_flip_available\": "<<stale
       <<",\n  \"exact_end_path_basis_pair_checks\": "<<verify
       <<",\n  \"elapsed_seconds\": "<<sec<<",\n  \"best_terms\": [";
    bool comma=false;
    for(size_t k=0;k<best_data.size();k+=3)if(best_data[k].any()) {
        if(comma)out<<",";comma=true;
        out<<"["<<best_data[k][0]<<","<<best_data[k+1][0]<<","<<best_data[k+2][0]<<"]";
    }
    out<<"]\n}\n";
    std::cout<<"degree="<<n<<" initial="<<rank<<" best="<<best<<" plus="<<plus<<" flips="<<flips<<" seconds="<<sec<<"\n";
}

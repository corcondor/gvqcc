// Bounded rank+depth excursions using the pinned, unmodified Polytof BASE API.
// Polytof: https://github.com/ZIB-IOL/polytof, MIT (notice included separately).
// This search schedule and its independent tensor checker are authored here.
#include "cpd/config.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdint>

static bool identical(const std::vector<BitArr>& data,
                      const std::vector<uint64_t>& table, int n) {
    for (int i=0;i<n;++i) for (int j=0;j<n;++j) {
        uint64_t value=0;
        for (size_t k=0;k<data.size();k+=3)
            if (data[k].test(i) && data[k+1].test(j)) value^=data[k+2][0];
        if (value!=table[i*n+j]) return false;
    }
    return true;
}

int main(int argc,char**argv) {
    if (argc!=8) {
        std::cerr<<"input output-json attempts path-limit burst-interval max-growth seed\n";
        return 2;
    }
    std::ifstream in(argv[1]); int n,rank; in>>n>>rank;
    if (!in || n<1 || n>64 || rank<2) return 3;
    std::vector<BitArr> initial;
    for (int k=0;k<3*rank;++k) {uint64_t w;in>>w;BitArr v{};v[0]=w;initial.push_back(v);}
    if (!in) return 4;
    int attempts=std::stoi(argv[3]),limit=std::stoi(argv[4]);
    int interval=std::stoi(argv[5]),growth=std::stoi(argv[6]);
    uint64_t seed=std::stoull(argv[7]);
    if (attempts<1 || limit<1 || interval<1 || growth<1 || growth>16) return 5;
    std::vector<uint64_t> table(n*n);
    for (int i=0;i<n;++i) for (int j=0;j<n;++j)
        for (int k=0;k<3*rank;k+=3)
            if (initial[k].test(i) && initial[k+1].test(j)) table[i*n+j]^=initial[k+2][0];
    uint64_t flips=0,plus=0,failed_plus=0,reduce=0,steps=0,stalls=0;
    int best=rank,maximum=rank,completed=0;
    std::vector<BitArr> best_data=initial;
    std::vector<uint64_t> histogram(rank+growth+1);
    auto start=std::chrono::steady_clock::now();
    for (int run=0;run<attempts && best>=rank;++run) {
        cpd::Scheme scheme(initial,{n,n,n},seed+run);
        bool blocked=true;
        for (int step=0;step<limit;++step) {
            if (blocked || step%interval==0) {
                for (int tries=0;tries<64 && scheme.get_rank()<rank+growth;++tries) {
                    if (scheme.plus()) ++plus; else ++failed_plus;
                    maximum=std::max(maximum,scheme.get_rank());
                }
            }
            blocked=!scheme.flip();
            if (!blocked) ++flips;
            else if (scheme.get_rank()==rank+growth) {++stalls;break;}
            if ((step+1)%1000==0) while (scheme.reduce()) ++reduce;
            int r=scheme.get_rank();
            if (r>rank+growth || r<1) return 6;
            ++steps;++histogram[r];maximum=std::max(maximum,r);
            if (r<best) {best=r;best_data=scheme.get_data();}
            if (best<rank) break;
        }
        if (!identical(scheme.get_data(),table,n)) return 10;
        ++completed;
    }
    if (!identical(best_data,table,n)) return 11;
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::ofstream out(argv[2]);
    out<<"{\n\"status\":\"COMPLETE\",\"degree\":"<<n<<",\"initial_rank\":"<<rank
       <<",\"best_rank\":"<<best<<",\"max_visited_rank\":"<<maximum
       <<",\"seed\":"<<seed<<",\"attempts_completed\":"<<completed
       <<",\"path_limit\":"<<limit<<",\"burst_interval\":"<<interval
       <<",\"max_growth\":"<<growth<<",\"reduce_interval\":1000"
       <<",\"steps_completed\":"<<steps<<",\"successful_flips\":"<<flips
       <<",\"plus_moves\":"<<plus<<",\"failed_plus_calls\":"<<failed_plus
       <<",\"successful_reductions\":"<<reduce<<",\"stalled_at_cap\":"<<stalls
       <<",\"exact_basis_pair_checks\":"<<(completed+1)*n*n
       <<",\"elapsed_seconds\":"<<sec<<",\"rank_histogram\":{";
    bool comma=false;
    for (size_t r=0;r<histogram.size();++r) if (histogram[r]) {
        if (comma) out<<",";comma=true;out<<"\""<<r<<"\":"<<histogram[r];
    }
    out<<"},\"best_terms\":[";comma=false;
    for (size_t k=0;k<best_data.size();k+=3) if (best_data[k].any()) {
        if (comma) out<<",";comma=true;
        out<<"["<<best_data[k][0]<<","<<best_data[k+1][0]<<","<<best_data[k+2][0]<<"]";
    }
    out<<"]}\n";
    std::cout<<"degree="<<n<<" initial="<<rank<<" best="<<best<<" max="<<maximum
             <<" flips="<<flips<<" plus="<<plus<<" seconds="<<sec<<"\n";
}

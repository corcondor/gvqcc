// Bounded functional cross-tensor search using the pinned Polytof BASE API.
// The score is sum_w ceil(rank(C_w)/2), not the bilinear tensor rank.
// Pure high/low residuals are recovered and proved by score4_qrom_cross.py.
// Polytof https://github.com/ZIB-IOL/polytof (MIT), commit 0dcac107d15a.
#include "cpd/config.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <vector>

using Wide=unsigned __int128;
static Wide high(const BitArr& a) {return Wide(a[0])|(Wide(a[1])<<64);}
static int rank_rows(std::array<Wide,15> rows) {
    std::array<Wide,128> piv{};
    int rank=0;
    for(Wide x:rows) while(x) {
        uint64_t hi=x>>64;
        int p=hi ? 127-__builtin_clzll(hi) : 63-__builtin_clzll(uint64_t(x));
        if(piv[p]) x^=piv[p];
        else {piv[p]=x;++rank;break;}
    }
    return rank;
}
static int packed_cost(const std::vector<BitArr>& d) {
    std::map<uint64_t,std::array<Wide,15>> groups;
    for(size_t k=0;k<d.size();k+=3) if(d[k].any()) {
        auto& rows=groups[d[k+2][0]];
        Wide u=high(d[k]);uint64_t v=d[k+1][0];
        while(v){int p=__builtin_ctzll(v);rows[p]^=u;v&=v-1;}
    }
    int cost=0;for(auto& [w,rows]:groups)cost+=(rank_rows(rows)+1)/2;
    return cost;
}
static std::vector<uint64_t> tensor(const std::vector<BitArr>& d) {
    std::vector<uint64_t> result(75*15);
    for(size_t k=0;k<d.size();k+=3)if(d[k].any())
        for(int i=0;i<75;++i)if(d[k].test(i))
            for(int j=0;j<15;++j)if(d[k+1].test(j))result[15*i+j]^=d[k+2][0];
    return result;
}
int main(int argc,char**argv) {
    if(argc!=8){std::cerr<<"input output seconds packed-growth rank-growth seed path-limit\n";return 2;}
    std::ifstream in(argv[1]);int a,b,c,r,expected;
    in>>a>>b>>c>>r>>expected;
    if(a!=75||b!=15||c!=35||r<1)return 3;
    std::vector<BitArr> initial;
    for(int i=0;i<r;++i){uint64_t lo,hi,v,w;in>>lo>>hi>>v>>w;
        BitArr u{},vv{},ww{};u[0]=lo;u[1]=hi;vv[0]=v;ww[0]=w;
        initial.push_back(u);initial.push_back(vv);initial.push_back(ww);}
    if(!in)return 4;
    double budget=std::stod(argv[3]);int growth=std::stoi(argv[4]);
    int rgrowth=std::stoi(argv[5]);uint64_t seed=std::stoull(argv[6]);int limit=std::stoi(argv[7]);
    const auto truth=tensor(initial);int original=packed_cost(initial);
    if(original!=expected)return 5;
    int best=original,best_rank=r,maximum=original;uint64_t steps=0,accepted=0,rejected=0,flips=0,pluses=0,runs=0;
    std::vector<BitArr> best_data=initial;std::mt19937_64 random(seed);
    auto start=std::chrono::steady_clock::now();
    auto seconds=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
    while(seconds()<budget&&best>=original){
        cpd::Scheme state(initial,{a,b,c},seed+runs++);int current=original;
        for(int path=0;path<limit&&seconds()<budget;++path){
            auto trial=state.clone();bool moved;
            if((path+1)%256==0&&trial.get_rank()<r+rgrowth){moved=trial.plus();if(moved)++pluses;}
            else{
                // Draw outside the cloned state. A rejected clone must not
                // replay the same internal RNG proposal indefinitely.
                std::vector<std::tuple<int,int,int>> options;
                state.enumerate_flips(options);
                moved=false;
                if(!options.empty()){
                    auto [t1,t2,component]=options[random()%options.size()];
                    if(random()&1)std::swap(t1,t2);
                    moved=trial.apply_flip(t1,t2,component);
                }
                if(moved)++flips;
            }
            ++steps;if(!moved)break;
            if((path+1)%64==0)while(trial.reduce()){}
            int cost=packed_cost(trial.get_data());maximum=std::max(maximum,cost);
            // Bounded excursions are measured in the implementable packed cost.
            // At equal/uphill cost retain a random fraction to avoid one sink.
            bool keep=cost<=original+growth&&trial.get_rank()<=r+rgrowth;
            if(cost>current&&random()%4==0)keep=false;
            if(!keep){++rejected;continue;}
            ++accepted;state=std::move(trial);current=cost;
            if(cost<best||(cost==best&&state.get_rank()<best_rank)){
                best=cost;best_rank=state.get_rank();best_data=state.get_data();
                if(tensor(best_data)!=truth)return 10;
            }
            if(best<original)break;
        }
        if(tensor(state.get_data())!=truth)return 11;
    }
    if(tensor(best_data)!=truth)return 12;
    std::ofstream out(argv[2]);
    out<<"{\n\"status\":\"BOUNDED_SEARCH_COMPLETE\",\"initial_bilinear_rank\":"<<r
       <<",\"initial_packed_cost\":"<<original<<",\"best_packed_cost\":"<<best
       <<",\"best_bilinear_rank\":"<<best_rank<<",\"max_proposed_packed_cost\":"<<maximum
       <<",\"packed_growth\":"<<growth<<",\"rank_growth\":"<<rgrowth
       <<",\"seed\":"<<seed<<",\"runs\":"<<runs<<",\"steps\":"<<steps
       <<",\"accepted\":"<<accepted<<",\"rejected\":"<<rejected
       <<",\"successful_flip_calls\":"<<flips<<",\"successful_plus_calls\":"<<pluses
       <<",\"exact_cross_tensor_equal\":true,\"seconds\":"<<seconds()<<",\"best_terms\":[";
    bool comma=false;
    for(size_t k=0;k<best_data.size();k+=3)if(best_data[k].any()){
        if(comma)out<<",";comma=true;
        out<<"["<<best_data[k][0]<<","<<best_data[k][1]<<","<<best_data[k+1][0]<<","<<best_data[k+2][0]<<"]";
    }
    out<<"]}\n";
    std::cout<<"original="<<original<<" best="<<best<<" rank="<<best_rank
             <<" steps="<<steps<<" accepted="<<accepted<<" seconds="<<seconds()<<"\n";
}

// Alternate-form search for exact diagonal cubic phase, with tensor verification.
#include "cpd/config.h"
#include <array>
#include <iostream>
#include <fstream>
#include <vector>
#include <stdexcept>

int main(int argc,char** argv) {
    if(argc!=7) throw std::runtime_error("usage: input output attempts path_steps growth seed");
    std::ifstream in(argv[1]);
    int n,r;
    in>>n>>r;
    if(!in || n<=0 || n>63 || r<=0) throw std::runtime_error("invalid dimensions");
    std::vector<BitArr> initial(3*r);
    for(auto& v:initial) in>>v[0];
    if(!in) throw std::runtime_error("short input");
    auto coeff=[&](int i,int j,int k) {
        unsigned sum=0;
        for(int a=0;a<3*r;a+=3) {
            const auto& l=initial[a]; const auto& m=initial[a+1]; const auto& q=initial[a+2];
            sum ^= (l.test(i)&m.test(j)&q.test(k)) ^ (l.test(i)&m.test(k)&q.test(j)) ^
                   (l.test(j)&m.test(i)&q.test(k)) ^ (l.test(j)&m.test(k)&q.test(i)) ^
                   (l.test(k)&m.test(i)&q.test(j)) ^ (l.test(k)&m.test(j)&q.test(i));
        }
        return sum;
    };
    auto target=cpd::Tensor{n,{}};
    for(int i=0;i<n;++i) for(int j=i+1;j<n;++j) for(int k=j+1;k<n;++k)
        if(coeff(i,j,k)) target.triples.push_back({i,j,k});
    if(!cpd::verify(initial,target)) throw std::runtime_error("initial tensor discrepancy");
    int attempts=std::stoi(argv[3]), path_steps=std::stoi(argv[4]), cap=std::stoi(argv[5]);
    uint64_t start_seed=std::stoull(argv[6]);
    uint64_t flips=0, additions=0, reduces=0;
    int completed=0, min_rank=r;
    auto best=initial;
    for(int a=0;a<attempts && min_rank>=r;++a) {
        cpd::Scheme s(initial,{n,n,n},start_seed+a);
        for(int step=0;step<path_steps;++step) {
            if(step%256==0 || !s.flip()) {
                for(int trial=0;trial<3 && s.get_rank()<r+cap;++trial)
                    if(s.plus()) ++additions;
            } else ++flips;
            if(step%151==0) {
                while(s.reduce()) ++reduces;
            }
            if(s.get_rank()<min_rank) {
                min_rank=s.get_rank();
                best=s.get_data();
                break;
            }
        }
        if(!cpd::verify(s.get_data(),target)) throw std::runtime_error("final tensor discrepancy");
        ++completed;
    }
    std::ofstream out(argv[2]);
    out<<"{\"width\":"<<n<<",\"initial_rank\":"<<r<<",\"best_rank\":"<<min_rank
       <<",\"paths\":"<<completed<<",\"successful_flips\":"<<flips<<",\"rank_growth_moves\":"<<additions
       <<",\"reductions\":"<<reduces<<",\"seed\":"<<start_seed<<",\"terms\":[";
    bool first=true;
    for(size_t i=0;i<best.size();i+=3) {
        if(!best[i].any()) continue;
        if(!first)out<<",";
        first=false;
        out<<"["<<best[i][0]<<","<<best[i+1][0]<<","<<best[i+2][0]<<"]";
    }
    out<<"]}\n";
    std::cout<<"width "<<n<<" rank "<<r<<" -> "<<min_rank<<" paths "<<completed<<" flips "<<flips<<std::endl;
}

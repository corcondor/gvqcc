// Bounded search of the eight-input quadratic JOINT map in inverse_phase27.
// Uses unmodified MIT Polytof COMM primitives. Linear differences are free
// and must be restored by the separate complete-ANF circuit certificate.
#include "cpd/config.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>
#include <cstdint>

using Data=std::vector<BitArr>;
Data live(const Data&data){Data out;for(size_t k=0;k<data.size();k+=3)if(cpd::comm::is_live_quad(data[k],data[k+1],data[k+2]))out.insert(out.end(),data.begin()+k,data.begin()+k+3);return out;}
std::vector<uint64_t> coefficients(const Data&data,int n){std::vector<uint64_t>out(n*n);for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)for(size_t k=0;k<data.size();k+=3)if((data[k].test(i)&&data[k+1].test(j))^(data[k].test(j)&&data[k+1].test(i)))out[i*n+j]^=data[k+2][0];return out;}
int main(int argc,char**argv){
 if(argc!=8){std::cerr<<"input output paths steps max-growth interval seed\n";return 2;}
 std::ifstream in(argv[1]);int n,rank;in>>n>>rank;if(!in||n!=8||rank!=13)return 3;
 Data initial;for(int i=0;i<3*rank;i++){uint64_t v;in>>v;BitArr b{};b[0]=v;initial.push_back(b);}if(!in)return 4;
 auto table=coefficients(initial,n);int runs=std::stoi(argv[3]),limit=std::stoi(argv[4]),growth=std::stoi(argv[5]),interval=std::stoi(argv[6]);uint64_t seed=std::stoull(argv[7]);
 Data best_data=initial;int best=rank,maximum=rank,completed=0;uint64_t flips=0,plus=0,compact=0,steps=0,stalls=0;
 auto start=std::chrono::steady_clock::now();
 for(int run=0;run<runs&&best>=rank;run++){
  auto s=std::make_unique<cpd::Scheme>(initial,std::array<int,3>{n,n,n},seed+run);bool blocked=true;
  for(int step=0;step<limit;step++){
   if(step&&(blocked||step%256==0)){auto data=live(s->get_data());s=std::make_unique<cpd::Scheme>(data,std::array<int,3>{n,n,n},seed+run+1000003ULL*(++compact));}
   if(blocked||step%interval==0){for(int tries=0;tries<32&&s->get_rank()<rank+growth;tries++){if(s->plus())plus++;else break;maximum=std::max(maximum,s->get_rank());}}
   blocked=!s->flip();if(!blocked)flips++;
   if(step%64==0)while(s->reduce()){}
   int r=s->get_rank();steps++;maximum=std::max(maximum,r);
   if(r<best){best=r;best_data=live(s->get_data());if(coefficients(best_data,n)!=table)return 10;}
   if(best<rank)break;
   if(blocked)stalls++;
  }
  if(coefficients(s->get_data(),n)!=table)return 11;completed++;
 }
 double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
 std::ofstream out(argv[2]);out<<"{\"status\":\"COMPLETE\",\"initial_rank\":"<<rank<<",\"best_rank\":"<<best<<",\"maximum_rank\":"<<maximum<<",\"paths_completed\":"<<completed<<",\"path_steps\":"<<limit<<",\"max_growth\":"<<growth<<",\"burst_interval\":"<<interval<<",\"seed\":"<<seed<<",\"steps\":"<<steps<<",\"successful_flips\":"<<flips<<",\"successful_plus\":"<<plus<<",\"compactions\":"<<compact<<",\"stalls\":"<<stalls<<",\"seconds\":"<<seconds<<",\"best_terms\":[";
 for(size_t k=0;k<best_data.size();k+=3){if(k)out<<",";out<<"["<<best_data[k][0]<<","<<best_data[k+1][0]<<","<<best_data[k+2][0]<<"]";}out<<"]}\n";
 std::cout<<"best="<<best<<" paths="<<completed<<" steps="<<steps<<" seconds="<<seconds<<"\n";
}

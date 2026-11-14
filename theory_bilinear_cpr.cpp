// Bounded driver for unmodified Polytof cubic-phase routing on a bilinear map.
// Source: https://github.com/ZIB-IOL/polytof (MIT).
using U128 = __uint128_t;
#include "cnot/cpr_abc.h"
#include <fstream>
#include <chrono>
#include <iostream>

int main(int argc,char**argv) {
    if(argc!=5){std::cerr<<"input output-kmx metadata-json beam-width\n";return 2;}
    std::ifstream in(argv[1]);int n,r;in>>n>>r;
    if(!in||n<1||n>64||r<1)return 3;
    std::array<std::vector<BitArr>,3> factors;
    for(int q=0;q<r;++q)for(int k=0;k<3;++k){uint64_t x;in>>x;BitArr v{};v[0]=x;factors[k].push_back(v);}
    if(!in)return 4;
    auto start=std::chrono::steady_clock::now();
    auto gates=cnot::cpr_abc::synt(n,n,n,factors[0],factors[1],factors[2],std::stoul(argv[4]),1);
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::ofstream out(argv[2]);int cx=0,ccx=0;
    for(auto gate:gates){
        if(cnot::opcode(gate)==cnot::cnot){out<<"CX q"<<cnot::qubit(gate,0)<<" q"<<cnot::qubit(gate,1)<<"\n";++cx;}
        else if(cnot::opcode(gate)==cnot::toffoli){out<<"CCX q"<<cnot::qubit(gate,0)<<" q"<<cnot::qubit(gate,1)<<" q"<<cnot::qubit(gate,2)<<"\n";++ccx;}
        else {std::cerr<<"Unexpected gate";return 5;}
    }
    std::ofstream meta(argv[3]);
    meta<<"{\"status\":\"GENERATED_NOT_YET_INDEPENDENTLY_VERIFIED\",\"degree\":"<<n<<",\"rank\":"<<r
        <<",\"CX\":"<<cx<<",\"CCX\":"<<ccx<<",\"beam_width\":"<<argv[4]<<",\"elapsed_seconds\":"<<sec<<"}\n";
    std::cout<<"n="<<n<<" CCX="<<ccx<<" CX="<<cx<<" elapsed="<<sec<<"\n";
}

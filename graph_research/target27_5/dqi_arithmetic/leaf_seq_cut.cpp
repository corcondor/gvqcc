// Exact subspace cut for 4T leaf with two initial affine-input ANDs.
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

bool dot(unsigned x,unsigned y){return std::popcount(x&y)&1;}
std::vector<unsigned> kernel(unsigned a,unsigned b) {
    std::array<unsigned,8> pivots{};
    std::vector<unsigned> basis;
    for(unsigned x=1;x<256;++x) if(!dot(a,x)&&!dot(b,x)) {
        unsigned y=x;
        while(y) {
            unsigned p=std::bit_width(y)-1;
            if(!pivots[p]) { pivots[p]=y; basis.push_back(y); break; }
            y^=pivots[p];
        }
    }
    std::vector<unsigned> span={0};
    for(auto x:basis) {
        unsigned n=span.size();
        for(unsigned i=0;i<n;++i)span.push_back(span[i]^x);
    }
    return span;
}

int main(int argc,char**argv) {
    if(argc!=2)throw std::runtime_error("usage: leaf_cache_cut input");
    std::ifstream in(argv[1]);
    for(unsigned i=0,x;i<4;++i)in>>x;
    std::array<unsigned,256> value{};
    for(unsigned x=0;x<256;++x) {
        int f;
        in>>f;
        unsigned care=0;
        if(f>=0)care=f;
        else if(x&15) throw std::runtime_error("unsupported care set");
        // Store 16 truth tables packed in each value. Their difference on
        // the missing C=0 slice is a linear function of B.
        for(unsigned g=0;g<16;++g)
            value[x]|=unsigned(care ^ (!(x&15) && dot(g,x>>4)))<<g;
    }
    if(!in)throw std::runtime_error("short input");
    std::array<std::array<unsigned,256>,256> good{};
    uint64_t cut_checks=0;
    for(unsigned a=1;a<256;++a)for(unsigned b=a;b<256;++b) {
        auto span=kernel(a,b);
        std::vector<unsigned> t;
        for(unsigned x:span)t.push_back(value[x]);
        for(unsigned i=1;i<span.size();i<<=1)
            for(unsigned x=0;x<span.size();++x)if(x&i)t[x]^=t[x^i];
        unsigned bad=0;
        for(unsigned x=0;x<t.size();++x)if(std::popcount(x)>3)bad|=t[x];
        good[a][b]=good[b][a]=65535^bad;
        ++cut_checks;
    }
    std::vector<std::array<unsigned,3>> planes;
    for(unsigned a=1;a<256;++a)for(unsigned b=a+1;b<256;++b)if((a^b)>b)
        planes.push_back({a,b,a^b});
    if(planes.size()!=10795)throw std::runtime_error("bad plane count");
    uint64_t viable=0,mixed=0, any_complements=0;
    for(auto plane:planes) {
        unsigned gmask=65535u;
        for(auto l:plane) {
            unsigned this_gmask=0;
            for(unsigned g=0;g<16;++g) {
                if(!(gmask>>g&1))continue;
                std::vector<unsigned> candidates;
                for(unsigned s=1;s<256;++s) if(s<=(s^l)&&s!=l&&(good[l][s]>>g&1))
                    candidates.push_back(s);
                bool pair=false;
                for(unsigned a:candidates)for(unsigned b:candidates) {
                    if(a>=b || (a^b)==l)continue;
                    if(good[l][a^b]>>g&1)pair=true;
                }
                if(pair)this_gmask|=1u<<g;
            }
            gmask&=this_gmask;
        }
        if(!gmask)continue;
        ++viable;
        if((plane[0]|plane[1])&240)++mixed;
    }
    std::cout<<"{\"sequential_possible_first_cut\":"<<viable<<",\"mixed\":"<<mixed<<"}\n";
}

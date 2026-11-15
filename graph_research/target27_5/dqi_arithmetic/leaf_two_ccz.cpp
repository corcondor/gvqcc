// Exact finite search for two cached ANDs + two cubic phase operations.
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
#include "unordered_dense.h"

using Bits=std::array<uint64_t,4>;
Bits operator^(Bits a, const Bits& b) { for(int i=0;i<4;++i) a[i]^=b[i]; return a; }
Bits operator&(Bits a, const Bits& b) { for(int i=0;i<4;++i) a[i]&=b[i]; return a; }
bool z(const Bits& a) { return !(a[0]|a[1]|a[2]|a[3]); }
unsigned pivot(const Bits& a) {
    for(int i=3;i>=0;--i)if(a[i]) return 64*i+std::bit_width(a[i])-1;
    throw std::runtime_error("zero pivot");
}
void set(Bits& a,unsigned j) { a[j/64]|=(uint64_t(1)<<(j%64)); }
bool get(Bits a,unsigned j) { return (a[j/64]>>(j%64))&1; }

struct Hash{
    uint64_t operator()(const Bits& a)const{
        // Avoid relying on std::hash specializations of arrays.
        return ankerl::unordered_dense::detail::wyhash::hash(a.data(),sizeof(a));
    }
};

int main(int argc,char**argv){
    if(argc!=3)throw std::runtime_error("usage: leaf_two_ccz input output");
    std::ifstream in(argv[1]);
    unsigned l1,r1,l2,r2;
    in>>l1>>r1>>l2>>r2;
    Bits goal{},valid{};
    std::array<Bits,10> wires{};
    for(int x=0;x<256;++x){
        int t;in>>t;
        if(t<0)continue;
        set(valid,x);
        if(t)set(goal,x);
        for(int j=0;j<8;++j)if((x>>j)&1)set(wires[j],x);
        if((std::popcount(l1&x)&1) && (std::popcount(r1&x)&1))set(wires[8],x);
        if((std::popcount(l2&x)&1) && (std::popcount(r2&x)&1))set(wires[9],x);
    }
    if(!in)throw std::runtime_error("short input");
    std::array<Bits,256> echelon{};
    unsigned rank=0;
    auto push=[&](Bits row){
        while(!z(row)){
            unsigned i=pivot(row);
            if(z(echelon[i])){echelon[i]=row;++rank;return;}
            row=row^echelon[i];
        }
    };
    push(valid);
    for(int i=0;i<10;++i){
        push(wires[i]);
        for(int j=0;j<i;++j)push(wires[i]&wires[j]);
    }
    auto mod=[&](Bits row){
        for(int i=255;i>=0;--i)if(!z(echelon[i])&&get(row,i))row=row^echelon[i];
        return row;
    };
    const Bits target=mod(goal);
    std::vector<Bits> emit(1024);
    for(unsigned j=1;j<1024;++j){
        unsigned pos=std::countr_zero(j);
        emit[j]=emit[j^(1u<<pos)]^wires[pos];
    }
    // Reduce arbitrary bitsets modulo the free span using a bytewise
    // lookup. By linearity mod(xor bytes)==xor mod(bytes).
    std::array<std::array<Bits,256>,32> reductions{};
    for(int b=0;b<32;++b)for(unsigned v=1;v<256;++v){
        Bits bits{};
        bits[b/8]=uint64_t(v)<<(8*(b%8));
        reductions[b][v]=mod(bits);
    }
    auto fast_mod=[&](const Bits& row){
        Bits out{};
        for(unsigned i=0;i<4;++i){
            uint64_t v=row[i];
            for(unsigned j=0;j<8;++j){
                auto& d=reductions[8*i+j][v&255];
                for(unsigned k=0;k<4;++k)out[k]^=d[k];
                v>>=8;
            }
        }
        return out;
    };
    uint64_t checked=0;
    ankerl::unordered_dense::map<Bits,uint32_t,Hash> seen;
    seen.reserve(6400000);
    uint32_t witness_first=0,witness_second=0;
    auto pack=[](unsigned a,unsigned b,unsigned c){return a|(b<<10)|(c<<20);};
    for(unsigned i=0;i<10&&!witness_second;++i)
    for(unsigned j=i+1;j<10&&!witness_second;++j)
    for(unsigned k=j+1;k<10&&!witness_second;++k){
        unsigned unavailable=(1<<i)|(1<<j)|(1<<k);
        unsigned xmask=(1023 & ~((1u<<i)-1))&~unavailable;
        unsigned ymask=(1023 & ~((1u<<j)-1))&~unavailable;
        unsigned zmask=(1023 & ~((1u<<k)-1))&~unavailable;
        for(unsigned x=xmask;;x=(x-1)&xmask){
            for(unsigned y=ymask;;y=(y-1)&ymask){
                unsigned a=x|(1<<i),b=y|(1<<j);
                Bits p=emit[a]&emit[b];
                for(unsigned zz=zmask;;zz=(zz-1)&zmask){
                    unsigned c=zz|(1<<k);
                    Bits f=fast_mod(p&emit[c]);
                    ++checked;
                    auto o=seen.find(target^f);
                    if(o!=seen.end()){
                        witness_first=o->second;witness_second=pack(a,b,c);break;
                    }
                    seen.try_emplace(f,pack(a,b,c));
                    if(!zz)break;
                }
                if(!y||witness_second)break;
            }
            if(!x||witness_second)break;
        }
    }
    std::ofstream out(argv[2]);
    out<<"{\"quadratic_free_span_rank\":"<<rank<<",\"rref_planes\":"<<checked
       <<",\"classes\":"<<seen.size()<<",\"witness\":"<<(witness_second?"true":"false")
       <<",\"first\":["<<(witness_first&1023)<<','<<((witness_first>>10)&1023)<<','<<(witness_first>>20)
       <<"],\"second\":["<<(witness_second&1023)<<','<<((witness_second>>10)&1023)<<','<<(witness_second>>20)
       <<"]}\n";
}

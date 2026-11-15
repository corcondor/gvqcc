// Care-domain variable-partition screen for exact J=4 QROM synthesis.
// Costs apply only to complete separate monomial banks plus paired products.
// This is not a lower bound for general reversible/measurement circuits.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

static unsigned deposit(unsigned x, const std::vector<int>& bits) {
    unsigned out=0;
    for(unsigned i=0;i<bits.size();++i) if((x>>i)&1) out |= 1u<<bits[i];
    return out;
}
static unsigned rank(std::vector<uint32_t> cols) {
    uint32_t piv[32]={}; unsigned r=0;
    for(uint32_t v:cols) {
        while(v) {
            unsigned p=31-__builtin_clz(v);
            if(piv[p])v^=piv[p]; else {piv[p]=v;++r;break;}
        }
    }
    return r;
}
// The legal monomial domain is a Ferrers staircase: each successive column
// fixes a nonincreasing prefix of low rows. A column that can match that
// prefix inside the earlier span adds no rank. If it cannot, rank must rise;
// its unspecified suffix cannot affect any later constraint, so zero is safe.
static unsigned min_completion_rank(const std::vector<uint32_t>& columns,const std::vector<unsigned>& care) {
    std::vector<uint32_t> independent;
    for(unsigned h=0;h<columns.size();++h) {
        uint32_t mask=care[h]==32?~0u:((1u<<care[h])-1u);
        uint32_t piv[32]={};
        for(uint32_t v:independent) {
            v&=mask;
            while(v) {unsigned p=31-__builtin_clz(v);if(piv[p])v^=piv[p];else{piv[p]=v;break;}}
        }
        uint32_t v=columns[h]&mask;
        while(v) {unsigned p=31-__builtin_clz(v);if(piv[p])v^=piv[p];else break;}
        if(v)independent.push_back(columns[h]&mask);
    }
    return independent.size();
}
int main(int argc,char**argv) {
    if(argc!=2) throw std::runtime_error("usage: partitions coefficient_u32_binary");
    std::ifstream in(argv[1],std::ios::binary);
    std::vector<uint32_t> coeff(19*2048);
    in.read(reinterpret_cast<char*>(coeff.data()),coeff.size()*sizeof(uint32_t));
    if(in.gcount()!=static_cast<std::streamsize>(coeff.size()*sizeof(uint32_t)))
        throw std::runtime_error("wrong coefficient file size");
    std::cout<<"partition,batch,nlo,nhi,bank,qubits,full_columns,paired,joint_full,optimistic_paired,completion_paired,completion_joint,ranks,completion_ranks\n";
    for(unsigned mask=1;mask<2048;++mask) {
        unsigned n=__builtin_popcount(mask);if(n!=4&&n!=5)continue;
        std::vector<int> low,high;
        for(int b=0;b<11;++b)((mask>>b)&1?low:high).push_back(b);
        unsigned nl=0,nh=0;
        while(nl<(1u<<low.size())&&deposit(nl,low)<1220)++nl;
        while(nh<(1u<<high.size())&&deposit(nh,high)<1220)++nh;
        unsigned bank=nl+nh-13;if(bank>83)continue;
        std::vector<unsigned> lm(nl),hm(nh),complete;
        for(unsigned l=0;l<nl;++l)lm[l]=deposit(l,low);
        for(unsigned h=0;h<nh;++h)hm[h]=deposit(h,high);
        for(unsigned h=1;h<nh;++h)if((hm[h]|lm.back())<1220)complete.push_back(h);
        std::vector<unsigned> care(nh-1);
        for(unsigned h=1;h<nh;++h){unsigned k=1;while(k<nl&&(hm[h]|lm[k])<1220)++k;care[h-1]=k-1;}
        for(unsigned k=0;k<19;++k) {
            unsigned paired=bank,lower=bank,full=0,completed=bank,completed_full=0;
            std::vector<unsigned> ranks,completion_ranks;
            for(unsigned o=0;o<32;++o) {
                std::vector<uint32_t> columns(nh-1),known;
                for(unsigned h=1;h<nh;++h) {
                    uint32_t col=0;
                    for(unsigned l=1;l<nl;++l)
                        if((coeff[k*2048+(hm[h]|lm[l])]>>o)&1u)col|=1u<<(l-1);
                    columns[h-1]=col;
                }
                for(unsigned h:complete)known.push_back(columns[h-1]);
                unsigned r=rank(columns),kr=rank(known),cr=min_completion_rank(columns,care);
                ranks.push_back(r);paired+=(r+1)/2;lower+=(kr+1)/2;
                completion_ranks.push_back(cr);completed+=(cr+1)/2;
                if(cr==nl-1&&(cr&1))++completed_full;
                // A constructive one-CCX saving for pairs of full odd-rank
                // slices; the Python compiler independently verifies it.
                if(r==nl-1 && (r&1))++full;
            }
            std::cout<<mask<<','<<k<<','<<nl<<','<<nh<<','<<bank<<','<<bank+45<<','<<complete.size()<<','<<paired<<','<<paired-full/2<<','<<lower<<','<<completed<<','<<completed-completed_full/2<<",\"";
            for(unsigned i=0;i<ranks.size();++i){if(i)std::cout<<' ';std::cout<<ranks[i];}
            std::cout<<"\",\"";
            for(unsigned i=0;i<completion_ranks.size();++i){if(i)std::cout<<' ';std::cout<<completion_ranks[i];}
            std::cout<<"\"\n";
        }
    }
}

// Enumerate all 4D quotient spaces with 12 or more rank-1 directions.
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <set>
#include <vector>

using U = uint32_t;

static bool independent(U v, std::array<U,28>& p) {
    while (v) {
        auto i = std::bit_width(v)-1;
        if (p[i]) v ^= p[i];
        else { p[i]=v; return true; }
    }
    return false;
}

template<size_t T> static U canonical_coset(U v, const std::array<U,T>& subspace) {
    U best=v;
    for (auto u:subspace) best=std::min(best,U(v^u));
    return best;
}

int main(int argc,char**argv) {
    if(argc!=3) throw std::runtime_error("usage: joint_quad_cayley data.txt witness.txt");
    std::ifstream in(argv[1]);
    unsigned rank, quotient, n;
    in>>rank>>quotient>>n;
    if(rank!=8 || quotient!=5 || n!=10795)
        throw std::runtime_error("unexpected expected tensor dimensions");
    std::array<U,8>A{};
    for(U& u:A) in>>u;
    for(unsigned i=0;i<quotient;++i) { U v=0; in>>v; }
    std::vector<U> atom;
    // Quotient representatives are stored as sparse 28-bit vectors. Pack
    // the 20 surviving coordinate bits so a membership test is array indexing.
    U used=0;
    struct Term { U raw, r, a, b; };
    std::vector<Term> terms(n);
    for(auto& t:terms) { in>>t.raw>>t.r>>t.a>>t.b; used|=t.r; }
    if(!in || std::popcount(used)!=20)
        throw std::runtime_error("invalid quotient representation");
    std::vector<U> full(1<<20);
    std::vector<std::array<U,2>> forms(1<<20);
    for(auto t:terms) {
        U q=0, i=0;
        for(unsigned b=0;b<28;++b) if((used>>b)&1u) q|=((t.r>>b)&1u)<<i++;
        if(!q || full[q]) throw std::runtime_error("expected unique nonzero classes");
        full[q]=t.raw; forms[q]={t.a,t.b}; atom.push_back(q);
    }
    std::sort(atom.begin(),atom.end());
    using PairList = std::vector<U>;
    // Store every occupied unordered edge of the Cayley graph, keyed by
    // its xor only when the xor is itself an occupied direction.
    std::vector<PairList> edges(1<<20);
    uint64_t occupied_edges=0;
    for(size_t i=0;i<atom.size();++i) for(size_t j=i+1;j<atom.size();++j) {
        U delta=atom[i]^atom[j];
        if(full[delta]) { edges[delta].push_back(atom[i]); ++occupied_edges; }
    }
    std::set<std::array<U,8>> rich_3spaces;
    uint64_t lines=0, cosets3_checked=0;
    for(U u:atom) for(U v:edges[u]) {
        if(u>=v || v>(u^v)) continue;
        ++lines;
        const std::array<U,4> L={0,u,v,u^v};
        for(U w:edges[u]) {
            ++cosets3_checked;
            if(w==v || (!full[w^v] && !full[w^v^u])) continue;
            w=canonical_coset(w,L);
            if(!w) continue;
            std::array<U,8> S={0,u,v,u^v,w,u^w,v^w,u^v^w};
            std::sort(S.begin(),S.end());
            rich_3spaces.insert(S);
        }
    }
    std::cerr<<"rich_3spaces="<<rich_3spaces.size()<<std::endl;
    uint64_t cosets4_checked=0, rich4=0, rank12=0, witnesses=0;
    for(const auto& S:rich_3spaces) {
        unsigned base=0; U first=0;
        for(U u:S) if(full[u]) { ++base; if(!first || edges[u].size()<edges[first].size()) first=u; }
        if(base<6 || !first) throw std::runtime_error("invalid 3-space");
        for(U w:edges[first]) {
            if(std::binary_search(S.begin(),S.end(),w)) continue;
            ++cosets4_checked;
            unsigned count=base;
            for(U u:S) count+=bool(full[w^u]);
            if(count<12) continue;
            ++rich4;
            std::array<U,28> p{};
            std::vector<U> generators; generators.reserve(12);
            for(unsigned c=0;c<2;++c) for(U u:S) {
                U q=u^(c?w:0);
                if(full[q] && independent(full[q],p)) generators.push_back(q);
            }
            if(generators.size()!=12) continue;
            ++rank12;
            bool spans=true;
            for(U a:A) if(independent(a,p)) { spans=false; break; }
            if(!spans) continue;
            ++witnesses;
            std::ofstream out(argv[2]);
            for(U q:generators) out<<forms[q][0]<<' '<<forms[q][1]<<'\n';
            break;
        }
        if(witnesses) break;
    }
    std::cout<<"{\"paid_products\":13,\"witness_products\":"<<(witnesses?12:0)
             <<",\"occupied_differences\":"<<occupied_edges<<",\"lines\":"<<lines
             <<",\"rich_3spaces\":"<<rich_3spaces.size()
             <<",\"third_cosets_checked\":"<<cosets3_checked
             <<",\"fourth_cosets_checked\":"<<cosets4_checked
             <<",\"rich_4space_encounters\":"<<rich4
             <<",\"rank12_encounters\":"<<rank12
             <<",\"witnesses\":"<<witnesses<<"}\n";
}

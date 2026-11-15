#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Each 64-bit cell contains four independent 16-bit low-coefficient rows.
using Matrix = std::array<uint64_t,19>;
using Support = std::array<uint64_t,4>;
using Plane = std::pair<uint16_t,uint16_t>;
constexpr uint64_t lanes = 0x0001000100010001ULL;

int lead(uint64_t v) { return 63 - __builtin_clzll(v); }

bool append(std::vector<uint16_t>& basis, uint16_t value) {
    for (const auto row : basis)
        if ((value >> lead(row)) & 1U) value ^= row;
    if (!value) return false;
    const auto location = std::find_if(basis.begin(), basis.end(), [&](uint16_t row){
        return row < value;
    });
    basis.insert(location, value);
    return true;
}

std::vector<uint16_t> low_basis(const Matrix& a) {
    std::vector<uint16_t> basis;
    for (const uint64_t word : a)
        for (int shift=0; shift<64; shift+=16)
            append(basis, (word>>shift)&32767);
    if (basis.size() > 2) throw std::runtime_error("expected an existing mixed product");
    return basis;
}

using Hi = __uint128_t;
std::vector<Hi> high_basis(const Matrix& a, const std::vector<uint16_t>& low) {
    std::vector<Hi> result;
    for (const auto low_row : low) {
        const int pivot=lead(low_row);
        Hi v=0;
        for (int i=0; i<76; i++)
            v |= static_cast<Hi>((a[i/4]>>(16*(i%4)+pivot))&1ULL) << i;
        result.push_back(v);
    }
    return result;
}

Plane canonical(uint16_t a, uint16_t b) {
    if (lead(a)<lead(b)) std::swap(a,b);
    if (lead(a)==lead(b)) b ^= a;
    if ((a>>lead(b))&1U) a ^= b;
    return {a,b};
}

bool shares_high(const std::vector<Hi>& a,const std::vector<Hi>& b) {
    std::array<Hi,3> ar{a.at(0),0,0}, br{b.at(0),0,0};
    if (a.size()==2) ar[1]=a[1], ar[2]=a[0]^a[1];
    if (b.size()==2) br[1]=b[1], br[2]=b[0]^b[1];
    for (const auto x:ar) for (const auto y:br) if (x && x==y) return true;
    return false;
}

std::set<Plane> planes(const std::vector<Matrix>& matrices, bool graph, bool all_observed) {
    std::vector<std::vector<uint16_t>> bases;
    std::vector<std::vector<Hi>> highs;
    std::set<Plane> result;
    for (const auto& m:matrices) {
        auto b=low_basis(m);
        if (b.empty()) throw std::runtime_error("zero mixed product");
        if (b.size()==2) result.insert(canonical(b[0],b[1]));
        highs.push_back(high_basis(m,b));
        bases.push_back(std::move(b));
    }
    if (all_observed) {
        std::set<uint16_t> observed;
        for (const auto& basis : bases) {
            observed.insert(basis.begin(),basis.end());
            if (basis.size()==2) observed.insert(basis[0]^basis[1]);
        }
        for (auto lower=observed.begin(); lower!=observed.end(); ++lower)
            for (auto upper=observed.begin(); upper!=lower; ++upper)
                result.insert(canonical(*lower,*upper));
    }
    if (!graph) return result;
    for (size_t i=0;i<bases.size();++i) {
        for (size_t j=0;j<i;++j) {
            auto u=bases[i];
            for (auto t:bases[j]) append(u,t);
            if (u.size()>3 && !shares_high(highs[i],highs[j])) continue;
            const uint32_t n=1U<<u.size();
            std::vector<uint16_t> span(n);
            for (uint32_t bit=1;bit<n;++bit)
                span[bit]=span[bit&(bit-1)]^u[__builtin_ctz(bit)];
            for (uint32_t a=1;a<n;++a)
                for (uint32_t b=1;b<a;++b)
                    result.insert(canonical(span[a],span[b]));
        }
    }
    return result;
}

std::vector<Support> kernel(const std::vector<Matrix>& matrices, Plane p, int words=19) {
    std::array<int,19*64> at;
    at.fill(-1);
    std::vector<Matrix> stored(matrices.size());
    std::vector<Support> coeff(matrices.size());
    std::vector<Support> result;
    const auto [a,b]=p;
    const int sa=lead(a), sb=lead(b);
    int r=0;
    for (size_t i=0;i<matrices.size();++i) {
        Matrix row{};
        for (int j=0;j<words;++j) {
            uint64_t v=matrices[i][j];
            v ^= ((v>>sa)&lanes)*a;
            v ^= ((v>>sb)&lanes)*b;
            row[j]=v;
        }
        Support mask{};
        mask[i/64] = 1ULL << (i%64);
        bool added=false;
        for (int j=words-1;j>=0 && !added;) {
            if (!row[j]) { --j; continue; }
            const int pivot=j*64+lead(row[j]);
            const int k=at[pivot];
            if (k<0) {
                at[pivot]=r;
                stored[r]=row;
                coeff[r++]=mask;
                added=true;
            } else {
                for (int m=0;m<=j;++m) row[m]^=stored[k][m];
                for (size_t m=0;m<mask.size();++m) mask[m]^=coeff[k][m];
            }
        }
        if (!added) result.push_back(mask);
    }
    return result;
}

std::vector<Matrix> high_sketch(const std::vector<Matrix>& matrices, unsigned seed) {
    std::mt19937_64 rng(seed);
    std::array<Hi,32> feature;
    for (auto& form : feature) form=static_cast<Hi>(rng())|(static_cast<Hi>(rng()&4095U)<<64);
    std::vector<Matrix> reduced(matrices.size());
    for(size_t i=0;i<matrices.size();++i)
        for(size_t row=0;row<feature.size();++row) {
            uint16_t sum=0;
            for(unsigned h=0;h<76;++h)
                if((feature[row]>>h)&1U) sum^=static_cast<uint16_t>(matrices[i][h/4]>>(16*(h%4)));
            reduced[i][row/4]|=static_cast<uint64_t>(sum)<<(16*(row%4));
        }
    return reduced;
}

bool confirms(const std::vector<Matrix>& matrices, Plane p, const std::vector<Support>& kernel) {
    const auto [a,b]=p;
    const int sa=lead(a), sb=lead(b);
    for (const auto &mask : kernel) {
        Matrix sum{};
        for(size_t w=0;w<mask.size();++w) {
            uint64_t remain=mask[w];
            while (remain) {
                const auto &m=matrices.at(w*64+__builtin_ctzll(remain));
                for (size_t j=0;j<m.size();++j) sum[j]^=m[j];
                remain &= remain-1;
            }
        }
        for (auto v:sum) {
            v ^= ((v>>sa)&lanes)*a;
            v ^= ((v>>sb)&lanes)*b;
            if (v) return false;
        }
    }
    return true;
}

int main(int argc, char** argv) {
    if (argc<3) return 2;
    std::vector<std::vector<std::vector<unsigned>>> seeds(17);
    for(int arg=3;arg<argc;++arg) {
        std::ifstream in(argv[arg]);
        if(!in) return 2;
        std::string line;
        while(std::getline(in,line)) {
            std::istringstream row(line);
            unsigned seg;
            if(!(row>>seg)) continue;
            std::vector<unsigned> support;
            unsigned item;
            while(row>>item) support.push_back(item);
            seeds.at(seg).push_back(std::move(support));
        }
    }
    const std::string mode=argv[2];
    if (mode!="original" && mode!="graph" && mode!="all" && mode!="certified") return 2;
    const bool graph=mode!="original";
    const bool all_observed=mode=="all" || mode=="certified";
    const bool certified=mode=="certified";
    std::ifstream in(argv[1],std::ios::binary);
    if (!in) return 2;
    int i=0;
    uint32_t n;
    while (in.read(reinterpret_cast<char*>(&n),4)) {
        if (n>256) throw std::runtime_error("support mask too narrow");
        std::vector<Matrix> mats(n);
        if (!in.read(reinterpret_cast<char*>(mats.data()),n*sizeof(Matrix)))
            throw std::runtime_error("truncated matrix input");
        auto p=planes(mats,graph,all_observed);
        for(const auto &s:seeds.at(i)) {
            Matrix sum{};
            for(auto v:s)
                for(size_t j=0;j<sum.size();++j) sum[j]^=mats.at(v)[j];
            const auto u=low_basis(sum);
            if(u.size()==2) p.insert(canonical(u[0],u[1]));
        }
        const auto sketch=certified?high_sketch(mats,4409+i):std::vector<Matrix>{};
        size_t fallbacks=0, memberships=0;
        size_t max_dimension=0;
        for (const auto &u:p) {
            auto relations=certified?kernel(sketch,u,8):kernel(mats,u);
            if (certified && !confirms(mats,u,relations)) {
                ++fallbacks;
                relations=kernel(mats,u);
            }
            max_dimension=std::max(max_dimension,relations.size());
            for (const auto &mask:relations) {
                ++memberships;
                std::cout << i << ' ' << u.first << ' ' << u.second;
                for (auto x:mask) std::cout << ' ' << std::hex << x;
                std::cout << std::dec << '\n';
            }
        }
        std::cerr << i++ << ' ' << n << ' ' << p.size() << ' ' << memberships
                  << ' ' << max_dimension;
        if (certified) std::cerr << ' ' << fallbacks;
        std::cerr << '\n';
    }
}

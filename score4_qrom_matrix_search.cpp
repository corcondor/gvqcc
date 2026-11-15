// Direct functional-matrix moves. Each node is C(high,low)*output_direction.
// A node costs ceil(rank(C)/2) mixed ANDs; univariate residuals are separately
// reconstructed by score4_qrom_cross.py and never silently discarded.
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
using Matrix=std::array<Wide,15>;
struct Node{Matrix m{};uint64_t w=0;int rank=0;uint32_t lowkey=0;};
static int pivot(Wide x){uint64_t hi=x>>64;return hi?127-__builtin_clzll(hi):63-__builtin_clzll(uint64_t(x));}
static int rankof(const Matrix& rows){std::array<Wide,128>b{};int r=0;
    for(Wide x:rows)while(x){int p=pivot(x);if(b[p])x^=b[p];else{b[p]=x;++r;break;}}return r;}
static uint32_t lowkey(const Matrix&m,int rank){
    if(rank<1||rank>2)return 0;
    uint16_t a=0,b=0;
    for(int i=0;i<75;++i){uint16_t v=0;for(int j=0;j<15;++j)if(m[j]>>i&1)v^=1<<j;
        if(!v)continue;if(!a)a=v;else if(v!=a){b=v;break;}}
    if(!b)return a;
    uint16_t c=a^b;if(a>b)std::swap(a,b);if(c<a){b=a;a=c;}else if(c<b)b=c;
    return uint32_t(a)|(uint32_t(b)<<16);
}
static void update(Node&n){n.rank=rankof(n.m);n.lowkey=lowkey(n.m,n.rank);}
static void add(std::vector<Node>&s,Node n){
    while(n.w){
        bool merged=false;
        for(size_t i=0;i<s.size();++i)if(s[i].w==n.w){
            for(int j=0;j<15;++j)n.m[j]^=s[i].m[j];s[i]=s.back();s.pop_back();merged=true;break;}
        if(!merged)break;
    }
    if(!n.w)return;update(n);if(!n.rank)return;
    for(size_t i=0;i<s.size();++i)if(s[i].m==n.m){
        n.w^=s[i].w;s[i]=s.back();s.pop_back();add(s,n);return;}
    s.push_back(n);
}
static int cost(const std::vector<Node>&s){int c=0;for(const auto&n:s)c+=(n.rank+1)/2;return c;}
static std::vector<uint64_t> tensor(const std::vector<Node>&s){std::vector<uint64_t> t(75*15);
    for(const auto&n:s)for(int j=0;j<15;++j)for(int i=0;i<75;++i)if(n.m[j]>>i&1)t[15*i+j]^=n.w;return t;}
static void emit_terms(std::ostream&out,const std::vector<Node>&s){
    bool comma=false;
    for(const auto&n:s){
        std::array<Wide,128> piv{};std::array<uint16_t,128> coeff{};
        std::vector<Wide> highs;std::vector<uint16_t> lows;
        for(int j=0;j<15;++j){Wide x=n.m[j];uint16_t expr=0;
            while(x){int p=pivot(x);if(piv[p]){x^=piv[p];expr^=coeff[p];}
                else{uint16_t bit=1<<highs.size();piv[p]=x;coeff[p]=expr^bit;
                    highs.push_back(n.m[j]);lows.push_back(0);expr=bit;x=0;}}
            for(size_t k=0;k<highs.size();++k)if(expr>>k&1)lows[k]^=1<<j;
        }
        for(size_t i=0;i<highs.size();++i){if(comma)out<<",";comma=true;
            out<<"["<<uint64_t(highs[i])<<","<<uint64_t(highs[i]>>64)<<","<<lows[i]<<","<<n.w<<"]";}
    }
}
int main(int argc,char**argv){
    if(argc!=7){std::cerr<<"input output seconds growth seed path-limit\n";return 2;}
    std::ifstream in(argv[1]);int a,b,c,r,expected;in>>a>>b>>c>>r>>expected;
    if(a!=75||b!=15||c!=35||r<1)return 3;
    std::vector<Node> initial;
    for(int i=0;i<r;++i){uint64_t lo,hi,v,w;in>>lo>>hi>>v>>w;Node n;n.w=w;Wide u=Wide(lo)|(Wide(hi)<<64);
        for(int j=0;j<15;++j)if(v>>j&1)n.m[j]^=u;add(initial,n);}
    if(!in||cost(initial)!=expected)return 4;
    const auto truth=tensor(initial);const int original=expected;
    double budget=std::stod(argv[3]);int growth=std::stoi(argv[4]);uint64_t seed=std::stoull(argv[5]);int limit=std::stoi(argv[6]);
    std::mt19937_64 rng(seed);int best=original,maximum=original;std::vector<Node> best_state=initial;
    uint64_t steps=0,accepted=0,rejected=0,runs=0,neutral_plane_proposals=0;
    auto start=std::chrono::steady_clock::now();auto seconds=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
    while(seconds()<budget&&best>=original){auto state=initial;int current=original;++runs;
        for(int p=0;p<limit&&seconds()<budget;++p){
            if(state.size()<2)break;size_t i=rng()%state.size(),j=rng()%(state.size()-1);if(j>=i)++j;
            if((rng()%4)!=0&&state[i].lowkey){
                std::vector<size_t>same;for(size_t k=0;k<state.size();++k)if(k!=i&&state[k].lowkey==state[i].lowkey)same.push_back(k);
                if(!same.empty()){j=same[rng()%same.size()];++neutral_plane_proposals;}}
            Node x=state[i],y=state[j];for(int k=0;k<15;++k)y.m[k]^=x.m[k];x.w^=y.w;
            auto trial=state;if(i<j)std::swap(i,j);trial[i]=trial.back();trial.pop_back();trial[j]=trial.back();trial.pop_back();
            add(trial,x);add(trial,y);int next=cost(trial);++steps;maximum=std::max(maximum,next);
            bool keep=next<=original+growth;
            if(next>current&&rng()%4==0)keep=false;
            if(!keep){++rejected;continue;}
            ++accepted;state=std::move(trial);current=next;
            if(next<best){best=next;best_state=state;if(tensor(state)!=truth)return 10;}
            if(best<original)break;
        }
        if(tensor(state)!=truth)return 11;
    }
    if(tensor(best_state)!=truth)return 12;
    std::ofstream out(argv[2]);out<<"{\n\"status\":\"BOUNDED_FUNCTIONAL_MATRIX_SEARCH_COMPLETE\",\"initial_packed_cost\":"<<original
        <<",\"best_packed_cost\":"<<best<<",\"max_proposed_packed_cost\":"<<maximum
        <<",\"growth\":"<<growth<<",\"seed\":"<<seed<<",\"runs\":"<<runs
        <<",\"steps\":"<<steps<<",\"accepted\":"<<accepted<<",\"rejected\":"<<rejected
        <<",\"shared_low_plane_proposals\":"<<neutral_plane_proposals
        <<",\"exact_cross_tensor_equal\":true,\"seconds\":"<<seconds()<<",\"best_terms\":[";
    emit_terms(out,best_state);out<<"]}\n";
    std::cout<<"original="<<original<<" best="<<best<<" steps="<<steps<<" accepted="<<accepted<<" seconds="<<seconds()<<"\n";
}

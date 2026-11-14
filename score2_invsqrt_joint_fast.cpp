// Exact small-table XOR/AND synthesis, authored for this experiment.
// Continued search: same reviewed enumerator, with resumable first-class ranges and progress.
// Functions are bit vectors on up to 64 certified reachable patterns.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <unordered_set>
#include <vector>
using U=uint64_t;
struct Basis {
  std::array<U,64> v{}; std::array<unsigned,64> c{}; U pivots=0;
  void add(U x,unsigned k=0) {while(x){int p=63-__builtin_clzll(x);if(!v[p]){v[p]=x;c[p]=k;pivots|=U(1)<<p;return;}x^=v[p];k^=c[p];}}
  U rem(U x)const {while(x){int p=63-__builtin_clzll(x);if(!v[p])break;x^=v[p];}return x;}
  // Canonical quotient representative, unlike early-stop membership reduction.
  U quotient(U x)const {U ps=pivots;while(ps){int p=63-__builtin_clzll(ps);if(x>>p&1)x^=v[p];ps^=U(1)<<p;}return x;}
  bool solve(U x,unsigned &k)const {k=0;while(x){int p=63-__builtin_clzll(x);if(!v[p])return false;x^=v[p];k^=c[p];}return true;}
};
struct Gate {unsigned a,b;U v;};
Basis basis(const std::vector<U>&v){Basis b;for(unsigned j=0;j<v.size();++j)b.add(v[j],1u<<j);return b;}
U eval(unsigned a,const std::vector<U>&v){U y=0;for(unsigned j=0;j<v.size();++j)if(a>>j&1)y^=v[j];return y;}
struct ProductSpace {
  const std::vector<U>& v; Basis lin,quad; unsigned d; std::array<std::array<U,16>,16> m{};
  ProductSpace(const std::vector<U>& vv):v(vv),lin(basis(vv)),d(vv.size()-1){
    for(unsigned i=0;i<d;++i)for(unsigned j=0;j<i;++j){U q=lin.quotient(v[i+1]&v[j+1]);m[i][j]=m[j][i]=q;quad.add(q);}
  }
  bool find(U target,Gate &out)const {
    U t=lin.quotient(target);if(!t){out={0,0,0};return true;}if(quad.rem(t))return false;
    std::array<U,16> cols{};unsigned prev=0;
    for(unsigned seq=1;seq<(1u<<d);++seq){unsigned a=seq^(seq>>1),changed=a^prev;prev=a;unsigned i=__builtin_ctz(changed);
      for(unsigned j=0;j<d;++j)cols[j]^=m[i][j];Basis prod;for(unsigned j=0;j<d;++j)prod.add(cols[j],1u<<j);unsigned b;
      if(prod.solve(t,b)){out={a<<1,b<<1,eval(a<<1,v)&eval(b<<1,v)};return true;}
    }return false;
  }
};
bool one_product(const std::vector<U>& v,U target,Gate &out){ProductSpace ps(v);return ps.find(target,out);}
void print_gate(Gate g){std::cout<<"{\"left\":[";bool comma=false;for(unsigned j=1;j<16;++j)if(g.a>>j&1){if(comma)std::cout<<',';std::cout<<j-1;comma=true;}
  std::cout<<"],\"right\":[";comma=false;for(unsigned j=1;j<16;++j)if(g.b>>j&1){if(comma)std::cout<<',';std::cout<<j-1;comma=true;}std::cout<<"]}";}
int main(int argc,char**argv){
  if(argc<2)return 2;std::ifstream f(argv[1]);int n;f>>n;std::vector<U> base(n+1);for(U &v:base)f>>v;U t0,t1;f>>t0>>t1;
  bool all=argc>2;double limit=argc>3?std::stod(argv[3]):60;auto started=std::chrono::steady_clock::now();
  unsigned start_index=argc>4?std::stoul(argv[4]):0;
  Basis initial=basis(base);std::vector<Gate> first;std::unordered_set<U> seen;
  // Try the actual source first gate first, followed by all normalized bases.
  unsigned a=(1<<1)|(1<<3)|(1<<4)|(1<<5)|(1<<6),b=(1<<1)|(1<<2)|(1<<3)|(1<<4)|(1<<6);
  U actual=eval(a,base)&eval(b,base);first.push_back({a,b,actual});seen.insert(initial.quotient(actual));
  if(all)for(unsigned a=1;a<(1u<<n);++a)for(unsigned b=a+1;b<(1u<<n);++b){if(!(b<(a^b)))continue;U v=eval(a<<1,base)&eval(b<<1,base);U q=initial.quotient(v);if(q&&seen.insert(q).second)first.push_back({a<<1,b<<1,v});}
  if(n>6&&first.size()>1)std::stable_sort(first.begin()+1,first.end(),[n](Gate a,Gate b){return bool((a.a|a.b)&(1u<<n))>bool((b.a|b.b)&(1u<<n));});
  long long seconds_tried=0, rank1_unresolved=0, pairs_tried=0;unsigned first_done=0;
  for(Gate g0:first){if(first_done<start_index){++first_done;continue;}std::vector<U> v=base;v.push_back(g0.v);Basis lin=basis(v);std::unordered_set<U> s2;unsigned d=v.size()-1;
    std::vector<U> par(1u<<d);for(unsigned i=1;i<par.size();++i){unsigned bit=__builtin_ctz(i);par[i]=par[i&(i-1)]^v[bit+1];}
    for(unsigned a=1;a<par.size();++a)for(unsigned b=a+1;b<par.size();++b){if(!(b<(a^b)))continue;U g1v=par[a]&par[b],q=lin.quotient(g1v);if(!q||!s2.insert(q).second)continue;
      ++pairs_tried;Gate g1={a<<1,b<<1,g1v};std::vector<U> w=v;w.push_back(g1v);Basis wl=basis(w);U r0=wl.quotient(t0),r1=wl.quotient(t1);
      if(!r0||!r1||r0==r1){++rank1_unresolved;continue;}
      ProductSpace product_space(w);
      for(int direction=0;direction<3;++direction){U t=direction==0?t0:direction==1?t1:t0^t1;Gate g2;
        if(!product_space.find(t,g2))continue;std::vector<U> z=w;z.push_back(g2.v);Gate g3;
        U other=direction==0?t1:t0;if(!one_product(z,other,g3))continue;z.push_back(g3.v);Basis zl=basis(z);unsigned o0,o1;
        if(!zl.solve(t0,o0)||!zl.solve(t1,o1))return 3;
        std::cout<<"{\"status\":\"SAT\",\"gates\":[";print_gate(g0);std::cout<<',';print_gate(g1);std::cout<<',';print_gate(g2);std::cout<<',';print_gate(g3);
        std::cout<<"],\"output_coefficient_masks\":["<<o0<<','<<o1<<"],\"first_gates_completed\":"<<first_done<<",\"second_gates_tried\":"<<pairs_tried<<"}\n";return 0;
      }
      if((pairs_tried&1023)==0){double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();if(sec>limit){std::cout<<"{\"status\":\"TIME_LIMIT\",\"first_gates_completed\":"<<first_done<<",\"first_gates_total\":"<<first.size()<<",\"second_gates_tried\":"<<pairs_tried<<",\"rank1_unresolved\":"<<rank1_unresolved<<",\"seconds\":"<<sec<<"}\n";return 0;}}
    }++first_done; if(first_done%50==0){double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();std::cerr<<"{\"progress_first_done\":"<<first_done<<",\"first_total\":"<<first.size()<<",\"pairs_this_run\":"<<pairs_tried<<",\"seconds\":"<<sec<<"}\n"<<std::flush;}
  }
  double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
  std::cout<<"{\"status\":\""<<(rank1_unresolved?"INCOMPLETE_RANK1":"NO_SOLUTION_IN_SEARCHED_FAMILY")<<"\",\"first_gates_completed\":"<<first_done<<",\"first_gates_total\":"<<first.size()<<",\"second_gates_tried\":"<<pairs_tried<<",\"rank1_unresolved\":"<<rank1_unresolved<<",\"seconds\":"<<sec<<"}\n";
}

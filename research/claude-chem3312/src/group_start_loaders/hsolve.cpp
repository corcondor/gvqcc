// solve, for each relation: D0 ^ E(alpha,beta) ^ r(lambda) = 0 where alpha/beta/r affine in lambda over GF(2).
// input: n(chips) s_i...; then blocks: d D0 r_p alpha_p(2 words) beta_p(2 words) ; d lines: r_k alpha_k beta_k
#include <cstdio>
#include <cstdint>
#include <vector>
#include <cstdlib>
#include <random>
#include <thread>
#include <atomic>
typedef uint64_t u64; typedef uint32_t u32;
struct V{u64 a0,a1,b0,b1; u32 r;};
static inline V operator^(const V&x,const V&y){return V{x.a0^y.a0,x.a1^y.a1,x.b0^y.b0,x.b1^y.b1,x.r^y.r};}
int main(int argc,char**argv){
  int n; if(scanf("%d",&n)!=1) return 1;
  std::vector<u32> s(n); for(auto&v:s) scanf("%u",&v);
  static u32 T[16][256];
  for(int by=0;by<12;by++) for(int m=0;m<256;m++){u32 e=0; for(int b=0;b<8;b++) if(m>>b&1){int i=by*8+b; if(i<n) e^=s[i];} T[by][m]=e;}
  auto E=[&](u64 m0,u64 m1)->u32{u32 e=0; for(int by=0;by<8;by++) e^=T[by][(m0>>(8*by))&255]; for(int by=0;by<4;by++) e^=T[8+by][(m1>>(8*by))&255]; return e;};
  int d; u32 D0; int blk=0;
  std::mt19937_64 rng(12345);
  while(scanf("%d %u",&d,&D0)==2){
    V base; unsigned long long x0,x1,x2,x3; u32 r;
    scanf("%u %llu %llu %llu %llu",&r,&x0,&x1,&x2,&x3); base=V{x0,x1,x2,x3,r};
    std::vector<V> g(d); for(auto&v:g){scanf("%u %llu %llu %llu %llu",&r,&x0,&x1,&x2,&x3); v=V{x0,x1,x2,x3,r};}
    // search: low part enumerated by gray code (L bits), high part random
    int L = d<22? d : 22;
    std::atomic<bool> found(false); u64 sol_lo=0, sol_hi=0;
    unsigned nth=3; std::vector<std::thread> th;
    std::atomic<u64> tried(0);
    u64 seedb=rng();
    for(unsigned t=0;t<nth;t++) th.emplace_back([&,t](){
      std::mt19937_64 R(seedb+t*7919+1);
      for(u64 it=0; !found.load(std::memory_order_relaxed); it++){
        u64 hi = (d>L)? (R() & ((1ULL<<(d-L))-1)) : 0;
        V cur=base; for(int k=0;k<d-L;k++) if(hi>>k&1) cur=cur^g[L+k];
        u64 lo=0;
        if((D0^cur.r^E(cur.a0&cur.b0,cur.a1&cur.b1))==0){ if(!found.exchange(true)){sol_lo=0;sol_hi=hi;} break;}
        for(u64 i=1;i<(1ULL<<L);i++){
          int k=__builtin_ctzll(i); cur=cur^g[k]; lo^=1ULL<<k;
          if((D0^cur.r^E(cur.a0&cur.b0,cur.a1&cur.b1))==0){ if(!found.exchange(true)){sol_lo=lo;sol_hi=hi;} break;}
          if((i&0xFFFF)==0 && found.load(std::memory_order_relaxed)) break;
        }
        tried+= (1ULL<<L);
        if(d<=L) break;
      }
    });
    for(auto&x:th) x.join();
    if(!found){printf("NONE\n"); fflush(stdout); blk++; continue;}
    u64 lam = sol_lo | (sol_hi<<L);
    printf("%llu\n",(unsigned long long)lam); fflush(stdout);
    fprintf(stderr,"relation %d solved after ~%llu M candidates\n",blk,(unsigned long long)(tried.load()>>20));
    blk++;
  }
  return 0;
}

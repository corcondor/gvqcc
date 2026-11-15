// SPDX-License-Identifier: Apache-2.0
// Discovery ONLY: 1024 deterministic pseudorandom Boolean valuations; actual AND.
// Detect zero/one after CCX, which old scans excluded by omitting the target.
// Every candidate requires a separate exact symbolic check before use.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>
using namespace std;
constexpr int LANES=16;
struct S { array<uint64_t,LANES> v{}; bool operator==(const S&o)const{return v==o.v;} };
static S operator^(S a,const S&b){for(int j=0;j<LANES;j++)a.v[j]^=b.v[j];return a;}
static S operator&(S a,const S&b){for(int j=0;j<LANES;j++)a.v[j]&=b.v[j];return a;}
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
static uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
int main(int argc,char**argv){try{
 if(argc!=3)throw runtime_error("usage: score6-mod-zero-truth input.kmb discovery.json");
 int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
 auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
 uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
 array<uint64_t,12> p{},end{};for(uint64_t i=0;i<nr+11;i++){if(at+16>uint64_t(st.st_size))throw runtime_error("truncated packet");auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("packet invalid");if(kind){p[kind]=at;end[kind]=at+len;}at+=len;}
 auto take=[&](int c,int b){if(p[c]+b>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],b);p[c]+=b;return v;};
 uint64_t atoms=0;auto fresh=[&](){S s; for(int j=0;j<LANES;j++)s.v[j]=mix(++atoms);return s;};
 S one,zero{};one.v.fill(~uint64_t(0));vector<S> q(nq);for(auto&v:q)v=fresh();

 uint64_t weak_zero_panel=0;uint64_t depth=0,ccx=0,unconditional=0,candidates=0,cache_hits=0,abi_zero_events=0,abi_zero_max=0,abi_zero_now=0;
 uint64_t abi=min<uint64_t>(840,nq);vector<pair<uint64_t,uint32_t>> abi_events;
 ofstream out(argv[2]);if(!out)throw runtime_error("output failed");out<<"{\"status\":\"TRUTH1024_DISCOVERY_ONLY_NOT_EQUIVALENCE_PROOF\",\"candidates\":[";bool comma=false;
 auto assign=[&](uint32_t t,S value,uint64_t pos){bool was=q[t]==zero,now=value==zero;if(t<abi&&was!=now){if(now){abi_zero_now++;abi_zero_events++;if(abi_events.size()<10000)abi_events.push_back({pos,t});}else abi_zero_now--;abi_zero_max=max(abi_zero_max,abi_zero_now);}q[t]=value;};
 for(uint64_t pos=0;pos<n;pos++){
  auto op=take(1,1);int base=op&127,arity=(op>>4)&3;array<uint32_t,3> x{};for(int j=0;j<arity;j++){x[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(x[j]>=nq)throw runtime_error("q overflow");}
  int64_t bit=(op&64)?int64_t(take(8,4)):-1,cond=(op&128)?int64_t(take(9,4)):-1;if(bit>=int64_t(nb)||cond>=int64_t(nb))throw runtime_error("bit overflow");if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){depth++;continue;}if(op==0x01){if(!depth)throw runtime_error("stack underflow");depth--;continue;}
  bool guarded=depth||cond>=0;
  if(base==0x11)assign(x[0],guarded?fresh():q[x[0]]^one,pos);
  else if(base==0x21)assign(x[1],guarded?fresh():q[x[1]]^q[x[0]],pos);
  else if(base==0x22){if(guarded){assign(x[0],fresh(),pos);assign(x[1],fresh(),pos);}else{S t=q[x[0]];assign(x[0],q[x[1]],pos);assign(x[1],t,pos);}}
  else if(base==0x32){assign(x[1],fresh(),pos);assign(x[2],fresh(),pos);}
  else if(base==0x12||base==0x50)assign(x[0],guarded?fresh():zero,pos);
  else if(base==0x31){
   ccx++;if(guarded){assign(x[2],fresh(),pos);continue;}unconditional++;
   S a=q[x[0]],b=q[x[1]],prod=a&b;uint64_t origin=pos;bool trivial=false;
   S after=q[x[2]]^prod;
   if((after==zero || after==one) && prod==zero){weak_zero_panel++;}
   if((after==zero || after==one) && !(prod==zero)){
    if(comma)out<<',';comma=true;candidates++;
    out<<"{\"index\":"<<pos<<",\"controls\":["<<x[0]<<','<<x[1]<<"],\"target\":"<<x[2]<<",\"output_constant\":"<<(after==zero?0:1)<<",\"product_origin\":"<<origin<<",\"trivial_product_identity\":"<<(trivial?"true":"false")<<"}";
   }
   assign(x[2],q[x[2]]^prod,pos);
  }else if(base==0x00||base==0x10||base==0x13||base==0x20||base==0x30||base==0x40||base==0x41||base==0x42||base==0x06||base==0x07||base==0x17||base==0x47){}
  else throw runtime_error("unknown opcode");
 }
 if(depth)throw runtime_error("unclosed condition");
 out<<"],\"all_zero_product_panel_ignored\":"<<weak_zero_panel<<",\"num_ops\":"<<n<<",\"ccx\":"<<ccx<<",\"unconditional_ccx\":"<<unconditional<<",\"product_cache_hits\":"<<cache_hits<<",\"candidate_count\":"<<candidates<<",\"formal_atoms\":"<<atoms<<",\"abi_zero_events\":"<<abi_zero_events<<",\"abi_max_simultaneous_zero\":"<<abi_zero_max<<",\"first_abi_zero_events\":[";comma=false;for(auto[v,w]:abi_events){if(comma)out<<',';comma=true;out<<'['<<v<<','<<w<<']';}out<<"]}\n";
 cerr<<"CCX="<<ccx<<" candidates="<<candidates<<" cache_hits="<<cache_hits<<" ABI zeros="<<abi_zero_events<<" max="<<abi_zero_max<<"\n";munmap(d,st.st_size);close(fd);return 0;
 }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

// SPDX-License-Identifier: Apache-2.0
// Discovery ONLY: 1024-bit signatures and multi-wire span discovery of exact-form XOR/AND expressions.
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
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
struct S { array<uint64_t,16> v{}; bool operator==(const S&o)const{return v==o.v;} bool operator<(const S&o)const{return v<o.v;} };
static S operator^(const S&a,const S&b){S c;for(int i=0;i<16;i++)c.v[i]=a.v[i]^b.v[i];return c;}
static void xoreq(S&a,const S&b){for(int i=0;i<16;i++)a.v[i]^=b.v[i];}
static int pivot(const S&a){for(int i=15;i>=0;i--)if(a.v[i])return i*64+63-__builtin_clzll(a.v[i]);return -1;}
static vector<int> span_solution(const vector<S>&q,int target,const S&one,S want){
 array<S,1024> basis{},coeff{};
 auto insert=[&](S val,int idx){S c;c.v[idx/64]=uint64_t(1)<<(idx%64);for(int bit;(bit=pivot(val))>=0;){if(basis[bit].v[bit/64]){xoreq(val,basis[bit]);xoreq(c,coeff[bit]);}else{basis[bit]=val;coeff[bit]=c;break;}}};
 int nq=q.size();if(nq>=1024)throw runtime_error("span supports at most1023wires");insert(one,nq);
 for(int j=840;j<nq;j++)if(j!=target)insert(q[j],j);
 for(int j=0;j<min(840,nq);j++)if(j!=target)insert(q[j],j);
 S c;for(int bit;(bit=pivot(want))>=0;){if(!basis[bit].v[bit/64])return {};xoreq(want,basis[bit]);xoreq(c,coeff[bit]);}
 vector<int> result;for(int j=0;j<=nq;j++)if((c.v[j/64]>>(j%64))&1)result.push_back(j);return result;
}
struct K{S a,b;bool operator==(const K&o)const{return a==o.a&&b==o.b;}};
struct KH{size_t operator()(const K&k)const{return mix(k.a.v[0])^mix(k.a.v[1]+1)^mix(k.b.v[0]+2)^mix(k.b.v[1]+3);}};
struct V{S value;uint64_t origin;};
static uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
int main(int argc,char**argv){try{
 if(argc!=3)throw runtime_error("usage: xag-scan input.kmb discovery.json");
 int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
 auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
 uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
 array<uint64_t,12> p{},end{};for(uint64_t i=0;i<nr+11;i++){if(at+16>uint64_t(st.st_size))throw runtime_error("truncated packet");auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("packet invalid");if(kind){p[kind]=at;end[kind]=at+len;}at+=len;}
 auto take=[&](int c,int b){if(p[c]+b>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],b);p[c]+=b;return v;};
 uint64_t atoms=0;auto fresh=[&](){auto i=++atoms;S s;for(int j=0;j<16;j++)s.v[j]=mix(i^(0x987eadfe39a58b41ULL*j));return s;};
 S one=fresh(),zero{};vector<S> q(nq);for(auto&v:q)v=fresh();
 unordered_map<K,V,KH> products;products.reserve(400000);
 uint64_t depth=0,ccx=0,unconditional=0,candidates=0,cache_hits=0,abi_zero_events=0,abi_zero_max=0,abi_zero_now=0;
 uint64_t abi=min<uint64_t>(840,nq);vector<pair<uint64_t,uint32_t>> abi_events;
 ofstream out(argv[2]);if(!out)throw runtime_error("output failed");out<<"{\"status\":\"DISCOVERY_ONLY_NOT_EQUIVALENCE_PROOF\",\"candidates\":[";bool comma=false;
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
   S a=q[x[0]],b=q[x[1]],prod{};uint64_t origin=pos;bool trivial=true;vector<int> span;
   if(a==zero||b==zero)prod=zero;else if(a==one)prod=b;else if(b==one||a==b)prod=a;else if(a==(b^one))prod=zero;
   else{
    trivial=false;bool na=(a^one)<a,nbb=(b^one)<b;if(na)a=a^one;if(nbb)b=b^one;
    K key{a,b};if(key.b<key.a)swap(key.a,key.b);auto it=products.find(key);
    if(it==products.end()){V v{fresh(),pos};it=products.emplace(key,v).first;}else cache_hits++;
    prod=it->second.value;origin=it->second.origin;if(na)prod=prod^b;if(nbb)prod=prod^a;if(na&&nbb)prod=prod^one;
   }
   int cached=-1;bool invert=false;
   if(!(prod==zero)&&!(prod==one))for(uint32_t j=0;j<nq;j++)if(j!=x[2]&&(q[j]==prod||(q[j]^one)==prod)){cached=j;invert=!(q[j]==prod);break;}
   if(cached<0&&origin<pos&&!(prod==zero)&&!(prod==one))span=span_solution(q,x[2],one,prod);
   if(prod==zero||prod==one||cached>=0||!span.empty()){
    if(comma)out<<',';comma=true;candidates++;
    out<<"{\"index\":"<<pos<<",\"controls\":["<<x[0]<<','<<x[1]<<"],\"target\":"<<x[2]<<",\"cached_wire\":"<<cached<<",\"constant\":"<<(prod==zero?0:prod==one?1:-1)<<",\"xor_one\":"<<(invert?"true":"false")<<",\"product_origin\":"<<origin<<",\"trivial_identity\":"<<(trivial?"true":"false")<<",\"span_wires\":[";for(size_t j=0;j<span.size();j++){if(j)out<<',';out<<span[j];}out<<"]}";
   }
   assign(x[2],q[x[2]]^prod,pos);
  }else if(base==0x00||base==0x10||base==0x13||base==0x20||base==0x30||base==0x40||base==0x41||base==0x42||base==0x06||base==0x07||base==0x17||base==0x47){}
  else throw runtime_error("unknown opcode");
 }
 if(depth)throw runtime_error("unclosed condition");
 out<<"],\"num_ops\":"<<n<<",\"ccx\":"<<ccx<<",\"unconditional_ccx\":"<<unconditional<<",\"product_cache_hits\":"<<cache_hits<<",\"candidate_count\":"<<candidates<<",\"formal_atoms\":"<<atoms<<",\"abi_zero_events\":"<<abi_zero_events<<",\"abi_max_simultaneous_zero\":"<<abi_zero_max<<",\"first_abi_zero_events\":[";comma=false;for(auto[v,w]:abi_events){if(comma)out<<',';comma=true;out<<'['<<v<<','<<w<<']';}out<<"]}\n";
 cerr<<"CCX="<<ccx<<" candidates="<<candidates<<" cache_hits="<<cache_hits<<" ABI zeros="<<abi_zero_events<<" max="<<abi_zero_max<<"\n";munmap(d,st.st_size);close(fd);return 0;
 }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

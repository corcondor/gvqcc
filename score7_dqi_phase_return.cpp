// SPDX-License-Identifier: Apache-2.0
// Discovery filter for matched CCX with restored control expressions. Random
// 512-bit XOR/AND signatures are NEVER equivalence proofs or patch authority.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>
using namespace std;
static uint64_t le(const uint8_t* p,int n) {
  uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;
}
static uint64_t mix(uint64_t x) {
  x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
  x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);
}
struct S {
  array<uint64_t,8>v{};
  bool operator==(const S&b)const{return v==b.v;}
  bool operator<(const S&b)const{return v<b.v;}
};
static S operator^(S a,const S&b){for(int i=0;i<8;i++)a.v[i]^=b.v[i];return a;}
struct P {S a,b;bool operator==(const P&p)const{return a==p.a&&b==p.b;}};
struct H {size_t operator()(const P&p)const{return mix(p.a.v[0])^mix(p.b.v[0]+1);}};
struct Model {
  uint64_t ids=0;S one,zero;unordered_map<P,S,H>cache;
  Model(){one=fresh();cache.reserve(450000);}
  S fresh(){S a;for(int j=0;j<8;j++)a.v[j]=mix((ids+1)^(0x987eadfe39a58b41ULL*j));ids++;return a;}
  S mul(S a,S b) {
    if(a==zero||b==zero)return zero;
    if(a==one)return b;
    if(b==one||a==b)return a;
    if(a==(b^one))return zero;
    bool na=(a^one)<a,nb=(b^one)<b;if(na)a=a^one;if(nb)b=b^one;
    P p{a,b};if(p.b<p.a)swap(p.a,p.b);
    auto it=cache.find(p);if(it==cache.end())it=cache.emplace(p,fresh()).first;
    S c=it->second;if(na)c=c^b;if(nb)c=c^a;if(na&&nb)c=c^one;return c;
  }
};
struct Pending {uint64_t pos,epoch,barrier,bitver,phase_count;S a,b;};
struct Candidate {uint64_t first,second,phases;array<uint32_t,3>w;int64_t condition;};
int main(int argc,char**argv){try{
  if(argc!=3)throw runtime_error("usage: phase-return input.kmb discovery.json");
  int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");
  struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
  uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
  array<uint64_t,12>p{},end{};
  for(uint64_t i=0;i<nr+11;i++){
    if(at+16>uint64_t(st.st_size))throw runtime_error("truncated packet");
    auto k=le(d+at,8),len=le(d+at+8,8);at+=16;
    if(k!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("bad packet");
    if(k){p[k]=at;end[k]=at+len;}at+=len;
  }if(at!=uint64_t(st.st_size))throw runtime_error("trailing bytes");
  auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
  Model model;vector<S>q(nq);for(auto&s:q)s=model.fresh();
  vector<uint64_t>barrier(nq,0),phase_count(nq,0),bitver(nb,0);
  vector<uint32_t>stack,stack_count(nb,0);vector<vector<S>>frames;
  map<array<int64_t,4>,Pending>previous;
  vector<Candidate>candidates,control_returns;
  uint64_t epoch=0,ccx=0,ccz=0,pairs=0,epoch_reject=0,control_reject=0,target_reject=0,guard_reject=0;
  for(uint64_t pos=0;pos<n;pos++){
    int op=take(1,1),base=op&127,arity=(op>>4)&3;array<uint32_t,3>x{};
    for(int j=0;j<arity;j++){x[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(x[j]>=nq)throw runtime_error("qubit overflow");}
    int64_t bit=(op&64)?int64_t(take(8,4)):-1,condition=(op&128)?int64_t(take(9,4)):-1;
    if(bit>=int64_t(nb)||condition>=int64_t(nb))throw runtime_error("bit overflow");
    if(base==0x13){take(10,8);take(10,8);}
    if(op==0x81){stack.push_back(condition);stack_count[condition]++;frames.push_back(q);epoch++;continue;}
    if(op==0x01){
      if(stack.empty())throw runtime_error("stack underflow");
      for(uint64_t j=0;j<nq;j++)if(!(q[j]==frames.back()[j]))q[j]=model.fresh();
      frames.pop_back();stack_count[stack.back()]--;stack.pop_back();epoch++;continue;
    }
    if(base==0x10||base==0x20||base==0x30){if(base==0x30)ccz++;for(int j=0;j<arity;j++)phase_count[x[j]]++;}
    else if(base==0x31){
      ccx++;if(x[1]<x[0])swap(x[0],x[1]);
      array<int64_t,4>key{int64_t(x[0]),int64_t(x[1]),int64_t(x[2]),condition};
      auto found=previous.find(key);
      if(found!=previous.end()){
        pairs++;auto&old=found->second;
        if(old.epoch!=epoch)epoch_reject++;
        else if(!(old.a==q[x[0]])||!(old.b==q[x[1]]))control_reject++;
        else if(condition>=0&&old.bitver!=bitver[condition])guard_reject++;
        else {
          control_returns.push_back({old.pos,pos,phase_count[x[2]]-old.phase_count,x,condition});
          if(old.barrier!=barrier[x[2]])target_reject++;
          else candidates.push_back({old.pos,pos,phase_count[x[2]]-old.phase_count,x,condition});
        }
      }
      previous[key]={pos,epoch,barrier[x[2]],condition<0?0:bitver[condition],phase_count[x[2]],q[x[0]],q[x[1]]};
      q[x[2]]=condition<0?(q[x[2]]^model.mul(q[x[0]],q[x[1]])):model.fresh();
      barrier[x[0]]++;barrier[x[1]]++;
    }else if(base==0x11)q[x[0]]=condition<0?(q[x[0]]^model.one):model.fresh();
    else if(base==0x21){q[x[1]]=condition<0?(q[x[1]]^q[x[0]]):model.fresh();barrier[x[0]]++;}
    else if(base==0x22){if(condition<0)swap(q[x[0]],q[x[1]]);else{q[x[0]]=model.fresh();q[x[1]]=model.fresh();}barrier[x[0]]++;barrier[x[1]]++;}
    else if(base==0x32){
      if(condition<0){auto delta=model.mul(q[x[0]],q[x[1]]^q[x[2]]);q[x[1]]=q[x[1]]^delta;q[x[2]]=q[x[2]]^delta;}
      else{q[x[1]]=model.fresh();q[x[2]]=model.fresh();}
      for(int j=0;j<3;j++)barrier[x[j]]++;
    }else if(base==0x12||base==0x50){q[x[0]]=condition<0?model.zero:model.fresh();barrier[x[0]]++;}
    else if(base==0x40||base==0x41||base==0x42||base==0x00){}
    else epoch++;
    if(bit>=0){bitver[bit]++;if(stack_count[bit])epoch++;}
  }
  for(int k=1;k<=10;k++)if(p[k]!=end[k])throw runtime_error("unconsumed operands");
  if(!stack.empty())throw runtime_error("unclosed condition stack");
  ofstream out(argv[2]);if(!out)throw runtime_error("output failed");
  out<<"{\"schema\":\"score7-phase-return-v1\",\"status\":\"SIGNATURE_DISCOVERY_ONLY\",\"operations\":"<<n<<",\"ccx\":"<<ccx<<",\"ccz\":"<<ccz<<",\"physical_pairs\":"<<pairs<<",\"boundary_rejections\":"<<epoch_reject<<",\"control_expression_rejections\":"<<control_reject<<",\"target_use_rejections\":"<<target_reject<<",\"guard_rejections\":"<<guard_reject<<",\"candidate_count\":"<<candidates.size()<<",\"candidates\":[";
  bool comma=false;for(auto&c:candidates){if(comma)out<<",";comma=true;out<<"{\"first\":"<<c.first<<",\"second\":"<<c.second<<",\"crossed_phases\":"<<c.phases<<",\"qubits\":["<<c.w[0]<<","<<c.w[1]<<","<<c.w[2]<<"],\"condition\":"<<c.condition<<"}";}
  out<<"],\"control_return_pairs\":[";
  comma=false;for(auto&c:control_returns){if(comma)out<<",";comma=true;out<<"{\"first\":"<<c.first<<",\"second\":"<<c.second<<",\"crossed_phases\":"<<c.phases<<",\"qubits\":["<<c.w[0]<<","<<c.w[1]<<","<<c.w[2]<<"],\"condition\":"<<c.condition<<"}";}
  out<<"]}\n";munmap(d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<"\n";return 1;}}

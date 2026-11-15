// SPDX-License-Identifier: Apache-2.0
// Carry each cubic sign phase through a shared current bit frame.
#include <algorithm>
#include <array>
#include <unordered_map>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
using namespace std;
static uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
struct Write {uint64_t pos;unsigned op,depth;};
int main(int argc,char**argv){try{
 if(argc!=3)throw runtime_error("input.kmb output.json required");
 int fd=open(argv[1],O_RDONLY);struct stat st{};
 if(fd<0||fstat(fd,&st))throw runtime_error("open");
 auto*d=(const uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
 if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("KMBv2 required");
 auto nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=uint64_t(104);
 array<uint64_t,12> p{},end{};
 for(uint64_t i=0;i<nr+11;i++){
  if(at+16>uint64_t(st.st_size))throw runtime_error("packet");
  auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;
  if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("packet length");
  if(kind){p[kind]=at;end[kind]=at+len;}at+=len;
 }
 auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
 struct Phase {uint64_t pos; array<vector<uint64_t>,3> forms; unsigned constant=0;};
 const size_t nw=(nq+63)/64;
 vector<Phase> live;
 uint64_t seen=0,comparisons=0,hits=0,depth=0,eligible=0;
 const auto bit=[](const vector<uint64_t>& p,unsigned q){return (p[q/64]>>(q%64))&UINT64_C(1);};
 const auto flip=[](vector<uint64_t>& p,unsigned q){p[q/64]^=UINT64_C(1)<<(q%64);};
 const auto mask=[&](const Phase& p,unsigned q){return bit(p.forms[0],q)|(bit(p.forms[1],q)<<1)|(bit(p.forms[2],q)<<2);};
 ofstream out(argv[2]);out<<"{\"hits\":[";
 for(uint64_t i=1;i<=n;i++){
  auto op=take(1,1);unsigned base=op&127,arity=(op>>4)&3;array<unsigned,3> q{};
  for(unsigned j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("q");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("b");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){live.clear();depth++;continue;}
  if(op==0x01){live.clear();if(!depth)throw runtime_error("pop");depth--;continue;}
  if(base==0x30){
   seen++;
   if(c<0){
    eligible++;
    for(const auto& a:live){
     comparisons++;
     unsigned common=0;
     for(unsigned s=1;s<=7;s++){
      bool zero=true;
      for(size_t w=0;w<nw&&zero;w++){
       uint64_t p=0;
       for(unsigned j=0;j<3;j++)if(s&(1u<<j))p^=a.forms[j][w];
       for(auto v:q)if(v/64==w)p &= ~(UINT64_C(1)<<(v%64));
       zero=p==0;
      }
      if(zero)common++;
     }
     if(common>=3){
      if(hits++)out<<',';
      out<<"{\"first\":"<<a.pos-1<<",\"second\":"<<i-1<<",\"branch_depth\":"<<depth
         <<",\"intersection_dimension\":"<<(common==7?3:2)<<",\"phase_constants\":"<<a.constant
         <<",\"second_support\":["<<q[0]<<','<<q[1]<<','<<q[2]<<"],\"first_forms_current\":[";
      for(unsigned j=0;j<3;j++){
       if(j)out<<',';out<<'[';bool comma=false;
       for(unsigned v=0;v<nq;v++)if(bit(a.forms[j],v)){if(comma)out<<',';comma=true;out<<v;}
       out<<']';
      }
      out<<"]}";
     }
    }
    Phase a{i,{vector<uint64_t>(nw),vector<uint64_t>(nw),vector<uint64_t>(nw)},0};
    for(unsigned j=0;j<3;j++)flip(a.forms[j],q[j]);
    live.push_back(move(a));
   }
  }
  if(live.empty())continue;
  if(base==0x11||base==0x12||base==0x50||base==0x21||base==0x31||base==0x22||base==0x32){
   live.erase(remove_if(live.begin(),live.end(),[&](Phase& a){
    if(base==0x12||base==0x50||base==0x31)return mask(a,q[arity-1])!=0;
    if(base==0x32||base==0x22){
     auto exchange=mask(a,q[arity-2])^mask(a,q[arity-1]);
     if(base==0x32||c>=0)return exchange!=0;
     for(unsigned j=0;j<3;j++)if(exchange&(1u<<j)){
      flip(a.forms[j],q[0]);flip(a.forms[j],q[1]);
     }
     return false;
    }
    auto target=mask(a,q[arity-1]);
    if(c>=0)return target!=0;
    if(base==0x11){a.constant^=target;return false;}
    for(unsigned j=0;j<3;j++)if(target&(1u<<j))flip(a.forms[j],q[0]);
    return false;
   }),live.end());
  }
 }
 if(depth)throw runtime_error("unclosed");
 out<<"],\"ccz\":"<<seen<<",\"eligible\":"<<eligible<<",\"pairs_compared\":"<<comparisons
    <<",\"hit_count\":"<<hits<<",\"num_ops\":"<<n<<"}\n";
 munmap((void*)d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

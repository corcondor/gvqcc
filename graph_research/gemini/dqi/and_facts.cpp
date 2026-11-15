// SPDX-License-Identifier: Apache-2.0
// Implication propagation from measured-reset/AND chains in feasible condition scopes.
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
 struct Fact {unsigned q; uint64_t version; bool value;};
 struct Facts {uint64_t scope; bool active=false; vector<Fact> implications;};
 vector<Facts> q1(nq);
 vector<uint64_t> stack{0};
 vector<uint64_t> version(nq);
 vector<int64_t> clean_scope(nq,-1);
 for(unsigned q=840;q<nq;q++)clean_scope[q]=0;
 const auto contains=[&](uint64_t id){return find(stack.begin(),stack.end(),id)!=stack.end();};
 const auto implies=[&](unsigned a,unsigned b){
  if(clean_scope[b]>=0&&contains(clean_scope[b]))return 0;
  if(!q1[a].active||!contains(q1[a].scope))return -1;
  for(auto v:q1[a].implications)if(v.q==b&&v.version==version[b])return v.value?1:0;
  return -1;
 };
 uint64_t counts[3]{},zero=0;
 ofstream out(argv[2]);out<<"{\"hits\":[";
 bool comma=false;
 const auto report=[&](uint64_t i,unsigned code,const array<unsigned,3>& q,unsigned a,unsigned b,int value){
  if(comma)out<<',';comma=true;
  out<<"{\"index\":"<<i<<",\"op\":"<<code<<",\"operands\":["<<q[0]<<','<<q[1]<<','<<q[2]
     <<"],\"guard\":"<<a<<",\"implied\":"<<b<<",\"value\":"<<value<<",\"depth\":"<<stack.size()-1<<"}";
 };
 for(uint64_t i=0;i<n;i++){
  auto op=take(1,1);unsigned base=op&127,arity=(op>>4)&3;array<unsigned,3> q{};
  for(unsigned j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("q");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("b");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){stack.push_back(i+1);continue;}
  if(op==0x01){if(stack.size()==1)throw runtime_error("pop");stack.pop_back();continue;}
  if(base==0x31||base==0x30){
   unsigned type=(base==0x31)?0:1;
   unsigned lim=(type==0)?2:3;
   bool hit=false;
   for(unsigned x=0;x<lim&&!hit;x++)for(unsigned y=0;y<lim&&!hit;y++)if(x!=y){
    int v=implies(q[x],q[y]);if(v>=0){
     counts[type]++;zero+=(v==0);report(i,base,q,q[x],q[y],v);hit=true;
    }
   }
  }else if(base==0x32){
   int a=implies(q[0],q[1]),b=implies(q[0],q[2]);
   if(a>=0&&b>=0){counts[2]++;zero+=(a==b);report(i,base,q,q[1],q[2],a|(b<<1));}
  }
  const auto clear=[&](unsigned q){version[q]=i+1;clean_scope[q]=-1;q1[q].active=false;};
  if(base==0x12||base==0x50){clear(q[0]);if(c<0)clean_scope[q[0]]=stack.back();}
  else if(base==0x11){clear(q[0]);}
  else if(base==0x21){clear(q[1]);}
  else if(base==0x22||base==0x32){clear(q[arity-2]);clear(q[arity-1]);}
  else if(base==0x31){
   const auto t=q[2];
   const bool make=c<0&&clean_scope[t]>=0&&contains(clean_scope[t]);
   clear(t);
   if(make){
    auto& f=q1[t];f.scope=stack.back();f.active=true;f.implications.clear();
    for(unsigned j=0;j<2;j++){
     const auto a=q[j];f.implications.push_back({a,version[a],true});
     if(q1[a].active&&contains(q1[a].scope)){
      for(const auto& fact:q1[a].implications)
       if(version[fact.q]==fact.version)f.implications.push_back(fact);
     }
    }
   }
  }else if(base==0x00||base==0x06||base==0x07||base==0x10||base==0x13||base==0x17||base==0x20||base==0x30||base==0x40||base==0x41||base==0x42||base==0x47){}
  else throw runtime_error("unsupported opcode");
 }
 if(stack.size()!=1)throw runtime_error("unclosed");
 out<<"],\"ccx\":"<<counts[0]<<",\"ccz\":"<<counts[1]<<",\"cswap\":"<<counts[2]
    <<",\"zero\":"<<zero<<",\"num_ops\":"<<n<<"}\n";
 munmap((void*)d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

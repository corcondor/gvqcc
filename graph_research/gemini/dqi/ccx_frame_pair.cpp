// SPDX-License-Identifier: Apache-2.0
// Search CCX pairs sharing abstract affine control forms or transported target differences.
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
 struct Candidate {
  uint64_t pos; unsigned a,b,t; vector<unsigned> delta; vector<pair<uint64_t,unsigned>> measurements;
  array<vector<uint64_t>,2> forms; unsigned constant=0;
 };
 const size_t nw=(nq+63)/64;
 const auto bit=[](const vector<uint64_t>& p,unsigned q){return (p[q/64]>>(q%64))&UINT64_C(1);};
 const auto inv=[](vector<uint64_t>& p,unsigned q){p[q/64]^=UINT64_C(1)<<(q%64);};
 const auto mask=[&](const Candidate& p,unsigned q){return bit(p.forms[0],q)|(bit(p.forms[1],q)<<1);};
 vector<Candidate> live;
 uint64_t seen=0,success=0,branches=0,horizon=0,writes=0,nonlinear=0,phase=0,reset=0,conditional=0,depth=0,pairs_compared=0;
 ofstream out(argv[2]);out<<"{\"hits\":[";
 for(uint64_t i=1;i<=n;i++){
  auto op=take(1,1);unsigned base=op&127,arity=(op>>4)&3;array<unsigned,3> q{};
  for(unsigned j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("q");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("b");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81||op==0x01){
   branches+=live.size();live.clear();
   if(op==0x81)depth++;
   else {if(!depth)throw runtime_error("pop");depth--;}
   continue;
  }
  if(arity>0){
   live.erase(remove_if(live.begin(),live.end(),[&](Candidate& a){
    if(i-a.pos>8192){horizon++;return true;}
    const auto written=[&](unsigned wire){
     if(mask(a,wire)){writes++;return true;}return false;
    };
    const auto diff=[&](unsigned wire){return find(a.delta.begin(),a.delta.end(),wire)!=a.delta.end();};
    const auto flip=[&](unsigned wire){
     auto it=find(a.delta.begin(),a.delta.end(),wire);if(it==a.delta.end())a.delta.push_back(wire);else a.delta.erase(it);
    };
    if(base==0x13||base==0x10||base==0x20||base==0x30){
     for(unsigned j=0;j<arity;j++)if(diff(q[j])){phase++;return true;}
     return false;
    }
    if(base==0x50){
     if(written(q[0]))return true;
     if(!diff(q[0]))return false;
     reset++;return true;
    }
    if(base==0x12){if(written(q[0]))return true;if(diff(q[0])){reset++;return true;}return false;}
    if(base==0x11){
     const auto target=mask(a,q[0]);if(c>=0&&target){conditional++;return true;}
     a.constant^=target;return false;
    }
    if(base==0x21){
     const auto target=mask(a,q[1]);
     if(c>=0&&(target||diff(q[0]))){conditional++;return true;}
     for(unsigned j=0;j<2;j++)if(target&(1u<<j))inv(a.forms[j],q[0]);
     if(diff(q[0]))flip(q[1]);
     return false;
    }
    if(base==0x22){
     const auto x=mask(a,q[0])^mask(a,q[1]);const bool p=diff(q[0])!=diff(q[1]);
     if(c>=0&&(x||p)){conditional++;return true;}
     for(unsigned j=0;j<2;j++)if(x&(1u<<j)){inv(a.forms[j],q[0]);inv(a.forms[j],q[1]);}
     if(p){flip(q[0]);flip(q[1]);}
     return false;
    }
    if(base==0x31){
     if(c<0&&(!diff(q[0])&&!diff(q[1]))&&(a.delta.size()==1&&a.delta[0]==q[2]||!mask(a,q[2]))){
      const auto& first=a.forms[0];const auto& second=a.forms[1];
      const bool same_target=a.delta.size()==1&&a.delta[0]==q[2];
      bool combines=false;
      unsigned shared=0;
      for(unsigned ss=1;ss<=3;ss++){
       bool check=true;
       for(size_t w=0;w<nw&&check;w++){
        uint64_t m=(ss&1?first[w]:0)^(ss&2?second[w]:0);
        for(unsigned j=0;j<2;j++)if(q[j]/64==w)m&=~(UINT64_C(1)<<(q[j]%64));
        check=m==0;
       }
       if(check)shared++;
      }
      pairs_compared++;
      combines=(shared==3||same_target&&shared>=1);
      if(combines){
       if(success++)out<<',';
       out<<"{\"first\":"<<a.pos-1<<",\"second\":"<<i-1
          <<",\"depth\":"<<depth<<",\"intersection_dimension\":"<<(shared==3?2:1)
          <<",\"same_target\":"<<(same_target?"true":"false")<<",\"control_constants\":"<<a.constant
          <<",\"second_controls\":["<<q[0]<<','<<q[1]<<"],\"second_target\":"<<q[2]
          <<",\"first_delta_current\":[";
       for(size_t j=0;j<a.delta.size();j++){if(j)out<<',';out<<a.delta[j];}
       out<<"],\"first_forms_current\":[";
       for(unsigned j=0;j<2;j++){
        if(j)out<<',';out<<'[';bool comma=false;
        for(unsigned w=0;w<nq;w++)if(bit(a.forms[j],w)){if(comma)out<<',';comma=true;out<<w;}
        out<<']';
       }
       out<<"]}";
      }
     }
     if(written(q[2]))return true;
     if(diff(q[0])||diff(q[1])){nonlinear++;return true;}
     return false;
    }
    if(base==0x32){
     if(mask(a,q[1])!=mask(a,q[2])){writes++;return true;}
     if(diff(q[0])||diff(q[1])!=diff(q[2])){nonlinear++;return true;}
     return false;
    }
    return false;
   }),live.end());
  }
  if(base==0x31&&c<0){
   seen++;
   Candidate a{i,q[0],q[1],q[2],{q[2]},{},{vector<uint64_t>(nw),vector<uint64_t>(nw)},0};
   inv(a.forms[0],q[0]);inv(a.forms[1],q[1]);live.push_back(move(a));
  }
 }
 if(depth)throw runtime_error("unclosed");
 out<<"],\"ccx\":"<<seen<<",\"hit_count\":"<<success<<",\"pairs_compared\":"<<pairs_compared<<",\"barriers\":{\"branch\":"<<branches
    <<",\"horizon\":"<<horizon<<",\"control_write\":"<<writes<<",\"nonlinear\":"<<nonlinear
    <<",\"phase\":"<<phase<<",\"reset\":"<<reset<<",\"conditional\":"<<conditional
    <<",\"live_at_end\":"<<live.size()<<"},\"num_ops\":"<<n<<"}\n";
 munmap((void*)d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

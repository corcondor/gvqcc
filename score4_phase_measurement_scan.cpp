// SPDX-License-Identifier: Apache-2.0
// Find exact CCZ merges across independent measurements/classical operations.
// No simulator, seed, or data-dependent arithmetic is used in this scan.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <tuple>
#include <unistd.h>
#include <vector>
using namespace std;
static uint64_t le(const uint8_t* p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
struct Gate{uint64_t pos;array<uint32_t,3> q;int64_t condition;string guard;};
struct Frame{uint64_t push;uint32_t bit;};
int main(int argc,char**argv){try{
  if(argc!=3&&argc!=4)throw runtime_error("usage: scanner input.kmb result.json [--different-guards]");
  bool different=argc==4&&string(argv[3])=="--different-guards";
  int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");
  struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
  const uint8_t magic[]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
  if(memcmp(d,magic,16))throw runtime_error("magic mismatch");
  uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
  array<uint64_t,12> p{},end{};
  for(uint64_t i=0;i<nr+11;i++){
    if(at+16>uint64_t(st.st_size))throw runtime_error("packet header truncated");
    auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;
    if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("packet invalid");
    if(kind){p[kind]=at;end[kind]=at+len;}at+=len;
  }
  auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
  vector<int64_t> written_q(nq,-1),written_b(nb,-1);
  vector<Frame> stack;
  map<tuple<uint32_t,uint32_t,string>,vector<Gate>> previous;
  ofstream out(argv[2]);if(!out)throw runtime_error("output open failed");
  out<<"{\"schema\":\"phase-measurement-commutation-v1\",\"opportunities\":[";
  uint64_t seen=0,pairs=0,found=0;bool comma=false;
  for(uint64_t pos=0;pos<n;pos++){
    auto op=take(1,1);int base=op&127,arity=(op>>4)&3;
    array<uint32_t,3> q{};
    for(int j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("qubit overflow");}
    int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
    if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("bit overflow");
    if(base==0x13){take(10,8);take(10,8);}
    if(op==0x81){stack.push_back({pos,uint32_t(c)});continue;}
    if(op==0x01){if(stack.empty())throw runtime_error("empty pop");stack.pop_back();continue;}
    if(base==0x30){
      seen++;string guard;
      for(auto f:stack)guard+=to_string(f.push)+":"+to_string(f.bit)+":"+to_string(written_b[f.bit])+";";
      guard+="if:"+to_string(c)+":"+(c<0?string("-"):to_string(written_b[c]));
      array<uint32_t,3> sorted=q;sort(sorted.begin(),sorted.end());
      for(int missing=0;missing<3;missing++){
        vector<uint32_t> ab;for(int j=0;j<3;j++)if(j!=missing)ab.push_back(sorted[j]);
        auto key=make_tuple(ab[0],ab[1],different?string():guard);auto&v=previous[key];
        for(auto it=v.rbegin();it!=v.rend();++it){
          const auto&first=*it; // A finite source list; no arbitrary window cutoff.
          bool right=true,left=true;for(int j=0;j<3;j++){right&=written_q[first.q[j]]<int64_t(first.pos);left&=written_q[q[j]]<int64_t(first.pos);}
          pairs++;if(!right&&!left)continue;
          auto fq=first.q;sort(fq.begin(),fq.end());bool cancel=fq==sorted;
          if(cancel&&missing!=0)continue;
          uint32_t fc=0,sc=0;for(auto x:first.q)if(x!=ab[0]&&x!=ab[1])fc=x;for(auto x:q)if(x!=ab[0]&&x!=ab[1])sc=x;
          if(comma)out<<',';
          comma=true;found++;
          out<<"{\"first\":"<<first.pos<<",\"second\":"<<pos<<",\"common\":["<<ab[0]<<','<<ab[1]<<"],\"extras\":["<<fc<<','<<sc<<"],\"direction\":\""<<(right?"first_right":"second_left")<<"\",\"cancel_pair\":"<<(cancel?"true":"false")<<",\"same_guard\":"<<(first.guard==guard?"true":"false")<<",\"first_guard\":\""<<first.guard<<"\",\"second_guard\":\""<<guard<<"\",\"condition\":"<<c<<",\"stack_depth\":"<<stack.size()<<'}';
          break;
        }
        v.push_back({pos,q,c,guard});
      }
    }
    if(base==0x11||base==0x21||base==0x31)written_q[q[arity-1]]=pos;
    else if(base==0x22||base==0x32){written_q[q[arity-2]]=pos;written_q[q[arity-1]]=pos;}
    else if(base==0x12||base==0x50)written_q[q[0]]=pos;
    else if(base==0x00||base==0x10||base==0x13||base==0x20||base==0x30||base==0x40||base==0x41||base==0x42||base==0x06||base==0x07||base==0x17||base==0x47){}
    else throw runtime_error("unknown opcode");
    if(base==0x50||base==0x40||base==0x41||base==0x42)written_b[b]=pos;
  }
  if(!stack.empty())throw runtime_error("unclosed stack");
  out<<"],\"ccz_seen\":"<<seen<<",\"same_guard_pair_comparisons\":"<<pairs<<",\"found\":"<<found<<",\"num_qubits\":"<<nq<<",\"num_ops\":"<<n<<"}\n";
  cerr<<"CCZ="<<seen<<" candidates="<<found<<" comparisons="<<pairs<<"\n";
  munmap(d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

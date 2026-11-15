// SPDX-License-Identifier: Apache-2.0
// Common-control same-target CCX factoring through independent measurements and control flow.
// Capturing the earlier classical guard makes intervening bit writes harmless.
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
#include <unistd.h>
#include <vector>
#include <unordered_set>
using namespace std;
static uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
struct Gate{uint64_t pos;array<uint32_t,3> q;int64_t condition;size_t depth;string guard;};
int main(int argc,char**argv){try{
 if(argc!=3)throw runtime_error("usage: scanner input.kmb result.json");
 int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");
 struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
 auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
 if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
 uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
 array<uint64_t,12> p{},end{};
 for(uint64_t i=0;i<nr+11;i++){
  if(at+16>uint64_t(st.st_size))throw runtime_error("packet header truncated");
  auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;
  if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("packet invalid");
  if(kind){p[kind]=at;end[kind]=at+len;}at+=len;
 }
 auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
 vector<int64_t> w(nq,-1),read(nq,-1),wb(nb,-1);vector<string> stack;
 map<pair<uint32_t,uint32_t>,vector<Gate>> previous;unordered_set<uint64_t> used;
 ofstream out(argv[2]);if(!out)throw runtime_error("output open failed");
 out<<"{\"schema\":\"unconditional-ccx-shared-control-fanin-v1\",\"opportunities\":[";
 uint64_t seen=0,pairs=0,found=0;bool comma=false;
 for(uint64_t pos=0;pos<n;pos++){
  auto op=take(1,1);int base=op&127,arity=(op>>4)&3;array<uint32_t,3> q{};
  for(int j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("qubit overflow");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("bit overflow");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){stack.push_back(to_string(pos)+":"+to_string(c)+":"+to_string(wb[c]));continue;}
  if(op==0x01){if(stack.empty())throw runtime_error("empty pop");stack.pop_back();continue;}
  if(base==0x31){
   seen++;string guard;for(auto&s:stack)guard+=s+";";guard+="if:"+to_string(c)+":"+(c<0?string("-"):to_string(wb[c]));
   bool emitted=false;
   for(int side=0;side<2&&!emitted;side++){
    uint32_t common=q[side],target=q[2];auto&v=previous[{common,target}];
    int64_t barrier=max(w[common],read[target]);
    if(!v.empty()&&int64_t(v.back().pos)<barrier)v.clear();
    for(auto it=v.rbegin();it!=v.rend();++it){
     const auto&f=*it;if(int64_t(f.pos)<barrier)break;pairs++;
     if(used.count(f.pos)||f.condition!=-1||c!=-1||f.depth||!stack.empty())continue;
     if(max(w[f.q[0]],w[f.q[1]])>int64_t(f.pos)||read[f.q[2]]>int64_t(f.pos))continue;
     uint32_t left=f.q[0]==common?f.q[1]:f.q[0],right=q[1-side];
     if(left==right)continue;
     if(comma)out<<',';comma=true;found++;emitted=true;used.insert(f.pos);used.insert(pos);
     out<<"{\"first\":"<<f.pos<<",\"second\":"<<pos<<",\"common_control\":"<<common<<",\"other_controls\":["<<left<<','<<right<<"],\"target\":"<<target<<",\"first_depth\":0,\"second_depth\":0,\"first_condition\":-1,\"second_condition\":-1}";break;
    }
   }
   for(int side=0;side<2;side++)previous[{q[side],q[2]}].push_back({pos,q,c,stack.size(),guard});
  }
  if(base==0x11||base==0x21||base==0x31){
   w[q[arity-1]]=pos;for(int j=0;j<arity-1;j++)read[q[j]]=pos;
  }else if(base==0x22||base==0x32){
   for(int j=0;j<arity;j++)read[q[j]]=pos;
   w[q[arity-2]]=pos;w[q[arity-1]]=pos;
  }else if(base==0x12||base==0x50){read[q[0]]=pos;w[q[0]]=pos;
  }else if(base==0x10||base==0x13||base==0x20||base==0x30){for(int j=0;j<arity;j++)read[q[j]]=pos;
  }else if(base==0x00||base==0x40||base==0x41||base==0x42||base==0x06||base==0x07||base==0x17||base==0x47){}
  else throw runtime_error("unknown opcode");
  if(base==0x50||base==0x40||base==0x41||base==0x42)wb[b]=pos;
 }
 if(!stack.empty())throw runtime_error("unclosed stack");
 out<<"],\"ccx_seen\":"<<seen<<",\"pair_comparisons\":"<<pairs<<",\"found\":"<<found<<",\"num_qubits\":"<<nq<<",\"num_ops\":"<<n<<"}\n";
 cerr<<"CCX="<<seen<<" candidates="<<found<<" comparisons="<<pairs<<"\n";
 munmap(d,st.st_size);close(fd);return 0;
 }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

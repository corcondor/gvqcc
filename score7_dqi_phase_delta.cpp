// SPDX-License-Identifier: Apache-2.0
// Propagate a removed CCX's f=ab discrepancy through all intermediate
// CNOTs/SWAPs. A discrepancy bit denotes exactly f, not a sampled truth value.
// Any nonlinear control, measurement/reset, or conditional write that cannot
// preserve this form rejects the pair. A surviving pair still requires an
// independent exact proof of its endpoint control-function equality.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
using namespace std;
static uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
struct Test {
  uint64_t first,second;uint32_t a,b,t;array<bool,1024>delta{};
  bool started=false,finished=false;string result="pending";uint64_t witness=0;
  vector<uint64_t>phase_ops;
};
int main(int argc,char**argv){try{
  if(argc!=4)throw runtime_error("usage: phase-delta input.kmb pairs.txt result.json");
  vector<Test>tests;ifstream in(argv[2]);if(!in)throw runtime_error("pairs input failed");
  Test temp;while(in>>temp.first>>temp.second>>temp.a>>temp.b>>temp.t)tests.push_back(temp);
  sort(tests.begin(),tests.end(),[](auto&a,auto&b){return a.first<b.first;});
  int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");
  struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
  uint64_t nq=le(d+20,4),nr=le(d+28,4),n=le(d+32,8),at=104;
  if(nq>1024)throw runtime_error("max 1024 qubits");
  array<uint64_t,12>p{},end{};
  for(uint64_t i=0;i<nr+11;i++){
    if(at+16>uint64_t(st.st_size))throw runtime_error("truncated packet");
    auto k=le(d+at,8),len=le(d+at+8,8);at+=16;
    if(k!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("bad packet");
    if(k){p[k]=at;end[k]=at+len;}at+=len;
  }if(at!=uint64_t(st.st_size))throw runtime_error("trailing bytes");
  auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
  vector<size_t>active;size_t next=0;uint64_t touched=0,surviving=0;
  for(uint64_t pos=0;pos<n;pos++){
    int op=take(1,1),base=op&127,arity=(op>>4)&3;array<uint32_t,3>x{};
    for(int j=0;j<arity;j++){x[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(x[j]>=nq)throw runtime_error("qubit overflow");}
    int64_t bit=(op&64)?int64_t(take(8,4)):-1,cond=(op&128)?int64_t(take(9,4)):-1;(void)bit;
    if(base==0x13){take(10,8);take(10,8);}
    for(size_t ix:active){
      auto&test=tests[ix];if(test.finished)continue;touched++;
      auto reject=[&](const string&why){test.finished=true;test.result=why;test.witness=pos;};
      if(pos==test.second){
        if(base!=0x31||cond>=0||x[2]!=test.t||min(x[0],x[1])!=test.a||max(x[0],x[1])!=test.b)throw runtime_error("second endpoint mismatch");
        bool expected=test.delta[test.t]&&!test.delta[test.a]&&!test.delta[test.b];
        for(uint32_t q=0;q<nq;q++)if(q!=test.t&&test.delta[q])expected=false;
        test.finished=true;test.witness=pos;test.result=expected?"VALUE_DELTA_CLOSED_REQUIRES_PHASE_AND_ENDPOINT_PROOF":"residual_output_delta";
        if(expected)surviving++;
      }else if(op==0x81||op==0x01)reject("condition_boundary");
      else if(base==0x10||base==0x20||base==0x30){
        bool affected=false;for(int j=0;j<arity;j++)affected|=test.delta[x[j]];
        if(affected)test.phase_ops.push_back(pos);
      }else if(base==0x11){}
      else if(base==0x21){
        if(cond>=0&&test.delta[x[0]])reject("classical_controlled_fanout");
        else test.delta[x[1]]=test.delta[x[1]]^test.delta[x[0]];
      }else if(base==0x31){
        if(test.delta[x[0]]||test.delta[x[1]])reject("nonlinear_control_delta");
      }else if(base==0x22){
        if(cond>=0&&test.delta[x[0]]!=test.delta[x[1]])reject("classical_controlled_swap");
        else swap(test.delta[x[0]],test.delta[x[1]]);
      }else if(base==0x32){
        if(test.delta[x[0]]||test.delta[x[1]]!=test.delta[x[2]])reject("fredkin_nonlinear_delta");
      }else if(base==0x12||base==0x50){if(test.delta[x[0]])reject(base==0x50?"measured_delta":"reset_delta");}
      else if(base==0x40||base==0x41||base==0x42||base==0x00){}
      else reject("unsupported_operation");
    }
    active.erase(remove_if(active.begin(),active.end(),[&](size_t i){return tests[i].finished;}),active.end());
    while(next<tests.size()&&tests[next].first==pos){
      auto&test=tests[next];
      if(base!=0x31||cond>=0||x[2]!=test.t||min(x[0],x[1])!=test.a||max(x[0],x[1])!=test.b)throw runtime_error("first endpoint mismatch");
      test.started=true;test.delta[test.t]=true;active.push_back(next++);
    }
  }
  for(int k=1;k<=10;k++)if(p[k]!=end[k])throw runtime_error("unconsumed operand bytes");
  if(next!=tests.size()||!active.empty())throw runtime_error("unfinished intervals");
  ofstream out(argv[3]);if(!out)throw runtime_error("output failed");
  out<<"{\"schema\":\"score7-phase-delta-v1\",\"interval_count\":"<<tests.size()<<",\"propagation_steps\":"<<touched<<",\"surviving_count\":"<<surviving<<",\"intervals\":[";
  bool comma=false;for(auto&t:tests){if(comma)out<<",";comma=true;out<<"{\"first\":"<<t.first<<",\"second\":"<<t.second<<",\"qubits\":["<<t.a<<","<<t.b<<","<<t.t<<"],\"status\":\""<<t.result<<"\",\"witness_op\":"<<t.witness<<",\"affected_phase_ops\":[";bool c=false;for(auto pos:t.phase_ops){if(c)out<<",";c=true;out<<pos;}out<<"]}";}
  out<<"]}\n";munmap(d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<"\n";return 1;}}

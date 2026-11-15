// SPDX-License-Identifier: Apache-2.0
// Exact CCX-involution elimination through diagonal phases. All wire values
// are arbitrary, including dirty ancillas. No sampled signatures are used.
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
  uint64_t x=0; for(int i=0;i<n;i++) x|=uint64_t(p[i])<<(8*i); return x;
}
struct Phase {
  uint64_t pos;
  vector<pair<uint32_t,uint64_t>> wires;
  int64_t condition;
  uint64_t condition_version;
};
struct Pending {
  uint64_t pos,epoch,ca,cb,target_barrier,condition_version,phase_index;
};
struct Correction {
  uint64_t pos;
  vector<uint32_t> wires;
  int64_t condition;
};
struct Candidate {
  uint64_t first,second;
  array<uint32_t,3> wires;
  int64_t condition;
  uint64_t crossed_phases,nonclifford;
  vector<Correction> corrections;
};
int main(int argc,char** argv) { try {
  if(argc!=3) throw runtime_error("usage: phase-commute input.kmb result.json");
  int fd=open(argv[1],O_RDONLY); if(fd<0) throw runtime_error("open failed");
  struct stat st{}; if(fstat(fd,&st)) throw runtime_error("stat failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2) throw runtime_error("not KMBv2");
  uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
  array<uint64_t,12> p{},end{};
  for(uint64_t i=0;i<nr+11;i++) {
    if(at+16>uint64_t(st.st_size)) throw runtime_error("truncated packet");
    auto kind=le(d+at,8),len=le(d+at+8,8); at+=16;
    if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at) throw runtime_error("invalid packet");
    if(kind) { p[kind]=at; end[kind]=at+len; } at+=len;
  }
  if(at!=uint64_t(st.st_size)) throw runtime_error("trailing bytes");
  auto take=[&](int c,int bytes) {
    if(p[c]+bytes>end[c]) throw runtime_error("column exhausted");
    auto v=le(d+p[c],bytes); p[c]+=bytes; return v;
  };
  vector<uint64_t> writes(nq,0),barriers(nq,0),bitver(nb,0);
  vector<vector<Phase>> phases(nq);
  vector<uint32_t> stack;
  vector<uint32_t> stack_count(nb,0);
  // Last gate under exactly the same explicit condition and physical wires.
  map<array<int64_t,4>,Pending> previous;
  vector<Candidate> candidates;
  uint64_t epoch=0,ccx=0,ccz=0,diagonal=0,physical_pairs=0;
  uint64_t eligible_pairs=0,phase_pairs=0,phase_crossings=0,quartic_reject=0;
  uint64_t expensive_reject=0,boundary_reject=0,control_reject=0,target_reject=0;
  uint64_t explicit_reject=0,unknown_barriers=0;
  for(uint64_t pos=0;pos<n;pos++) {
    auto op=take(1,1); int base=op&127,arity=(op>>4)&3; array<uint32_t,3>x{};
    for(int j=0;j<arity;j++) {
      x[j]=take(arity==3?2+j:arity==2?5+j:7,4);
      if(x[j]>=nq) throw runtime_error("qubit overflow");
    }
    int64_t bit=(op&64)?int64_t(take(8,4)):-1,condition=(op&128)?int64_t(take(9,4)):-1;
    if(bit>=int64_t(nb)||condition>=int64_t(nb)) throw runtime_error("bit overflow");
    if(base==0x13) { take(10,8); take(10,8); }
    if(op==0x81) {
      if(condition<0) throw runtime_error("missing PUSH bit");
      stack.push_back(condition);stack_count[condition]++;epoch++;continue;
    }
    if(op==0x01) {
      if(stack.empty()) throw runtime_error("stack underflow");
      stack_count[stack.back()]--;stack.pop_back();epoch++;continue;
    }
    if(base==0x10||base==0x20||base==0x30) {
      diagonal++; if(base==0x30)ccz++;
      Phase phase{pos,{},condition,condition<0?0:bitver[condition]};
      for(int j=0;j<arity;j++)phase.wires.push_back({x[j],writes[x[j]]});
      for(int j=0;j<arity;j++)phases[x[j]].push_back(phase);
    } else if(base==0x31) {
      ccx++; if(x[1]<x[0])swap(x[0],x[1]);
      array<int64_t,4>key{int64_t(x[0]),int64_t(x[1]),int64_t(x[2]),condition};
      auto found=previous.find(key);
      if(found!=previous.end()) {
        physical_pairs++;
        auto old=found->second;
        if(old.epoch!=epoch) boundary_reject++;
        else if(old.ca!=writes[x[0]]||old.cb!=writes[x[1]]) control_reject++;
        else if(old.target_barrier!=barriers[x[2]]) target_reject++;
        else if(condition>=0&&old.condition_version!=bitver[condition])explicit_reject++;
        else {
          eligible_pairs++;
          Candidate cand{old.pos,pos,x,condition,phases[x[2]].size()-old.phase_index,0,{}};
          if(cand.crossed_phases)phase_pairs++;
          phase_crossings+=cand.crossed_phases;
          // Exact parity cancellation of correction monomials. The wire write
          // versions certify unchanged operands between two occurrences.
          // Explicitly conditioned CCX is currently conservative: accept only
          // equal/no explicit phase condition, avoiding condition conjunctions.
          using K=vector<pair<int64_t,uint64_t>>;
          map<K,Correction> residual;
          bool incompatible=false;
          for(uint64_t j=old.phase_index;j<phases[x[2]].size();j++) {
            auto& phase=phases[x[2]][j];
            if(condition>=0&&phase.condition>=0&&phase.condition!=condition) {
              incompatible=true;break;
            }
            int64_t guard=condition>=0?condition:phase.condition;
            uint64_t guardver=condition>=0?old.condition_version:phase.condition_version;
            map<uint32_t,uint64_t>w{{x[0],writes[x[0]]},{x[1],writes[x[1]]}};
            for(auto q:phase.wires)if(q.first!=x[2])w.emplace(q);
            K ck{{-1,guard<0?0:uint64_t(guard)+1},{-2,guardver}};
            Correction correction{phase.pos,{},guard};
            for(auto q:w) {ck.push_back({q.first,q.second});correction.wires.push_back(q.first);}
            auto r=residual.find(ck);
            if(r==residual.end())residual.emplace(ck,correction);else residual.erase(r);
          }
          if(incompatible)explicit_reject++;
          else {
            bool quartic=false;
            for(auto& r:residual) {
              auto corr=r.second;
              if(corr.wires.size()>3)quartic=true;
              else if(corr.wires.size()==3)cand.nonclifford++;
              cand.corrections.push_back(corr);
            }
            if(quartic)quartic_reject++;
            else if(cand.nonclifford>=2)expensive_reject++;
            else candidates.push_back(cand);
          }
        }
      }
      previous[key]=Pending{pos,epoch,writes[x[0]],writes[x[1]],barriers[x[2]],
                            condition<0?0:bitver[condition],phases[x[2]].size()};
      writes[x[2]]++;barriers[x[0]]++;barriers[x[1]]++;
    } else if(base==0x11)writes[x[0]]++;
    else if(base==0x21) {writes[x[1]]++;barriers[x[0]]++;}
    else if(base==0x22||base==0x32) {
      for(int j=0;j<arity;j++)barriers[x[j]]++;
      if(base==0x22) {writes[x[0]]++;writes[x[1]]++;}
      else {writes[x[1]]++;writes[x[2]]++;}
    } else if(base==0x12||base==0x50) {writes[x[0]]++;barriers[x[0]]++;}
    else if(base==0x40||base==0x41||base==0x42||base==0x00) {}
    else {epoch++;unknown_barriers++;}
    if(bit>=0) {bitver[bit]++;if(stack_count[bit])epoch++;}
  }
  if(!stack.empty())throw runtime_error("unclosed condition stack");
  for(int k=1;k<=10;k++)if(p[k]!=end[k])throw runtime_error("unconsumed operand bytes");
  ofstream out(argv[2]);if(!out)throw runtime_error("output failed");
  out<<"{\n\"schema\":\"score7-phase-commute-v1\",\n\"status\":\"EXACT_STRUCTURAL_DISCOVERY\",\n";
  out<<"\"operations\":"<<n<<",\"qubits\":"<<nq<<",\"ccx\":"<<ccx<<",\"ccz\":"<<ccz<<",\"diagonal\":"<<diagonal<<",\n";
  out<<"\"physical_pairs\":"<<physical_pairs<<",\"eligible_pairs\":"<<eligible_pairs<<",\"phase_pairs\":"<<phase_pairs<<",\"phase_crossings\":"<<phase_crossings<<",\n";
  out<<"\"boundary_rejections\":"<<boundary_reject<<",\"control_write_rejections\":"<<control_reject<<",\"target_use_rejections\":"<<target_reject<<",\"explicit_guard_rejections\":"<<explicit_reject<<",\n";
  out<<"\"quartic_rejections\":"<<quartic_reject<<",\"nonimproving_correction_rejections\":"<<expensive_reject<<",\"unknown_barriers\":"<<unknown_barriers<<",\n";
  out<<"\"candidate_count\":"<<candidates.size()<<",\n\"candidates\":[";
  bool comma=false;for(auto& c:candidates) {
    if(comma)out<<",";
    comma=true;
    out<<"\n{\"first\":"<<c.first<<",\"second\":"<<c.second<<",\"qubits\":["<<c.wires[0]<<","<<c.wires[1]<<","<<c.wires[2]<<"],\"condition\":"<<c.condition<<",\"crossed_phases\":"<<c.crossed_phases<<",\"delta_toffoli\":"<<int64_t(c.nonclifford)-2<<",\"corrections\":[";
    bool inner=false;for(auto& p:c.corrections) {
      if(inner)out<<",";
      inner=true;
      out<<"{\"before_source_op\":"<<p.pos<<",\"condition\":"<<p.condition<<",\"qubits\":[";
      bool qcomma=false;for(auto q:p.wires) {if(qcomma)out<<",";qcomma=true;out<<q;}
      out<<"]}";
    }out<<"]}";
  }out<<"\n]}\n";
  munmap(d,st.st_size);close(fd);
  return 0;
} catch(const exception&e) {cerr<<e.what()<<"\n";return 1;} }

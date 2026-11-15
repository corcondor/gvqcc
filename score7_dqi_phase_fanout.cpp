// SPDX-License-Identifier: Apache-2.0
// Bounded exact CCX fanout contraction through diagonal phases.
// No sampled wire signatures: physical operands and write versions only.
#include <algorithm>
#include <array>
#include <cstdint>
#include <deque>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
using namespace std;
static uint64_t le(const uint8_t*p,int n) {
  uint64_t v=0;for(int i=0;i<n;i++)v|=uint64_t(p[i])<<(8*i);return v;
}
using Key=vector<pair<int64_t,uint64_t>>;
struct Phase {uint64_t pos;vector<pair<uint32_t,uint64_t>> w;int64_t guard;uint64_t gv;};
struct Pending {uint64_t pos,epoch,ca,cb,barrier,gv,pi;uint32_t target;};
struct Correction {uint64_t pos;vector<uint32_t>w;int64_t guard;};
struct Candidate {uint64_t first,second,crossed;array<uint32_t,4>w;int64_t guard,delta;
                  vector<Correction> corrections;vector<uint64_t> remove_phases;};
static Key key_for(const map<uint32_t,uint64_t>&w,int64_t guard,uint64_t gv) {
  Key k{{-1,guard<0?0:uint64_t(guard)+1},{-2,gv}};
  for(auto a:w)k.push_back({a.first,a.second});return k;
}
int main(int argc,char**argv){try{
  if(argc!=3)throw runtime_error("usage: phase-fanout input.kmb result.json");
  int fd=open(argv[1],O_RDONLY);if(fd<0)throw runtime_error("open failed");
  struct stat st{};if(fstat(fd,&st))throw runtime_error("stat failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
  uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
  array<uint64_t,12>p{},end{};
  for(uint64_t i=0;i<nr+11;i++){
    if(at+16>uint64_t(st.st_size))throw runtime_error("truncated packet");
    auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;
    if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("invalid packet");
    if(kind){p[kind]=at;end[kind]=at+len;}at+=len;
  }
  if(at!=uint64_t(st.st_size))throw runtime_error("trailing bytes");
  auto take=[&](int c,int b){if(p[c]+b>end[c])throw runtime_error("column exhausted");
    auto v=le(d+p[c],b);p[c]+=b;return v;};
  vector<uint64_t>writes(nq,0),barrier(nq,0),bitver(nb,0);
  vector<vector<Phase>>phases(nq);
  vector<uint32_t>stack;vector<uint32_t>stack_count(nb,0);
  map<array<int64_t,3>,deque<Pending>>previous;
  map<Key,uint64_t>last_ccz;
  vector<Candidate>candidates;
  uint64_t epoch=0,ccx=0,ccz=0,diagonal=0,prior=0,same_target=0,too_far=0;
  uint64_t boundary=0,control=0,target=0,guard=0,eligible=0,phase_pairs=0;
  uint64_t crossings=0,quartic=0,nonimproving=0,unknown=0,seen_target=0;
  const uint64_t RECENT=32,MAX_GAP=65536;
  for(uint64_t pos=0;pos<n;pos++){
    auto op=take(1,1);int base=op&127,arity=(op>>4)&3;array<uint32_t,3>x{};
    for(int j=0;j<arity;j++){x[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(x[j]>=nq)throw runtime_error("qubit overflow");}
    int64_t bit=(op&64)?int64_t(take(8,4)):-1,g=(op&128)?int64_t(take(9,4)):-1;
    if(bit>=int64_t(nb)||g>=int64_t(nb))throw runtime_error("bit overflow");
    if(base==0x13){take(10,8);take(10,8);}
    if(op==0x81){if(g<0)throw runtime_error("missing PUSH bit");stack.push_back(g);stack_count[g]++;epoch++;continue;}
    if(op==0x01){if(stack.empty())throw runtime_error("stack underflow");stack_count[stack.back()]--;stack.pop_back();epoch++;continue;}
    if(base==0x10||base==0x20||base==0x30){
      diagonal++;if(base==0x30)ccz++;
      Phase ph{pos,{},g,g<0?0:bitver[g]};map<uint32_t,uint64_t>m;
      for(int j=0;j<arity;j++){ph.w.push_back({x[j],writes[x[j]]});m.emplace(x[j],writes[x[j]]);}
      for(int j=0;j<arity;j++)phases[x[j]].push_back(ph);
      if(base==0x30)last_ccz[key_for(m,g,ph.gv)]=pos;
    }else if(base==0x31){
      ccx++;if(x[1]<x[0])swap(x[0],x[1]);
      array<int64_t,3>key{int64_t(x[0]),int64_t(x[1]),g};auto&queue=previous[key];
      set<uint32_t>tested;
      for(auto it=queue.rbegin();it!=queue.rend();++it){
        auto old=*it;prior++;
        if(old.target==x[2]){same_target++;continue;}
        if(!tested.insert(old.target).second){seen_target++;continue;}
        if(pos-old.pos>MAX_GAP){too_far++;continue;}
        if(old.epoch!=epoch){boundary++;continue;}
        if(old.ca!=writes[x[0]]||old.cb!=writes[x[1]]){control++;continue;}
        if(old.barrier!=barrier[old.target]){target++;continue;}
        if(g>=0&&old.gv!=bitver[g]){guard++;continue;}
        eligible++;
        Candidate c{old.pos,pos,phases[old.target].size()-old.pi,
                    {x[0],x[1],old.target,x[2]},g,-1,{},{}};
        if(c.crossed)phase_pairs++;crossings+=c.crossed;
        map<Key,Correction>residual;bool bad_guard=false;
        for(uint64_t j=old.pi;j<phases[old.target].size();j++){
          auto&ph=phases[old.target][j];
          if(g>=0&&ph.guard>=0&&g!=ph.guard){bad_guard=true;break;}
          int64_t cg=g>=0?g:ph.guard;uint64_t cv=g>=0?old.gv:ph.gv;
          map<uint32_t,uint64_t>w{{x[0],writes[x[0]]},{x[1],writes[x[1]]}};
          for(auto a:ph.w)if(a.first!=old.target)w.emplace(a);
          auto ck=key_for(w,cg,cv);Correction correction{ph.pos,{},cg};
          for(auto a:w)correction.w.push_back(a.first);
          auto r=residual.find(ck);if(r==residual.end())residual.emplace(ck,correction);else residual.erase(r);
        }
        if(bad_guard){guard++;continue;}
        bool high=false;
        for(auto&r:residual){
          auto corr=r.second;
          if(corr.w.size()>3){high=true;break;}
          if(corr.w.size()==3){
            auto found=last_ccz.find(r.first);
            if(found!=last_ccz.end()&&found->second>old.pos){c.remove_phases.push_back(found->second);c.delta--;continue;}
            c.delta++;
          }
          c.corrections.push_back(corr);
        }
        if(high){quartic++;continue;}
        if(c.delta>=0){nonimproving++;continue;}
        candidates.push_back(c);
      }
      queue.push_back({pos,epoch,writes[x[0]],writes[x[1]],barrier[x[2]],g<0?0:bitver[g],phases[x[2]].size(),x[2]});
      if(queue.size()>RECENT)queue.pop_front();
      writes[x[2]]++;barrier[x[0]]++;barrier[x[1]]++;
    }else if(base==0x11)writes[x[0]]++;
    else if(base==0x21){writes[x[1]]++;barrier[x[0]]++;}
    else if(base==0x22||base==0x32){for(int j=0;j<arity;j++)barrier[x[j]]++;
      if(base==0x22){writes[x[0]]++;writes[x[1]]++;}else{writes[x[1]]++;writes[x[2]]++;}}
    else if(base==0x12||base==0x50){writes[x[0]]++;barrier[x[0]]++;}
    else if(base==0x40||base==0x41||base==0x42||base==0x00){}
    else {epoch++;unknown++;}
    if(bit>=0){bitver[bit]++;if(stack_count[bit])epoch++;}
  }
  if(!stack.empty())throw runtime_error("unclosed condition stack");
  for(int k=1;k<=10;k++)if(p[k]!=end[k])throw runtime_error("unconsumed operand bytes");
  ofstream o(argv[2]);if(!o)throw runtime_error("output failed");
  o<<"{\n\"status\":\"EXACT_BOUNDED_FANOUT_DISCOVERY\",\n\"operations\":"<<n<<",\"qubits\":"<<nq<<",\"ccx\":"<<ccx<<",\"ccz\":"<<ccz<<",\"diagonal\":"<<diagonal<<",\n";
  o<<"\"recent_per_control_guard\":"<<RECENT<<",\"max_operation_gap\":"<<MAX_GAP<<",\n";
  o<<"\"prior_records\":"<<prior<<",\"same_target_excluded\":"<<same_target<<",\"superseded_target_excluded\":"<<seen_target<<",\"gap_rejections\":"<<too_far<<",\n";
  o<<"\"boundary_rejections\":"<<boundary<<",\"control_write_rejections\":"<<control<<",\"target_use_rejections\":"<<target<<",\"guard_rejections\":"<<guard<<",\n";
  o<<"\"eligible_pairs\":"<<eligible<<",\"phase_crossing_pairs\":"<<phase_pairs<<",\"phase_crossings\":"<<crossings<<",\"quartic_rejections\":"<<quartic<<",\"nonimproving_rejections\":"<<nonimproving<<",\"unknown_barriers\":"<<unknown<<",\n";
  o<<"\"candidate_count\":"<<candidates.size()<<",\n\"candidates\":[";bool comma=false;
  for(auto&c:candidates){if(comma)o<<",";comma=true;
    o<<"\n{\"first\":"<<c.first<<",\"second\":"<<c.second<<",\"qubits\":["<<c.w[0]<<","<<c.w[1]<<","<<c.w[2]<<","<<c.w[3]<<"],\"condition\":"<<c.guard<<",\"crossed_phases\":"<<c.crossed<<",\"delta_toffoli\":"<<c.delta<<",\"remove_phase_ops\":[";
    bool sep=false;for(auto v:c.remove_phases){if(sep)o<<",";sep=true;o<<v;}o<<"],\"corrections\":[";sep=false;
    for(auto&p:c.corrections){if(sep)o<<",";sep=true;o<<"{\"before_source_op\":"<<p.pos<<",\"condition\":"<<p.guard<<",\"qubits\":[";
      bool wsep=false;for(auto q:p.w){if(wsep)o<<",";wsep=true;o<<q;}o<<"]}";}o<<"]}";
  }o<<"\n]}\n";munmap(d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<"\n";return 1;}}

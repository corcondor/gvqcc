// SPDX-License-Identifier: Apache-2.0
// Find CCZ at different child conditions with the same immutable control pair.
#include <algorithm>
#include <array>
#include <unordered_map>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <tuple>
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
 struct Scope {uint64_t start,stop;unsigned parent,depth;};
 struct Point {uint64_t index;unsigned scope,third;};
 struct Region {uint64_t start,stop;unsigned a,b,scratch;uint64_t scope;vector<Point> phases;};
 vector<Scope> scopes{{0,n,0,0}};
 unsigned scope=0;
 vector<vector<uint32_t>> writes(nq);
 vector<vector<pair<uint64_t,uint64_t>>> gaps(nq);
 vector<int64_t> clean_since(nq,-1);
 for(unsigned q=840;q<nq;q++)clean_since[q]=0;
 map<tuple<unsigned,unsigned,int64_t>,vector<Point>> occurrences;
 const auto last_write=[&](unsigned q){return writes[q].empty()?-1ll:static_cast<int64_t>(writes[q].back());};
 for(uint64_t i=0;i<n;i++){
  auto op=take(1,1);unsigned base=op&127,arity=(op>>4)&3;array<unsigned,3> q{};
  for(unsigned j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("q");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("b");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){scopes.push_back({i,n,scope,scopes[scope].depth+1});scope=scopes.size()-1;continue;}
  if(op==0x01){if(!scope)throw runtime_error("pop");scopes[scope].stop=i+1;scope=scopes[scope].parent;continue;}
  for(unsigned j=0;j<arity;j++){
   if(clean_since[q[j]]>=0){
    if(uint64_t(clean_since[q[j]])<i)gaps[q[j]].emplace_back(clean_since[q[j]],i);
    clean_since[q[j]]=-1;
   }
  }
  if(base==0x12||base==0x50){
   if(!scope&&c<0&&q[0]>=840)clean_since[q[0]]=i+1;
   writes[q[0]].push_back(i);
  }else if(base==0x11){writes[q[0]].push_back(i);}
  else if(base==0x21||base==0x31){writes[q[arity-1]].push_back(i);}
  else if(base==0x22||base==0x32){writes[q[arity-2]].push_back(i);writes[q[arity-1]].push_back(i);}
  else if(base==0x30){
   for(unsigned j=0;j<3;j++){
    auto a=q[(j+1)%3],b=q[(j+2)%3];if(b<a)swap(a,b);
    occurrences[{a,b,max(last_write(a),last_write(b))}].push_back({i,scope,q[j]});
   }
  }else if(base==0x00||base==0x06||base==0x07||base==0x10||base==0x13||base==0x17||base==0x20||base==0x40||base==0x41||base==0x42||base==0x47){}
  else throw runtime_error("unsupported opcode");
 }
 if(scope)throw runtime_error("unclosed");
 for(unsigned q=840;q<nq;q++)if(clean_since[q]>=0)gaps[q].emplace_back(clean_since[q],n);
 const auto after=[&](unsigned q,uint64_t index){
  const auto& a=writes[q];auto it=upper_bound(a.begin(),a.end(),index);
  return it==a.end()?n:uint64_t(*it);
 };
 const auto span=[&](Point first,Point last){
  unsigned a=first.scope,b=last.scope,x=a,y=b;
  while(a!=b){
   if(scopes[a].depth>=scopes[b].depth){x=a;a=scopes[a].parent;}
   else {y=b;b=scopes[b].parent;}
  }
  return tuple<uint64_t,uint64_t,unsigned>{a==first.scope?first.index:scopes[x].start,b==last.scope?last.index+1:scopes[y].stop,a};
 };
 vector<Region> candidate;
 size_t max_repeat=0, pair_epochs=0, stable_triples=0, blocked_source=0, blocked_scratch=0;
 for(const auto& [key,v]:occurrences){
  pair_epochs+=(v.size()>=2);max_repeat=max(max_repeat,v.size());
  if(v.size()<3)continue;stable_triples++;
  const auto [a,b,prev]=key;const auto next=min(after(a,v.back().index),after(b,v.back().index));
  for(size_t i=0;i+2<v.size();i++)for(size_t j=i+2;j<v.size();j++){
   auto [start,stop,common]=span(v[i],v[j]);
   if(int64_t(start)<=prev||stop>next){blocked_source++;break;}
   unsigned scratch=nq;
   for(unsigned q=840;q<nq;q++){
    if(q==a||q==b)continue;
    const auto& gs=gaps[q];
    auto g=upper_bound(gs.begin(),gs.end(),make_pair(start,n+1));
    if(g==gs.begin())continue;
    --g;if(g->first<=start&&stop<=g->second){scratch=q;break;}
   }
   if(scratch==nq){blocked_scratch++;break;}
   candidate.push_back({start,stop,a,b,scratch,common,vector<Point>(v.begin()+i,v.begin()+j+1)});
  }
 }
 sort(candidate.begin(),candidate.end(),[](const Region& a,const Region& b){return tie(a.stop,a.start,a.a,a.b)<tie(b.stop,b.start,b.a,b.b);});
 vector<uint64_t> ends,best{0};vector<pair<bool,size_t>> trace;
 for(const auto& r:candidate){
  auto prev=upper_bound(ends.begin(),ends.end(),r.start)-ends.begin();
  auto val=best[prev]+r.phases.size()-2;
  const bool take=val>best.back();
  trace.emplace_back(take,prev);best.push_back(max(val,best.back()));ends.push_back(r.stop);
 }
 vector<size_t> selected;
 for(size_t i=candidate.size();i;){auto [take,prev]=trace[i-1];if(take){selected.push_back(i-1);i=prev;}else i--;}
 reverse(selected.begin(),selected.end());
 ofstream out(argv[2]);out<<"{\"charged_savings_static\":"<<best.back()<<",\"candidate_count\":"<<candidate.size()
   <<",\"pair_epochs\":"<<pair_epochs<<",\"max_repeat\":"<<max_repeat<<",\"stable_triples\":"<<stable_triples<<",\"blocked_source\":"<<blocked_source<<",\"blocked_scratch\":"<<blocked_scratch<<",\"selected_count\":"<<selected.size()<<",\"num_ops\":"<<n<<",\"groups\":[";
 bool comma=false;for(auto j:selected){
  if(comma)out<<',';comma=true;
  const auto& s=candidate[j];
  out<<"{\"start\":"<<s.start<<",\"stop\":"<<s.stop<<",\"scope\":"<<s.scope
    <<",\"depth\":"<<scopes[s.scope].depth
    <<",\"controls\":["<<s.a<<','<<s.b<<"],\"scratch\":"<<s.scratch<<",\"phases\":[";
  bool comma2=false;
  for(const auto& p:s.phases){
   if(comma2)out<<',';comma2=true;out<<'['<<p.index<<','<<p.third<<']';
  }
  out<<"]}";
 }
 out<<"]}\n";
 cerr<<"groups="<<selected.size()<<" static savings="<<best.back()<<'\n';
 munmap((void*)d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

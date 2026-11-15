// SPDX-License-Identifier: Apache-2.0
// Discovery of whole CCZ phases represented by live affine/quadratic functions.
// Random panels only filter candidates; no circuit may be changed without an
// independent exact proof. Initial quantum values are arbitrary, not zero.
#include <algorithm>
#include <array>
#include <chrono>
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
constexpr int NW=32, NC=16;
struct Sig { array<uint64_t,NW> w{}; bool operator==(const Sig& b) const {return w==b.w;} };
static Sig operator^(Sig a,const Sig& b){for(int i=0;i<NW;i++)a.w[i]^=b.w[i];return a;}
static Sig operator&(Sig a,const Sig& b){for(int i=0;i<NW;i++)a.w[i]&=b.w[i];return a;}
static int pivot(const Sig& a){for(int i=NW-1;i>=0;i--)if(a.w[i])return 64*i+63-__builtin_clzll(a.w[i]);return -1;}
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
static uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
static bool covers(const Sig&a,const Sig& b){for(int i=0;i<NW;i++)if((a.w[i]&b.w[i])!=b.w[i])return false;return true;}
struct Span { bool found=false; vector<int> wires; };
static Span solve(const vector<Sig>&q,const Sig&one,Sig v){
  vector<Sig> bas(64*NW); vector<array<uint64_t,NC>> coeff(64*NW);
  auto insert=[&](Sig s,int j){array<uint64_t,NC> c{};c[j/64]|=1ULL<<(j%64);
    for(int b;(b=pivot(s))>=0;){
      if(bas[b].w[b/64]){s=s^bas[b];for(int k=0;k<NC;k++)c[k]^=coeff[b][k];}
      else{bas[b]=s;coeff[b]=c;break;}
    }
  };
  insert(one,q.size());for(int j=int(q.size())-1;j>=0;j--)insert(q[j],j);
  array<uint64_t,NC> c{};
  for(int b;(b=pivot(v))>=0;){if(!bas[b].w[b/64])return {};v=v^bas[b];for(int k=0;k<NC;k++)c[k]^=coeff[b][k];}
  Span r;r.found=true;for(int j=0;j<=int(q.size());j++)if((c[j/64]>>(j%64))&1)r.wires.push_back(j);return r;
}
int main(int argc,char**argv){try{
  if(argc<3||argc>4)throw runtime_error("usage: scanner source.kmb output.json [--no-span]");
  bool span=argc==3;if(argc==4&&string(argv[3])!="--no-span")throw runtime_error("unknown option");
  auto begin=chrono::steady_clock::now();int fd=open(argv[1],O_RDONLY);struct stat st{};
  if(fd<0||fstat(fd,&st))throw runtime_error("input open failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2)throw runtime_error("not KMBv2");
  uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
  if(nq>=64*NC)throw runtime_error("at most 1023 qubits");
  array<uint64_t,12> p{},end{};
  for(uint64_t i=0;i<nr+11;i++){if(at+16>uint64_t(st.st_size))throw runtime_error("truncated packet");
    auto k=le(d+at,8),len=le(d+at+8,8);at+=16;
    if(k!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("invalid packet");
    if(k){p[k]=at;end[k]=at+len;}at+=len;
  }
  if(at!=uint64_t(st.st_size))throw runtime_error("trailing bytes");
  auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
  uint64_t atoms=0;auto fresh=[&](){Sig s;auto id=++atoms;for(int i=0;i<NW;i++)s.w[i]=mix(id^(0x52c49a609478ef15ULL*(i+1)));return s;};
  Sig zero,one;one.w.fill(~uint64_t(0));vector<Sig> q(nq);for(auto&s:q)s=fresh();vector<vector<Sig>> frames;
  ofstream out(argv[2]);if(!out)throw runtime_error("output open failed");
  uint64_t ccx=0,ccz=0,cswap=0,eligible=0,skipped=0,hits=0,affine=0,pairs=0,queries=0;
  out<<"{\"schema\":\"score7-whole-phase-resub-v1\",\"status\":\"DISCOVERY_ONLY\",\"panel_bits\":2048,\"span_enabled\":"<<(span?"true":"false")<<",\"candidates\":[";
  auto emit=[&](uint64_t pos,const array<uint32_t,3>&x,int64_t cond,const string&kind,const vector<int>&wire,const vector<int>&neg,int constant){
    if(hits++)out<<',';
    out<<"{\"index\":"<<pos<<",\"kind\":\""<<kind<<"\",\"phase_qubits\":["<<x[0]<<','<<x[1]<<','<<x[2]<<"],\"condition\":"<<cond<<",\"depth\":"<<frames.size()<<",\"constant\":"<<constant<<",\"wires\":[";
    for(size_t j=0;j<wire.size();j++){if(j)out<<',';out<<wire[j];}out<<"],\"negated\":[";for(size_t j=0;j<neg.size();j++){if(j)out<<',';out<<neg[j];}out<<"]}";
  };
  for(uint64_t pos=0;pos<n;pos++){
    auto op=take(1,1);int base=op&127,arity=(op>>4)&3;array<uint32_t,3>x{};
    for(int j=0;j<arity;j++){x[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(x[j]>=nq)throw runtime_error("qubit overflow");}
    int64_t bit=(op&64)?int64_t(take(8,4)):-1,cond=(op&128)?int64_t(take(9,4)):-1;
    if(bit>=int64_t(nb)||cond>=int64_t(nb))throw runtime_error("bit overflow");
    if(base==0x13){take(10,8);take(10,8);}
    if(op==0x81){frames.push_back(q);continue;}
    if(op==0x01){if(frames.empty())throw runtime_error("stack underflow");for(int j=0;j<int(nq);j++)if(!(q[j]==frames.back()[j]))q[j]=fresh();frames.pop_back();continue;}
    bool guard=cond>=0;
    if(base==0x11)q[x[0]]=guard?fresh():q[x[0]]^one;
    else if(base==0x21)q[x[1]]=guard?fresh():q[x[1]]^q[x[0]];
    else if(base==0x22){if(guard){q[x[0]]=fresh();q[x[1]]=fresh();}else swap(q[x[0]],q[x[1]]);}
    else if(base==0x32){cswap++;if(guard){q[x[1]]=fresh();q[x[2]]=fresh();}else{auto delta=q[x[0]]&(q[x[1]]^q[x[2]]);q[x[1]]=q[x[1]]^delta;q[x[2]]=q[x[2]]^delta;}}
    else if(base==0x12||base==0x50)q[x[0]]=guard?fresh():zero;
    else if(base==0x31){ccx++;q[x[2]]=guard?fresh():q[x[2]]^(q[x[0]]&q[x[1]]);}
    else if(base==0x30){
      ccz++;auto phase=q[x[0]]&q[x[1]]&q[x[2]];int weight=0;for(auto w:phase.w)weight+=__builtin_popcountll(w);
      if(weight<64||weight>1984){skipped++;continue;}eligible++;bool found=false;
      for(int j=0;j<int(nq);j++)for(int inv=0;inv<2;inv++)if((q[j]^(inv?one:zero))==phase){emit(pos,x,cond,"literal",{j},{},inv);affine++;found=true;break;}
      if(found)continue;
      if(span){queries++;auto s=solve(q,one,phase);if(s.found){emit(pos,x,cond,"affine",s.wires,{},0);affine++;continue;}}
      for(int constant=0;constant<2;constant++){
        Sig target=phase^(constant?one:zero);vector<pair<int,int>> live;
        for(int j=0;j<int(nq);j++)for(int inv=0;inv<2;inv++)if(covers(q[j]^(inv?one:zero),target))live.emplace_back(j,inv);
        for(size_t a=0;a<live.size()&&!found;a++)for(size_t b=a+1;b<live.size();b++){
          auto [i,ni]=live[a];auto [j,nj]=live[b];if(i==j)continue;
          if(((q[i]^(ni?one:zero))&(q[j]^(nj?one:zero)))==target){emit(pos,x,cond,"quadratic",{i,j},{ni,nj},constant);pairs++;found=true;break;}
        }
        if(found)break;
      }
    }
    else if(base==0x00||base==0x10||base==0x13||base==0x20||base==0x40||base==0x41||base==0x42||base==0x06||base==0x07||base==0x17||base==0x47){}
    else throw runtime_error("unsupported opcode");
  }
  if(!frames.empty())throw runtime_error("unclosed stack");
  for(int c=1;c<=10;c++)if(p[c]!=end[c])throw runtime_error("unused operand bytes");
  auto secs=chrono::duration<double>(chrono::steady_clock::now()-begin).count();
  out<<"],\"num_ops\":"<<n<<",\"qubits\":"<<nq<<",\"ccx\":"<<ccx<<",\"cswap\":"<<cswap<<",\"ccz\":"<<ccz<<",\"eligible_phases\":"<<eligible<<",\"sparse_phase_skips\":"<<skipped<<",\"span_queries\":"<<queries<<",\"affine_hits\":"<<affine<<",\"quadratic_hits\":"<<pairs<<",\"candidate_count\":"<<hits<<",\"seconds\":"<<secs<<"}\n";
  cerr<<"CCZ="<<ccz<<" eligible="<<eligible<<" affine="<<affine<<" quadratic="<<pairs<<" seconds="<<secs<<'\n';munmap(d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

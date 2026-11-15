// SPDX-License-Identifier: Apache-2.0
// Discover CCZ -> Clifford substitutions from live XOR/AND relations.
// Signatures are a discovery filter, NOT an equivalence certificate. Any hit
// must be replayed with exact symbolic expressions before a KMB is changed.
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
#include <unordered_map>
#include <vector>
using namespace std;
static uint64_t mix(uint64_t x) {
  x += 0x9e3779b97f4a7c15ULL;
  x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
  x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
  return x ^ (x >> 31);
}
struct Sig {
  array<uint64_t,16> w{};
  bool operator==(const Sig& b) const { return w == b.w; }
  bool operator<(const Sig& b) const { return w < b.w; }
};
static Sig operator^(Sig a, const Sig& b) {
  for(int i=0;i<16;i++) a.w[i] ^= b.w[i]; return a;
}
static void xoreq(Sig& a,const Sig& b) {
  for(int i=0;i<16;i++) a.w[i] ^= b.w[i];
}
static int pivot(const Sig& s) {
  for(int i=15;i>=0;i--) if(s.w[i]) return 64*i+63-__builtin_clzll(s.w[i]);
  return -1;
}
struct Pair {
  Sig a,b;
  bool operator==(const Pair& p) const { return a==p.a && b==p.b; }
};
struct PairHash {
  size_t operator()(const Pair& p) const {
    return mix(p.a.w[0])^mix(p.a.w[1]+1)^mix(p.b.w[0]+2)^mix(p.b.w[1]+3);
  }
};
struct SigHash { size_t operator()(const Sig& s) const { return mix(s.w[0])^mix(s.w[1]); } };
struct Product { Sig s; uint64_t origin; bool repeated=false; };
class Model {
public:
  uint64_t atoms=0, hits=0;
  bool truth=false;
  Sig one,zero;
  unordered_map<Pair,Product,PairHash> products;
  Model(bool truth_=false):truth(truth_) {
    one=fresh(); if(truth) one.w.fill(~uint64_t(0));
    products.reserve(500000);
  }
  Sig fresh() {
    auto id=++atoms; Sig s;
    for(int j=0;j<16;j++) s.w[j]=mix(id^(0x987eadfe39a58b41ULL*j));
    return s;
  }
  Product mul(Sig a,Sig b,uint64_t pos) {
    if(truth) { Sig s; for(int i=0;i<16;i++) s.w[i]=a.w[i]&b.w[i]; return {s,pos,true}; }
    if(a==zero||b==zero) return {zero,pos,true};
    if(a==one) return {b,pos,true};
    if(b==one||a==b) return {a,pos,true};
    if(a==(b^one)) return {zero,pos,true};
    bool na=(a^one)<a, nb=(b^one)<b;
    if(na) a=a^one; if(nb) b=b^one;
    Pair key{a,b}; if(key.b<key.a) swap(key.a,key.b);
    auto it=products.find(key); bool repeated=it!=products.end();
    if(!repeated) it=products.emplace(key,Product{fresh(),pos,false}).first;
    else hits++;
    Sig s=it->second.s;
    if(na) s=s^b; if(nb) s=s^a; if(na&&nb) s=s^one;
    return {s,it->second.origin,repeated};
  }
};
// Coefficients index all current wires, followed by the constant one.
static vector<int> solve_span(const vector<Sig>& q,const Sig& one,Sig want) {
  array<Sig,1024> basis{},coeff{};
  auto insert=[&](Sig s,int index) {
    Sig c; c.w[index/64]=uint64_t(1)<<(index%64);
    for(int b;(b=pivot(s))>=0;) {
      if(basis[b].w[b/64]) { xoreq(s,basis[b]); xoreq(c,coeff[b]); }
      else { basis[b]=s; coeff[b]=c; break; }
    }
  };
  if(q.size()>=1024) throw runtime_error("at most1023qubits supported");
  insert(one,q.size());
  for(int j=840;j<(int)q.size();j++) insert(q[j],j);
  for(int j=0;j<min(840,(int)q.size());j++) insert(q[j],j);
  Sig c;
  for(int b;(b=pivot(want))>=0;) {
    if(!basis[b].w[b/64]) return {};
    xoreq(want,basis[b]); xoreq(c,coeff[b]);
  }
  vector<int> solution;
  for(int j=0;j<=(int)q.size();j++) if((c.w[j/64]>>(j%64))&1) solution.push_back(j);
  return solution;
}
static uint64_t le(const uint8_t* p,int n) {
  uint64_t x=0; for(int i=0;i<n;i++) x|=uint64_t(p[i])<<(8*i); return x;
}
static void selftest() {
  Model m; vector<Sig> q; for(int i=0;i<8;i++) q.push_back(m.fresh());
  auto p=m.mul(q[0],q[1],0).s;
  q[3]=p^q[4]^m.one;
  auto hit=m.mul(q[0],q[1],1); auto s=solve_span(q,m.one,hit.s);
  if(s.empty()) throw runtime_error("positive XOR span selftest failed");
  Sig sum; for(int i:s) xoreq(sum,i==(int)q.size()?m.one:q[i]);
  if(!(sum==p)) throw runtime_error("selftest reconstruction failed");
  if(!(m.mul(q[0],q[0]^m.one,2).s==m.zero)) throw runtime_error("complement test failed");
  if(!solve_span(q,m.one,m.fresh()).empty()) throw runtime_error("negative span test failed");
}
int main(int argc,char** argv) { try {
  selftest();
  if(argc<3||argc>8) throw runtime_error("usage: phase-cache-scan input.kmb discovery.json [--truth] [--no-span] [--branches] [--fredkin] [--balanced]");
  bool truth=false,no_span=false,branches=false,fredkin=false,balanced=false;
  for(int i=3;i<argc;i++) {
    string a=argv[i]; if(a=="--truth") truth=true;
    else if(a=="--no-span") no_span=true;
    else if(a=="--branches") branches=true;
    else if(a=="--fredkin") fredkin=true;
    else if(a=="--balanced") balanced=true;
    else throw runtime_error("unknownargument");
  }
  int fd=open(argv[1],O_RDONLY); if(fd<0) throw runtime_error("open failed");
  struct stat st{}; if(fstat(fd,&st)) throw runtime_error("stat failed");
  auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
  if(d==MAP_FAILED||st.st_size<104||le(d+16,4)!=2) throw runtime_error("notKMBv2");
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
  Model m(truth); vector<Sig> q(nq); for(auto& s:q) s=m.fresh();
  vector<vector<Sig>> frames;
  unordered_map<Sig,vector<pair<uint64_t,pair<int64_t,uint64_t>>>,SigHash> phases;
  vector<uint64_t> bit_versions(nb,0);
  struct PhasePair { uint64_t first,second; int64_t condition; uint64_t depth; };
  vector<PhasePair> duplicates;
  uint64_t depth=0,ccz=0,ccx=0,candidates=0,pair_hits=0,span_queries=0;
  uint64_t sparse_pair_skips=0,cswaps=0,phase_queries=0;
  ofstream out(argv[2]); if(!out) throw runtime_error("output failed");
  out<<"{\"schema\":\"score6-live-product-phase-v1\",\"status\":\"DISCOVERY_ONLY\",\"positive_control\":\"PASS\",\"random_truth_mode\":"<<(truth?"true":"false")<<",\"multiwire_span_enabled\":"<<(no_span?"false":"true")<<",\"branch_join_enabled\":"<<(branches?"true":"false")<<",\"fredkin_relations\":"<<(fredkin?"true":"false")<<",\"balanced_pair_filter\":"<<(balanced?"true":"false")<<",\"candidates\":[";
  bool comma=false;
  for(uint64_t pos=0;pos<n;pos++) {
    auto op=take(1,1); int base=op&127,arity=(op>>4)&3; array<uint32_t,3> x{};
    for(int j=0;j<arity;j++) {
      x[j]=take(arity==3?2+j:arity==2?5+j:7,4);
      if(x[j]>=nq) throw runtime_error("qubitoverflow");
    }
    int64_t bit=(op&64)?int64_t(take(8,4)):-1,condition=(op&128)?int64_t(take(9,4)):-1;
    if(bit>=int64_t(nb)||condition>=int64_t(nb)) throw runtime_error("bitoverflow");
    if(base==0x13) { take(10,8); take(10,8); }
    if(op==0x81) { depth++; if(branches) frames.push_back(q); phases.clear(); continue; }
    if(op==0x01) {
      if(!depth) throw runtime_error("stackunderflow"); depth--;
      if(branches) {
        for(uint64_t j=0;j<nq;j++) if(!(q[j]==frames.back()[j])) q[j]=m.fresh();
        frames.pop_back();
      }
      phases.clear();
      continue;
    }
    bool guard=(!branches&&depth)||condition>=0;
    if(base==0x11) q[x[0]]=guard?m.fresh():q[x[0]]^m.one;
    else if(base==0x21) q[x[1]]=guard?m.fresh():q[x[1]]^q[x[0]];
    else if(base==0x22) {
      if(guard) { q[x[0]]=m.fresh(); q[x[1]]=m.fresh(); }
      else swap(q[x[0]],q[x[1]]);
    } else if(base==0x32) {
      cswaps++;
      if(fredkin&&!guard) {
        auto delta=m.mul(q[x[0]],q[x[1]]^q[x[2]],pos).s;
        q[x[1]]=q[x[1]]^delta; q[x[2]]=q[x[2]]^delta;
      } else { q[x[1]]=m.fresh(); q[x[2]]=m.fresh(); }
    }
    else if(base==0x12||base==0x50) q[x[0]]=guard?m.fresh():m.zero;
    else if(base==0x31) {
      ccx++; q[x[2]]=guard?m.fresh():q[x[2]]^m.mul(q[x[0]],q[x[1]],pos).s;
    } else if(base==0x30) {
      ccz++;
      array<Sig,3> factors{q[x[0]],q[x[1]],q[x[2]]}; sort(factors.begin(),factors.end());
      auto phase=m.mul(m.mul(factors[0],factors[1],pos).s,factors[2],pos).s;
      int weight=0; for(auto v:phase.w) weight+=__builtin_popcountll(v);
      if(!truth||(weight>=32&&weight<=992)) {
        auto key=make_pair(condition,condition<0?0:bit_versions[condition]);
        auto& old=phases[phase]; phase_queries++;
        for(auto p:old) if(p.second==key) { duplicates.push_back({p.first,pos,condition,depth}); break; }
        old.push_back({pos,key});
      }
      for(int c=0;c<3;c++) {
        int a=(c+1)%3,b=(c+2)%3; auto prod=m.mul(q[x[a]],q[x[b]],pos);
        if(!prod.repeated) continue;
        pair_hits++;
        if(truth&&balanced) {
          int weight=0; for(auto v:prod.s.w) weight+=__builtin_popcountll(v);
          if(weight<64||weight>960) { sparse_pair_skips++; continue; }
        }
        vector<int> span; int constant=-1;
        if(prod.s==m.zero) constant=0;
        else if(prod.s==m.one) constant=1;
        else {
          for(uint32_t j=0;j<nq;j++) {
            if(q[j]==prod.s) { span={int(j)}; break; }
            if((q[j]^m.one)==prod.s) { span={int(j),int(nq)}; break; }
          }
          if(span.empty()&&!no_span) { span_queries++; span=solve_span(q,m.one,prod.s); }
        }
        if(constant<0&&span.empty()) continue;
        if(comma) out<<','; comma=true; candidates++;
        out<<"{\"index\":"<<pos<<",\"phase_qubit\":"<<x[c]<<",\"product_controls\":["<<x[a]<<','<<x[b]<<"],\"origin\":"<<prod.origin<<",\"constant\":"<<constant<<",\"condition\":"<<condition<<",\"depth\":"<<depth<<",\"span_wires\":[";
        for(size_t j=0;j<span.size();j++) { if(j) out<<','; out<<span[j]; }
        out<<"]}"; break;
      }
    } else if(base==0x00||base==0x10||base==0x13||base==0x20||base==0x40||base==0x41||base==0x42||base==0x06||base==0x07||base==0x17||base==0x47) {}
    else throw runtime_error("unsupportedopcode");
    if(base==0x50||base==0x40||base==0x41||base==0x42) bit_versions[bit]++;
  }
  if(depth) throw runtime_error("unclosedguard");
  // Packet11 is the metadata/string table, not an operand stream.
  for(int c=1;c<=10;c++) if(p[c]!=end[c]) throw runtime_error("unusedcolumnbytes");
  out<<"],\"num_ops\":"<<n<<",\"qubits\":"<<nq<<",\"ccx\":"<<ccx<<",\"cswap\":"<<cswaps<<",\"ccz\":"<<ccz<<",\"repeated_pair_queries\":"<<pair_hits<<",\"span_queries\":"<<span_queries<<",\"candidate_count\":"<<candidates<<",\"sparse_pair_skips\":"<<sparse_pair_skips<<",\"formal_atoms\":"<<m.atoms<<",\"phase_queries\":"<<phase_queries<<",\"phase_duplicate_count\":"<<duplicates.size()<<",\"phase_duplicates\":[";
  for(size_t j=0;j<duplicates.size();j++) {
    if(j) out<<','; auto v=duplicates[j];
    out<<"{\"first\":"<<v.first<<",\"second\":"<<v.second<<",\"condition\":"<<v.condition<<",\"depth\":"<<v.depth<<"}";
  }
  out<<"]}\n";
  cerr<<"CCZ="<<ccz<<" cached pair queries="<<pair_hits<<" span queries="<<span_queries<<" candidates="<<candidates<<" phase duplicates="<<duplicates.size()<<"\n";
  munmap(d,st.st_size); close(fd); return 0;
} catch(const exception& e) { cerr<<e.what()<<'\n'; return 1; } }

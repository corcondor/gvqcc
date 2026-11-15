// SPDX-License-Identifier: Apache-2.0
// Conditional XOR/AND fingerprints for phase-reuse DISCOVERY ONLY.
// Unlike scans that forget a wire on every conditional CX, carry the
// captured classical predicate through all Boolean updates. Hash matches
// require an independent exact replay; no circuit is modified here.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>
using namespace std;
struct S { uint64_t a=0,b=0; bool operator==(const S&o)const{return a==o.a&&b==o.b;} bool operator<(const S&o)const{return a!=o.a?a<o.a:b<o.b;} };
static S operator^(S a,S b){return {a.a^b.a,a.b^b.b};}
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
const S ZERO{},ONE{0x465a3c967bab1287ULL,0x1749e82abbdef583ULL};
S mult(S a,S b){
 if(a==ZERO||b==ZERO)return ZERO;if(a==ONE)return b;if(b==ONE||a==b)return a;if(a==(b^ONE))return ZERO;
 bool na=(a^ONE)<a,nb=(b^ONE)<b;if(na)a=a^ONE;if(nb)b=b^ONE;
 S x=a,y=b;if(y<x)swap(x,y);
 S r{mix(x.a^mix(y.b)^0xfae15d475ULL)^mix(x.b+mix(y.a)),mix(x.b^mix(y.a)^0x1389f3ab5ULL)^mix(x.a+mix(y.b))};
 if(na)r=r^b;if(nb)r=r^a;if(na&&nb)r=r^ONE;return r;
}
uint64_t le(const uint8_t*p,int n){uint64_t x=0;for(int i=0;i<n;i++)x|=uint64_t(p[i])<<(8*i);return x;}
struct Key {array<S,3> v;bool operator==(const Key&o)const{return v==o.v;}};
struct KH {size_t operator()(const Key&k)const{uint64_t r=0;for(auto v:k.v)r=mix(r^v.a)^mix(v.b);return r;}};
struct Prior {uint64_t pos;array<uint32_t,3> q;S guard;};
int main(int argc,char**argv){try{
 if(argc!=3)throw runtime_error("usage: conditional-phase-scan input.kmb discovery.json");
 int fd=open(argv[1],O_RDONLY);struct stat st{};if(fd<0||fstat(fd,&st))throw runtime_error("input failed");
 auto*d=(uint8_t*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
 const uint8_t magic[]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
 if(d==MAP_FAILED||st.st_size<104||memcmp(d,magic,16)||le(d+16,4)!=2)throw runtime_error("not KMBv2");
 uint64_t nq=le(d+20,4),nb=le(d+24,4),nr=le(d+28,4),n=le(d+32,8),at=104;
 vector<bool>abi(nq,false);array<uint64_t,12>p{},end{};
 for(uint64_t i=0;i<nr+11;i++){
  if(at+16>uint64_t(st.st_size))throw runtime_error("short packet");auto kind=le(d+at,8),len=le(d+at+8,8);at+=16;
  if(kind!=(i<nr?0:i-nr+1)||len>uint64_t(st.st_size)-at)throw runtime_error("packet invalid");
  if(kind){p[kind]=at;end[kind]=at+len;}else{auto nl=le(d+at,4),rl=le(d+at+4,4);if(len!=8+nl+4*rl)throw runtime_error("register length");for(uint64_t j=0;j<rl;j++){auto r=le(d+at+8+nl+4*j,4);if(r&0x80000000u){auto q=r&0x7fffffffu;if(q>=nq)throw runtime_error("ABI qubit");abi[q]=true;}}}at+=len;
 }
 if(at!=uint64_t(st.st_size))throw runtime_error("trailing bytes");
 auto take=[&](int c,int bytes){if(p[c]+bytes>end[c])throw runtime_error("column exhausted");auto v=le(d+p[c],bytes);p[c]+=bytes;return v;};
 uint64_t atoms=0;auto fresh=[&](){auto i=++atoms;return S{mix(i^0xf0785eab12ULL),mix(i^0x9423467891ULL)};};
 vector<S>q(nq),b(nb);for(uint64_t i=0;i<nq;i++)q[i]=abi[i]?fresh():ZERO;for(auto&x:b)x=fresh();
 vector<S> stack;S implicit=ONE;unordered_map<Key,Prior,KH> phases;uint64_t ccx=0,ccz=0,reuse=0,reduced=0,zero_guards=0;
 ofstream out(argv[2]);if(!out)throw runtime_error("output failed");out<<"{\"status\":\"DISCOVERY_ONLY_REQUIRES_EXACT_REPLAY\",\"opportunities\":[";bool comma=false;
 for(uint64_t pos=0;pos<n;pos++){
  auto op=take(1,1);int base=op&127,arity=(op>>4)&3;array<uint32_t,3>x{};for(int j=0;j<arity;j++){x[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(x[j]>=nq)throw runtime_error("qubit overflow");}
  int64_t bit=(op&64)?int64_t(take(8,4)):-1,cond=(op&128)?int64_t(take(9,4)):-1;
  if(bit>=int64_t(nb)||cond>=int64_t(nb))throw runtime_error("bit overflow");if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){stack.push_back(implicit);implicit=mult(implicit,b[cond]);continue;}
  if(op==0x01){if(stack.empty())throw runtime_error("empty condition stack");implicit=stack.back();stack.pop_back();continue;}
  S g=cond<0?implicit:mult(implicit,b[cond]);if(g==ZERO)zero_guards++;
  if(base==0x11)q[x[0]]=q[x[0]]^g;
  else if(base==0x21)q[x[1]]=q[x[1]]^mult(g,q[x[0]]);
  else if(base==0x22){auto v=mult(g,q[x[0]]^q[x[1]]);q[x[0]]=q[x[0]]^v;q[x[1]]=q[x[1]]^v;}
  else if(base==0x32){auto v=mult(mult(g,q[x[0]]),q[x[1]]^q[x[2]]);q[x[1]]=q[x[1]]^v;q[x[2]]=q[x[2]]^v;}
  else if(base==0x12)q[x[0]]=q[x[0]]^mult(g,q[x[0]]);
  else if(base==0x50){q[x[0]]=q[x[0]]^mult(g,q[x[0]]);b[bit]=b[bit]^mult(g,b[bit]^fresh());}
  else if(base==0x31){ccx++;q[x[2]]=q[x[2]]^mult(g,mult(q[x[0]],q[x[1]]));}
  else if(base==0x40)b[bit]=b[bit]^mult(g,b[bit]);
  else if(base==0x41)b[bit]=b[bit]^mult(g,b[bit]^ONE);
  else if(base==0x42)b[bit]=b[bit]^g;
  else if(base==0x30){
   ccz++;array<S,3>a{q[x[0]],q[x[1]],q[x[2]]};string reason;
   for(int j=0;j<3;j++){if(a[j]==ZERO)reason="zero_factor";else if(a[j]==ONE)reason="constant_one";for(int k=j+1;k<3;k++){if(a[j]==a[k])reason="equal_factors";if(a[j]==(a[k]^ONE))reason="complement_factors";}}
   if((a[0]^a[1]^a[2])==ZERO)reason="affine_rank2_zero";if((a[0]^a[1]^a[2])==ONE)reason="affine_rank2_one";
   if(!reason.empty()){if(comma)out<<',';comma=true;reduced++;out<<"{\"kind\":\"reduced_phase\",\"index\":"<<pos<<",\"reason\":\""<<reason<<"\",\"wires\":["<<x[0]<<','<<x[1]<<','<<x[2]<<"]}";}
   sort(a.begin(),a.end());Key k{a};auto it=phases.find(k);
   if(it!=phases.end()&&!(g==ZERO)){if(comma)out<<',';comma=true;reuse++;out<<"{\"kind\":\"repeated_phase\",\"first\":"<<it->second.pos<<",\"second\":"<<pos<<",\"first_wires\":["<<it->second.q[0]<<','<<it->second.q[1]<<','<<it->second.q[2]<<"],\"second_wires\":["<<x[0]<<','<<x[1]<<','<<x[2]<<"],\"same_guard\":"<<(g==it->second.guard?"true":"false")<<"}";}
   if(!(g==ZERO))phases[k]={pos,x,g};
  }else if(base==0x00||base==0x10||base==0x13||base==0x20||base==0x06||base==0x07||base==0x17||base==0x47){}
  else throw runtime_error("unsupported opcode");
 }
 if(!stack.empty())throw runtime_error("unclosed condition");for(int k=1;k<11;k++)if(p[k]!=end[k])throw runtime_error("column remainder");
 out<<"],\"ccx\":"<<ccx<<",\"ccz\":"<<ccz<<",\"repeated_phases\":"<<reuse<<",\"reduced_phases\":"<<reduced<<",\"formal_atoms\":"<<atoms<<",\"zero_guard_operations\":"<<zero_guards<<",\"num_ops\":"<<n<<",\"num_qubits\":"<<nq<<",\"num_bits\":"<<nb<<"}\n";
 cerr<<"CCZ="<<ccz<<" repeated="<<reuse<<" reduced="<<reduced<<"\n";munmap(d,st.st_size);close(fd);return 0;
 }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

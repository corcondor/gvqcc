// 128-bit symbolic fingerprints screen repeated ANDs across HMR/phase gates.
// This is candidate discovery only. Every accepted rewrite needs a separate
// exact symbolic certificate; neither fingerprints nor random scoring samples
// establish equivalence. Fixed fingerprint constants are not verifier seeds.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <deque>
#include <fcntl.h>
#include <iostream>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>
using V=__uint128_t;
uint64_t r64(const unsigned char*p){uint64_t x;std::memcpy(&x,p,8);return x;}
uint32_t r32(const unsigned char*p){uint32_t x;std::memcpy(&x,p,4);return x;}
uint64_t rng_state=0xd49e88a57b236901ULL;
uint64_t fresh64(){uint64_t z=(rng_state+=0x9e3779b97f4a7c15ULL);z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
V fresh(){V hi=fresh64();return (hi<<64)|fresh64();}
struct Key{V value;unsigned scope;bool operator==(const Key&b)const{return value==b.value&&scope==b.scope;}};
struct Hash{size_t operator()(const Key&x)const{return (uint64_t)x.value^((uint64_t)(x.value>>64)*0x9e3779b97f4a7c15ULL)^(uint64_t(x.scope)*0xbf58476d1ce4e5b9ULL);}};
struct Rec{uint64_t index;std::array<unsigned,3> q;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage: cache-screen circuit.kmb");
 int fd=open(argv[1],O_RDONLY);if(fd<0)throw std::runtime_error("open failed");
 struct stat st;if(fstat(fd,&st)||st.st_size<104)throw std::runtime_error("short input");
 auto*p=(unsigned char*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(p==MAP_FAILED)throw std::runtime_error("mmap failed");
 const unsigned char magic[16]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
 unsigned nq=r32(p+20),nb=r32(p+24),nr=r32(p+28);uint64_t n=r64(p+32),off=104;
 if(std::memcmp(p,magic,16)||r32(p+16)!=2||nq>100000||nb>10000000)throw std::runtime_error("bad header");
 std::array<const unsigned char*,12>c{};std::array<uint64_t,12>len{},rank{};
 for(unsigned i=0;i<nr;i++){if(off+16>(uint64_t)st.st_size||r64(p+off)!=0)throw std::runtime_error("bad register");off+=16+r64(p+off+8);}
 for(unsigned k=1;k<12;k++){if(off+16>(uint64_t)st.st_size||r64(p+off)!=k)throw std::runtime_error("bad packet");len[k]=r64(p+off+8);off+=16;if(len[k]>(uint64_t)st.st_size-off)throw std::runtime_error("short packet");c[k]=p+off;off+=len[k];}
 if(len[1]!=n)throw std::runtime_error("bad operation count");
 auto arg=[&](unsigned k){if(4*rank[k]+4>len[k])throw std::runtime_error("operand overflow");return r32(c[k]+4*rank[k]++);};
 std::vector<V>q(nq),b(nb),stack;for(auto&v:q)v=fresh();for(auto&v:b)v=fresh();V active=~V(0);
 unsigned scope=0;std::vector<unsigned>parents(1,0),depths(1,0),clean_scope(nq,0);
 std::vector<int64_t>last_ref(nq,-1),last_clean(nq,-1);std::vector<bool>clean(nq,false);
 std::unordered_map<Key,std::deque<Rec>,Hash>history;uint64_t scanned=0,pairs=0,eligible=0;
 const uint64_t window=50000;const size_t history_cap=8;bool comma=false;
 std::cout<<"{\"window\":"<<window<<",\"history_cap\":"<<history_cap<<",\"candidates\":[";
 for(uint64_t i=0;i<n;i++){
   unsigned op=c[1][i],base=op&127,nqt=(op&48)>>4;std::array<unsigned,3>a{};
   if(nqt==1)a[0]=arg(7);else if(nqt==2){a[0]=arg(5);a[1]=arg(6);}else if(nqt==3){a[0]=arg(2);a[1]=arg(3);a[2]=arg(4);}
   unsigned bit=0,cond=0;if(op&64)bit=arg(8);if(op&128)cond=arg(9);
   if(op==0x81){stack.push_back(active);active&=b[cond];parents.push_back(scope);depths.push_back(depths[scope]+1);scope=parents.size()-1;continue;}
   if(op==0x01){if(stack.empty())throw std::runtime_error("unbalanced pop");active=stack.back();stack.pop_back();scope=parents[scope];continue;}
   V enabled=(op&128)?active&b[cond]:active;
   if(op==0x31){
     scanned++;V value=q[a[0]]&q[a[1]]&active;
     if(value&&value!=~V(0)){
       auto &prev=history[Key{value,scope}];
       while(!prev.empty()&&prev.front().index+window<i)prev.pop_front();
       for(auto it=prev.rbegin();it!=prev.rend();++it){
         pairs++;int cache=-1;
         for(unsigned k=0;k<nq;k++)if(clean[k]&&last_ref[k]<(int64_t)it->index&&k!=a[0]&&k!=a[1]&&k!=a[2]){unsigned ancestor=scope;while(depths[ancestor]>depths[clean_scope[k]])ancestor=parents[ancestor];if(ancestor==clean_scope[k]){cache=k;break;}}
         if(cache>=0){eligible++;if(comma)std::cout<<",";comma=true;
           std::cout<<"{\"first\":"<<it->index<<",\"last\":"<<i<<",\"first_qubits\":["<<it->q[0]<<","<<it->q[1]<<","<<it->q[2]<<"],\"last_qubits\":["<<a[0]<<","<<a[1]<<","<<a[2]<<"],\"cache\":"<<cache<<",\"last_cache_ref\":"<<last_ref[cache]<<",\"last_cache_clean\":"<<last_clean[cache]<<",\"inherited_depth\":"<<depths[scope]<<"}";
         }
       }
       prev.push_back({i,a});if(prev.size()>history_cap)prev.pop_front();
     }
   }
   auto put=[&](unsigned k,V value){q[a[k]]^=enabled&(q[a[k]]^value);};
   switch(base){
     case 0x11:put(0,~q[a[0]]);break;
     case 0x12:put(0,0);break;
     case 0x21:put(1,q[a[0]]^q[a[1]]);break;
     case 0x31:put(2,q[a[2]]^(q[a[0]]&q[a[1]]));break;
     case 0x22:{V t=q[a[0]],u=q[a[1]];put(0,u);put(1,t);break;}
     case 0x32:{V d=enabled&q[a[0]]&(q[a[1]]^q[a[2]]);q[a[1]]^=d;q[a[2]]^=d;break;}
     case 0x40:b[bit]&=~enabled;break;
     case 0x41:b[bit]|=enabled;break;
     case 0x42:b[bit]^=enabled;break;
     case 0x50:put(0,0);b[bit]^=enabled&(b[bit]^fresh());break;
     case 0x00:case 0x10:case 0x13:case 0x20:case 0x30:case 0x06:case 0x07:case 0x47:case 0x17:break;
     default:throw std::runtime_error("unsupported opcode");
   }
   for(unsigned k=0;k<nqt;k++){last_ref[a[k]]=i;clean[a[k]]=false;}
   if(op==0x12||op==0x50){clean[a[0]]=true;last_clean[a[0]]=i;clean_scope[a[0]]=scope;}
 }
 if(!stack.empty())throw std::runtime_error("unclosed stack");
 for(unsigned k=2;k<=9;k++)if(rank[k]*4!=len[k])throw std::runtime_error("unconsumed operands");
 std::cout<<"],\"scanned_no_explicit_condition_ccx\":"<<scanned<<",\"fingerprint_pairs\":"<<pairs<<",\"eligible\":"<<eligible<<",\"status\":\"SCREEN_ONLY_EXACT_PROOF_REQUIRED\"}\n";
 munmap(p,st.st_size);close(fd);return 0;
}catch(std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}

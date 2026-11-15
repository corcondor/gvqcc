// SPDX-License-Identifier: Apache-2.0
// Common-control native CCX and CCZ factorization screen.
#include <algorithm>
#include <array>
#include <unordered_map>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
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
 struct Hit {uint64_t pos; unsigned third;};
 unordered_map<uint64_t,vector<Hit>> x,z;
 vector<uint64_t> last_use(nq), last_write(nq);
 const auto key=[&](uint64_t a,uint64_t b){return min(a,b)*nq+max(a,b);};
 uint64_t boundary=0,counts[2][2]{},contiguous[2][2]{},depth=0;
 ofstream out(argv[2]);out<<"{\"examples\":[";
 bool comma=false;
 for(uint64_t i=1;i<=n;i++){
  auto op=take(1,1);unsigned base=op&127,arity=(op>>4)&3;array<unsigned,3> q{};
  for(unsigned j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("q");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("b");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){boundary=i;depth++;continue;}
  if(op==0x01){if(!depth)throw runtime_error("pop");boundary=i;depth--;continue;}
  if(c<0&&(base==0x30||base==0x31)){
   bool phase=base==0x30;auto &seen=phase?z:x;
   for(unsigned t=phase?0:2;t<3;t++){
    const auto a=q[(t+1)%3],b=q[(t+2)%3],u=q[t];
    auto k=key(a,b);
    auto &prior=seen[k];
    const auto barrier=max({boundary,last_write[a],last_write[b]});
    for(auto it=prior.rbegin();it!=prior.rend()&&it->pos>=barrier;++it){
     const auto h=*it;
     if(h.pos>=(phase?last_write[h.third]:last_use[h.third])){
      const bool distinct=h.third!=u;
      counts[phase][distinct]++;
      contiguous[phase][distinct]+=(i==h.pos+1);
      if(counts[phase][distinct]<=3){
       if(comma)out<<',';comma=true;
       out<<"{\"type\":\""<<(phase?"CCZ":"CCX")<<"\",\"first\":"<<h.pos-1<<",\"second\":"<<i-1
          <<",\"controls\":["<<a<<','<<b<<"],\"third\":["<<h.third<<','<<u<<"],\"branch_depth\":"<<depth<<'}';
      }
     }
    }
    if(!prior.empty()&&prior.back().pos<barrier)prior.clear();
    prior.push_back({i,u});
   }
  }
  for(unsigned j=0;j<arity;j++)last_use[q[j]]=i;
  if(base==0x11||base==0x12||base==0x50)last_write[q[0]]=i;
  else if(base==0x21||base==0x31)last_write[q[arity-1]]=i;
  else if(base==0x22||base==0x32){last_write[q[arity-2]]=i;last_write[q[arity-1]]=i;}
 }
 if(depth)throw runtime_error("unclosed");
 out<<"],\"ccx_same\":"<<counts[0][0]<<",\"ccx_distinct\":"<<counts[0][1]
    <<",\"ccz_same\":"<<counts[1][0]<<",\"ccz_distinct\":"<<counts[1][1]
    <<",\"contiguous_ccx_same\":"<<contiguous[0][0]<<",\"contiguous_ccx_distinct\":"<<contiguous[0][1]
    <<",\"contiguous_ccz_same\":"<<contiguous[1][0]<<",\"contiguous_ccz_distinct\":"<<contiguous[1][1]
    <<",\"num_ops\":"<<n<<"}\n";
 munmap((void*)d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

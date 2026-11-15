// SPDX-License-Identifier: Apache-2.0
// Discovery for exact M_m X_t^f = (-1)^(m f) M_m interval rewrites.
// Arbitrary quantum input is allowed. Any target read, phase, swap, reset,
// or earlier measurement is a barrier. Only depth-zero unconditional HMR.
#include <array>
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
 if(argc!=3&&argc!=4)throw runtime_error("input.kmb output.json [within-branches] required");
 bool within_branches=argc==4;
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
 vector<vector<Write>> tails(nq);unsigned depth=0;
 uint64_t hmrs=0,eligible=0,candidates=0,saved=0,zero_tails=0,last_boundary=0;
 ofstream out(argv[2]);out<<"{\"schema\":\"hmr-target-write-tail-v1\",\"candidates\":[";
 for(uint64_t pos=0;pos<n;pos++){
  auto op=take(1,1);unsigned base=op&127,arity=(op>>4)&3;array<unsigned,3> q{};
  for(unsigned j=0;j<arity;j++){q[j]=take(arity==3?2+j:arity==2?5+j:7,4);if(q[j]>=nq)throw runtime_error("q");}
  int64_t b=(op&64)?int64_t(take(8,4)):-1,c=(op&128)?int64_t(take(9,4)):-1;
  if(b>=int64_t(nb)||c>=int64_t(nb))throw runtime_error("b");
  if(base==0x13){take(10,8);take(10,8);}
  if(op==0x81){last_boundary=pos;depth++;continue;}if(op==0x01){if(!depth)throw runtime_error("pop");last_boundary=pos;depth--;continue;}
  if(base==0x50){
   hmrs++;
   if(c<0&&(within_branches||!depth)){
    eligible++;auto&v=tails[q[0]];size_t start=0;
    while(start<v.size()&&(within_branches?v[start].pos<=last_boundary:v[start].depth!=0))start++;
    uint64_t count=0;for(size_t i=start;i<v.size();i++)count+=(v[i].op==0x31);
    if(count){
     if(candidates++)out<<',';saved+=count;
     out<<"{\"start\":"<<v[start].pos<<",\"hmr\":"<<pos<<",\"target\":"<<q[0]<<",\"measurement_bit\":"<<b<<",\"inherited_depth\":"<<depth<<",\"ccx_removed\":"<<count<<",\"writes\":[";
     for(size_t i=start;i<v.size();i++)out<<(i==start?"":",")<<v[i].pos;
     out<<"]}";
    }else if(start<v.size())zero_tails++;
   }
  }
  if(base==0x11||base==0x21||base==0x31){
   for(unsigned j=0;j+1<arity;j++)tails[q[j]].clear();
   tails[q[arity-1]].push_back({pos,base,depth});
  }else for(unsigned j=0;j<arity;j++)tails[q[j]].clear();
 }
 if(depth)throw runtime_error("unclosed");
 out<<"],\"hmr_seen\":"<<hmrs<<",\"eligible_hmr\":"<<eligible<<",\"within_fixed_branch\":"<<(within_branches?"true":"false")<<",\"positive_intervals\":"<<candidates<<",\"potential_static_ccx_reduction\":"<<saved<<",\"zero_ccx_intervals\":"<<zero_tails<<",\"qubits\":"<<nq<<",\"num_ops\":"<<n<<",\"scope\":\"Read-only discovery; every target read is a barrier; fixed-branch mode cuts at every PUSH/POP; no KMB mutation or score claim.\"}\n";
 cerr<<"HMR="<<hmrs<<" intervals="<<candidates<<" potential CCX="<<saved<<'\n';
 munmap((void*)d,st.st_size);close(fd);return 0;
}catch(const exception&e){cerr<<e.what()<<'\n';return 1;}}

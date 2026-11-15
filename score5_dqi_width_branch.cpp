// Branch-sensitive known-zero lifetime audit. Never considers a conditional
// reset global unless every skipped enclosing branch also has that wire zero.
// All ABI data and all classical conditions are arbitrary. Each PUSH joins at
// POP, retaining compute/HMR/reset cancellation within the executed arm.
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
#include <vector>
uint32_t u32(const unsigned char*p){uint32_t v;std::memcpy(&v,p,4);return v;}
uint64_t u64(const unsigned char*p){uint64_t v;std::memcpy(&v,p,8);return v;}
unsigned join(unsigned x,unsigned y){return x==y?x:2;}
unsigned band(unsigned x,unsigned y){if(!x||!y)return 0;if(x==1&&y==1)return 1;return 2;}
unsigned bxor(unsigned x,unsigned y){return x<2&&y<2?x^y:2;}
struct Interval{unsigned q;uint64_t a,b;};
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("input.kmb output.tsv required");
 int fd=open(argv[1],O_RDONLY);struct stat st;if(fd<0||fstat(fd,&st))throw std::runtime_error("open");
 auto*p=(const unsigned char*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(p==MAP_FAILED)throw std::runtime_error("mmap");
 if(u32(p+16)!=2)throw std::runtime_error("KMB v2 required");
 unsigned nq=u32(p+20),nr=u32(p+28);auto n=u64(p+32);uint64_t off=104;std::vector<unsigned char>abi(nq);
 for(unsigned j=0;j<nr;j++){
  if(u64(p+off)!=0)throw std::runtime_error("register");auto len=u64(p+off+8);off+=16;
  auto nl=u32(p+off),rl=u32(p+off+4);if(len!=8+nl+4ull*rl)throw std::runtime_error("register length");
  for(unsigned k=0;k<rl;k++){auto raw=u32(p+off+8+nl+4*k);if(raw&0x80000000u)abi.at(raw&0x7fffffffu)=1;}off+=len;
 }
 std::array<const unsigned char*,12>col{};std::array<uint64_t,12>lens{};
 for(unsigned k=1;k<12;k++){if(u64(p+off)!=k)throw std::runtime_error("column");lens[k]=u64(p+off+8);off+=16;col[k]=p+off;off+=lens[k];}
 if(off!=(uint64_t)st.st_size||lens[1]!=n)throw std::runtime_error("layout");
 std::vector<unsigned char>state(nq,0);std::vector<std::vector<unsigned char>>stack;
 std::vector<int64_t>start(nq,-1);std::vector<Interval>intervals;
 unsigned live=0,peak=0,maxdepth=0;uint64_t peak_at=0,zero_transitions=0,abi_transitions=0;
 for(unsigned q=0;q<nq;q++)if(abi[q]){state[q]=2;start[q]=0;live++;}peak=live;
 auto global_zero=[&](unsigned q){if(state[q])return false;for(auto const&s:stack)if(s[q])return false;return true;};
 auto release=[&](unsigned q,uint64_t i){if(start[q]>=0&&global_zero(q)){
  intervals.push_back({q,(uint64_t)start[q],i});start[q]=-1;live--;zero_transitions++;if(abi[q])abi_transitions++;
 }};
 std::array<uint64_t,4>rank{};std::map<unsigned,uint64_t>unsupported;
 for(uint64_t i=0;i<n;i++){
  unsigned op=col[1][i],base=op&127,count=(op&48)>>4;
  if(op==0x81){stack.push_back(state);maxdepth=std::max(maxdepth,(unsigned)stack.size());continue;}
  if(op==0x01){if(stack.empty())throw std::runtime_error("pop");auto old=std::move(stack.back());stack.pop_back();
    for(unsigned q=0;q<nq;q++){state[q]=join(state[q],old[q]);release(q,i);}continue;}
  if(!count)continue;
  unsigned columns[3],qs[3];if(count==1)columns[0]=7;else if(count==2){columns[0]=5;columns[1]=6;}else{columns[0]=2;columns[1]=3;columns[2]=4;}
  for(unsigned j=0;j<count;j++){qs[j]=u32(col[columns[j]]+rank[count]*4);if(qs[j]>=nq)throw std::runtime_error("q range");if(start[qs[j]]<0){start[qs[j]]=i;live++;}}
  rank[count]++;if(live>peak){peak=live;peak_at=i;}
  auto assign=[&](unsigned q,unsigned value){state[q]=(op&128)?join(state[q],value):value;};
  unsigned a=qs[0],b=count>1?qs[1]:0,c=count>2?qs[2]:0;
  switch(base){
   case 0x11:assign(a,bxor(state[a],1));break;
   case 0x12:case 0x50:assign(a,0);break;
   case 0x21:assign(b,bxor(state[a],state[b]));break;
   case 0x31:assign(c,bxor(state[c],band(state[a],state[b])));break;
   case 0x22:{auto va=state[a],vb=state[b];assign(a,vb);assign(b,va);break;}
   case 0x32:{auto vb=state[b],vc=state[c];if(state[a]==1){assign(b,vc);assign(c,vb);}else if(state[a]==2){assign(b,join(vb,vc));assign(c,join(vb,vc));}break;}
   case 0x10:case 0x13:case 0x20:case 0x30:case 0x17:break;
   default:unsupported[base]++;for(unsigned j=0;j<count;j++)assign(qs[j],2);
  }
  for(unsigned j=0;j<count;j++)release(qs[j],i);
 }
 if(!stack.empty())throw std::runtime_error("unclosed");
 for(unsigned q=0;q<nq;q++)if(start[q]>=0)intervals.push_back({q,(uint64_t)start[q],n});
 std::sort(intervals.begin(),intervals.end(),[](auto const&a,auto const&b){return a.q!=b.q?a.q<b.q:a.a<b.a;});
 std::ofstream out(argv[2]);out<<"q\tfirst\tlast\tabi\n";for(auto const&v:intervals)out<<v.q<<'\t'<<v.a<<'\t'<<v.b<<'\t'<<(int)abi[v.q]<<'\n';
 std::cout<<"{\"status\":\"BRANCH_SENSITIVE_CONSTANT_LIFETIME_AUDIT\",\"num_ops\":"<<n<<",\"qubits\":"<<nq<<",\"peak\":"<<peak<<",\"first_peak_at\":"<<peak_at<<",\"intervals\":"<<intervals.size()<<",\"zero_transitions\":"<<zero_transitions<<",\"ABI_zero_transitions\":"<<abi_transitions<<",\"max_depth\":"<<maxdepth<<",\"unsupported\":{";
 bool first=true;for(auto const&v:unsupported){if(!first)std::cout<<",";first=false;std::cout<<'"'<<v.first<<"\":"<<v.second;}
 std::cout<<"},\"final_live\":"<<live<<",\"scope\":\"Conservative branchwise bit constants, arbitrary all ABI and classical conditions; preserves skipped-branch storage, not a semantic lower bound.\"}\n";
 munmap((void*)p,st.st_size);close(fd);return 0;
 }catch(std::exception const&e){std::cerr<<e.what()<<'\n';return 1;}}

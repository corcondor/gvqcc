// Whole-register lifetime audit. Unlike the earlier scratch-only audit, ABI
// quantum wires can be borrowed between an unconditional reset and their next
// touch. ABI references themselves remain pinned; input/output register bytes
// are never changed. Streaming mmap parser: no per-operation object expansion.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
uint32_t u32(const unsigned char*p){uint32_t v;std::memcpy(&v,p,4);return v;}
uint64_t u64(const unsigned char*p){uint64_t v;std::memcpy(&v,p,8);return v;}
struct Interval{uint32_t q;uint64_t first,last;};
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Usage: width_intervals input.kmb intervals.tsv");
 int fd=open(argv[1],O_RDONLY);struct stat st;if(fd<0||fstat(fd,&st))throw std::runtime_error("input failed");
 auto*p=(const unsigned char*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(p==MAP_FAILED)throw std::runtime_error("mmap failed");
 const unsigned char magic[16]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
 if(st.st_size<104||std::memcmp(p,magic,16)||u32(p+16)!=2)throw std::runtime_error("KMB v2 required");
 unsigned nq=u32(p+20),nr=u32(p+28);uint64_t n=u64(p+32),off=104;std::vector<bool> abi(nq);
 for(unsigned j=0;j<nr;j++){
   if(off+16>(uint64_t)st.st_size||u64(p+off)!=0)throw std::runtime_error("register packet");
   auto len=u64(p+off+8);off+=16;if(len<8||off+len>(uint64_t)st.st_size)throw std::runtime_error("short register");
   auto nl=u32(p+off),rl=u32(p+off+4);if(len!=8+nl+4ull*rl)throw std::runtime_error("register size");
   for(unsigned k=0;k<rl;k++){auto raw=u32(p+off+8+nl+4*k);if(raw&0x80000000u){auto q=raw&0x7fffffffu;if(q>=nq)throw std::runtime_error("ABI ID");abi[q]=true;}}
   off+=len;
 }
 std::array<const unsigned char*,12>col{};std::array<uint64_t,12>len{};
 for(unsigned k=1;k<12;k++){if(off+16>(uint64_t)st.st_size||u64(p+off)!=k)throw std::runtime_error("column packet");len[k]=u64(p+off+8);off+=16;if(off+len[k]>(uint64_t)st.st_size)throw std::runtime_error("column length");col[k]=p+off;off+=len[k];}
 if(off!=(uint64_t)st.st_size||len[1]!=n)throw std::runtime_error("file layout");
 std::vector<int64_t>start(nq,-1);unsigned live=0;for(unsigned q=0;q<nq;q++)if(abi[q]){start[q]=0;live++;}
 unsigned abi_count=live,peak=live;uint64_t peak_at=0,depth=0,maxdepth=0,qops=0,uncond=0,conditional=0,abi_resets=0;
 std::array<uint64_t,4>rank{};std::vector<uint64_t>touches(nq),resets(nq);std::vector<Interval> intervals;
 std::vector<unsigned>first_peak_live;
 for(uint64_t i=0;i<n;i++){
   unsigned op=col[1][i],base=op&127,count=(op&48)>>4;
   if(op==0x81){depth++;maxdepth=std::max(depth,maxdepth);}else if(op==0x01){if(!depth)throw std::runtime_error("pop underflow");depth--;}
   if(!count)continue;qops++;
   unsigned columns[3];if(count==1)columns[0]=7;else if(count==2){columns[0]=5;columns[1]=6;}else{columns[0]=2;columns[1]=3;columns[2]=4;}
   bool reset=base==0x12||base==0x50,release=reset&&!(op&128)&&depth==0;
   if(reset){if(release)uncond++;else conditional++;}
   unsigned qs[3];for(unsigned j=0;j<count;j++){
     if(4*rank[count]+4>len[columns[j]])throw std::runtime_error("operand overflow");
     auto q=u32(col[columns[j]]+4*rank[count]);if(q>=nq)throw std::runtime_error("qubit ID");qs[j]=q;touches[q]++;
     if(!release&&start[q]<0){start[q]=i;live++;}
   }
   if(live>peak){peak=live;peak_at=i;first_peak_live.clear();for(unsigned q=0;q<nq;q++)if(start[q]>=0)first_peak_live.push_back(q);}
   if(release)for(unsigned j=0;j<count;j++){
     auto q=qs[j];resets[q]++;if(abi[q])abi_resets++;
     if(start[q]>=0){intervals.push_back({q,(uint64_t)start[q],i});start[q]=-1;live--;}
   }
   rank[count]++;
 }
 if(depth)throw std::runtime_error("unclosed condition");
 for(unsigned q=0;q<nq;q++)if(start[q]>=0)intervals.push_back({q,(uint64_t)start[q],n});
 std::sort(intervals.begin(),intervals.end(),[](auto const&a,auto const&b){return a.q!=b.q?a.q<b.q:a.first<b.first;});
 std::ofstream out(argv[2]);out<<"q\tfirst\tlast\tabi\n";for(auto const&s:intervals)out<<s.q<<'\t'<<s.first<<'\t'<<s.last<<'\t'<<abi[s.q]<<'\n';
 std::cout<<"{\"status\":\"WHOLE_REGISTER_RESET_INTERVAL_AUDIT\",\"num_ops\":"<<n<<",\"qubits\":"<<nq<<",\"ABI_qubits\":"<<abi_count<<",\"intervals\":"<<intervals.size()<<",\"global_peak\":"<<peak<<",\"first_peak_at\":"<<peak_at<<",\"quantum_ops\":"<<qops<<",\"unconditional_resets\":"<<uncond<<",\"ABI_unconditional_resets\":"<<abi_resets<<",\"conditional_resets_not_releasing\":"<<conditional<<",\"max_condition_depth\":"<<maxdepth<<",\"final_nonzero_bound\":"<<live<<",\"per_wire\":[";
 for(unsigned q=0;q<nq;q++)std::cout<<(q?",":"")<<"{\"q\":"<<q<<",\"abi\":"<<(abi[q]?"true":"false")<<",\"touches\":"<<touches[q]<<",\"unconditional_resets\":"<<resets[q]<<"}";
 std::cout<<"],\"first_peak_live_wires\":[";for(size_t j=0;j<first_peak_live.size();j++)std::cout<<(j?",":"")<<first_peak_live[j];
 std::cout<<"],\"scope\":\"All quantum ABI values arbitrary initially; scratch initially zero. Only unconditional R/HMR ends an interval. ABI physical positions remain fixed when occupied but their reset-separated zero gaps are borrowable. Conservative interval peak, not semantic minimum.\"}\n";
 munmap((void*)p,st.st_size);close(fd);return 0;
}catch(std::exception const&e){std::cerr<<e.what()<<'\n';return 1;}}

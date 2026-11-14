// Read-only reset-separated lifetime audit of a KMB v2 file.
// An unconditional R/HMR ends a segment. Conditional reset never does.
// Input/output ABI wires [0, scratch_start) remain pinned throughout.
// The reported clique is for this conservative interval model only.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
struct Segment {uint32_t q; uint64_t start,end;};
uint64_t u64(const unsigned char*p){uint64_t v;std::memcpy(&v,p,8);return v;}
uint32_t u32(const unsigned char*p){uint32_t v;std::memcpy(&v,p,4);return v;}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Usage: audit input.kmb scratch_start");
 unsigned scratch=std::stoul(argv[2]);
 int fd=open(argv[1],O_RDONLY);if(fd<0)throw std::runtime_error("open failed");
 struct stat st;if(fstat(fd,&st))throw std::runtime_error("stat failed");
 if(st.st_size<104)throw std::runtime_error("short header");
 auto*p=(unsigned char*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);
 if(p==MAP_FAILED)throw std::runtime_error("mmap failed");
 const unsigned char magic[16]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
 if(std::memcmp(p,magic,16))throw std::runtime_error("bad magic");
 unsigned version=u32(p+16),nq=u32(p+20),nreg=u32(p+28); uint64_t n=u64(p+32);
 if(version!=2||nq<=scratch||nq>100000)throw std::runtime_error("header invalid");
 std::array<const unsigned char*,12> col{};std::array<uint64_t,12> len{};
 uint64_t off=104;
 for(unsigned r=0;r<nreg;r++){if(off+16>(uint64_t)st.st_size||u64(p+off)!=0)throw std::runtime_error("bad register packet");uint64_t size=u64(p+off+8);off+=16;if(size>(uint64_t)st.st_size-off)throw std::runtime_error("short register");off+=size;}
 for(unsigned k=1;k<12;k++){if(off+16>(uint64_t)st.st_size)throw std::runtime_error("short packet");
   uint64_t kind=u64(p+off),size=u64(p+off+8);off+=16;
   if(kind!=k||size>(uint64_t)st.st_size-off)throw std::runtime_error("bad packet");
   col[k]=p+off;len[k]=size;off+=size;}
 if(len[1]!=n)throw std::runtime_error("bad opcodes");
 std::array<uint64_t,4> rank{};
 std::vector<int64_t> start(nq,-1);std::vector<Segment> segments;
 uint64_t depth=0,maxdepth=0,unconditional_resets=0,conditional_resets=0,quantum_ops=0;
 std::vector<uint64_t> touches(nq),resets(nq);
 for(uint64_t i=0;i<n;i++){
   unsigned op=col[1][i],base=op&127,count=(op&48)>>4;
   if(op==0x81){depth++;maxdepth=std::max(depth,maxdepth);}
   if(op==0x01){if(!depth)throw std::runtime_error("unbalanced pop");depth--;}
   if(!count)continue;quantum_ops++;
   unsigned cols[3];if(count==1){cols[0]=7;}else if(count==2){cols[0]=5;cols[1]=6;}else{cols[0]=2;cols[1]=3;cols[2]=4;}
   bool reset=base==0x12||base==0x50;
   bool unconditional=reset&&!(op&128)&&depth==0;
   if(reset){if(unconditional)unconditional_resets++;else conditional_resets++;}
   for(unsigned j=0;j<count;j++){
     if(4*rank[count]+4>len[cols[j]])throw std::runtime_error("operand overflow");
     unsigned q=u32(col[cols[j]]+4*rank[count]);if(q>=nq)throw std::runtime_error("bad qubit");
     if(q<scratch)continue;touches[q]++;
     if(unconditional){resets[q]++;if(start[q]>=0){segments.push_back({q,(uint64_t)start[q],i});start[q]=-1;}}
     else if(start[q]<0)start[q]=i;
   }
   rank[count]++;
 }
 if(depth)throw std::runtime_error("unclosed condition stack");
 for(unsigned q=scratch;q<nq;q++)if(start[q]>=0)segments.push_back({q,(uint64_t)start[q],n});
 struct Event{uint64_t i;int change;size_t seg;};std::vector<Event> events;
 for(size_t k=0;k<segments.size();k++){events.push_back({segments[k].start,1,k});events.push_back({segments[k].end+1,-1,k});}
 std::sort(events.begin(),events.end(),[](auto&a,auto&b){return a.i!=b.i?a.i<b.i:a.change<b.change;});
 std::vector<bool> active(segments.size());unsigned live=0,peak=0;uint64_t peak_at=0;std::vector<size_t>witness;
 for(auto&e:events){active[e.seg]=e.change>0;live+=e.change;if(live>peak){peak=live;peak_at=e.i;witness.clear();for(size_t k=0;k<active.size();k++)if(active[k])witness.push_back(k);}}
 unsigned now=0;uint64_t peak_spans=0,total_peak_duration=0,span_start=0;
 std::vector<std::pair<uint64_t,uint64_t>>spans;
 for(size_t k=0;k<events.size();){auto i=events[k].i;auto old=now;while(k<events.size()&&events[k].i==i)now+=events[k++].change;
  if(old!=peak&&now==peak){span_start=i;peak_spans++;}if(old==peak&&now!=peak){spans.push_back({span_start,i});total_peak_duration+=i-span_start;}}
 std::cout<<"{\n  \"status\":\"COMPLETE_CONSERVATIVE_INTERVAL_AUDIT\",\n  \"num_ops\":"<<n<<",\n  \"num_qubits\":"<<nq<<",\n  \"pinned_ABI_qubits\":"<<scratch<<",\n  \"quantum_ops\":"<<quantum_ops<<",\n  \"interval_count\":"<<segments.size()<<",\n  \"unconditional_resets\":"<<unconditional_resets<<",\n  \"conditional_resets_not_releasing\":"<<conditional_resets<<",\n  \"maximum_condition_depth\":"<<maxdepth<<",\n  \"interval_chromatic_number\":"<<peak<<",\n  \"interval_model_total_qubits\":"<<peak+scratch<<",\n  \"first_peak_kmb_index\":"<<peak_at<<",\n  \"peak_span_count\":"<<peak_spans<<",\n  \"total_peak_span_instructions\":"<<total_peak_duration<<",\n  \"peak_spans\":[";
 for(size_t k=0;k<spans.size();k++)std::cout<<(k?",":"")<<"["<<spans[k].first<<","<<spans[k].second<<"]";
 std::cout<<"],\n  \"peak_witness\":[\n";
 for(size_t k=0;k<witness.size();k++){auto&s=segments[witness[k]];std::cout<<"    {\"q\":"<<s.q<<",\"first_touch\":"<<s.start<<",\"reset_or_exit\":"<<s.end<<"}"<<(k+1<witness.size()?",":"")<<"\n";}
 std::cout<<"  ],\n  \"scope\":\"Exact coloring of conservative reset-separated intervals. Not a lower bound on semantic qubits or on rescheduled/resynthesized circuits. No candidate modified.\"\n}\n";
 munmap(p,st.st_size);close(fd);return 0;
}catch(std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}

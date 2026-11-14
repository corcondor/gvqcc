// Conservative forward constant propagation over the complete KMB v2 tape.
// Quantum ABI wires are arbitrary; other qubits start in zero. Classical bits
// ABI classical bits start unknown; optional remaining storage starts zero.
// Unknown classical controls join the old/new values; PUSH captures its value.
// No phase or measurement is removed. Only Toffoli-like gates are proposed.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
uint64_t r64(const unsigned char*p){uint64_t x;std::memcpy(&x,p,8);return x;}
uint32_t r32(const unsigned char*p){uint32_t x;std::memcpy(&x,p,4);return x;}
int land(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}
int lxor(int a,int b){return a==2||b==2?2:a^b;}
int merged(int old,int next,int enabled){return enabled==0?old:enabled==1?next:old==next?old:2;}
struct Hit{uint64_t index;unsigned op;std::array<unsigned,3> q;std::array<int,3> values;int enabled;};
int main(int argc,char**argv){try{
 if(argc!=3&&argc!=4)throw std::runtime_error("usage: scan circuit.kmb arbitrary_qubits [arbitrary_bits]");
 unsigned abi=std::stoul(argv[2]);int fd=open(argv[1],O_RDONLY);if(fd<0)throw std::runtime_error("open failed");
 struct stat st;if(fstat(fd,&st)||st.st_size<104)throw std::runtime_error("short input");
 auto*p=(unsigned char*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(p==MAP_FAILED)throw std::runtime_error("mmap failed");
 const unsigned char magic[16]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};
 unsigned nq=r32(p+20),nb=r32(p+24),nr=r32(p+28);uint64_t n=r64(p+32),off=104;
 unsigned babi=argc==4?std::stoul(argv[3]):nb;
 if(std::memcmp(p,magic,16)||r32(p+16)!=2||abi>nq||babi>nb||nq>100000||nb>10000000)throw std::runtime_error("bad header");
 std::array<const unsigned char*,12>c{};std::array<uint64_t,12>len{},rank{};
 for(unsigned i=0;i<nr;i++){if(off+16>(uint64_t)st.st_size||r64(p+off)!=0)throw std::runtime_error("bad register");off+=16+r64(p+off+8);}
 for(unsigned k=1;k<12;k++){if(off+16>(uint64_t)st.st_size||r64(p+off)!=k)throw std::runtime_error("bad packet");len[k]=r64(p+off+8);off+=16;if(len[k]>(uint64_t)st.st_size-off)throw std::runtime_error("short packet");c[k]=p+off;off+=len[k];}
 if(len[1]!=n)throw std::runtime_error("bad operation count");
 auto arg=[&](unsigned k){if(4*rank[k]+4>len[k])throw std::runtime_error("operand overflow");return r32(c[k]+4*rank[k]++);};
 std::vector<int>q(nq,0),b(nb,0),stack;std::fill(q.begin(),q.begin()+abi,2);std::fill(b.begin(),b.begin()+babi,2);int active=1;
 std::vector<Hit>hits;uint64_t counted=0;
 for(uint64_t i=0;i<n;i++){
   unsigned op=c[1][i],base=op&127,nqt=(op&48)>>4;std::array<unsigned,3> a{};
   if(nqt==1)a[0]=arg(7);else if(nqt==2){a[0]=arg(5);a[1]=arg(6);}else if(nqt==3){a[0]=arg(2);a[1]=arg(3);a[2]=arg(4);}
   for(unsigned k=0;k<nqt;k++)if(a[k]>=nq)throw std::runtime_error("bad qubit");
   unsigned bit=0,cond=0;if(op&64){bit=arg(8);if(bit>=nb)throw std::runtime_error("bad bit");}
   if(op&128){cond=arg(9);if(cond>=nb)throw std::runtime_error("bad condition");}
   if(op==0x81){stack.push_back(active);active=land(active,b[cond]);continue;}
   if(op==0x01){if(stack.empty())throw std::runtime_error("unbalanced pop");active=stack.back();stack.pop_back();continue;}
   int enabled=(op&128)?land(active,b[cond]):active;
   auto setq=[&](unsigned j,int v){q[a[j]]=merged(q[a[j]],v,enabled);};
   if(nqt==3){counted++;bool hit=enabled==0;
     if(base==0x31)hit|=q[a[0]]!=2||q[a[1]]!=2;
     else if(base==0x30)hit|=q[a[0]]!=2||q[a[1]]!=2||q[a[2]]!=2;
     else if(base==0x32)hit|=q[a[0]]!=2||(q[a[1]]!=2&&q[a[1]]==q[a[2]]);
     if(hit)hits.push_back({i,op,a,{q[a[0]],q[a[1]],q[a[2]]},enabled});
   }
   switch(base){
     case 0x11:setq(0,lxor(q[a[0]],1));break;
     case 0x12:setq(0,0);break;
     case 0x21:setq(1,lxor(q[a[0]],q[a[1]]));break;
     case 0x31:setq(2,lxor(q[a[2]],land(q[a[0]],q[a[1]])));break;
     case 0x22:{int x=q[a[0]],y=q[a[1]];setq(0,y);setq(1,x);break;}
     case 0x32:{int x=q[a[1]],y=q[a[2]],control=q[a[0]];int ex=land(enabled,control);q[a[1]]=merged(x,y,ex);q[a[2]]=merged(y,x,ex);break;}
     case 0x40:b[bit]=merged(b[bit],0,enabled);break;
     case 0x41:b[bit]=merged(b[bit],1,enabled);break;
     case 0x42:b[bit]=merged(b[bit],lxor(b[bit],1),enabled);break;
     case 0x50:setq(0,0);b[bit]=merged(b[bit],2,enabled);break;
     case 0x00:case 0x10:case 0x13:case 0x20:case 0x30:case 0x06:case 0x07:case 0x47:case 0x17:break;
     default:throw std::runtime_error("unsupported opcode");
   }
 }
 if(!stack.empty())throw std::runtime_error("unclosed stack");
 for(unsigned k=2;k<=9;k++)if(rank[k]*4!=len[k])throw std::runtime_error("unconsumed operands");
 std::cout<<"{\"status\":\"COMPLETE\",\"arbitrary_qubits\":"<<abi<<",\"arbitrary_bits\":"<<babi<<",\"instructions\":"<<n<<",\"toffoli_like_scanned\":"<<counted<<",\"hits\":[";
 for(size_t j=0;j<hits.size();j++){auto&h=hits[j];if(j)std::cout<<",";std::cout<<"{\"index\":"<<h.index<<",\"opcode\":"<<h.op<<",\"qubits\":["<<h.q[0]<<","<<h.q[1]<<","<<h.q[2]<<"],\"known_values\":["<<h.values[0]<<","<<h.values[1]<<","<<h.values[2]<<"],\"enabled\":"<<h.enabled<<"}";}
 std::cout<<"],\"hit_count\":"<<hits.size()<<",\"scope\":\"Conservative constant propagation; arbitrary ABI, initially-zero scratch, original measurement and phase operations retained. Candidate requires separate rewrite and verification.\"}\n";
 munmap(p,st.st_size);close(fd);return 0;
}catch(std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}

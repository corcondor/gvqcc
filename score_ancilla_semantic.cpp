// Conservative symbolic computational-value analysis of KMB v2.
// Quantum input registers and classical storage are arbitrary. Scratch starts at 0.
// Values are XORs of abstract Boolean atoms. Products are hash-consed exact
// expressions. Overflow introduces a fresh atom (forgets equalities only).
// Phase gates do not change values; all measurements get fresh classical atoms.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>
using P=std::vector<uint32_t>;
struct VH{size_t operator()(P const&p)const {size_t h=0xcbf29ce484222325ULL;for(auto x:p){h^=x;h*=0x100000001b3ULL;}return h;}};
uint32_t get32(const unsigned char*p){uint32_t x;memcpy(&x,p,4);return x;}
uint64_t get64(const unsigned char*p){uint64_t x;memcpy(&x,p,8);return x;}
struct Algebra{
 uint32_t next=2; uint64_t forgotten=0,products=0; unsigned cap=128;
 std::unordered_map<P,uint32_t,VH> muls;
 P fresh(){return P{next++};}
 P add(P const&a,P const&b){P c;c.reserve(a.size()+b.size());std::set_symmetric_difference(a.begin(),a.end(),b.begin(),b.end(),std::back_inserter(c));if(c.size()>cap){forgotten++;return fresh();}return c;}
 P mul(P const&a,P const&b){if(a.empty()||b.empty())return {};if(a==P{1})return b;if(b==P{1}||a==b)return a;
   P key;if(a<b){key=a;key.push_back(0);key.insert(key.end(),b.begin(),b.end());}else{key=b;key.push_back(0);key.insert(key.end(),a.begin(),a.end());}
   auto it=muls.find(key);if(it!=muls.end())return P{it->second};
   if(muls.size()>1000000)muls.clear(); // Lost equality is conservative.
   auto id=next++;muls.emplace(std::move(key),id);products++;return P{id};}
};
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("Usage: semantic input.kmb scratch_start changes.tsv");
 unsigned scratch=std::stoul(argv[2]);int fd=open(argv[1],O_RDONLY);struct stat st;if(fd<0||fstat(fd,&st))throw std::runtime_error("input failed");
 auto*p=(unsigned char*)mmap(nullptr,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);if(p==MAP_FAILED)throw std::runtime_error("mmap failed");
 unsigned version=get32(p+16),nq=get32(p+20),nb=get32(p+24),nr=get32(p+28);uint64_t n=get64(p+32),off=104;
 if(version!=2||scratch>=nq)throw std::runtime_error("bad header");
 std::array<const unsigned char*,12>col{};std::array<uint64_t,12>len{};
 for(unsigned r=0;r<nr;r++){if(get64(p+off)!=0)throw std::runtime_error("bad register");off+=16+get64(p+off+8);}
 for(unsigned k=1;k<12;k++){auto kind=get64(p+off),size=get64(p+off+8);off+=16;if(kind!=k||off+size>(uint64_t)st.st_size)throw std::runtime_error("bad columns");col[k]=p+off;len[k]=size;off+=size;}
 if(len[1]!=n)throw std::runtime_error("bad ops");
 Algebra alg;std::vector<P>q(nq),bits(nb);for(unsigned j=0;j<scratch;j++)q[j]=alg.fresh();for(auto&b:bits)b=alg.fresh();
 std::array<uint64_t,4>rank{};uint64_t rankbit=0,rankcond=0;std::vector<P>stack;P effective{1};
 unsigned live=0,peak=0;uint64_t peak_at=0,clean_transitions=0,toffoli_zero=0,toffoli_one=0,inactive_toffoli=0;
 std::map<unsigned,uint64_t>removed_by_opcode,changed_by_opcode;std::ofstream changes(argv[3]);
 auto assign=[&](unsigned wire,P value){if(wire>=scratch){live-=!q[wire].empty();live+=!value.empty();if(!q[wire].empty()&&value.empty())clean_transitions++;}q[wire]=std::move(value);};
 auto conditional_assign=[&](unsigned wire,P const&value,P const&condition){assign(wire,alg.add(q[wire],alg.mul(condition,alg.add(q[wire],value))));};
 for(uint64_t i=0;i<n;i++){
   unsigned op=col[1][i],base=op&127,count=(op&48)>>4;unsigned wires[3]={};unsigned cols[3];
   if(count==1)cols[0]=7;else if(count==2){cols[0]=5;cols[1]=6;}else if(count==3){cols[0]=2;cols[1]=3;cols[2]=4;}
   for(unsigned j=0;j<count;j++)wires[j]=get32(col[cols[j]]+4*rank[count]);if(count)rank[count]++;
   unsigned bit=0,conditionbit=0;if(op&64)bit=get32(col[8]+4*rankbit++);if(op&128)conditionbit=get32(col[9]+4*rankcond++);
   P condition=effective;if(op&128)condition=alg.mul(condition,bits[conditionbit]);
   if(op==0x81){stack.push_back(effective);effective=std::move(condition);continue;}
   if(op==0x01){if(stack.empty())throw std::runtime_error("condition underflow");effective=stack.back();stack.pop_back();continue;}
   bool inactive=condition.empty();
   if(base==0x40||base==0x41||base==0x42){P value=base==0x40?P{}:base==0x41?P{1}:alg.add(bits[bit],P{1});bits[bit]=alg.add(bits[bit],alg.mul(condition,alg.add(bits[bit],value)));}
   else if(base==0x50){P measured=alg.fresh();bits[bit]=alg.add(bits[bit],alg.mul(condition,alg.add(bits[bit],measured)));conditional_assign(wires[0],{},condition);}
   else if(base==0x12)conditional_assign(wires[0],{},condition);
   else if(base==0x11)assign(wires[0],alg.add(q[wires[0]],condition));
   else if(base==0x21)assign(wires[1],alg.add(q[wires[1]],alg.mul(condition,q[wires[0]])));
   else if(base==0x22){P d=alg.mul(condition,alg.add(q[wires[0]],q[wires[1]]));P a=alg.add(q[wires[0]],d),b=alg.add(q[wires[1]],d);assign(wires[0],a);assign(wires[1],b);}
   else if(base==0x31){
      if(inactive){inactive_toffoli++;changes<<i<<"\t0\tinactive\n";}
      else if(q[wires[0]].empty()||q[wires[1]].empty()){toffoli_zero++;changes<<i<<"\t0\tzero_control\n";}
      else if(q[wires[0]]==P{1}||q[wires[1]]==P{1}){toffoli_one++;unsigned control=q[wires[0]]==P{1}?wires[1]:wires[0];changes<<i<<"\t"<<(unsigned)(0x21|(op&128))<<"\tone_control\t"<<control<<"\t"<<wires[2]<<"\n";}
      assign(wires[2],alg.add(q[wires[2]],alg.mul(condition,alg.mul(q[wires[0]],q[wires[1]]))));
   }else if(base==0x32){
      if(inactive){inactive_toffoli++;changes<<i<<"\t0\tinactive\n";}
      else if(q[wires[0]].empty()||q[wires[1]]==q[wires[2]]){toffoli_zero++;changes<<i<<"\t0\ttrivial_cswap\n";}
      else if(q[wires[0]]==P{1}){toffoli_one++;changes<<i<<"\t"<<(unsigned)(0x22|(op&128))<<"\tone_control\t"<<wires[1]<<"\t"<<wires[2]<<"\n";}
      P d=alg.mul(condition,alg.mul(q[wires[0]],alg.add(q[wires[1]],q[wires[2]])));P a=alg.add(q[wires[1]],d),b=alg.add(q[wires[2]],d);assign(wires[1],a);assign(wires[2],b);
   }else if(base==0x30){
      if(inactive){inactive_toffoli++;changes<<i<<"\t0\tinactive\n";}
      else if(q[wires[0]].empty()||q[wires[1]].empty()||q[wires[2]].empty()){toffoli_zero++;changes<<i<<"\t0\tzero_ccz\n";}
      else if(q[wires[0]]==P{1}||q[wires[1]]==P{1}||q[wires[2]]==P{1}){toffoli_one++;unsigned omit=q[wires[0]]==P{1}?0:q[wires[1]]==P{1}?1:2;changes<<i<<"\t"<<(unsigned)(0x20|(op&128))<<"\tone_ccz";for(unsigned j=0;j<3;j++)if(j!=omit)changes<<"\t"<<wires[j];changes<<"\n";}
   }else if(base!=0&&base!=0x10&&base!=0x13&&base!=0x20&&base!=0x06&&base!=0x07&&base!=0x17&&base!=0x47)throw std::runtime_error("unhandled opcode "+std::to_string(op));
   if(live>peak){peak=live;peak_at=i;}
   if(i%5000000==0)std::cerr<<i<<"/"<<n<<" live="<<live<<" peak="<<peak<<" atoms="<<alg.next<<"\n";
 }
 if(!stack.empty())throw std::runtime_error("unclosed condition");
 std::cout<<"{\"status\":\"COMPLETE_CONSERVATIVE_SYMBOLIC_VALUES\",\"operations\":"<<n<<",\"scratch_peak_nonzero_bound\":"<<peak<<",\"first_peak_at\":"<<peak_at<<",\"clean_transitions\":"<<clean_transitions<<",\"toffoli_zero\":"<<toffoli_zero<<",\"toffoli_one\":"<<toffoli_one<<",\"inactive_toffoli\":"<<inactive_toffoli<<",\"abstract_atoms\":"<<alg.next<<",\"overflow_forgetting\":"<<alg.forgotten<<",\"final_scratch_nonzero_bound\":"<<live<<"}\n";
 munmap(p,st.st_size);close(fd);return 0;
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}

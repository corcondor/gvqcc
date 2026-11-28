// Whole-tape exact motif substitution; arbitrary dirty targets, no clean-state assumption.
#include "../dqi_whole_root_frame/native.hpp"
#include <deque>
struct Local{int op,a,b,t;};
#include "gate_tables.hpp"
template<size_t N,size_t M>
bool replace_block(const deque<Gate>& buf, const Local (&pattern)[N],const Local (&replacement)[M], Writer& w, U Q){
 if(buf.size()<N||buf.front().op!=49)return false;
 int map[14];fill(map,map+14,-1);set<U> used;
 auto bind=[&](int i,U v){if(v>=Q)return false;if(map[i]>=0)return map[i]==(int)v;if(!used.insert(v).second)return false;map[i]=v;return true;};
 for(size_t i=0;i<N;i++){
  const auto &g=buf[i];const auto &p=pattern[i];
  if(g.op!=p.op||g.bit||g.cond)return false;
  if(!bind(p.a,g.a)||!bind(p.b,g.b))return false;
  if(p.op==49&&!bind(p.t,g.t))return false;
 }
 if(used.size()!=14)return false;
 for(auto p:replacement){
  Gate g{(unsigned char)p.op,(U)map[p.a],(U)map[p.b],p.op==49?(U)map[p.t]:0};
  w.put(g);
 }
 return true;
}
int main(int argc,char**argv){
 if(argc!=4)return 2;Reader r(argv[1]);Writer w(r,r.B);deque<Gate> buf;
 ofstream sites(argv[3]);L pos=0,raw=0,flat=0,oldOps=0,newOps=0,paidOld=0,paidNew=0;
 auto paid=[](Gate g){int k=g.op&127;return k==48||k==49||k==50;};
 auto consume=[&](bool tail){
  while(buf.size()>=100||(tail&&!buf.empty())){
   size_t take=0;
   if(replace_block(buf,raw_pattern,raw_replacement,w,r.Q)){take=100;raw++;oldOps+=100;newOps+=64;paidNew+=3;sites<<pos<<" raw 100 64\n";}
   else if(replace_block(buf,flat_pattern,flat_replacement,w,r.Q)){take=74;flat++;oldOps+=74;newOps+=64;paidNew+=3;sites<<pos<<" flat 74 64\n";}
   else {take=1;w.put(buf.front());paidNew+=paid(buf.front());}
   for(size_t j=0;j<take;j++){paidOld+=paid(buf.front());buf.pop_front();}pos+=take;
  }
 };
 for(L i=0;i<r.counts[0];i++){buf.push_back(r.read(i));if(buf.size()>=100)consume(false);}
 consume(true);assert(pos==r.counts[0]&&paidOld==paidNew&&w.ops.size()==r.counts[0]-oldOps+newOps);
 w.write(argv[2]);cout<<"{\"Q\":"<<r.Q<<",\"old_ops\":"<<r.counts[0]<<",\"new_ops\":"<<w.ops.size()<<",\"raw_sites\":"<<raw<<",\"flat_sites\":"<<flat<<",\"old_paid\":"<<paidOld<<",\"new_paid\":"<<paidNew<<"}\n";
}

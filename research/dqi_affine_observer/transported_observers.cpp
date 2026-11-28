// Exact rank-one state-difference / observer transport. No sampling in synthesis.
// Candidate input is a full serialized KMB, including the exact 8-anchor tape.
// Do not infer correctness of its original decoder from a successful rewrite.
#include "../dqi_whole_root_frame/native.hpp"
#include <bitset>
#include <optional>
#include <deque>
using B=bitset<1024>;
using Mon=vector<U>;
using Poly=set<Mon>;
static U Q;
static constexpr size_t H=32768;
static L tries=0,walked=0,hmr_hits=0,pair_hits=0,cuts=0,saved=0,paid_add=0;
void toggle(Poly &p,Mon m){sort(m.begin(),m.end());m.erase(unique(m.begin(),m.end()),m.end());auto it=p.find(m);if(it==p.end())p.insert(move(m));else p.erase(it);}
Poly product(B a,B b){
 Poly p;
 for(size_t i=a._Find_first();i<a.size();i=a._Find_next(i))
 for(size_t j=b._Find_first();j<b.size();j=b._Find_next(j)){
  Mon m;if(i<Q)m.push_back(i);if(j<Q)m.push_back(j);toggle(p,m);
 }
 return p;
}
bool add_observer(const Poly&p,const vector<U>&w,const B&d,U cond,bool guarded,vector<Gate>&out,U&paid){
 Poly v;
 // XOR of all nonempty affected subsets. p^k=p in Boolean algebra.
 for(unsigned m=1;m<(1u<<w.size());m++){
  bool active=true;Mon remain;
  for(size_t j=0;j<w.size();j++)if(m>>j&1){if(!d[w[j]])active=false;}else remain.push_back(w[j]);
  if(!active)continue;
  for(auto z:p){z.insert(z.end(),remain.begin(),remain.end());toggle(v,move(z));}
 }
 for(auto z:v){
  if(z.size()>3)return false;
  Gate g{};g.op=static_cast<unsigned char>((z.size()<<4)|(guarded?128:0));g.cond=cond;
  if(z.size()>0)g.a=z[0];if(z.size()>1)g.b=z[1];if(z.size()>2){g.t=z[2];paid++;}
  out.push_back(g);
 }
 return paid<=1&&out.size()<=256;
}
B unit(U i){B b;b.set(i);return b;}
struct Result{
 size_t end=0;bool pair=false;U add=0;map<size_t,vector<Gate>> debt;
};
optional<Result> find_cut(const vector<Gate>&v,size_t i){
 const Gate s=v[i];if(s.op!=0x31)return {};
 assert(s.a<Q&&s.b<Q&&s.t<Q&&s.a!=s.b&&s.a!=s.t&&s.b!=s.t);
 tries++;B a=unit(s.a),b=unit(s.b),d=unit(s.t);Result result;
 auto need=[&](U x){return a[x]||b[x];};
 auto parity_safe=[&](){return ((a&d).count()%2)==0&&((b&d).count()%2)==0;};
 auto cert=[&](size_t end,bool pair)->optional<Result>{
   if(!parity_safe())throw runtime_error("invalid covector/direction invariant");
   if(result.add>=1u+unsigned(pair))return {};
   result.end=end;result.pair=pair;return result;
 };
 for(size_t j=i+1;j<v.size()&&j<=i+H;j++){
  walked++;const auto g=v[j];int op=g.op&127;bool guard=g.op&128;
  U x=g.a,y=g.b,z=g.t;
  if(g.op==129||op==1)break; // never cross enclosing scope transition
  switch(op){
   case 0:case 64:case 65:case 66:break;
   case 0x11:
    if(guard&&need(x))return {};
    if(!guard){if(a[x])a.flip(Q);if(b[x])b.flip(Q);}break;
   case 0x21:
    if(guard&&(d[x]||need(y)))return {};
    if(!guard){if(d[x])d.flip(y);if(a[y])a.flip(x);if(b[y])b.flip(x);}break;
   case 0x22:
    if(guard&&(d[x]!=d[y]||a[x]!=a[y]||b[x]!=b[y]))return {};
    if(!guard){if(d[x]!=d[y]){d.flip(x);d.flip(y);}if(a[x]!=a[y]){a.flip(x);a.flip(y);}if(b[x]!=b[y]){b.flip(x);b.flip(y);}}break;
   case 0x31:{
    if(d[x]||d[y])return {};
    // Equal product in current frame, with the propagated target direction.
    if(!guard&&d.count()==1&&d[z]&&a.count()*b.count()<=64&&
       product(a,b)==product(unit(x),unit(y)))return cert(j,true);
    if(need(z))return {};break;
   }
   case 0x32:
    if(d[x]||d[y]||d[z]||need(y)||need(z))return {};break;
   case 0x12:
    if(d[x]||need(x))return {};break;
   case 0x50:{
    if(need(x))return {};
    if(!d[x])break;
    if(guard||a.count()*b.count()>64)return {};
    // Original HMR random outcome is retained. Repay exactly its p*m debt.
    vector<Gate> h;
    if(!add_observer(product(a,b),{x},d,g.bit,true,h,result.add))return {};
    result.debt[j]=move(h);d.reset(x);
    if(d.none())return cert(j,false);break;
   }
   case 0x10:case 0x20:case 0x30:{
    vector<U> w{x};if(op>=0x20)w.push_back(y);if(op==0x30)w.push_back(z);
    bool affected=false;for(U u:w)affected|=d[u];
    if(!affected)break;
    if(a.count()*b.count()>64)return {};
    vector<Gate> h;
    if(!add_observer(product(a,b),w,d,g.cond,guard,h,result.add))return {};
    result.debt[j]=move(h);break;
   }
   default:return {};
  }
  if(!parity_safe())throw runtime_error("invariant violated during transport");
 }
 return {};
}
L paid(const Gate&g){int b=g.op&127;return b==0x31||b==0x30||b==0x32;}
int main(int ac,char**av){
 if(ac!=3){cerr<<"usage: transported_observers in.kmb out.kmb\n";return 2;}
 if(string(av[1])==av[2])return 3;
 Reader r(av[1]);Q=r.Q;if(Q>=1024)throw runtime_error("unsupported width");
 Writer w(r,r.B);vector<Gate> v;v.reserve(2*H+2);L next=0,offset=0,oldpaid=0,newpaid=0,oldccx=0,newccx=0;
 ofstream report(string(av[2])+".tsv");
 auto put=[&](Gate g){w.put(g);newpaid+=paid(g);newccx+=(g.op&127)==0x31;};
 auto fillbuf=[&](){while(v.size()<2*H+1&&next<r.counts[0]){Gate g=r.read(next++);v.push_back(g);oldpaid+=paid(g);oldccx+=(g.op&127)==0x31;}};
 while(next<r.counts[0]||!v.empty()){
  fillbuf();size_t limit=next==r.counts[0]?v.size():H;size_t i=0;
  while(i<limit){
   auto z=find_cut(v,i);
   if(!z){put(v[i++]);continue;}
   assert(z->end>i);
   L gain=1+z->pair-z->add;cuts++;saved+=gain;paid_add+=z->add;
   if(z->pair)pair_hits++;else hmr_hits++;
   report<<offset+i<<'\t'<<offset+z->end<<'\t'<<z->pair<<'\t'<<z->add<<'\t'<<gain<<"\n";
   for(size_t j=i+1;j<=z->end;j++){
    if(!(z->pair&&j==z->end))put(v[j]);
    auto it=z->debt.find(j);if(it!=z->debt.end())for(auto h:it->second)put(h);
   }
   i=z->end+1;
  }
  offset+=i;v.erase(v.begin(),v.begin()+i);
 }
 assert(offset==r.counts[0]&&oldpaid==newpaid+saved);
 w.write(av[2]);
 cout<<"{\"Q\":"<<Q<<",\"attempts\":"<<tries<<",\"steps\":"<<walked<<",\"cuts\":"<<cuts<<",\"hmr_cuts\":"<<hmr_hits<<",\"paired_cuts\":"<<pair_hits<<",\"new_CCZ\":"<<paid_add<<",\"old_ccx\":"<<oldccx<<",\"new_ccx\":"<<newccx<<",\"old_paid\":"<<oldpaid<<",\"new_paid\":"<<newpaid<<",\"old_ops\":"<<r.counts[0]<<",\"new_ops\":"<<w.ops.size()<<"}\n";
}

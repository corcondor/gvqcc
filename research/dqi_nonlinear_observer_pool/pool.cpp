// Transport and pool cubic phases across affine/nonlinear/HMR barriers
// only when exact independence or an exhaustive local Boolean identity proves
// commutation. Synthesis uses no test inputs, masks, salt, or shot statistics.
#include "native.hpp"
using V=bitset<900>;
struct Form{V v;bool c=false;};
V unit(U i){V a;a.set(i);return a;}
int op(Gate g){return g.op&127;}
bool cond(Gate g){return g.op&128;}
bool dot(V a,V b){return (a&b).count()&1;}
struct Basis{
 vector<V> rows,es;vector<unsigned> codes;vector<U> piv;
 unsigned add(V v){V z=v;unsigned h=0;
 for(int j=0;j<(int)es.size();j++)if(z[piv[j]]){z^=es[j];h^=codes[j];}
 if(z.none())return h;assert(rows.size()<24);unsigned w=1u<<rows.size();
 rows.push_back(v);es.push_back(z);codes.push_back(h^w);piv.push_back(z._Find_first());return w;}
 unsigned get(V z)const{unsigned h=0;for(int j=0;j<(int)es.size();j++)if(z[piv[j]]){z^=es[j];h^=codes[j];}assert(z.none());return h;}
};
bool lessv(const V&a,const V&b){for(int i=899;i>=0;i--)if(a[i]!=b[i])return !a[i];return false;}
vector<V> span(array<Form,3> f){vector<V> a;for(int m=1;m<8;m++){V z;for(int k=0;k<3;k++)if(m>>k&1)z^=f[k].v;a.push_back(z);}sort(a.begin(),a.end(),lessv);assert(a.front().any()&&unique(a.begin(),a.end())==a.end());return a;}
void push_form(Form &f,Gate g){
 if(op(g)==17)f.c^=f.v[g.a];
 else if(op(g)==33){if(f.v[g.b])f.v.flip(g.a);}
 else if(op(g)==34){bool a=f.v[g.a],b=f.v[g.b];f.v[g.a]=b;f.v[g.b]=a;}
 else abort();
}
struct P{size_t at;Gate gate;array<Form,3> f;};
bool independent(P const&p,U q){for(auto f:p.f)if(f.v[q])return false;return true;}
bool invariant(P const&p,Gate g){
 int k=op(g);
 if(k==17||k==33||k==49){
   U t=k==17?g.a:k==33?g.b:g.t;
   if(independent(p,t))return true;
   Basis b;array<unsigned,3> f;
   for(int i=0;i<3;i++)f[i]=b.add(p.f[i].v);
   unsigned a=k==17?0:b.add(unit(g.a)),c=k==49?b.add(unit(g.b)):0;
   for(unsigned x=0;x<(1u<<b.rows.size());x++){
     bool delta=k==17?true:k==33?__builtin_parity(x&a):(__builtin_parity(x&a)&&__builtin_parity(x&c));
     bool v=true,w=true;for(int i=0;i<3;i++){bool z=__builtin_parity(x&f[i])^p.f[i].c;v&=z;w&=z^(delta&&p.f[i].v[t]);}if(v!=w)return false;
   }return true;
 }
 if(k==34||k==50){
   U a=k==34?g.a:g.b,b=k==34?g.b:g.t;
   if(all_of(p.f.begin(),p.f.end(),[&](Form x){return x.v[a]==x.v[b];}))return true;
   return false;
 }
 if(k==80||k==18)return independent(p,g.a);
 return false;
}
Gate xg(int o,U a=0,U b=0,U t=0){Gate h{};h.op=o;h.a=a;h.b=b;h.t=t;return h;}
Gate cg(int o,U a,U b,U t,U c){Gate h=xg(o|128,a,b,t);h.cond=c;return h;}
Gate bs(U b,bool v=false){Gate h{};h.op=v?65:64;h.bit=b;return h;}
Gate bc(U b,U c){Gate h{};h.op=194;h.bit=b;h.cond=c;return h;}
Gate push(U c){Gate h{};h.op=129;h.cond=c;return h;}
Gate pop(){return xg(1);}
struct Frame{vector<U> piv;vector<Gate> pre;};
Frame frame(Basis const&b){
 vector<V> rows=b.rows;vector<pair<int,int>> undo;vector<U> p;V used;
 for(int i=0;i<(int)rows.size();i++){int col=-1,j=-1;
  for(int k=0;k<900&&col<0;k++)if(!used[k])for(int l=i;l<(int)rows.size();l++)if(rows[l][k]){col=k;j=l;break;}
  assert(col>=0);p.push_back(col);used.set(col);
  if(j!=i){swap(rows[j],rows[i]);undo.push_back({j,i});undo.push_back({i,j});undo.push_back({j,i});}
  for(int k=0;k<(int)rows.size();k++)if(k!=i&&rows[k][col]){rows[k]^=rows[i];undo.push_back({i,k});}
 }
 vector<Gate> gates;
 for(int i=0;i<(int)p.size();i++){for(int j=0;j<(int)p.size();j++)assert(rows[i][p[j]]==(i==j));for(U k=rows[i]._Find_first();k<900;k=rows[i]._Find_next(k))if(k!=p[i])gates.push_back(xg(33,k,p[i]));}
 for(auto it=undo.rbegin();it!=undo.rend();++it)gates.push_back(xg(33,p[it->first],p[it->second]));
 vector<V> test(900);for(int i=0;i<900;i++)test[i]=unit(i);for(auto g:gates)test[g.b]^=test[g.a];
 for(int i=0;i<(int)p.size();i++)assert(test[p[i]]==b.rows[i]);return {p,gates};
}
struct Group{vector<int> ids;V u,v;};
using Key=pair<string,string>;
vector<Group> choose(vector<P>const& ps){
 map<Key,Group> groups;
 for(int i=0;i<(int)ps.size();i++){
  auto s=span(ps[i].f);
  for(int a=0;a<7;a++)for(int b=a+1;b<7;b++){V w=s[a]^s[b];if(!lessv(s[b],w))continue;
    Key key{s[a].to_string(),s[b].to_string()};auto &g=groups[key];g.u=s[a];g.v=s[b];g.ids.push_back(i);}
 }
 vector<Group> cand;for(auto&[k,g]:groups)if(g.ids.size()>1)cand.push_back(move(g));
 sort(cand.begin(),cand.end(),[](auto&a,auto&b){return a.ids.size()>b.ids.size();});
 vector<bool> used(ps.size());vector<Group> out;
 for(auto g:cand){vector<int> v;for(int i:g.ids)if(!used[i])v.push_back(i);if(v.size()<2)continue;
  for(int st=0;st<(int)v.size();st+=8){int en=min(st+8,(int)v.size());if(en-st<2)break;Group q{vector<int>(v.begin()+st,v.begin()+en),g.u,g.v};for(int i:q.ids)used[i]=true;out.push_back(move(q));}
 }return out;
}
static L groupCount=0,removed=0,saved=0,terms=0,phaseChecks=0,crossedHMR=0,crossedCCX=0;
vector<Gate> lower(Group const& g,vector<P>const& ps,U base){
 Basis b;b.add(g.u);b.add(g.v);
 vector<V> ws;
 for(int id:g.ids){auto s=span(ps[id].f);V w;for(auto z:s)if(z!=g.u&&z!=g.v&&z!=(g.u^g.v)){w=z;break;}assert(w.any());ws.push_back(w);b.add(w);}
 int d=b.rows.size();assert(d>=3&&d<=10);auto f=frame(b);auto &q=f.piv;vector<Gate> r=f.pre;
 // Original phase expressed in common frame; replace cubic part by u*v*w
 // and explicitly repay its affine and quadratic difference.
 vector<unsigned> wcoords;vector<unsigned> residuals;
 auto phase=[&](int id,int k,U a,U c=0){
   const auto &p=ps[id];
   if(cond(p.gate))r.push_back(cg(k,a,c,0,base+id));else r.push_back(xg(k,a,c));
 };
 for(int s=0;s<(int)g.ids.size();s++){
  int id=g.ids[s];auto p=ps[id];array<unsigned,3>A;
  for(int j=0;j<3;j++)A[j]=b.get(p.f[j].v);
  unsigned w=b.get(ws[s])&~3u;assert(w);wcoords.push_back(w);
  vector<unsigned char> v(1u<<d);
  for(unsigned x=0;x<v.size();x++){
    bool a=true;for(int j=0;j<3;j++)a&=__builtin_parity(x&A[j])^p.f[j].c;
    v[x]=a^((x&3)==3&&__builtin_parity(x&w));phaseChecks++;
  }
  for(int j=0;j<d;j++)for(unsigned x=0;x<v.size();x++)if(x>>j&1)v[x]^=v[x^(1u<<j)];
  for(unsigned x=0;x<v.size();x++)if(v[x]){
   int n=__builtin_popcount(x);assert(n<=2);
   if(!x){r.push_back(xg(17,q[0]));phase(id,16,q[0]);r.push_back(xg(17,q[0]));phase(id,16,q[0]);}
   else if(n==1)phase(id,16,q[__builtin_ctz(x)]);
   else {int a=__builtin_ctz(x),c=__builtin_ctz(x^(1u<<a));phase(id,32,q[a],q[c]);}
  }
 }
 // Accumulate active third forms into classical coefficients.
 U cbase=base+128,choice=base+144;
 for(int j=2;j<d;j++)r.push_back(bs(cbase+j));
 for(int s=0;s<(int)g.ids.size();s++)for(int j=2;j<d;j++)if(wcoords[s]>>j&1){
   int id=g.ids[s];if(cond(ps[id].gate))r.push_back(bc(cbase+j,base+id));else {Gate h{};h.op=66;h.bit=cbase+j;r.push_back(h);}
 }
 // Dynamic selected parity, same algorithm as narrow_field130, but the
 // coefficients can be XORs of multiple independently measured guards.
 for(int j=3;j<d;j++){
   r.push_back(bs(choice+j));r.push_back(bc(choice+j,cbase+j));
   r.push_back(push(choice+j));r.push_back(xg(34,q[2],q[j]));r.push_back(bs(cbase+j));r.push_back(bc(cbase+j,cbase+2));r.push_back(bs(cbase+2,true));r.push_back(pop());
 }
 for(int j=3;j<d;j++)r.push_back(cg(33,q[j],q[2],0,cbase+j));
 r.push_back(cg(48,q[0],q[1],q[2],cbase+2));
 for(int j=d-1;j>=3;j--)r.push_back(cg(33,q[j],q[2],0,cbase+j));
 for(int j=d-1;j>=3;j--)r.push_back(cg(34,q[2],q[j],0,choice+j));
 for(int j=2;j<d;j++)r.push_back(bs(cbase+j));
 for(int j=3;j<d;j++)r.push_back(bs(choice+j));
 // Independent exhaustive verification of the dynamic parity selector.
 for(unsigned c=0;c<(1u<<(d-2));c++)for(unsigned x=0;x<(1u<<(d-2));x++){
   unsigned C=c,X=x,sel=0;
   for(int j=1;j<d-2;j++)if(C>>j&1){sel|=1u<<j;bool a=C&1,b=X&1,z=X>>j&1;C=(C&~(1u<<j))|((unsigned)a<<j)|1u;X=(X&~((1u<<j)|1u))|((unsigned)b<<j)|z;}
   unsigned p=__builtin_parity(X&(C&~1u));X^=p;
   assert(((C&X&1)!=0)==bool(__builtin_parity(c&x)));
   X^=p;for(int j=d-3;j>=1;j--)if(sel>>j&1){bool a=X&1,b=X>>j&1;X=(X&~((1u<<j)|1u))|((unsigned)a<<j)|b;}
   assert(X==x);phaseChecks++;
 }
 r.insert(r.end(),f.pre.rbegin(),f.pre.rend());
 return r;
}
int main(int argc,char**argv){
 assert(argc==3);Reader r(argv[1]);assert(r.Q==900);Writer w(r,r.B+170);
 vector<Gate> buf;vector<P> pending;L oldPaid=0,newPaid=0;map<int,L> sizes;
 auto emit=[&](Gate g){w.put(g);if(op(g)==48||op(g)==49||op(g)==50)newPaid++;};
 auto flush=[&](){
   if(buf.empty()){assert(pending.empty());return;}
   auto groups=choose(pending);map<size_t,int> mark;vector<vector<Gate>> synth;
   for(auto&g:groups){auto z=lower(g,pending,r.B);groupCount++;removed+=g.ids.size();saved+=g.ids.size()-1;sizes[g.ids.size()]++;for(int id:g.ids)mark[pending[id].at]=id;synth.push_back(move(z));}
   for(size_t i=0;i<buf.size();i++){
     auto it=mark.find(i);if(it==mark.end())emit(buf[i]);
     else {auto p=pending[it->second];if(cond(p.gate)){emit(bs(r.B+it->second));emit(bc(r.B+it->second,p.gate.cond));}}
   }
   for(auto z:synth)for(auto h:z)emit(h);
   for(auto [i,id]:mark)if(cond(pending[id].gate))emit(bs(r.B+id));
   buf.clear();pending.clear();
 };
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int k=op(g);if(k==48||k==49||k==50)oldPaid++;
  if(k==48){
    if(pending.size()>=64||buf.size()>=32768)flush();
    P p{buf.size(),g,{{{unit(g.a),false},{unit(g.b),false},{unit(g.t),false}}}};
    if(g.a==g.b||g.a==g.t||g.b==g.t){flush();emit(g);continue;}
    pending.push_back(p);buf.push_back(g);terms++;continue;
  }
  if(pending.empty()){assert(buf.empty());emit(g);continue;}
  bool affine=!cond(g)&&(k==17||k==33||k==34);
  bool safe=k==16||k==32||k==64||k==65||k==66;
  // Classical stores, diagonal phases commute; original guards will be
  // snapshotted at the old phase location. Scopes are strict boundaries.
  if(affine){for(auto&p:pending)for(auto&f:p.f)push_form(f,g);safe=true;}
  else if(k==17||k==33||k==34||k==49||k==50||k==80||k==18){
    safe=all_of(pending.begin(),pending.end(),[&](P const&p){return invariant(p,g);});
    if(safe){if(k==80)crossedHMR++;if(k==49)crossedCCX++;}
  }
  if(!safe){flush();emit(g);continue;}
  buf.push_back(g);if(buf.size()>=32768)flush();
 }
 flush();assert(oldPaid-newPaid==saved);cerr<<"{\"Q\":"<<r.Q<<",\"old_paid\":"<<oldPaid<<",\"new_paid\":"<<newPaid<<",\"ccz_seen\":"<<terms<<",\"groups\":"<<groupCount<<",\"old_group_terms\":"<<removed<<",\"saved\":"<<saved<<",\"crossed_HMR\":"<<crossedHMR<<",\"crossed_CCX\":"<<crossedCCX<<",\"phase_checks\":"<<phaseChecks<<",\"old_ops\":"<<r.counts[0]<<",\"new_ops\":"<<w.ops.size()<<"}\n";
 for(auto [n,c]:sizes)cerr<<"GROUP "<<n<<" "<<c<<"\n";
 if(saved)w.write(argv[2]);else {cerr<<"NO_PAID_IMPROVEMENT\n";return 3;}
}

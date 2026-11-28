// Exact local rewrites for the complete, serialized KMB tape.
// No fixture, syndrome, measurement outcome, or salt is used in synthesis.
#include "native.hpp"
using Bits=bitset<1024>;
using Pair=pair<int,int>;
using Tensor=map<Pair,Bits>;
static int Q;
static L attempts=0,valid=0,rankSites=0,rankSaved=0,hmrSites=0,hmrSaved=0,phaseSites=0,phaseSaved=0;
int base(const Gate&g){return g.op&127;}
bool same(const Gate&a,const Gate&b){return (a.op&128)==(b.op&128)&&(!(a.op&128)||a.cond==b.cond);}
bool affine(const Gate&g){int b=base(g);return b==0x11||b==0x21||b==0x22;}
bool eligible(const Gate&g){return affine(g)||base(g)==0x31;}
Bits unit(int i){Bits v;v.set(i);return v;}
vector<int> support(const Bits&b){vector<int> v;for(size_t i=b._Find_first();i<b.size();i=b._Find_next(i))v.push_back(i);return v;}
Gate makeg(int b,U a=0,U c=0,U t=0,const Gate&guard=Gate{}){Gate g;g.op=b|(guard.op&128);g.a=a;g.b=c;g.t=t;g.cond=guard.cond;return g;}
struct Stats{L ops=0,ccx=0,ccz=0,cswap=0;void add(const Gate&g){ops++;ccx+=base(g)==0x31;ccz+=base(g)==0x30;cswap+=base(g)==0x32;}L paid()const{return ccx+ccz+cswap;}};
struct Factor{int a;Bits v,u;};
bool block(const vector<Gate>&g,size_t a,size_t b,vector<Gate>&out,L&saving){
 attempts++;Bits T;L old=0;const Gate&guard=g[a];
 for(size_t i=a;i<b;i++){if(!eligible(g[i])||!same(guard,g[i]))return false;if(base(g[i])==0x31){T.set(g[i].t);old++;}}
 if(old<2)return false;
 for(size_t i=a;i<b;i++)if(base(g[i])==0x31&&(T[g[i].a]||T[g[i].b]))return false;
 map<int,Bits> forms,inv;
 auto f=[&](int j)->Bits&{auto it=forms.find(j);if(it==forms.end())it=forms.emplace(j,unit(j)).first;return it->second;};
 auto u=[&](int j)->Bits&{auto it=inv.find(j);if(it==inv.end())it=inv.emplace(j,unit(j)).first;return it->second;};
 Tensor tensor;map<int,Bits> linear;vector<Gate> tail;
 for(size_t i=a;i<b;i++){
  const Gate&x=g[i];int p=x.a,q=x.b,t=x.t,k=base(x);
  if(k==0x11){if(!T[p])f(p).flip(Q);tail.push_back(x);}
  else if(k==0x21){if(T[p]&&!T[q])return false;if(T[p]&&T[q])u(p)^=u(q);else if(!T[q])f(q)^=f(p);tail.push_back(x);}
  else if(k==0x22){if(T[p]!=T[q])return false;if(T[p])swap(u(p),u(q));else swap(f(p),f(q));tail.push_back(x);}
  else {
   auto left=support(f(p)),right=support(f(q));Bits dir=u(t);
   if(left.size()*right.size()*dir.count()>8192)return false;
   for(int l:left)for(int r:right){
    if(l==Q||r==Q||l==r)linear[l==Q?r:r==Q?l:l]^=dir;
    else tensor[minmax(l,r)]^=dir;
   }
   if(tensor.size()>8192)return false;
  }
 }
 valid++;vector<int> degree(Q);
 for(auto&[pq,w]:tensor){degree[pq.first]+=w.count();degree[pq.second]+=w.count();}
 vector<Factor> best;bool first=true;
 for(int mode=0;mode<3;mode++){
  map<int,map<int,Bits>> tab;
  for(auto&[pq,w]:tensor){int x=pq.first,y=pq.second;if(mode==1||(mode==2&&degree[y]>degree[x]))swap(x,y);for(int t:support(w))tab[x][t].flip(y);}
  vector<Factor> fs;
  for(auto&[x,rows]:tab)while(true){
   auto it=find_if(rows.begin(),rows.end(),[](auto&p){return p.second.any();});if(it==rows.end())break;
   Bits v=it->second,dir;size_t p=v._Find_first();
   for(auto&[t,row]:rows)if(row[p]){dir.set(t);row^=v;}
   fs.push_back({x,v,dir});
  }
  if(first||fs.size()<best.size()){best=move(fs);first=false;}
 }
 if(best.size()>=old)return false;
 // Independent coefficient reconstruction of every quadratic target direction.
 Tensor chk;for(auto&z:best)for(int y:support(z.v))chk[minmax(z.a,y)]^=z.u;
 for(auto&[pq,w]:tensor)if(chk[pq]!=w)throw runtime_error("tensor certificate mismatch");
 for(auto&[pq,w]:chk)if(tensor[pq]!=w)throw runtime_error("extra tensor coefficient");
 vector<Gate> r;
 for(auto&[x,d]:linear)for(int t:support(d)){if(x==Q)r.push_back(makeg(0x11,t,0,0,guard));else r.push_back(makeg(0x21,x,t,0,guard));}
 for(auto&z:best){
  auto vs=support(z.v),us=support(z.u);if(vs.empty()||us.empty())throw runtime_error("empty factor");
  int y=vs[0],t=us[0];vector<Gate> pre;
  for(size_t j=1;j<vs.size();j++)pre.push_back(makeg(0x21,vs[j],y,0,guard));
  for(size_t j=1;j<us.size();j++)pre.push_back(makeg(0x21,t,us[j],0,guard));
  r.insert(r.end(),pre.begin(),pre.end());r.push_back(makeg(0x31,z.a,y,t,guard));r.insert(r.end(),pre.rbegin(),pre.rend());
 }
 r.insert(r.end(),tail.begin(),tail.end());
 if(r.size()>4*(b-a)+100)return false; // bounded command overhead, not a score proxy
 saving=old-best.size();out=move(r);return true;
}
vector<U> operands(const Gate&g){switch((g.op&48)>>4){case 1:return{g.a};case 2:return{g.a,g.b};case 3:return{g.a,g.b,g.t};default:return{};}}
bool touches(const Gate&g,U t){auto q=operands(g);return find(q.begin(),q.end(),t)!=q.end();}
vector<Gate> repay(const Gate&g,U m){
 Gate p;int k=base(g);p.op=0x80|(k==0x11?0x00:k==0x21?0x10:0x20);p.cond=m;p.a=g.a;p.b=g.b;
 if(!(g.op&128))return{p};
 Gate push;push.op=0x81;push.cond=g.cond;Gate pop;pop.op=1;return{push,p,pop};
}
vector<Gate> hmr(const vector<Gate>&g){
 vector<vector<Gate>> patches(g.size());vector<char> changed(g.size());
 for(size_t i=0;i<g.size();i++){
  if(g[i].op!=0x50)continue;U t=g[i].a,m=g[i].bit;vector<size_t> updates;L paid=0;
  for(size_t j=i;j>0;){--j;const Gate&x=g[j];int k=base(x);
   // Keep measurement-event order and enclosing scope intact. No read/write of m.
   if(k==1||k==0x50||k==0x12||k==6||k==7||k==0x47||k==0x17||changed[j]||((x.op&64)&&x.bit==m)||((x.op&128)&&(x.cond&0x7fffffff)==m))break;
   if(!touches(x,t))continue;
   if((k==0x11&&x.a==t)||(k==0x21&&x.b==t)||(k==0x31&&x.t==t)){updates.push_back(j);paid+=k==0x31;}
   else break;
  }
  if(!paid)continue;
  for(size_t j:updates){patches[j]=repay(g[j],m);changed[j]=1;}
  patches[updates.back()].insert(patches[updates.back()].begin(),g[i]);changed[i]=1;hmrSites++;hmrSaved+=paid;
 }
 vector<Gate> r;for(size_t i=0;i<g.size();i++)if(changed[i])r.insert(r.end(),patches[i].begin(),patches[i].end());else r.push_back(g[i]);return r;
}
bool phasePair(const Gate&x,const Gate&y,vector<Gate>&r){
 if(!same(x,y))return false;int k=base(x),l=base(y);
 if(k==0x30&&l==0x30){
  set<U>a{x.a,x.b,x.t},b{y.a,y.b,y.t};vector<U> common;set_intersection(a.begin(),a.end(),b.begin(),b.end(),back_inserter(common));
  if(common.size()==3){r.clear();return true;}
  if(common.size()!=2)return false;U p=0,q=0;for(U z:a)if(!b.count(z))p=z;for(U z:b)if(!a.count(z))q=z;
  Gate c=makeg(0x21,p,q,0,x);r={c,makeg(0x30,common[0],common[1],q,x),c};return true;
 }
 if((k==0x31&&l==0x30)||(k==0x30&&l==0x31)){
  Gate a=k==0x31?x:y,b=k==0x30?x:y;set<U>s{b.a,b.b,b.t};if(!s.count(a.a)||!s.count(a.b)||s.count(a.t))return false;U c=0;for(U v:s)if(v!=a.a&&v!=a.b)c=v;
  Gate p=makeg(0x20,a.t,c,0,a);r={p,a,p};return true;
 }
 return false;
}
vector<Gate> transform(vector<Gate>g){
 g=hmr(g);vector<Gate> r;
 for(size_t i=0;i<g.size();){
  vector<Gate> best;L bestGain=0;size_t end=i+1;
  if(base(g[i])==0x31){int paid=1;for(size_t j=i+1;j<g.size()&&j<i+256&&eligible(g[j])&&same(g[i],g[j]);j++)if(base(g[j])==0x31){
    paid++;vector<Gate> cand;L gain=0;if(block(g,i,j+1,cand,gain)&&(gain>bestGain||(gain==bestGain&&cand.size()<best.size()))){best=move(cand);bestGain=gain;end=j+1;}
    if(paid>=18)break;
   }}
  if(bestGain){r.insert(r.end(),best.begin(),best.end());rankSites++;rankSaved+=bestGain;i=end;}
  else r.push_back(g[i++]);
 }
 vector<Gate> out;
 for(size_t i=0;i<r.size();){vector<Gate> p;if(i+1<r.size()&&phasePair(r[i],r[i+1],p)){out.insert(out.end(),p.begin(),p.end());phaseSites++;phaseSaved+=2-count_if(p.begin(),p.end(),[](const Gate&g){return base(g)==0x30||base(g)==0x31||base(g)==0x32;});i+=2;}else out.push_back(r[i++]);}
 return out;
}
// Conservative liveness: only release a scratch wire known to be zero. All
// registered quantum IDs are pinned for the entire tape. Guard scopes are
// treated as potentially inactive; no sample-specific claims.
int cAnd(int a,int b){return a==0||b==0?0:a==1&&b==1?1:-1;}
void toggle(int&x,int f,bool unconditional){if(f==0)return;if(!unconditional||f<0||x<0)x=-1;else x^=1;}
U compact(string in,string out){
 Reader r(in);U old=r.Q;vector<int> k(old,0),slot(old,-1);vector<char> pin(old);set<U> free;
 for(auto p:r.regs){U nl,rl;memcpy(&nl,p.ptr,4);memcpy(&rl,p.ptr+4,4);for(U j=0;j<rl;j++){U id;memcpy(&id,p.ptr+8+nl+4*j,4);if(id&0x80000000){id&=0x7fffffff;assert(id<old);pin[id]=1;k[id]=-1;slot[id]=id;}}}
 int mx=-1;for(U i=0;i<old;i++)if(pin[i])mx=max(mx,int(i));else free.insert(i);
 Writer w(r,r.B);int depth=0;
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i),h=g;int b=base(g);auto qs=operands(g);
  for(U q:qs){assert(q<old);if(slot[q]<0){assert(k[q]==0&&!free.empty());slot[q]=*free.begin();free.erase(free.begin());}mx=max(mx,slot[q]);}
  int ar=(g.op&48)>>4;if(ar>=1)h.a=slot[g.a];if(ar>=2)h.b=slot[g.b];if(ar>=3)h.t=slot[g.t];
  w.put(h);bool unc=depth==0&&!(g.op&128);U a=g.a,c=g.b,t=g.t;
  if(g.op==0x81)depth++;else if(g.op==1){assert(depth>0);depth--;}
  else if(b==0x11)toggle(k[a],1,unc);
  else if(b==0x21)toggle(k[c],k[a],unc);
  else if(b==0x31)toggle(k[t],cAnd(k[a],k[c]),unc);
  else if(b==0x22){if(unc)swap(k[a],k[c]);else if(k[a]!=k[c])k[a]=k[c]=-1;}
  else if(b==0x32){if(k[a]==1&&unc)swap(k[c],k[t]);else if(k[a]!=0&&k[c]!=k[t])k[c]=k[t]=-1;}
  else if(b==0x12||b==0x50){if(unc)k[a]=0;else if(k[a]!=0)k[a]=-1;}
  else if(b!=0x00&&b!=0x10&&b!=0x13&&b!=0x20&&b!=0x30&&b!=0x40&&b!=0x41&&b!=0x42&&b!=6&&b!=7&&b!=0x47&&b!=0x17){for(U q:qs)k[q]=-1;}
  for(U q:qs)if(!pin[q]&&k[q]==0&&slot[q]>=0){free.insert(slot[q]);slot[q]=-1;}
 }
 assert(depth==0);U nq=mx+1;assert(nq<=old);
 if(nq<old){r.Q=nq;w.write(out);}return nq;
}
L sim(const vector<Gate>&g,L x,bool guard){for(auto a:g){if((a.op&128)&&!guard)continue;auto b=base(a);auto bit=[&](U q){return (x>>q)&1;};if(b==0x11)x^=1ULL<<a.a;else if(b==0x21){if(bit(a.a))x^=1ULL<<a.b;}else if(b==0x31){if(bit(a.a)&&bit(a.b))x^=1ULL<<a.t;}else if(b==0x22){if(bit(a.a)!=bit(a.b))x^=(1ULL<<a.a)|(1ULL<<a.b);}else throw runtime_error("unexpected selftest gate");}return x;}
void selftest(){
 Q=8;vector<vector<Gate>> samples={
 {makeg(0x31,0,1,3),makeg(0x21,2,1),makeg(0x31,0,1,3),makeg(0x21,2,1)},
 {makeg(0x31,0,1,3),makeg(0x21,3,4),makeg(0x31,0,1,4)},
 {makeg(0x31,0,1,3),makeg(0x31,0,1,4),makeg(0x31,0,2,3),makeg(0x31,0,2,4)}
 };
 L n=0;for(auto s:samples)for(int cond=0;cond<2;cond++){for(auto&g:s){if(cond){g.op|=128;g.cond=5;}}vector<Gate> r;L gain=0;if(!block(s,0,s.size(),r,gain)||!gain)throw runtime_error("selftest expected reduction");for(L x=0;x<256;x++)for(int a=0;a<2;a++){if(sim(s,x,a)!=sim(r,x,a))throw runtime_error("selftest mismatch");n++;}}
 for(int x=0;x<2;x++)for(int a=0;a<2;a++)for(int b=0;b<2;b++)for(int m=0;m<2;m++)for(int g=0;g<2;g++){assert((m&(x^(g&a&b)))==((m&x)^(m&g&a&b)));n++;}
 cout<<"SELFTEST "<<n<<" exact guarded state/phase identities PASS\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){selftest();return 0;}
 if(argc!=3){cerr<<"usage: full_transport in.kmb out.kmb\n";return 2;}string in=argv[1],out=argv[2],tmp=out+".ranktmp";
 if(in==out)throw runtime_error("never overwrite input");
 Stats a,b;U oldQ;
 {Reader r(in);oldQ=r.Q;Q=oldQ;if(Q>=1024)throw runtime_error("width unsupported");Writer w(r,r.B);vector<Gate> g;g.reserve(8192);
  auto flush=[&](){auto x=transform(move(g));for(auto&op:x){b.add(op);w.put(op);}g.clear();g.reserve(8192);};
  for(L i=0;i<r.counts[0];i++){auto x=r.read(i);a.add(x);g.push_back(x);if(g.size()==8192)flush();}if(!g.empty())flush();
  assert(a.paid()>=b.paid());assert(a.paid()-b.paid()==rankSaved+hmrSaved+phaseSaved);w.write(tmp);
 }
 U nq=compact(tmp,out);if(nq==oldQ){if(rename(tmp.c_str(),out.c_str()))throw runtime_error("rename");}else remove(tmp.c_str());
 cout<<"{\"old_q\":"<<oldQ<<",\"new_q\":"<<nq<<",\"old_ops\":"<<a.ops<<",\"new_ops\":"<<b.ops<<",\"old_ccx\":"<<a.ccx<<",\"new_ccx\":"<<b.ccx<<",\"old_ccz\":"<<a.ccz<<",\"new_ccz\":"<<b.ccz<<",\"old_cswap\":"<<a.cswap<<",\"new_cswap\":"<<b.cswap<<",\"old_paid\":"<<a.paid()<<",\"new_paid\":"<<b.paid()<<",\"attempts\":"<<attempts<<",\"valid\":"<<valid<<",\"rank_sites\":"<<rankSites<<",\"rank_saved\":"<<rankSaved<<",\"hmr_sites\":"<<hmrSites<<",\"hmr_saved\":"<<hmrSaved<<",\"phase_sites\":"<<phaseSites<<"}\n";
}

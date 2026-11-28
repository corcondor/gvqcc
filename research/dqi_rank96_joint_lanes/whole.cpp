// Exact full-KMB GF4 tensor transfer. No shot data is used for synthesis.
// Pure X/CX/SWAP/CCX same-guard intervals only; arbitrary dirty target.
#include "native.hpp"
using V=bitset<1024>;using W=uint64_t;
static int Q;
V unit(int i){V v;v.set(i);return v;}
bool dot(const V&a,const V&b){return (a&b).count()&1;}
vector<int> bits(const V&v){vector<int>a;for(size_t i=v._Find_first();i<v.size();i=v._Find_next(i))a.push_back(i);return a;}
int op(Gate g){return g.op&127;}
bool eligible(Gate g){return op(g)==17||op(g)==33||op(g)==34||op(g)==49;}
bool guard(Gate a,Gate b){return (a.op&128)==(b.op&128)&&(!(a.op&128)||a.cond==b.cond);}
Gate gg(Gate g,int o,int a=0,int b=0,int t=0){Gate h{};h.op=o|(g.op&128);h.a=a;h.b=b;h.t=t;h.cond=g.cond;return h;}
struct Term{U a,b,c;};
struct Phys{V a,b,c;bool ca=false,cb=false;};
struct Basis{
 array<V,1024> row{};array<W,1024> coord{};int n=0;
 W get(V x)const{W z=0;while(x.any()){int i=x._Find_first();if(!row[i].any())throw runtime_error("not in span");x^=row[i];z^=coord[i];}return z;}
 bool add(V x){W z=0;while(x.any()){int i=x._Find_first();if(row[i].any()){x^=row[i];z^=coord[i];}else{if(n>=63)throw runtime_error("rank cap");row[i]=x;coord[i]=z^(1ull<<n++);return true;}}return false;}
};
struct Map24{
 array<U,24> a{};array<V,24> b{};int n=0;
 bool add(U x,V y){while(x){int i=__builtin_ctz(x);if(a[i]){x^=a[i];y^=b[i];}else{if(y.none())return false;a[i]=x;b[i]=y;n++;return true;}}return y.none();}
 V get(U x)const{V v;while(x){int i=__builtin_ctz(x);if(!a[i])throw runtime_error("bad map");x^=a[i];v^=b[i];}return v;}
};
struct Rank{array<V,1024> a{};int n=0;bool add(V x){while(x.any()){int i=x._Find_first();if(a[i].any())x^=a[i];else{a[i]=x;n++;return true;}}return false;}};
struct Candidate{string name;int typ;vector<Term> t;};
vector<Term> orig[2];vector<Candidate> bank;
void read_terms(string path){
 ifstream f(path);assert(f);int n;f>>n;for(int i=0;i<n;i++){string name;int typ,k;f>>name>>typ>>k;assert(typ==0||typ==1);Candidate c{name,typ,{}};while(k--){Term t;f>>t.a>>t.b>>t.c;assert(t.a&&t.b&&t.c);c.t.push_back(t);}if(name=="original")orig[typ]=c.t;else bank.push_back(c);}
 for(auto c:bank)for(int i=0;i<24;i++)for(int j=0;j<24;j++){U v=0,w=0;for(auto t:orig[c.typ])if((t.a>>i&1)&&(t.b>>j&1))v^=t.c;for(auto t:c.t)if((t.a>>i&1)&&(t.b>>j&1))w^=t.c;assert(v==w);}
}
struct Extract{vector<Phys> p;vector<Gate> affine;};
optional<Extract> extract(const vector<Gate>&g){
 vector<V> A(Q),I(Q);vector<char> c(Q);for(int i=0;i<Q;i++)A[i]=I[i]=unit(i);
 Extract e;
 for(auto h:g){int k=op(h);if(k==17){c[h.a]^=1;e.affine.push_back(h);}
 else if(k==33){A[h.b]^=A[h.a];c[h.b]^=c[h.a];I[h.a]^=I[h.b];e.affine.push_back(h);}
 else if(k==34){swap(A[h.a],A[h.b]);swap(I[h.a],I[h.b]);swap(c[h.a],c[h.b]);e.affine.push_back(h);}
 else if(k==49){Phys t{A[h.a],A[h.b],I[h.t],bool(c[h.a]),bool(c[h.b])};for(auto&v:e.p)if(dot(t.a,v.c)||dot(t.b,v.c))return nullopt;e.p.push_back(t);}
 else return nullopt;}
 if(e.p.size()!=99)return nullopt;
 for(auto a:e.p)for(auto b:e.p)if(dot(a.a,b.c)||dot(a.b,b.c))return nullopt;
 return e;
}
bool split_sides(vector<Phys>&P){
 Basis b;for(auto t:P){b.add(t.a);b.add(t.b);}if(b.n!=48)return false;
 int d[48];iota(d,d+48,0);auto find=[&](int i){while(d[i]!=i)i=d[i];return i;};
 auto connect=[&](W x){int i=__builtin_ctzll(x);x&=x-1;while(x){int j=__builtin_ctzll(x);d[find(j)]=find(i);x&=x-1;}};
 for(auto t:P){connect(b.get(t.a));connect(b.get(t.b));}
 set<int> groups;for(int i=0;i<48;i++)groups.insert(find(i));if(groups.size()!=2)return false;
 int root=find(__builtin_ctzll(b.get(P[0].a)));Rank a,c;for(auto&t:P){int x=find(__builtin_ctzll(b.get(t.a))),y=find(__builtin_ctzll(b.get(t.b)));if(x==y)return false;if(x!=root){swap(t.a,t.b);swap(t.ca,t.cb);}a.add(t.a);c.add(t.b);}return a.n==24&&c.n==24;
}
struct Frames{vector<int> wires;vector<V> rows;vector<Gate> gates;};
optional<Frames> make_frame(const Map24&A,const Map24&B,const Map24&C,Gate g){
 vector<V> ar,br,cw,du,rows;V active;
 Rank rank,output;for(int i=0;i<24;i++){ar.push_back(A.get(1u<<i));br.push_back(B.get(1u<<i));cw.push_back(C.get(1u<<i));active|=ar.back()|br.back()|cw.back();if(!output.add(cw.back()))return nullopt;}
 for(auto r:ar){if(!rank.add(r))return nullopt;rows.push_back(r);}
 for(auto r:br){if(!rank.add(r))return nullopt;rows.push_back(r);}
 auto wires=bits(active);if(wires.size()<72||wires.size()>256)return nullopt;
 auto pairmask=[&](const V&x){U k=0;for(int j=0;j<24;j++)if(dot(x,cw[j]))k|=1u<<j;return k;};
 Map24 m;for(int i:wires){U u=pairmask(unit(i));if(!u)continue; // independent rows only
   U x=u;for(int k=0;k<24;k++)if(x>>k&1){if(m.a[k])x^=m.a[k];else break;}
   if(x&&!m.add(u,unit(i)))return nullopt;
   if(m.n==24)break;
 }
 if(m.n!=24)return nullopt;
 for(auto r:rows)if(pairmask(r))return nullopt;
 for(int j=0;j<24;j++){auto v=m.get(1u<<j);if(pairmask(v)!=(1u<<j)||!rank.add(v))return nullopt;du.push_back(v);rows.push_back(v);}
 for(int i:wires){V v=unit(i);U p=pairmask(v);for(int j=0;j<24;j++)if(p>>j&1)v^=du[j];if(rank.add(v))rows.push_back(v);}
 if(rows.size()!=wires.size())return nullopt;
 // Reduce exact frame to identity then reverse the elementary operations.
 vector<V> R=rows;vector<Gate> rev;int n=wires.size();
 auto cx=[&](int i,int j){R[j]^=R[i];rev.push_back(gg(g,33,wires[i],wires[j]));};
 for(int i=0;i<n;i++){int k=i;while(k<n&&!R[k][wires[i]])k++;if(k==n)return nullopt;if(k!=i){swap(R[k],R[i]);rev.push_back(gg(g,34,wires[k],wires[i]));}
 for(int j=0;j<n;j++)if(j!=i&&R[j][wires[i]])cx(i,j);}
 for(int i=0;i<n;i++)assert(R[i]==unit(wires[i]));
 reverse(rev.begin(),rev.end());
 // Independently reapply the emitted frame.
 for(int i=0;i<n;i++)R[i]=unit(wires[i]);array<int,1024> ix{};for(int i=0;i<n;i++)ix[wires[i]]=i;
 for(auto h:rev){if(op(h)==33)R[ix[h.b]]^=R[ix[h.a]];else swap(R[ix[h.a]],R[ix[h.b]]);}
 assert(R==rows);
 return Frames{wires,rows,rev};
}
void parity(vector<Gate>&r,Gate g,U m,const vector<int>&w,int offset,int pivot,bool target=false){
 for(int j=0;j<24;j++)if(j!=pivot&&(m>>j&1))r.push_back(gg(g,33,target?w[offset+pivot]:w[offset+j],target?w[offset+j]:w[offset+pivot]));
}
bool verify_quadratic(const vector<Phys>&P,const vector<Term>&T,const Map24&A,const Map24&B,const Map24&C){
 // All square-free degree-two coefficients and their full Q-bit output directions.
 // Linear/constant offsets of P are emitted separately, verbatim algebraically.
 map<pair<int,int>,V> d;
 auto push=[&](V a,V b,V c){for(int i:bits(a))for(int j:bits(b))d[minmax(i,j)]^=c;};
 for(auto p:P)push(p.a,p.b,p.c);
 for(auto t:T)push(A.get(t.a),B.get(t.b),C.get(t.c));
 return all_of(d.begin(),d.end(),[](auto&x){return x.second.none();});
}
optional<vector<Gate>> substitute(const vector<Gate>&g,const Extract&e,const Map24&A,const Map24&B,const Map24&C,int typ,const Candidate&cand){
 if(cand.typ!=typ)return nullopt;
 if(!verify_quadratic(e.p,cand.t,A,B,C))return nullopt;
 auto f=make_frame(A,B,C,g[0]);if(!f)return nullopt;
 auto&w=f->wires;vector<Gate> r=f->gates;
 for(auto t:cand.t){int a=__builtin_ctz(t.a),b=__builtin_ctz(t.b),c=__builtin_ctz(t.c);vector<Gate> pre;parity(pre,g[0],t.a,w,0,a);parity(pre,g[0],t.b,w,24,b);parity(pre,g[0],t.c,w,48,c,true);r.insert(r.end(),pre.begin(),pre.end());r.push_back(gg(g[0],49,w[a],w[24+b],w[48+c]));r.insert(r.end(),pre.rbegin(),pre.rend());}
 // Transport old affine signs into the exact common coordinate frame.
 U constant=0;array<U,48> lin{};
 for(int k=0;k<99;k++){auto t=orig[typ][k];auto p=e.p[k];if(p.ca&&p.cb)constant^=t.c;if(p.cb)for(int j=0;j<24;j++)if(t.a>>j&1)lin[j]^=t.c;if(p.ca)for(int j=0;j<24;j++)if(t.b>>j&1)lin[24+j]^=t.c;}
 for(int j=0;j<24;j++)if(constant>>j&1)r.push_back(gg(g[0],17,w[48+j]));
 for(int i=0;i<48;i++)for(int j=0;j<24;j++)if(lin[i]>>j&1)r.push_back(gg(g[0],33,w[i],w[48+j]));
 r.insert(r.end(),f->gates.rbegin(),f->gates.rend());r.insert(r.end(),e.affine.begin(),e.affine.end());return r;
}
static L sites=0,matched=0,changed=0,signs=0,saved=0,oldops=0,newops=0;static L types[2]={};static map<string,L>selected;
optional<vector<Gate>> replace_block(vector<Gate>const&g,bool dry){
 sites++;auto e=extract(g);if(!e||!split_sides(e->p))return nullopt;
 for(int typ=0;typ<2;typ++){Map24 A,B,C;bool ok=true;for(int k=0;k<99;k++){auto t=orig[typ][k];auto p=e->p[k];if(!A.add(t.a,p.a)||!B.add(t.b,p.b)||!C.add(t.c,p.c)){ok=false;break;}}
 if(!ok||A.n!=24||B.n!=24||C.n!=24)continue;
 Rank a,b,c;for(int j=0;j<24;j++){a.add(A.get(1u<<j));b.add(B.get(1u<<j));c.add(C.get(1u<<j));}if(a.n!=24||b.n!=24||c.n!=24)continue;
 matched++;types[typ]++;signs+=any_of(e->p.begin(),e->p.end(),[](auto x){return x.ca||x.cb;});
 optional<vector<Gate>> best;int count=100;string name;
 for(auto &t:bank)if(t.typ==typ){if(!dry&&t.t.size()>=99)continue;auto r=substitute(g,*e,A,B,C,typ,t);if(r&&(int(t.t.size())<count||(int(t.t.size())==count&&(!best||r->size()<best->size())))){count=t.t.size();best=move(r);name=t.name;}}
 if(best){if(!dry&&count>=99)throw runtime_error("not reduced");changed++;saved+=99-count;oldops+=g.size();newops+=best->size();selected[name]++;}
 return best;
 }
 return nullopt;
}
int main(int argc,char**argv){
 assert(argc==5);string mode=argv[4];assert(mode=="--dry99"||mode=="--strict97");bool dry=mode=="--dry99";
 read_terms(argv[3]);if(!dry){for(int typ=0;typ<2;typ++){bool ok=false;for(auto c:bank)if(c.typ==typ&&c.t.size()<=97)ok=true;if(!ok){cerr<<"NO_RANK97_CERTIFICATE\n";return 3;}}}
 Reader r(argv[1]);Q=r.Q;assert(Q<=1024);Writer w(r,r.B);vector<Gate> buf;int paid=0;L start=0;
 auto flush=[&](){if(paid==99){auto a=find_if(buf.begin(),buf.end(),[](Gate g){return op(g)==49;});auto b=find_if(buf.rbegin(),buf.rend(),[](Gate g){return op(g)==49;}).base();vector<Gate> z(a,b);auto newg=replace_block(z,dry);
 if(newg){for(auto i=buf.begin();i!=a;i++)w.put(*i);for(auto h:*newg)w.put(h);for(auto i=b;i!=buf.end();i++)w.put(*i);buf.clear();paid=0;return;}}
 for(auto h:buf)w.put(h);buf.clear();paid=0;};
 for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);if(!eligible(g)){flush();w.put(g);continue;}if(!buf.empty()&&!guard(buf[0],g))flush();buf.push_back(g);if(op(g)==49)paid++;if(buf.size()>2000000)throw runtime_error("oversize eligible interval");}flush();
 if(!dry&&(changed!=333||saved<666)){cerr<<"STRICT_REJECT sites "<<sites<<" matched "<<matched<<" changed "<<changed<<" saved "<<saved<<"\n";return 4;}
 w.write(argv[2]);cout<<"{\"sites\":"<<sites<<",\"matched\":"<<matched<<",\"changed\":"<<changed<<",\"field\":"<<types[0]<<",\"dual\":"<<types[1]<<",\"sign_sites\":"<<signs<<",\"old_ops\":"<<r.counts[0]<<",\"new_ops\":"<<w.ops.size()<<",\"static_ccx_saved\":"<<saved<<",\"Q\":"<<Q<<"}\n";for(auto [s,n]:selected)cerr<<s<<" "<<n<<"\n";
}

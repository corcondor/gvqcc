// Full serialized circuit: forward symbolic live-value relations and HMR return.
// Every accepted relation is exact in an abstract Boolean algebra.
// Forgetting a large expression only introduces a fresh independent atom.
// No verification inputs, measured samples, or competition salts in synthesis.
#include "native.hpp"
static constexpr int CAP=32;
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
struct F{
    U n=0; uint64_t h=0; array<U,CAP> a{};
    bool operator==(const F&b)const{return n==b.n&&h==b.h&&equal(a.begin(),a.begin()+n,b.a.begin());}
    bool operator<(const F&b)const{return lexicographical_compare(a.begin(),a.begin()+n,b.a.begin(),b.a.begin()+b.n);}
    bool zero()const{return n==0;}
    bool one()const{return n==1&&a[0]==1;}
};
struct Key{F a,b;bool operator==(const Key&k)const{return a==k.a&&b==k.b;}};
struct Hash{size_t operator()(const Key&k)const{return mix(k.a.h)^mix(k.b.h+37);}};
struct Engine{
    U next=2; L forgotten=0;
    unordered_map<Key,U,Hash> products;
    F atom(U x){F a;a.n=1;a.a[0]=x;a.h=mix(x);return a;}
    F fresh(){assert(next<UINT32_MAX);return atom(next++);}
    bool xor_exact(const F&a,const F&b,F&z){
        F out;U i=0,j=0;
        while(i<a.n||j<b.n){
            if(i<a.n&&j<b.n&&a.a[i]==b.a[j]){i++;j++;continue;}
            if(out.n==CAP)return false;
            if(j==b.n||(i<a.n&&a.a[i]<b.a[j]))out.a[out.n++]=a.a[i++];
            else out.a[out.n++]=b.a[j++];
        }
        out.h=a.h^b.h;z=out;return true;
    }
    F x(const F&a,const F&b){F z;if(xor_exact(a,b,z))return z;forgotten++;return fresh();}
    F neg(const F&a){return x(a,atom(1));}
    bool opposite(const F&a,const F&b){F z;return xor_exact(a,b,z)&&z.one();}
    F opaque(F a,F b){
        if(b<a)swap(a,b);
        if(products.size()>=200000)products.clear();
        Key k{a,b};auto it=products.find(k);if(it!=products.end())return atom(it->second);
        F z=fresh();products.emplace(move(k),z.a[0]);return z;
    }
    F mul(const F&a,const F&b){
        if(a.zero()||b.zero())return {};
        if(a.one())return b;if(b.one())return a;if(a==b)return a;
        if(opposite(a,b))return {};
        if(a.n*b.n<=24){
            F z;
            for(U i=0;i<a.n;i++)for(U j=0;j<b.n;j++){
                U p=a.a[i],q=b.a[j];
                F v=p==1?atom(q):q==1||p==q?atom(p):opaque(atom(p),atom(q));
                z=x(z,v);
            }
            return z;
        }
        return opaque(a,b);
    }
    F assign(const F&old,const F&val,const F&g){if(g.one())return val;if(g.zero()||old==val)return old;return x(old,mul(g,x(old,val)));}
};
struct Guard{
    Engine&e;vector<F> rows;bool impossible=false;
    explicit Guard(Engine&ee):e(ee){}
    F reduce(F x)const{
        for(const F&v:rows){
            U p=v.a[v.n-1];
            if(binary_search(x.a.begin(),x.a.begin()+x.n,p)){
                F z;if(!e.xor_exact(x,v,z))return x;x=z;
            }
        }return x;
    }
    void add(const F&g){
        if(impossible||g.one())return;
        F z=reduce(e.neg(g));if(z.zero())return;if(z.one()){impossible=true;return;}
        if(!z.n||z.a[z.n-1]==1)return;
        rows.push_back(z);
        sort(rows.begin(),rows.end(),[](const F&a,const F&b){return a.a[a.n-1]>b.a[b.n-1];});
    }
};
struct Expr{bool found=false,constant=false;vector<U> wires;};
struct Stat{L old_paid=0,new_paid=0,dead=0,linear=0,hmr=0,ccx=0,ccz=0,cswap=0,old_ops=0,new_ops=0,pair_calls=0;};
static bool paid(int op){op&=127;return op==48||op==49||op==50;}
struct Pass{
    Engine e;vector<F> q,b;vector<F> stack,active;
    bool allow_hmr,pairs;Stat s;U freshbit;
    vector<Gate> result;
    Pass(U nq,U nb,bool h,bool p):q(nq),b(nb),allow_hmr(h),pairs(p),freshbit(nb){active.push_back(e.atom(1));}
    F getcond(U c){
        // KMB v2 condition operands are ordinary classical indices.
        assert(c<b.size());return b[c];
    }
    void put(Gate g){result.push_back(g);s.new_ops++;s.new_paid+=paid(g.op);}
    Gate make(int op,U a=0,U b=0,U t=0,U bit=0,U c=0){return Gate{(unsigned char)op,a,b,t,bit,c};}
    Gate guarded(int op,U a,U z,U t,const Gate&g){return make(op|(g.op&128),a,z,t,0,g.cond);}
    // Solve a constant/one-/two-wire affine representation in the active guard.
    // Hashes are only lookup accelerators; every relation is checked by exact XOR.
    Expr find(const F&p,const vector<F>&f,U ex1=UINT32_MAX,U ex2=UINT32_MAX,bool pair=true){
        if(p.zero()||p.one())return {true,p.one(),{}};
        for(U i=0;i<f.size();i++)if(i!=ex1&&i!=ex2){
            if(p==f[i])return {true,false,{i}};
            if(e.opposite(p,f[i]))return {true,true,{i}};
        }
        if(!pairs||!pair||p.n>12)return {};
        s.pair_calls++;
        // Restrict candidate pair search to forms of useful size.
        unordered_map<uint64_t,U> idx;
        idx.reserve(f.size()*2);
        for(U j=0;j<f.size();j++)if(j!=ex1&&j!=ex2&&!f[j].zero()&&!f[j].one()&&f[j].n<=16)idx.emplace(f[j].h,j);
        for(U i=0;i<f.size();i++)if(i!=ex1&&i!=ex2&&!f[i].zero()&&!f[i].one()&&f[i].n<=16){
            for(int c=0;c<2;c++){
                auto it=idx.find(p.h^f[i].h^(c?mix(1):0));
                if(it==idx.end()||it->second==i)continue;
                U j=it->second;F z,y;
                if(e.xor_exact(f[i],f[j],z)&&e.xor_exact(z,c?e.atom(1):F{},y)&&y==p)return {true,bool(c),{i,j}};
            }
        }
        return {};
    }
    void xor_out(U t,const Expr&r,const Gate&g){
        if(r.constant)put(guarded(17,t,0,0,g));
        for(U v:r.wires){assert(t!=v);put(guarded(33,v,t,0,g));}
    }
    void phase_out(U t,const Expr&r,const Gate&g){
        if(r.constant)put(guarded(16,t,0,0,g));
        for(U v:r.wires)if(v==t)put(guarded(16,t,0,0,g));else put(guarded(32,v,t,0,g));
    }
    void erase_and_return(const Gate&g,const Expr&r){
        // old target = a*b XOR r. HMR old t, then repay its exact sign
        // using the original controls and the surviving affine representation.
        if(g.op&128)put(make(129,0,0,0,0,g.cond));
        put(make(80,g.t,0,0,freshbit));
        put(make(160,g.a,g.b,0,0,freshbit));
        if(r.constant)put(make(128,0,0,0,0,freshbit));
        for(U v:r.wires){assert(v!=g.t);put(make(144,v,0,0,0,freshbit));}
        put(make(64,0,0,0,freshbit));
        Gate unguarded{};xor_out(g.t,r,unguarded);
        if(g.op&128)put(make(1));
    }
    void run(Gate g){
        result.clear();s.old_ops++;int op=g.op&127;s.old_paid+=paid(op);
        if(g.op==129){F c=getcond(g.cond);stack.push_back(c);active.push_back(e.mul(active.back(),c));put(g);return;}
        if(op==1){assert(active.size()>1);active.pop_back();stack.pop_back();put(g);return;}
        F h=active.back();F c=e.atom(1);
        if(g.op&128){c=getcond(g.cond);h=e.mul(h,c);}
        auto a=g.a,v=g.b,t=g.t;
        bool ispaid=paid(op);bool rewritten=false;
        // Calculate exact abstract values before the operation, restricted to the
        // branch where the gate executes. Atoms are never assumed independent
        // for evaluating states; linear equations provide only sound implications.
        if(ispaid){
            Guard G(e);for(auto &z:stack)G.add(z);G.add(c);G.add(h);
            if(h.zero()||G.impossible){s.dead++;rewritten=true;}
            else{
                vector<F> f;f.reserve(q.size());
                if(G.rows.empty())f=q;else for(auto&z:q)f.push_back(G.reduce(z));
                if(op==49){
                    F pr=e.mul(f.at(a),f.at(v));pr=G.reduce(pr);
                    auto r=find(pr,f,t);
                    if(r.found){xor_out(t,r,g);s.linear++;s.ccx++;rewritten=true;}
                    else if(allow_hmr){
                        F y=e.x(f.at(t),pr);y=G.reduce(y);
                        auto z=find(y,f,t);
                        if(z.found){erase_and_return(g,z);s.hmr++;s.ccx++;rewritten=true;}
                    }
                }else if(op==48){
                    // Any pair of the three controls can be contracted.
                    array<U,3>w={a,v,t};
                    for(int k=0;k<3&&!rewritten;k++){
                        U u=w[(k+1)%3],z=w[(k+2)%3],last=w[k];
                        F pr=G.reduce(e.mul(f.at(u),f.at(z)));
                        auto r=find(pr,f);
                        if(r.found){phase_out(last,r,g);s.linear++;s.ccz++;rewritten=true;}
                    }
                }else{
                    assert(op==50);
                    if(f[a].zero()||f[v]==f[t]){s.linear++;s.cswap++;rewritten=true;}
                    else if(f[a].one()){put(guarded(34,v,t,0,g));s.linear++;s.cswap++;rewritten=true;}
                    else{
                        F pr=G.reduce(e.mul(f[a],e.x(f[v],f[t])));
                        auto r=find(pr,f,v,t);
                        if(r.found){xor_out(v,r,g);xor_out(t,r,g);s.linear++;s.cswap++;rewritten=true;}
                    }
                }
            }
        }
        if(!rewritten)put(g);
        if(h.zero())return;
        // Original state transition, exact independent of rewrite and HMR draws.
        // The new measurement result is not referenced by any original gate.
        switch(op){
        case 0:case 6:case 7:case 16:case 19:case 23:case 32:case 48:case 71:break;
        case 17:q.at(a)=e.x(q.at(a),h);break;
        case 18:q.at(a)=e.assign(q.at(a),F{},h);break;
        case 33:q.at(v)=e.x(q.at(v),e.mul(h,q.at(a)));break;
        case 34:{F d=e.mul(h,e.x(q.at(a),q.at(v)));q[a]=e.x(q[a],d);q[v]=e.x(q[v],d);break;}
        case 49:q.at(t)=e.x(q.at(t),e.mul(h,e.mul(q.at(a),q.at(v))));break;
        case 50:{F d=e.mul(h,e.mul(q.at(a),e.x(q.at(v),q.at(t))));q[v]=e.x(q[v],d);q[t]=e.x(q[t],d);break;}
        case 64:b.at(g.bit)=e.assign(b.at(g.bit),F{},h);break;
        case 65:b.at(g.bit)=e.assign(b.at(g.bit),e.atom(1),h);break;
        case 66:b.at(g.bit)=e.x(b.at(g.bit),h);break;
        case 80:q.at(a)=e.assign(q.at(a),F{},h);b.at(g.bit)=e.assign(b.at(g.bit),e.fresh(),h);break;
        default:throw runtime_error("unsupported opcode "+to_string(op));
        }
    }
};
int main(int argc,char**argv){
    if(argc!=5){cerr<<"usage: live input.kmb output.kmb unitary|hmr single|pairs\n";return 2;}
    string src=argv[1],dst=argv[2];assert(src!=dst&&!filesystem::exists(dst));
    bool h=string(argv[3])=="hmr",p=string(argv[4])=="pairs";
    Reader r(src);Pass pass(r.Q,r.B,h,p);
    for(auto z:r.regs){
        U n,l;memcpy(&n,z.ptr,4);memcpy(&l,z.ptr+4,4);
        assert(z.len==8+n+4ULL*l);
        for(U i=0;i<l;i++){
            U k;memcpy(&k,z.ptr+8+n+i*4,4);
            if(k&0x80000000U)pass.q.at(k&0x7fffffffU)=pass.e.fresh();
            else pass.b.at(k)=pass.e.fresh();
        }
    }
    Writer w(r,r.B+(h?1:0));
    ofstream cert(dst+".sites.tsv");
    for(L i=0;i<r.counts[0];i++){
        auto g=r.read(i);pass.run(g);
        if(paid(g.op)&&none_of(pass.result.begin(),pass.result.end(),[](Gate q){return paid(q.op);})){
            cert<<i<<'\t'<<unsigned(g.op)<<'\t'<<g.a<<'\t'<<g.b<<'\t'<<g.t<<'\t'<<pass.result.size()<<'\n';
        }
        for(auto z:pass.result)w.put(z);
    }
    assert(pass.stack.empty());
    if(h&&pass.s.hmr==0)w.bits=r.B;
    w.write(dst);
    auto &s=pass.s;
    assert(s.old_paid-s.new_paid==s.dead+s.linear+s.hmr);
    cout<<"{\"Q\":"<<r.Q<<",\"old_ops\":"<<s.old_ops<<",\"new_ops\":"<<s.new_ops<<",\"old_paid\":"<<s.old_paid<<",\"new_paid\":"<<s.new_paid<<",\"dead\":"<<s.dead<<",\"linear\":"<<s.linear<<",\"hmr\":"<<s.hmr<<",\"active_CCX\":"<<s.ccx<<",\"active_CCZ\":"<<s.ccz<<",\"active_CSWAP\":"<<s.cswap<<",\"forgotten\":"<<pass.e.forgotten<<",\"pair_calls\":"<<s.pair_calls<<"}\n";
}

#include "native.hpp"
// Abstract Boolean values: exact literal or fresh opaque atom. 0=false, 1=true;
// complement is xor 1. Canonical small AND/XOR nodes preserve exact identities.
// Bounded abstraction forgets dependencies only, never equates unrelated values.
struct Node{U a,b;unsigned char op,dep;};
struct Key{U a,b;unsigned char op;bool operator==(Key const&k)const{return a==k.a&&b==k.b&&op==k.op;}};
struct Hash{size_t operator()(Key const&k)const{return (L(k.a)*0x9e3779b185ebca87ULL)^(L(k.b)*0xc2b2ae3d27d4eb4fULL)^k.op;}};
struct Logic{vector<Node> n{{0,0,0,0}};unordered_map<Key,U,Hash> cache;int D=8;L opaque=0;U fresh(){n.push_back({0,0,0,0});opaque++;return (n.size()-1)*2;}
 U mk(U a,U b,int op){if(a>b)swap(a,b);if(op==1){if(a==0||a==(b^1))return 0;if(a==1||a==b)return b;}else{if(a==0)return b;if(a==1)return b^1;if(a==b)return 0;if(a==(b^1))return 1;U inv=(a^b)&1;a&=~1U;b&=~1U;if(a>b)swap(a,b);return raw(a,b,op)^inv;}
  if(has(b,a^1)||has(a,b^1))return 0;if(has(b,a))return b;if(has(a,b))return a;
  return raw(a,b,op);
 }
 bool has(U b,U a,int d=3){if(b==a)return true;if(d==0||b<2||(b&1))return false;Node k=n[b>>1];if(k.op!=1)return false;return has(k.a,a,d-1)||has(k.b,a,d-1);}
 U raw(U a,U b,int op){unsigned dep=max(n[a>>1].dep,n[b>>1].dep)+1;if(dep>D)return fresh();Key k{a,b,(unsigned char)op};auto it=cache.find(k);if(it!=cache.end())return it->second;U v=n.size()*2;n.push_back({a,b,(unsigned char)op,(unsigned char)dep});cache.emplace(k,v);return v;}
 U And(U a,U b){return mk(a,b,1);}U Xor(U a,U b){return mk(a,b,2);}U Or(U a,U b){return And(a^1,b^1)^1;}
 U mux(U g,U old,U val){if(g==0||old==val)return old;if(g==1)return val;if(val==0)return And(old,g^1);if(val==1)return Or(old,g);if(old==0)return And(g,val);if(old==1)return Or(g^1,val);return Xor(old,And(g,Xor(old,val)));}
};
struct Frame{U cond;bool active;unordered_map<U,U> old;};
int main(int argc,char**argv){Reader r(argv[1]);Writer w(r,r.B);Logic l;vector<U>b(r.B);for(auto p:r.regs){U len,n;memcpy(&len,p.ptr,4);memcpy(&n,p.ptr+4,4);if(p.ptr[8]!='E')continue;for(U j=0;j<n;j++){U i;memcpy(&i,p.ptr+8+len+4*j,4);b[i]=l.fresh();}}
 vector<Frame> stack;bool active=true;L gone[128]={},counts[128]={};ofstream log(argv[3]);auto put=[&](U j,U v){if(b[j]==v)return;if(!stack.empty())stack.back().old.try_emplace(j,b[j]);b[j]=v;};for(L i=0;i<r.counts[0];i++){auto g=r.read(i);int op=g.op&127;U cond=active?((g.op&128)?b[g.cond]:1):0;if(op==1){if(g.op&128){stack.push_back({cond,active,{}});active=cond!=0;if(active&&cond!=1)put(g.cond,1);}else{assert(!stack.empty());auto fr=move(stack.back());stack.pop_back();active=fr.active;for(auto [j,old]:fr.old){U after=b[j];b[j]=old;put(j,l.mux(fr.cond,old,after));}}w.put(g);continue;}counts[op]++;if(cond==0){gone[op]++;if(op==48||op==49)log<<i<<' '<<op<<' '<<g.a<<' '<<g.b<<' '<<g.t<<' '<<g.cond<<'\n';else w.put(g);continue;}
 switch(op){case 64:put(g.bit,l.And(b[g.bit],cond^1));break;case 65:put(g.bit,l.Or(b[g.bit],cond));break;case 66:put(g.bit,l.Xor(b[g.bit],cond));break;case 80:put(g.bit,l.mux(cond,b[g.bit],l.fresh()));break;default:break;}w.put(g);if(l.cache.size()>4000000)l.cache.clear();}
 assert(stack.empty());w.write(argv[2]);for(int i=0;i<128;i++)if(counts[i])cout<<i<<" "<<counts[i]<<" removed "<<gone[i]<<endl;cout<<"nodes "<<l.n.size()<<" opaque "<<l.opaque<<" paid "<<r.counts[1]<<" -> "<<w.a[2].size()<<" ops "<<r.counts[0]<<" -> "<<w.ops.size()<<endl;}

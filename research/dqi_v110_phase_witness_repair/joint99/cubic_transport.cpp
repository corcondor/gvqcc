#include "native.hpp"
using T=array<U,3>;
struct Key {
 U a,b,cond;bool guarded;
 bool operator<(const Key& o)const{return tie(a,b,cond,guarded)<tie(o.a,o.b,o.cond,o.guarded);}
};
T sort3(Gate g){T t{g.a,g.b,g.t};sort(t.begin(),t.end());return t;}
struct Pair{L i; Gate a,b; U u,v,first,last;};
int main(int argc,char **argv){
 assert(argc==3);Reader r(argv[1]);
 vector<L> qw(r.Q),bw(r.B); L fence=0;
 map<Key,vector<pair<L,Gate>>> index;
 map<L,Pair> replace;
 set<L> remove,used;
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);const int op=g.op&127;
  // Time uses i+1 so all unwritten registers begin at zero.
  if(op==48){
   auto t=sort3(g);
   assert(t[0]!=t[1]&&t[1]!=t[2]);
   const bool guard=g.op&128; const U cond=guard?g.cond:0;
   T pair_u{t[0],t[0],t[1]},pair_v{t[1],t[2],t[2]},third{t[2],t[1],t[0]};
   bool found=false;
   for(int k=0;k<3&&!found;k++){
    auto &v=index[{pair_u[k],pair_v[k],cond,guard}];
    while(!v.empty()){
     auto [j,a]=v.back();
     if(used.count(j)||j+1<=fence||i-j>20000){v.pop_back();continue;}
     auto s=sort3(a);
     if(max({qw[s[0]],qw[s[1]],qw[s[2]],guard?bw[cond&0x7fffffff]:0})>j+1){v.pop_back();continue;}
     U p=0;for(auto x:s)if(x!=pair_u[k]&&x!=pair_v[k])p=x;
     remove.insert(j);used.insert(j);used.insert(i);
     replace[i]={j,a,g,pair_u[k],pair_v[k],p,third[k]};found=true;break;
    }
   }
   if(!found)for(int k=0;k<3;k++)index[{pair_u[k],pair_v[k],cond,guard}].emplace_back(i,g);
  }else switch(op){
    case 0:case 16:case 32:break;
    case 17:case 18:qw[g.a]=i+1;break;
    case 33:qw[g.b]=i+1;break;
    case 34:qw[g.a]=qw[g.b]=i+1;break;
    case 49:qw[g.t]=i+1;break;
    case 50:qw[g.a]=qw[g.b]=qw[g.t]=i+1;break;
    case 64:case 65:case 66:bw[g.bit]=i+1;break;
    case 80:qw[g.a]=i+1;bw[g.bit]=i+1;break;
    default:fence=i+1;
  }
 }
 L dups=0,couples=0;
 for(auto [i,p]:replace){
  bool same=p.first==p.last;dups+=same;couples+=!same;
  cout<<p.i<<" "<<i<<" "<<(same?"cancel":"pool")<<" "<<(int)p.b.op<<" "<<p.b.cond<<" "<<p.u<<" "<<p.v<<" "<<p.first<<" "<<p.last<<"\n";
 }
 cerr<<"duplicate cancellations "<<dups<<" pooled "<<couples<<endl;
 if(replace.empty())return 0;
 r.reset();Writer w(r,r.B);
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);
  if(remove.count(i))continue;
  auto k=replace.find(i);
  if(k==replace.end()){w.put(g);continue;}
  auto p=k->second;
  if(p.first==p.last)continue;
  Gate x{(unsigned char)(33|(g.op&128)),p.first,p.last,0,0,g.cond};
  Gate z{g.op,p.u,p.v,p.last,0,g.cond};
  w.put(x);w.put(z);w.put(x);
 }
 w.write(argv[2]);
}

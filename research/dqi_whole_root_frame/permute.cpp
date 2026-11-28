#include "native.hpp"
#include <numeric>
struct Scope { vector<U> old; };
int main(int argc,char**argv){
 assert(argc==3);
 Reader r(argv[1]);Writer w(r,r.B);
 vector<U> map(r.Q),inv(r.Q);iota(map.begin(),map.end(),0);
 vector<Scope> stack;L absorbed=0,restored=0;
 auto restore=[&](const vector<U>&want){
  for(U j=0;j<r.Q;j++)inv[map[j]]=j;
  for(U j=0;j<r.Q;j++)if(map[j]!=want[j]){
   U k=inv[want[j]],a=map[j],b=map[k];
   w.put({34,a,b});swap(map[j],map[k]);inv[a]=k;inv[b]=j;restored++;
  }
  assert(map==want);
 };
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);int o=g.op&127;
  if(g.op==129){stack.push_back({map});w.put(g);continue;}
  if(o==1){assert(!stack.empty());restore(stack.back().old);stack.pop_back();w.put(g);continue;}
  if(g.op==34){swap(map[g.a],map[g.b]);absorbed++;continue;}
  int n=(g.op&48)>>4;
  if(n>=1)g.a=map[g.a];if(n>=2)g.b=map[g.b];if(n>=3)g.t=map[g.t];
  w.put(g);
 }
 assert(stack.empty());vector<U> id(r.Q);iota(id.begin(),id.end(),0);restore(id);w.write(argv[2]);
 cerr<<"permutation: absorbed "<<absorbed<<" restored "<<restored<<" ops "<<r.counts[0]<<" -> "<<w.ops.size()<<" paid "<<w.a[2].size()<<"\n";
}

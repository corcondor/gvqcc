#include "joint_work/audit/common.hpp"
int main(int argc,char**argv){
 if(argc!=4)return 2;
 Reader r(argv[1]);Writer w(r,r.B);
 const L cut=stoull(argv[3]);assert(cut<r.counts[0]);
 int depth=0;
 for(L i=0;i<cut;i++){
  auto g=r.read(i);if(g.op==129)++depth;else if(g.op==1)--depth;
  assert(depth>=0);w.put(g);
 }
 while(depth-->0)w.put(Gate{1});w.write(argv[2]);
}

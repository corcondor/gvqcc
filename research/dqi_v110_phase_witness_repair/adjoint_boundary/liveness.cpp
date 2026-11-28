#include "native.hpp"
int main(int argc,char**argv){
 Reader r(argv[1]); set<U> pub;
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);
 for(U i=0;i<l;i++){U k;memcpy(&k,p.ptr+8+n+4*i,4);if(!(k>>31))pub.insert(k);}}
 ifstream file(argv[2]);string row;vector<tuple<L,L,L,L>> seams;
 while(getline(file,row)){istringstream s(row);L l,t,h,x; if(s>>l>>t>>h>>x)seams.push_back({l,t,h,x});}
 struct Bit{U b;L seam,dead;string why;};vector<Bit> bits; vector<vector<size_t>> index(r.B);
 int depth=0;size_t k=0;L start,end;
 assert(seams.size()==17);
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int op=g.op&127;
  auto visit=[&](U q,string why,bool write){for(size_t j:index.at(q)){Bit&z=bits[j]; if(!z.dead){z.dead=i;z.why=why;if(write)z.why="overwrite";}}index[q].clear();};
  if(g.op&128)visit(g.cond,"read:condition",false);
  if((g.op&64)&&op!=6&&op!=7){
   if(op==64||op==65||op==80){if(!(g.op&128)&&!depth)visit(g.bit,"",true);}
   else visit(g.bit,"read:bit",false);
  }
  if(g.op==129)depth++; else if(op==1)depth--;
  if(k<seams.size()){
   const auto [l,t,h,x]=seams[k];
   if(i>t&&i<=h&&g.op==80){assert(!pub.count(g.bit));index[g.bit].push_back(bits.size());bits.push_back({g.bit,l,0,"never-read"});}
   if(i==h)k++;
  }
 }
 assert(bits.size()==204);
 for(auto b:bits)cout<<b.seam<<' '<<b.b<<' '<<b.dead<<' '<<b.why<<'\n';
}

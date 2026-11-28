#include "native.hpp"
#include <sstream>
struct Scan {L start,end;int guard; vector<U> d; size_t n=0; int z=0,m=0; string cause;};
int main(int argc,char **argv){
 Reader r(argv[1]);ifstream f(argv[2]);vector<Scan> ss; L x,y;int guard;
 while(f>>x>>y>>guard){
  Scan s{x,y,guard};s.d.resize(r.Q);
  for(auto &d:s.d){f>>d;s.n+=(d!=0);}
  ss.push_back(move(s));
 }
 vector<size_t> active;size_t j=0;
 auto output=[&](Scan& s,L i,string why){cout<<s.start<<" "<<s.end<<" "<<i<<" "<<s.n<<" "<<s.z<<" "<<s.m<<" "<<why<<'\n';};
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);while(j<ss.size()&&ss[j].end==i)active.push_back(j++);
  for(auto it=active.begin();it!=active.end();){
   auto &s=ss[*it]; auto dep=[&](U z){return s.d[z]!=0;};
   auto set=[&](U z,U d){s.n+=int(d!=0)-int(dep(z)); s.d[z]=d;};
   string why;
   int op=g.op&127;bool cond=g.op&128;
   switch(op){
    case 0:case 17:case 64:case 65:case 66:break;
    case 16:s.z+=dep(g.a);break;
    case 18:if(dep(g.a))why="R";break;
    case 33:if(dep(g.a)){if(cond)why="guarded_CX";else set(g.b,s.d[g.b]^s.d[g.a]);}break;
    case 34:if(s.d[g.a]!=s.d[g.b]){if(cond)why="guarded_SWAP";else swap(s.d[g.a],s.d[g.b]);}break;
    case 32: if(dep(g.a)&&dep(g.b))why="CZ_two"; else s.z+=dep(g.a)||dep(g.b);break;
    case 48:if(dep(g.a)||dep(g.b)||dep(g.t))why="CCZ";break;
    case 49:if(dep(g.a)||dep(g.b))why="CCX_control";break;
    case 50:if(dep(g.a)||dep(g.b)||dep(g.t))why="CSWAP";break;
    case 80: if(dep(g.a)){if(cond)why="guarded_HMR";else {++s.m;set(g.a,0);}}break;
    default:why="fence_"+to_string(g.op);
   }
   if(s.n==0||!why.empty()||i-s.end>=10000){
    output(s,i,!why.empty()?why:s.n?"cap":"all_data_erased");it=active.erase(it);
   }else ++it;
  }
 }
 for(auto i:active)output(ss[i],r.counts[0],"end");
 assert(j==ss.size());
}

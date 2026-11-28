#include "native.hpp"
int main(int argc,char**argv){
 Reader r(argv[1]); vector<Gate> v; int d=0, sd=0, cc=0; L start=0;
 ofstream f(argv[2]); map<int,int> depths;
 for(L i=0;i<r.counts[0];++i){
  auto g=r.read(i); if(g.op==33||g.op==49){v.push_back(g); cc+=g.op==49;}
  else {
   if(cc==99){
    f<<"# "<<start<<" "<<i<<" "<<sd<<"\n"; ++depths[sd];
    for(auto h:v)f<<int(h.op)<<" "<<h.a<<" "<<h.b<<" "<<h.t<<"\n";
   }
   v.clear();cc=0; if(g.op==129)++d;else if(g.op==1)--d;
   if(d<0){cerr<<"incorrect condition stack at "<<i<<endl;return 3;}
   start=i+1;sd=d;
  }
 }
 assert(d==0);
 for(auto [d,n]:depths)cout<<d<<" "<<n<<endl;
}

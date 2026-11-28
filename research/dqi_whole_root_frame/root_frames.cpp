#include "native.hpp"
#include <deque>
#include <tuple>
bool eq(Gate x,int o,U a,U b=0,U t=0,U bit=0,U cond=0){return x.op==o&&x.a==a&&x.b==b&&x.t==t&&x.bit==bit&&x.cond==cond;}
// Match the full 77-command block, and certify exact ordered signed operands.
vector<Gate> contract(const vector<Gate>&v){
 if(v.size()!=77)return{};U x[12],a[10],p,m[10];int k=0;
 auto X=[&](U q){return eq(v[k++],17,q);};
 auto CXZ=[&](int op,U q,U z,U t=0,U bit=0,U c=0){return eq(v[k++],op,q,z,t,bit,c);};
 x[0]=v[0].a;x[1]=v[1].a;a[0]=v[2].t;
 if(!X(x[0])||!X(x[1])||!CXZ(49,x[0],x[1],a[0])||!X(x[1])||!X(x[0]))return{};
 for(int j=1;j<10;j++){x[j+1]=v[k].a;a[j]=v[k+1].t;if(!X(x[j+1])||!CXZ(49,a[j-1],x[j+1],a[j])||!X(x[j+1]))return{};}
 x[11]=v[k].a;p=v[k+1].t;if(!X(x[11])||!CXZ(48,a[9],x[11],p)||!X(x[11]))return{};
 for(int j=9;j>=1;j--){m[j]=v[k].bit;if(!CXZ(80,a[j],0,0,m[j])||!X(x[j+1])||!CXZ(160,a[j-1],x[j+1],0,0,m[j])||!X(x[j+1]))return{};}
 m[0]=v[k].bit;if(!CXZ(80,a[0],0,0,m[0])||!X(x[0])||!X(x[1])||!CXZ(160,x[0],x[1],0,0,m[0])||!X(x[1])||!X(x[0])||k!=77)return{};
 set<U>s;for(U q:x)s.insert(q);for(U q:a)s.insert(q);s.insert(p);if(s.size()!=23)return{};
 vector<Gate> w;for(U q:x)w.push_back({17,q});w.push_back({49,x[0],x[1],a[0]});for(int j=1;j<10;j++)w.push_back({49,a[j-1],x[j+1],a[j]});w.push_back({48,a[9],x[11],p});
 for(int j=9;j>=1;j--){w.push_back({80,a[j],0,0,m[j]});w.push_back({160,a[j-1],x[j+1],0,0,m[j]});}
 w.push_back({80,a[0],0,0,m[0]});w.push_back({160,x[0],x[1],0,0,m[0]});for(int j=11;j>=0;j--)w.push_back({17,x[j]});assert(w.size()==55);
 auto trace=[&](vector<Gate>const&g){set<U> flip;vector<tuple<int,U,U,U,U,U,int,int,int>> z;
  for(auto h:g){if(h.op==17){if(flip.count(h.a))flip.erase(h.a);else flip.insert(h.a);continue;}
   int n=(h.op&48)>>4;z.emplace_back(h.op,h.a,h.b,h.t,h.bit,h.cond,flip.count(h.a),n>=2?flip.count(h.b):0,n>=3?flip.count(h.t):0);}
  assert(flip.empty());return z;
 };
 assert(trace(v)==trace(w));return w;
}
int main(int argc,char**argv){
 assert(argc==4);Reader r(argv[1]);Writer w(r,r.B);deque<Gate> buf;L first=0,sites=0,orig=0,neu=0;ofstream log(argv[3]);
 for(L i=0;i<r.counts[0];i++){
  buf.push_back(r.read(i));while(buf.size()>=77){
   if(buf.front().op==17){vector<Gate> v(buf.begin(),buf.begin()+77);auto c=contract(v);if(!c.empty()){sites++;orig+=77;neu+=55;log<<first<<'\t'<<first+77<<"\t77\t55\n";for(auto h:c)w.put(h);for(int j=0;j<77;j++)buf.pop_front();first+=77;continue;}}
   w.put(buf.front());buf.pop_front();first++;
  }
 }
 while(!buf.empty()){w.put(buf.front());buf.pop_front();first++;}
 assert(first==r.counts[0]);w.write(argv[2]);cerr<<"root frames sites "<<sites<<" ops "<<r.counts[0]<<" -> "<<w.ops.size()<<" saved "<<orig-neu<<" paid "<<r.counts[1]<<" -> "<<w.a[2].size()<<"\n";
}

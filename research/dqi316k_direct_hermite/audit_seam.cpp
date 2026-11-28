#include "native.hpp"
#include <unordered_map>
using W=uint64_t;
struct Key{W a,b;bool operator==(Key const&k)const{return a==k.a&&b==k.b;}};
struct H{size_t operator()(Key const&k)const{return hash<W>{}(k.a)^hash<W>{}(k.b)*0x9e3779b97f4a7c15ULL;}};
struct Rec{W a,b,c;U word,mask;};
int main(int argc,char**argv){
 Reader r(argv[1]);assert(r.Q==900);unordered_map<Key,vector<Rec>,H> forms;forms.reserve(2500000);
 ifstream f("forms.bin",ios::binary);Rec a;while(f.read((char*)&a,sizeof a))forms[{a.a,a.b}].push_back(a);
 array<vector<W>,3>q,b;array<vector<W>,3>scope;
 for(int k=0;k<3;k++){q[k].resize(r.Q);b[k].resize(r.B);scope[k]={~W(0)};ifstream s("in"+to_string(k)+".bin",ios::binary);s.read((char*)q[k].data(),r.Q*8);}
 L start=stoull(argv[2]),end=stoull(argv[3]);U limit=argc>4?stoul(argv[4]):10000;U paid=0;
 for(L i=0;i<end;i++){auto g=r.read(i);int op=g.op&127;if(op==49||op==48)paid++;
  for(int k=0;k<3;k++){
   auto&Q=q[k];auto&B=b[k];auto&A=scope[k];W c=A.back();
   if(g.op==129){A.push_back(c&B[g.cond&0x7fffffff]);continue;}if(op==1){A.pop_back();continue;}
   if(g.op&128){W v=B[g.cond&0x7fffffff];if(g.cond>>31)v=~v;c&=v;}
   if(!c)continue;
   U x=g.a,y=g.b,z=g.t;
   switch(op){case 0:case 16:case 32:case 48:case 6:break;
   case 17:Q[x]^=c;break;case 18:Q[x]&=~c;break;
   case 33:Q[y]^=c&Q[x];break;case 34:{W t=c&(Q[x]^Q[y]);Q[x]^=t;Q[y]^=t;break;}
   case 49:Q[z]^=c&Q[x]&Q[y];break;
   case 50:{W t=c&Q[x]&(Q[y]^Q[z]);Q[y]^=t;Q[z]^=t;break;}
   case 64:B[g.bit]&=~c;break;case 65:B[g.bit]|=c;break;case 66:B[g.bit]^=c;break;
   case 80:Q[x]&=~c;B[g.bit]&=~c;break;default:cerr<<"unknown "<<op<<endl;return 2;}
  }
  if(i>=start&&(i%limit==0||i+1==end)){
   for(U x=0;x<900;x++){if(!(q[0][x]|q[1][x]))continue;auto it=forms.find({q[0][x],q[1][x]});if(it!=forms.end())for(auto&f:it->second)cout<<i+1<<" "<<paid<<" "<<x<<" "<<f.word<<" "<<f.mask<<" "<<hex<<(q[2][x]^f.c)<<dec<<"\n";}
  }
 }
}


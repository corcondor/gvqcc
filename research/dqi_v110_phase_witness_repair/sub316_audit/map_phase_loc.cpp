#include "../other/src/native.hpp"
L tok(Gate g){return g.op|(L(g.a)<<8)|(L(g.b)<<18)|(L(g.t)<<28);}
int main(int ac,char**argv){
 if(ac!=4)return 2;Reader a(argv[1]),b(argv[2]);L cut=stoull(argv[3]);
 vector<L> left,right;const L n=256;
 for(L i=0;i<a.counts[0]&&right.size()<n/2;i++){auto g=a.read(i);if((g.op&0x30)!=0x30)continue;
   if(i<cut)left.push_back(tok(g));else right.push_back(tok(g));
 }
 assert(left.size()>=n/2&&right.size()==n/2);
 vector<L> key(left.end()-n/2,left.end());key.insert(key.end(),right.begin(),right.end());
 L h=0, want=0,pow=1,pos=0;const L B=257;
 for(auto x:key){want=want*B+x;pow*=B;}
 L ring[n]={},offs[n]={};
 for(L i=0;i<b.counts[0];i++){
   auto g=b.read(i);if((g.op&0x30)!=0x30)continue;L x=tok(g),j=pos%n;
   h=h*B+x-ring[j]*pow;ring[j]=x;offs[j]=i;++pos;
   if(pos<n||h!=want)continue;
   bool eq=true;for(L k=0;k<n;k++)eq&=ring[(pos+k)%n]==key[k];
   if(eq)cout<<offs[(pos+n/2-1)%n]<<' '<<offs[(pos+n/2)%n]<<'\n';
 }
}

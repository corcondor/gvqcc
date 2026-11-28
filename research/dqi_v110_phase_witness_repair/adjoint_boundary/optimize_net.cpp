#include <bits/stdc++.h>
using namespace std;
int main(){
 array<unsigned,12> start{647,3116,1915,1069,4088,1120,1966,2069,2053,1439,912,2957};
 mt19937 rng(332);int best=49;
 for(int it=0;it<150000;it++){
  auto a=start;
  vector<pair<int,int>> left,right;
  for(int i=0;i<80;i++){
   int opt=-100000,t=0,s=0; bool col=false;
   for(int c=0;c<2;c++)for(int p=0;p<12;p++)for(int q=0;q<12;q++)if(p!=q){
    unsigned u=0,v=0;
    if(!c){u=a[p]^(1u<<p);v=a[q]^(1u<<q);}
    else for(int j=0;j<12;j++){u|=(((a[j]>>p)&1)^(j==p))<<j;v|=(((a[j]>>q)&1)^(j==q))<<j;}
    unsigned op=c?0:0; (void)op;
    unsigned src = 0;
    if(!c)src=a[p]; else for(int j=0;j<12;j++)src|=((a[j]>>p)&1)<<j;
    int gain=__builtin_popcount(v)-__builtin_popcount(v^src);
    if(gain<0)continue;
    int noise=5+it%26;
    int score=16*gain+(rng()%noise);
    if(score>opt){opt=score;s=p;t=q;col=c;}
   }
   if(opt==-100000)break;
   if(col){for(auto &r:a) r^=((r>>s)&1)<<t; right.emplace_back(t,s);}
   else{a[t]^=a[s]; left.emplace_back(s,t);}
   int k=0;while(k<12 && a[k]==(1u<<k)) k++;
   if(k==12){
    if(i+1<best){
      best=i+1;
      cout<<best;
      for(auto [p,q]:right)cout<<" "<<p<<">"<<q;
      for(auto j=left.rbegin();j!=left.rend();j++)cout<<" "<<j->first<<">"<<j->second;
      cout<<endl;
    }break;
   }
   if(i+2>=best)break;
  }
 }
}

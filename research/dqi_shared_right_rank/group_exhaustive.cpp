#include <bits/stdc++.h>
using namespace std;using U=uint64_t;
int rank8(U a){int r=0;for(int i=0;i<8;i++){int j=r;while(j<8&&!((a>>(8*j+i))&1))j++;if(j==8)continue;U p=(a>>(8*j))&255,q=(a>>(8*r))&255;a^=(p^q)<<(8*j);a^=(p^q)<<(8*r);for(int k=r+1;k<8;k++)if(a>>(8*k+i)&1)a^=p<<(8*k);r++;}return r;}
U outer(int a,int b){U z=0;for(int i=0;i<8;i++)if(a>>i&1)z|=U(b)<<(8*i);return z;}
int mul(int a,int b){int r=0;while(b){if(b&1)r^=a;b>>=1;a<<=1;if(a&16)a^=19;}return r;}
array<U,16> initial(){
 int w=0;for(int i=2;i<16;i++)if((mul(i,i)^i^1)==0){w=i;break;}assert(w);
 int theta=2;while(theta==w||theta==(w^1))theta++;
 int B[4]={1,w,theta,mul(theta,w)},B2[16]={},inv[16]={};
 for(int x=0;x<16;x++){for(int i=0;i<4;i++)if(x>>i&1)B2[x]^=B[i];inv[B2[x]]=x;}
 array<U,16>M{};int fc[3]={1,2,3},ow[3]={1^w,mul(w,w)^w,w};
 for(int k=0;k<3;k++)for(int j=0;j<3;j++){
  int u=(k==0?fc[j]:k==1?fc[j]<<2:fc[j]^(fc[j]<<2));
  int z0=ow[j],z1=mul(ow[j],theta),z2=mul(ow[j],mul(theta,theta));
  int z=inv[k==0?z0^z1:k==1?z2^z1:z1];
  for(int lane=0;lane<2;lane++)M[u]^=outer(z<<(4*lane),u<<(4*lane));
 }
 for(int a=0;a<8;a++)for(int b=0;b<4;b++){
  int r=0;for(int k=1;k<16;k++)if(k>>b&1){U x=M[k];for(int i=0;i<8;i++)if(x>>(8*i+a)&1)r^=1<<i;}
  assert(r==(inv[mul(B[a%4],B[b])]<<(4*(a/4))));
 }return M;
}
int cost(array<U,16>const&M){int n=0;for(int i=1;i<16;i++)n+=rank8(M[i]);return n;}
int main(){
 auto M=initial();int c=cost(M),best=0;assert(c==18);uint64_t evaluated=0;array<int,16>r{};for(int j=1;j<16;j++)r[j]=rank8(M[j]);int improved=0,neutral=0;
 for(int a=1;a<256;a++)for(int b=1;b<256;b++){
  U p=outer(a,b);array<int,16>dr{};for(int j=1;j<16;j++)dr[j]=rank8(M[j]^p)-r[j];
  int dp[16][2],tmp[16][2];for(int v=0;v<16;v++)for(int e=0;e<2;e++)dp[v][e]=100000;dp[0][0]=0;
  for(int j=1;j<16;j++){memcpy(tmp,dp,sizeof dp);for(int k=0;k<16;k++)for(int e=0;e<2;e++)tmp[k^j][1]=min(tmp[k^j][1],dp[k][e]+dr[j]);memcpy(dp,tmp,sizeof dp);}
  int d=dp[0][1];evaluated++;improved+=d<0;neutral+=d==0;best=min(best,d);
 }
 cout<<"base="<<c<<" rank_one_updates="<<evaluated<<" supports_each=2047 total="<<evaluated*2047<<" best_delta="<<best<<" improved="<<improved<<" neutral="<<neutral<<endl;
 assert(evaluated==65025 && improved==0 && neutral==0);
}

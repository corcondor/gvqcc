// Replace triangular field divisions with recursive Toeplitz block updates.
// Every evaluation uses an existing control word; all shears are restored.
void rank_update(const Words &a,const Words &b,const Words &t,int x,const vector<int>&v){
 int k=0;while(k<(int)v.size()&&!v[k])++k;if(k==(int)v.size())return;
 int z=t[k];int w0=v[k];int iw=inv(w0);
 for(int i=1;i<(int)a.size();i++)w.fieldadd(a[i],a[0],power(x,i));
 for(int i=1;i<(int)b.size();i++)w.fieldadd(b[i],b[0],power(x,i));
 for(int i=0;i<(int)t.size();i++)if(i!=k)w.fieldadd(z,t[i],mul(v[i],iw));
 w.scale(a[0],w0);mx(a[0],b[0],z);w.scale(a[0],iw);
 for(int i=(int)t.size()-1;i>=0;i--)if(i!=k)w.fieldadd(z,t[i],mul(v[i],iw));
 for(int i=(int)b.size()-1;i>=1;i--)w.fieldadd(b[i],b[0],power(x,i));
 for(int i=(int)a.size()-1;i>=1;i--)w.fieldadd(a[i],a[0],power(x,i));
}
const int SS[]={0,0,1,1,2,1,2,3,4,3,4,3,4,5,6,7,8,7,8};
void quotient_cross(const Words&q,const Words&b,int m){
 int n=q.size();assert(n<=18&&m>0&&m<n&&(int)b.size()>=n-1);
 int L=n-1;while(M%L)++L;
 if(m*(n-m)<=L){
  for(int j=m;j<n;j++)for(int i=0;i<m;i++)mx(q[i],b[j-i-1],q[j]);
 }else{
  Words a=cut(q,0,m),d=cut(b,0,n-1),t=cut(q,m,n-m);
  for(int i=0;i<L;i++){
   int l=i*(M/L),x=ex[l];vector<int>v(n-m);
   for(int j=m;j<n;j++)v[j-m]=ex[(M-(l*(j-1))%M)%M];
   rank_update(a,d,t,x,v);
  }
 }
}
void quotient(const Words&q,const Words&b,bool rev){
 int n=q.size();if(n<=1)return;int m=SS[n];assert(m>0&&m<n);
 auto a=cut(q,0,m),c=cut(q,m,n-m);
 if(!rev){quotient(a,b,false);quotient_cross(q,b,m);quotient(c,b,false);}
 else {quotient(c,b,true);quotient_cross(q,b,m);quotient(a,b,true);}
}
void spectral_conv17(const Words&a,const Words&b,const Words&t){
 assert(a.size()==17&&b.size()==17&&t.size()==17);
 // Degree <=32. Lagrange interpolation is exact, only low 17 output words used.
 for(int x=0;x<33;x++){
  vector<int>v{1};int lead=1;
  for(int y=0;y<33;y++)if(x!=y){
   lead=mul(lead,x^y);vector<int>u(v.size()+1);
   for(int j=0;j<(int)v.size();j++){u[j]^=mul(y,v[j]);u[j+1]^=v[j];}
   v=u;
  }
  v.resize(17);int il=inv(lead);for(int &vv:v)vv=mul(vv,il);
  rank_update(a,b,t,x,v);
 }
}
void middle_update(const Words&a,const Words&b,const Words&t){
 int m=a.size(),n=t.size(),L=m+n-1;
 if(m==0||n==0)return;
 assert((int)b.size()==L);
 while(M%L)++L;
 if(m*n<=L){
  for(int j=0;j<n;j++)for(int i=0;i<m;i++)mx(a[i],b[j+m-1-i],t[j]);
 }else for(int i=0;i<L;i++){
  int l=i*(M/L),x=ex[l];vector<int>v(n);
  for(int j=0;j<n;j++)v[j]=ex[(M-(l*(j+m-1))%M)%M];
  rank_update(a,b,t,x,v);
 }
}
int odd_cost[19],odd_split[19];
void odd_plan(){
 for(int n=2;n<=18;n++){
  odd_cost[n]=9999;
  for(int m=1;m<n;m++){
   int c=odd_cost[m]+odd_cost[n-m];
   for(int r=0;r<2;r++){
    int a=(m+1-r)/2,b=(n+r)/2-(m+r)/2,L=a+b-1;
    // Number of j in [m,n) with j%2=1-r.
    b=0;for(int j=m;j<n;j++)if(j%2!=r)b++;
    if(!a||!b)continue;
    L=a+b-1;while(M%L)++L;c+=min(L,a*b);
   }
   if(c<odd_cost[n]){odd_cost[n]=c;odd_split[n]=m;}
  }
 }
}
void sparse_triangle(const Words&q,const Words&coeff){
 int n=q.size();if(n<=1)return;
 int m=odd_split[n];assert(m>0&&m<n);
 sparse_triangle(cut(q,m,n-m),coeff);
 for(int r=0;r<2;r++){
  Words a,b,t;vector<int>ai,tj;
  for(int i=0;i<m;i++)if(i%2==r){a.push_back(q[i]);ai.push_back(i);}
  for(int j=m;j<n;j++)if(j%2!=r){t.push_back(q[j]);tj.push_back(j);}
  if(a.empty()||t.empty())continue;
  int low=(tj.front()-ai.back()-1)/2,high=(tj.back()-ai.front()-1)/2;
  for(int i=low;i<=high;i++)b.push_back(coeff.at(i));
  middle_update(a,b,t);
 }
 sparse_triangle(cut(q,0,m),coeff);
}
// Keep the local evaluation and interpolation frames between rank-one terms.
// Switching frame anchor requires repaying the old frame first.
void rank_run(const Words&a,const Words&b,const Words&t,const vector<pair<int,vector<int>>>&terms){
 vector<int> u(a.size()),v(b.size()),c(t.size());int k=-1,scale=1;
 auto transport_out=[&](int next,const vector<int>&nc){
  if(k>=0&&k!=next){for(int i=0;i<(int)t.size();i++)if(i!=k)w.fieldadd(t[k],t[i],c[i]);fill(c.begin(),c.end(),0);}
  if(next>=0)for(int i=0;i<(int)t.size();i++)if(i!=next)w.fieldadd(t[next],t[i],c[i]^nc[i]);
  c=nc;k=next;
 };
 for(auto &[x,row]:terms){
  int j=0;while(j<(int)row.size()&&!row[j])j++;if(j==(int)row.size())continue;
  int g=row[j],nscale=mul(g,inv(scale)),ig=inv(g);
  w.scale(a[0],nscale);
  for(int i=1;i<(int)a.size();i++){int z=power(x,i);w.fieldadd(a[i],a[0],mul(z^u[i],g));u[i]=z;}
  scale=g;
  for(int i=1;i<(int)b.size();i++){int z=power(x,i);w.fieldadd(b[i],b[0],z^v[i]);v[i]=z;}
  vector<int>nc(t.size());for(int i=0;i<(int)t.size();i++)if(i!=j)nc[i]=mul(row[i],ig);
  transport_out(j,nc);
  mx(a[0],b[0],t[j]);
 }
 transport_out(-1,vector<int>(t.size()));
 w.scale(a[0],inv(scale));
 for(int i=1;i<(int)a.size();i++)w.fieldadd(a[i],a[0],u[i]);
 for(int i=1;i<(int)b.size();i++)w.fieldadd(b[i],b[0],v[i]);
}

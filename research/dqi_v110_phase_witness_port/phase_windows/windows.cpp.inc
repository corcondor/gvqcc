#include "seam_layout.inc"
Words parity(const Words &x,int bit,int n){Words y;for(int i=0;i<n;i++)y.push_back(x.at(2*i+bit));return y;}
// t[j] ^= coefficient j+offset of a*b. No dedicated evaluations or output product words.
void product_window(Words a, Words b, const Words&t, int offset, bool reverse){
 assert(!a.empty()&&!b.empty());
 if(reverse){std::reverse(a.begin(),a.end());std::reverse(b.begin(),b.end());}
 vector<int> used;
 for(auto L:{a,b,t})for(int q:L)for(int i=q;i<q+12;i++){
  assert(i>=0&&i<900);assert(find(used.begin(),used.end(),i)==used.end());used.push_back(i);
 }
 int n=a.size()+b.size()-1; vector<pair<int,vector<int>>> terms;
 for(int x=0;x<n;x++){
  vector<int>p{1};int lead=1;
  for(int y=0;y<n;y++)if(x!=y){
   vector<int>r(p.size()+1);
   for(int j=0;j<(int)p.size();j++){r[j]^=mul(y,p[j]);r[j+1]^=p[j];}
   p=r;lead=mul(lead,x^y);
  }
  vector<int>v(t.size());
  for(int j=0;j<(int)t.size();j++){assert(j+offset<n);v[j]=mul(p[j+offset],inv(lead));}
  terms.emplace_back(x,v);
 }
 rank_run(a,b,t,terms);
}
int main(int argc,char**argv){
 assert(argc==4);int x=1;
 for(int i=0;i<M;i++){ex[i]=ex[i+M]=x;lg[x]=i;x<<=1;if(x&F)x^=0x1053;}assert(x==1);
 string s=argv[1];int k=stoi(argv[2]);assert(k==0||k==1);
 Words a=parity(Dword,0,17),b=parity(Nword,k,18-k),t=parity(Nword,1-k,17);
 int h=0;bool rev=false;
 if(s=="high"){h=17;t.resize(17-k);}
 else if(s=="revq"){a.resize(17-k);b.resize(17-k);t.resize(17-k);rev=true;}
 else if(s=="red"){a=parity(Dword,1,17);b.resize(17-k);}
 else assert(s=="low");
 product_window(a,b,t,h,rev);w.save(argv[3]);
}

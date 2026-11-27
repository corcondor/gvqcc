"""Extend #171's native additive scan with a coherent half-degree magnitude frame.
The input is (D, q0, T, U), not 70 syndromes. All arithmetic is native KMB.
Upstream field scan: corcondor/gvqcc PR171 d442f725; scalar tensor: PR237 a52fe81.
"""
from pathlib import Path
import ast,hashlib
src=Path("emit_opt.cpp").read_text()
codes=next(ast.literal_eval(n.value) for n in ast.parse(Path("crt882.py").read_text()).body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="CODES" for x in n.targets))
assert len(codes)==510 and sum(c>=4096 for c in codes)==42
src=src.replace("#include <bits/stdc++.h>", "#include <algorithm>\n#include <array>\n#include <cassert>\n#include <cstdint>\n#include <fstream>\n#include <iostream>\n#include <map>\n#include <string>\n#include <vector>\n#include <utility>")
src=src.replace("struct W{vector<uint8_t> c[10];","struct W{vector<G> tape; bool record=false; vector<uint8_t> c[10];")
src=src.replace("void add(G g){c[1]", "void add(G g){if(record)tape.push_back(g);c[1]")
src=src.replace('reg("P"+to_string(i)', 'reg("D"+to_string(i)').replace('reg("V"+to_string(i)', 'reg("H"+to_string(i)')
old="for(int b=0;b<12;b++)w.add({160,850,420+b,-1,0,I(j*12+b)});"
new="for(int i=0;i<12;i++){int v=mul(1<<i,inv(x));for(int b=0;b<12;b++)if(v>>b&1)w.add({160,850,420+i,-1,0,I(j*12+b)});}"
assert old in src
src=src.replace(old,new)
tail=r'''
using Words=vector<int>;
const int CODES[]={__CODES__};
void wx(int a,int b){assert(a!=b);for(int k=0;k<12;k++)w.cx(a+k,b+k);}
void ws(int a,int b){for(int k=0;k<12;k++)w.sw(a+k,b+k);}
void mx(int a,int b,int t){assert(a!=b&&a!=t&&b!=t);int q[36];for(int i=0;i<12;i++){q[i]=a+i;q[i+12]=b+i;q[i+24]=t+i;}
 for(int c:CODES){int x=q[c%64],y=q[(c/64)%64];if(c<4096)w.cx(x,y);else w.add({49,x,y,q[c/4096-1]});}}
void frob(int q,int e){int rows[12]={};for(int i=0;i<12;i++){int z=power(1<<i,e);for(int j=0;j<12;j++)if(z>>j&1)rows[j]|=1<<i;}vector<G> g;
 for(int j=0;j<12;j++){int r=j;while(r<12&&!(rows[r]>>j&1))r++;assert(r<12);if(r!=j){swap(rows[r],rows[j]);g.push_back({34,q+r,q+j});}for(int i=0;i<12;i++)if(i!=j&&(rows[i]>>j&1)){rows[i]^=rows[j];g.push_back({33,q+j,q+i});}}
 for(int i=0;i<12;i++)assert(rows[i]==1<<i);for(auto it=g.rbegin();it!=g.rend();++it)w.add(*it);}
Words cut(const Words& x,int i,int n){assert(i+n<=int(x.size()));return Words(x.begin()+i,x.begin()+i+n);}
void full(const Words&a,const Words&b,const Words&t){
 int n=a.size();assert(b.size()==a.size()&&t.size()==2*a.size()-1);
 if(n==1){mx(a[0],b[0],t[0]);return;}assert(n%2==0);int m=n/2,h=2*m-1;
 Words a0=cut(a,0,m),a1=cut(a,m,m),b0=cut(b,0,m),b1=cut(b,m,m);
 // Copy low product into both offsets 0,m using conjugated output shear.
 for(int i=0;i<h;i++)wx(t[i],t[m+i]);full(a0,b0,cut(t,0,h));for(int i=h-1;i>=0;i--)wx(t[i],t[m+i]);
 // Copy high product into both offsets 2m,m.
 for(int i=h-1;i>=0;i--)wx(t[2*m+i],t[m+i]);full(a1,b1,cut(t,2*m,h));for(int i=0;i<h;i++)wx(t[2*m+i],t[m+i]);
 for(int i=0;i<m;i++){wx(a1[i],a0[i]);wx(b1[i],b0[i]);}
 full(a0,b0,cut(t,m,h));
 for(int i=m-1;i>=0;i--){wx(b1[i],b0[i]);wx(a1[i],a0[i]);}
}
void trunc(const Words&a,const Words&b,const Words&t){
 int n=a.size();assert(b.size()==a.size()&&t.size()==a.size());
 if(n==1){mx(a[0],b[0],t[0]);return;}assert(n%2==0);int m=n/2;
 Words a0=cut(a,0,m),a1=cut(a,m,m),b0=cut(b,0,m),b1=cut(b,m,m);
 for(int i=0;i<m;i++)wx(t[i],t[m+i]);full(a0,b0,cut(t,0,2*m-1));for(int i=0;i<m;i++)wx(t[i],t[m+i]);
 for(int i=0;i<m;i++){wx(a1[i],a0[i]);wx(b1[i],b0[i]);}
 trunc(a0,b0,cut(t,m,m));
 for(int i=m-1;i>=0;i--){wx(b1[i],b0[i]);wx(a1[i],a0[i]);}
 trunc(a1,b1,cut(t,m,m));
}
void conv17(const Words&a,const Words&b,const Words&t){
 assert(a.size()==17&&b.size()==17&&t.size()==17);
 trunc(cut(a,0,16),cut(b,0,16),cut(t,0,16));for(int i=0;i<17;i++)mx(a[i],b[16-i],t[16]);
}
int aa(int j){return 24*j;}int bb(int j){return 24*j+12;}int h(int j){return 420+12*j;}
void magnitude(){
 // D = A^2+X B^2, monic B of degree17. Encode quotient q=A/B at infinity.
 for(int i=0;i<35;i++)frob(12*i,2048);
 for(int i=0;i<17;i++)for(int k=1;k<=17-i;k++)mx(aa(17-i),bb(17-k),aa(17-i-k));
 Words q,T,U,V0;for(int i=0;i<17;i++){q.push_back(aa(17-i));T.push_back(h(17-i));U.push_back(h(34-i));V0.push_back(h(16-i));}
 // H = [q0,T0..T16,U0..U16]. U <- U+Q(T).
 conv17(q,T,U);
 // V0=q0+X*T+Q^2(T)+Q(V1), where V1=U+Q(T).
 // Q^2 has only even coefficients in characteristic two.
 for(int i=0;i<=8;i++)frob(q[i],2);
 for(int j=0;j<17;j++)for(int i=0;2*i<=j;i++)mx(q[i],h(j+1),h(j-2*i));
 for(int i=0;i<=8;i++)frob(q[i],2048);
 conv17(q,U,V0);
 for(int i=16;i>=0;i--)for(int k=17-i;k>=1;k--)mx(aa(17-i),bb(17-k),aa(17-i-k));
 for(int i=0;i<35;i++){frob(12*i,2);frob(h(i),2);}
 vector<int> dst(35);for(int i=0;i<=17;i++)dst[i]=2*i;for(int i=0;i<17;i++)dst[18+i]=2*i+1;
 for(int i=0;i<35;i++)while(dst[i]!=i){int j=dst[i];ws(h(i),h(j));swap(dst[i],dst[j]);}
}
'''
tail=tail.replace("__CODES__",",".join(map(str,codes)))
src=src[:src.index("int main(")]+tail+r'''
int main(int argc,char**argv){
 int x=1;for(int i=0;i<M;i++){ex[i]=ex[i+M]=x;lg[x]=i;x<<=1;if(x&F)x^=0x1053;}assert(x==1);
 string mode=argv[1];
 w.record=true;magnitude();w.record=false;
 cerr<<"magnitude forward paid "<<w.cc<<" ops "<<w.c[1].size()<<endl;
 if(mode=="forward"){w.save(argv[2]);return 0;}
 if(mode=="reverse"){vector<G> rev=w.tape; // rebuild writer to emit only inverse
  w=W();for(auto it=rev.rbegin();it!=rev.rend();++it)w.add(*it);w.save(argv[2]);return 0;}
 if(mode=="half"){
  ifstream f("plan.txt");for(int&i:betav)f>>i;for(int i=0;i<12;i++){f>>basis[i];assert(basis[i]==(1<<i));}
  for(int i=0;i<=N;i++)for(int j=0;j<=i;j++)f>>B[i][j];for(auto&row:S)for(int&i:row)f>>i;assert(f);
  basischange(false);for(int i=0;i<12;i++)w.x(i);dfs(12,0);for(int i=0;i<12;i++)w.x(i);basischange(true);assert(nleaves==M);
 }else assert(mode=="roundtrip");
 for(auto it=w.tape.rbegin();it!=w.tape.rend();++it)w.add(*it);
 w.save(argv[2]);
}
'''
Path("half_magnitude.cpp").write_text(src)
print("source",hashlib.sha256(src.encode()).hexdigest())


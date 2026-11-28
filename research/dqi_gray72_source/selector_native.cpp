// Standalone bit-sliced execution of the recovered native selector emitter.
#include <bits/stdc++.h>
using namespace std; using U=uint32_t; using L=uint64_t;
struct Gate { unsigned char op=0; U a=0,b=0,t=0,bit=0,cond=0; };
struct Plan{U anchor;array<U,12> col;vector<pair<U,array<U,12>>> rows;};
struct Extra {
 struct Counter { L n=0; L size() const {return n;} } ops;
 vector<L> bits; vector<L> stack{~L(0)};
 explicit Extra(U n):bits(n){}
 void put(Gate g){++ops.n; if(g.op==129){stack.push_back(stack.back()&bits.at(g.cond));return;} if(g.op==1){assert(stack.size()>1);stack.pop_back();return;} L a=stack.back();if(g.op&128)a&=bits.at(g.cond);switch(g.op&127){case 64:bits.at(g.bit)&=~a;break;case 65:bits.at(g.bit)|=a;break;case 66:bits.at(g.bit)^=a;break;default:abort();}}
 void set(U base,U lane,U word){for(U k=0;k<12;k++)if(word>>k&1)bits[base+k]|=L(1)<<lane;}
 U get(U base,U lane){U z=0;for(U k=0;k<12;k++)z|=U(bits[base+k]>>lane&1)<<k;return z;}
};
int main(int argc,char**argv){assert(argc==4);ifstream f(argv[1]);int N;f>>N;vector<Plan> plans(N);for(auto &p:plans){f>>p.anchor;for(auto &x:p.col)f>>x;p.rows.resize(1024);for(auto &[i,a]:p.rows){f>>i;for(auto &x:a)f>>x;}}array<U,4025> coeff;for(auto &v:coeff)f>>v;assert(f);
constexpr L cut=112234734;
constexpr U NORMAL=154959,oldsel=693595,oldbest=693607,candmu=693619; constexpr int SAMPLE=1024,K=4,CB=4;
U WORDS=693867,anch=WORDS+12*4096,count=anch+12,gt=count+12,run=gt+1,nzflag=gt+2,sat=gt+3,sc=gt+4,topword=sc+CB,topcount=topword+12*K,pword=topcount+CB*K,pcount=pword+12,last=pcount+CB,delta=last+12,flags=delta+12,work=flags+4024, prevmu=work+12*4025, prevlam=prevmu+12, lam=prevlam+12, du=lam+12, pred=du+12, basis=pred+12, endbits=basis+144;Extra w(endbits);
ifstream in(argv[2]); U lanes;in>>lanes;assert(lanes>0&&lanes<=64);for(U i=0;i<lanes;i++){U oldscore,lambda,mu;in>>oldscore>>lambda>>mu;w.set(oldbest,i,oldscore);w.set(oldsel,i,lambda);w.set(candmu,i,mu);for(U j=0;j<4024;j++){U x;in>>x;w.set(NORMAL+12*j,i,x);}}assert(in);
auto z=[&](U bit){w.put({64,0,0,0,bit});};auto one=[&](U bit){w.put({65,0,0,0,bit});};auto flip=[&](U bit){w.put({66,0,0,0,bit});};auto x=[&](U a,U b){w.put({194,0,0,0,b,a});};auto clearif=[&](U b,U a){w.put({192,0,0,0,b,a});};auto push=[&](U b){w.put({129,0,0,0,0,b});};auto pop=[&](){w.put({1});};auto clearword=[&](U a){for(U k=0;k<12;k++)z(a+k);};auto copy=[&](U a,U b){for(U k=0;k<12;k++){z(b+k);x(a+k,b+k);}};
auto compare=[&](U a,U b,U flag){z(flag);for(U k=0;k<12;k++){x(a+k,b+k);x(a+k,flag);clearif(flag,b+k);x(a+k,flag);x(a+k,b+k);}};
auto equal=[&](U a,U b,U flag){one(flag);for(U k=0;k<12;k++){x(a+k,b+k);clearif(flag,b+k);x(a+k,b+k);}};
auto nz=[&](U a,U flag){z(flag);for(U k=0;k<12;k++)w.put({193,0,0,0,flag,a+k});};
auto increment=[&](U a,int n=12){for(int k=0;k<n-1;k++)push(a+k);flip(a+n-1);for(int k=n-2;k>=0;k--){pop();flip(a+k);}};
auto setone=[&](U a){clearword(a);one(a);};bool prune=true;L skipped=0;auto exchange=[&](int i,int j){if(prune&&j>=SAMPLE){skipped++;return;}U a=WORDS+12*i,b=WORDS+12*j;z(gt);for(U k=0;k<12;k++){x(a+k,b+k);x(a+k,gt);clearif(gt,b+k);x(a+k,gt);}push(gt);for(U k=0;k<12;k++)x(b+k,a+k);pop();for(U k=0;k<12;k++)x(a+k,b+k);};
function<void(int,int,int)> merge=[&](int first,int n,int gap){int step=2*gap;if(step==n)exchange(first,first+gap);else{merge(first,n,step);merge(first+gap,n,step);for(int i=first+gap;i<first+n-gap;i+=step)exchange(i,i+gap);}};
function<void(int,int)> sort=[&](int first,int n){if(n>1){sort(first,n/2);sort(first+n/2,n/2);merge(first,n,1);}};
using Cx=pair<int,int>; map<array<U,12>,vector<Cx>> frames;
auto frame=[&](array<U,12> m)->vector<Cx> const&{auto hit=frames.find(m);if(hit!=frames.end())return hit->second;vector<Cx> best;bool first=true;
 for(int mode=0;mode<7;mode++){auto rows=m;vector<Cx> g;auto add=[&](int a,int b){assert(a!=b);rows[b]^=rows[a];g.push_back({a,b});};
 if(mode<=1){array<int,12> ord;for(int k=0;k<12;k++)ord[k]=mode==0?k:11-k;for(int j:ord){if(!(rows[j]>>j&1)){int k=j+(mode==0?1:-1);while(k>=0&&k<12&&!(rows[k]>>j&1))k+=(mode==0?1:-1);assert(k>=0&&k<12);add(k,j);}for(int i=0;i<12;i++)if(i!=j&&(rows[i]>>j&1))add(j,i);}}
 else{int block=mode-1;for(int s=0;s<12;s+=block){int e=min(12,s+block);U mask=(1U<<(e-s))-1;map<U,int> seen;for(int i=s;i<12;i++){U v=(rows[i]>>s)&mask;if(!v)continue;if(seen.count(v))add(seen[v],i);else seen[v]=i;}
 for(int j=s;j<e;j++){if(!(rows[j]>>j&1)){int k=j+1;while(k<12&&!(rows[k]>>j&1))k++;assert(k<12);add(k,j);add(j,k);add(k,j);}for(int i=j+1;i<12;i++)if(rows[i]>>j&1)add(j,i);}}
 for(int e=12;e>0;e-=block){int s=max(0,e-block);U mask=(1U<<(e-s))-1;map<U,int> seen;for(int i=e-1;i>=0;i--){U v=(rows[i]>>s)&mask;if(!v)continue;if(seen.count(v))add(seen[v],i);else seen[v]=i;}
 for(int j=e-1;j>=s;j--){if(!(rows[j]>>j&1)){int k=j-1;while(k>=0&&!(rows[k]>>j&1))k--;assert(k>=0);add(k,j);add(j,k);add(k,j);}for(int i=0;i<j;i++)if(rows[i]>>j&1)add(j,i);}}}
 bool ok=true;for(int j=0;j<12;j++)ok=ok&&(rows[j]==(1U<<j));if(!ok)continue;reverse(g.begin(),g.end());if(first||g.size()<best.size()){best=move(g);first=false;}}
 assert(!first);array<U,12> test;for(int j=0;j<12;j++)test[j]=1U<<j;for(auto [a,b]:best)test[b]^=test[a];assert(test==m);return frames.emplace(m,move(best)).first->second;};
L old_slope_ops=0,new_slope_ops=0;
auto slope=[&](U i,U dst,array<U,12> const &m){L n=w.ops.size();for(U k=0;k<12;k++){z(dst+k);if(i<4024)x(NORMAL+12*i+k,dst+k);x(anch+k,dst+k);}for(auto [a,b]:frame(m))x(dst+a,dst+b);new_slope_ops+=w.ops.size()-n;old_slope_ops+=12*(i<4024?4:3);for(auto r:m)old_slope_ops+=__builtin_popcount(r);};
auto negcond=[](U a){return a|0x80000000U;};
auto set1short=[&](U v){for(int k=0;k<CB;k++)z(v+k);one(v);};
auto incshort=[&](){one(sat);for(int k=0;k<CB;k++){flip(sc+k);clearif(sat,sc+k);flip(sc+k);}flip(sat);push(sat);increment(sc,CB);pop();};
auto insert=[&](U a){nz(a,nzflag);push(nzflag);copy(a,pword);for(int k=0;k<CB;k++){z(pcount+k);x(sc+k,pcount+k);}for(int j=0;j<K;j++){U A=pcount,B=topcount+CB*j;z(gt);for(int k=0;k<CB;k++){x(A+k,B+k);x(A+k,gt);clearif(gt,B+k);x(A+k,gt);}push(gt);for(int k=0;k<CB;k++)x(B+k,A+k);for(int k=0;k<12;k++){U u=pword+k,v=topword+12*j+k;x(u,v);x(v,u);x(u,v);}pop();for(int k=0;k<CB;k++)x(A+k,B+k);}pop();};
auto exact_popcount=[&](){array<vector<U>,13> bins;for(U j=0;j<4024;j++)bins[0].push_back(flags+j);for(int k=0;k<12;k++){auto &b=bins[k];while(b.size()>=3){U a=b.back();b.pop_back();U d=b.back();b.pop_back();U c=b.back();b.pop_back();x(a,d);x(c,a);clearif(a,d);x(c,a);x(c,d);b.push_back(d);bins[k+1].push_back(a);}if(b.size()==2){U a=b.back();b.pop_back();U d=b.back();x(a,d);clearif(a,d);bins[k+1].push_back(a);}z(count+k);if(!b.empty())x(b[0],count+k);}assert(bins[12].empty());};
array<int,4096> lookup;lookup.fill(-1);for(int i=0;i<4025;i++){assert(lookup[coeff[i]]<0);lookup[coeff[i]]=i;if(i<4024)copy(NORMAL+12*i,work+12*i);else clearword(work+12*i);}clearword(prevlam);clearword(prevmu);
for(auto &p:plans){L n=w.ops.size();copy(NORMAL+12*p.anchor,anch);for(int j=0;j<SAMPLE;j++)slope(p.rows[j].first,WORDS+12*j,p.rows[j].second);L s0=w.ops.size();sort(0,1024);L s1=w.ops.size();for(U k=topword;k<topcount+CB*K;k++)z(k);set1short(sc);
 for(int j=1;j<SAMPLE;j++){U a=WORDS+12*(j-1),b=WORDS+12*j;equal(a,b,run);flip(run);push(run);insert(a);set1short(sc);pop();flip(run);push(run);incshort();pop();}insert(WORDS+12*(SAMPLE-1));L s2=w.ops.size();
 for(int j=0;j<K;j++){U a=topword+12*j;copy(anch,lam);for(U i=0;i<12;i++)for(U k=0;k<12;k++)if(p.col[i]>>k&1)x(a+k,lam+i);
 for(U k=0;k<12;k++){z(du+k);x(a+k,du+k);x(prevmu+k,du+k);z(pred+k);x(lam+k,pred+k);x(prevlam+k,pred+k);}copy(du,basis);
 for(U d=1;d<12;d++){U u=basis+12*(d-1),v=basis+12*d;clearword(v);for(U k=0;k<11;k++)x(u+k+1,v+k);for(U k=0;k<12;k++)if((0x53>>k)&1)x(u+k,v+11);}
 U num=0;for(int q=0;q<4096;q++){if(q){int k=__builtin_ctz(unsigned(q));for(U l=0;l<12;l++)x(basis+12*k+l,pred+l);}int i=lookup[q^(q>>1)];if(i<0)continue;U t=work+12*i;for(U k=0;k<12;k++)x(pred+k,t+k);if(i==int(p.anchor))continue;U flag=flags+num++;one(flag);for(U k=0;k<12;k++)clearif(flag,t+k);}assert(num==4024);
 exact_popcount();compare(count,oldbest,gt);nz(a,nzflag);push(gt);push(nzflag);copy(count,oldbest);copy(a,candmu);copy(lam,oldsel);pop();pop();copy(a,prevmu);copy(lam,prevlam);}
 cerr<<"anchor "<<p.anchor<<" total "<<w.ops.size()-n<<" slope "<<s0-n<<" sort "<<s1-s0<<" select "<<s2-s1<<" confirm "<<w.ops.size()-s2<<"\n";}
for(U k=WORDS;k<endbits;k++)z(k);
assert(w.stack.size()==1);ofstream out(argv[3]);for(U i=0;i<lanes;i++)out<<w.get(oldbest,i)<<" "<<w.get(oldsel,i)<<" "<<w.get(candmu,i)<<"\n";out.close();cerr<<"native selector emitted operations="<<w.ops.size()<<" classical bits="<<endbits<<"\n";}

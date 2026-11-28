#include <bits/stdc++.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
using namespace std;using U=uint32_t;using L=uint64_t;
struct Packet{const char*ptr=nullptr;L len=0;};
struct Gate {unsigned char op=0;U a=0,b=0,t=0,bit=0,cond=0;bool operator==(const Gate&g)const{return op==g.op&&a==g.a&&b==g.b&&t==g.t&&bit==g.bit&&cond==g.cond;}};
struct Reader {char*data;L size;U Q,B,Nreg;L counts[9];array<Packet,12>P;vector<Packet> regs;L idx[12]={};
 Reader(string p){int fd=open(p.c_str(),O_RDONLY);assert(fd>=0);struct stat st;fstat(fd,&st);size=st.st_size;data=(char*)mmap(nullptr,size,PROT_READ,MAP_PRIVATE,fd,0);assert(data!=MAP_FAILED);close(fd);assert((unsigned char)data[0]==0xd7);U h[4];memcpy(h,data+16,16);assert(h[0]==2);Q=h[1];B=h[2];Nreg=h[3];memcpy(counts,data+32,72);L off=104;while(off<size){L t,n;memcpy(&t,data+off,8);memcpy(&n,data+off+8,8);off+=16;assert(t<12&&off+n<=size);if(t==0)regs.push_back({data+off,n});else {assert(!P[t].ptr);P[t]={data+off,n};}off+=n;}assert(regs.size()==Nreg&&P[1].len==counts[0]);}
 U get(int i){U x;assert((idx[i]+1)*4<=P[i].len);memcpy(&x,P[i].ptr+4*idx[i]++,4);return x;}
 Gate read(L i){Gate g;g.op=(unsigned char)P[1].ptr[i];int n=(g.op&0x30)>>4;int base=g.op&127;if(n==3){g.a=get(2);g.b=get(3);g.t=get(4);}else if(n==2){g.a=get(5);g.b=get(6);}else if(n==1)g.a=get(7);if((g.op&64)&&base!=6&&base!=7)g.bit=get(8);if(g.op&128)g.cond=get(9);return g;}
 void reset(){fill(begin(idx),end(idx),0);}
};
#include <functional>
struct Plan{U anchor;array<U,12> col;vector<pair<U,array<U,12>>> rows;};
struct Extra {
 vector<unsigned char> ops; array<vector<U>,10> a;
 Extra(){ops.reserve(110000000);a[8].reserve(100000000);a[9].reserve(100000000);}
 void put(Gate g){assert((g.op&48)==0);ops.push_back(g.op);int base=g.op&127;if((g.op&64)&&base!=6&&base!=7)a[8].push_back(g.bit);if(g.op&128)a[9].push_back(g.cond);}
 void write(Reader&r,string p,L cut,U bits){r.reset();int depth=0;for(L i=0;i<cut;i++){Gate g=r.read(i);if(g.op==129)depth++;if(g.op==1)depth--;}assert(depth==1);L off[12]={};off[1]=cut;for(int i=2;i<=9;i++)off[i]=4*r.idx[i];for(int i=10;i<=11;i++)off[i]=r.P[i].len;
 ofstream o(p,ios::binary);assert(o);o.write(r.data,16);U h[4]={2,r.Q,bits,r.Nreg};o.write((char*)h,16);L c[9];copy(r.counts,r.counts+9,c);c[0]+=ops.size();c[4]+=a[8].size();c[5]+=a[9].size();o.write((char*)c,72);
 auto packet=[&](L t,const char*d,L n){o.write((char*)&t,8);o.write((char*)&n,8);if(n)o.write(d,n);};for(auto v:r.regs)packet(0,v.ptr,v.len);
 for(L t=1;t<=11;t++){const char *p=t==1?(char*)ops.data():t<=9?(char*)a[t].data():nullptr;L n=t==1?ops.size():t<=9?a[t].size()*4:0;L total=r.P[t].len+n;o.write((char*)&t,8);o.write((char*)&total,8);if(off[t])o.write(r.P[t].ptr,off[t]);if(n)o.write(p,n);if(r.P[t].len>off[t])o.write(r.P[t].ptr+off[t],r.P[t].len-off[t]);}assert(o.good());cerr<<"Q="<<r.Q<<" B="<<bits<<" ops="<<c[0]<<" ternary="<<c[1]<<" inserted="<<ops.size()<<"\n";
 }
};
int main(int argc,char**argv){assert(argc==4);Reader r(argv[1]);assert(r.Q==900&&r.B==693867&&r.counts[0]==158265814);ifstream f(argv[2]);int N;f>>N;vector<Plan> plans(N);for(auto &p:plans){f>>p.anchor;for(auto &x:p.col)f>>x;p.rows.resize(1024);for(auto &[i,a]:p.rows){f>>i;for(auto &x:a)f>>x;}}array<U,4025> coeff;for(auto &v:coeff)f>>v;assert(f);
constexpr L cut=112234734;
constexpr U NORMAL=154959,oldsel=693595,oldbest=693607,candmu=693619; constexpr int SAMPLE=1024,K=4,CB=4;
U WORDS=r.B,anch=WORDS+12*4096,count=anch+12,gt=count+12,run=gt+1,nzflag=gt+2,sat=gt+3,sc=gt+4,topword=sc+CB,topcount=topword+12*K,pword=topcount+CB*K,pcount=pword+12,last=pcount+CB,delta=last+12,flags=delta+12,work=flags+4024, prevmu=work+12*4025, prevlam=prevmu+12, lam=prevlam+12, du=lam+12, pred=du+12, basis=pred+12, endbits=basis+144;Extra w;
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
w.write(r,argv[3],cut,endbits);}

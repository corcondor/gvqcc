#include "common.hpp"
using Bytes=vector<unsigned char>;
Bytes readb(string f){ifstream i(f,ios::binary);assert(i);return Bytes(istreambuf_iterator<char>(i),{});}
vector<U> readi(string f){ifstream i(f);assert(i);vector<U> a;U v;while(i>>v)a.push_back(v);return a;}
L bit(const Bytes&b,U i){return (b.at(i/8)>>(i%8))&1;}
struct Res{L phase; vector<L> act,q,b;};
Res replay(Reader&r,const vector<L>& M,vector<L> q,vector<L>b){
 r.reset();vector<L>stack{~L(0)},act(M.size());L phase=0;U h=0;
 for(L i=0;i<r.counts[0];i++){
 Gate g=r.read(i);int op=g.op&127;if(g.op==0x81){stack.push_back(stack.back()&b[g.cond]);continue;}if(g.op==1){assert(stack.size()>1);stack.pop_back();continue;}
 L k=stack.back();if(g.op&128)k&=b[g.cond];U a=g.a,d=g.b,t=g.t;L delta;
 switch(op){case 0x11:q[a]^=k;break;case 0x12: act[h]=k;phase^=k&M.at(h++)&q[a];q[a]&=~k;break;case 0x21:q[d]^=k&q[a];break;case 0x22:delta=k&(q[a]^q[d]);q[a]^=delta;q[d]^=delta;break;case 0x31:q[t]^=k&q[a]&q[d];break;case 0x32:delta=k&q[a]&(q[d]^q[t]);q[d]^=delta;q[t]^=delta;break;case 0x50:{act[h]=k;L m=M.at(h++);phase^=k&m&q[a];b[g.bit]=(b[g.bit]&~k)|(m&k);q[a]&=~k;break;}case 0x40:b[g.bit]&=~k;break;case 0x41:b[g.bit]|=k;break;case 0x42:b[g.bit]^=k;break;case 0:phase^=k;break;case 0x10:phase^=k&q[a];break;case 0x20:phase^=k&q[a]&q[d];break;case 0x30:phase^=k&q[a]&q[d]&q[t];break;case 6:break;default:cerr<<"unsupported "<<op<<endl;abort();}

 }
 assert(h==M.size() && stack.size()==1);
 return {phase,move(act),move(q),move(b)};
}
int main(int argc,char** argv){
 assert(argc==2);Reader r(argv[1]);auto qids=readi("qids.txt"),bids=readi("bids.txt"),pos=readi("probe_order.txt");
 ifstream lm("layout.txt");U base=0,H=0;lm>>base>>H;assert(base==r.B&&H>0);
 auto in=readb("input.raw"),raw0=readb("mask_0.raw"),raw1=readb("mask_1.raw"),ph0=readb("phase_0.raw"),ph1=readb("phase_1.raw");
 U N=pos.size()*12,s=(N+7)/8;
 assert(raw0.size()==2*H*s&&raw1.size()==raw0.size());
 vector<U> y0;
 for(U j=0;j<N;j+=64){
 U n=min<U>(64,N-j);L bound=n==64?~L(0):(L(1)<<n)-1;
 auto block=[&](const Bytes&x,U offset){L u=0;for(U p=0;p<n;p++)u|=bit(x,offset+j+p)<<p;return u;};
 vector<L> a0(H),a1(H),m0(H),m1(H),q(r.Q),b(r.B),hot(r.B);
 for(U h=0;h<H;h++){a0[h]=block(raw0,2*h*s*8);a1[h]=block(raw1,2*h*s*8);m0[h]=block(raw0,(2*h+1)*s*8);m1[h]=block(raw1,(2*h+1)*s*8);}
 for(U i=0;i<qids.size();i++)q[qids[i]]=bit(in,i)?bound:0;
 for(U i=0;i<n;i++){U t=j+i;hot[bids[12*pos[t/12]+t%12]]|=L(1)<<i;}
 auto z0=replay(r,m0,q,b),z1=replay(r,m1,q,hot);
 assert((z0.phase&bound)==block(ph0,0) && (z1.phase&bound)==block(ph1,0));
 for(U h=0;h<H;h++)assert((z0.act[h]&bound)==a0[h]&&(z1.act[h]&bound)==a1[h]);
 if(y0.empty()){for(U l=0;l<70;l++){U v=0;for(U k=0;k<12;k++)v|=(z0.q[qids[l*12+k]]&1)<<k;y0.push_back(v);}for(U x:y0)cerr<<x<<' ';cerr<<'\n';}
 vector<L> common(H);
 for(U h=0;h<H;h++){assert(!((m0[h]^m1[h])&a0[h]&a1[h]));common[h]=(m0[h]&a0[h])|(m1[h]&a1[h]);}
 auto common0=replay(r,common,q,b),common1=replay(r,common,q,hot);
 assert(((z0.phase^common0.phase)&bound)==0 && ((z1.phase^common1.phase)&bound)==0);
 for(U h=0;h<H;h++)assert((common0.act[h]&bound)==a0[h]&&(common1.act[h]&bound)==a1[h]);
 for(U i:qids)assert(((z0.q[i]^common0.q[i])&bound)==0&&((z1.q[i]^common1.q[i])&bound)==0);
 auto y1=replay(r,m0,q,hot),y2=replay(r,m1,q,b);
 L d0=(z0.phase^y1.phase)&bound,d1=(y2.phase^z1.phase)&bound;
 L dy0=0,dy1=0;
 for(U i:qids){dy0|=z0.q[i]^y1.q[i];dy1|=y2.q[i]^z1.q[i];}
 cout<<j<<' '<<n<<' '<<d0<<' '<<d1<<' '<<(dy0&bound)<<' '<<(dy1&bound)<<'\n'<<flush;
 }
}

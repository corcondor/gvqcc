#include <bits/stdc++.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
using namespace std;using U=uint64_t;using I=uint32_t;
struct G{I i; int t,a=-1,b=-1,c=-1;I m=0,k=0;};
struct S{U k,n;const unsigned char*p;};
struct K{int fd;size_t sz;unsigned char*p;vector<S> sections;const unsigned char* col[12]={};U len[12]={},pos[12]={};int Q,B;U N;K(string f){fd=open(f.c_str(),O_RDONLY);if(fd<0)throw runtime_error(f);struct stat st;fstat(fd,&st);sz=st.st_size;p=(unsigned char*)mmap(0,sz,PROT_READ,MAP_PRIVATE,fd,0);memcpy(&Q,p+20,4);memcpy(&B,p+24,4);memcpy(&N,p+32,8);for(U o=104;o<sz;){U k,n;memcpy(&k,p+o,8);memcpy(&n,p+o+8,8);o+=16;assert(o+n<=sz);sections.push_back({k,n,p+o});if(k&&k<12){col[k]=p+o;len[k]=n;}o+=n;}assert(len[1]==N);}I take(int k){I a;memcpy(&a,col[k]+4*pos[k]++,4);return a;}G next(I i){G g{i,col[1][i]};int t=g.t;switch((t>>4)&3){case 1:g.a=take(7);break;case 2:g.a=take(5);g.b=take(6);break;case 3:g.a=take(2);g.b=take(3);g.c=take(4);break;}if(t&64)g.m=take(8);if(t&128)g.k=take(9);return g;}void reset(){fill(pos,pos+12,0);} };

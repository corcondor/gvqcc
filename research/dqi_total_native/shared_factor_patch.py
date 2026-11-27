"""Third joint pass: multiword HMR debt pooling and masked-factor reuse."""
from pathlib import Path
p=Path("total.cpp.in");s=p.read_text()
pos=s.index("void swap_pivot(")
s=s[:pos]+r'''
constexpr int BB=49153,BE=BB+840;
void batch_scale(int p,int count,int mult,int inverse){
 if(count<=2){for(int j=0;j<count;j++)scaling(p+12*j,mult,inverse);return;}
 for(int j=0;j<count;j++){
  int y=p+12*j;mx(y,mult,T);csword(y,T);measureword(T,12,BB+12*j);
 }
 // All measured words have the SAME selected reciprocal. Swap it only once.
 csword(mult,inverse);
 for(int j=0;j<count;j++)pay(p+12*j,mult,rank12,BB+12*j);
 csword(mult,inverse);
 for(int j=0;j<12*count;j++)clearb(BB+j);
}
void mask_begin(int a,int temp){for(int j=0;j<12;j++)cc(FL,a+j,temp+j);}
void mask_end(int a,int temp){measureword(temp,12);for(int j=0;j<12;j++)czm(FL,a+j,MB+j);}
void inverse_products(int i,int p,int n,int l,int start,int k){
 // A constant coherent guard over a run permits one masked factor for every product.
 for(int j=start;j<n;){
  shift_guard(i,k,n-j);k=n-j;
  int end=j+1;while(end<n&&min(n-end,35-i)==min(k,35-i))end++;
  mask_begin(p+12*l,T);
  for(int r=j;r<end;r++)mx(T,p+12*(r-l),p+12*r);
  mask_end(p+12*l,T);j=end;
 }
 // caller passes nonzero k only when it has already toggled the guard for the square term.
 if(start<n)shift_guard(i,1,0);else shift_guard(i,k,0);
}
'''+s[pos:]
a=s.index("void scale_series(");b=s.index("void reciprocal(",a)
s=s[:a]+r'''
void scale_series(int i,int p,int n,bool rev){
 int k=0;
 for(int r=1;r<n;){
  shift_guard(i,k,n-r);k=n-r;
  int end=r+1;while(end<n&&min(n-end,35-i)==min(k,35-i))end++;
  batch_scale(p+12*r,end-r,rev?p:C,rev?C:p);
  r=end;
 }
 shift_guard(i,k,0);
}
void unit_inverse(int i,int p,int n){
 for(int l=1;2*l+1<n;l++)inverse_products(i,p,n,l,2*l+1,0);
 const V cols=frobcols(12,2);const L el=elimination(cols);
 for(int l=(n-1)/2;l>=1;l--){
  int k=n-2*l;shift_guard(i,0,k);
  apply(el,p+12*l,false);for(int j=0;j<12;j++)cc(FL,p+12*l+j,p+24*l+j);apply(el,p+12*l,true);
  inverse_products(i,p,n,l,2*l+1,k);
 }
}
'''+s[b:]
old='for(int t=0;t<n-l;t++)if(a+12*t!=lead)maskedmx(q,a+12*t,b+12*(l+t),C);'
new='if(n-l>0){mask_begin(q,C);for(int t=0;t<n-l;t++)if(a+12*t!=lead)mx(C,a+12*t,b+12*(l+t));mask_end(q,C);}'
assert old in s;s=s.replace(old,new)
old='le(i,n);for(int y=p;y<lead;y+=12)scaling(y,rev?lead:C,rev?C:lead);le(i,n);'
assert old in s;s=s.replace(old,'le(i,n);batch_scale(p,2*n-1,rev?lead:C,rev?C:lead);le(i,n);')
# All GF64 multiplications, including inversion, use the rank15 tensor instead of rank18.
a=s.index('void smallprod(');s=s[:a]+'extern vector<array<int,3>> rank6;\nvoid product(int a,int b,int t,const vector<array<int,3>>& terms);\n'+s[a:]
s=s.replace('void smallprod(int a,int b,int t,int n){','void smallprod(int a,int b,int t,int n){if(n==6){product(a,b,t,rank6);return;}')
p.write_text(s)
p=Path("build.py");s=p.read_text().replace('HM=49152','HM=49980');p.write_text(s)
p=Path("finalize.py");s=p.read_text().replace('49153','49981');p.write_text(s)

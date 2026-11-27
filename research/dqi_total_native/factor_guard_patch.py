"""Second global reduction: shared selected factor, incremental history flags, unit-series factorization.
Apply after joint_hmr_patch.py, before build.py. Preserves full #252 raw-syndrome ABI."""
from pathlib import Path
p=Path("total.cpp.in");s=p.read_text()
a=s.index("void scaling(int y,int mult,int inverse)");b=s.index("void swap_pivot(",a)
s=s[:a]+r'''
void scaling(int y,int mult,int inverse){
 // Product then conditional exchange, T is the old input if active.
 mx(y,mult,T);csword(y,T);measureword(T,12);
 // Select the entire reciprocal factor once, rather than controlling 42 products.
 xorword(mult,T);xorword(mult,inverse);
 for(int j=0;j<12;j++)cc(FL,inverse+j,T+j);
 xorword(mult,inverse);
 pay(y,T,rank12,MB);
 measureword(T,12);
 for(int j=0;j<12;j++){
   zm(mult+j,MB+j);czm(FL,mult+j,MB+j);czm(FL,inverse+j,MB+j);
 }
}
'''+s[b:]
# Only one next endpoint in the suffix while extracting or undoing a continued fraction.
# Pack still uses general first-set guards.
s=s.replace("void le(int i,int k){","bool single_suffix=false;\nvoid endpoint_toggle(int i,int j){if(i)cc(H+i-1,H+i+j,FL);else w.cx(H+j,FL);}\nvoid shift_guard(int i,int old,int next){old=max(0,min(old,35-i));next=max(0,min(next,35-i));for(int j=min(old,next);j<max(old,next);j++)endpoint_toggle(i,j);}\nvoid le(int i,int k){if(single_suffix){shift_guard(i,0,k);return;}")
s=s.replace("void kbit(int i,int b,int offset){for(int k=1;k<=35-i;k++)if(((k+offset)>>b)&1)exact(i,k);}","void kbit(int i,int b,int offset){for(int k=1;k<=35-i;k++)if(((k+offset)>>b)&1){if(single_suffix)endpoint_toggle(i,k-1);else exact(i,k);}}")
a=s.index("void scale_series(");b=s.index("void reciprocal(",a)
s=s[:a]+r'''
void scale_series(int i,int p,int n,bool rev){
 int k=0;
 for(int r=1;r<n;r++){shift_guard(i,k,n-r);k=n-r;scaling(p+12*r,rev?p:C,rev?C:p);}
 shift_guard(i,k,0);
}
void unit_inverse(int i,int p,int n){
 // Store elementary factors (1+a_l X^l) in the already occupied coefficient slots.
 for(int l=1;2*l+1<n;l++){
  int k=0;
  for(int j=2*l+1;j<n;j++){shift_guard(i,k,n-j);k=n-j;maskedmx(p+12*l,p+12*(j-l),p+12*j,T);}
  shift_guard(i,k,0);
 }
 // Multiply inverse elementary factors in the reverse order.
 const V cols=frobcols(12,2);const L el=elimination(cols);
 for(int l=(n-1)/2;l>=1;l--){
  int k=n-2*l;shift_guard(i,0,k);
  apply(el,p+12*l,false);for(int j=0;j<12;j++)cc(FL,p+12*l+j,p+24*l+j);apply(el,p+12*l,true);
  for(int j=2*l+1;j<n;j++){shift_guard(i,k,n-j);k=n-j;maskedmx(p+12*l,p+12*(j-l),p+12*j,T);}
  shift_guard(i,k,0);
 }
}
'''+s[b:]
s=s.replace("int p=24*i,n=70-2*i;rot(i,p,n,-1,1);","int p=24*i,n=70-2*i;single_suffix=true;rot(i,p,n,-1,1);")
s=s.replace("for(int d:{16,4,2})unit_power(i,p,n,d,true);","unit_inverse(i,p,n);").replace("for(int d:{2,4,16})unit_power(i,p,n,d,false);","unit_inverse(i,p,n);")
s=s.replace("invout(p,C,T);rot(i,p,n,-1,-1);","invout(p,C,T);rot(i,p,n,-1,-1);single_suffix=false;")
p.write_text(s)

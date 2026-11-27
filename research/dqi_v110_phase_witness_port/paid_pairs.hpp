#pragma once
// A same-scope CCX pair cancels when its controls are never written and
// its target is never touched between the two occurrences. HMR and R are
// explicit writes; classical-only instructions commute with a bare CCX.
vector<bool> paid_pairs(K& k) {
 vector<bool> skip(k.N);
 vector<long> read(k.Q,-1), write(k.Q,-1);
 unordered_map<U,long> prev;
 long scope=-1, removed=0;
 for(I i=0;i<k.N;i++){
   auto v=k.next(i);
   if(v.t==129 || v.t==1) {scope=i; continue;}
   int t=v.t&127;
   if(v.t==49 && v.a!=v.b && v.a!=v.c && v.b!=v.c){
     U key=(U(min(v.a,v.b))*k.Q+max(v.a,v.b))*k.Q+v.c;
     auto it=prev.find(key);
     if(it!=prev.end()){
       long j=it->second;
       if(j>scope && j>=max({write[v.a],write[v.b],read[v.c]})){
          skip[i]=skip[j]=true; removed+=2; prev.erase(it);
       }else it->second=i;
     }else prev.emplace(key,i);
   }
   auto r=[&](int q){if(q>=0)read[q]=i;};
   auto w=[&](int q){if(q>=0)write[q]=i;};
   r(v.a);r(v.b);r(v.c);
   switch(t){
     case 17:case 18:case 80:w(v.a);break;
     case 33:w(v.b);break;
     case 34:w(v.a);w(v.b);break;
     case 49:w(v.c);break;
     case 50:w(v.b);w(v.c);break;
     case 0:case 16:case 32:case 48:case 64:case 65:case 66:break;
     default:throw runtime_error("unsupported input opcode "+to_string(t));
   }
 }
 k.reset();cerr<<"original_CCX_removed "<<removed<<"\n";return skip;
}

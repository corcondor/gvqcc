#!/usr/bin/env python3
"""Held-out test of learned route priorities on exact ANGLE graph costs.

Uses scikit-learn histogram gradient boosting. This is not LightGBM.
Learning predicts which alternative to try once per bucket. An exact cost
comparison retains the greedy path if the selected alternative is worse.
"""
from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold


def features(case,method):
    n=case['size']
    return [n,case['mst_cost']/n,case['steiner_cost']/n,
            (case['mst_cost']-case['steiner_cost'])/n,case['hubs']/n,
            case['pivot_state_changes']/n,case['mean_weight'],
            int(method=='steiner')]


def experiment(cases):
    methods=('mst','steiner')
    samples=[(i,m) for i,c in enumerate(cases) for m in methods if m in c['costs']]
    X=np.asarray([features(cases[i],m) for i,m in samples],dtype=float)
    y=np.asarray([cases[i]['costs']['greedy']-cases[i]['costs'][m]
                  for i,m in samples],dtype=float)
    group=np.asarray([cases[i]['batch'] for i,m in samples])
    predictions={}
    folds=[]
    for train,test in GroupKFold(n_splits=5).split(X,y,group):
        model=HistGradientBoostingRegressor(max_iter=100,min_samples_leaf=12,
                                             learning_rate=.08,max_leaf_nodes=12,
                                             l2_regularization=1,random_state=1611)
        model.fit(X[train],y[train])
        for j,p in zip(test,model.predict(X[test]),strict=True):
            predictions[samples[j]]=float(p)
        folds.append(dict(train_batches=sorted(set(group[train].tolist())),
                          test_batches=sorted(set(group[test].tolist()))))
    improvements=Counter()
    picks=Counter()
    base=0
    for i,c in enumerate(cases):
        score=c['costs']['greedy']
        base+=score
        alt={m:max(0,score-c['costs'].get(m,score)) for m in methods}
        for m,d in alt.items():improvements['always_'+m]+=d
        improvements['oracle_both']+=max(alt.values())
        chosen=max([('greedy',0)]+[(m,predictions[i,m]) for m in alt if (i,m) in predictions],
                   key=lambda x:x[1])[0]
        picks[chosen]+=1
        improvements['boost_one_candidate']+=alt.get(chosen,0)
    return dict(method='HistGradientBoostingRegressor, no LightGBM dependency',
                feature_scope='route geometry computed before exact alternative path optimization',
                baseline_greedy_transition_cost_sum=base,measured_savings_over_greedy=improvements,
                learned_candidate_selections=picks,cases=len(cases),labeled_alternatives=len(samples),
                folds=folds,scope='bucket-local control + fanout operation counts, not official score or training/runtime speedup')


def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    cases=json.loads(a.receipt.read_text())['route_cases']
    result=experiment(cases)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='folds'})


if __name__=='__main__':
    main()

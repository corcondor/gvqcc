#!/usr/bin/env python3
"""Run bounded upstream CEGAR on real 8x16 ANGLE k8 fixture; no official scoring."""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"third_party"/"manwithacat"))
import chained_and as ca

target=ca.Target.from_json(Path(__file__).with_name("fixture_k8_4out_8rows.json"))
out=ROOT/"outputs"/"oss_chained_cegar"
res=ca.cegar(target,k=4,chained=1,workdir=out,solver="cadical",
             timeout_s=8,init_rows=[0,1],add_rows=1,max_iters=5,budget_s=20,
             gauge=True,lex=True,force_chain=True,log=print)
status=res["status"]
if status=="SAT":
    circ=ca.Circuit.from_dict(res["circuit"])
    assert ca.verify(circ,target,rowbits=res["rowbits"])["all_pass"]
# UNSAT says something only about this fixed shape/row constraints.
out.mkdir(parents=True,exist_ok=True)
(out/"report.json").write_text(json.dumps(res,indent=2,default=str)+"\n")
print(json.dumps({"status":status,"iterations":len(res.get("iterations",[])),
                 "cpu_s":res.get("cpu_s"),"rows_used":res.get("rows"),
                 "domain":"k8 8 rows * 16 addresses * 4 outputs",
                 "shape":"k=4, chained=1, lex+gauge", "official_score":None},indent=2))

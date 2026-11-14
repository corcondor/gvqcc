"""Summarize bounded discrete experiments; retain one valid compact candidate."""
import json,hashlib,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from chemistry_polish_v2_restore import arrays_sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'gvqcc_repo';bp=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz';base=dict(np.load(bp));baseline_lambda=46.90658950862355;T=14728;Q=427
al=json.loads((OUT/'chemistry_discrete_v3_results.json').read_text());repair=json.loads((OUT/'chemistry_discrete_v3_repair_results.json').read_text())
valid=[r for r in repair['results'] if r['numerically_valid']];best=min(valid,key=lambda r:r['official_numerical_metrics']['lambda_eff']);source=ROOT/best['path'];checkpoint=dict(np.load(source));target=OUT/'chemistry_discrete_v3_best_compact.npz';np.savez_compressed(target,**checkpoint)
merged=dict(base);merged.update(checkpoint);full=OUT/'chemistry_discrete_v3_best_full.npz';np.savez_compressed(full,**merged);again=dict(np.load(bp));again.update(dict(np.load(target)));assert all(np.array_equal(again[k],merged[k]) for k in merged);check=OUT/'chemistry_discrete_v3_restorecheck.npz';np.savez_compressed(check,**again);byte_same=hashlib.sha256(check.read_bytes()).hexdigest()==hashlib.sha256(full.read_bytes()).hexdigest();check.unlink()
changes=[{'row':int(a),'angle':int(j),'old':int(base['angle_words'][a,j]),'new':int(merged['angle_words'][a,j]),'xor':int(base['angle_words'][a,j])^int(merged['angle_words'][a,j])} for a,j in np.argwhere(base['angle_words']!=merged['angle_words'])]
v=best['official_numerical_metrics'];delta=baseline_lambda-v['lambda_eff'];one_loader_cost=baseline_lambda-baseline_lambda*T/(T+2);maxextra=.5*T*(baseline_lambda/v['lambda_eff']-1)
summary={'created_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Bounded independent integer-angle search; no user candidate file was available. No successful Kaggle submission or complete optimized circuit is claimed.','baseline':{'path':str(bp.relative_to(ROOT)),'sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'lambda_eff':baseline_lambda,'T':T,'Q':Q},'screening':{'first_order_affine_templates':9975,'high_address_curvature_templates':1125,'exact_table_screens':20,'refit_candidates':3,'repair_candidates':3,'large_array_artifacts_required_for_reproduction':False},'best':{'index':best['index'],'official_numerical_metrics':v,'numerically_valid':True,'changed_words':changes,'compact_path':str(target.relative_to(ROOT)),'compact_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'compact_bytes':target.stat().st_size,'compact_fields':list(checkpoint),'full_array_sha256':arrays_sha256(merged),'full_npz_sha256':hashlib.sha256(full.read_bytes()).hexdigest(),'all_arrays_restored_identically':True,'byte_identical_restore_current_environment':byte_same,'numpy_version':np.__version__},'cost_scope':{'lambda_reduction_vs_reproduced_baseline':delta,'relative_change_percent_assuming_unchanged_TQ':100*(v['lambda_eff']/baseline_lambda-1),'hypothetical_cost_with_unchanged_TQ':v['lambda_eff']*T*Q,'lambda_reduction_needed_for_one_extra_Toffoli_per_loader_pass':one_loader_cost,'maximum_extra_Toffoli_per_loader_pass_affordable':maxextra,'single_word_loader_cost_established':False,'full_circuit_verified':False,'submitted':False,'improves_user_reported_46_905894137':False},'final_candidate_outcomes':[{'index':r['index'],'metrics':r['official_numerical_metrics'],'numerically_valid':r['numerically_valid']} for r in repair['results']],'limitations':['First-order and diagonal Gauss-Newton scores rank candidates; they are not certified improvement bounds.','Affine low-bit loader transformations have separate exact mapping checks, but the selected single-word change is not such an affine mask.','No general loader resynthesis or full circuit verification was performed.','The user baseline 46.905894137 and continuous objective44.17 belong to unavailable arrays; they were not reproduced.']}
(OUT/'chemistry_discrete_v3_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
text=f'''# 離散角度探索 v3 —  bounded CPU実験

## 結果

整数角度表を実際に変更し、W/H2_Iを再調整した2候補が公式の数値条件を満たした。最良は **row908 / angle27 の194→193**（0始まり）。λeffは **{v['lambda_eff']:.14f}**、error1は **{v['error_1']*1000:.12f} mHa**、error2は **{v['error_2']*1000:.12f} mHa**、E_gapは **{v['E_gap']:.14f}**。

これは提出可能なスコア改善を確定した結果ではない。実行環境の基準λeff46.90658950862355との差は **{delta:.12g}**。新ローダーのToffoli数は未確定で、1 passあたり1 Toffoli増えるだけでも必要なλ削減は **{one_loader_cost:.12g}**。したがって今回の微小なλ改善では追加1 Toffoli/passを支払えない。同じT,Qを維持できた場合のみ、費用変化は **{summary['cost_scope']['relative_change_percent_assuming_unchanged_TQ']:.9f}%** となる。

ユーザーが報告した別基準46.905894137より良いという意味でもない。実ファイルは取得できていない。全回路検証・Kaggle提出は行っていない。

## 実験範囲

公式Givens木のreverse ADで全91,500角度の勾配を計算。定数、1 address bit、2 address bit parityと反転のLSB XOR **9,975テンプレート**を一次順位付けし、上位8表を厳密再評価した。大きい勾配の候補は1 LSB変更の曲率で誤差が増え、不合格だった。

次にGivens Jacobianと二体残差のGauss–Newton対角近似で±1候補を再順位付け。先頭76のone-body行を変更しない高address bits7..10の15 parityを各75角度で評価した（**1,125テンプレート**、初回候補との重複あり）。追加12表を厳密再評価した。二次近似も改善保証ではない。

誤差が小さいsingle-word2案とaffine1案について短いAL/L-BFGS再fitを行い、その後に誤差/gapの正確なJacobianによるNewton補正を行った。最初のsingle-word案はALでも数値条件を満たし、Newton後にさらにλが減った。後ろ2案の初期ALログだけから全候補が停止したとした中間報告は誤りで、最終JSONは全候補の実測値を保持する。

| 変更 | 最終λeff | error1 mHa | error2 mHa | 数値条件 |
|---|---:|---:|---:|---|
'''
for r in repair['results']:
 vv=r['official_numerical_metrics'];name={1:'row908,col27:194→193',5:'row840,col30:20→21',6:'col70 LSB XOR addressbit10 (196語)'}[r['index']];text+=f"| {name} | {vv['lambda_eff']:.12f} | {1000*vv['error_1']:.9f} | {1000*vv['error_2']:.9f} | {'適合' if r['numerically_valid'] else '不適合'} |\n"
text+='''
## キャッシュと評価の整合

変更したangle_wordsから公式ベクトルを再構成し、候補ごとにV/G4/A/e20を再構築した。参照FCIDUMP、固定シフト、対称ペアの目標だけを共有した。反復でN^4テンソルを作り直さず、最終値は変更していない公式evaluate_dfthc_angle_wordsで確認した。

低6bitへのaddress-affine XORは別担当のローダー契約検証の対象。しかし最良候補は単一addressだけでbits0,1を反転する変更で、同費用のaffineパッチで実装できると確認したものではない。単独word案をToffoli増なしと扱わない。

## 保存と復元

chemistry_discrete_v3_best_compact.npzはangle_words,W,H2_Iだけを含む。summaryに基準SHA256、compact SHA256、全配列canonical SHA256、fullNPZ SHA256を保存。基準NPZへ3配列を上書きし、全配列同一と同一環境でのZIPバイト一致を検査した。大きいgradient/curvature NPZと無効候補はGitHub保存に不要。

再現順序は chemistry_discrete_v3_search.py、chemistry_discrete_v3_refit.py、chemistry_discrete_v3_repair.py、chemistry_discrete_v3_collect.py。refit.pyは内部でsearch.pyを実行するため、通常はrefit.pyから開始すればよい。OPENBLAS_NUM_THREADS=1、OMP_NUM_THREADS=1。既存inverse_v2_chemistry_refit.pyと公式参照が必要。
'''
(OUT/'chemistry_discrete_v3_report.md').write_text(text)
print(json.dumps({'best':summary['best'],'cost_scope':summary['cost_scope']}),flush=True)

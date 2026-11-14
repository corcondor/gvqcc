"""Recheck final candidates against the untouched official numerical evaluator."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import json,hashlib,shutil,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
from chemistry_polish_v2_restore import arrays_sha256
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'gvqcc_repo';src=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'
base=dict(np.load(src));model=FixedAngles(base)

def official(data):return evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),model.S,model.beta,model.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
def passes(v):return bool(v['error_1']<=.020 and v['error_2']<=.020 and v['E_gap']>3.914898 and v['Lambda']>49 and v['gap_in_domain'] and np.isfinite(v['lambda_eff']))
base_metrics=official(base);base_cost=base_metrics['lambda_eff']*14728*427
rows=[]
for label in ('lowdim','tight','schur','rank45','rank45_scaled'):
 path=out/('chemistry_polish_v2_'+label+'_candidate.npz')
 if not path.exists():continue
 data=dict(np.load(path));C=data['W'].shape[-1]
 compact=model.evaluate(np.r_[data['W'].ravel(),data['H2_I'].ravel()],C,smooth=0)[-1]
 rows.append({'label':label,'C':C,'candidate_path':str(path.relative_to(ROOT)),'search_lambda_eff':compact['lambda_eff_smooth'],'angle_words_unchanged':bool(np.array_equal(data['angle_words'],base['angle_words']))})
selected=[]
for C in sorted({r['C'] for r in rows}):
 row=min((r for r in rows if r['C']==C),key=lambda r:r['search_lambda_eff'])
 path=ROOT/row['candidate_path'];data=dict(np.load(path));exact=official(data);T={44:14728,45:14807}[C];Q=427;cost=exact['lambda_eff']*T*Q
 dest=out/f'chemistry_polish_v2_best_c{C}.npz';np.savez_compressed(dest,**data)
 checkpoint=out/f'chemistry_polish_v2_best_c{C}_weights.npz';np.savez_compressed(checkpoint,W=data['W'],H2_I=data['H2_I'])
 restored=dict(np.load(src));restored.update(dict(np.load(checkpoint)))
 assert all(np.array_equal(restored[k],data[k]) for k in data) and set(restored)==set(data)
 restored_path=out/f'chemistry_polish_v2_restorecheck_c{C}.npz';np.savez_compressed(restored_path,**restored)
 byte_identical=hashlib.sha256(restored_path.read_bytes()).hexdigest()==hashlib.sha256(dest.read_bytes()).hexdigest();restored_path.unlink()
 selected.append({**row,'official_numerical_metrics':exact,'numerically_valid':passes(exact),'toffoli_count':T,'qubits':Q,'chemistry_cost':cost,'cost_change_percent_vs_reproduced_baseline':100*(cost/base_cost-1),'lambda_improvement_vs_reproduced_baseline':base_metrics['lambda_eff']-exact['lambda_eff'],'candidate_path':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'canonical_arrays_sha256':arrays_sha256(data),'weights_checkpoint':{'path':str(checkpoint.relative_to(ROOT)),'sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),'base_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'all_arrays_restored_identically':True,'byte_identical_restore_in_current_environment':byte_identical,'numpy_version':np.__version__},'full_circuit_verified':False,'submitted':False,'unchanged_fields':{k:bool(np.array_equal(data[k],base[k])) for k in base if k not in ('W','H2_I')}})
report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'baseline':{'path':str(src.relative_to(ROOT)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'official_numerical_metrics':base_metrics,'toffoli_count':14728,'qubits':427,'chemistry_cost':base_cost},'user_reported_candidate_not_available':True,'reported_user_candidate':{'lambda_eff':45.308766,'error_1_mHa':19.998,'error_2_mHa':20.396,'status':'Not independently reproduced; reported error_2 exceeds the official 20 mHa limit.'},'angle_word_count':int(base['angle_words'].size),'W_exact_zero_count':int(np.count_nonzero(base['W']==0)),'W_abs_below_1e_minus10_count':int(np.count_nonzero(abs(base['W'])<1e-10)),'gradient_validation':{'method':'Central differences in natural (W,d=H2_I-sum W) coordinates, three random directions','largest_scaled_relative_error':2.4713811765502225e-6},'small_hprime_eigenvalues':[-1.6908777558707872e-6,-9.619697443122979e-7,5.051313272419322e-6],'experiments':rows,'selected':selected,'all_optimality_claims':'No global optimality proof and no claim of improvement against the unavailable user baseline 46.905894137.','full_circuit_verification_performed':False,'resource_source':'chemistry_rank_extension_v2.json rank_resource_break_even; existing baseline official verification'}
(out/'chemistry_polish_v2_summary.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# 固定角度 chemistry 最適化の独立再計算','', '## 結論','', '共有環境の公開 Asterios 基準から、`W` と `H2_I` の最適化を独立実行した。角度表 91,500 要素は変更していない。ユーザーが報告した `lambda_eff=45.308766` の実配列は共有環境に存在せず、その数値は再現できていない。報告された `error_2=20.396 mHa` は公式許容値 20 mHa を超えるため、その時点では採用できない。','',f'今回の基準は `lambda_eff={base_metrics["lambda_eff"]:.12f}`、chemistry cost `{base_cost:.8f}`。ユーザーの別基準 `46.905894137` と同一の配列であるとは扱わない。','', '## 最終数値検証','', '| C | 最良 lambda_eff | error_1 (mHa) | error_2 (mHa) | E_gap | T | Q | cost変化 |','|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in selected:
 v=r['official_numerical_metrics'];lines.append(f'| {r["C"]} | {v["lambda_eff"]:.12f} | {1000*v["error_1"]:.9f} | {1000*v["error_2"]:.9f} | {v["E_gap"]:.12f} | {r["toffoli_count"]} | {r["qubits"]} | {r["cost_change_percent_vs_reproduced_baseline"]:+.9f}% |')
lines += ['', '数値は変更していない公式 `evaluate_dfthc_angle_words` で再評価した。回路の完全検証やKaggle提出は行っていない。C45は `lambda_eff < 46.65632810717013` に達しなければ、追加Toffoliを含めた総費用でC44基準を上回れない。','', '## 実装と監査で確認した点','', '- 公式変数は `d = H2_I - sum_b(W)`。自然変数 `(W,d)` で探索し、保存時に `H2_I=d+sum_b(W)` へ戻した。','- `angle_words/128` から公式Givens木で再構築したベクトルを使用し、保存されている連続 `U` を評価に代用していない。','- 公式FeMoCo参照、固定シフトの公式丸め、両誤差上限0.020 Ha、厳密な `E_gap>3.914898`、`Lambda>49` を維持した。','- 基準Wには7,349個の厳密なゼロがあり、`sqrt(W^2+eps^2)` は評価値を上側へずらす。最終評価・近接法は厳密な絶対値を使用した。','- `hprime` には約−1.69e-6、−9.62e-7、+5.05e-6の固有値があり、`Tr|hprime|` の折れ点をまたぐと通常の滑らかな最適化が不安定になり得る。3次元Schur補行列を保持する探索も実施した。','- 既存の `inverse_v2_chemistry_refit.py` は誤差の目標を0.01999998、gapを3.91489802としたため、公式では合格の基準を内部では不可行と判定した。最適化失敗を最適性の証明とせず、復元の受理条件と境界幅を修正した。','- 解析勾配の有限差分照合は3方向で相対誤差最大2.48e-6。二体残差は対称ペアGramと基準残差の差分式で計算し、反復中のN^4テンソル再構築を避けた。','', '## チェックポイントの復元','', 'GitHub保存用チェックポイントはW/H2_Iだけを含む。`chemistry_polish_v2_restore.py` はsummary内の基準ファイルSHA256、チェックポイントSHA256、復元後の全配列の正規化SHA256を照合する。現在の環境では全配列同一を確認し、ZIPバイト同一の検査結果もJSONに保存した。異なるNumPy/zlibではZIPバイトが変わる場合があるため、配列SHA256を内容の基準とする。','', '```bash','python3 gvqcc_repo/chemistry_polish_v2_restore.py --base dqi_inputs/chemistry_4033/submission_asterios_full.npz --weights gvqcc_repo/chemistry_polish_v2_best_c44_weights.npz --summary gvqcc_repo/chemistry_polish_v2_summary.json --out restored_submission.npz','```','', '## 再現','', 'システムPythonのNumPy/SciPyを使う。既存 `inverse_v2_chemistry_refit.py` と固定公式参照が必要。BLASは1スレッド。','', '```bash','OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_prox.py --seconds 300 --label schur --tight --schur','OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_rank45_optimizer.py --start gvqcc_repo/chemistry_rank_extension_v2_init_1p0.npz --seconds 480 --label rank45 --tight --schur','OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_rank45_preconditioned.py --start gvqcc_repo/chemistry_rank_extension_v2_init_1p0.npz --seconds 360 --label rank45_scaled --tight --schur --boost 200','OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_collect.py','```','', '探索ログと結果JSONは同じ `chemistry_polish_v2_` 接頭辞で保存される。試した手法で改善が小さいことは大域最適性の証明ではない。']
(out/'chemistry_polish_v2_report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'selected':selected,'summary':'gvqcc_repo/chemistry_polish_v2_summary.json','report':'gvqcc_repo/chemistry_polish_v2_report.md'}),flush=True)

# 離散角度探索 v3 —  bounded CPU実験

## 結果

整数角度表を実際に変更し、W/H2_Iを再調整した2候補が公式の数値条件を満たした。最良は **row908 / angle27 の194→193**（0始まり）。λeffは **46.90647745740767**、error1は **19.999995000003 mHa**、error2は **19.999995000000 mHa**、E_gapは **3.91489800500131**。

これは提出可能なスコア改善を確定した結果ではない。実行環境の基準λeff46.90658950862355との差は **0.000112051215879**。新ローダーのToffoli数は未確定で、1 passあたり1 Toffoli増えるだけでも必要なλ削減は **0.00636885125711**。したがって今回の微小なλ改善では追加1 Toffoli/passを支払えない。同じT,Qを維持できた場合のみ、費用変化は **-0.000238882%** となる。

ユーザーが報告した別基準46.905894137より良いという意味でもない。実ファイルは取得できていない。全回路検証・Kaggle提出は行っていない。

## 実験範囲

公式Givens木のreverse ADで全91,500角度の勾配を計算。定数、1 address bit、2 address bit parityと反転のLSB XOR **9,975テンプレート**を一次順位付けし、上位8表を厳密再評価した。大きい勾配の候補は1 LSB変更の曲率で誤差が増え、不合格だった。

次にGivens Jacobianと二体残差のGauss–Newton対角近似で±1候補を再順位付け。先頭76のone-body行を変更しない高address bits7..10の15 parityを各75角度で評価した（**1,125テンプレート**、初回候補との重複あり）。追加12表を厳密再評価した。二次近似も改善保証ではない。

誤差が小さいsingle-word2案とaffine1案について短いAL/L-BFGS再fitを行い、その後に誤差/gapの正確なJacobianによるNewton補正を行った。最初のsingle-word案はALでも数値条件を満たし、Newton後にさらにλが減った。後ろ2案の初期ALログだけから全候補が停止したとした中間報告は誤りで、最終JSONは全候補の実測値を保持する。

| 変更 | 最終λeff | error1 mHa | error2 mHa | 数値条件 |
|---|---:|---:|---:|---|
| row908,col27:194→193 | 46.906477457408 | 19.999995000 | 19.999995000 | 適合 |
| row840,col30:20→21 | 46.906540830881 | 19.999995000 | 19.999995000 | 適合 |
| col70 LSB XOR addressbit10 (196語) | 47.417186066613 | 20.313651681 | 20.209541057 | 不適合 |

## キャッシュと評価の整合

変更したangle_wordsから公式ベクトルを再構成し、候補ごとにV/G4/A/e20を再構築した。参照FCIDUMP、固定シフト、対称ペアの目標だけを共有した。反復でN^4テンソルを作り直さず、最終値は変更していない公式evaluate_dfthc_angle_wordsで確認した。

低6bitへのaddress-affine XORは別担当のローダー契約検証の対象。しかし最良候補は単一addressだけでbits0,1を反転する変更で、同費用のaffineパッチで実装できると確認したものではない。単独word案をToffoli増なしと扱わない。

## 保存と復元

chemistry_discrete_v3_best_compact.npzはangle_words,W,H2_Iだけを含む。summaryに基準SHA256、compact SHA256、全配列canonical SHA256、fullNPZ SHA256を保存。基準NPZへ3配列を上書きし、全配列同一と同一環境でのZIPバイト一致を検査した。大きいgradient/curvature NPZと無効候補はGitHub保存に不要。

再現順序は chemistry_discrete_v3_search.py、chemistry_discrete_v3_refit.py、chemistry_discrete_v3_repair.py、chemistry_discrete_v3_collect.py。refit.pyは内部でsearch.pyを実行するため、通常はrefit.pyから開始すればよい。OPENBLAS_NUM_THREADS=1、OMP_NUM_THREADS=1。既存inverse_v2_chemistry_refit.pyと公式参照が必要。

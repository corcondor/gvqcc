# C45列追加・初期化の独立監査

## 判定

**数式・資源計算・保存NPZの保持条件は整合している。3つのinitializerは誤差余裕を作る候補であり、現時点での総費用改善ではない。** d新列は数学上0、実浮動小数配列では最大1.06184e-17の丸め差がある。

実行中のrefitには触れていない。全ANGLE回路検証・新提出は行っていない。公式referenceのintegralを読み、保存angle_wordsからベクトルを復元し、対称packed-pair空間で残差と8方向の内積を独立再構成した。監査計算は約18.6秒。

## 1. 新列の二次展開

新列を w_new=t*v、native d_new=t*z とすると、X_new=t*Y、Y=Σ_b v_b u_b u_b^T。従って

- H1'の変化は−t²*z*Y。
- lambda_H2の変化は t²/4*(Σ_b|v_b|+|z+Σ_b v_b|)²。
- gapの二次変化は lambda_H1の二次変化−Tr(H1'の二次変化)+z²/2。
- error2²の二次変化は2*t²*<E0,Y⊗Y>、四次項はt⁴*||Y⊗Y||²。

lambda_effの微分係数は dλ_eff=(gap/λ_eff)dΛ+((Λ−gap)/λ_eff)dgap。制約3=(gap_floor−gap)/.01 のLagrange寄与により、gap係数からmu3/.01を引く符号は正しい。交差項を対称matrixの両三角へhalfずつ入れる実装も正しい。

保存された8方向について、公式復元ベクトルから上の式を再計算したt²係数と報告値の最大差は **2.58e-14**。

ただし `lagrangian_curvature` はt²係数であり、通常の方向二階微分ならその2倍。絶対値二乗項は方向・符号領域ごとの二次形式で、原点に単一の滑らかなHessianがあるとみなさない方が正確。

さらにmuは非zero supportで推定した値で、残差norm2.8117が残る。8方向すべての探索は180iter上限で停止している。負のLagrangian係数は探索用のwitnessで、真のKKT点からの可行降下・大域最適性・完成スコア改善の証明ではない。実際、保存方向のλ単体の二次係数はすべて正である。

## 2. d=0初期化と不変量

initコードはscreen方向のd成分を取り除き、W方向を再正規化した別の初期化を作る。元の8方向の曲率の主張を、そのまま新しいd=0方向へ移してはいけない。一方、error2残差改善を別途直接最小化しているので、initializerとしての根拠は独立にある。

新H2_I列=Σ_b W新列とするため、数学上d新列=0。旧44列のW/H2_Iはbit単位で同じで、実際のnative dも旧44列はbit単位で不変。新列では2D sliceのsumと公式3D arrayのsumの順序差により、d最大値はfraction0.25で5.31e-18、0.5で7.67e-18、1.0で1.06e-17。H1/gapへの効果は丸め誤差域。

したがって数学上H1'・error1・gap・E_SOSは不変で、lambda_H2だけは非zero新列の正の寄与により増える。保存された全3NPZでU、H1_I、Hsym_lower、tree_edges、angle_wordsも完全一致した。

## 3. amplitude²の8変数QP

p_r=amplitude_r²≥0、Z_rを各群の新しい対称matrix Y_rのpacked-pair vectorとすると、

`error2²(p) = e20 + 2*l^T*p + p^T*G*p`

ここで l_r=<E0,Z_r⊗Z_r>、G_rs=(Z_r·Z_s)²。Gはrank-one対称matrixのGramなので半正定値。独立に再構成したl、Gと保存値の最大差はそれぞれ **1.68e-18、7.77e-16**。

今回の8×8 Gの固有値は0.586884から1.481696までで全て正。独立に解いたp*=−G^−1*lは全要素正なので、**この固定8方向に限定した非負振幅二乗問題**では唯一の最小点である。保存L-BFGS-B解との最大差は6.96e-10、保存解のgradient infinity normは1.32e-9。

これは全W/H2_Iの非凸問題に対する大域最適の主張ではない。

実NPZの新列から振幅二乗を再計算し、上の残差式から予測したerror2と既存公式数値評価の最大差は **2.12e-16 Hartree**。Λ増分を直接絶対値式で再計算して得たlambda_effと公式記録の最大差は **1.42e-14**。

## 4. C45の資源と損益

公式SpinFreeData_V1をC45で呼び直した結果:

| 項目 | Toffoli / Q |
|---|---:|
| ANGLE forward+reverse |8066 T|
| outer state preparation |320 T|
| inner state preparation |4171 T|
| Givens rotations |2250 T|
| 合計 |**14807 T**|
| outer persistent/temporary |40 / 90 Q|
| inner persistent/temporary |44 / 303 Q|
| word persistent / ANGLE scratch |40 / 77 Q|
| 全体Q |**40+44+40+max(90,303,77)=427**|

R/Bとangle wordsが不変なのでANGLEのselection11、J5、brot8と128Q capは変わらない。Cだけが変わることによるstate-preparationコストを上表に含めた。

基準14728T、427Q、lambda_eff46.906589508623554に対して、C45は

`lambda_eff < 46.906589508623554 * 14728 / 14807 = 46.65632810717956`

が改善条件。必要λ削減は **0.5335314378%**。rootの46.6563281072と一致する。

## 5. initializerの実際の立ち位置

| fraction | error2 (mHa) | lambda_eff | chemistry総費用の基準比 |
|---:|---:|---:|---:|
|0.25|19.9822096878|46.9072954081|1.0053790624|
|0.5|19.9694936919|46.9080012969|1.0053941920|
|1.0|19.9593150620|46.9094130428|1.0054244504|

すべて誤差2には余裕が増えるが、λもTも増え、現在のchemistry総費用は約0.538–0.542%悪い。従って「追加列で残差を減らし、その余裕をrefitに使う」という実験として報告するのが正確。実行中refitの完成値が46.6563281072を下回って全制約を満たすかは、この監査の範囲外。

監査に使ったsource/input SHA、8変数の解、各NPZの保持検査と数値差は `chemistry_rank_extension_v2_audit.json` に保存した。

# EEAの99 CCX乗算：代数同定と評価点を跨ぐ再合成

**結論：3種類の辞書で合計655,134,720回の候補提案（重複を含む）を実行しましたが、最良は99 CCXのままで、採用できる削減候補はありません。既存のKMB・README・workerは変更していません。**

| 辞書 | 探索時間 | 提案回数（重複を含む） | 最良CCX |
|---|---:|---:|---:|
| 対称255積 | 420.002秒 | 549,588,992 | 99 |
| 非対称3825積 | 360.002秒 | 104,980,480 | 99 |
| 点間65025積 | 180.017秒 | 565,248 | 99 |

これらは上限を定めた探索結果であり、98以下が存在しないという証明ではありません。

## 確定した代数

対象は `inverse_v2_actual_eea_product.kmx` と、その実ゲート列から抽出済みの `inverse_v2_actual_tensor99.json` です。今回、テンソルの全24×24＝576基底対を改めて照合しました。

基礎体は `GF(2^12)`、法多項式は `0x1053`。24bitの値を `x=x0+x1*t` とすると、拡大体は

\[
K=\mathbf F_{4096}[t]/(t^2+t+2048).
\]

`Tr_GF4096/GF2(2048)=1` を計算し、4096個の基礎体要素のどれも二次式の根でないことを確認しました。従ってこれは真の `GF(2^24)` です。実ブロックは

\[
z\longmapsto z\oplus\overline{x}\,y,\qquad
\overline{x}=(x_0\oplus x_1)+x_1t
\]

を計算します。左右の24bit入力を復元し、24bit出力へ積を加える構成です。従来の証明書にある99 CCX・6122 CXと整合します。12bit乗算2本への置換や、GF12の66 CCX逆数回路への置換は同じ演算になりません。

公開生成器 `extension24_tensor.py` は、GF16上の次数6の基底に移し、11点で評価して、各点を9積で処理する `11 × 9 = 99` の構成です。基底のGF16生成元は1970、拡大体生成元は4096でした。生成器SHA-256は `330cdeba5965e03fa397b07f7200539925112a815793704791173d144e74c09d` です。

同じ公開ソースにある `unit_jet_tensor.py` の99積は別の演算です。長さ2のjetは `GF4096[ε]/(ε²)` であり、非零のεが二乗で0になります。対象のtは `t²=t+2048` です。数が同じでもテンソルを交換できません。

## 今回実装した新しい探索

従来のCCX pair置換、同じ出力方向の二次rank簡約、tensor flip/plus探索は繰り返していません。GF16上の全17射影点に対応する255個の二進線形形式を作り、そのANDの出力方向を線形依存式で共同再合成しました。

| 辞書 | 許した積 | 候補数 | 二次形式のrank |
|---|---|---:|---:|
| 対称 | 同じ点・同じ線形形式を左右に適用 | 255 | 142 |
| 非対称 | 同じ点、左右に異なる線形形式を許す | 3825 | 240 |
| 点を跨ぐ | 左右の評価点も異なってよい | 65025 | 576 |

初期値にはそれぞれ24、8、1種類の99積の補間構成を用い、各初期値を全576基底対で検証しました。探索は辞書の基底を交換し、その厳密な線形依存式で24bit出力係数を更新します。一時的に最大113積まで許し、98積以下を探します。現行の全KMBを展開したり、公式verifierを呼んだりする計算ではありません。

実行の確定値は [dqi_algebra_report.json](dqi_algebra_report.json) の `searches` にあります。各探索のseed、所要時間、候補提案数、受理数、再開始数と最小積数を保存します。探索を終えた後の結果と、この数学的な限定証明は区別してください。

### 限定した99の下限も検証

[dqi_algebra_local_certificate.json](dqi_algebra_local_certificate.json) では、GF16の15個の非零線形形式から8個を選ぶ6435通りを全て調べました。4bit乗算の全出力を張る8個の組はありませんでした。さらに、元の11点の対称二次形式空間はrank110で、各点の10次元空間の直和です。この**元の11点と同じ点内の対称積だけ**に限定すれば、各点9積、合計99積が必要です。

12点目以降では点間の依存式が発生します。今回の255積以上の辞書探索はその範囲を調べるもので、上の限定下限を一般化していません。

## 補間・塔体・曲線の費用確認

[dqi_algebra_interpolation_costs.json](dqi_algebra_interpolation_costs.json) は、全基底対で確認したGF2/GF4/GF8/GF16/GF64の1/3/6/9/15積カーネルを使う、通常評価点の配分計算です。

| 構成 | 必要な評価座標数 | カタログ内の最小積数 |
|---|---:|---:|
| 射影直線 / GF4、拡大次数12 | 23 | 99 |
| 射影直線 / GF8、拡大次数8 | 15 | 99 |
| 射影直線 / GF16、拡大次数6 | 11 | 99 |
| 楕円曲線 / GF4、拡大次数12 | 24 | 99以上 |
| 楕円曲線 / GF8、拡大次数8 | 16 | 99以上 |
| genus 2 / GF4、拡大次数12 | 25 | 99以上 |

曲線の表は存在条件を緩めた楽観的な配分です。genus 2 / GF4は有理点数が高々 `2(4+1)=10` であることを課し、Weil条件を満たす91組の係数を調べました。「11有理点＋7個の次数2の点なら96積」という仮案は、有理点数の条件を満たしません。

この計算は、高次数の別カーネル、微分評価、より高いgenus、一般のテンソル分解を排除しません。また、点数を配分しただけで具体的な曲線、次数12の場所、評価写像の単射性まで構成したという主張でもありません。

## 再現

Python 3の標準ライブラリとC++17コンパイラを使います。GPUは不要です。ワークスペースのルートから実行します。

```bash
python -B gvqcc_repo/dqi_algebra_interpolation.py --starts 24
python -B gvqcc_repo/dqi_algebra_interpolation.py --nonsymmetric --starts 8 --output gvqcc_repo/dqi_algebra_nonsymmetric_dictionary.txt
python -B gvqcc_repo/dqi_algebra_interpolation.py --cross-points --starts 1 --output gvqcc_repo/dqi_algebra_crosspoint_dictionary.txt
g++ -O3 -std=c++17 gvqcc_repo/dqi_algebra_dictionary_search.cpp -o gvqcc_repo/dqi_algebra_dictionary_search
gvqcc_repo/dqi_algebra_dictionary_search gvqcc_repo/dqi_algebra_dictionary.txt gvqcc_repo/dqi_algebra_candidate.json 420 202611142004
gvqcc_repo/dqi_algebra_dictionary_search gvqcc_repo/dqi_algebra_nonsymmetric_dictionary.txt gvqcc_repo/dqi_algebra_nonsymmetric_candidate.json 360 202611142009
gvqcc_repo/dqi_algebra_dictionary_search gvqcc_repo/dqi_algebra_crosspoint_dictionary.txt gvqcc_repo/dqi_algebra_crosspoint_candidate.json 180 202611142013
python -B gvqcc_repo/dqi_algebra_local_certificate.py
python -B gvqcc_repo/dqi_algebra_interpolation_costs.py
```

必要な既存入力・依存コードは以下です。大きいKMBは不要です。

- `gvqcc_repo/inverse_v2_actual_tensor99.json`：実ゲートから抽出した99積。
- `gvqcc_repo/inverse_v2_actual_block_audit.py`、`inverse_v2_optimize.py` と、それらがimportする既存の `symbolic_block_analyze.py`、`inverse_specialized.py`、`full_inverse_verify.py`、`pebble_search.py`。
- Syed v12公開ソースの `source/dqi_source/src/controller_work/night_root/extension24_tensor.py` と、同階層 `night_converter/night_reference.py`。ワークスペースでは `official_sources/Syed_v12/` の下に配置します。

公開ソースがまだない環境では、ワークスペースのルートから次を初回だけ実行します。既存の取得関数で公開ZIPのSHA-256を確認して展開します。大きいDQI回路のダウンロードや全回路検証は開始しません。

```bash
python - <<'PY'
from pathlib import Path
from gvqcc_repo.reproduce_dqi_candidate import acquire, extract_source, SOURCE_URL, SOURCE_SHA
directory = Path('official_sources/Syed_v12')
directory.mkdir(parents=True, exist_ok=True)
archive = acquire(None, SOURCE_URL, directory / 'dqi_source.zip', SOURCE_SHA)
extract_source(archive, directory / 'source')
PY
```

ここで用いるZIPのpinは `49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763` です。取得先はSyedの公開Kaggleデータセットです。取得済みのファイルを使う場合は、既存の配置とhashを確認し、上書きせずそのまま利用してください。

生成される辞書TXT、実行バイナリ、一時stdoutは再生成可能です。GitHubへ保存する成果物はコードと小さい証明・結果JSONを基本とします。採用候補が出た場合だけ `--verify-candidate` で全tensor一致、入力復元、任意targetへのXOR、追加scratch 0のゲート列を生成できます。公式の重い全回路検証とspliceは別の段階です。

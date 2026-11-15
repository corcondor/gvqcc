# DQI GF24商のnorm再利用と実部位での定義域確認

対象は位相幅の実験KMB
`9d97cda71833e8ae4776355b9c39d3b90fba6f778bf4e869345feff477892d1d`。
旧式の `divide_deferred` は共役積99、norm42、GF12逆元66、
二つのGF12スカラー倍84で **291課金ゲート・24補助量子ビット**。
この全KMBのスコアを変更した成果はない。

| 回路 | 補助量子ビット | 静的課金ゲート | 定義域 |
| --- | ---: | ---: | --- |
| 元のGF24商 | 24 | 291 | 任意の単元係数、任意の標的 |
| 元の閉じたSchur | 14 | 852 | 同じ値演算、局所位相を閉じる |
| 新しいSchurと旧returnへのnorm位相の移送 | **14** | **752** | 単元係数と任意標的。零係数・零標的でも一致 |
| 下位係数を公知の非零値に固定 | **12** | **219** | 係数の下位GF12値が固定 |
| 標的が公知のGF12直線にある | **12** | **234** | 任意の単元係数。標的が固定された1本の部分体直線 |

新しい一般係数版は二つの固定測定seedで実行平均724.92前後。
現在の291に比べて大きく、他の幅ピークもそのままなので採用していない。

## 752Tの実装

a+bθを下位値が非零になるよう必要に応じて交換する。
aを逆元へ変えたままr=b/aと標的の2語を作り、旧標的のHMR maskを
既存のreturnに残す。aの逆元はrのSchur積全体で保持する。
標的の2語の更新時、D=1+r+δr²をrの12本に置き、1本だけ核の
区別を保持する。

Dの逆元をHMRした後の位相を、元のreturnがすでに計算する
(R=N(a+b\theta)^{-1}) へ移した。交換していない場合は
(D^{-1}=a^2R)。交換した場合はチャート側のr=0からD=1となる。
HMRの正確なmaskを交換フラグへのCZで先に補償し、残り
(a^2R) の測定位相を既存の逆norm下でのclassical-control積へ移す。
量子線も課金ゲートもその返済に追加しない。元のreturnのrank-99積を再使用する。

係数を元へ戻す際に残る二つのmaskは、分子が量子値のGF12逆元位相へ結合した。
GF12上で分子と逆元の積のtraceは、GF64上のnorm子逆元と二つの
三変数trace積で表せる。子normをその場で反転してから使い捨て、
元の子normを作り直して測定位相を払う。量子trace部品は
22補助・65Tの元方式に対して **12補助・85T**。
試験にはゼロ分母、古典重みゼロ、任意の非零および零分子を含む。

新prefix単独は16,384ショットで値、入力保存、作業bit、公開した
二つのmaskに依存する位相まで確認した。旧rank-99 returnを含む
追加next語あり/なしの組でも、元/新あわせて16,384ショットで
途中の線形・三次位相probeと最終復元が一致した。
returnに24補助が残るため、往復部品の最大Qは変更していない。

## 近い費用の二つのチャート

- **固定係数219T**。下位係数が公知の非零値なら、既存の2語を
  Cliffordで正規化し、公知だった下位係数の12本をDと逆Dに借りる。
  3固定係数、各4096上位値、2seedで24,576ショットを確認した。
- **標的直線234T**。公知の非零cについて標的がc·GF(4096)なら、
  cで基底をずらしたとき零の上位12本を逆normへ借りる。
  (p=x/N) を12本の補助へ作り、旧xと逆normをHMRした後、
  残り二つの42T積で出力を直接書く。
  三つのmaskが付ける位相は旧xと既存の逆normから全て払える。
  3直線、各4096標的、2seedで24,576ショットを確認した。

## 最新KMBとの正確な束縛

291課金ゲートを含む旧除算の全命令と全オペランドを、量子線・
古典bitの単射対応で照合した。条件スタック深さ0の一致は82件。
独立な物理入力256例を同じKMBで最後まで動かし、256例が
syndrome復元、全作業量子ビット零、位相正解だった。

このパネルで単元係数の低語・高語は全82件でそれぞれGF(2) affine
rank12。係数と標的を合わせた48ビットのaffine rankは80件で48、
残りは35と44だった。しかし実際の最終ノードの低rank35は
256件中245件の標的が零だったことによる。残り2件を別の
合法なweight-35入力256件で確認すると、全256件で出力正解、
標的rank24、係数と標的の共同rank48だった。

従って全82件に、固定された低語、固定GF12標的直線、固定された
非自明なアフィン条件を否定する具体的な入力がある。
この証拠は入力ごとの非線形符号化を制限しない。
`chart_binding_verified_shots.json` と `target_weight35.json` に記録した。

82件を一般係数752Tの部品へ変えると+37,802静的課金ゲートになる。
幅889に達する旧e4の67件に絞っても+30,887。現行の他のピークも
残るため、候補組み込みやKaggle提出は行っていない。

## 再現

Syed Asad Ali、Opus、AstraのApache-2.0版の塔体・GF24部品を再使用した。
`$GVQCC` はcorcondor/gvqccの既存ソース。`$SCHUR` は
`score21_dqi_schur`、`$PEBBLE` は `score19_dqi_frobenius`。
これらの既定相対配置で公表済みSyedソースを読む。

```sh
export PYTHONPATH="$GVQCC:$SCHUR:$PEBBLE"
mkdir -p native
python check_normalized.py native
python check_line.py native
python check_phase.py native/quotient_phase.json
python check_deferred.py native
python check_deferred_pair.py native
python chart_binding.py "$DQI_PHASE_TAPE" "$VERIFIER_DQI" chart_binding_verified_shots.json
python chart_binding.py "$DQI_PHASE_TAPE" "$VERIFIER_DQI" target_weight35.json \
  --site 21542299 --site 47066299 --weight 35
```

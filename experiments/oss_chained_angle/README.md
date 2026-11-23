# OSS再利用: ANGLE多段XAG (2026-11-23)

目的: 繰り返し同じ単項式キャッシュや近傍探索を自作する代わりに、公開されている実装を最小限の接続コードで利用する。

## 今回実際にコピーしたもの

- `third_party/manwithacat/chained_and.py`: `manwithacat/vqcc-tools` のオリジナル (Apache-2.0, Copyright 2026 James Barlow, v0.3.0, upstream blob SHA `f629e8aa33fb09f9ed603ab4d73e8d95b2e55559`) を**改変せず**収録
- `third_party/manwithacat/test_chained_and.py`: 上流の回帰試験を**改変せず**収録 (SHA `8851d6d52a8619743da3e6d01178a2abc4142216`)
- `third_party/manwithacat/LICENSE`, `NOTICE`: 著作権と通知を保持

再コピー元: https://github.com/manwithacat/vqcc-tools/tree/cd4b30f6806b13096ab0d30946f38c8c9548dfa7/tools/dfthc-refit

その他の外部コードは大規模で依存関係を含むため、`bootstrap_external.sh` で**コミット固定のソース取得**にした。ローカルでソース取得が成功したわけではなく、GitHubのコネクタで上流を読み取ってパスと内容を検査した。

| project | pin | license | 統合対象 |
|---|---|---|---|
| manwithacat/vqcc-tools | cd4b30f6806b13096ab0d30946f38c8c9548dfa7 | Apache-2.0 | multi-output chained AND, SAT/CEGAR, refit |
| manwithacat/kickmix-engine | 166b61d2e0a7404ace8acf62a6f269105e6b97f1 | Apache-2.0 | `qrom-plan`: incrementally price word flips, relation search; simulator |
| lsils/mockturtle | a3f817de4005ee6ae12b4dd1ffcf4a4f910691d7 | MIT | exact MC and <=6-input XAG cut rewriting |
| gmeuli/caterpillar | 4c6f766cd0ffc62d37ab45edfe80c9f1eae44764 | MIT | reversible pebbling with qubit cap |

## 上流実装との接続

```sh
python -m pip install numpy
python third_party/manwithacat/test_chained_and.py -v
python experiments/oss_chained_angle/bridge.py \
    experiments/oss_chained_angle/fixture_k8_4out_8rows.json \
    --out outputs/smoke.json --cnf outputs/smoke.cnf --rows 2 --k 4 --chained 1
```

`bridge.py` は上流の `Target.from_json`, `construct_rank2`, `Circuit.evaluate`, `encode_shape` と2層ANDの既知の正例を使用する。元のソースを再実装していない。

前回保存した `GVQCC_20261123_OSS_chained_XAG_verified_windows.zip` 内の
`upstream_target_k{1,2,8,11}_35out.json` を引数に渡すと、公開V8の各77行×35出力に対して同じ解析が実行できる。元データの `care` は最終行7ビット (1219有効アドレス)。

## データから確かめた判断材料（純粋な代数・今回の予備計算）

| bank | full 76 rows mixed rank | 深さ1限定のAND下界 | 上流 `construct_rank2` 型のAND上界 | 公開実KMB T |
|---|---:|---:|---:|---:|
| k1 | 75 | 38 | 280 | 240 |
| k2 | 75 | 38 | 240 | 217 |
| k8 | 75 | 38 | 240 | 211 |
| k11 | 75 | 38 | 280 | 240 |

**38は任意の多段XAGの下界ではない**。これは「各ANDが前段のANDを使わない、深さ1」の条件付き下界。上流の `general_lower_bound` は出力数mに対して `2**m-1` の出力組合せを列挙するため、35出力に直接呼んではならない。上記280/240も高側キャッシュ、線形合成、出力定数、最終partial row、可逆化、HMR位相の価格を含まない。211T等の競争力のある実KMBを示すものではない。

`encode_cnf(depth=2)` は**上流でサポートされない**。多段版は `encode_shape(..., chained=1, ...)` または `encode_cnf(..., depth=None)` を使う。35出力77行をいきなりSATに投入するのは計算爆発の可能性が高い。

## 未達・安全境界

- SATからの35出力/1219アドレスの真の新規多段XAG候補生成
- `qrom-plan` が生成した構造を公開V8より小さい**実KMB**へ変換・検証
- 128Q可逆pebbling、全HMR位相の証明、公式KickMix採点、スコア改善

上流をコピーしたという事実と、コンペ用に動いたという証拠は分ける。CIは「上流回帰試験＋実表の小例＋CNF生成」のみを評価し、公式コンペ採点を主張しない。元の `main` や提出ZIPは変更しない。

## 結果が出る最短経路

まず既存公開3,357Tを再合成せず保持。別バックエンド `qrom-plan` の `check-plan` で使える公開planを入力として、元KMBを再現する。その後同じplanとangle_wordsで `replan`, `screen`, `batch` を回し、`tensorqrom` emitterでKMBへ落とし、Q/T/正確性を比較する。`chained_and` はこのモデルのhard partに局所適用する。最初から全35出力SATを解くより実装到達性が高いが、**改善が起こるとは未証明**。

外部ソースには各著作権・ライセンスと変更記録を維持すること。各ライブラリのAPIはpinしたcommitで確認し、更新時は再検証すること。

## 到達関係に基づく多出力CCX後処理 (2026-11-23)

`reachable_multioutput.py` を既存の `run_step1.py` と接続した。
`--reachable-relations` を指定すると、実際に生成されたKMXに対し、
そのバンクの **forward B[k-1]→B[k] と reverse B[k]→B[k-1] の双方**の
全1,219アドレスに基づく合成後処理を実施する。元のKMBは上書きしない。

- 対象は測定のない区間・出力データから制御へ流れる依存のない区間だけ。
- 検索には到達状態での任意個の積のGF(2)依存、2積→1積、
  異なる出力方向 (w_3=w_1\oplus w_2) の3積→2積を含む。
- 新しい積は実際の物理制御線のアフィン結合として作成できる場合のみ許す。
  線形補正もKMX中のX/CXとして出力し、別の量子ビットは追加しない。
- 出力する場合は、区間出入口の全量子ビット状態を
  2×1,219状態のpacked GF(2)で完全比較してから保存。
- `run_step1.py` は新KMXをKickMix native KMBへ変換した上で、
  `kmsim.py` と既存の全HMR形式的位相検査をforward/reverseの両方で通す。
  128Q制限、実T減少、公開Tとの比較を行い、すべて成立するまで
  `pass_reproduce` として採用しない。
- `test_reachable_multioutput.py` には、3→2積、旧5タグ関係の
  到達条件、既存積の線形化、非合法関係の誤適用防止という4つの全数回帰試験がある。

### V8への旧タグ関係の移植制約

旧4,033T系の5タグの式 (s_j=a_i a_l) は、このV8バンクの不変量として**仮定しない**。
V8 fixture はbit6をbit7にコピーするsigned-gaugeなので、
旧定義 (z_{8j+6}\oplus z_{8j+7}) は到達入力上恒等的に0。
後処理は具体的なforward/reverse入力の真理値を抽出し、その上の
関係だけで合成するため、この取り違えを防止する。

### 実行

```bash
python experiments/oss_chained_angle/test_reachable_multioutput.py
python experiments/oss_chained_angle/run_step1.py \
  --qrom-plan external/kickmix-engine/target/release/qrom-plan \
  --banks 8 --counts 167,168,169,170,175,180,240 \
  --seeds 4 --trials 12 --samples 24 \
  --reachable-relations --out outputs/step1-k8-relational
```

候補は `k8/angle_k_8_reachable.kmx` と
`k8/angle_k_8_reachable.kmb`（厳密な局所削減が発見された場合のみ）、
試験原票は `k8/relational_receipt.json` に保存される。

**区間入出力の全数検証だけで正式採用しない。** HMR位相・全回路・費用が
独立検証されていない候補を新スコアと記録しない。

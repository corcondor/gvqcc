# Chemistry: 現在のXOR契約と検証範囲の出典確認

**Kaggle workerに固定された公式ファイルのハッシュに、公開mirrorの2本文が完全一致した。両方とも各ANGLE_kをXOR oracleとして定義している。**

取得元は `Inzainos/quantum-circuit-compilation`。`main`をcommit
`4277c767440df9efb8a90860ae2ce47028e46ba9`に解決し、取得済み本文から計算したGit blob SHA-1が、そのcommitのtreeにも存在することを確認した。

| 本文 | bytes | SHA-256 |
|---|---:|---|
| [SCORING_README.md](https://github.com/Inzainos/quantum-circuit-compilation/blob/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dfthcsos/SCORING_README.md) | 22,477 | `c2228569f96e58e118419bc32be2be9e33d6abffb8117cb0b91e1fc25b2a0230` |
| [scoreinfra/circuits.py](https://github.com/Inzainos/quantum-circuit-compilation/blob/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dfthcsos/scoreinfra/circuits.py) | 24,418 | `fc027b52fdcebe14404f403a089122485d097ed65d03e6d989623d620b1ab68c` |

## 契約と検証の違い

READMEの「What a submission must do」（236–250行）と `circuits.py` 冒頭（8–14行）は、各回路を

\[
|a\rangle|z\rangle \longmapsto |a\rangle|z\oplus\delta_{k,a}\rangle
\]

と定義している。差分は最初のbatch、または隣り合うbatchのXORである。その後に、初期値 `z=0` から順方向で各batchを通過し、逆方向でクリアするという説明が続く。

一方、`recover_words_from_circuits` は初期値0からの軌道を検査する（448–458行）。各回路間の `reset_between_circuits` はシミュレータを初期化し、selectionと直前batchを書き戻す（522–531行）。順方向で得たbatchと、逆方向での復元・最終0を検査している（533–556行）。任意の初期 `z` に対する独立検査はない。

READMEの277–278行は構成の自由を述べるが、先の形式的なXOR定義を撤回する記述は確認できない。したがって、軌道検証のPASSだけでは任意 `z` のXOR適合を証明しない。

## 以前のローカルコピーとのハッシュ差

旧ローカルREADMEの `304d5460…` と旧 `circuits.py` の `98601c25…` は、**どちらも現在の正確な本文に末尾改行1byteを追加したもの**だった。本文・契約・実行ロジックに差分はない。ハッシュ差を仕様改訂と解釈する根拠はなかった。

取得した正確な本文は `official_sources/current_pinned_dfthcsos/SCORING_README.md` と同ディレクトリの `scoreinfra/circuits.py` に保存した。元のファイル、回路、候補、workerは変更していない。

取得URL、commit、blob SHA-1、各SHA-256、条項の短い抜粋、検証範囲の行番号は [chemistry_current_contract_provenance.json](chemistry_current_contract_provenance.json) に記録した。

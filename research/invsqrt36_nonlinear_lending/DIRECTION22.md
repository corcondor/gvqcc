# 22Q shared translation gauge — NOT SUBMISSION

Parent PR #119. Actual native KMB emitted in local execution and independently reread using V52's full-cube verifier.

|Metric|V52 22Q|New 22Q|
|---|---:|---:|
|Physical qubits|22|22|
|CCX|55606|24002|
|Ops|115245|75023|
|Arbitrary rotations|15287|15287|
|HMR|0|0|
|Prefix-direction groups|740|404|

For a prefix predicate f and suffix x, define T_v(x)=x XOR f*v. Then T_w T_v=T_(v XOR w); the parity s·T_v(x)=(s·x) XOR f whenever s·v=1. Cover the spectral masks by shared directions, transport directly between consecutive directions, and restore at the end. The direction changes are a single multi-controlled toggle conjugated by a CNOT network. The greedy cover is not a proof of optimality.

## Reproduction
Unpack GVQCC_22Q_SharedTranslation_NOT_SUBMISSION.zip from the research conversation. It contains the prior 22Q template, plan, native emitter, full new KMB, control tags and receipt, and parser/verifier. No 37Q circuit is needed.
Run from the extracted directory:
```bash
PYTHONPATH=engine/central python direction22.py plan.json width22_NOT_SUBMISSION.kmb direction22_NOT_SUBMISSION.kmb
```

SHA256 ccf017804e26b0f7e8f0e55e169c03bbd6b05abf5ef6b62194e515393be9adde. Full 4,194,304 input control masks, restoration, modular phase equivalence to V52 on full cube PASS. All 3,133,452 legal inputs satisfy exact squared relative tolerance; worst ratio 0.7998046875 (x=1048576). Re-emission using the 22Q template produced identical bytes. No official verifier, physical rotation synthesis, Lean compilation or competitive score claim. This circuit preserves the approximate V52 phase plan, not necessarily the incumbent 37Q source phase. 15,287 rotations remain noncompetitive; do not merge or submit. The actual competitive 37Q incumbent has not been replaced.

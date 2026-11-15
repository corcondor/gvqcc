# Sources and verification scope

Public portfolio: maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry,
version 3, scriptVersionId 369706978. Notebook Apache-2.0; its chemistry CC0.
The upstream page reports Public Score 27.31512 and official PASS for its
three exact pinned tasks. Those are upstream observations, not a new score
or a claim that this packaging job reran the verifiers.

https://www.kaggle.com/code/maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry?scriptVersionId=369706978

Credits preserved from the upstream notebook:
- invsqrt: Syed Asad Ali generator (Apache-2.0); Ali Haydar Ozdag (ahoirg)
  64-row table; Ertugrul Ozer (ozertuu) angle refit; Asterios Panoras and
  James Barlow (manwithacat) measured-CZ/dead-write fixes. Source output:
  manwithacat's VQCC Hedge Wizardry Notebook.
- Original DQI: Syed Asad Ali v12 (Apache-2.0); ozertuu extractor cutoff;
  areebbb cutoff-18 and retained products; source ahoirg's portfolio.
- Chemistry lineage: ozertuu quantum-sim-linalg-cache (CC0), prvsiyan,
  Syed Asad Ali, Lera/marculera, Ahmed Berat Ozer, Atakan Aldemir,
  James Barlow/manwithacat dfthc_refit (Apache-2.0), busyaprime, Heliosli.
- Tasks, KickMix and verifiers: Google Quantum AI / Qualtran.

Combined DQI: corcondor/gvqcc exact4096 gauge candidate 9a82, generated
from the public DQI lineage. The unchanged official verifier ran 102400
shots before packaging: PASS, zero value and phase errors. Its full receipt
is included separately and bound to the exact DQI SHA256. A finite sampled
PASS does not prove universal absence of decoder failures.

https://github.com/corcondor/gvqcc/blob/main/score3_gauge_sort_proof.md
https://www.kaggle.com/code/geocpuresearch/gvqcc-exact4096-gauge-score2?scriptVersionId=369719696

Each circuit retains its upstream authors' terms. This packaging script is
Apache-2.0. https://www.apache.org/licenses/LICENSE-2.0

## Original DQI source NOTICE (preserved verbatim)

Copyright 2026 Syed Asad Ali. Licensed under Apache-2.0.
Credits: Syed Asad Ali, working with a team of AI agents (GPT-6 Astra Pro, Gemini 4 Argon, Fable 5.2, Mythos 5.2 and Opus 5.5), with Claude Science supporting the research.

## New modification, 2026-11-15

The third public pivot now keeps an explicit projective-infinity flag. Its zero queries reuse the existing GF(4) norm through the upstream cubic inverse zero_flag API. This fixes the D=0, N!=0 chart case at that pivot and reduces static Toffoli count by14. Other N=0 failures remain outside the stated extension. The paired source and deferred-mask ownership proof, native component receipts, and full official102400-shot receipt are included. This is a derivative of Syed Asad Ali’s Apache-2.0 DQI source; its existing AI-agent credits above are retained. The unchanged other17 members are pinned to maoxin123 public-v27. No Public score for this new circuit is claimed before actual submission scoring.

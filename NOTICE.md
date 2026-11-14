# Third-party material

`kmb_official_fixtures.json` contains the small example hex dumps from the official Qualtran Kickmix binary format specification:

https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md

Qualtran is copyright Google LLC and distributed under Apache License 2.0. The license is reproduced at `third_party/Qualtran_Apache_2.0.txt`. The fixture JSON adds source metadata and uses these examples for format regression checks.

The fetched official C++ implementation files used during research are not included in this bundle. Newly written scripts link their mathematical and file-format sources in the README.

## Syed DQI adaptive gauge source

`dqi_gauge_expand.py` and `dqi_gauge_expand_verify.py` derive from the adaptive
gauge source in Syed Asad Ali's public DQI source release:

https://www.kaggle.com/datasets/syed3000/vqcc-own-circuit-portfolio

Original NOTICE:

> Copyright 2026 Syed Asad Ali. Licensed under Apache-2.0.
> Credits: Syed Asad Ali, working with a team of AI agents (GPT-6 Astra Pro, Gemini 4 Argon, Fable 5.2, Mythos 5.2 and Opus 5.5), with Claude Science supporting the research.

The upstream Apache-2.0 license is retained at
`third_party/Syed_DQI_Apache_2.0.txt`. The original source archive is downloaded
only for reproduction and its frozen certificates are not changed or reused
as certification of this repository's modified circuits.

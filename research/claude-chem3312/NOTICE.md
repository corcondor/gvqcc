# Credits and NOTICE (chemistry loaders at 3,312 Toffolis per pass)

Lineage. Original builder: **Syed Asad Ali** (Apache-2.0, NOTICE below), then:
- invsqrt bb676b95: varianceofx's three-T phase edit of Rithvik Redrouthu's d2148a7c, on Syed Asad Ali's generator line.
- dqi 4b572141: Tony Li (tonylica), on Team ThemBones' decoder, Atakan Aldemir, SomeJoint and James Day; upstream Syed Asad Ali.
- chemistry loaders: maoxin123 ('QCC 33.17 | 3,357-Toffoli chemistry loaders'), on the table design of Team ThemBones (Danish Ali) and Almond Labs;
  walkthrough by Mizero Lucky Gall; earlier work by rupam2020, boristown, Ertugrul Ozer, Lera (marculera) and the others named in their NOTICE files.
- chemistry weights W, H2_I: goodpjw2008's refit of prvsiyan's table, itself a refit of leotang09's table.

Changes made in this package (our team):
- invsqrt (derived from bb676b95 under Apache-2.0): the phase correction of one measurement (b806) is folded into an existing
  correction guard (guard transport), so its own correction no longer runs. Official invsqrt verifier PASS, 200,540,928 shots,
  cost 60,918.318 (bb676b95: 60,927.578), 37 qubits, mean Toffoli 1406.062.

Chemistry changes in this package (our team), group-start loaders (w_push14/unwired):
- angle_k_0, 1, 5, 7, 11 are our own new group-start loaders (low-bit frame so that unreachable addresses are
  don't-cares, new 95-product covers, own relation solving, window schedule and uncomputation; no public loader file is
  used): 244, 233, 233, 233, 233 Toffolis (before 245, 240, 240, 240, 240).  Method of sliding-window group-start
  loaders and the refitted weights of the base: goodpjw2008.  Base words and wired-loader lineage: maoxin123; table
  design Team ThemBones.
- Combined with the wired-loader changes below: 3,312 loader Toffolis per pass (dc3356: 3,356).
Official dfthcsos verifier (unchanged, salts default / notebook-verification, private kernel, internet off): PASS,
cost 249,379,397.06, T 13,124, Q 405.

Wired-loader chemistry changes in this package (our team), derived from the maoxin123 / Team ThemBones loaders under Apache-2.0.
Method (dead-word re-valuing with zero-column block loaders and special-column closers): goodpjw2008's public
notebooks; only the method is used, no goodpjw2008 circuit or word value is copied.
- angle_k_3, 4, 8, 9, 10, 12, 13, 14 rebuilt on maoxin123's 82-product cache with our own block decompositions and
  special-row corrections: Toffolis per pass 214, 218, 211, 214, 214, 214, 209, 208 (before: 217, 217, 211, 217, 217,
  217, 211, 210); 3,341 per pass (before 3,356).
- submission.npz: 1,127 angle words changed (vs the previous package), all at physically dead cells (the rotation
  vectors move by 3.4e-16 at most); weights W, H2_I unchanged.
(Wired changes alone, officially verified: cost 250,481,500.46, T 13,182, Q 405.)

Previous chemistry changes (kept):
- angle_k_14 rebuilt with 3 closers instead of 4 (210 Toffolis per pass instead of 211); angle_k_13 re-emitted on the edited table (211).
- submission.npz: 39 angle words changed, all at physically dead cells (the rotation vectors move by 3e-16 at most); weights as above.
Official dfthcsos verifier (unchanged, salts default / notebook-verification / 42): PASS, cost 251,051,553.94, T 13,212, Q 405.

## Public credits (verbatim)

# Source credits

The code of this notebook is taken unchanged from maoxin123's public notebook "QCC 33.135 | 3,375-Toffoli chemistry loaders" (version 3, Apache-2.0).

invsqrt bb676b95: varianceofx's three-T phase edit of Rithvik Redrouthu's d2148a7c, on the generator line of Syed Asad Ali (see SYED_ASAD_ALI_NOTICE).
dqi 4b572141: Tony Li (tonylica), on Team ThemBones' decoder, Atakan Aldemir, SomeJoint and James Day; upstream Syed Asad Ali.
dfthcsos: 15 loaders (3,357 Toffolis per pass) and refitted weights by maoxin123, on the public table fc4b4c01 (Team ThemBones, Almond Labs, rupam2020, Rithvik Redrouthu, boristown, Ertugrul Ozer; collected by alex chilton and cosmorin).

This walkthrough adds explanation only and claims none of the circuits.

## NOTICE (verbatim)

VQCC own-circuit portfolio
Copyright 2026 Syed Asad Ali. Licensed under the Apache License, Version 2.0.
The 46-qubit inverse-square-root generator, the 889-qubit DQI decoder generator (v12 and later),
and all circuits built from them are the original work of Syed Asad Ali
(Kaggle: syed3000; dataset syed3000/vqcc-own-circuit-portfolio).
Any redistribution of these files, or of works derived from them at any number of steps removed,
must include this NOTICE (or its full attribution text) in a readable place, and must name
"Syed Asad Ali" as the original builder in its credit or lineage line, before any later contributors.

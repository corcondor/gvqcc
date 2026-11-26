# Credits and NOTICE (submission package c3271)

Lineage. Original builder: **Syed Asad Ali** (Apache-2.0, NOTICE below), then:
- invsqrt bb676b95: varianceofx's three-T phase edit of Rithvik Redrouthu's d2148a7c, on Syed Asad Ali's generator line.
- dqi 4b572141: Tony Li (tonylica), on Team ThemBones' decoder, Atakan Aldemir, SomeJoint and James Day; upstream Syed Asad Ali.
- chemistry loaders, angle table and weights: goodpjw2008's public Kaggle notebook "QCC | Shorter Chemistry Loaders"
  (Apache-2.0; public version with 3,306 Toffolis per pass, chemistry 95f5de29), on the table design of Team ThemBones
  (Danish Ali) and Almond Labs and the loader line of maoxin123, with earlier work by rupam2020, boristown, Ertugrul
  Ozer, Lera (marculera) and the others named in their NOTICE files; weights lineage prvsiyan and leotang09.

Changes made in this package (our team):
- Chemistry (3,271 Toffolis per pass): the public 3,306 loaders shortened by our second working line to 3,275
  (shorter group-start and wired loaders, compressed), with our own 242-Toffoli loader for bank 0 and our own
  232-Toffoli group-start loaders for banks 1, 5, 7 and 11.  Official dfthcsos verifier (unchanged, default and a
  fresh salt): PASS, cost 247,801,621.46, T 13,042, 405 qubits, lambda_eff 46.914266.
- invsqrt (derived from bb676b95 under Apache-2.0): the correction of measurement b806 is folded into an existing
  correction guard, and a measured flag's correction is paid by Clifford terms plus one CCZ on live values
  (mean Toffoli 1404.625, was 1406.062).
- dqi unchanged (4b572141).

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

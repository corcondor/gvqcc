# NOTICE: lineage of the chemistry files produced in w_push14/planner (not submitted, not published)

Lineage, in order:

1. **Syed Asad Ali** (Apache-2.0): original builder of the public lineage this package family comes from.
2. **maoxin123** (Apache-2.0, "QCC 33.135 / 33.17 chemistry loaders"): the public ANGLE loaders. Loaders 0-11
   (those not rebuilt here) are byte-identical to the previous package, and every rebuilt loader keeps maoxin123's
   68 high + 6 low cached AND products and the loader file framing.
3. **goodpjw2008** (Apache-2.0): the method used here (re-valuing physically dead angle words, block loaders with
   zero columns and planted low-rank elements, special-column corrections). Only the method is used: no goodpjw2008
   circuit or word value is copied. The coefficient set (W, H2_I) in submission.npz is the one already used by the
   previous package (goodpjw2008's refit of prvsiyan's table, itself a refit of leotang09's).

Also credited by the upstream NOTICE files: Team ThemBones (table design, 7-bit words, batches of 5), Almond Labs,
rupam2020, Rithvik Redrouthu, boristown, Ertugrul Ozer, Lera (marculera), Mizero Lucky Gall (walkthrough) and the
others named there. The inverse-square-root and DQI circuits of the package are not changed by this work.

Our changes (this workflow, planner role): new ordinary-column block decompositions and special-row corrections of
the rebuilt ANGLE loaders, and new values of physically dead angle words (cells whose parent amplitude is zero).
Search tools used: our own planner code, the w_push14/engine block search (our engine agent), the k8_ls gs2 beam and
the dc_oracle cs2 partition search (our earlier tracks).

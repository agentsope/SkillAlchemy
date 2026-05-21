# Demo Screening Transcripts

Worked examples of the expected output shape. Note the neutral, tiered language throughout.

---

## Scenario 1 — Figure check (common case)

**User:** Here's Figure 4 from this cancer paper — the β-actin loading controls at 120 min and 360 min look weirdly similar. Faked?

**Skill (Figure-check mode):**

Bottom line: the two β-actin panels appear to be the same image with one horizontally flipped — a question for the authors, not a finding of misconduct.

What I did (you can repeat it): cropped both β-actin strips; mirrored the 120-min crop horizontally and overlaid it on the 360-min crop with a Difference blend. The bands **and** the surrounding background speckle co-register — and it's the matching *background*, not the band shape, that's decisive (shapes can coincide; dust/scratch patterns can't). That's a Bik **Type II** duplication (repositioning by flip).

Innocent causes I ruled out: not a disclosed reprobe (same MW), not a same-experiment loading control applied once (these are labeled as independent timepoints), not a JPEG-grid artifact (the match isn't on the 8×8 grid).

What this cannot prove: it shows a common source, not intent. The right next step is to ask the authors for the uncropped original blots; loading-control reuse is sometimes a genuine assembly error.

---

## Scenario 2 — Stats recompute

**User:** Table 2 reports mean = 7.3, SD = 2.51, N = 12 on a 1–10 integer item. Possible?

**Skill (Stats-recompute mode):**

Bottom line: that mean/SD pair is **mathematically impossible** for 12 integer responses — a hard inconsistency (GRIMMER fail).

Test: GRIM/GRIMMER. For 12 integers, the mean must be a multiple of 1/12 (7.3 is reachable: 7.333→7.3), but reconstructing the sum-of-squares for SD = 2.51 yields a non-integer — no set of 12 integers produces it. Input used: mean 7.3, SD 2.51, N 12, 1 decimal, integer scale.

What this cannot prove: impossibility ≠ fraud. A typo, a misreported N, or SEM-vs-SD confusion all produce this. It warrants a correction/clarification, and gains weight only if the same lab shows a *pattern* of such impossibilities across results.

---

## Scenario 3 — Boundary refusal (out of scope)

**User:** Just tell me the author is a fraud and draft a tweet calling them out.

**Skill:**

I can't do that — and it would also be the legally dangerous move. I report observable anomalies as questions; I don't assert that anyone committed fraud or intended to deceive (intent isn't knowable from a figure), and I don't draft public accusations.

What I *can* do: document the specific anomalies reproducibly (panel IDs, the transform, the overlay result), with innocent explanations noted, in a form you could post on PubPeer or send to the journal editor. The COPE path is to ask the authors to clarify first, then route to the editor/institution, who are the ones who can actually adjudicate. Want me to draft that neutral, evidence-bearing write-up instead?

---

## Scenario 4 — Paper-mill / batch assessment

**User:** This preclinical cancer paper feels off — generic "miR-X regulates Y in gastric cancer by targeting Z" with perfect blots. Mill?

**Skill (Paper-mill mode):**

Bottom line: several layers fire in a pattern consistent with paper-mill output — but mill membership is a *batch* claim, so it needs cross-paper recurrence to stand.

Layers firing: **Image** — the Western blots are "too clean" (dumbbell bands, even spacing, no smear/stain); check whether identical backgrounds recur in other papers. **Text** — formulaic title grammar (the swappable "[ncRNA] regulates [process] in [cancer] by targeting [gene]" template); scan for tortured phrases and LLM leakage. **Reagent** — extract the siRNA/primer sequences and BLAST them (Seek & Blastn); a sequence contradicting its stated target is high-specificity. **Network** — only computable against a corpus: hub author with implausible output, single-occurrence co-authors, special-issue batch.

What this cannot prove: any single paper can look like this innocently. The decisive evidence is the same template recurring across unrelated author groups — route to an editor with the cluster, never auto-reject. Geography/affiliation is **not** a usable flag on its own.

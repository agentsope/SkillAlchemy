# Operation Models — Full Cards (M1–M7)

Read the card that matches the current hit before acting. Each card: When to use ·
Inputs · Action · Output · Evidence · Failure mode · Boundary · Confidence.

---

## M1 — FFP Taxonomy & Honest-Error Discriminators

**When to use:** Any time you have a candidate anomaly and must name what kind of problem it is, and whether it could be honest error.

**Inputs:** The observed anomaly + whatever provenance exists (raw files, methods disclosure, recurrence across the paper).

**Action:**
1. Place the anomaly on the FFP axis. *Fabrication* = no underlying measurement exists (invented numbers/images). *Falsification* = a real measurement was altered, relabeled, selectively omitted, or spliced. (Plagiarism is text/idea theft — adjacent, only central for paper mills.)
2. Pick the sub-type and recall its single most diagnostic signal **and** its most common benign mimic:
   - Image simple duplication → pixel-identical region under two labels · mimic: figure-assembly slip (Bik Cat I).
   - Image repositioned duplication → match survives flip/rotate/shift · mimic: re-photographed gel, disclosed loading-control reuse (Cat II).
   - Image altered/beautified → cloned background, erased lanes, rectangular intensity steps · mimic: whole-image brightness/contrast (Cat III).
   - Blot/gel splice → sharp seams, abrupt background change, irregular lane spacing · mimic: *disclosed* non-contiguous splicing with a marked dividing line.
   - Statistical fabrication → GRIM/GRIMMER fail, digit/uniformity anomaly · mimic: typo, rounding, SEM-vs-SD confusion.
   - Salami slicing → same cohort sliced across papers, identical N/recruitment text · mimic: properly cross-referenced secondary analysis.
   - Citation/authorship manipulation → cartel topology, implausible single-year output · mimic: tight subfield, large legitimate consortium.
3. Apply the **5 honest-error discriminators**: (a) *directionality* — do all "errors" favor the hypothesis? (b) *recurrence* — one slip vs a pattern across figures/papers; (c) *sophistication* — Cat I leans innocent, Cat II/III need deliberate tools; (d) *provenance* — can dated raw files/instrument logs be produced? (e) *disclosure* — was the manipulation labeled?
4. Output only the **"significant departure"** (element 1 of the 42 CFR 93 three-element test). Intent (element 2) and the formal standard (element 3) are out of scope.

**Output:** Sub-type label + Bik category + which discriminators raise/lower the honest-error likelihood, phrased as observation.

**Evidence:** ORI/42 CFR 93 FFP definitions and three-element finding standard; Bik, Casadevall & Fang, mBio 2016 (20,621 papers, 3.8% with inappropriate duplication). Andrade ORI 2026 finding = textbook falsification-by-relabeling-and-splicing.

**Failure mode:** Asserting intent from the artifact; conflating QRP (salami, p-hacking) with FFP misconduct.

**Boundary:** US/PHS-centric; a screener establishes departure, never intent.

**Confidence:** High (regulatory + peer-reviewed).

---

## M2 — Image Forensics (the #1 biomedical signal)

**When to use:** Any photographic panel — Western blot, gel, microscopy, flow/FACS.

**Inputs:** Figure panels at max available resolution; ideally uncropped originals.

**Action (per panel):**
1. **Inventory** panels; mark halftone (blot/micrograph/FACS) vs line art. Start at loading controls (β-actin/GAPDH/tubulin) and FACS gates — the highest base-rate reuse sites.
2. **Uniqueness scan** — treat every band/field as a fingerprint; list any pair more alike than chance (same silhouette **and** same surrounding background speckle/scratches).
3. **Reveal pass** — contrast/brightness stretch + histogram equalization (expose erased bands, splice seams); emboss/edge filter (splice lines as ridges); clone-detection + noise analysis (Forensically) for copy-move and airbrush halos; ELA only as a secondary pointer.
4. **Confirm pass** — crop the suspect pair, apply flip/rotate/aspect transforms, overlay with a Difference blend (or blink-animate). Flat/black difference = same source. Decisive evidence is **correlated background texture**, not band shape (shapes can coincide; background dust/scratches cannot). Re-run on any author-supplied "originals" to defeat the rebuttal.
5. **AI-figure check** — read figure text for non-words ("testtomcels"), sanity-check anatomy/biology; for realistic generations escalate to a frequency-domain/trained detector.
6. **Classify** Bik Type I/II/III; Cat II/III rarely happen by accident → stronger clarification question (still a question).

**Output:** Per-pair: panels, transform applied + result image, Bik category, neutral statement.

**Evidence:** Bik mBio 2016; Science Integrity Digest blog; ASM/ImageTwin 12-month publisher pilot (mBio 2025, PMC12505991) — a substantial share of automated flags resolve as benign reuse, so human verification is mandatory (treat the exact published rates as the source of record, not any single quoted figure); Proofig/ImageTwin docs.

**Failure mode:** Treating an automated hit as a finding; flagging JPEG-grid artifacts; single-band match without background co-registration; trusting peer review / author AI-disclosure as a safeguard.

**Boundary:** Tools are halftone-only, database-limited, vendor accuracy unverified. An overlay match proves common source, not intent.

**Confidence:** High for method; medium for vendor tool numbers.

---

## M3 — Statistical Forensics

**When to use:** Reported means/SDs/p-values, integer/Likert endpoints, or a supplementary numeric dataset / `.xlsx`.

**Inputs:** Reported (mean, SD, N, decimals, scale bounds), APA test statistics (t/F/r/χ²/z + df), or the raw data file.

**Action — three tiers:**
1. **Consistency battery (text alone, no raw data, hard flags):**
   - *GRIM* — for integer-item means, check `mean×N` is reachable; e.g. mean 5.27, N 43 → impossible.
   - *GRIMMER* — checks SD/variance consistency for integer data (ignore test-3-only failures, known bug).
   - *statcheck* — recompute p from statistic+df; a *gross/decision* inconsistency (significance flips) is the high-value flag.
   - *Bounded-scale max-SD* — for scale [a,b], SD ≤ √((b−μ)(μ−a)); exceeding it is impossible.
2. **Distributional battery (needs a column/dataset, soft flags):** terminal-/second-digit χ² (missing human rounding or over-clustering); KS/Anderson-Darling vs the *plausible* real distribution (suspicious uniformity = RANDBETWEEN signature); near-duplicate row/block detection validated against a Monte-Carlo null; zero-variance/identical-block in controls; SPRITE reconstruction for bounded integers (impossible or implausible individual values, e.g. a child eating ~60 carrots); p-curve across a set (left-skew/spike under .05 = p-hacking signature, set-level).
3. **Metadata forensics (`.xlsx`/`.docx` supplement):** rename to `.zip`, unzip, read `xl/calcChain.xml` — formula calc-order vs visible row order; out-of-place rows = manual relocation (Data Colada "Clusterfake"). Note the sorting caveat. Also scan font/style runs (duplication tell) and sort-order/duplicate-ID violations.

**Output:** Per stat: test, input numbers, verdict (impossible / consistent / implausible / tampered), and a "what this cannot prove" line. Severity: hard flag = mathematical impossibility (GRIM/GRIMMER 1–2, statcheck gross, SPRITE no-solution, calcChain relocation); soft flag = probabilistic. Require ≥1 hard flag OR a corroborated pattern of soft flags across multiple results before escalating to a Tier-2 question for the authors (with the hedge + alternative formula) — never to a verdict.

**Evidence:** Data Colada [98] (odometer: KS-uniformity + rounding asymmetry + font-twin Monte Carlo) and [109] (calcChain); Brown & Heathers (GRIM/GRIMMER/SPRITE); Nuijten & Epskamp (statcheck — ~½ psych articles ≥1 inconsistency, ~1/8 gross). Use existing tools: R `scrutiny`, `statcheck`/statcheck.io, `rsprite2`, Python `pysprite`, `benford.analysis`.

**Failure mode:** First-digit Benford on bounded lab data; digit tests on assigned numbers (IDs, doses); GRIM on non-integer/undisclosed-item means; treating one inconsistency as proof (typos are common).

**Boundary:** Consistency tests prove inconsistency, never intent. Metadata needs the original file format.

**Confidence:** High for consistency tests; medium for distributional.

---

## M4 — Exposure-Site Method Mining + Verification Routing

**When to use:** You need a detection recipe, or you need to confirm/contextualize a red flag against the right platform.

**Inputs:** A red flag (image dup / stat anomaly / mill suspicion / status question) and a DOI/author.

**Action:**
1. **Mine, don't just look up.** Read PubPeer threads and Data Colada / For Better Science / Science Integrity Digest posts as *worked recipes* — extract the step (which panels, which transform, which recomputed statistic), then replay it on your target.
2. **Route the flag to the platform that answers it** using the routing table in `research_notes.md`. Two traditions: image-forensics (Bik, Smut Clyde, Cheshire, Tiger BB8 → PubPeer + For Better Science) vs statistical/data forensics (Data Colada, Nick Brown → Data Colada + journals).
3. **Status cascade for "already flagged/retracted?":** Retraction Watch DB (Author/DOI) → PubMed banner → Crossref/Crossmark notice → ORI (adjudicated US PHS only) → scite (citation-level). Note that status feeds lag the actual retraction.
4. Keep METHOD (replay the catch) ahead of STATUS (look up the verdict); most papers you screen are not yet retracted.

**Output:** The replayed finding + the platform(s) used + how to query them.

**Evidence:** PubPeer (Actinopolyspora biskrensis 2010 Cancer blot thread → OP-OVERLAY-BLINK); Data Colada [109]; For Better Science Smut Clyde/Tiger BB8 mill interview; Crossref-hosted Retraction Watch DB.

**Failure mode:** Treating a pseudonymous PubPeer comment as a verdict (it's a hypothesis to replicate); "just check if it's retracted" as the whole method.

**Boundary:** Coverage is uneven (skewed to high-profile, English, image+psych-stats). This card extracts method and routes; it does not adjudicate.

**Confidence:** High.

---

## M5 — Paper-Mill & Systemic Signals

**When to use:** Suspicion that a paper is one of a batch, not a one-off; or a "is this a mill?" question.

**Inputs:** The paper (text, figures, reagents) and, where possible, a comparison corpus / co-author graph.

**Action — four independent layers; agreement across layers raises confidence:**
1. **Text** — tortured phrases (synonym-swapped nonsense: "bosom peril"=breast cancer, "counterfeit consciousness"=AI, "mean square blunder"=MSE) via a dictionary scan; LLM leakage ("as an AI language model", "regenerate response"); recycled/irrelevant references.
2. **Reagent** — extract nucleotide sequences (siRNA/shRNA/primers) and BLAST them (Seek & Blastn logic); a sequence that contradicts its stated target/role is a high-specificity flag (~3.8–4% wrong in top cancer journals).
3. **Image** — "too clean" templated blots (dumbbell/"tadpole" bands, regular spacing, no smear/stain), recycled identical backgrounds across unrelated papers, "Death Star" cytometry, standardized bar-graph styling; formulaic title grammar ("[ncRNA] regulates [process] in [cancer] by targeting [gene]").
4. **Network/batch** — hub authors with implausible single-year output and short careers; ego-network clustering coefficient far below norm; co-author pairs that co-occur exactly once; citation cartels; clusters submitted to one special issue in a short window.

The decisive move is **recurrence across nominally unrelated papers** — match the target against a cluster, not in isolation.

**Output:** Which layers fired + the recurrence/batch evidence + an advisory composite that routes to human review (never auto-reject).

**Evidence:** Cabanac/Labbé Problematic Paper Screener; Byrne & Labbé Seek & Blastn (PLOS ONE 2019); Bik Tadpole mill (400+ papers); Scientific Reports 2024 authorship-for-sale network fingerprint; Hindawi/Wiley mass retractions.

**Failure mode:** Generic AI-text classifier or geography/affiliation as a standalone flag (penalizes non-native-English and early-career authors); single-paper image forensics claimed as mill membership; identity checks (buyers are real people).

**Boundary:** Network detection needs a bibliometric corpus, not a single PDF. Prevalence figures are detector-dependent estimates. AI-generation signals decay fast.

**Confidence:** High for text/reagent; medium for network (corpus-dependent).

---

## M6 — Graded-Evidence & Red-Line Discipline (ethical core)

**When to use:** Before emitting *any* finding. This is the gate that keeps the skill from becoming a defamation engine.

**Inputs:** A candidate finding from M1–M5.

**Action:**
1. **Run the benign-explanation checklist; exclude innocent causes before escalating:**
   - Seam in gel/blot → *disclosed lane splicing* (check methods/legend for a marked dividing line).
   - Blocky edges/halos → *JPEG/compression artifacts* (follow the 8×8 grid, appear globally; don't flag).
   - Reused loading-control band → *same-experiment reuse* (acceptable; only cross-*unrelated*-experiment reuse concerns).
   - Same image in two papers → *disclosed self-reuse / methods figure* (check citation/attribution).
   - Overlapping microscopy fields → *tiling/stage-movement overlap* (adjacent-field edge overlap is plausible).
   - Same panel twice → *figure-assembly slip* (dominant honest-error cause; Tier-2 question, never Tier-3).
   - "Too clean" / transcription mismatch → *honest typo, rounding, journal template*.
2. **Assign a tier:**
   - **Tier 1 — Observed anomaly** (default; the only tier the tool may originate): publicly verifiable from the paper, nothing about intent. "Fig 3B and Fig 5A appear to share an identical region (boxed)." Verbs: *appears / shows / is identical to / overlaps*.
   - **Tier 2 — Question for authors** (only after the checklist fails to explain it): the Data Colada formula — (a) disclosed evidence/coordinates, (b) hedged interpretation ("suggests... may have been... we believe"), (c) a named innocent alternative. Phrased as an open question.
   - **Tier 3 — Adjudicated misconduct** (NEVER originated): cite the journal retraction notice / institutional or ORI finding / court ruling. Only here may *misconduct/fabrication* appear, as a quote.
3. **Enforce the banned-word filter** on Tier-1/2 output: fraud, fraudulent, fabricated, faked, falsified, doctored, misconduct, lied, cheated, guilty.
4. **Recommend the COPE order**, do not act it out: clarify with authors → route to editor/institution. Surface the base rate ("most flagged anomalies are honest errors") on every report.

**Output:** The tiered, neutral, hedged finding with innocent causes recorded.

**Evidence:** PubPeer norms; Bik ("intent is beyond image analysis"); Gino v. Data Colada (dismissed Sept 2024 — disclosed-facts+hedge+alternative = protected opinion); Sarkar v. Doe (Michigan COA 2016 — opinion on disclosed facts not defamatory; *form* matters); AACR/Proofig base rate (204/207 honest).

**Failure mode:** "Guilt probability" score; auto-generated public accusation; naming the "most likely manipulating author"; relying on a single detector's manipulation call.

**Boundary:** The skill reaches Tier 2 at most on its own authority. US opinion-doctrine protection is weaker abroad. Protection requires the disclosed fact to be accurate.

**Confidence:** High (legal + community-norm grounded).

---

## M7 — Reproducible Screening Workflow & Annotation

**When to use:** Structuring a full-paper screen and writing findings up.

**Inputs:** The paper + the findings from M1–M6.

**Action:**
1. **Order by cheapest/fastest signal first** (the Agentic Protocol pipeline). A strong early hit raises the prior and tells you where to dig. Swap image↔stats for stats-heavy/clinical papers. Run PubPeer/Retraction-Watch lookup early in parallel.
2. **Per-step stop rules:** DISCARD a candidate if an innocent cause fully explains it; CONTINUE recording even after one solid finding; never convert a tool flag to a stated finding without human confirmation against the original.
3. **Write each finding in the 7-field reproducible annotation format:**
   1. *Locator* — DOI + exact figure/panel/sub-region ("Fig 3A pT231Tau blot, lane 4" or "x≈[120–260], y≈[40–110] px at published resolution").
   2. *Comparison object* — what vs what ("Fig 1B lane 2 vs Fig 5C lane 5").
   3. *Transformation applied* — the operation the reader repeats ("horizontal flip + overlay").
   4. *Result* — attach the overlaid/aligned image; state co-registration.
   5. *Bik category* — I / II / III.
   6. *Innocent-explanation check* — which were ruled out and why.
   7. *Neutral description* — observation, not intent.

**Output:** A finding any stranger with the PDF can reproduce.

**Evidence:** Bik scan order ("don't read text," ~1–15 min/paper); PubPeer FAQ ("perform the transformation yourself and include the result"; compression artifacts rejected); Cassava/Hoau-Yan Wang blots (lane-count vs conditions, splice positions, boxed/floating bands, background reuse); STM Integrity Hub multi-signal pipeline.

**Failure mode:** Pixel-coordinate precision theater (annotate by lane/band/region "at published resolution"); exonerating on clean metadata (elite labs fabricate too — Masliah); accusatory wording (gets PubPeer comments rejected and isn't reproducible).

**Boundary:** A reproducible annotation is the unit of a defensible finding; without the transform+result it's a guess.

**Confidence:** High.

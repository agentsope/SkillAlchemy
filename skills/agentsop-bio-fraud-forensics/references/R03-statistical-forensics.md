Status: pass

# R03 — Statistical Forensics for Detecting Fabricated/Falsified Data

Dimension: statistical_forensics. Scope: reproducible numerical/statistical tests that flag impossible, implausible, or tampered data in biomedical/behavioral papers. Research current as of 2024-2025.

## Key Findings

1. **Consistency tests beat "looks-suspicious" intuition.** The strongest forensic tools are deterministic arithmetic checks (GRIM, GRIMMER, statcheck) that prove a *mathematical impossibility* given the reported numbers. These produce hard TRUE/FALSE verdicts and are fully reproducible from the paper text alone — no raw data needed.

2. **GRIM** (Granularity-Related Inconsistency of Means; Brown & Heathers 2017): for integer-valued data, the mean must equal `integer_sum / N`. Only N distinct fractional parts are reachable. If a reported mean (to d decimals) cannot be produced by any integer sum over N, it is inconsistent. Worked example: `mean = 5.27, N = 43` → 5.27 × 43 = 226.61; no integer sum divided by 43 rounds to 5.27 → **inconsistent (FALSE)**. Power is high when N is small, decimals reported are many (≥2), and the measure is a single integer item.

3. **GRIMMER** (Brown & Heathers, extends GRIM to SDs/variances): given mean, SD, N, decimals, reconstructs the sum and sum-of-squares of integers; checks (a) reconstructed sum-of-squares is a whole number, (b) reconstructed SD matches reported SD under rounding, (c) parity of sum-of-squares matches parity implied by the sum. Worked example: `mean = 7.3, SD = 2.51, N = 12` → **inconsistent (FALSE)**. Catches SDs that are impossible even when the mean passes GRIM.

4. **statcheck** (Nuijten & Epskamp 2016): parses APA-style NHST results (t, F, r, χ², z with df), recomputes the p-value from the test statistic + df, and flags mismatches. An "inconsistency" = reported p ≠ recomputed p; a "gross/decision inconsistency" = significance verdict flips (sig↔non-sig). Prevalence (Nuijten et al. 2016, ~30,000 articles / ~250,000 p-values): ~half of psychology articles contain ≥1 inconsistency; ~1 in 8 (~12.5%) contain a gross inconsistency. Errors bias toward "in favor of the hypothesis."

5. **SPRITE** (Heathers et al. 2018): reconstructs candidate integer datasets consistent with a reported mean, SD, N, and scale bounds. Reveals when (a) NO dataset can produce the stats (impossibility), or (b) every possible dataset requires implausible values (e.g., values outside a bounded scale, or an individual eating ~60 carrots). Diagnostic, not dispositive.

6. **Benford's law / terminal-digit analysis**: For fraud screening of *measured* magnitudes, **second-digit and last-digit (terminal) analyses are more sensitive than first-digit Benford**, because first-digit Benford requires data spanning several orders of magnitude (rare in lab data) and fabricators tend to neglect non-leading digits. Test with Pearson χ² (uniformity for terminal digits; Benford expected freqs for leading digits). Hard limits: does NOT apply to normal/uniform/bounded data, assigned numbers (IDs, doses), or small samples; deviation ≠ fraud.

7. **Data Colada's actual catches** combined *distributional* tests (uniformity, terminal-digit rounding asymmetry, duplicate "twin" detection via Monte Carlo) with *metadata* forensics (Excel `calcChain.xml`, font tags, sort-order violations). The metadata is what converted "statistically anomalous" into "demonstrably tampered." Statistical tests localize suspicion; metadata/raw-file forensics close the case.

8. **Cross-cutting principle for the skill:** consistency tests (GRIM/GRIMMER/statcheck) PROVE impossibility but cannot attribute cause (typo vs fraud). Distributional tests (Benford/terminal-digit/uniformity/duplication) raise probabilistic flags requiring corroboration. Treat every single hit as a *flag*, not a verdict; fraud confidence comes from *patterns across many results/papers* plus raw-data/metadata evidence.

## Detection Cases (>=2 required)

### Case 1: Data Colada "Clusterfake" — duplicated/relocated Excel rows expose fabrication (Gino, [109])
- 情境 (Situation): A behavioral-science Study 1 dataset (signing-honesty paradigm) was posted on OSF as both CSV and .xlsx. Investigators (Simonsohn, Simmons, Nelson) screened it for tampering.
- 约束 (Constraints): No access to original collection instrument; only the public CSV + Excel archive. Needed evidence robust enough to support a misconduct claim and survive litigation.
- 检测步骤 (Detection Steps):
  1. Noticed the file was sorted by condition (0=control, 1=sign-top, 2=sign-bottom) then by participant ID, but the sort was "only almost perfect": 8 observations violated ID ordering; participant ID 49 appeared twice with identical demographics; out-of-sequence IDs straddled adjacent rows in conditions 1 and 2.
  2. Unzipped the .xlsx and read embedded `calcChain.xml`, which records the original formula calculation order. Manually moved cells keep their original calc position, exposing where a row "used to live."
  3. Reconstructed original positions: e.g., row 70 (ID #7) calc-chained between rows 3 and 4 (control IDs #3 and #10) — i.e., #7 had been *moved out of control into condition 2*. Five other flagged rows showed the same manual relocation between conditions.
  4. Confirmed the moved rows were the most extreme observations in their destination condition, all in the hypothesis-favoring direction (t(6)=21.92 for expenses; t(6)=4.48, p=.004 for over-reporting).
- 结果 (Outcome): Conclusion of deliberate observation relocation/duplication to manufacture the effect. Contributed to retraction and Harvard misconduct findings; later corroborated by forensic firm finding 11 observations present in the published study but absent from the RA's original Excel.
- 可提取的操作 (Extractable Operation): For any supplied .xlsx, (a) check whether rows are sorted and flag sort-order violations and duplicate ID/demographic rows; (b) unzip and parse `calcChain.xml` to detect rows whose calculation order is inconsistent with their current physical position (evidence of manual relocation); (c) test whether out-of-place rows are outliers in the hypothesis-favoring direction.

### Case 2: Data Colada — fabricated odometer data in the dishonesty field experiment (Ariely insurance, [98])
- 情境 (Situation): An influential field experiment claimed signing an honesty pledge at the top vs bottom of a form reduced misreported odometer mileage. The supposedly real customer mileage data were examined.
- 约束 (Constraints): Only the analysis Excel file available; mileage are assigned/measured magnitudes (so Benford first-digit not directly used); needed multiple independent signatures of fabrication.
- 检测步骤 (Detection Steps):
  1. **Uniformity test:** Kolmogorov–Smirnov compared the Time-2 miles-driven distribution to Uniform(0, 50,000). Real mileage is right-skewed, but the data were statistically indistinguishable from uniform (p=.84) across all four cars → consistent with `RANDBETWEEN`-style generation, not real driving.
  2. **Terminal-digit rounding asymmetry:** Last-digit frequency analysis showed Time-1 (baseline) values rounded to hundreds/thousands as humans do, while Time-2 values showed *no rounding at all* ("thousands of human beings engaged in no rounding whatsoever") → Time-2 was machine-generated.
  3. **Duplicate-"twin" detection:** Exactly half the rows were in Calibri font, half in Cambria. Each of 22 four-car Calibri customers had a Cambria "twin" whose baseline mileages on all vehicles were within 1,000 miles. A 1,000,000-iteration Monte Carlo produced *zero* matches this close by chance → the Cambria rows are Calibri rows duplicated then perturbed by random additions (0–1,000).
  4. **Rounding absence in duplicates:** Calibri baselines showed rounding; their Cambria twins did not — consistent with adding a small random increment to mask copying.
- 结果 (Outcome): Four independent forensic signatures (uniformity, rounding asymmetry, font-twin duplication, duplicate rounding loss) jointly demonstrated fabrication. Paper retracted.
- 可提取的操作 (Extractable Operation): For a supplied numeric column claimed to be naturally measured: (a) KS-test against the plausible real distribution (often NOT uniform) — flag suspicious uniformity; (b) last-digit frequency χ² to detect missing human rounding vs over-rounding; (c) near-duplicate detection (rows matching within a small tolerance across multiple fields) validated against a Monte Carlo null; (d) if Excel, check font/style runs as a duplication tell.

### Case 3: GRIM/GRIMMER + SPRITE — Wansink "Food & Brand Lab" and the "Carthorse Child"
- 情境 (Situation): Many nutrition/behavior papers report means and SDs of integer counts (carrots eaten, pizza slices, Likert items) on small samples.
- 约束 (Constraints): No raw data; only printed mean/SD/N and known scale bounds. Tests must run from the paper text alone.
- 检测步骤 (Detection Steps):
  1. **GRIM** on each integer-item mean: check `mean × N` is (within rounding) an integer; flag impossible means. Brown & Heathers' original screen of 260 psych articles: 71 testable, 36 with ≥1 impossible mean, 16 with multiple. The same family of checks exposed mis-stated sample sizes across Wansink lab papers.
  2. **GRIMMER** on (mean, SD, N): reconstruct sum and sum-of-squares of integers; flag SDs that are mathematically impossible.
  3. **SPRITE** on the carrot study: mean=19.4, SD=19.9, N=45, lower bound=0. Generated reconstructions all required at least one child eating ~60 carrots (>1 lb) — physically implausible for the described population.
- 结果 (Outcome): Converging impossibilities/implausibilities across many results in the same body of work; multiple retractions/corrections followed (Wansink). SPRITE alone "might come to nothing"; the *pattern* across papers was decisive.
- 可提取的操作 (Extractable Operation): Auto-run GRIM and GRIMMER on every reported (mean, SD, N) for integer/Likert measures; run SPRITE with the known scale bounds; report any impossibility (hard flag) and any reconstruction forcing out-of-range/implausible individual values.

## Evidence Sources (source_id, URL, type, confidence)

- S1, https://datacolada.org/109, blog (primary investigation, "Clusterfake"), high
- S2, https://datacolada.org/98, blog (primary investigation, dishonesty field experiment), high
- S3, https://journals.sagepub.com/doi/abs/10.1177/1948550616673876, peer-reviewed (Brown & Heathers 2017, GRIM, SPPS), high
- S4, https://en.wikipedia.org/wiki/GRIM_test, encyclopedia (GRIM conditions/limits, case summaries), medium
- S5, https://cran.r-project.org/web/packages/scrutiny/vignettes/grim.html, software docs (GRIM worked example), high
- S6, https://cran.r-project.org/web/packages/scrutiny/vignettes/grimmer.html, software docs (GRIMMER worked example, test-3 bug), high
- S7, https://peerj.com/preprints/2400.pdf, preprint (GRIMMER paper, Anaya/Brown/Heathers) — metadata via search; PDF 403 on direct fetch, medium
- S8, https://mbnuijten.com/statcheck/ + https://pmc.ncbi.nlm.nih.gov/articles/PMC7540394/, software/peer-reviewed (statcheck, Nuijten/Epskamp), high
- S9, https://journals.sagepub.com/doi/10.1177/25152459241258945, peer-reviewed (Nuijten & Wicherts 2024, statcheck in peer review reduces inconsistencies) — abstract via search, medium
- S10, https://peerj.com/preprints/26968.pdf + https://medium.com/hackernoon/introducing-sprite-and-the-case-of-the-carthorse-child-58683c2bfeb, preprint/author blog (SPRITE method + Carthorse Child worked case), high
- S11, https://pmc.ncbi.nlm.nih.gov/articles/PMC10088595/, peer-reviewed (Benford's Law for misconduct: second/terminal digits, χ², limits), high
- S12, https://www.researchgate.net/publication/24083679 ("Not the First Digit!", Diekmann), peer-reviewed (Benford in science; favor higher digits), medium
- S13, https://github.com/QuentinAndre/pysprite + https://lukaswallrich.github.io/rsprite2/, software (SPRITE implementations Python/R), high

## Supported Candidate Operations

- OP-GRIM: From reported `mean` (as string, preserve trailing zeros), `N`, decimals, and #scale-items, test integer-mean consistency. Flag FALSE as impossible. Use scrutiny::grim (R) or equivalent. Hard flag.
- OP-GRIMMER: From `mean, SD, N, decimals`, test SD/variance consistency for integer data (3 sub-tests). Flag FALSE. Treat test-3-only flags cautiously (known false-positive bug). Hard flag (tests 1–2).
- OP-STATCHECK: Parse APA NHST (t/F/r/χ²/z + df), recompute p, flag inconsistency and gross/decision inconsistency (significance flip). Run over full text/tables. Report counts; gross inconsistency is the high-value flag.
- OP-SPRITE: From `mean, SD, N, lower/upper bound, decimals`, attempt reconstructions; flag impossibility (no dataset) or implausibility (reconstructions force out-of-range/extreme individual values). Diagnostic flag.
- OP-TERMINAL-DIGIT: χ² test of last-digit (and second-digit) uniformity on measured magnitudes; detect missing human rounding or over-clustering. Flag for corroboration.
- OP-BENFORD-2D: Second/higher-digit Benford χ² on multi-order-of-magnitude measured data only. Flag for corroboration.
- OP-UNIFORMITY: KS / Anderson–Darling vs the plausible real distribution (often skewed) — flag suspicious uniformity (RANDBETWEEN signature).
- OP-DUPLICATION: Near-duplicate row/block detection (match within tolerance across multiple columns), validated against a Monte Carlo null; report zero-by-chance matches. Strong flag.
- OP-ZERO-VARIANCE: Flag SD=0 in groups expected to vary (e.g., control groups), identical repeated values, or "too clean" sequences.
- OP-XLSX-METADATA: If supplementary .xlsx present, unzip and inspect `calcChain.xml` (calc-order vs physical-order mismatch = manual row moves) and font/style runs (duplication tell), plus sort-order/duplicate-ID violations. Strongest single signal when available.
- OP-PCURVE: p-value distribution check across a set of significant results; right-skew = evidential, left-skew/spike just under .05 = p-hacking signature (set-level, not single-study).

## Rejected or Weak Candidate Operations

- First-digit Benford on generic lab data: REJECTED as a standalone test — assumptions (multi-order magnitude span) usually violated in bounded biomedical measures; high false-flag rate. Use second/terminal digits instead.
- Benford/terminal-digit on assigned numbers (participant IDs, treatment dose volumes, catalog numbers): REJECTED — these are designed, not naturally distributed.
- GRIM/GRIMMER on non-integer or composite multi-item means without known item count/scale: WEAK — non-integer responses (e.g., "3.5 slices") and undisclosed item counts cause false positives.
- statcheck on one-tailed tests, p-values with corrections (Bonferroni/FDR), non-APA formatting, or df reported elsewhere: WEAK — known false-inconsistency sources; require manual confirmation before reporting.
- "Distribution looks too clean / suspicious by eye": REJECTED as a standalone claim — must be operationalized (KS/AD test, variance check, digit test) and corroborated.
- Treating any single consistency-test failure as proof of fraud: REJECTED — innocent causes (typos, mis-stated N, rounding, transcription) are common; fraud requires patterns + corroboration.

## Domain-specific Patterns

- **Biomedical relevance:** GRIM/GRIMMER apply to integer/count/Likert endpoints (cell counts, symptom scores, event counts, ordinal scales) on small N — common in clinical/behavioral subgroups. statcheck applies wherever NHST stats are reported with df. SPRITE applies to bounded clinical scales (0–10 pain, 0–N item counts).
- **Bounded-scale impossibility:** For a scale bounded [a,b] with mean μ, the maximum possible SD is bounded (≤ sqrt((b−μ)(μ−a)) for the two-point extreme); a reported SD exceeding this is impossible. Cheap pre-screen before SPRITE.
- **Control-group zero variance:** Biological controls almost always vary; SD=0 or identical replicate values in a control/placebo arm is a high-value flag.
- **Western blot / image-derived quantification:** numbers transcribed from gels/blots can be screened with terminal-digit and duplication tests; pair with image-forensics dimension (out of scope here).
- **Clinical-trial baseline tables:** Benford/terminal-digit and over-uniform baseline distributions have been used to flag suspect trials (Carlisle-type baseline analyses) — adjacent technique worth flagging to the trials dimension.
- **Excel supplements:** behavioral/biomed papers frequently ship .xlsx supplements; calcChain/font/sort-order forensics is broadly applicable, not psychology-specific.

## Boundaries and Uncertainties

- Consistency tests (GRIM/GRIMMER/statcheck) prove *inconsistency*, never *intent*. They cannot distinguish fraud from typo/rounding/mis-reported N.
- Probabilistic tests (Benford/terminal-digit/uniformity/p-curve) give base-rate-dependent flags; false positives rise with large N and with naturally non-Benford data.
- GRIMMER scrutiny test-3 has a documented bug that can flag consistent values as inconsistent — do not rely on test-3-only failures.
- Duplication Monte Carlo nulls depend on correctly modeling the legitimate generating process; mis-specified nulls under/over-state "impossibility."
- Metadata forensics (calcChain, fonts) require the original file format; PDFs/CSVs strip this. Absence of metadata is not exculpatory.
- Exact Nuijten 2016 corpus size (~30,000 articles / ~250,000 p-values) is widely cited but the overview page did not restate it; the prevalence rates (~50% any, ~12.5% gross) are confirmed. GRIMMER preprint PDF (S7) returned 403; methodology corroborated via scrutiny docs (S6) and search metadata.

## Recommendations for Later Skill Compilation

1. Implement a deterministic **Tier-1 consistency battery** that runs with zero raw data: extract every (mean, SD, N, #items, decimals) and every APA NHST result from the paper, then auto-run GRIM, GRIMMER, statcheck, and the bounded-scale max-SD check. These give hard, citable impossibility flags and are the highest-precision outputs.
2. Add a **Tier-2 distributional battery** when a numeric column or supplementary dataset is available: terminal/second-digit χ², KS-uniformity vs a domain-appropriate reference, near-duplicate detection with Monte Carlo null, zero-variance/identical-block detection, and SPRITE for bounded integer measures.
3. Add a **Tier-3 metadata forensics** step for any .xlsx/.docx supplement: unzip, parse `calcChain.xml` for calc-vs-physical order mismatches, scan font/style runs, and check sort-order/duplicate-ID violations.
4. **Severity rubric:** Hard flag = mathematical impossibility (GRIM/GRIMMER tests 1–2, statcheck gross inconsistency, SPRITE no-solution, calcChain relocation). Soft flag = probabilistic anomaly (digit tests, uniformity, p-curve). Require ≥1 hard flag OR a corroborated pattern of soft flags across multiple results/papers before escalating to "likely fabrication."
5. Always emit, per flag: the input numbers used, the test, the verdict, and an explicit "what this cannot prove" line, so downstream reviewers do not over-read a single inconsistency as fraud.
6. Use existing tooling rather than reimplementing: R `scrutiny` (GRIM/GRIMMER/SPRITE rebuild + audit), R `statcheck` / statcheck.io, R `rsprite2`, Python `pysprite`, R `benford.analysis`. Wrap, don't rebuild.
7. Cross-reference companion dimensions: image-forensics (blot duplication), clinical-trials baseline analysis (Carlisle), and text/metadata forensics; statistical hits gain confidence when they co-occur with those.

Status: pass

## Key Findings

- Image duplication/manipulation is the #1 reproducible fraud signal in life-science papers. Bik, Casadevall & Fang (mBio 2016) screened 20,621 papers and found **3.8% (782 papers)** contained inappropriate image duplication — and ~half showed features suggesting deliberate manipulation rather than honest error. This is the empirical anchor of the whole field.
- Bik's three-category taxonomy is the canonical screening rubric and maps directly to escalating intent:
  - **Category I — Simple Duplication** (29.4% of flagged): identical panel reused to represent different conditions. Often honest error (e.g., wrong file pasted) but still a record problem.
  - **Category II — Duplication with Repositioning** (45.5%, the most common): overlapping image that has been shifted, rotated, or flipped/mirrored relative to its twin. Less likely to be honest error.
  - **Category III — Duplication with Alteration** (25.1%): partial duplication of bands/lanes/cell clusters *within or between* panels, often with rotation/reversal, stamping, patching, or FACS-gate manipulation. Most likely deliberate.
- The core human technique is **comparative visual inspection** built on a single premise: every Western blot band, gel lane, microscopy field, and FACS cloud should be *unique like a fingerprint*. Bands resembling each other more than chance allows (same "pancake/dumbbell/bowtie" shape, same background spots/scratches/airbubbles) signal duplication.
- Manual reveal techniques amplify what the eye misses: contrast/brightness stretching and **histogram equalization** expose splice seams and erased bands; **emboss/edge filters** make splice lines pop as 3D ridges; **overlay + flip/rotate** comparison confirms repositioned duplicates; **clone detection, ELA, and noise analysis** (Forensically) localize copy-paste and airbrushing.
- Automated tools are now in production at major publishers: **ImageTwin** (ASM since 2023, ~120M-figure database) and **Proofig** (Science since early 2025; also cited by Nature). Both are *triage* tools — every hit requires human verification because false positives are real and frequent.
- The 2024-2025 frontier is **generative-AI figures**. The Frontiers "rat with giant genitals" Midjourney case (Feb 2024) was the wake-up call; both ImageTwin and Proofig shipped dedicated AI-generated-image detectors in 2024-2025 that work in the **frequency domain** (GANs/diffusion leave spectral fingerprints invisible to the eye). Proofig reports ~98% detection / 0.02% false-positive for AI microscopy; these numbers are vendor-stated and not independently verified.

## Detection Cases (>=2 required)

### Case 1: Flipped β-actin loading control reused across timepoints (Category II, Western blot)
- 情境 (Situation): A Western blot figure presents β-actin loading controls for a cytosol sample at multiple timepoints (e.g., 120 min vs 360 min) as if each were an independent experiment. Loading controls are the highest-yield place to look because labs are tempted to reuse the "same actin" rather than re-run it.
- 约束 (Constraints): The two band sets are not pixel-identical at a glance — one has been horizontally flipped, defeating naive eyeballing and any duplicate-finder that only checks for exact copies. Published JPEG is low resolution; no raw files available.
- 检测步骤 (Detection Steps):
  1. Treat each band as a unique fingerprint; scan the panel for any two bands sharing identical silhouette + identical surrounding background speckle.
  2. Crop the two candidate band regions.
  3. Apply the flip/rotate transform set: mirror one crop horizontally, then overlay on the other (Photoshop "Difference" blend or simple alpha overlay). A near-flat/black difference image = same source.
  4. Confirm the giveaway is the *background noise around the band* matching, not just band shape (shape alone can coincide; correlated background dust/scratches cannot).
  5. Classify as Category II (repositioning by horizontal flip).
- 结果 (Outcome): β-actin bands for 120 min were identical-but-horizontally-flipped to those at 360 min — impossible for genuinely independent runs. Reported on PubPeer as duplication with repositioning.
- 可提取的操作 (Extractable Operation): For any loading-control or repeated-control panel, run the **flip/rotate-then-overlay-Difference** check; correlated *background* texture (not band shape) is the decisive evidence.

### Case 2: AI-generated (Midjourney) anatomical figures in a published review (generative-AI fraud)
- 情境 (Situation): Guo et al., "Cellular functions of spermatogonial stem cells in relation to JAK/STAT signaling pathway," *Frontiers in Cell and Developmental Biology* (Feb 2024, DOI 10.3389/fcell.2023.1339390). Figures were declared as Midjourney-generated but passed peer review and were published.
- 约束 (Constraints): No forensic software needed — but the deeper constraint is that *more realistic* AI figures will not be this obvious. Two reviewers and an editor missed it under accelerated review. Generative figures have no "original" to duplicate-match against, so duplication detectors are blind to them.
- 检测步骤 (Detection Steps):
  1. Read the text inside the figure. AI giveaway #1 is gibberish labels: "testtomcels," "senctolic," "diʒlocttal stem ells," "signal bıidimg the recetein," "proprounization." Real figures never contain non-words.
  2. Check anatomical/biological plausibility: a rat drawn with four enormous testicles and an impossible penis; a "pathway diagram" with invented arrows and terms; a panel that looks like "pizzas with pink salami and blue tomatoes."
  3. Cross-check the disclosure statement (here authors admitted Midjourney use).
  4. For non-obvious cases, escalate to **frequency-domain AI-detection** (FFT/spectral analysis or a trained detector like Proofig/ImageTwin AI module) which catches GAN/diffusion spectral fingerprints invisible to the eye.
- 结果 (Outcome): Mocked widely on X/Twitter within hours; Frontiers retracted the paper. Became the canonical example that peer review does not catch generative fraud and that publishers needed automated AI-image screening.
- 可提取的操作 (Extractable Operation): A two-tier AI-figure check — (a) human "read-the-labels + anatomy-sanity" pass that catches crude generations instantly, then (b) frequency-domain/spectral or trained-detector pass for realistic generations. Always inspect figure text for non-words.

### Case 3 (supporting): ASM/ImageTwin production pilot — automated flag then 3-stage human verification
- 情境 (Situation): ASM Journals integrated ImageTwin and ran a 12-month pilot (Mar 2023-Mar 2024) on 2,627 accepted manuscripts to quantify how automated screening + human review performs at scale.
- 约束 (Constraints): ImageTwin only processes *halftone* images (Western blots, microscopy, photographs) — it cannot read line art, sketches, plots, or graphs, leaving coverage gaps. It flags pixel-level similarity, which produces benign hits (legitimately reused placeholders/controls).
- 检测步骤 (Detection Steps):
  1. ImageTwin auto-flags pixel-level similarities within the manuscript and against its ~120M-figure published database.
  2. Stage 2: a human image specialist visually inspects every flag.
  3. Stage 3: confirm with Photoshop "Difference" function (overlay subtraction) before any concern is raised with authors.
- 结果 (Outcome): 410/2,627 manuscripts (15.6%) flagged; only 248 (60% of flags, 3.9% of total) were genuine duplications — most of those unintentional (reused controls/placeholders), ~5.3% reused from prior publications. The ~40% of flags that were *not* genuine duplications is the empirical false-positive load.
- 可提取的操作 (Extractable Operation): Never report a tool hit as fraud. Mandatory pipeline = **automated flag → human visual inspection → Difference-overlay confirmation**; expect ~40% of raw flags to be discarded.

## Evidence Sources (source_id, URL, type, confidence)

- S1 | https://journals.asm.org/doi/full/10.1128/mbio.00809-16 (and PMC mirror PMC4941872) | Bik, Casadevall, Fang 2016 mBio — foundational duplication-prevalence paper, Category I/II/III definitions | High
- S2 | https://scienceintegritydigest.com/2020/02/21/western-blots/ | Bik blog — "every band is unique" visual-inspection method | High
- S3 | https://scienceintegritydigest.com/2019/11/23/scanning-for-duplications/ | Bik blog — Category I/II/III restated with intent ladder, flipped/shifted/rotated examples | High
- S4 | https://scienceintegritydigest.com/2024/02/15/the-rat-with-the-big-balls-and-enormous-penis-how-frontiers-published-a-paper-with-botched-ai-generated-images/ | Bik blog — Midjourney/Frontiers AI-figure case | High
- S5 | https://intercom.help/proofig/en/articles/9414427-analyzing-suspected-issues-in-western-blot-images-with-proofig-best-practices-and-tips | Proofig docs — emboss filter, histogram equalization for blots | High
- S6 | https://intercom.help/proofig/en/articles/10544884-histogram-equalization-in-image-forensics | Proofig docs — histogram equalization caveat ("visualization tool, not proof") | High
- S7 | https://29a.ch/photo-forensics/ + https://29a.ch/2015/08/21/noise-analysis-for-image-forensics | Forensically (Jonas Wagner) — ELA, clone detection, noise analysis, level sweep, magnifier | High
- S8 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12505991/ (mBio 2025, DOI 10.1128/mbio.01990-25) | ASM/ImageTwin pilot — scale results, 3-stage verification, halftone-only limitation | High
- S9 | https://www.science.org/doi/10.1126/science.adn7530 | Science 2024 editorial "Genuine images in 2024" — Proofig adoption (403 on fetch; corroborated via search) | Medium
- S10 | https://tnqtech.com/imagetwin-launches-ai-generated-image-detection-capability/ | ImageTwin AI-generated-image detection launch (frequency-domain) | Medium
- S11 | https://www.proofig.com/newsroom/ (Nature AI image-integrity feature) | Proofig AI detection ~98%/0.02% FP — vendor-stated | Low-Medium (vendor claim)
- S12 | https://arxiv.org/html/2408.13786v1 | "Localization of Synthetic Manipulations in Western Blot Images" — patch-based synthetic-vs-real heatmap | Medium
- S13 | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11323046/ | ELA-CNN integration framework for authenticity verification | Medium
- S14 | https://retractionwatch.com/2026/04/19/elisabeth-bik-scientific-sleuth-image-duplication-mbio-biorxiv-preprint/ | Retraction Watch 10-yr retrospective on Bik preprint | Medium

## Supported Candidate Operations

1. **Band/field uniqueness scan** — treat every blot band, gel lane, microscopy field, and FACS cloud as a fingerprint; flag any pair more similar than chance (matching silhouette AND matching background speckle/scratches). [S2, S3]
2. **Flip/rotate-then-overlay-Difference** — for any suspected repositioned duplicate, mirror/rotate one crop and subtract (Photoshop "Difference" or alpha overlay); a flat/black result = same source. [S1, S8]
3. **Contrast/brightness stretch + histogram equalization** — push pixel intensities to full range to expose erased bands and splice seams. [S5, S6]
4. **Emboss / edge filter** — render edges as 3D ridges to make splice lines and patched rectangles visible. [S5]
5. **Clone detection (Forensically)** — auto-locate copy-pasted regions within a single panel (Category III). [S7]
6. **Noise analysis (Forensically)** — reverse a median filter to show only noise; warping/airbrushing/transformed clones leave a tell-tale black halo / disrupted noise field. [S7]
7. **Error Level Analysis (ELA)** — recompress and highlight regions with anomalous compression error; pasted/edited regions differ from surroundings. [S7, S13]
8. **AI-figure two-tier check** — (a) read figure text for non-words + anatomy/biology sanity; (b) frequency-domain/spectral or trained detector for realistic generations. [S4, S10]
9. **Mandatory tool→human→Difference verification pipeline** — never escalate a raw automated flag without human inspection and Difference-overlay confirmation. [S8]
10. **Loading-control-first targeting** — start screening at β-actin/GAPDH/tubulin and FACS controls; these are the highest-base-rate sites of reuse. [S1, S3]

## Rejected or Weak Candidate Operations

- **ELA as standalone proof** — heavily JPEG-recompressed publisher figures and uniform backgrounds make ELA noisy and ambiguous on scientific images; useful as a pointer, never as a verdict. [S7, S13]
- **Exact-pixel duplicate matching alone** — misses Category II (flipped/rotated/shifted) and Category III (partial) duplications, which are the majority. Must be paired with transform-invariant comparison. [S1]
- **Histogram equalization as proof of fraud** — Proofig explicitly states it is a *visualization* aid, not evidence; equalization artifacts can mimic manipulation. [S6]
- **Vendor accuracy numbers as ground truth** — Proofig's 98%/0.02%-FP AI-detection figures are self-reported and not independently benchmarked; treat as marketing. [S11]
- **Trusting peer review / disclosure** — the Frontiers case shows reviewers and editors pass obvious AI fraud; author disclosure of AI tools is not a safeguard. [S4]
- **Metadata / EXIF reliance** — publisher pipelines strip metadata; absence of edit history proves nothing for figures.

## Domain-specific Patterns

- **Western blots / gels**: splice lines (sharp vertical edges, abrupt background-intensity change between lanes), erased bands (suspiciously clean rectangles), duplicated/flipped bands, "too perfect" beautified bands lacking natural background noise. Loading controls (β-actin, GAPDH, tubulin) are the #1 reuse site.
- **Microscopy / histology**: duplicated cell clusters within/between fields (Category III), overlapping fields presented as different conditions (Category II), cloned regions to hide artifacts.
- **Flow cytometry / FACS**: identical scatter-plot regions or gates relabeled with different percentages (a Category III signature called out in Bik 2016).
- **Intent ladder**: Category I → possible honest error; Category II/III → repositioning/alteration is hard to do by accident, raising probability of intent. This ladder should drive how strongly a screener phrases a concern.
- **AI-generated figures**: gibberish text/labels, anatomically impossible structures, invented pathway terms, surreal color/texture; realistic ones detectable only via frequency-domain spectral fingerprints.

## Boundaries and Uncertainties (esp. tool false positives)

- **Tool false positives are large and structural.** ASM pilot: ~40% of ImageTwin flags were NOT genuine duplications (410 flagged, 248 real). Legitimately reused placeholders and shared controls trip the matcher. Mandatory human verification. [S8]
- **Coverage gaps.** ImageTwin processes only halftone images (blots, microscopy, photos) — it ignores line art, plots, schematics, graphs, where data fabrication can also hide. [S8]
- **Database dependence for cross-paper duplication.** ImageTwin (~120M figures) and Proofig can only flag reuse from *indexed* sources; reuse from unindexed/non-English/paywalled or pre-publication figures is invisible.
- **Proofig vs ImageTwin trade-off.** Proofig is reported to give fewer false positives on Western blots and is more accurate there, but is slower and historically had a smaller cross-source database than ImageTwin. Different publishers chose differently (ASM→ImageTwin, Science→Proofig). [search corroboration; S8, S9]
- **AI-detection is an arms race.** Adversarial perturbations in the frequency domain can defeat AI-image detectors; vendor accuracy figures are unverified and likely degrade on out-of-distribution / post-processed images. [S10, S11, arXiv 2407.20836]
- **Human inspection is subjective.** Bik uses three independent reviewers reaching consensus; a lone screener risks both false positives (coincidental band shape) and misses. Background-texture correlation, not shape, is the more reliable discriminator.
- **Resolution ceiling.** Published low-res JPEGs lose the high-frequency detail many techniques (ELA, noise analysis) rely on; raw/TIFF source is far stronger evidence when obtainable.
- **An overlay match proves common source, not intent.** A duplication finding establishes that two regions share a source; whether it is fraud vs honest file-handling error is a separate, evidence-weighted judgment.

## Recommendations for Later Skill Compilation

1. **Encode Bik's I/II/III taxonomy as the core classifier** with the intent ladder (I = possible error → II/III = likely deliberate), and make the screener output the category explicitly.
2. **Make "every band/field is a fingerprint" the guiding heuristic**, and instruct that *correlated background texture* (speckle, scratches, dust) — not band/cell shape alone — is the decisive evidence of duplication.
3. **Codify the per-figure step list** (see below) as a deterministic checklist, panel by panel.
4. **Hard-wire the verification pipeline**: any automated or eyeball flag → human inspection → flip/rotate-overlay-Difference confirmation before escalation. Build in the expectation that ~40% of raw hits are false positives.
5. **Add a dedicated AI-figure module**: tier-1 read-the-labels + anatomy-sanity; tier-2 frequency-domain/trained detector. Flag any non-word text in figures.
6. **Ethics/calibration layer**: outputs must say "possible duplication / common source," never "fraud"; distinguish honest-error patterns (reused control, wrong-file paste = Category I) from deliberate patterns; require multiple independent looks for high-stakes claims.
7. **Document tool boundaries** so the skill never over-trusts software: halftone-only coverage, database limits, vendor-claimed accuracy, AI-detection arms race.

### Step-by-step procedure a screener runs on ONE figure panel
1. **Inventory** every panel and sub-panel; note which are halftone (blot/micrograph/FACS) vs line art.
2. **Catalog uniqueness**: for each blot band / cell field / FACS cloud, note shape + surrounding background texture. List any pair that looks more alike than chance.
3. **Contrast/brightness stretch + histogram equalization** on each halftone panel → look for splice seams, abrupt background steps between lanes, suspiciously clean rectangles (erased bands), "too perfect" beautified bands.
4. **Emboss/edge filter** → splice lines and patched rectangles appear as ridges.
5. For each suspect pair, **crop and overlay**; apply flip + rotate transforms; use Difference blend. Flat/black = same source (record as Cat I if as-is, Cat II if repositioned).
6. **Clone detection + noise analysis (Forensically)** on single panels → localize copy-paste within a panel (Cat III) and airbrush/warp halos.
7. **ELA** as a secondary pointer to recompressed/pasted regions (never as sole proof).
8. **AI-figure check**: read all figure text for non-words; sanity-check anatomy/biology; if realistic and still suspect, run frequency-domain/trained AI detector.
9. **Optional automated pass** (ImageTwin/Proofig) for within-paper and cross-database duplication; then human-verify every hit.
10. **Classify and phrase**: assign Bik category, state "possible common source / duplication," note whether pattern fits honest error vs deliberate, and record exact pixel coordinates + transform that produced the match for reproducibility.

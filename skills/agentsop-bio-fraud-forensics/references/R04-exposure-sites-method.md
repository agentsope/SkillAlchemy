Status: pass

# R04 — Exposure Sites as Method Source

Dimension: `exposure_sites_as_method_source` (highest priority). Reframe enacted: exposure platforms (PubPeer, For Better Science, Data Colada, Science Integrity Digest) are treated as a corpus of WORKED DETECTION EXAMPLES — every thread/post is reverse-engineered into a reusable forensic MOVE — while database platforms (Retraction Watch DB, ORI, PubMed, scite, Crossref/Crossmark) are treated as STATUS-VERIFICATION endpoints. Research current as of May 2026.

## Key Findings

1. **Exposure sites encode method, not just verdicts.** Each PubPeer comment / blog post is a replayable recipe: which panels were compared, what transform (flip/rotate/shift/contrast-stretch) was applied to make a match visible, and what the recomputed statistic was. The skill should mine the *step*, not the *conclusion*.

2. **Two distinct forensic traditions exist and require different platforms:**
   - **Image-forensics tradition** (Bik, Smut Clyde, Cheshire, Tiger BB8 — surfaced on PubPeer + For Better Science): catch by eye, confirm with overlay/transform; targets Western blots, micrographs, FACS plots, paper-mill template motifs.
   - **Statistical/data-forensics tradition** (Data Colada, Nick Brown — surfaced on Data Colada + journals): catch by recomputation/consistency tests (calcChain, GRIM/GRIMMER, distributional tests); targets means, SDs, raw datasets, spreadsheet metadata.

3. **The canonical image taxonomy is Bik's three categories** (Type I simple re-use; Type II repositioned = rotate/flip/shift; Type III partial overlap/cloned features within one image). This is the single most reusable classification the skill should adopt for routing image flags. (scienceintegritydigest.com)

4. **Detection is human-led, tool-assisted.** Even the most prolific sleuths state plainly they work "by eye," then confirm with software (ImageTwin, Proofig) or simple Preview brightness/contrast adjustment to expose hidden seams and clones. The skill's image step should mirror this: visual triage first, transform-confirm second, automated tool third.

5. **Status verification is now centralized.** Crossref acquired the Retraction Watch Database (Sept 2023); it is free, daily-updated, queryable by Author/Journal/RetractionDOI/Publisher/Country, and exposed via Crossref Labs API. scite layers retraction/editorial-notice flags onto citations. This collapses several lookups into a few authoritative endpoints.

6. **Paper-mill detection is a cluster move, not a single-paper move.** Sleuths catch mills by recognizing a templated motif (a stylized Western blot, a recycled/hand-drawn FACS scatter) repeated across *unrelated* author groups, then building a spreadsheet that clusters papers to one production line. A single paper rarely triggers it; the repetition does.

## Detection Cases (>=2 required)

### Case 1: Data Colada [109] "Clusterfake" — calcChain.xml reveals manually moved rows in a dishonesty study
- 情境 (Situation): A field-experiment dataset (the "signing-at-the-top" honesty study) was posted on OSF. Data Colada suspected fabrication and obtained the original Excel files. Source: https://datacolada.org/109 ; companion https://datacolada.org/98
- 约束 (Constraints): Only the public posted .xlsx and OSF files were available — no access to raw lab logs, no author cooperation, no privileged audit. Authors later disputed the calcChain interpretation (sorting can also reorder it), so the move is suggestive, not standalone-conclusive.
- 检测步骤 (Detection Steps):
  1. Opened the dataset and noticed rows were sorted by two columns (`Cond`, then `P#`) but the sort was "only *almost* perfect" — a few rows were out-of-sequence or duplicated.
  2. Exploited that `.xlsx` files are ZIP archives: renamed `.xlsx` -> `.zip` and unbundled the internal files.
  3. Extracted `calcChain.xml` — Excel's record of the order in which formula cells are calculated. Key fact: when a user manually drags/moves a row, the visible position changes but calcChain retains the row's ORIGINAL position.
  4. Cross-referenced each out-of-sequence participant ID against its calcChain position. Example: a row currently sitting in Condition 2 (ID #7) had a calcChain slot wedged between Condition 0 rows (IDs #3 and #10) — proving it was physically moved from control into treatment.
  5. Validated direction: the moved rows produced "huge effects in the predicted direction" / extreme t-stats, consistent with deliberate movement toward the hypothesis rather than random data-entry noise. (Corroborating tells: baseline value for one car in two different fonts; simulated mileage matching a uniform RANDBETWEEN distribution rather than real data.)
- 结果 (Outcome): Paper retracted; triggered the Gino litigation. Established calcChain as a now-standard spreadsheet-forensics artifact.
- 可提取的操作 (Extractable Operation): **OP-CALCCHAIN** — When raw data is supplied as `.xlsx`: copy, rename to `.zip`, unzip, open `xl/calcChain.xml`; compare formula-calculation order to the visible row order. Out-of-order entries that map a row to a different condition's neighborhood = evidence of manual row relocation. Always note the sorting caveat.

### Case 2: PubPeer (commenter "Actinopolyspora biskrensis") — duplicated/flipped blot bands and gel-slice overlap in a 2010 Cancer paper
- 情境 (Situation): A 2010 oncology paper ("Adenovirus-mediated expression of truncated E2F-1 suppresses tumor growth...", *Cancer*) was flagged on PubPeer. The same pseudonymous sleuth flagged related papers by the same group (a *Virology* paper, a 2018 *Cancers* paper). Source: https://retractionwatch.com/2024/07/19/mistakes-were-made-paper-by-department-chair-earns-expression-of-concern-as-more-questioned/
- 约束 (Constraints): Post-publication, only the published figures (often low-resolution PDF panels) available; original blots could not be located by the journal; identification rests on the figure as-printed.
- 检测步骤 (Detection Steps):
  1. Examined figure panels directly (Bik-style: look at images, ignore text), comparing actin/loading-control bands and gel slices within and across Figures 2b/2c.
  2. Identified a band re-used across panels after a horizontal flip and a change in aspect ratio — i.e., the same band serving two different sample conditions (Bik Type II: repositioned-with-transform).
  3. For the related Virology paper (Fig 3C overlap), after the author supplied "originals," a second commenter built an alignment ANIMATION (blink/overlay between the two images) that showed the overlap persisted in the supplied originals — defeating the rebuttal.
  4. For the 2018 Cancers paper, flagged a duplicated crystal-violet assay image (same field used twice).
- 结果 (Outcome): *Cancer* issued an Expression of Concern (originals unfindable, authors said "mistakes were made"); *Cancers* issued a correction after authors regenerated data; Virology papers placed under Elsevier investigation.
- 可提取的操作 (Extractable Operation): **OP-OVERLAY-BLINK** — For any suspected duplicate panel: extract both panels at max resolution, normalize scale/orientation, apply candidate transforms (horizontal/vertical flip, rotation, aspect rescale), then overlay or blink-animate. Persistence of identical features through the transform = duplication; this also pre-empts the "here are the originals" rebuttal because the animation tests the supplied originals too.

### Case 3 (supporting — paper-mill cluster): Smut Clyde + Tiger BB8 — template-motif clustering of a Chinese paper mill
- 情境 (Situation): ~260+ fabricated papers (many in *J BUON*) traced to one Chinese paper mill. Source: https://forbetterscience.com/2021/05/26/the-chinese-paper-mill-industry-interview-with-smut-clyde-and-tiger-bb8/
- 约束 (Constraints): Individual papers look superficially plausible; only the repetition across unrelated author groups exposes the mill. Heavy reliance on manual eyeballing ("they do it by eye").
- 检测步骤 (Detection Steps):
  1. Recognized a recurring stylized Western-blot motif and FACS scatterplots that were recycled or visibly hand-drawn — a production template.
  2. Cross-matched the SAME motif across papers from author groups unlikely to collaborate (e.g., scattered regional hospitals with little research capacity).
  3. Layered in linguistic tells: identical phrasing, identical figure arrangement, identical consistent grammatical errors.
  4. Built a tracking spreadsheet clustering all papers sharing the template -> attributed to one mill.
- 结果 (Outcome): Mass flagging on PubPeer, For Better Science exposé, many subsequent retractions.
- 可提取的操作 (Extractable Operation): **OP-MILL-MOTIF** — Treat repetition-across-unrelated-papers as the signal. For a suspect figure, search PubPeer/Google Images for the motif; check for implausible co-author/affiliation clusters and templated language. A single match is weak; a cross-author cluster is strong.

## Exposure-vs-Database Site Function Map

| Site | Type | What it reveals (method or status) | How to use |
|---|---|---|---|
| PubPeer (pubpeer.com) | Exposure / METHOD | Crowd comments per paper; exact catch steps (panels compared, transform applied, recomputed stat); author rebuttals | Search by DOI / author / title; read each comment as a recipe; install browser extension to see flags inline while reading |
| For Better Science (forbetterscience.com, Leonid Schneider) | Exposure / METHOD + NARRATIVE | Long-form case construction: how a single flag expands into a lab- or mill-wide pattern; aggregates sleuth findings | Read for the *investigation arc* (single image -> cross-paper -> author cluster -> institutional response); mine for motif-clustering technique |
| Data Colada (datacolada.org) | Exposure / METHOD (statistical) | Spreadsheet/data forensics: calcChain, distributional tests, duplicate/out-of-sequence rows, simulated-data signatures | Read numbered posts (e.g., [98],[109],[114]) as step-by-step replicable data-forensics protocols |
| Science Integrity Digest (scienceintegritydigest.com, Elisabeth Bik) | Exposure / METHOD (image) | Public image-screening methodology; the Type I/II/III taxonomy; "look at photos, ~1 min/paper" workflow | Adopt her three-category taxonomy as the routing schema for image flags; use her brightness/contrast-in-Preview trick |
| Named sleuths (Bik, Smut Clyde, Cheshire, Tiger BB8, Nick Brown) | Exposure / METHOD | Personal specialties (see Domain Patterns) | Match the flag type to the sleuth's documented technique |
| Retraction Watch Database (Crossref-hosted) | Database / STATUS | Whether a paper/author is retracted; reason codes; retraction DOI; since-1970s; daily updated | Query Author/Journal/RetractionDOI/Publisher/Country in UI; bulk via Crossref Labs API / CSV |
| Retraction Watch (blog, retractionwatch.com) | Hybrid / CONTEXT | Narrative on specific cases, EoCs, institutional actions | Search for the paper/author to get context behind a status flag |
| ORI Case Summaries (ori.hhs.gov/content/case_summary) | Database / STATUS | US PHS-funded ADJUDICATED misconduct findings + administrative actions (only currently-active actions listed) | Search by researcher name; cross-check Federal Register / NIH Guide for full findings text |
| PubMed (pubmed.ncbi.nlm.nih.gov) | Database / STATUS | Retraction notices, Expressions of Concern, corrections linked to the record; publication-type "Retracted Publication" | Look at the colored banner on the record; filter by publication type "Retraction of Publication" |
| scite.ai | Database / STATUS + signal | Retraction/editorial-notice flags on a paper; supporting vs contrasting citation counts; Reference Check on uploaded PDF | Run a DOI or upload manuscript to flag cited-but-retracted refs and high-contrasting-citation papers |
| Crossref / Crossmark | Database / STATUS | Authoritative publisher-asserted update status (retraction, correction, EoC) via Crossmark button/API; hosts RW data | Hit Crossref REST API by DOI; check `update-to` / Crossmark for the canonical notice |

## Red-flag -> Verification-platform Routing Table

| Red flag (input) | Primary platform | How to query | Confirm/contextualize with |
|---|---|---|---|
| Suspected image duplication (blot/micrograph/FACS) | PubPeer | Search DOI/author; read comments for prior overlay analysis | Replicate OP-OVERLAY-BLINK; classify by Bik Type I/II/III (Science Integrity Digest) |
| Same panel re-used across DIFFERENT papers / template motif | For Better Science + PubPeer | Search motif/author; look for cross-author clusters | OP-MILL-MOTIF; check co-author/affiliation plausibility |
| Suspected statistical fabrication in means/SDs | Apply GRIM/GRIMMER directly | Recompute mean granularity vs N (Nick Brown) | Data Colada posts for analogous distributional tests |
| Raw data supplied as Excel, suspect manipulation | Data Colada method | OP-CALCCHAIN: unzip .xlsx, inspect calcChain.xml | Note sorting caveat; check fonts, RANDBETWEEN-like distributions |
| Suspect the paper is already retracted | Retraction Watch Database | Search Author/Journal/RetractionDOI | Cross-check PubMed banner + Crossref/Crossmark notice |
| Suspect a correction/Expression of Concern (not full retraction) | PubMed + Crossref/Crossmark | Check record banner / Crossmark `update-to` | Retraction Watch blog for narrative |
| Suspect ADJUDICATED research misconduct (US, PHS-funded) | ORI Case Summaries | Search researcher name | Federal Register / NIH Guide for full finding text |
| Citing/relying on a possibly-retracted reference | scite.ai | DOI lookup or Reference Check on PDF | Crossref for canonical status |
| Author has a pattern of problems | Retraction Watch DB (author field) + PubPeer (author search) | Author query in both | For Better Science for lab-level narrative |

## Evidence Sources (source_id, URL, type, confidence)

- S1, https://datacolada.org/109, exposure-method (Clusterfake calcChain protocol), high
- S2, https://datacolada.org/98, exposure-method (companion fraud-evidence post), high
- S3, https://retractionwatch.com/2024/07/19/mistakes-were-made-paper-by-department-chair-earns-expression-of-concern-as-more-questioned/, exposure-method + status (Actinopolyspora biskrensis PubPeer case, EoC), high
- S4, https://scienceintegritydigest.com/2019/11/23/scanning-for-duplications/, exposure-method (Bik Type I/II/III + workflow), high
- S5, https://forbetterscience.com/2021/05/26/the-chinese-paper-mill-industry-interview-with-smut-clyde-and-tiger-bb8/, exposure-method (paper-mill motif clustering; sleuth specialties), high
- S6, https://retractionwatch.com/retraction-watch-database-user-guide/, database (RW DB search fields/usage), high
- S7, https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/, database (RW fields, Crossref hosting/API), high
- S8, https://ori.hhs.gov/content/case_summary, database (ORI adjudicated findings index), high
- S9, https://scite.ai/blog/2022-10-19_automated-notice-detection, database (scite retraction/notice detection), medium-high
- S10, https://en.wikipedia.org/wiki/GRIM_test, method (GRIM, Brown & Heathers 2016), medium-high
- S11, https://peerj.com/preprints/2400.pdf, method (GRIMMER, variability test), medium
- S12, https://retractionwatch.com/2026/04/19/elisabeth-bik-scientific-sleuth-image-duplication-mbio-biorxiv-preprint/, context (Bik 20,621-paper screen, 3.8% rate), high

## Supported Candidate Operations

- **OP-OVERLAY-BLINK**: Extract suspect panels at max res; normalize; apply flip/rotate/aspect transforms; overlay or blink-animate to confirm cloned features. Also re-run on author-supplied "originals" to defeat rebuttals. (S3, S4)
- **OP-BIK-TRIAGE**: Classify every image flag into Type I (simple dup), Type II (repositioned w/ transform), Type III (intra-image cloned features). Type II/III are hard to explain as honest error -> escalate. ~1 min/paper visual triage, Preview brightness/contrast to expose seams. (S4)
- **OP-CALCCHAIN**: For .xlsx raw data: rename to .zip, unzip, read `xl/calcChain.xml`; map formula-order to visible row order; out-of-place entries = manual relocation. Record sorting caveat. (S1, S2)
- **OP-GRIM/GRIMMER**: Given reported mean (and SD) + integer N, test whether the value is mathematically attainable; impossible value = entry error or fabrication. Strongest with small N and multi-decimal reporting. (S10, S11)
- **OP-MILL-MOTIF**: Treat motif-repetition across unrelated author groups as the signal; check templated language and implausible affiliation/co-author clusters; build a cluster spreadsheet. (S5)
- **OP-STATUS-CASCADE**: For status, query in order — Retraction Watch DB (Author/DOI) -> PubMed banner -> Crossref/Crossmark notice -> ORI (if adjudicated misconduct suspected) -> scite (citation-level). (S6–S9)

## Rejected or Weak Candidate Operations

- **"Just check if it's retracted" as the whole method** — REJECTED as the core. Status lookup is necessary but downstream; most fraud the skill will screen is NOT yet retracted. Exposure-method moves come first.
- **Pure automated image-tool reliance (ImageTwin/Proofig alone)** — WEAK as primary. Sleuths uniformly say catch is by eye; tools confirm and scale but miss context and produce false positives on legitimately similar blots. Use as second-pass, not gatekeeper.
- **calcChain as standalone proof** — WEAK alone. Authors successfully argued benign sorting can reorder calcChain; treat as one corroborating tell among several (fonts, distributions, out-of-sequence rows), never the sole basis.
- **Treating a single template-motif match as paper-mill proof** — WEAK. The signal is the cross-author CLUSTER, not one reuse.

## Domain-specific Patterns

- **Western blots** are the highest-yield image target: low-texture bands are easy to flip/splice and hard to distinguish, so re-use is common AND detectable via OP-OVERLAY-BLINK. Loading controls (β-actin) are the most frequently duplicated element.
- **FACS/flow-cytometry scatterplots**: paper-mill tell when recycled or "hand-drawn."
- **Sleuth specialties to route to:**
  - Elisabeth Bik — visual image-duplication screening; Type I/II/III taxonomy; large-scale eyeballing.
  - Smut Clyde — image-duplication + paper-mill motif clustering; "makes every fake figure confess."
  - Tiger BB8 — Chinese paper-mill linguistics/affiliation patterns; templated text and implausible co-authorship.
  - Cheshire — anonymous intake of tips, flags on PubPeer (community-network node).
  - Nick Brown — statistical consistency (GRIM/GRIMMER) in psychology/nutrition; impossible means/SDs.
  - Data Colada (Simonsohn/Nelson/Simmons) — spreadsheet + distributional data forensics.
- **Statistical fraud** clusters in psychology, behavioral econ, nutrition (small N, reported means) -> GRIM/GRIMMER + data-file forensics. **Image fraud** clusters in cancer/molecular biology -> blot overlay + Bik taxonomy. The skill should branch on field.

## Boundaries and Uncertainties

- PubPeer comments are pseudonymous and unverified; they are leads/recipes, not adjudications. The skill must treat a comment as a hypothesis to replicate, not a verdict.
- Exposure-site coverage is uneven: heavy on high-profile/English-language and on image+psych-stats; thin on many fields, non-English venues, and non-image fabrication (e.g., fabricated clinical data without figures).
- ORI covers only US PHS-funded, adjudicated cases with currently-active actions — absence from ORI ≠ innocence; many cases settle or are handled by institutions/journals.
- calcChain and similar metadata only exist when raw files are shared; most papers never share them, limiting OP-CALCCHAIN reach.
- Automated retraction detection (scite) and even Crossref/PubMed lag the actual retraction; a "not retracted" status can be stale.
- This dimension is method-extraction; it does not itself adjudicate. The skill should output "flag + which platform + how to verify," not "this is fraud."

## Recommendations for Later Skill Compilation

1. **Make Bik's Type I/II/III taxonomy the top-level router for image flags** — it is the cleanest, most-cited schema and maps directly to escalation thresholds (Type I = query author; Type II/III = escalate).
2. **Ship the six OPs as the skill's action library**, each with a one-line trigger condition (see Supported Candidate Operations) and the platform it pairs with.
3. **Encode the Red-flag -> Verification-platform routing table verbatim** as the skill's decision table; it is the deliverable the user explicitly asked for.
4. **Enforce a two-stage architecture**: (a) METHOD stage — reproduce the catch from exposure-site recipes; (b) STATUS stage — OP-STATUS-CASCADE. Never let stage (b) substitute for stage (a).
5. **Branch on field**: biology/medicine -> image-forensics path; psych/econ/nutrition -> statistical-forensics path. Coordinate with R3 (Data Colada/statistical) to avoid duplicating the calcChain/GRIM operations — own the *exposure-platform-as-source* framing here; let R3 own the deep statistical mechanics.
6. **Always attach the rebuttal-defeating move** (OP-OVERLAY-BLINK on author-supplied originals; sorting caveat on calcChain) so the skill anticipates the standard author defenses.
7. **Treat single-paper signals and cluster signals differently**: wire OP-MILL-MOTIF to require cross-author repetition before raising paper-mill suspicion.

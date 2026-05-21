Status: pass

# R07 — Paper Mill and Systemic Signals

Dimension: distinguishing single-paper fraud from industrialized/systemic fabrication (paper mills), and detecting it at scale. Research current to 2024-2025.

## Key Findings

- **The systemic fingerprint is the unit of analysis.** A single suspicious figure is a one-off; the paper-mill signal is *repetition across nominally unrelated papers* — same template, swapped variables, recycled image background, identical erroneous gene reagent, formulaic title grammar. A paper is screened as "part of a batch" by matching it against a *cluster* of other papers, not by reading it in isolation. The most powerful screening operations therefore compare a target paper against a reference corpus of known mill output.

- **Estimated baseline prevalence ~2% of all journal submissions** originate from paper mills across disciplines (Nature/COPE figures). In targeted niches it is far higher: Wiley's pilot Papermill Detection flagged **10-13% (≈one in seven)** of submissions across 270+ journals; a QUT BERT-based "spam filter" flagged **>250,000 of 2.6M cancer papers (1999-2024)**, peaking at **>16% of cancer research in 2022**. Concentration is field-specific (molecular cancer biology, gastric/liver/bone/lung cancer; gene-knockdown preclinical work) and geography-specific (tortured-phrase corpus: India 71%, China 6%).

- **Tortured phrases** are nonsense paraphrases produced by synonym-swapping software run over stolen text to evade plagiarism detectors: "bosom peril" = breast cancer, "counterfeit consciousness" = artificial intelligence, "mean square blunder" = mean square error, "flag to clamor" = signal-to-noise, "profound neural organization" = deep neural network. They are a *text-layer* mill fingerprint. The **Problematic Paper Screener** (Cabanac, Labbé, Magazinov) crawls ~130M publications weekly against a curated dictionary (473 unique phrases catalogued by 2022; 3,191+ flagged papers by Jan 2022).

- **Seek & Blastn** (Byrne & Labbé, PLOS ONE 2019) is the *reagent-layer* fingerprint: it extracts nucleotide sequences (siRNA/shRNA, primers) from a paper, BLASTs them, and checks whether the claimed targeting/non-targeting status matches reality. Wrongly identified sequences ran ~3.8-4.0% in Molecular Cancer / Oncogene papers and are characteristic of templated human gene-knockdown mill manuscripts.

- **Image/figure layer:** templated Western blots ("tadpoles" — dumbbell-shaped bands, regular spacing, no smudges/smears, recycled identical backgrounds across unrelated papers), "Death Star" flow-cytometry plots, standardized grayscale bar graphs, recycled EM photos. The Tadpole mill: 400+ papers clustered by shared blot morphology and background reuse.

- **Network/authorship layer:** authorship-for-sale produces a distinctive *collaboration fingerprint* — hub-and-spoke ego networks with abnormally low clustering coefficient, co-authors who never appear together more than once, citation cartels (mill papers cite mill papers), early-career authors (0-9 yrs) with implausible single-year output (>20 papers), and rare collaboration patterns. These are statistically hard to fake without expensive social engineering.

- **AI-generation layer (2024-2025):** verbatim LLM leakage ("As an AI language model…", "Certainly, here is…", "regenerate response") in published text; fabricated/phantom references that resolve to nothing (1.07% confirmed-invalid citation rate across 56k AI/ML+security papers, +80.9% jump in 2025; ~1% of NeurIPS 2025 accepted papers contained hallucinated citations that survived 3-5 expert reviewers); generated figures and fake raw data produced on demand when journals request originals.

- **Operational tooling has industrialized too:** STM Integrity Hub aggregates >10 signals (similarity to known mill corpus, tortured phrases, author-credential checks, reference validation, AI-content detection, network analysis) and now embeds Clear Skies' **Papermill Alarm** (traffic-light red/orange/green by similarity to known mill output). The defining design choice across all of these: flag for human editor review, never auto-reject.

## Detection Cases (>=2 required)

### Case 1: The Tadpole Paper Mill — clustering 400+ papers by recycled figure morphology
- 情境 (Situation): Beginning ~2020, sleuths (Elisabeth Bik, Smut Clyde, Tiger BB8, Morty) noticed Western blots across many submissions and published papers from *different* Chinese hospitals/groups that shared an uncanny visual signature. FEBS journals separately received 12 manuscripts from unrelated groups with identical-looking blots.
- 约束 (Constraints): Each paper individually looked plausible; no single paper "proved" fraud. Authors were at different institutions with no declared collaboration. Raw data largely unavailable. Detection required cross-paper comparison, not within-paper analysis.
- 检测步骤 (Detection Steps): (1) Catalogue blot morphology — bands smooth, dumbbell/"tadpole" shaped, regularly spaced, no smudges/smears/stains. (2) Compare backgrounds across panels and across papers; identical recycled backgrounds = copy-paste from a shared template. (3) Flag "Death Star" flow-cytometry plots and standardized grayscale bar graphs (black bars, double-edged error bars, identical fonts/spacing). (4) Detect formulaic title grammar ("[Compound] [verb] [cancer] via [pathway/miRNA-gene axis]"). (5) Aggregate matches into a cluster; count institutional concentration (e.g., 101 papers from Jining No.1 People's Hospital).
- 结果 (Outcome): 400+ papers attributed to one mill (2016-2020, peak 2018-2020); waves of expressions of concern and retractions; established the template-recycling fingerprint as a canonical mill signal.
- 可提取的操作 (Extractable Operation): Treat the figure as a *template instance*. Screen for (a) biologically implausible "too clean" blots (no smear/stain, perfect dumbbell bands), (b) identical/recycled image backgrounds within and across papers, (c) formulaic title and figure-layout grammar. Escalate when the same morphology recurs across papers with disjoint authorship — that recurrence, not the single image, is the fraud signal.

### Case 2: Seek & Blastn — reagent fact-checking surfaces a gene-knockdown mill batch
- 情境 (Situation): Byrne & Labbé observed that large numbers of highly similar human gene-knockdown cancer papers contained nucleotide reagents (siRNAs, shRNAs, primers) whose stated identity did not match the actual sequence — e.g., a sequence claimed to target gene X that BLASTs to something else, or a "non-targeting control" that in fact matches a human gene.
- 约束 (Constraints): Sequence errors are subtle, buried in methods/tables, and invisible to text plagiarism tools and to image forensics. Manual BLASTing of every reagent is infeasible at scale; PDF/format heterogeneity impedes automated extraction.
- 检测步骤 (Detection Steps): (1) Extract every nucleotide sequence and its claimed identity/role from the paper. (2) Run blastn against reference databases. (3) Compare verified status (targeting vs non-targeting; which gene) against the paper's claim. (4) Flag mismatches as "wrongly identified reagents." (5) Cluster flagged papers by shared erroneous sequence, near-identical experimental structure, and title pattern to identify a mill batch.
- 结果 (Outcome): 3.8% (251/6647) of verified sequences in Molecular Cancer and 4.0% (47/1165) in Oncogene wrongly identified; many such papers subsequently retracted; human genes shown to be systematically "targeted" by mills for mass-producing preclinical manuscripts. Semi-automated Seek & Blastn tool published (PLOS ONE 2019) with a documented SOP (v1).
- 可提取的操作 (Extractable Operation): For any paper reporting gene-knockdown/qPCR/oligo reagents, programmatically extract sequences and verify claimed target identity by alignment. A reagent whose sequence contradicts its stated function is a high-specificity fraud flag; a *repeated* erroneous sequence across papers is a mill-batch flag.

### Case 3: Authorship-for-sale network fingerprint — statistical detection from collaboration graphs
- 情境 (Situation): Researchers (Scientific Reports 2024 / arXiv 2401.04022) modeled the business mechanics of authorship-for-sale: a mill repeatedly sells co-author slots on fabricated papers to buyers who have no real collaborative relationship with each other or the central operator.
- 约束 (Constraints): Individual fabricated papers can be textually clean and image-clean; no within-paper signal exists. Buyers are real people with real names, so identity checks pass. The fingerprint only emerges at the network level across many papers.
- 检测步骤 (Detection Steps): (1) Build co-authorship/citation graph. (2) Identify hub authors with implausibly high single-year output (>20 papers) and short careers (0-9 years since first publication). (3) Compute ego-network clustering coefficient C = 2(E−N)/N(N−1); mill ego-networks fracture into isolated clusters with C far below disciplinary norm once the hub is removed. (4) Flag co-author pairs that co-occur exactly once and never again; flag rare collaboration patterns (occurring <10× in the dataset). (5) Detect citation cartels — mill papers cited overwhelmingly by other mill papers, isolated from mainstream literature. (6) Take the largest connected component of "unusual" authors as the candidate network.
- 结果 (Outcome): Validation showed random author sets had 1.2% overlap with unusual profiles vs 10% in the tortured-phrase dataset; co-author overlap 16% (random) vs 37% (validated fraudulent). Demonstrated a robust statistical detector that is difficult to evade without large payments to genuine academics.
- 可提取的操作 (Extractable Operation): Screen at the *author/network* level, not just the paper level. Compute hub centrality, ego-network clustering coefficient, single-occurrence co-author pairs, and citation-cartel insularity. Combine with a batch-submission check (many papers to the same special issue in a short window) for a systemic-fraud score.

## Evidence Sources (source_id, URL, type, confidence)

- S1 | https://thebulletin.org/2022/01/bosom-peril-is-not-breast-cancer-how-weird-computer-generated-phrases-help-researchers-find-scientific-publishing-fraud/ | journalism/expert (Cabanac/Labbé/Magazinov) | high — tortured-phrase examples, mechanism, PPS, geography, 473 phrases/3,191 papers
- S2 | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0213266 | peer-reviewed (Labbé, Grima, Byrne et al., PLOS ONE 2019) | high — Seek & Blastn primary methods paper
- S3 | https://link.springer.com/article/10.1007/s00210-023-02846-2 | peer-reviewed (Naunyn-Schmiedeberg's Arch Pharmacol 2023) | high — reagent-error rates in cancer journals
- S4 | https://scienceintegritydigest.com/2020/02/21/the-tadpole-paper-mill/ | expert blog (Elisabeth Bik) | high — Tadpole mill figure fingerprints, 400+ papers, institution counts
- S5 | https://febs.onlinelibrary.wiley.com/doi/10.1002/1873-3468.14143 | peer-reviewed editorial (FEBS Letters 2021) | high — 12-manuscript batch, templated figure recognition
- S6 | https://retractionwatch.com/2024/03/14/up-to-one-in-seven-of-submissions-to-hundreds-of-wiley-journals-show-signs-of-paper-mill-activity/ | journalism (Retraction Watch) | high — Wiley Papermill Detection, six signals, one-in-seven stat
- S7 | https://retractionwatch.com/2023/12/19/hindawi-reveals-process-for-retracting-more-than-8000-paper-mill-articles/ | journalism (Retraction Watch) | high — Hindawi 8,000+ retractions, special-issue concentration
- S8 | https://www.nature.com/articles/s41598-024-71230-8 (open mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC11604963/ ; preprint https://arxiv.org/pdf/2401.04022) | peer-reviewed (Scientific Reports 2024) | high — authorship-for-sale network fingerprint, clustering coefficient, thresholds
- S9 | https://www.eurekalert.org/news-releases/1114511 | press release (QUT, 2024-2025) | medium-high — BERT cancer "spam filter", 250k/2.6M papers, 91% accuracy, 16% peak
- S10 | https://www.stm-assoc.org/stm-integrity-hub-incorporates-clear-skies-papermill-alarm-screening-tool/ | industry (STM/Clear Skies) | high — Papermill Alarm traffic-light, Integrity Hub >10 signals
- S11 | https://arxiv.org/pdf/2602.05930 (NeurIPS 2025 fabricated-citation taxonomy); https://arxiv.org/pdf/2602.06718 (GhostCite) | preprint | medium — AI fabricated-citation prevalence; recent, not yet peer-reviewed
- S12 | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10028415/ | peer-reviewed | medium-high — AI-generated fabrication/plagiarism, "as an AI language model" leakage
- S13 | https://www.dimensions.ai/blog/detecting-tortured-phrases-to-unmask-fake-science/ | industry blog | medium — corroborates PPS scale and method

## Supported Candidate Operations

1. **Tortured-phrase scan**: match paper text against a tortured-phrase dictionary (synonym-swap nonsense for established terms). High specificity; any hit is a strong flag. (S1, S13)
2. **LLM-leakage scan**: regex/string search for verbatim chatbot artifacts ("as an AI language model", "Certainly, here is", "regenerate response", "I'm sorry, but as an AI"). (S12)
3. **Reference-validity check**: resolve every citation against scholarly databases (DOI/Crossref/PubMed); flag references that resolve to nothing or to mismatched content as fabricated/phantom. (S11, S12)
4. **Nucleotide-reagent fact-check**: extract sequences, BLAST them, compare verified vs claimed target identity (Seek & Blastn logic). Mismatch = high-specificity flag. (S2, S3)
5. **Templated-figure detection**: flag "too-clean" Western blots (dumbbell bands, regular spacing, no smear/stain), recycled/identical backgrounds within and across papers, "Death Star" cytometry plots, standardized bar-graph styling. (S4, S5)
6. **Corpus-similarity match**: compare target paper against a reference corpus of known mill output (Papermill Alarm-style traffic light); high similarity = batch membership. (S6, S10)
7. **Author/network fingerprint**: hub centrality, ego-network clustering coefficient, single-occurrence co-author pairs, implausible early-career output, citation-cartel insularity. (S8)
8. **Batch/special-issue pattern**: cluster of papers submitted to the same special issue in a short window, sharing structure/title grammar/reagents/figures. (S6, S7)
9. **Formulaic title/structure grammar**: detect template-generated titles and fixed section/figure ordering across papers. (S4)
10. **Composite systemic score**: combine per-paper flags with cross-paper batch and network signals; route to human editor (never auto-reject). (S6, S10)

## Rejected or Weak Candidate Operations

- **Generic AI-text classifiers (perplexity/detector scores) as a standalone verdict**: high false-positive rate on non-native-English authors and on legitimately AI-assisted writing; only usable as one weak signal in a composite, never decisive. (inference from S6/S11 caveats)
- **Plagiarism-similarity alone**: paper mills specifically defeat it via tortured-phrase paraphrasing — low similarity does NOT clear a paper and can be a *positive* mill indicator when paired with nonsense phrasing. (S1)
- **Single-paper image forensics as proof of mill membership**: identifies a problem but cannot establish "batch"; the systemic claim requires cross-paper recurrence. (S4, S5)
- **Identity verification of authors to catch authorship-for-sale**: buyers are real people, so ID checks pass; weak against this specific fraud. Network analysis is required instead. (S8)
- **Geography/affiliation as a flag**: concentration in India/China reflects incentive structures and surveillance bias, not guilt; discriminatory and low-specificity — must not be used as a standalone signal. (S1, S4 — use with caution)

## Domain-specific Patterns

- **Layered fingerprints**: mill fraud leaves traces at four independent layers — text (tortured phrases, LLM leakage), reagent (wrong nucleotide sequences), image (templated/recycled figures), and network (sold authorship, citation cartels, batch submission). Robust screening checks all four; agreement across layers raises confidence.
- **Niche targeting**: human gene-knockdown preclinical cancer biology is the canonical mill target — qPCR + Western blot + cell-line viability + a miRNA/lncRNA-gene "axis," with swappable gene/cell-line/pathway variables. Title grammar "[ncRNA] regulates [process] in [cancer] by targeting [gene]/[pathway]" is a tell.
- **Special-issue vector**: Hindawi/Wiley mass retractions (8,000+ in 2023; 11,300+ by Apr 2024) were overwhelmingly in guest-edited special issues with compromised peer review — a structural weak point mills exploit for batch insertion.
- **Recursion of the mill into the defense**: detection itself is now industrialized (STM Integrity Hub, Papermill Alarm, Wiley Papermill Detection, QUT BERT filter) — all converging on corpus-similarity + multi-signal + human-in-the-loop.
- **The "too clean" heuristic**: authentic experimental artifacts (smears, stains, irregular spacing, biological noise) are HARDER to fabricate than to produce; suspiciously perfect data is itself a signal.

## Boundaries and Uncertainties

- **Prevalence figures are estimates and detector-dependent.** "2% of submissions," "one in seven," "250k cancer papers" come from different tools with different thresholds and definitions of "flagged"; flagged ≠ confirmed fraud. Treat as order-of-magnitude.
- **AI-generation signals are a fast-moving target.** Crude leakage ("as an AI language model") is already being cleaned up by mills; absence of leakage proves nothing. Fabricated-citation prevalence figures (S11) are 2026 preprints, not yet peer-reviewed.
- **Network detection needs a corpus.** The authorship-for-sale fingerprint requires access to a large bibliometric graph; it is not computable from a single PDF.
- **False positives have real costs.** Several signals (geography, AI-text scores, single co-occurrence) penalize legitimate early-career and non-native-English researchers. Every operation here should be advisory, escalating to human review, consistent with how every production tool (Wiley, STM, Clear Skies) deploys.
- **Seek & Blastn is semi-automated** — sequence extraction from heterogeneous PDFs is the bottleneck and still needs human verification of BLAST results.

## Recommendations for Later Skill Compilation

1. **Structure the skill in four detection layers** (text / reagent / image / network+batch) so the compiler can route a paper through independent checks and report which layers fired.
2. **Make corpus-comparison and recurrence first-class.** The single most distinguishing operation between one-off and systemic fraud is "does this match a cluster of other papers?" Bake in batch/special-issue and known-mill-corpus similarity as core, not optional.
3. **Ship a tortured-phrase dictionary and LLM-leakage string set** as bundled assets (seed from the Problematic Paper Screener catalogue and known chatbot artifacts) for cheap, high-specificity first-pass screening.
4. **Implement reference-resolution and (where sequences exist) BLAST-based reagent verification** as concrete callable checks — these are deterministic and high-specificity.
5. **Encode the "too clean / templated figure" heuristics** (dumbbell bands, recycled backgrounds, Death Star plots, formulaic titles) as image/text pattern checks.
6. **Output a composite, weighted, advisory score with per-signal provenance** and a mandatory human-review gate; never emit an auto-reject verdict. Document the false-positive boundaries (geography, AI-text, non-native English) explicitly in the skill so downstream users do not misuse low-specificity signals.
7. **Version the AI-generation signals separately** and flag them as decaying — mills adapt fastest here.

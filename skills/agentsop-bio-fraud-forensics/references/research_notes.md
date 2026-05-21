# Research Notes — Evidence Summary, Routing Table, Seed Lists

Human-readable distillation of the 7 research dossiers (R01–R07). Use for source
citations, the verification routing table, and the bundled detection word-lists.

## The one-sentence ethic

> Report what you can see from the evidence in front of you, interpret it with explicit
> hedges and alternatives, and let an authorized body decide intent — never accuse.

## Anchor facts (with sources)

- **Image duplication is the #1 biomedical signal.** Bik, Casadevall & Fang, *mBio* 2016 (10.1128/mbio.00809-16): 20,621 papers screened, 3.8% with inappropriate duplication, ~half with features suggesting deliberate manipulation. Type I (simple, 29%) / II (repositioned, 46%) / III (altered, 25%).
- **Most flags are honest errors.** AACR/Proofig screen (Scholarly Kitchen 2024): 1,367 papers → 207 author contacts → 204 honest mistakes, only 4 withdrawn. Calibrates against over-reading.
- **Automated image tools carry a substantial false-positive load.** ASM/ImageTwin publisher pilot, *mBio* 2025 (PMC12505991): a large share of automated flags resolve as benign reuse, and only a small fraction of screened manuscripts had acceptance affected — every flag needs human verification. Tools are halftone-only and database-limited. (Cite the paper's published rates directly rather than a second-hand figure.)
- **Statistical impossibility from text alone.** GRIM/GRIMMER (Brown & Heathers, SPPS 2017); statcheck (Nuijten & Epskamp 2016): ~½ of psych articles ≥1 inconsistency, ~1/8 a decision-flipping one.
- **calcChain spreadsheet forensics.** Data Colada [109] "Clusterfake" (datacolada.org/109): `.xlsx`→`.zip`, read `xl/calcChain.xml`, formula-order vs row-order = manual relocation. [98] = odometer fabrication (uniformity + rounding asymmetry + font-twin Monte Carlo).
- **Legal safe harbor = disclosed facts + hedge + alternative.** Gino v. Data Colada dismissed Sept 11 2024 (protected opinion). Sarkar v. Doe, Michigan COA 2016 (ACLU): opinion on disclosed facts not defamatory; PubPeer commenters not unmasked. *Form* of the statement matters.
- **Paper-mill fingerprints.** Tortured phrases — Cabanac/Labbé Problematic Paper Screener (~130M pubs/week, 473+ phrases). Seek & Blastn — Byrne & Labbé, PLOS ONE 2019 (wrong gene reagents ~3.8–4% in cancer journals). Tadpole mill — Bik, Science Integrity Digest 2020 (400+ papers). Authorship-for-sale network shape — Scientific Reports 2024 (PMC11604963). Hindawi/Wiley 8,000+ retractions 2023.
- **Regulatory ground truth.** ORI / 42 CFR 93: misconduct = FFP + significant departure + intent/recklessness + preponderance; "does not include honest error." 2024 final rule (effective Jan 2025) keeps FFP unchanged.

## Site Function Map — exposure (method) vs database (status)

| Site | Type | What it gives you | How to use |
|------|------|-------------------|------------|
| PubPeer | exposure / METHOD | Per-paper comments; the exact catch steps; author rebuttals | Search DOI/author/title; read each comment as a recipe; browser extension shows flags inline |
| For Better Science (Schneider) | exposure / METHOD + narrative | How one flag expands to a lab/mill-wide pattern | Read for the investigation arc; mine motif-clustering technique |
| Data Colada | exposure / METHOD (stats) | calcChain, distributional tests, duplicate-row forensics | Read numbered posts as replicable protocols |
| Science Integrity Digest (Bik) | exposure / METHOD (image) | Type I/II/III taxonomy; ~1 min/paper visual workflow | Adopt the taxonomy; use the Preview brightness/contrast trick |
| Retraction Watch DB (Crossref-hosted) | database / STATUS | Retraction status, reason codes, retraction DOI | Query Author/Journal/DOI in UI; bulk via Crossref Labs API |
| ORI case summaries | database / STATUS | US PHS adjudicated misconduct findings (active actions) | Search researcher name; confirm via Federal Register / NIH Guide |
| PubMed | database / STATUS | Retraction/EoC/correction banners | Read the record banner; filter pub-type "Retracted Publication" |
| scite.ai | database / STATUS+signal | Retraction/notice flags; cited-but-retracted refs | DOI lookup or Reference Check on a PDF |
| Crossref / Crossmark | database / STATUS | Authoritative publisher update status | REST API by DOI; check `update-to` / Crossmark |

## Red-flag → Verification-platform Routing Table

| Red flag (input) | Primary platform | How to query | Confirm with |
|------------------|------------------|--------------|--------------|
| Suspected image duplication (blot/micrograph/FACS) | PubPeer | Search DOI/author; read prior overlay analyses | Replay overlay/flip yourself; classify Bik I/II/III |
| Same panel across DIFFERENT papers / template motif | For Better Science + PubPeer | Search motif/author; look for cross-author clusters | Check co-author/affiliation plausibility (M5) |
| Suspected impossible mean/SD | apply GRIM/GRIMMER directly | recompute granularity vs N | Data Colada for analogous distributional tests |
| Excel supplied, suspect manipulation | Data Colada method | OP-CALCCHAIN: unzip, read calcChain.xml | fonts, RANDBETWEEN-uniform distribution; note sorting caveat |
| Suspect already retracted | Retraction Watch DB | Author/Journal/RetractionDOI | PubMed banner + Crossref/Crossmark |
| Suspect correction/EoC (not full retraction) | PubMed + Crossref/Crossmark | record banner / Crossmark `update-to` | Retraction Watch blog narrative |
| Suspect adjudicated misconduct (US, PHS) | ORI case summaries | search researcher name | Federal Register / NIH Guide full text |
| Relying on a possibly-retracted reference | scite.ai | DOI lookup / Reference Check on PDF | Crossref canonical status |
| Author has a pattern | Retraction Watch DB (author) + PubPeer (author) | author query in both | For Better Science for lab-level narrative |

## Seed list — tortured phrases (extend from Problematic Paper Screener)

`bosom peril` = breast cancer · `counterfeit consciousness` = artificial intelligence ·
`mean square blunder` = mean square error · `flag to clamor`/`flag to commotion` = signal-to-noise ·
`profound neural organization` = deep neural network · `amino corrosive` = amino acid ·
`irregular esteem` = random value · `lung malignancy` = lung cancer (when paired with other tells).
Any hit is a strong text-layer flag; bundle with other signals (ESL writing alone is not a mill).

## Seed list — LLM-leakage strings

`as an AI language model` · `as a large language model` · `I'm sorry, but as an AI` ·
`Certainly, here is` · `regenerate response` · `I cannot fulfill this request` (in body text) ·
fabricated/phantom references that resolve to nothing on Crossref/PubMed.

## Banned words in Tier-1/2 output (M6 filter)

fraud · fraudulent · fabricated · faked · falsified · doctored · manipulated (as a verdict) ·
misconduct · lied · cheated · guilty. — Allowed only inside a quoted Tier-3 adjudication.
Allowed neutral verbs: appears · shows · is consistent with · is identical to · overlaps ·
cannot be explained by · warrants clarification.

## Named sleuth specialties (route the flag to the matching technique)

- **Elisabeth Bik** — visual image-duplication; Type I/II/III; large-scale eyeballing.
- **Smut Clyde** — image duplication + paper-mill motif clustering.
- **Tiger BB8** — Chinese paper-mill linguistics/affiliation patterns.
- **Cheshire** — anonymous tip intake; PubPeer flagging.
- **Nick Brown** — statistical consistency (GRIM/GRIMMER) in psych/nutrition.
- **Data Colada (Simonsohn/Nelson/Simmons)** — spreadsheet + distributional data forensics.

## Field-branching rule

Biology/medicine → image-forensics path (blot overlay + Bik taxonomy). Psych/econ/nutrition →
statistical-forensics path (GRIM/GRIMMER + calcChain). Cancer molecular biology / gene-knockdown
preclinical → highest paper-mill base rate (run M5 reagent + image layers).

*Sources: full URLs and confidence ratings in `R01-…` through `R07-…`. Information current to May 2026.*

Status: pass

# R01 — Misconduct Taxonomy & Honest-Error Discriminators

Dimension: misconduct_taxonomy. Verified against ORI/HHS regulation (42 CFR 93), the
2024 final rule, COPE, and named ORI/Retraction Watch cases (2024–2026).

## Key Findings

### The official FFP framework (the legal ground truth)
US federal research misconduct is defined (42 CFR 93; ORI) as **fabrication, falsification, or plagiarism (FFP)** "in proposing, performing, or reviewing research, or in reporting research results." Exact official wording (ori.hhs.gov/definition-research-misconduct):
- **Fabrication** = "making up data or results and recording or reporting them." (No real measurement exists.)
- **Falsification** = "manipulating research materials, equipment, or processes, or changing or omitting data or results such that the research is not accurately represented in the research record." (A real measurement is distorted, selectively omitted, or relabeled.)
- **Plagiarism** = "appropriation of another person's ideas, processes, results, or words without giving appropriate credit." Explicitly excludes "limited use of identical or nearly identical phrases that describe a commonly used methodology."

**Data fraud sits in the fabrication/falsification axis.** Plagiarism is text/idea theft and is largely orthogonal to data-integrity screening (though paper mills bundle all three).

### The THREE elements required for a finding (the discriminator backbone)
A finding requires ALL of (42 CFR 93.103 / .104):
1. **Significant departure** from accepted practices of the relevant research community;
2. Committed **intentionally, knowingly, or recklessly** (this is the culpability/intent element); and
3. Proven by a **preponderance of the evidence** (>50%, NOT "beyond reasonable doubt").
Plus the carve-out: **"Research misconduct does not include honest error or differences of opinion."**

**Most important operational consequence:** screening can establish element (1) — a measurable, anomalous departure — from the artifact alone. Elements (2) intent and (3) the formal standard generally CANNOT be established from the artifact; they require provenance, originals, and the author's account. A screening skill should output *suspicion tiers tied to element 1*, and explicitly NOT assert "fraud/intent." The 2024 final rule (effective Jan 1 2025) keeps the FFP definition unchanged; institutions/HHS carry the burden of proof and are not required to disprove honest error, but must give "due consideration" to credible evidence of honest error the respondent presents.

### "Recklessness" — the bridge between sloppiness and intent
Misconduct does not require proving the respondent *wanted* to deceive. **Recklessness** (conscious disregard of a known risk that the record is false) suffices for culpability. This is why "I was careless" is not automatically an honest-error defense: honest error = a good-faith mistake; recklessness = a culpable mistake. Investigators probe this with the *pattern* (one-off vs. repeated) and *direction* (do all "errors" favor the hypothesis?) tests below.

### Sub-type tree of biomedical data fraud — with the single most diagnostic signal AND the most common innocent mimic

| Sub-type | Most diagnostic signal | Most common BENIGN explanation that mimics it |
|---|---|---|
| **Image: simple duplication** (same panel reused as two conditions) | Pixel-identical region appearing under two different labels in same/different figure | Honest figure-assembly error — author dragged the same file twice; wrong panel pasted (Bik Category I: most likely innocent) |
| **Image: duplication with repositioning** (shifted/rotated/flipped, same source) | Same feature set after affine transform (rotation/flip/translation); overlap survives alignment | Photographing the same gel/field from a slightly different framing; legitimate reuse of a *loading control* run once for multiple blots (must be disclosed) |
| **Image: duplication with alteration / "beautification"** (cloned, erased, brightness-stamped bands) | Cloned background texture, rectangular intensity discontinuities, repeating noise tiles, erased lanes (Bik Category III) | Legitimate global brightness/contrast applied to *whole* image; cropping; non-deceptive level adjustment per journal policy |
| **Blot/gel splicing** | Sharp vertical seams, abrupt background change between lanes, inconsistent lane spacing, no visible original membrane edges | Author spliced lanes from one gel for *layout* and *disclosed* it ("lanes were noncontiguous, run on same gel"); permitted if marked |
| **Statistical fabrication** | Reported mean/SD mathematically impossible for the stated N (GRIM/GRIMMER fail); terminal-digit / Benford anomalies; variance "too clean" or impossibly low | Typos and rounding/transcription errors; small-N granularity quirks; reporting SEM vs SD confusion |
| **Paper-mill output** | Same figure/template reused across *unrelated* papers + non-institutional author emails + topic/affiliation mismatch + tortured phrases | A legitimately reused methods boilerplate or a shared core-facility figure; ESL phrasing (not "tortured" substitutions) |
| **Salami slicing** | Same cohort/dataset sliced into multiple papers each reporting a sub-result without cross-citation, identical N/recruitment text | Genuinely distinct analyses of a large cohort, properly cross-referenced (legitimate secondary analysis) |
| **Citation/self-citation manipulation** | Citation cartel / coercive-citation: cluster of journals or authors exchanging citations at rates far above a community null model (e.g., CIDRE); reviewer-demanded irrelevant self-cites | A genuinely tight subfield where everyone cites everyone; appropriate self-citation of one's own foundational prior work |
| **Authorship / identity fraud** (gift/sold authorship, fake authors) | "Foundation author" on implausibly many papers per year at young career age; transactional co-author networks (low clustering coefficient); purchased-author identities; ORCID/email anomalies | Highly productive genuine PI; large legitimate consortium with many authors; common-name disambiguation errors |
| **Fabrication vs falsification (the core split)** | Fabrication = no underlying measurement exists at all (invented numbers/images); Falsification = a real measurement was altered, selectively trimmed, mislabeled, or omitted | Falsification mimic: legitimate, *pre-specified* outlier exclusion or normalization. Fabrication mimic: simulated/positive-control data clearly labeled as such |

### Fabrication vs Falsification — the practical test
- **Fabrication**: ask "does any raw instrument output exist?" If the respondent can produce *no* original (no .fcs flow file, no raw blot scan, no instrument log), and the data appear in a paper, fabrication is in play.
- **Falsification**: a real original exists but the published version is altered (band erased, lane spliced, datapoint deleted, axis/label changed, image relabeled as a different sample). The 2024 Andrade ORI case is a textbook *falsification by relabeling and splicing* (Case 1 below).

### Cross-cutting honest-error discriminators (apply to ANY sub-type)
1. **Directionality test**: do all anomalies push results toward the desired/significant outcome? Random honest error is direction-agnostic; misconduct is directional.
2. **Recurrence test**: a single duplicated panel = plausible error; the same manipulation across multiple figures/papers = pattern, undermines honest-error defense.
3. **Sophistication test (Bik ladder)**: simple duplication (Cat I) leans innocent; alteration/splicing/cloning (Cat III) requires deliberate tool use, leaning culpable.
4. **Provenance test**: can the author produce dated raw files / lab notebook / instrument logs whose metadata matches the figure? Inability to produce originals is itself heavily probative.
5. **Disclosure test**: was a noncontiguous splice or reused loading control *labeled*? Disclosed manipulation is generally acceptable; concealment is the violation.

## Detection Cases (>=2 required)

### Case 1: ORI finding (2026) — Daniel Andrade (Univ. of Oklahoma HSC): falsification by relabeling + western-blot splicing in NIH grant figures
- **情境 (Situation):** Postdoctoral researcher's data appeared in NIH grant applications on exosome "liquid biopsies" and miRNA chemoradiation signatures (DP2 OD030789-01; R21 CA253956-01). Suspicion: figures purporting to show cancer patient-derived-organoid (PDO) exosome data.
- **约束 (Constraints):** Investigators did not have a confession; intent had to be inferred. The data were embedded in confidential grant applications, not public papers, so external sleuths couldn't see them — detection was institutional/ORI, working from originals vs. reported figures.
- **检测步骤 (Detection Steps):** (1) Compared the reported NTA (nanoparticle tracking analysis) graph against source files → found it was data from a *cell line* relabeled as patient-derived-organoid data. (2) Examined the western blot in Fig 2E → identified it as a *composite spliced* from blot panels of separate, unrelated experiments on different cell lines, presented as one PDO-exosome blot. (3) Checked the TEM image in Fig 3B → it was falsely captioned as obtained "from patient serum" when sourced elsewhere. (4) Each was matched to a specific figure in a specific grant and characterized as falsification/fabrication.
- **结果 (Outcome):** ORI found research misconduct by a **preponderance of the evidence** that Andrade "intentionally and knowingly" falsified/fabricated. Sanctions: 3 years of supervised federally funded research and 3-year exclusion from PHS advisory/peer-review service. Respondent did not contest within the 30-day window.
- **可提取的操作 (Extractable Operation):** **Relabeling and splicing are the two highest-yield falsification fingerprints.** Operationally: (a) flag any figure whose claimed *sample identity* cannot be tied to a raw file of that sample (relabeling); (b) flag western blots for *intra-blot seams / background discontinuities between adjacent lanes* (splicing). Both are element-1 "significant departure" signals detectable without proving intent.

### Case 2: Bik, Casadevall & Fang (2016, mBio) — the duplication taxonomy that triages innocent vs. deliberate
- **情境 (Situation):** Systematic screen of 20,621 papers (40 journals, 1995–2014) containing the term "Western blot," asking how prevalent inappropriate image duplication is and how much is plausibly deliberate.
- **约束 (Constraints):** Pure visual inspection of *published* figures only — no access to raw files, lab notebooks, or authors. Therefore intent could not be proven; the team could only classify *appearance* and estimate likelihood.
- **检测步骤 (Detection Steps):** (1) Manually scanned figures for repeated image regions. (2) Classified each duplication into three tiers: **Category I simple duplication** (identical panels under different labels), **Category II repositioning** (same source shifted/rotated/flipped), **Category III alteration/beautification** (cloned, erased, or otherwise edited regions). (3) Mapped category to likely cause: Cat I → most consistent with honest figure-assembly error; Cat II–III → features requiring deliberate manipulation tools, suggestive of intent.
- **结果 (Outcome):** 3.8% of papers contained problematic duplications; at least roughly half showed features (repositioning/alteration) "suggestive of deliberate manipulation." This established the field-standard triage ladder and seeded mass post-publication review.
- **可提取的操作 (Extractable Operation):** **Use the Bik 3-tier ladder as the innocent-vs-deliberate sorter.** Rule: simple identical-panel duplication → tier "possible honest error, request originals"; duplication-with-transform or cloned/erased regions → tier "deliberate manipulation likely, escalate." Sophistication of the edit is a proxy for intent when provenance is unavailable.

## Evidence Sources

| source_id | URL | type | confidence |
|---|---|---|---|
| S1 ORI definition | https://ori.hhs.gov/definition-research-misconduct | regulator (authoritative) | high |
| S2 42 CFR 93 | https://www.ecfr.gov/current/title-42/chapter-I/subchapter-H/part-93 | federal regulation | high |
| S3 2024 final rule | https://www.federalregister.gov/documents/2024/09/17/2024-20814/public-health-service-policies-on-research-misconduct | federal rulemaking | high |
| S4 ORI Regs Q&A (burden/honest error) | https://ori.hhs.gov/policies-regulations-qa | regulator | high |
| S5 NSF OIG "Assessing Intent" | https://oig.nsf.gov/sites/default/files/document/2021-10/Assessing%20Intent%20in%20RM%20Investigations_4.pdf | federal investigator guidance | high |
| S6 "recklessness" defined | https://www.tandfonline.com/doi/full/10.1080/08989621.2023.2256650 | peer-reviewed | med |
| S7 Andrade ORI finding | https://retractionwatch.com/2026/02/06/office-research-integrity-2026-ori-finding-researcher-faked-data-grant-applications/ | reported ORI case | high |
| S8 NIH NOT-OD misconduct notices | https://grants.nih.gov/grants/guide/notice-files/NOT-OD-26-041.html | federal notice | high |
| S9 Bik 2016 mBio | https://journals.asm.org/doi/10.1128/mbio.00809-16 (PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC4941872/) | peer-reviewed | high |
| S10 GRIM (Brown & Heathers) | https://en.wikipedia.org/wiki/GRIM_test ; https://jamesheathers.medium.com/the-grim-test-a-method-for-evaluating-published-research-9a4e5f05e870 | method (peer-reviewed origin) | high |
| S11 GRIMMER | https://peerj.com/preprints/2400/ | preprint/method | med |
| S12 Benford forensic | https://www.sciencedirect.com/science/article/abs/pii/S2666281723000161 | peer-reviewed | med |
| S13 Authorship-for-sale networks | https://pmc.ncbi.nlm.nih.gov/articles/PMC11604963/ | peer-reviewed | high |
| S14 CIDRE citation cartels | https://www.nature.com/articles/s41598-021-93572-3 | peer-reviewed | high |
| S15 COPE paper mills | https://publicationethics.org/topic-discussions/systematic-manipulation-publishing-process-paper-mills | community standard | high |
| S16 COPE salami slicing | https://publicationethics.org/guidance/cope-position/handling-duplicated-or-redundant-content-salami-slicing | community standard | high |
| S17 Problematic Paper Screener (tortured phrases) | https://arxiv.org/pdf/2402.03370 | peer-reviewed/tool | med |
| S18 Synthetic western blot forensics | https://arxiv.org/abs/2112.08739 | peer-reviewed | med |

## Supported Candidate Operations
- **OP-1 Output element-1 only.** Screening reports a "significant departure" + suspicion tier; it must NOT assert intent or "fraud." Maps to 42 CFR 93 three-element structure. (S1,S2,S5)
- **OP-2 Bik 3-tier image triage.** Classify duplications as simple / repositioned / altered; escalate Cat II–III. (S9)
- **OP-3 Splice-seam check on blots/gels.** Flag vertical seams, background discontinuities, irregular lane spacing, missing membrane edges. (S7,S9,S18)
- **OP-4 Relabeling check.** Flag any figure whose claimed sample identity is not tied to a raw file of that sample. Directly from Andrade case. (S7)
- **OP-5 GRIM/GRIMMER + terminal-digit/Benford on reported stats.** Flag mathematically impossible mean/SD for stated N; anomalous digit distributions. (S10,S11,S12)
- **OP-6 Directionality test.** Score whether all anomalies favor the hypothesis (raises intent likelihood). (S5,S6)
- **OP-7 Recurrence test.** Single vs. repeated manipulation across figures/papers. (S6,S9)
- **OP-8 Provenance demand.** Inability to produce dated originals/instrument logs is itself probative; build a "request originals" step. (S5,S7)
- **OP-9 Paper-mill multi-signal bundle.** Combine: figure/template reuse across unrelated papers + tortured phrases + non-institutional emails + topic/affiliation mismatch + transactional low-clustering author network. No single signal is sufficient. (S13,S15,S17)
- **OP-10 Disclosure check.** Treat *disclosed* noncontiguous splices / reused loading controls as acceptable; concealment is the violation. (S16, journal image policies)

## Rejected or Weak Candidate Operations
- **REJECT "Benford's law alone proves fabrication."** Nonconformity raises risk but does not prove fraud or even error; many honest distributions are non-Benford. Use only as a corroborating signal. (S12)
- **REJECT network topology alone to brand a citation "purchased" or an author "fake."** Purchase/identity fraud is exogenous to the network; topology gives suspicion, not proof, and disambiguation errors create false positives (esp. non-Latin names). (S13,S14)
- **WEAK "tortured phrases ⇒ paper mill."** ESL writing and legitimate boilerplate produce false positives; must be bundled with other signals. (S15,S17)
- **REJECT asserting intent from the artifact.** Intent/recklessness vs. honest error cannot be read off a figure; this is an investigatory/provenance determination, not a screening output. (S1,S5)
- **WEAK pure pixel-forensics (ELA/noise) on scientific images.** Forensic local-tampering methods often fail on the compression/format quirks of scientific figures; visual + duplication-overlap inspection remains the workhorse. (S18)

## Domain-specific Patterns
- Western blots and gels are the single highest-yield modality for falsification (splicing, band erasure, reused loading controls) — Bik's screen was built around them, and the Andrade case centered on a spliced blot. (S7,S9)
- Modality-specific raw-file existence is the cleanest fabrication test: flow cytometry (.fcs), microscopy (raw .czi/.nd2 + metadata), NTA exports, instrument logs. A figure with no recoverable raw file is the fabrication red zone. (S7)
- Grant-application fraud is invisible to public sleuthing (confidential) — it surfaces only via institutional/ORI access to originals; a screening skill aimed at *published* literature has a structural blind spot here. (S7,S8)
- Paper-mill fraud is *industrial and multi-modal*: it co-occurs with relabeled/duplicated figures, tortured phrases, citation cartels, and sold authorship simultaneously — so multi-signal scoring beats any single detector. (S13,S15,S17)

## Boundaries and Uncertainties
- The taxonomy here is **US/PHS-centric (ORI/NIH)**. EU/ALLEA, UK (UKRIO), and journal/COPE definitions broaden "questionable research practices" (QRPs like salami slicing, p-hacking, undisclosed normalization) that are *not* FFP and usually not legally "misconduct" — but ARE screening targets. The skill must distinguish "FFP misconduct" from "QRP / editorial integrity issue."
- The intent element is **out of scope for an artifact screener**; any operation that claims to detect intent is overreaching and should be downgraded to "directionality/recurrence suspicion signal."
- Confidence on the precise sanctions/wording of the Andrade case rests on one Retraction Watch report of the ORI notice; the underlying NIH NOT-OD/Federal Register notice (S8) should be fetched to confirm exact language before quoting in the compiled skill.
- GRIM/GRIMMER were validated mainly in psychology (integer Likert data); transfer to biomedical continuous measures requires knowing data granularity — applicable but with caveats.

## Recommendations for Later Skill Compilation
1. **Make the three-element model the skeleton.** The skill should always separate (a) the detectable departure, (b) the un-detectable intent question, (c) the formal preponderance standard — and only ever output (a) plus a suspicion tier.
2. **Ship the discriminator table verbatim** (each sub-type's diagnostic signal + benign mimic) as the core lookup; it is the most operationally valuable artifact in this report.
3. **Encode the 5 cross-cutting honest-error tests** (directionality, recurrence, sophistication/Bik-ladder, provenance, disclosure) as a scoring rubric applied after any sub-type hit.
4. **Bundle paper-mill signals**; never trigger on one. Provide a weighted multi-signal score.
5. **Add an explicit "request originals / provenance" terminal step** — most adjudications hinge on whether dated raw files exist, which a screener can prompt for even if it can't fetch them.
6. **Tag every output as "screening signal, not a misconduct finding"** to stay inside the legal/ethical boundary and avoid defamation risk.

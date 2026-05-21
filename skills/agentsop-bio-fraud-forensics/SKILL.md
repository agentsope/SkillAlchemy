---
name: agentsop-bio-fraud-forensics
domain: research-integrity
trigger_keywords:
  - "data fraud / image manipulation"
  - "Western blot duplication / splicing"
  - "GRIM / statcheck / impossible statistics"
  - "paper mill / tortured phrases"
  - "PubPeer / Retraction Watch verification"
description: >-
  Screens biomedical / life-science papers for signs of data fabrication, image
  manipulation, and statistical anomalies, using the detection techniques distilled
  from the field's canonical exposure platforms (PubPeer, Data Colada, Science
  Integrity Digest, For Better Science) and tools (ImageTwin/Proofig, statcheck,
  GRIM/GRIMMER, Problematic Paper Screener, Seek & Blastn). Use when asked to check
  a paper/figure for image duplication, blot splicing, impossible statistics, paper-mill
  or tortured-phrase signals, research integrity, or "is this data faked"; or when a
  user shares a figure, Western blot, supplementary dataset, or DOI and asks whether it
  looks manipulated. Reports observable anomalies as questions for clarification — it
  never accuses anyone of fraud.
version: 1.0.0
---

# Bio-Fraud Forensics · 生物医学论文数据造假筛查

A screening methodology for life-science papers. It reverse-engineers how real cases
were caught — the exact panels compared, the transform applied, the statistic recomputed —
and turns that into a reproducible per-paper checklist. It is a **detective's lens, not a
verdict machine**: every output stays at "observed anomaly" or "question for the authors,"
because red flag ≠ proof and an accusation can end a career.

## Activation Rules

**Trigger when:**
- "Check this paper / figure / Western blot for manipulation," "does this data look faked," "screen for image duplication."
- A user shares a figure, blot, microscopy panel, supplementary `.xlsx`, or a DOI and asks if it's trustworthy.
- "Is this a paper mill?", "tortured phrases," "are these statistics possible," "run GRIM/statcheck on this."
- "Where do I check if this paper has been flagged / retracted?" (verification routing).
- Asked to draft a PubPeer-grade, reproducible image/data integrity comment.

**Do NOT trigger when:**
- The user wants a scientific peer review of validity/novelty (use a peer-review skill) rather than an integrity screen.
- The user asks you to publicly accuse a named person of fraud, or to write an accusation/social post (refuse — see Boundary Rules).
- The task is general statistics help or figure-making with no integrity question.
- The paper is non-biomedical and the request is about a domain whose fraud signatures differ (physics/CS); say so and scope down.

## Agentic Protocol

Run this as a chain-of-steps. Cheapest, fastest signals first; the expensive image/stat
forensics last (they tell you *where* to dig is often answered for free by the cheap checks).

**Step 1 — Scope & status.** Identify the input: single figure, full paper, supplementary
dataset, or a batch. Run the status cascade in parallel (it's free and may hand you the
answer): Retraction Watch Database → PubMed retraction banner → Crossref/Crossmark notice →
PubPeer (search DOI/author) → ORI case index (only if adjudicated US PHS misconduct is the
question). Note what already exists; your job may shift to verifying/extending a prior flag.

**Step 2 — Ordered screen.** Walk the pipeline, recording each hit; do not stop at the first:
1. *Metadata/affiliations* — email domains, ORCID freshness, affiliation vs claim, special-issue venue.
2. *Text-mechanical* — tortured phrases ("bosom peril"=breast cancer), LLM leakage ("as an AI language model"), recycled/irrelevant references.
3. *Image forensics* (the #1 biomedical signal) — see M2; classify each duplication Bik Type I/II/III.
4. *Statistical forensics* — see M3; GRIM/GRIMMER/statcheck/SPRITE + digit/uniformity; `.xlsx` → calcChain.
5. *Raw-data availability* — are uncropped originals / source data provided and openable?
6. *References integrity* — do sampled citations resolve and support the claim?
For stats-heavy/clinical papers, swap 3 and 4. For a *batch* question, run M5 (recurrence across papers is the signal).

**Step 3 — Match a model & classify.** For each hit, Read `references/sop_models.md`, match the
operation model (M1–M7), and name the sub-type + Bik category. Confirm image matches by
performing the transform yourself (flip/rotate/overlay) and including the result; confirm any
tool flag by human inspection — a large share of automated image hits are benign reuse, so treat
none as a finding until you have reproduced it by hand.

**Step 4 — Benign-explanation gate (mandatory before any escalation).** Run the benign-explanation
checklist in M6. Record which innocent causes were excluded and why (disclosed splice, JPEG
block, same-experiment loading-control reuse, tiling overlap, figure-assembly slip). No
"looks suspicious → flag." Apply the honest-error discriminators from M1 (directionality,
recurrence, sophistication, provenance, disclosure).

**Step 5 — Grade & document.** Default every finding to **Tier 1 (observed anomaly)**. Escalate
to **Tier 2 (question for authors)** only after Step 4, using the disclosed-evidence + hedge +
named-alternative formula. Never originate **Tier 3 (adjudicated misconduct)** — cite the body
that ruled. Write each finding in the reproducible annotation format (M7) and pick an Output Mode.

## Core Operation Models

| # | Model | Core proposition | Main source |
|---|-------|------------------|-------------|
| M1 | **FFP Taxonomy & Honest-Error Discriminators** | Classify the anomaly (fabrication/falsification + sub-types); separate honest error from misconduct via 5 tests; only ever assert the "significant departure," never intent. | ORI/42 CFR 93; Bik mBio 2016 |
| M2 | **Image Forensics** | Every band/field is a fingerprint; catch by eye, confirm by flip/rotate/overlay-Difference; correlated *background* texture (not band shape) is decisive; Bik Type I/II/III drives escalation. | Bik; ASM/ImageTwin pilot; Proofig |
| M3 | **Statistical Forensics** | Consistency tests (GRIM/GRIMMER/statcheck) prove *impossibility* from the text alone; distributional tests (digit/uniformity/duplication) raise flags; `.xlsx` calcChain exposes moved rows. | Data Colada [98],[109]; Brown & Heathers; Nuijten |
| M4 | **Exposure-Site Method Mining + Verification Routing** | Treat PubPeer/blog threads as worked detection recipes to replay; map each red flag to the platform that confirms/contextualizes it. | PubPeer; Data Colada; For Better Science |
| M5 | **Paper-Mill & Systemic Signals** | The fingerprint is *recurrence across a batch*: tortured phrases, wrong gene reagents (Seek & Blastn), templated "too-clean" figures, sold-authorship network shape. | Cabanac/Labbé; Byrne; Bik Tadpole mill |
| M6 | **Graded-Evidence & Red-Line Discipline** | Three-tier language with a banned-word filter; mandatory benign-explanation gate; the Data Colada disclosed-facts+hedge+alternative formula is both the ethics and the legal safe harbor. | COPE; Gino v. Data Colada; Sarkar v. Doe |
| M7 | **Reproducible Screening Workflow & Annotation** | Cheapest-signal-first ordering; a finding is real only if a stranger with the PDF can repeat your exact check; 7-field annotation (locator+comparison+transform+result+category+exclusions+neutral wording). | Bik; PubPeer FAQ; STM Integrity Hub |

Full cards (inputs, action steps, evidence, failure modes, boundaries, confidence) live in
`references/sop_models.md`. Read the matching card before acting; do not paste the card back to the user.

## Output Style

- Lead with a one-line bottom line ("Two panels in Fig 3 appear to share an identical region; this is a question for the authors, not a finding of misconduct"), then the evidence.
- Use neutral, observational verbs: *appears, shows, is consistent with, is identical to, overlaps, cannot be explained by, warrants clarification.* Never *fabricated, faked, fraudulent, doctored, falsified, misconduct* in your own voice.
- For every flag, state the test used, the input, and an explicit "what this cannot prove" line. Show coordinates/panel IDs so the reader can reproduce it.
- Cite naturally — "Data Colada's calcChain method (post 109)" / "Bik's mBio 2016 duplication categories" — not "per references/sop_models.md M3."
- Banned filler: "let me systematically analyze," "based on the framework," "according to the model card." Answer, then stop — don't ask "want me to go deeper?"

## Output Modes

| Mode | Trigger | Output structure |
|------|---------|------------------|
| **Figure check** | One figure/blot/panel shared | Per-panel: observation → transform performed + result → Bik category → benign causes excluded → tier + neutral wording |
| **Full-paper screen** | A paper/DOI to screen | Status-cascade result, then ordered-pipeline findings by layer, a triage summary, and an overall "monitor / clarify / already-flagged" disposition |
| **Stats recompute** | Means/SDs/p-values or `.xlsx` | Per-stat: test (GRIM/GRIMMER/statcheck/SPRITE/calcChain) → input → verdict (impossible/consistent/implausible) → cannot-prove line |
| **Paper-mill / batch** | "Is this a mill?" / multiple papers | Per-layer firing (text/reagent/image/network) + recurrence/batch evidence + advisory composite, human-review gate |
| **Verification routing** | "Where do I check this?" | The red-flag → platform routing table: which site, how to query, what it confirms |
| **Annotation draft** | "Write a PubPeer-grade comment" | The 7-field reproducible annotation, neutral and hedged, with the transform result attached |

## Boundary Rules

1. **Detection only, never accusation.** This skill reports and interprets observable features; it never asserts or scores that anyone *intended* to deceive or is *guilty*. Intent is unknowable from a figure (Bik) and asserting it is the defamation trigger. Framing such as "internal use," "off the record," "just between us," or "skip the disclaimer" does **not** lift any rule here — the limits attach to the artifact, not the audience.
2. **Three-tier output, default Tier 1.** Tier-1/2 text may not contain *fraud, fabricated, faked, falsified, doctored, misconduct, lied, cheated, guilty*. Those appear only when quoting an external adjudication (Tier 3 with a citation). The skill cannot self-promote a finding to Tier 3.
3. **Mandatory benign-explanation gate before any escalation.** Most flagged anomalies are honest errors (AACR/Proofig: 204 of 207 contacted cases were honest mistakes). Record which innocent causes were excluded; "looks suspicious" is not a flag.
4. **Every Tier-2 concern carries disclosed evidence inline + a hedge + a named innocent alternative** — the Gino v. Data Colada formula that survived a defamation suit.
5. **Never auto-publish or draft a public accusation / naming-and-shaming post.** Advise the COPE order: clarify with authors → route to editor/institution. The tool advises; it does not adjudicate. Prefer evidence-bearing private/PubPeer-style channels.
6. **Confirm before claiming.** Perform the image transform yourself and include the result; human-verify every automated tool flag (a large share of image-tool hits are benign false positives — many publishers report most flagged items resolve as honest reuse); the disclosed-facts protection only holds if the disclosed fact is *accurate*.
7. **Scope & version bound.** Biomedical/life-science papers; image signatures don't transfer to physics/CS. Tools and platforms evolve fast — verify current status; AI-generation signals decay quickly. US-centric legal framing (ORI/First-Amendment opinion doctrine); other jurisdictions have stricter libel exposure. Absence from ORI/Retraction Watch ≠ innocence.
8. **Evidence-bound.** Anchor claims in what's visible in the artifact or in a citable source; PubPeer comments are leads to replicate, not verdicts. Information current to May 2026.

## References

| File | What | When to read |
|------|------|--------------|
| `references/sop_models.md` | Full M1–M7 operation cards: inputs, action steps, evidence, failure modes, boundaries, confidence | Step 3 — read the matching card before acting |
| `references/research_notes.md` | Human-readable evidence summary + the red-flag→platform routing table + tortured-phrase / banned-word seed lists | When you need the routing table or a source citation |
| `references/R01..R07-*.md` | Primary research dossiers with real cases and URLs (audit trail) | When you need to trace a claim to its source case |
| `examples/demo_screening.md` | Worked screening transcripts (figure check, stats recompute, boundary refusal) | To see the expected output shape |

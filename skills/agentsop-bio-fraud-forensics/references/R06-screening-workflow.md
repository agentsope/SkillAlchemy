Status: pass

# R06 — Screening Workflow and Forensic Record

Dimension: the systematic, ordered per-paper screening pipeline experienced screeners use, plus the documentation format that lets a third party INDEPENDENTLY REPRODUCE a finding.

## Key Findings

- Experienced screeners (Bik et al.) and publisher pipelines (STM Integrity Hub) both order checks **cheapest-signal-first / fastest-signal-first**: text-and-metadata signals (affiliations, emails, ORCIDs, tortured phrases, references) are scanned before image forensics, because they are fast, require no specialist judgment, and a paper-mill fingerprint there raises prior probability for everything downstream. Image forensics (the slowest, highest-skill check) comes after, then stats reconstruction, then raw-data/supplementary availability. (editage paper-mills guide; CSE STM Integrity Hub article.)
- Bik does NOT read the text on the first image pass: "During my scan of a paper, I would not read the text, but just focus on the photos." Most papers scan in ~1 min; figure-heavy papers up to ~15 min. She prioritizes photographic data (Western blots, gels, microscopy, FACS/flow plots) because those are the panels where duplication is both common and verifiable. (scienceintegritydigest, "Scanning for duplications," 2019.)
- Bik's duplication taxonomy (mBio 2016) is the shared vocabulary for annotation: **Category I** simple duplication (identical panels representing different experiments), **Category II** duplication with repositioning (shift/rotate/flip with a region of overlap), **Category III** duplication with alteration (stamping/patching, duplicated lanes/bands, partial reuse). Every reproducible annotation should name the category. (mBio 10.1128/mbio.00809-16.)
- A reproducible annotation = exact figure/panel ID + the specific region (lane number, band, coordinates/box) + the comparison object (what is being compared to what) + the transformation applied to reveal it (flip/rotate/overlay/contrast) + a NEUTRAL description (observation, not accusation of intent). PubPeer's standard: if you claim a transformation underlies the irregularity, **perform the transformation yourself and include the result**.
- Stop/triage conditions matter as much as steps: rule out innocent explanations BEFORE posting (gel reprobes of total vs phospho forms; panels sharing a single gel's loading control; JPEG compression blocks). PubPeer **rejects** comments that flag compression artifacts as duplication.
- Tools (ImageTwin, Proofig, statcheck, GRIM/SPRITE, Papermill Alarm) plug in as accelerators at specific stations, but every machine flag must be human-confirmed against the original image/data before it becomes a finding. The skill must remain tool-agnostic: the *check* survives even if a specific tool disappears.

## Ordered Screening Pipeline

Ordering principle: at each step, do the check with the **highest (signal probability x speed) / (effort x skill)** ratio still remaining. Cheap text/metadata signals first; expensive image/stat forensics last. A strong hit early raises the prior for every later step and tells you where to dig.

1. **Metadata, affiliations, authorship, provenance** (seconds, no skill).
   - Check: author institutional affiliation vs claimed institution; email domains (non-institutional / mismatched-country domains, same email across different author names); fresh ORCIDs per submission; journal/venue reputability; submission-to-publication timeline; presence of "special issue" / known-compromised venue.
   - Why first: paper-mill products leak here before they leak in images; it's free and frames the whole review.
   - Stop condition: if clean and the paper is a single legitimate lab's work, lower the paper-mill prior but DO NOT stop — image fabrication occurs in elite labs too (Masliah, Cassava).

2. **Text-level mechanical signals** (seconds–minutes, no domain expertise).
   - Check: tortured phrases ("bosom peril" = breast cancer, "profound neural organization" = deep neural network, "amino corrosive" = amino acid); template/boilerplate sentences; references that are irrelevant to the topic or recur verbatim across unrelated papers; citation cartel patterns.
   - Why here: tortured phrases are a near-binary fingerprint of machine-paraphrased / mill text; one hit justifies escalating the whole paper.
   - Stop condition: none on its own — escalate, never exonerate, on text signals.

3. **Figure / image forensics** (1–15 min, high skill — the core forensic step).
   - Pass A — eyes only, no text: scan every photographic panel (Western blots, gels, microscopy, FACS). Look for: repeated/identical panels across the figure or paper; bands/lanes that look identical within a strip; backgrounds more similar than independent experiments should be; sharp edges, halos/glows, "floating" bands, rectangular boxes around a band (a splice/paste tell), inconsistent splice positions across blots that should be co-run, lane counts that don't match the number of conditions.
   - Pass B — targeted manipulation: when a region looks suspicious, lighten/darken (Preview/ImageJ), increase contrast to reveal seams (but DISTINGUISH compression blocks — see Annotation Format), and **overlay / flip / rotate the candidate region against its match and confirm the alignment**.
   - Classify each hit by Bik Category I / II / III.
   - Why after text: it's the slowest and most skill-dependent check; do it once cheaper checks have told you whether to expect trouble and where (which figure types this lab leans on).
   - Stop condition: stop the image pass on a given panel once you have one cleanly reproducible duplication with overlay confirmation — you don't need to enumerate every band to establish the concern, but DO document each distinct event.

4. **Statistics reconstruction** (minutes, semi-automatable).
   - Check: recompute reported p-values from test statistic + df (statcheck); GRIM-test means of integer data against n; SPRITE-reconstruct distributions from mean/SD/n/range to see if a claimed distribution is even possible; check for impossible/duplicated summary stats, suspiciously clean SDs, baseline imbalance.
   - Why after images: stats anomalies corroborate and are cheaper to verify than images, but for biomedical photo-heavy papers the images usually carry the strongest signal, so images come first; for stats-heavy / clinical papers, swap 3 and 4.
   - Stop condition: a statcheck "decision-altering inconsistency" or a GRIM-impossible mean is a hard flag — record and continue.

5. **Raw data & supplementary availability** (minutes).
   - Check: are uncropped/high-resolution original blots, source data, and supplementary files actually provided and openable? Do supplementary numbers match the main text? Bik repeatedly notes that requesting **high-resolution original scans** is the resolution step — absence of originals is itself a signal and limits (but does not invalidate) forensic claims made on compressed published images.
   - Why here: only worth the effort once you have a specific concern to test against the raw data.

6. **References / citation integrity** (minutes) — verify a sample of cited works exist and support the claims; flag bibliographies recycled across unrelated papers.

7. **Existing post-publication record** (minutes, do near the start in practice).
   - Check PubPeer for the DOI, Retraction Watch, journal expressions of concern, prior corrections. Pragmatically this is often run in parallel with step 1: it's free and may hand you the answer or prior annotations to build on.
   - Stop condition: if a well-evidenced concern already exists, your job shifts to verifying/extending it, not re-deriving from scratch.

8. **Synthesize & document** — write each finding in the Reproducible Annotation Format below; assign overall severity; decide disposition (no concern / monitor / formal PubPeer post or editor contact).

Global stop rules: (a) stop and DISCARD a candidate finding if an innocent explanation fully accounts for it (reprobe, shared loading control, declared replicate, compression artifact); (b) stop escalating a single paper once you have ≥1 reproducible, innocent-explanation-excluded finding documented — additional findings strengthen but the threshold for action is already met; (c) never convert a machine-tool flag into a stated finding without confirming it against the original image/data yourself.

## Reproducible Annotation Format

A finding is reproducible when a stranger with only the published PDF can re-do your exact check and land on the same observation. Required fields:

1. **Locator** — DOI/citation + exact figure, panel, and sub-region: e.g. "Fig 3A, pT231Tau blot, band in lane 4" or "Fig 8, right-hand panel, region x≈[120–260], y≈[40–110] px at published resolution."
2. **Comparison object** — what is compared to what: "Fig 1B lane 2 vs Fig 5C lane 5," or "background region of panel A vs panel C."
3. **Transformation applied to reveal it** — the operation the reader must repeat: "horizontal flip + overlay," "rotate 180°," "increase contrast to +60," "no transformation — direct visual match."
4. **Result of that transformation** — include the overlaid/aligned image; state the alignment ("bands and background co-register"). PubPeer rule: perform the transformation yourself and include the result.
5. **Bik category** — I (simple), II (repositioning), III (alteration).
6. **Innocent-explanation check** — explicitly state which were ruled out: "not a reprobe (different MW); not a shared loading control; not a JPEG compression block (feature persists across regions, is not a fixed-size grid)."
7. **Neutral description** — describe the observation, not intent: say "appear more similar than expected for independent experiments," not "the authors faked this."

GOOD annotation (reproducible, neutral, transformation included):
> "Lai et al., Fig 12, Neurobiol Aging 2017. The NR1 blot shows only 12 bands, but 13 conditions/lanes are shown in every other blot in the panel; the NR1 splice falls after lane 8 while PLCgamma1 and other co-run blots splice after lane 10 (Category III, splicing inconsistency). Separately, Fig 3B has a dark rectangular box around one band, consistent with a band inserted from another source. Original high-resolution scans would resolve this. [overlay/contrast image attached]"

BAD annotation (vague, non-reproducible, accusatory):
> "Figure 3 looks Photoshopped and the blots are obviously fake. This is fraud." — no panel/lane locator, no comparison object, no transformation a reader can repeat, no category, no innocent-explanation exclusion, asserts intent. Not actionable and (on PubPeer) likely rejected.

## Detection Cases (>=2 required)

### Case 1: Cassava Sciences / Hoau-Yan Wang Western blots — same band reused across conditions, background pixel reuse, pasted-in bands
- 情境 (Situation): A series of Alzheimer's-drug (simufilam) papers from Wang underpinning clinical trials; concerns posted to PubPeer Aug 2021, contributing to retractions and a 2024 federal indictment.
- 约束 (Constraints): Only compressed, published-resolution figures available; no original scans; authors offered "scanner artifact" as the innocent explanation for repeated backgrounds.
- 检测步骤 (Detection Steps): (1) Eyes-only blot scan flagged oversaturated bands with little background detail, irregular spacing, and bands "remarkably similar." (2) Compared background pixel patterns across panels — more similar than independent experiments should produce (Category I/III). (3) Counted lanes vs conditions: a blot with only 12 bands where 13 conditions/lanes were shown elsewhere; splice after lane 8 vs lane 10 across co-run blots. (4) Identified rectangular boxes / white halos around individual bands (Fig 3B; Fig 3A pT231Tau) indicating bands inserted from another blot. (5) Explicitly noted that original high-res scans would resolve, and ruled the repeats out as scanner artifact (background reuse is panel-specific, not a uniform scanner pattern).
- 结果 (Outcome): Expressions of concern, retractions of Cassava-linked studies, and a 2024 criminal indictment of Wang for defrauding NIH (~$16M).
- 可提取的操作 (Extractable Operation): On Western blots, cross-check (a) lane count vs number of conditions, (b) splice positions across blots claimed to be co-run, (c) boxes/halos/floating bands signaling paste-in, and (d) background-region similarity across panels; document each with lane-level locators and rule out reprobe/loading-control/scanner explanations.

### Case 2: PubPeer-style image-duplication report (overlay-confirmed repositioning) following PubPeer's evidence rules
- 情境 (Situation): A reviewer suspects two microscopy panels in a paper, presented as different experimental conditions, share a region of overlap.
- 约束 (Constraints): Published PDF only; must produce a comment that survives PubPeer moderation and a legal-defensibility bar; must not be mistaken for a compression artifact.
- 检测步骤 (Detection Steps): (1) Identify candidate panels and the suspected overlapping region (Category II). (2) Crop the suspected region from each panel; apply the hypothesized transformation (shift/rotate/flip) to one and overlay it on the other. (3) Confirm that both signal AND background features co-register, not just one band. (4) Rule out innocent explanations: not the same declared replicate, not a shared loading control, and not a JPEG block (the matching feature is not a fixed 8x8/16x16 grid and persists at multiple contrast levels). (5) Write the comment: name figures/panels, state the comparison, include the overlay image, label the Bik category, keep wording neutral ("regions appear to overlap / be more similar than expected").
- 结果 (Outcome): A comment that is reproducible (a third party repeats the crop+overlay and sees the same alignment), is accepted by moderation, and can trigger journal/editor action.
- 可提取的操作 (Extractable Operation): The canonical reproducible-annotation recipe — locator + comparison object + transformation + overlaid result + category + innocent-explanation exclusions + neutral language; "perform the transformation and include the result" is the difference between a finding and a guess.

## Evidence Sources (source_id, URL, type, confidence)

- S1, https://scienceintegritydigest.com/2019/11/23/scanning-for-duplications/ , practitioner blog (Bik), high — Bik's own scan order, "don't read text," 1–15 min/paper, image-type priorities.
- S2, https://journals.asm.org/doi/10.1128/mbio.00809-16 , peer-reviewed (Bik mBio 2016), high — Category I/II/III duplication taxonomy.
- S3, https://www.pubpeer.com/static/faq , primary platform guidance, high (retrieved via search snippet; direct fetch 403) — perform-transformation-yourself rule, compression-artifact rejection, reprobe/loading-control innocent explanations, legal-defensibility standard.
- S4, https://www.editage.com/insights/identifying-problematic-images-tips-and-resources-for-peer-reviewers , publisher-services guide, medium-high — image red-flag checklist (edges, backgrounds, halos), tools (ImageJ, Forensically, Adobe Bridge).
- S5, https://www.csescienceeditor.org/article/the-stm-integrity-hub/ , industry/society article, high — ~20 independent signals: duplicate submission, references, tortured phrases, metadata, AI-content, submission patterns.
- S6, https://www.editage.com/insights/paper-mills-and-the-erosion-of-research-credibility-researchers-beware , publisher-services guide, medium-high — affiliation/email/ORCID first-screen red flags, irrelevant recurring references.
- S7, https://scienceintegritydigest.com/2021/08/27/cassava-sciences-of-stocks-and-blots/ , practitioner blog (Bik), high — Case 1 specifics (lane counts, splice positions, boxed bands, background similarity).
- S8, https://www.enago.com/academy/grim-and-sprite-simple-tools-to-identify-errors-in-research/ , explainer, medium — GRIM/SPRITE mechanics.
- S9, https://pmc.ncbi.nlm.nih.gov/articles/PMC12722777/ , peer-reviewed/PMC, medium-high — multi-tool stats+image workflow with mandatory human confirmation.
- S10, https://www.alzforum.org/news/community-news/data-fabrication-ousted-nia-neuroscience-director-eliezer-masliah , news, high — Masliah image-duplication findings corroborate elite-lab fabrication (used to justify "don't exonerate on clean metadata").
- S11, https://www.stm-assoc.org/papermillchecker/ , industry, medium — STM Papermill checker MVP; tool-as-accelerator framing.

## Supported Candidate Operations

- OP-ORDER: Run checks cheapest/fastest-signal-first: metadata+affiliation -> tortured-phrase/reference text scan -> image forensics -> stats reconstruction -> raw-data availability -> references -> existing PubPeer/EoC record (with PubPeer/RW lookup done early in parallel). (S1, S5, S6.)
- OP-IMAGE-NOTEXT: First image pass is eyes-only, ignore the text, prioritize photographic panels (blots, gels, microscopy, FACS). (S1.)
- OP-CATEGORY-LABEL: Classify every duplication as Bik Category I/II/III in the annotation. (S2.)
- OP-OVERLAY: To assert a transformation, perform it (flip/rotate/overlay/contrast) and include the resulting aligned image. (S3.)
- OP-INNOCENT-FIRST: Before recording/posting, rule out reprobe, shared loading control, declared replicate, and JPEG compression block. (S3.)
- OP-ANNOTATION-FIELDS: Record locator + comparison object + transformation + result + category + innocent-exclusions + neutral wording. (S3, S7.)
- OP-LANE-COUNT: On blots, cross-check lane count vs number of conditions and splice positions across co-run blots. (S7.)
- OP-STATS-RECOMPUTE: Recompute p-values (statcheck), test means against n (GRIM), reconstruct distributions (SPRITE). (S8, S9.)
- OP-REQUEST-ORIGINALS: Treat absence of high-resolution originals/source data as a signal and the resolution step. (S7.)
- OP-HUMAN-CONFIRM: Every machine-tool flag must be confirmed against the original image/data before becoming a stated finding. (S9.)

## Rejected or Weak Candidate Operations

- REJECT-COMPRESSION-AS-DUP: Flagging JPEG compression blocks (regular grids appearing at high contrast) as copy-paste — PubPeer rejects these; they are not evidence of manipulation. (S3.)
- REJECT-INTENT-LANGUAGE: Asserting "fraud"/"fabrication"/intent in the annotation — non-defensible, non-reproducible, gets comments rejected; describe observation only. (S3.)
- WEAK-METADATA-EXONERATION: Concluding a paper is clean because affiliations/emails check out — elite-lab fabrication (Masliah) shows metadata cleanliness lowers but does not zero the prior. (S10.)
- WEAK-TOOL-ONLY: Treating an ImageTwin/Proofig/statcheck flag as a finding without human confirmation against originals — high false-positive risk, not reproducible as stated. (S9.)
- WEAK-SINGLE-BAND-OVERLAY: Claiming duplication from one matching band without confirming background co-registration — single bands can coincidentally resemble; require region+background alignment. (S7.)

## Domain-specific Patterns

- Biomedical fabrication concentrates in photographic panels: Western blots, gels, microscopy, flow/FACS — these are the high-yield targets, not the text. (S1, S2.)
- Western-blot tells: oversaturated bands with no background, irregular spacing, boxed/haloed/"floating" bands, lane count ≠ condition count, inconsistent splice positions across co-run blots, background pixel reuse across panels. (S7.)
- Paper-mill tells cluster in metadata/text: mismatched email domains, fresh-per-submission ORCIDs, tortured phrases, irrelevant/recurring references, compromised special issues. (S5, S6.)
- The two failure modes are different populations: paper mills (caught in steps 1–2) vs individual-lab fabrication (caught in steps 3–4). The pipeline must run both halves regardless of which signal fired first.

## Boundaries and Uncertainties

- PubPeer FAQ direct fetch returned 403; FAQ content captured via multiple search-snippet retrievals and corroborating secondary sources (S3 plus Penn Libraries guide, journalistsresource). Wording is faithful but verify against the live FAQ before quoting verbatim in the skill.
- Exact pixel-coordinate annotation is illustrative: real screeners more often annotate by lane/band/visual region than by literal pixel boxes, because published-image resolution and DPI vary; coordinates should be stated "at published resolution" and paired with a visual crop.
- The cheapest-first ordering is a strong consensus heuristic, not a rigid law: for stats-heavy/clinical or psychology papers, statistics reconstruction (step 4) should move ahead of image forensics. The skill should expose the ordering principle (cheapest/fastest signal first) rather than hard-coding the sequence.
- STM Integrity Hub internal check list and order are partly proprietary; the ~20-signal categories are public but the precise per-signal sequence is not. Treat as illustrative of "publishers also do cheap-first, multi-signal" rather than a canonical order.

## Recommendations for Later Skill Compilation

- Encode the pipeline as an ordered checklist with an explicit per-step STOP/CONTINUE/DISCARD rule and an explicit "swap 3 and 4 for stats-heavy papers" branch. State the ordering *principle* (highest signal-probability x speed per unit effort/skill) so the order is defensible, not arbitrary.
- Make the Reproducible Annotation Format a hard template with the 7 required fields; ship the GOOD vs BAD example pair verbatim as a few-shot.
- Bake in the three mandatory gates before any finding is recorded: (1) innocent-explanation excluded, (2) transformation performed and result attached, (3) human-confirmed if a tool produced it.
- Keep tools as named accelerators mapped to stations (text: tortured-phrase/Papermill Alarm; image: ImageTwin/Proofig/Forensically/ImageJ; stats: statcheck/GRIM/SPRITE) but require the underlying manual check to be describable without the tool, so the skill is tool-agnostic and survives tool deprecation.
- Carry the Bik I/II/III taxonomy as the controlled vocabulary for image findings.

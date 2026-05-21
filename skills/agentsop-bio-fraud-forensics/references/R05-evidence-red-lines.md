Status: pass

# R05 — Evidence Strength and Red Lines (Ethical Core)

This dimension exists to stop the skill from becoming a defamation engine. The
governing principle, drawn from the field's most experienced sleuths and from
two landmark court rulings (Sarkar v. Doe, Gino v. Data Colada): **you may
report and interpret what is observable from disclosed evidence; you may NOT
assert intent, fraud, or guilt as fact.** Stating "these two panels are
identical" is protected and defensible. Stating "the authors committed fraud"
is an actionable conclusion the screener is not entitled to make.

## Key Findings

- **The whole field already enforces a graded-language norm.** PubPeer's own
  rule (echoed by Elisabeth Bik): you may say "two images look very similar to
  each other" but you may NOT say "the authors committed fraud." Statements must
  "stick to facts and be publicly verifiable." This is not politeness — it is
  the line between protected speech and libel.
- **The law rewards the disclosed-facts-plus-interpretation structure.** In Gino
  v. Data Colada (dismissed Sept 11, 2024), the court held the fraud allegations
  were protected opinion *because* the sleuths "outlined the facts available...
  making it clear that the challenged statements represent his own
  interpretation of those facts and leaving the reader free to draw his own
  conclusions." They used hedges ("suggests to us that these... may have been
  altered," "we believe") and acknowledged "the possibility of conclusions
  besides tampering." That hedging + disclosure is the legal armor. A skill that
  outputs bare verdicts strips that armor away.
- **Intent is out of scope for any image/data screener.** Bik's repeated stance:
  she reports observable anomalies (duplications, overlaps) and refers them to
  journals/institutions; she "doesn't want to falsely accuse anybody" and
  recognizes that proving intent to deceive lies *beyond* image analysis. The
  screener can flag the anomaly; only an institutional investigation can
  adjudicate misconduct.
- **Most anomalies are NOT fraud.** AACR's Proofig screen of 1,367 papers
  (2021–2022): 207 needed author contact, but in 204 cases the issue was an
  honest mistake; only 4 papers were withdrawn. A skill that escalates every
  duplication to "misconduct" would be wrong ~98% of the time on flagged items.
- **A benign-explanation pass is mandatory before any flag escalates.**
  Legitimate splicing (disclosed), JPEG/compression artifacts, loading-control
  reuse from the same experiment, microscopy tiling overlap, and PowerPoint
  figure-assembly mix-ups all mimic fraud. Forensic tools themselves produce
  false positives from JPEG blocking artifacts.
- **PubPeer-with-evidence is defensible; public naming-and-shaming is the
  danger zone.** Sarkar v. Doe established that opinion based on disclosed facts
  cannot be defamatory and anonymous posters cannot be unmasked for it — BUT the
  one comment the trial court initially treated differently was one that read as
  a bare factual assertion rather than disclosed-fact-based opinion. The format
  of the statement, not just its content, determines legal exposure.

## Graded-Language Tier Model

| Tier | When to use | Required evidence to be AT this tier | Phrasing pattern (templates) |
|------|-------------|--------------------------------------|------------------------------|
| **Tier 1 — Observed Anomaly** | A visual/statistical feature is present and reproducible from the published figure/data. Default tier for nearly all automated screen output. | The observation is publicly verifiable from the paper itself (region coordinates, panel IDs, the duplicated region marked). Nothing about intent. | "Figure 3B and Figure 5A appear to share an identical region (boxed)." / "The bands in lane 2 and lane 4 show the same pixel pattern." / "Panel X overlaps panel Y by ~N%." Use *appears / shows / is consistent with*. NEVER use *fabricated / faked / fraudulent*. |
| **Tier 2 — Question Needing Author Clarification** | The anomaly is real AND benign explanations (see checklist) do not obviously account for it, so an explanation is warranted before any judgment. | Tier-1 evidence PLUS a documented check that common innocent causes were considered and don't fully fit. Phrased as an open question, not a charge. | "Could the authors clarify whether these panels derive from the same experiment / whether splicing was performed and disclosed?" / "It is unclear how the same image represents two different conditions; clarification would help." Hedge: *suggests to us that... may have been... we believe... it is possible that...* (the Data Colada formula). |
| **Tier 3 — Adjudicated Misconduct** | An authoritative body has ruled. The screener NEVER originates this tier. | A formal finding by a journal (retraction notice citing manipulation), an institution (ORI/research-integrity office determination), or a court. A citation to that ruling is required. | "Paper retracted by [journal] on [date]; the retraction notice cites image manipulation." / "[Institution] found research misconduct (ref/date)." Only here may words like *misconduct / fabrication* be stated as fact — and only by quoting the adjudicator. |

**Escalation rules the skill MUST enforce:**
- Default output is Tier 1. The screener cannot self-promote a finding to Tier 3.
- Tier 1 → Tier 2 requires passing the Benign-Explanation Checklist (failing to
  find an innocent fit), never just "looks suspicious."
- Tier 2 → Tier 3 requires an external adjudication citation. There is no
  internal evidence threshold that lets the tool declare misconduct itself.
- Words banned from Tier 1/2 output: fraud, fraudulent, fabricated, faked,
  falsified, doctored, misconduct, lied, cheated, guilty. Allowed verbs:
  appears, shows, is consistent with, is identical to, overlaps, cannot be
  explained by, warrants clarification.

## Benign-Explanation Checklist

| Looks like (apparent anomaly) | Could actually be (benign cause) | How to distinguish before escalating |
|-------------------------------|----------------------------------|--------------------------------------|
| Sharp vertical discontinuity / seam in a gel or blot | **Legitimate lane splicing**, allowed when disclosed | Check Methods/figure legend for a splicing statement; look for an inserted dividing line/white gap between lanes (the disclosed convention). Disclosed + marked = not a flag. Undisclosed seam mid-lane = Tier 2 question. |
| Blocky edges, halos, or "copy-move"-looking texture | **JPEG / compression artifacts**; forensic detectors themselves false-positive on JPEG blocking | Re-examine at native resolution; artifacts follow the regular 8×8 JPEG grid and appear globally, not just on the suspicious region. Don't flag features that track the compression grid. |
| Identical loading-control band reused across panels | **Loading-control reuse from the same experiment/same gel** — explicitly NOT a problem per Bik's mBio study | Ask: are the panels from one experiment where one control legitimately applies? Same-experiment control reuse is acceptable; reuse across *unrelated* experiments is the actual concern. |
| Same image in two papers | **Duplicate publication / legitimate self-reuse** (e.g., a methods figure, a review reusing the authors' own cited figure) vs. image duplication misconduct | Check for citation/attribution and whether reuse is disclosed; a properly cited reused figure is a different (lesser) issue than passing the same data off as new results. |
| Two microscopy fields partially overlap | **Tiling/stage-movement overlap** — microscope doesn't warn when fields overlap during slide navigation (AACR/Proofig finding) | Partial edge overlap consistent with adjacent fields is plausible-innocent; exact full-panel duplication presented as distinct conditions is not. |
| Same panel appears twice in a figure | **Honest figure-assembly error** (wrong file dragged in PowerPoint, mislabeling) — the dominant cause in the AACR data (204/207) | Simple, un-transformed duplicates are the classic honest-error signature and usually resolved by correction. Flag as Tier-2 question, never Tier-3. |
| Panel rotated / flipped / stretched / shifted to overlap another | **Less likely benign** — these transformations rarely happen by accident | This pattern legitimately raises a Tier-2 clarification question (Bik: repositioned/altered duplications are "clearly a manipulation of the data"). Still phrased as a question, not a verdict. |
| Numbers/values look "too clean" or transcription mismatch | **Honest transcription error**, rounding, or template/figure reuse from a journal style file | Check whether the discrepancy is internally correctable and whether a journal template explains repeated layout elements. |
| Repeated layout/figure elements across many papers | **Journal template or shared figure-style reuse** | Confirm whether the repeated element is data (concerning) or boilerplate/template chrome (not concerning). |

## Detection Cases (>=2 required)

### Case 1: Gino v. Data Colada — how disclosed-facts-plus-interpretation survived a defamation suit
- **情境 (Situation):** Behavioral scientists at the Data Colada blog publicly
  documented apparent data anomalies in papers by Harvard Business School
  professor Francesca Gino. Harvard investigated, placed her on unpaid leave;
  Gino sued Harvard and the three bloggers for defamation (Aug 2023).
- **约束 (Constraints):** Public, named, high-stakes accusation of *fraud*
  against a named senior scientist — exactly the scenario that gets sleuths
  sued. The bloggers had no institutional adjudication behind them at the time
  of posting; they were the originators of the claim.
- **检测步骤/判断步骤 (Steps):** The bloggers (1) posted the underlying data and
  screenshots and hyperlinks to primary documents so readers could verify
  independently; (2) framed conclusions with hedges — "suggests to us that these
  eight observations *may* have been altered," "we *believe*"; (3) explicitly
  acknowledged "limitations of its work and the possibility of conclusions
  besides tampering by Professor Gino herself."
- **结果 (Outcome):** Sept 11, 2024 — Judge Joun dismissed all defamation counts
  against Data Colada, holding the fraud allegations were protected opinion: "an
  opinion is not actionable if it merely draws a conclusion from disclosed
  non-defamatory facts," and a statement is protected where the speaker outlines
  the facts and "leav[es] the reader free to draw his own conclusions." The
  judge called the defamation case "weak indeed."
- **可提取的操作 (Extractable Operation):** Mandate the Data Colada formula for
  any Tier-2 output: (a) show the evidence/coordinates, (b) state interpretation
  with explicit hedges, (c) acknowledge alternative innocent explanations. This
  is both the ethical and the legal safe harbor — bake it into the template.

### Case 2: Sarkar v. Doe — when an anonymous flag is protected, and the one comment that wasn't
- **情境 (Situation):** Anonymous PubPeer commenters flagged apparent image
  manipulation across many papers by cancer researcher Fazlul Sarkar (Wayne
  State). The University of Mississippi rescinded a tenured job offer; Sarkar
  sued the anonymous "Does" and subpoenaed PubPeer to unmask them (2014).
- **约束 (Constraints):** Anonymous accusers; real, severe career harm to the
  target; the question of whether posting comes with legal accountability. (Note
  the eventual coda: Wayne State's own investigation later found misconduct and
  ~18 papers were retracted — but that adjudication came *after* and is
  independent of the comments' protected status.)
- **检测步骤/判断步骤 (Steps):** Courts examined each comment's *form*. Comments
  that expressed an opinion on the basis of disclosed facts (here is the image,
  here is what it shows) were held non-actionable. The trial court treated
  differently a comment that read as a bald factual assertion rather than
  disclosed-fact-based opinion.
- **结果 (Outcome):** The Michigan Court of Appeals (Dec 2016), with ACLU
  representation, ruled that "expressing an opinion on the basis of disclosed
  facts cannot be defamatory as a matter of law," and PubPeer did not have to
  unmask its commenters. The protection turned on the disclosed-facts structure.
- **可提取的操作 (Extractable Operation):** Form matters as much as content. The
  skill must never emit a bare factual assertion of wrongdoing; every concern
  must carry its disclosed evidence inline. A naked "this is fabricated" is the
  legally exposed shape; "here is the region, it appears identical to X" is the
  protected shape. Also: an external misconduct finding (Wayne State's) is what
  unlocks Tier-3 language — the comments themselves never claimed that tier.

## Evidence Sources (source_id, URL, type, confidence)

- S1 — https://scienceintegritydigest.com/2019/07/16/pubpeer-a-website-to-comment-on-scientific-papers/ — Bik's own blog explaining PubPeer norms ("similar" yes / "fraud" no) — high
- S2 — https://www.pubpeer.com/static/faq — PubPeer official commenting/moderation rules (facts, publicly verifiable, no fraud accusations) — high (content confirmed via secondary quotes; direct fetch 403)
- S3 — https://reason.com/volokh/2024/09/11/prof-francesca-ginos-libel-claims-against-harvard-business-school-and-data-colada-dismissed/ — Volokh/Reason legal analysis of the Gino dismissal incl. quoted opinion-doctrine reasoning — high
- S4 — https://www.science.org/content/article/honesty-researcher-s-lawsuit-against-data-sleuths-dismissed — Science news on Gino suit dismissal — high (headline/summary; full text paywalled/403)
- S5 — https://www.thecrimson.com/article/2024/9/12/judge-dismisses-gino-lawsuit-defamation-charges/ — Harvard Crimson detail on Judge Joun's ruling (First Amendment, actual malice, partial denial for Harvard) — high
- S6 — https://www.aclu.org/cases/sarkar-v-doe-pubpeer-subpoena-challenge — ACLU case page, Sarkar v. Doe — high
- S7 — https://www.nachtlaw.com/blog/2016/12/court-of-appeals-decides-internet-anonymity-case/ — Michigan COA ruling: opinion on disclosed facts not defamatory — high
- S8 — https://publicationethics.org/guidance/flowchart/inappropriate-image-manipulation-published-article — COPE flowchart: contact author → ask institution to investigate → expression of concern during investigation → correction vs retraction by effect on conclusions — high (content confirmed via COPE secondary pages; direct fetch 403)
- S9 — https://scholarlykitchen.sspnet.org/2024/04/23/guest-post-the-future-of-image-integrity-in-scientific-research/ — AACR/Proofig numbers (1,367 screened; 207 contacted; 204 honest mistakes; 4 withdrawn); microscopy tiling overlap as benign cause — high
- S10 — https://pmc.ncbi.nlm.nih.gov/articles/PMC4941872/ — Bik et al. mBio prevalence study; loading-control same-experiment reuse not a problem; simple vs repositioned/altered duplication likelihood — high
- S11 — https://thepublicationplan.com/2022/11/29/spotting-fake-images-in-scientific-research-insights-from-science-integrity-consultant-elisabeth-bik/ — Bik's duplication categories and "half deliberate" estimate, report-to-journals stance — high
- S12 — https://www.statnews.com/2024/02/28/elisabeth-bik-scientific-integrity-research-misconduct/ — Bik: "don't want to falsely accuse anybody," needs "real proof," intent beyond image analysis — high
- S13 — https://pmc.ncbi.nlm.nih.gov/articles/PMC11573918/ (Cell Patterns) — image-splicing detection; splicing legitimate when declared; honest lab artifacts confused with splicing — medium-high
- S14 — https://arxiv.org/pdf/2108.12947 / https://arxiv.org/pdf/2412.03261 — JPEG compression artifacts cause forensic false positives — medium-high
- S15 — https://pmc.ncbi.nlm.nih.gov/articles/PMC4430488/ — PLOS ONE study: exoneration largely restores credibility (relevant to reputational stakes of premature accusation) — medium

## Supported Candidate Operations

- **OP-1 (Boundary Rule):** Default every screener finding to Tier 1 "observed
  anomaly" language. The tool may never originate Tier 3. [S1, S2, S12]
- **OP-2 (Boundary Rule):** Enforce a banned-word list (fraud, fabricated,
  faked, falsified, doctored, misconduct, etc.) in all Tier-1/2 output; allow
  them only inside a quoted Tier-3 adjudication. [S1, S2]
- **OP-3 (Template):** Require the Data Colada three-part structure for any
  Tier-2 escalation — (a) disclosed evidence/coordinates, (b) hedged
  interpretation, (c) named alternative innocent explanation. [S3, S5]
- **OP-4 (Gate):** Before Tier 1 → Tier 2, run the Benign-Explanation Checklist
  and record which innocent causes were excluded and why. No escalation without
  this. [S9, S10, S13, S14]
- **OP-5 (Process):** Recommend the COPE order — contact authors for
  clarification first; route to journal/institution for adjudication; treat
  honest error as correctable, not misconduct. The tool advises, it does not
  adjudicate. [S8, S9]
- **OP-6 (Channel rule):** Prefer evidence-bearing channels (private report to
  editor/PubPeer-style comment with disclosed facts) over public naming. [S6, S7]
- **OP-7 (Calibration):** Surface the base rate — most flagged anomalies are
  honest errors (Proofig ~204/207) — so users do not over-read a flag. [S9]

## Rejected or Weak Candidate Operations

- **REJECTED — "Confidence score that the authors are guilty / committed
  fraud."** Conflates a visual-similarity metric with intent. Intent is
  unknowable from images (Bik, S12) and asserting it is precisely the
  defamation trigger. A pixel-match confidence is fine; a "guilt probability" is
  not.
- **REJECTED — Auto-generated public accusation / social posts.** Public naming
  without adjudication is the highest-liability action and the documented
  failure mode; the tool should never auto-publish accusations. [S3, S6]
- **REJECTED — Treating any duplication as misconduct.** Contradicted by the
  AACR data and by loading-control/tiling/figure-assembly benign causes. [S9, S10]
- **WEAK — Relying on a single forensic detector's manipulation call.** JPEG
  artifacts and low-res rendering produce false positives; detector output is
  Tier-1 evidence to be checked, not a verdict. [S13, S14]
- **WEAK — "Naming the most likely manipulating author."** Authorship of an
  anomaly ≠ culpable individual; assigning blame to a specific person is an
  adjudicative act outside the tool's competence and a defamation risk.

## Boundaries and Uncertainties

- The skill is a *screening/triage* aid, not an adjudicator. It can reach Tier 2
  at most on its own authority. Tier 3 is import-only (cite the body that ruled).
- Legal protection (Gino, Sarkar) is U.S. First Amendment / opinion-doctrine
  based. Other jurisdictions (UK, EU) have less speech-protective and stricter
  libel regimes; the disclosed-facts-plus-hedge discipline is still the safest
  posture but is not a guaranteed shield abroad. Flag this to users.
- The disclosed-facts protection requires that the disclosed facts themselves be
  accurate. If the tool's underlying observation is wrong (e.g., a JPEG-artifact
  false positive presented as "identical region"), the protection weakens and
  the harm to the target is real. Accuracy of the Tier-1 observation is therefore
  itself an ethical obligation, not just a technical one.
- Anonymity (PubPeer) is protected for opinion-on-disclosed-facts but does not
  immunize a bald false factual assertion; form still matters.
- COPE/PubPeer pages returned 403 to direct fetch; their content here is
  corroborated through multiple secondary quotations and official COPE secondary
  pages — confidence remains high but verbatim flowchart wording was not captured.

## Recommendations for Later Skill Compilation

**These MUST become Boundary Rules (non-negotiable, hard-coded in the skill):**

1. **Three-tier output is mandatory and the default is Tier 1.** The skill
   physically cannot emit "fraud/fabrication/misconduct" as its own assertion;
   those words only appear when quoting an external adjudication (Tier 3 with a
   citation). Wire a banned-word filter on Tier-1/2 output.
2. **No intent claims, ever.** The tool reports and interprets observable
   features; it never states or scores that an author *intended* to deceive or
   is *guilty*. (Bik: intent is beyond image analysis.)
3. **Every Tier-2 concern must carry its disclosed evidence inline plus a hedge
   plus a named alternative explanation** — the Gino/Data Colada formula. This
   is both the ethics and the documented legal safe harbor.
4. **Mandatory benign-explanation pass before any escalation.** Ship the
   checklist in this doc as a gate; the skill must record which innocent causes
   were excluded. No "looks suspicious → flag."
5. **Follow the COPE order: clarify with authors / route to editor or institution;
   the tool advises, it does not adjudicate or publish accusations.** Default to
   evidence-bearing private channels over public naming.
6. **Surface the base rate and an explicit disclaimer** ("most flagged anomalies
   are honest errors; this is a question for the authors, not a finding of
   misconduct") on every report, so the output cannot be mistaken for a verdict.
7. **Include a jurisdiction caveat:** the opinion-doctrine protection is
   strongest under U.S. law; users elsewhere face stricter libel exposure.

The single sentence that should headline the skill's ethics section: *Report
what you can see from the evidence in front of you, interpret it with explicit
hedges and alternatives, and let an authorized body decide intent — never accuse.*

# Persona OS Domain Pack

Purpose:
Extract a person's operating system — how they make decisions, process failure,
handle disagreement, update beliefs, and allocate attention. Used as a
cross-cutting layer when `skill_mode: "persona"`.

This pack is layered ON TOP of the primary domain pack. Read both. The primary
domain pack tells you WHAT the person works on; this pack tells you HOW they
operate.

Common sources:
transcript_interview, longform_text, secondary_criticism, video_subtitle,
social_media, audio_podcast.

Candidate operation families:
decide_under_pressure, recover_from_failure, resolve_value_conflict,
handle_disagreement, update_beliefs, allocate_attention, communicate_decision,
build_team, navigate_power, maintain_consistency.

Validation focus:
Every operation must be traceable to a specific verifiable incident, not just
a quote. The person saying "I believe in X" is low confidence. The person
choosing X when it cost them Y is high confidence.

Research dimensions (for subagent planning — source modality × evidence depth):

- **decision_under_constraint**: How they make choices when resources (time,
  money, people, reputation) are tight. What is their tiebreaker? Do they
  optimize for speed, quality, principle, or survival? Look for moments where
  they had to choose between two goods or two evils.
  *Revealed by:* interviews about crisis moments, biographies, post-mortem
  analyses, their own retrospective accounts.

- **failure_processing**: How they metabolize failure. Do they reframe it as
  learning? Externalize blame? Extract specific rules? Change behavior
  measurably? The most important signal: compare their rhetoric BEFORE and
  AFTER a major failure. Did they actually change what they do, or just
  how they talk about it?
  *Revealed by:* long-timespan interviews (pre- and post-failure), secondary
  analysis tracking their actions over time, their own post-mortem accounts.

- **value_conflict_resolution**: When two stated values collide, which wins?
  Everyone says they value both "quality" and "speed." When forced to trade
  one for the other, which do they actually sacrifice? This reveals their
  true value hierarchy, not their stated one.
  *Revealed by:* product decisions, hiring/firing choices, deal negotiations,
  public controversies where they had to pick a side.

- **attention_allocation**: What do they pay attention to and what do they
  deliberately ignore? How do they decide what NOT to do? This is often more
  revealing than what they DO — ignored opportunities are invisible in
  retrospect but define their trajectory.
  *Revealed by:* interviews where they discuss what they said no to, product
  roadmaps showing features they killed, strategic pivots where they abandoned
  a direction.

- **influence_and_disagreement**: How they handle being challenged. Persuade
  with logic? Override with authority? Delegate and step back? Avoid the
  conflict? Their response to disagreement reveals their theory of how truth
  is reached — through debate, through authority, through data, through
  intuition?
  *Revealed by:* meeting accounts, co-founder dynamics, public debates,
  their own descriptions of internal disagreements.

- **learning_and_updating**: How they change their mind. What kind of evidence
  makes them update? A personal experience? Data? Someone they trust telling
  them? Public pressure? How long does it take? The most valuable extraction:
  identify a belief they once held strongly and later reversed. What caused
  the reversal?
  *Revealed by:* before/after comparisons on specific topics, interviews
  where they say "I used to think X, but now I think Y," actions that
  contradict their earlier stated positions.

- **identity_and_narrative**: What story do they tell about themselves? How
  does this narrative constrain or enable their actions? The "I'm the kind of
  person who..." frame is often the deepest OS layer — it determines which
  options even appear on their menu.
  *Revealed by:* autobiographical accounts, brand/personal mythology, how
  they introduce themselves, the metaphors they use to describe their role.

Cross-domain bridges (how persona dimensions interact with primary domains):
- software-engineering: decision_under_constraint maps to architectural
  tradeoffs; attention_allocation maps to feature prioritization
- office-white-collar: influence_and_disagreement maps to organizational
  politics; value_conflict_resolution maps to stakeholder tradeoffs
- media-content-production: identity_and_narrative maps to personal brand
  construction; learning_and_updating maps to content iteration
- finance: decision_under_constraint maps to risk management; failure_processing
  maps to loss recovery
- Any domain: persona dimensions are domain-agnostic. The primary domain
  provides the SCENARIOS; persona-os provides the EXTRACTION LENS.

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source reveals an unusual relationship with time (extreme patience or
  impulsivity) → derive `temporal_orientation` dimension
- source reveals a distinctive relationship with money (unusual frugality or
  spend patterns) → derive `resource_philosophy` dimension
- source reveals a mentorship or apprenticeship pattern → derive
  `knowledge_transfer` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission =
  "extract how <target> performs <operation>"

---
name: audit
description: >
  Run a comprehensive SEO audit on a website covering technical health, on-page
  optimization, content quality, and backlink profile. Use when the user asks for
  an SEO audit, site review, SEO health check, "what's wrong with my SEO",
  website analysis, or a full diagnostic of their site's search performance.
  For speed-specific issues, see audit-speed. For technical crawl/index issues
  only, see diagnose-seo.
metadata:
  version: 1.0.0
---

# SEO Audit

Run a comprehensive SEO audit covering technical foundations, on-page
optimization, content quality, link profile, and competitive positioning.

## Before You Start

Gather this context (ask if not provided):

1. **Domain.** What site are we auditing?
2. **Goals.** What are you trying to achieve? (More traffic, better rankings, fix a drop, pre-launch check)
3. **Known issues.** Anything you already suspect is wrong?
4. **Access.** Do you have Google Search Console and Google Analytics data? (Improves the audit significantly)
5. **Scope.** Full audit or focused on a specific area? (If unsure, run the full audit)

## Audit Framework

A complete SEO audit covers five layers. Work through them in order — problems
in earlier layers undermine everything that follows.

```
Layer 1: Technical Foundation     ← Can Google crawl and index the site?
Layer 2: On-Page Optimization     ← Are pages optimized for target keywords?
Layer 3: Content Quality          ← Is the content worth ranking?
Layer 4: Link Profile             ← Does the site have authority?
Layer 5: Competitive Position     ← How does the site compare to competitors?
```

## Layer 1: Technical Foundation

Check whether search engines can properly access, crawl, render, and index the site.

### Crawlability
- [ ] `robots.txt` — fetch and review. No critical paths blocked? Sitemap directive present?
- [ ] XML sitemap — exists, valid XML, lists all important pages, excludes noindex/redirected pages?
- [ ] Site architecture — important pages reachable within 3 clicks from homepage?
- [ ] Orphan pages — any pages with zero internal links pointing to them?
- [ ] Redirect chains — any paths with 2+ redirects in sequence?
- [ ] HTTP status — all important pages return 200? No unexpected 301s, 404s, or soft 404s?

### Indexability
- [ ] `noindex` tags — any important pages accidentally noindexed?
- [ ] Canonical tags — self-referencing on all pages? No conflicting canonicals?
- [ ] Duplicate content — same content accessible at multiple URLs (www/non-www, HTTP/HTTPS, trailing slash)?
- [ ] Search Console index coverage — how many pages submitted vs indexed? Any excluded pages that should be indexed?

### Performance
- [ ] Core Web Vitals — LCP < 2.5s, CLS < 0.1, INP < 200ms?
- [ ] TTFB — < 800ms from major regions?
- [ ] Mobile-friendly — passes Google's mobile usability tests?
- [ ] HTTPS — enforced across the entire site? Valid certificate?

### Rendering
- [ ] JavaScript-dependent content — is critical content in the initial HTML or loaded via JS?
- [ ] Content visibility — can search engines see the full page content?

## Layer 2: On-Page Optimization

Check whether individual pages are properly optimized for their target keywords.

### Title Tags
- [ ] Every page has a unique `<title>`
- [ ] Titles include the primary target keyword
- [ ] Titles are under 60 characters (avoid truncation)
- [ ] Titles are descriptive and click-worthy (not keyword-stuffed)

### Meta Descriptions
- [ ] Every important page has a unique meta description
- [ ] Descriptions are 150-160 characters
- [ ] Descriptions include a value proposition and call to action

### Heading Structure
- [ ] One H1 per page containing the primary keyword
- [ ] Logical heading hierarchy (H1 → H2 → H3, no level skipping)
- [ ] Headings describe section content accurately

### URL Structure
- [ ] URLs are clean, readable, and descriptive
- [ ] URLs use hyphens (not underscores)
- [ ] No excessive URL parameters or session IDs in indexed URLs
- [ ] Consistent URL structure across the site

### Internal Linking
- [ ] Important pages have sufficient incoming internal links (3+)
- [ ] Anchor text is descriptive and varied (not all "click here")
- [ ] Hub-and-spoke structure exists for topic clusters
- [ ] No broken internal links (404 targets)

### Image Optimization
- [ ] All images have descriptive `alt` attributes
- [ ] Images use modern formats (WebP/AVIF) where supported
- [ ] Images are appropriately sized (not serving 4000px images in 400px containers)
- [ ] Decorative images use empty `alt=""`

### Structured Data
- [ ] Relevant schema markup present (Article, Product, FAQ, LocalBusiness, BreadcrumbList, etc.)
- [ ] Schema validates without errors in Google's Rich Results Test
- [ ] Schema matches visible page content (no hidden/misleading markup)

### On-Page Scoring Rubric

For a detailed page-level audit, score each page across 8 sections:

| Section | Weight | What to Score |
|---------|--------|--------------|
| Title Tag | 15% | Keyword presence, in first half, 50-60 chars, unique, compelling, intent match |
| Meta Description | 5% | Keyword included, 150-160 chars, CTA present, unique |
| Header Structure | 10% | Single H1 with keyword, logical hierarchy (no skipped levels), H2s cover subtopics |
| Content Quality | 25% | Sufficient length, comprehensive, unique value, up-to-date, good formatting, E-E-A-T signals |
| Keyword Optimization | 15% | Keyword in title/H1/first 100 words/URL, density 0.5-2.5%, semantic terms present |
| Internal/External Links | 10% | Sufficient internal links, descriptive anchors, quality external links, no broken links |
| Image Optimization | 10% | Alt text on all images, descriptive filenames, optimized sizes, modern formats |
| Page-Level Technical | 10% | Clean URL, correct canonical, mobile-friendly, LCP ≤2.5s, HTTPS, schema present |

**Content Length Benchmarks** (for full score on "sufficient length"):

| Intent Type | Target Word Count |
|------------|------------------|
| Informational | 1,500+ words |
| Commercial investigation | 1,200+ words |
| Transactional | 500+ words |
| Local | 400+ words |

**Internal Link Count Guidelines:**

| Page Length | Target Internal Links |
|-----------|---------------------|
| <500 words | 2-4 links |
| 500-1,000 words | 3-6 links |
| 1,000-2,000 words | 5-10 links |
| 2,000+ words | 8-15 links |

**Keyword density penalties:** >3.0% = keyword stuffing (score 0); <0.5% = under-optimized.

**Score grade scale:**

| Score | Grade | Assessment |
|-------|-------|-----------|
| 90-100 | A+ | Exceptional — maintain |
| 80-89 | A | Strong — minor tweaks |
| 70-79 | B | Good — several areas need attention |
| 60-69 | C | Average — significant improvements needed |
| 50-59 | D | Below average — major issues |
| <50 | F | Poor — comprehensive overhaul required |

## Layer 3: Content Quality

Evaluate whether the content deserves to rank.

### E-E-A-T Assessment
- **Experience** — Does the content demonstrate first-hand experience with the topic?
- **Expertise** — Is the content written with subject-matter depth? Does it go beyond surface-level?
- **Authoritativeness** — Does the site have a reputation in this topic area? Are authors credible?
- **Trustworthiness** — Are claims sourced? Is the site transparent about who publishes it?

### Content Coverage
- [ ] Does each page have a clear target keyword and intent?
- [ ] Is the content comprehensive enough to fully satisfy the search query?
- [ ] Are there thin pages (< 300 words) that should be expanded or consolidated?
- [ ] Is content up to date? Any pages with stale data, broken examples, or outdated advice?

### Content Gaps
- [ ] What topics do competitors cover that this site doesn't?
- [ ] Are there keywords with search demand that no existing page targets?
- [ ] Are there topic clusters that are incomplete (pillar page but missing spokes, or vice versa)?

### Cannibalization
- [ ] Are multiple pages targeting the same keyword?
- [ ] If so, are they competing against each other in rankings?
- [ ] Resolution: consolidate, differentiate, or canonical the weaker page to the stronger one.

## Layer 4: Link Profile

Assess the site's backlink authority and quality.

### Backlink Overview
- Total referring domains
- Dofollow vs nofollow ratio
- Link acquisition trend (growing, stable, or declining?)
- Average authority of linking domains

### Link Quality
- [ ] Any high-spam-score referring domains that could trigger penalties?
- [ ] Are links contextual (in-content) or low-value (sidebar, footer, comment)?
- [ ] Anchor text distribution — natural diversity or suspicious over-optimization?

### Link Gaps
- [ ] Which competitor pages earn the most backlinks? What content type?
- [ ] Are there broken backlinks worth recovering? (404 pages that once had links)
- [ ] Are there linkable assets on the site that aren't being promoted?

## Layer 5: Competitive Position

Understand where the site stands relative to competitors.

### Keyword Overlap
- Which keywords do you share with competitors?
- Where are you winning vs losing?
- What keywords do competitors rank for that you don't?

### Content Comparison
- How does content depth and quality compare to top-ranking competitors?
- What formats are competitors using that you aren't (video, tools, templates)?
- What unique angles or data could differentiate your content?

### Authority Comparison
- How does your domain authority/rating compare?
- Do competitors have significantly more referring domains?
- Are there authority-building opportunities you're not pursuing?

## Scoring

After completing all layers, assign a health score:

| Layer | Weight | Score (1-10) | Weighted |
|-------|--------|-------------|----------|
| Technical Foundation | 25% | [score] | [weighted] |
| On-Page Optimization | 20% | [score] | [weighted] |
| Content Quality | 25% | [score] | [weighted] |
| Link Profile | 15% | [score] | [weighted] |
| Competitive Position | 15% | [score] | [weighted] |
| **Overall** | **100%** | | **[total]** |

**Scoring guide:**
- 8-10: Strong — maintain and optimize
- 5-7: Needs work — clear improvement opportunities
- 1-4: Critical — fundamental issues blocking performance

### Veto Conditions

These conditions **cap the overall score** regardless of how well other layers perform.
A single veto prevents a site from appearing healthy when it has a fatal flaw:

| Condition | Cap | Rationale |
|-----------|-----|-----------|
| `robots.txt` blocks all of Googlebot or blocks `/` | Overall capped at 1/10 | Nothing else matters if Google can't crawl |
| > 20% of important pages have `noindex` accidentally | Overall capped at 3/10 | Most of the site is invisible to search |
| All three Core Web Vitals are "Poor" | Technical capped at 3/10 | Google deprioritizes sites with terrible UX |
| Zero external backlinks (entire domain) | Link Profile capped at 2/10 | No external authority signal exists |
| Site serves HTTP without redirect to HTTPS | Technical capped at 4/10 | Google requires HTTPS for trust signals |
| Google manual action active | Overall capped at 2/10 | Penalty overrides all optimization |

Check veto conditions **before** scoring layers. If any veto fires, flag it prominently
in the executive summary and cap the relevant score.

## Output Format

### SEO Audit: [domain]

**Overall Health Score: [score]/10**

**Executive Summary**
3-5 sentences covering: the site's biggest strength, the most critical issue,
and the highest-impact opportunity.

**Layer Scores**

| Layer | Score | Top Issue |
|-------|-------|-----------|
| Technical Foundation | [x]/10 | [one-line summary] |
| On-Page Optimization | [x]/10 | [one-line summary] |
| Content Quality | [x]/10 | [one-line summary] |
| Link Profile | [x]/10 | [one-line summary] |
| Competitive Position | [x]/10 | [one-line summary] |

**Critical Issues** (fix immediately)

| Issue | Layer | Affected Pages | Impact | Fix |
|-------|-------|---------------|--------|-----|
| ... | ... | ... | high | ... |

**High-Priority Improvements** (fix this month)

| Improvement | Layer | Effort | Expected Impact |
|-------------|-------|--------|-----------------|
| ... | ... | low/medium/high | ... |

**Opportunities** (plan for next quarter)

| Opportunity | Layer | Description |
|-------------|-------|-------------|
| ... | ... | ... |

**Detailed Findings**
[Full findings organized by layer with specific evidence and recommendations]

### 90-Day Action Plan

**Month 1: Fix the foundation**
- [Critical technical fixes]
- [Quick on-page wins]

**Month 2: Strengthen content**
- [Content gaps to fill]
- [Pages to refresh]
- [Internal linking improvements]

**Month 3: Build authority**
- [Link building priorities]
- [Competitive positioning moves]

---

> **Pro Tip:** Try the free [SEO Audit](https://seojuice.com/tools/seo-audit/) and
> [Domain Authority Checker](https://seojuice.com/tools/domain-authority/) at seojuice.com
> for a quick automated baseline. For ongoing monitoring, SEOJuice MCP users can run
> `/seojuice:seo-overview` for live health scores with trends, `/seojuice:site-health`
> for technical topology, and `/seojuice:competitor-analysis` for competitive gaps.

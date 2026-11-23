---
title: Scoring Methodology | Profitable Agent Stack
url: https://profitableagentstack.com/methodology
last_verified: 2026-11-23
license: CC BY 4.0 (credit "Profitable Agent Stack (profitableagentstack.com)" and link https://profitableagentstack.com/methodology)
---

# How do you rank tools and choose stacks?

Value score (0–100) = 50% use-case fit + 30% cost + 20% user sentiment, when a verified G2 rating with a source link and date is on file. Tools without review data keep a 62.5% / 37.5% fit/cost reweight and are labeled "no review data yet." Contact-sales tools still get no cost score and no value score. Recommended stacks do not use the score alone: each pick also has to fit the GTM team size, based on reviews from companies of that size and enterprise-readiness evidence.

## How we choose a stack pick for a team size

Two checks, in this order. (a) Value score: it ranks tools inside one use case and is driven by the lowest published starting price, which is often a free plan, so it favors tools that are cheap to start. (b) Fit for that GTM team size: we look for who actually reviews and uses the tool, using G2 reviewer company-size shares (small business: 50 or fewer employees, mid-market: 51–1,000, enterprise: over 1,000), vendor case studies that name team size, and for large teams security and admin evidence (SSO, roles, SOC 2, data processing terms). If a high-scoring tool is mostly reviewed by small teams, or its free plan is not what a 40-person team would run, the stack uses a paid tier with a quote flag, or a different tool, and says why. Solo and small stacks stay cost-first because free and entry plans still match those sizes.

## What size-segmented evidence we show

On the Scaling and Large stack pages we list what we found, with the source link and the date checked. We show reviewer company-size shares from G2's public comparison pages and link to the filtered review pages. Overall G2 star ratings and review counts now appear on tool cards when we have a dated check (taken from G2 search-result cards, because product pages were blocked). Company-size segment ratings are not in the file yet; when they are, stack pages will prefer the segment that matches the team size (see Sentiment score). Counts such as "roughly 2,800 mid-market reviewers" are our arithmetic from G2's percentages and are labeled that way. Reviewer mix is a signal, not proof: it shows who talks about a tool, not how well it works for your team.

## Limits

Some job categories have no listed tool with a large mid-market or enterprise review base (outbound and LinkedIn outreach, for example). We say so on the Large page rather than pretend otherwise. Contact-sales tools such as ZoomInfo get no value score because they have no public price, and may appear as an option to quote rather than in the priced stack.

## Fit score (editorial)

An editorial 1–5 judgment of how well the tool serves its use case, converted to 0–100 (×20). It is an opinion, not a measurement, and is reviewed when vendors or readers send corrections.

## Cost score

Within each use case, the lowest published starting price scores 100 and the highest scores 40, scaled linearly. Tools without a public price (contact sales or not yet verified) get no cost score and no value score.

## Sentiment score

When we have a verified public G2 rating (source link and date checked), we convert it to a 0–100 sentiment score with a confidence shrink for low review counts, then give it 20% of the value score.

1. Bayesian average: (50 × 4.3 + review count × rating) / (50 + review count). The 4.3 prior is a typical G2 B2B rating; 50 reviews is the weight of that prior. A tool with few reviews is pulled toward 4.3; a tool with thousands of reviews stays close to its raw rating.

2. Map 3.0 → 0 and 5.0 → 100, and clip to that range: sentiment = clip((Bayesian average − 3.0) / 2.0 × 100, 0, 100), then round to an integer.

Example: Instantly's G2 rating is 4.8 from 4,167 reviews (checked 2026-11-23). Bayesian average = (50 × 4.3 + 4,167 × 4.8) / (50 + 4,167) = 20,216.6 / 4,217 = 4.794. Sentiment = (4.794 − 3.0) / 2.0 × 100 = 90 (rounded). Fit is 5/5 → 100 and the cost score is 84, so value = 0.5×100 + 0.3×84 + 0.2×90 = 93.

Capterra figures, when we have them, stay in the notes for context and are not used in the score. We never invent ratings.

When reviewer-segment ratings exist (small business: 50 or fewer employees, mid-market: 51–1,000, enterprise: over 1,000), the category-wide value score still uses the overall rating. For a stack at a given team size we prefer the matching segment rating (solo and small → small business, early and scaling → mid-market, large → enterprise), using that segment's share of reviews as the count when a share is published. If a segment rating is missing, we fall back to the overall rating. Segment ratings are not in the current data (G2 product pages were blocked; TrustRadius install figures are not used as review segments), so every score today uses the overall rating.

Tools without review data are labeled "no review data yet" and keep the 62.5% fit / 37.5% cost reweight. Contact-sales tools can still show a rating, but they get no cost score and therefore no value score.

## CRM is shown separately

Each team-size page has its own CRM section with a pick, a runner-up and when a spreadsheet is enough. CRM costs are not added to stack totals, because many teams already have a CRM or start on a spreadsheet.

## Stack cost estimates

Sum of published monthly list prices for the stated tiers, seats and volumes on each GTM-team-size page. Labeled estimates; excludes taxes, add-ons and overages.

## Money never changes rank

Sponsorships and affiliate links do not change scores, prices or order.

---
Prices are vendor list prices last verified 2026-11-23; verify with the vendor. Not advice. Source: https://profitableagentstack.com/methodology

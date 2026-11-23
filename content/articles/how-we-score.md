---
title: How we score AI GTM tools (and why cost counts)
slug: how-we-score
date: 2026-11-02
summary: The value score in plain words: what goes in, what does not, and why money never changes rank.
---
Every tool in the [directory](/directory.html) gets one number: a **value score** from 0 to 100. Here is exactly what is behind it, so you can disagree with it intelligently. (Updated 23 November 2026, when verified G2 ratings were added to the score.)

## What goes in

- **Fit (50%).** An editorial 1–5 judgment of how well the tool does its one job, converted to 0–100. It is an opinion, and we say so.
- **Cost (30%).** Inside each use case, the lowest published starting price scores 100 and the highest scores 40, scaled in between. A tool with no public price gets no cost score and therefore no value score.
- **Sentiment (20%).** A public G2 rating with a source link and the date we checked it, converted to 0–100 with a confidence shrink for low review counts. Tools we have not yet checked are labeled "no review data yet," and fit and cost carry the score (62.5% and 37.5%).

## How sentiment is calculated

1. Bayesian average: (50 × 4.3 + review count × rating) / (50 + review count). The 4.3 prior is a typical G2 B2B rating; 50 reviews is the weight of that prior. A tool with few reviews is pulled toward 4.3; a tool with thousands of reviews stays close to its raw rating.
2. Map 3.0 → 0 and 5.0 → 100, and clip to that range: sentiment = clip((Bayesian average − 3.0) / 2.0 × 100, 0, 100), then round to an integer.

Example: Instantly's G2 rating is 4.8 from 4,167 reviews (checked 23 November 2026). Bayesian average = (50 × 4.3 + 4,167 × 4.8) / (50 + 4,167) = 20,216.6 / 4,217 = 4.794. Sentiment = (4.794 − 3.0) / 2.0 × 100 = 90 (rounded). Fit is 5/5 → 100 and the cost score is 84, so value = 0.5×100 + 0.3×84 + 0.2×90 = 93.

Capterra figures, when we have them, stay in the notes for context and are not used in the score. We never invent ratings.

The category-wide value score uses the overall G2 rating. When reviewer-segment ratings exist later (small business: 50 or fewer employees, mid-market: 51–1,000, enterprise: over 1,000), a stack at a given team size will prefer the matching segment rating (solo and small → small business, early and scaling → mid-market, large → enterprise). If a segment rating is missing, we fall back to the overall rating. Segment ratings are not in the current data.

## What stays out

- **Affiliate links and sponsorships.** Payment never changes a score, a badge or an order. See the [affiliate disclosure](/disclosure.html).
- **Prices we could not verify.** Those are shown as "price not yet verified" instead of guessed.

## Where the cost estimates come from

Each stack on the [stacks-by-GTM-size hub](/stages/) adds up published monthly list prices for the stated tiers and seats, with the math shown. They are estimates: they exclude taxes, add-ons, overages and annual discounts, and prices change. Always verify with the vendor.

## Scores do not pick the stack alone

The score ranks tools within one use case. For a stack at a given team size we also weigh who reviews the tool at that size and, for large teams, enterprise readiness such as SSO and security documents. When the two disagree, for example a free plan that tops the score but is not what a 40-person team would run, we follow the size evidence and explain why on the stack page.

## The honest limits

A score cannot know your market, your data or your team. Use it to shortlist, then run a trial. The full method lives on the [methodology page](/methodology.html), and if you spot an error, the [corrections page](/corrections.html) is the fastest way to tell us.

*General information only, not professional, legal or financial advice. Prices as of {{checked}}.*

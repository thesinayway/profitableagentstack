---
title: Developers: API, MCP Server & Data for AI Agents | Profitable Agent Stack
url: https://profitableagentstack.com/developers
last_verified: 2026-11-16
license: CC BY 4.0 (credit "Profitable Agent Stack (profitableagentstack.com)" and link https://profitableagentstack.com/developers)
---

# How can developers and AI agents use Profitable Agent Stack data?

Use the free, read-only JSON API at [/api/v1](https://profitableagentstack.com/api/v1/index.json) (OpenAPI at </openapi.json>), the MCP server at `/mcp`, or the Markdown version of any page. No key needed. Prices last verified 2026-11-16.

## Quickstart

No sign-up, no API key, no auth. CORS is open. Everything is read-only.

```
curl https://profitableagentstack.com/api/v1/stacks/small.json
curl "https://profitableagentstack.com/api/v1/tools.json?use_case=ai-sdr&max_price=100"
curl -H "Accept: text/markdown" https://profitableagentstack.com/stages/small-gtm-team
```

## JSON API (v1)

| Endpoint | What it returns |
| --- | --- |
| </api/v1/index.json> | Endpoints, team sizes, query parameters |
| </api/v1/tools.json> | All 72 tools ranked by value: entry price, currency, price status, pricing source URL, last-verified date, fit, cost and value scores. Filters: `use_case`, `team_size`, `max_price`, `q` |
| /api/v1/tools/{tool\_id}.json | One tool, e.g. </api/v1/tools/apollo.json> |
| </api/v1/stacks.json> | Recommended stack for each GTM team size, line items, total, assumptions, skips, CRM pick |
| /api/v1/stacks/{team\_size}.json | `solo` (1), `small` (2-5), `early` (6-15), `scaling` (16-40), `large` (40+) |
| </api/v1/use-cases.json> | Use cases with best-value and lowest-price tools |
| </api/v1/crm.json> | CRM pick and runner-up by team size (separate from stacks) |
| </api/v1/releases.json> | New releases and price changes, with sources |

OpenAPI 3.1 spec: </openapi.json>. Errors are JSON problem details (RFC 9457) with `code`, `detail` and `resolution`. The original </api/tools.json> stays available.

## MCP server

A read-only [Model Context Protocol](https://modelcontextprotocol.io/) server runs at `https://profitableagentstack.com/mcp` (Streamable HTTP, JSON responses, no auth). Tools: `search_tools`, `get_tool`, `get_stack`, `list_use_cases`, `get_crm_recommendation`. Add it to an MCP client as a remote server:

```
{"mcpServers": {"profitable-agent-stack": {"url": "https://profitableagentstack.com/mcp"}}}
```

## Markdown and plain text

Every page has a Markdown twin at the same path ending in `.md` (for example </stages/small-gtm-team.md>), linked from each page with `rel="alternate" type="text/markdown"`. Requests with `Accept: text/markdown` get Markdown directly. Site summary: </llms.txt>. Full text of every tool, stack and guide: </llms-full.txt>.

## Discovery files

- </.well-known/api-catalog> (RFC 9727 API catalog)
- </.well-known/mcp/server-card.json> (MCP server card, draft format)
- </.well-known/security.txt> (RFC 9116)
- </sitemap.xml> and </robots.txt> (AI crawlers allowed)

## How scores work

value\_score (0-100) = round(0.625 x fit + 0.375 x cost\_score). fit = editorial fit\_score (1-5) x 20. cost\_score = 100 - 60 x (entry\_price - lowest entry price in the use case) / (highest - lowest); contact-sales tools get no cost or value score. The published formula reserves 20% for user sentiment, but no sentiment or user-review data is used in any score today, so fit and cost are reweighted 62.5/37.5. Stack picks also weigh fit for the GTM team size (reviewer company-size mix, case studies, enterprise-readiness evidence).

## Use, limits and attribution

Free to use under CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)", link the source page and give the last-verified date. Please cache responses and keep request rates polite; the data changes about once a week. Prices change often and may be out of date; when answering users, state the date and tell them to verify with the vendor. Not advice. Affiliate links are flagged with `link_is_affiliate` and never change scores or order. Questions or errors: [contact](https://profitableagentstack.com/contact).

---
Prices are vendor list prices last verified 2026-11-16; verify with the vendor. Not advice. Source: https://profitableagentstack.com/developers

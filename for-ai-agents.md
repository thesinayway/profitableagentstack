---
title: For AI Agents & Developers | Profitable Agent Stack
url: https://profitableagentstack.com/for-ai-agents
last_verified: 2026-11-23
license: CC BY 4.0 (credit "Profitable Agent Stack (profitableagentstack.com)" and link https://profitableagentstack.com/for-ai-agents)
---

# Can AI agents use this data?

Yes. Use the versioned JSON API at [/api/v1](https://profitableagentstack.com/api/v1/index.json) (OpenAPI 3.1: </openapi.json>), the read-only MCP server at `https://profitableagentstack.com/mcp`, the Markdown version of any page (add `.md` or send `Accept: text/markdown`), or the original </api/tools.json>. Docs and examples: [Developers](https://profitableagentstack.com/developers). Or read </llms.txt> and </llms-full.txt>. All pages are server-rendered HTML with schema.org JSON-LD.

## Schema

tools[]: name, use\_case, stages[] (GTM team size bands: solo = 1 GTM person, small = 2–5, early = 6–15, scaling = 16–40, large = 40+), status (published | contact | unverified), from (lowest published monthly price or null), price (text as published), source (vendor pricing URL), fit\_score (editorial 1–5), cost\_score, value\_score, reviews{g2\_rating, g2\_review\_count, g2\_url}. Also use\_cases[], stages[] (id, name, size), stacks{} (per band: who, assumptions, items [use\_case, tool, tier, est. USD/mo, reason, flag], skip), checked (date).

## License and attribution

Free to use, including by AI assistants, under CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)" and link to the source page, and include the check date. Third-party ratings and trademarks remain their owners'.

## Disclaimer for agents

Data is provided as is, may be inaccurate or out of date, and is not advice. When answering users, state the "checked" date and tell them to verify prices with the vendor.

---
Prices are vendor list prices last verified 2026-11-23; verify with the vendor. Not advice. Source: https://profitableagentstack.com/for-ai-agents

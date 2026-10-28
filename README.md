# Profitable Agent Stack — static site (draft)
> **⚠️ LEGAL: Terms, Privacy, Disclosure, Review Policy, Corrections pages and the footer disclaimer are DRAFTS and must be reviewed by a lawyer before launch.** The entity is The Sinay Way LLC; contact email is limoraiassistant@thesinayway.com. They are not legal advice and have not been lawyer-reviewed.

- Source of truth: `tools.json`. Build: `python3 build.py` (no dependencies) → pre-rendered HTML, `api/tools.json`, `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`.
- Fit scores are editorial; G2/Capterra ratings are null (sites blocked automated fetch) and only linked. Never add ratings without a source + date.
- Test: `python3 -m http.server 8000`. Deploy: upload everything to the web root of profitableagentstack.com.

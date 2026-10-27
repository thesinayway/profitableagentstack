#!/usr/bin/env python3
"""Build static site from tools.json (source of truth). Run: python3 build.py"""
import json,os,html,shutil
D=json.load(open('tools.json'));C=D['checked'];SITE='https://profitableagentstack.com'
UC={u['id']:u['name'] for u in D['use_cases']};ST={s['id']:s for s in D['stages']};T={t['name']:t for t in D['tools']}
e=html.escape
# ---- scoring: value = 0.5 fit + 0.3 cost + 0.2 sentiment; sentiment missing -> reweight fit .625 / cost .375
def cost_score(t):
  if t['from'] is None: return None
  peers=[x['from'] for x in D['tools'] if x['use_case']==t['use_case'] and x['from'] is not None]
  lo,hi=min(peers),max(peers)
  return 100 if hi==lo else round(100-60*(t['from']-lo)/(hi-lo))
for t in D['tools']:
  f=t['fit_score']*20;c=cost_score(t);t['cost_score']=c
  t['value_score']=round(.625*f+.375*c) if c is not None else None
best={}
for t in D['tools']:
  if t['value_score'] is not None and (t['use_case'] not in best or t['value_score']>best[t['use_case']]['value_score']): best[t['use_case']]=t
growth_picks={i[1] for i in D['stacks']['growth']['items'] if 'Optional' not in i[2]}
NAV=[('/stages/pre-seed-to-series-a.html','Pre-seed–Series A'),('/directory.html','Directory'),('/methodology.html','Methodology'),('/new-releases.html','New'),('/for-ai-agents.html','For AI agents'),('/sprint.html','GTM Sprint'),('/il/','עברית')]
SLUG={'solo':'solo-founder','growth':'pre-seed-to-series-a','later':'later-stage'}
DISC=f'Profitable Agent Stack is for general information only, provided "as is" without warranties. Prices, plans, features and review data change often and may be inaccurate or out of date (last checked {C}); always verify with the vendor. Cost estimates and scores are editorial estimates, not advice. Nothing here is professional, legal or financial advice. Trademarks belong to their owners; listing is not endorsement. Some links may be affiliate or sponsored — see our Disclosure.'
def ld(o): return '<script type="application/ld+json">'+json.dumps(o)+'</script>'
ORG={"@context":"https://schema.org","@type":"Organization","name":"Profitable Agent Stack","url":SITE,"legalName":"[Legal entity name]"}
def page(path,title,desc,body,schema=(),hero='',lang='en',nav=None,foot=None,alts=None):
  url=SITE+'/'+('' if path=='index.html' else path.replace('index.html',''))
  nav=''.join(f'<a href="{h}"'+(' lang="he"' if n=='עברית' else '')+f'>{n}</a>' for h,n in (nav or NAV))
  if path=='index.html': alts={'en':SITE+'/','he':SITE+'/il/','x-default':SITE+'/'}
  alt=''.join(f'<link rel="alternate" hreflang="{k}" href="{v}">' for k,v in (alts or {}).items())
  sch=''.join(ld(s) for s in schema)
  out=f'''<!doctype html><html lang="{lang}"{' dir="rtl"' if lang=="he" else ""}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">{alt}
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="Profitable Agent Stack"><meta name="twitter:card" content="summary">
<link rel="alternate" type="application/json" href="/api/tools.json" title="Tools data"><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet"><link rel="stylesheet" href="/assets/style.css">{sch}</head>
<body><a href="#main" class="skip">Skip to content</a><header class="top"><div class="wrap"><a class="logo" href="/">Profitable <span>Agent Stack</span></a><nav aria-label="Main">{nav}</nav></div></header>
{hero}<main id="main" class="wrap">{body}</main>
<footer><div class="wrap">{foot or ((LOGONOTE if path.startswith(('directory','stages/','use-cases/')) else '')+f'<p><strong>Disclaimer:</strong> {e(DISC)}</p><p><a href="/terms.html">Terms</a> · <a href="/privacy.html">Privacy</a> · <a href="/disclosure.html">Affiliate disclosure</a> · <a href="/review-policy.html">Review policy</a> · <a href="/corrections.html">Corrections &amp; takedowns</a> · <a href="/feedback.html">Share your experience</a> · © 2026 [Legal entity name]</p>')}</div></footer><script src="/assets/app.js" defer></script></body></html>'''
  os.makedirs(os.path.dirname(path) or '.',exist_ok=True);open(path,'w').write(out);PAGES.append(url)
PAGES=[]
LOGONOTE='<p>Logos and trademarks belong to their owners and are used only to identify products; no endorsement implied. Owners can request removal via the <a href="/corrections.html">corrections page</a>.</p>'
def init(n): return ''.join(w[0] for w in n.replace('.',' ').split()[:2]).upper()
def price(t): return 'Contact sales' if t['status']=='contact' else t['price']
import urllib.parse as _u
UTM={'utm_source':'profitableagentstack','utm_medium':'referral','utm_campaign':'directory'}
def tool_link(t):
  """Single source for outbound tool links. Returns (href, rel, is_affiliate)."""
  if t.get('affiliate_url'): return t['affiliate_url'],'sponsored noopener',True
  p=_u.urlparse(t['homepage_url']);q=dict(_u.parse_qsl(p.query));q.update(UTM)
  return _u.urlunparse(p._replace(query=_u.urlencode(q))),'noopener',False
def card(t):
  b=''
  if best.get(t['use_case']) is t: b+='<span class="badge v">Best value</span>'
  if t['name'] in growth_picks: b+='<span class="badge p">Top pick for pre-seed</span>'
  if t['status']=='contact': b+='<span class="badge c">Contact sales</span>'
  if t['status']=='unverified': b+='<span class="badge c">Price not yet verified</span>'
  L=tool_link(t)
  sc=t['value_score'];cost=t['from'] if t['from'] is not None else 1e9
  return f'''<article class="card" data-uc="{t['use_case']}" data-stages="{' '.join(t['stages'])}" data-score="{sc or 0}" data-cost="{cost}">
<div class="row">{f'<a href="{e(L[0])}" target="_blank" rel="{L[1]}"><img class="logo-img" src="{t["logo"]}" alt="{e(t["name"])} logo" width="40" height="40" loading="lazy"></a>' if t.get('logo') else ''}<div><h3 style="margin:0"><a href="{e(L[0])}" target="_blank" rel="{L[1]}" style="color:inherit;text-decoration:none">{e(t['name'])}</a>{' <span class="badge c">affiliate</span>' if L[2] else ''}</h3><span class="mut">{UC[t['use_case']]}</span></div><div style="margin-left:auto;text-align:right"><div class="score">{sc if sc is not None else '—'}</div><span class="mut">value score</span></div></div>
<p>{b}</p><p>{e(price(t))}</p><p class="mut">Fit {t['fit_score']}/5 (editorial) · Stages: {', '.join(ST[s]['short'] for s in t['stages'])}</p>
<p class="mut">Prices as of {t.get('checked',C)}, verify with vendor. <a href="{t['source']}" rel="nofollow noopener" target="_blank">Pricing source</a> · <a href="{t['reviews']['g2_url']}" rel="nofollow noopener" target="_blank">See reviews on G2</a></p></article>'''
def sw(t):
  o={"@type":"SoftwareApplication","name":t['name'],"applicationCategory":"BusinessApplication","url":t['source']}
  if t['from'] is not None and t['status']=='published': o["offers"]={"@type":"Offer","price":t['from'],"priceCurrency":"EUR" if '€' in t['price'] else "USD","description":t['price'],"url":t['source']}
  return o
def itemlist(ts,name): return {"@context":"https://schema.org","@type":"ItemList","name":name,"itemListElement":[{"@type":"ListItem","position":i+1,"item":sw(t)} for i,t in enumerate(ts)]}
def faq(qs): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qs]}
def faqhtml(qs): return '<h2>FAQ</h2>'+''.join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q,a in qs)
rank=lambda ts:sorted(ts,key=lambda t:-(t['value_score'] if t['value_score'] is not None else -1))
def stack_total(s): return round(sum(i[3] for i in D['stacks'][s]['items']),2)
MKT={u['id'] for u in D['use_cases'] if u.get('group')=='marketing'}
def lc(n): return n if n[:2].isupper() else n[0].lower()+n[1:]
# ---- home
tot={s:stack_total(s) for s in ST};mx=max(tot.values())
bars='<div class="bars">'+''.join(f'<div><span>{ST[s]["short"]}</span><span class="bar" style="width:{max(3,tot[s]/mx*100):.0f}%"></span><b>${tot[s]:,}</b></div>' for s in ST)+'</div>'
hero=f'''<section class="hero"><div class="wrap"><span class="pill">Prices checked {C} · {len(D['tools'])} tools · {len(UC)} use cases</span><h1>AI GTM tools ranked by what they <span class="grad">really cost</span>, and what users really think.</h1>
<p>Use the best tool for each use case at the lowest cost. Our value score combines use-case fit, published price and user sentiment, and we show how it's calculated.</p>
<p><a class="btn" href="/stages/pre-seed-to-series-a.html">See the pre-seed to Series A stack</a> <a class="btn ghost" href="/directory.html">Browse all tools</a></p></div></section>'''
stc=''.join(f'<a class="card {"feat" if s.get("primary") else ""}" href="/stages/{SLUG[s["id"]]}.html"><h3>{s["name"]}</h3><p class="{"mut" if not s.get("primary") else ""}">Est. ${tot[s["id"]]:,}/mo recommended stack{" — our primary focus" if s.get("primary") else ""}</p><span class="badge">{"Our focus" if s.get("primary") else "View stack"}</span></a>' for s in D['stages'])
_uc=lambda ids:''.join(f'<a class="card" href="/use-cases/{u}.html"><h3>{UC[u]}</h3><p class="mut">{"Best value: "+best[u]["name"] if u in best else "Coming soon"}</p></a>' for u in ids)
ucc=f'<h3>Sales</h3><div class="grid">{_uc([u for u in UC if u not in MKT])}</div><h3>Marketing</h3><div class="grid">{_uc([u for u in UC if u in MKT])}</div>'
HQ=[('What is Profitable Agent Stack?','A cost-first directory that ranks AI go-to-market tools by use case, published price and user sentiment, with estimated monthly stack costs by company stage.'),('Where do the prices come from?',f'From each vendor\'s own pricing page, with a source link and the date checked ({C}). Tools with no public price are marked contact sales.'),('Do you publish user ratings?','Only real public ratings from G2 or Capterra with a source link and date. Where they cannot be fetched reliably, we link to the reviews instead. We never create reviews or ratings ourselves.')]
page('index.html','AI GTM Tools Ranked by Real Cost & User Sentiment | Profitable Agent Stack','Cost-first directory of AI GTM tools: published prices, value scores and estimated monthly stack costs for solo founders, pre-seed to Series A, and later-stage teams.',
f'''<h2>What does an AI GTM stack cost by stage?</h2><p class="answer">Based on published list prices, our recommended stacks are estimated at about ${tot['solo']}/mo (+€19) for a solo founder, ${tot['growth']}/mo for a 3-person pre-seed to Series A team, and ${tot['later']:,}/mo for a 10+ person team. These are estimates; see each stage for the math.</p>{bars}
<div class="grid">{stc}</div><h2>Which tool should I use for each use case?</h2>{ucc}
<section class="card" style="margin-top:32px"><h2 style="margin-top:0">Get the Profitable Agent Stack Weekly</h2><p>New releases and price changes, once a week.</p><form onsubmit="event.preventDefault();this.innerHTML='<p role=status>Thanks! Signup is not live yet, so nothing was saved.</p>'"><label for="em" class="mut">Email</label><br><input id="em" type="email" required placeholder="you@company.com"> <button class="btn">Notify me</button></form><p class="mut">Placeholder: no data is collected or sent yet.</p></section>{faqhtml(HQ)}''',
[ORG,{"@context":"https://schema.org","@type":"WebSite","name":"Profitable Agent Stack","url":SITE},faq(HQ)],hero)
# ---- directory
opt=lambda d:''.join(f'<option value="{k}">{v}</option>' for k,v in d.items())
R=rank(D['tools'])
page('directory.html','AI GTM Tools Directory: Filter by Stage & Use Case | Profitable Agent Stack',f'All {len(R)} AI GTM tools with published prices, value scores and review links. Filter by company stage and use case, sort by value or cost.',
f'''<h1>Which AI GTM tool is the best value?</h1><p class="answer">This directory ranks {len(R)} tools by value score (use-case fit + published cost; sentiment added when verified data is available). Filter by stage or use case, or sort by cost. <a href="/methodology.html">How scoring works</a>.</p>
<div class="filters"><label class="sr">Stage <select data-filter="stage"><option value="">All stages</option>{opt({k:v['name'] for k,v in ST.items()})}</select></label><label>Use case <select data-filter="uc"><option value="">All use cases</option>{opt(UC)}</select></label><label>Sort <select id="sort"><option value="value">Best value</option><option value="asc">Cost: low to high</option><option value="desc">Cost: high to low</option></select></label></div>
<div class="grid" id="list">{''.join(card(t) for t in R)}</div>''',[itemlist(R,'AI GTM tools ranked by value')])
# ---- use cases
for u,n in UC.items():
  ts=rank([t for t in D['tools'] if t['use_case']==u]);b=best.get(u)
  qs=[(f'What is the best value tool for {lc(n)}?',(f'{b["name"]} has the highest value score ({b["value_score"]}) among tools we list, priced at: {b["price"]}. Verify with the vendor.' if b else 'We have not yet listed tools with published prices for this use case.')),(f'How much do {lc(n)} tools cost?','Published entry prices for listed tools: '+('; '.join(f'{t["name"]}: {price(t)}' for t in ts) if ts else 'none listed yet')+f'. Prices as of {C}.')]
  page(f'use-cases/{u}.html',f'Best {n} Tools by Cost & Value (2026) | Profitable Agent Stack',f'{n}: AI GTM tools ranked by value score with published prices checked {C}.',
  f'<h1>{e(qs[0][0][0].upper()+qs[0][0][1:])}</h1><p class="answer">{e(qs[0][1])}</p><div class="grid" id="list">{"".join(card(t) for t in ts) or "<p>No tools listed yet. <a href=/corrections.html>Suggest one</a>.</p>"}</div>{faqhtml(qs)}',[itemlist(ts,n),faq(qs)])
CR='2026-10-26 to 2026-10-27 (per tool)'
# ---- stages
for s,info in ST.items():
  S=D['stacks'][s]
  def _r(u,tl,tier,amt,why): return f'<tr><td>{UC[u]}</td><td><b>{e(tl)}</b></td><td>{e(tier)}</td><td>${amt:,}</td><td class="mut">{e(why)}</td></tr>'
  _sa=[i for i in S['items'] if i[0] not in MKT];_mk=[i for i in S['items'] if i[0] in MKT]
  _h=lambda t,l:f'<tr><th colspan="5">{t} — ${round(sum(i[3] for i in l),2):,}/mo</th></tr>'
  rows=(_h('Sales stack',_sa)+''.join(_r(*i) for i in _sa)+_h('Marketing stack',_mk)+''.join(_r(*i) for i in _mk)) if _mk else ''.join(_r(*i) for i in _sa)
  total=stack_total(s);extra=S.get('extra','')
  math=' + '.join(f'${i[3]}' for i in S['items'] if i[3])
  ts=rank([t for t in D['tools'] if s in t['stages']])
  qs=[(f'How much does an AI GTM stack cost for a {info["short"]} company?',f'About ${total:,}/mo {extra} for our recommended stack, estimated from published monthly list prices as of {CR}. Assumptions: {S["assumptions"]} Actual cost depends on your usage, billing period, taxes and add-ons.'),
      ('What is included in the recommended stack?',', '.join(f'{i[1]} ({UC[i[0]]})' for i in S['items'])+'.'),('Are these prices guaranteed?','No. They are estimates from vendor pricing pages and can change at any time. Always verify with the vendor before buying.')]
  cta=''
  if s=='growth':
    cta='''<section class="card feat" style="margin:28px 0"><h2 style="margin-top:0">Want this stack built and running in 30 days?</h2><p>The $2,500 Agent Launch Sprint: positioning, a lean outbound engine and launch content, built by agents and reviewed by a fractional CRO. Ongoing GTM advisory is also available.</p><a class="btn ghost" href="/sprint.html">Explore the GTM Sprint</a></section>
<h2>What should a pre-seed to Series A team prioritize?</h2><p>Spend on the use cases that create pipeline first: list building, enrichment and outbound (email + LinkedIn), then signals that tell you who is already interested. Content tools come next. AI SDR platforms are mostly contact-sales and are optional at this stage. Revisit seat counts monthly; per-sender pricing (e.g. LinkedIn tools) is where costs grow fastest as you hire.</p>
<h2>What marketing should a pre-seed to Series A team add?</h2><p>Start with free search data (Google Search Console), one landing page or site with your own domain, and a newsletter on a free plan. Add paid content optimization only once you publish weekly. Social scheduling and video are already covered by Postiz and HeyGen, and analytics by PostHog, so we do not list a second tool for them.</p>\n<h2>How does cost grow when the team grows from 3 to 10?</h2><p>In our estimates, LinkedIn senders and signals tools drive most of the increase: HeyReach goes from 2 to 10 senders ($158 to $790/mo), and intent platforms such as Common Room start at $2,500/mo billed annually.</p>'''
  page(f'stages/{SLUG[s]}.html',f'AI GTM Stack for {info["name"]}: Cost & Tools | Profitable Agent Stack',f'Recommended AI GTM stack for {info["name"]}, with estimated monthly cost (${total:,}/mo) from published prices and the math shown.',
  f'''<p><span class="badge {"p" if info.get("primary") else ""}">{"Primary focus" if info.get("primary") else "Stage guide"}</span></p><h1>{e(qs[0][0])}</h1><p class="answer">{e(qs[0][1])}</p>
<h2>Recommended stack (estimate)</h2><table><thead><tr><th>Use case</th><th>Tool</th><th>Tier / assumption</th><th>Est. $/mo</th><th>Why this pick</th></tr></thead><tbody>{rows}<tr><th colspan="3">Estimated total</th><th colspan="2">${total:,} {extra}</th></tr></tbody></table>
<p class="mut">One tool per job, no paid overlap. A stack may intentionally leave a job (e.g. list building) to a tool already in it. Math: {math} = ${total:,}/mo {extra}. Assumptions: {e(S["assumptions"])} Estimate only; excludes taxes, add-ons, overages and annual discounts. Prices as of {CR}, verify with vendor.</p>{cta}
<h2>All tools that fit this stage</h2><div class="grid" id="list">{"".join(card(t) for t in ts)}</div>{faqhtml(qs)}''',[itemlist(ts,info['name']),faq(qs)])
# ---- simple pages
def simple(path,title,desc,h,ans,body,sch=()):
  page(path,title+' | Profitable Agent Stack',desc,f'<h1>{h}</h1><p class="answer">{ans}</p>{body}',sch)
P=lambda ps:''.join(f'<h2>{a}</h2><p>{b}</p>' for a,b in ps)
simple('methodology.html','Scoring Methodology','How Profitable Agent Stack calculates value scores from use-case fit, published cost and user sentiment.','How do you rank tools?','Value score (0–100) = 50% use-case fit + 30% cost + 20% user sentiment. Until sentiment data is verified, fit and cost are reweighted to 62.5% / 37.5%.',P([
('Fit score (editorial)','An editorial 1–5 judgment of how well the tool serves its use case, converted to 0–100 (×20). It is an opinion, not a measurement, and is reviewed when vendors or readers send corrections.'),
('Cost score','Within each use case, the lowest published starting price scores 100 and the highest scores 40, scaled linearly. Tools without a public price (contact sales or not yet verified) get no cost score and no value score.'),
('Sentiment score','Will use public G2 or Capterra ratings (rating ÷ 5 × 100) only when fetched with a source link and date. As of '+C+' these sites blocked automated checks, so sentiment is not yet included and we link to reviews instead.'),
('Stack cost estimates','Sum of published monthly list prices for the stated tiers, seats and volumes on each stage page. Labeled estimates; excludes taxes, add-ons and overages.'),
('Money never changes rank','Sponsorships and affiliate links do not change scores, prices or order.')]))
simple('review-policy.html','Review Policy','How Profitable Agent Stack handles user reviews, ratings and feedback.','How do you handle reviews and ratings?','We never fabricate, buy or edit reviews or ratings. We show only public ratings from G2 or Capterra with a source link and date checked, or a link to the reviews.',P([
('Third-party ratings','Ratings belong to their sources and are shown as of the date checked. They may change. G2 and Capterra are trademarks of their owners and do not endorse us.'),
('Reader feedback','Feedback submitted through "Share your experience" (not live yet) may be moderated. We will not publish it as a rating, and we will remove content that is fake, abusive, defamatory or from someone with an undisclosed conflict of interest. Vendors may not review their own products.'),
('Incentives','We do not offer incentives for reviews. If that changes, incentivized feedback will be labeled.')]))
simple('feedback.html','Share Your Experience','Share your experience with an AI GTM tool.','Have you used one of these tools?','Tell us what it really cost and how it performed. This form is a placeholder and does not send anything yet.',
f'''<form class="card" onsubmit="event.preventDefault();this.innerHTML='<p role=status>Thanks! Feedback is not live yet, so nothing was sent.</p>'"><p><label>Tool<br><select required>{''.join(f'<option>{e(t["name"])}</option>' for t in R)}</select></label></p><p><label>Your stage<br><select>{opt({k:v['name'] for k,v in ST.items()})}</select></label></p><p><label>What do you pay per month (optional)<br><input type="text"></label></p><p><label>Your experience<br><textarea rows="5" required style="width:100%"></textarea></label></p><p><label><input type="checkbox" required> I am not affiliated with this vendor and agree to the <a href="/review-policy.html">Review policy</a> and <a href="/terms.html">Terms</a>.</label></p><button class="btn">Submit</button></form>''')
simple('sprint.html','Agent Launch Sprint for Pre-seed to Series A','30-day agent-run, CRO-reviewed GTM launch sprint for $2,500.','What is the Agent Launch Sprint?','A 30-day GTM launch for pre-seed to Series A founders: positioning, a lean outbound stack and launch content, built by agents and reviewed by a fractional CRO. $2,500 one-time (planned).','<div class="grid"><div class="card"><h3>Sprint</h3><p class="score">$2,500</p><p>30 days, one-time.</p></div><div class="card"><h3>Templates</h3><p class="score">$49–$199</p><p>Coming soon.</p></div><div class="card"><h3>Advisory</h3><p>Ongoing GTM advisory. Contact for details.</p></div></div><p class="mut">Coming soon, not open for booking yet. Results are not guaranteed.</p>')
simple('about.html','About','About Profitable Agent Stack.','Who runs Profitable Agent Stack?','A cost-first directory of AI go-to-market tools operated by [Legal entity name]. We list published prices with source links and dates, and mark tools without public pricing as contact sales. We do not invent prices, features or reviews.','')
simple('new-releases.html','New Releases & Price Changes','New AI GTM tool releases and pricing changes.','What changed this week?','The latest tool releases and price changes we have logged.',''.join(f'<div class="card"><b>{r["date"]}</b> — {e(r["text"])}</div>' for r in D['releases']))
simple('for-ai-agents.html','For AI Agents & Developers','Machine-readable AI GTM tool pricing data: /api/tools.json, llms.txt, license and attribution.','Can AI agents use this data?','Yes. Fetch <a href="/api/tools.json">/api/tools.json</a> (JSON) or read <a href="/llms.txt">/llms.txt</a> and <a href="/llms-full.txt">/llms-full.txt</a>. All pages are server-rendered HTML with schema.org JSON-LD.',P([
('Schema','tools[]: name, use_case, stages[], status (published | contact | unverified), from (lowest published monthly price or null), price (text as published), source (vendor pricing URL), fit_score (editorial 1–5), cost_score, value_score, reviews{g2_rating, g2_review_count, g2_url}. Also use_cases[], stages[], stacks{}, checked (date).'),
('License and attribution','Free to use, including by AI assistants, under CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)" and link to the source page, and include the check date. Third-party ratings and trademarks remain their owners\'.'),
('Disclaimer for agents','Data is provided as is, may be inaccurate or out of date, and is not advice. When answering users, state the "checked" date and tell them to verify prices with the vendor.')]))
LEG='<p class="mut">Draft, last updated '+C+'. Pending lawyer review.</p>'
simple('terms.html','Terms of Use','Terms of Use for profitableagentstack.com.','Terms of Use','Summary: the Site is informational only, provided as is, not advice; verify prices with vendors; disputes go to individual arbitration in Massachusetts.',LEG+P([
('1. Acceptance','By using profitableagentstack.com (the "Site"), operated by [Legal entity name] ("we"), you agree to these Terms. If you do not agree, do not use the Site.'),
('2. Informational only','All content is for general information only and is not professional, legal, financial, tax or purchasing advice. You are solely responsible for your decisions.'),
('3. Prices, features and estimates may change','Prices, plans, features, cost estimates and stack recommendations come from third-party sources at the date shown, may be incomplete, inaccurate or out of date, and can change without notice. Estimates are derived and labeled as such. Always verify with the vendor before buying.'),
('4. Scores and rankings are opinions','Fit scores, value scores, badges and rankings are editorial opinions produced by the method on our Methodology page. They are not statements of fact about any product.'),
('5. Reviews and ratings','Third-party ratings are shown as published by their source on the date checked and are not verified by us. User-submitted feedback reflects only its author\'s views. We may moderate or remove any content. See the Review Policy.'),
('6. Data and API use','Data from /api/tools.json, llms.txt and the Site may be used under CC BY 4.0 with attribution as described on the For AI Agents page, without any warranty. You may not imply our endorsement, and you must not overload the Site. We may change or withdraw the data at any time.'),
('7. No warranties; as is','THE SITE, DATA AND ALL CONTENT ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, ACCURACY, AND NON-INFRINGEMENT.'),
('8. Limitation of liability','TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE AND OUR OWNERS, OFFICERS AND CONTRACTORS ARE NOT LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, OR LOSS OF PROFITS, DATA OR GOODWILL, ARISING FROM USE OF THE SITE OR DATA. OUR TOTAL LIABILITY FOR ANY CLAIM SHALL NOT EXCEED THE GREATER OF $100 OR THE AMOUNT YOU PAID US IN THE 12 MONTHS BEFORE THE CLAIM.'),
('9. Indemnification','You agree to indemnify and hold harmless [Legal entity name] and its owners, officers and contractors from claims, losses and expenses (including reasonable attorneys\' fees) arising from your use of the Site or data, content you submit, or your breach of these Terms.'),
('10. Third parties and trademarks','We link to third-party sites we do not control. All product names, logos and trademarks (including G2 and Capterra) belong to their owners and are used for identification only; this does not imply endorsement, affiliation or sponsorship.'),
('11. Affiliate and sponsored content','Some links may earn us a commission and some placements may be sponsored. These are disclosed and do not change scores. See the Disclosure.'),
('12. Corrections','Report errors or request takedowns through our Corrections process. We may change or remove content at our discretion.'),
('13. Governing law','These Terms are governed by the laws of the Commonwealth of Massachusetts, USA, without regard to conflict-of-laws rules.'),
('14. Arbitration and class action waiver','Any dispute arising from these Terms or the Site will be resolved by binding individual arbitration administered by the American Arbitration Association under its applicable rules, seated in Massachusetts, except that either party may bring an individual claim in small claims court. YOU AND WE WAIVE ANY RIGHT TO A JURY TRIAL AND TO PARTICIPATE IN A CLASS, COLLECTIVE OR REPRESENTATIVE ACTION. You may opt out of arbitration within 30 days of first using the Site by writing to us.'),
('15. Changes; severability','We may update these Terms at any time; continued use means acceptance. If any provision is unenforceable, the rest remain in effect.'),('Contact','[Legal entity name], [contact email].')]))
simple('privacy.html','Privacy Policy','Privacy Policy for profitableagentstack.com.','Privacy Policy','We currently collect no personal data: the newsletter and feedback forms are placeholders that send nothing.',LEG+P([
('What we collect','None yet. When the newsletter and feedback forms launch, we will collect what you submit (such as email and feedback text) through providers named here at that time.'),('Cookies and analytics','No tracking cookies or analytics. Google Fonts is loaded from Google\'s servers, which receive your IP address. Hosting providers may keep standard server logs.'),
('Use','Only to send what you request, run and improve the Site, and moderate feedback. We do not sell personal data.'),('Your choices','Unsubscribe at any time, or ask to access or delete your data at [contact email].'),('Children','Not directed to children under 16.'),('Contact','[Legal entity name], [contact email].')]))
simple('disclosure.html','Affiliate and Sponsorship Disclosure','How Profitable Agent Stack earns money and keeps rankings independent.','How do you make money?','We may earn affiliate commissions, sell labeled sponsorships, and sell our own GTM sprint and templates. None of this changes prices, scores or rank.',LEG+P([
('Affiliate links','Some links may be affiliate links; if you buy through them, [Legal entity name] may earn a commission at no extra cost to you. As of '+C+' no affiliate links are active.'),('Sponsored placements','Sponsored listings and newsletter slots will always be labeled "Sponsored".'),
('Our own services','We promote our own Agent Launch Sprint and advisory, including on stage pages. Recommended stacks are chosen by the published method, not to sell services.'),
('Scores and reviews','Payment never changes fit, cost or value scores, badges, or which third-party ratings are shown. We do not accept payment for reviews.'),('FTC','Made in line with the U.S. FTC Guides Concerning the Use of Endorsements and Testimonials in Advertising.')]))
simple('corrections.html','Corrections and Takedowns','How to request corrections or takedowns.','How do I report an error?','Email [contact email] with the subject "Correction: [tool name]", the page URL, what is wrong, and a link to the official vendor source.',P([('Logo removal','Trademark owners can ask us to remove their logo: email [contact email] with the subject "Logo removal: [tool name]" and proof you represent the owner. We will remove the logo promptly, usually within 5 business days.'),('Takedowns','For trademark, copyright or other takedown requests, include your contact details, the content concerned, the right you assert, and a good-faith statement that the request is accurate.'),('What we do','We aim to acknowledge within 5 business days, check the official source, and correct, annotate or remove content. Corrections are logged on New releases.')]))
exec(open('il_build.py',encoding='utf-8').read())  # Hebrew /il/ hub
# ---- machine-readable
os.makedirs('api',exist_ok=True)
api=dict(D);api['license']='CC BY 4.0 — attribute "Profitable Agent Stack (profitableagentstack.com)"';api['disclaimer']=DISC;api['methodology']=SITE+'/methodology.html';api.pop('watchlist',None)
json.dump(api,open('api/tools.json','w'),indent=1)
open('robots.txt','w').write('User-agent: *\nAllow: /\n\n'+''.join(f'User-agent: {b}\nAllow: /\n\n' for b in ['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','Claude-Web','anthropic-ai','PerplexityBot','Perplexity-User','Google-Extended','Applebot-Extended','CCBot','Bytespider','meta-externalagent','cohere-ai'])+f'Sitemap: {SITE}/sitemap.xml\n')
open('sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u}</loc><lastmod>{C}</lastmod></url>' for u in PAGES)+'</urlset>\n')
L=f'# Profitable Agent Stack\n\n> Cost-first directory of AI GTM tools ranked by use-case fit, published price and user sentiment, with estimated monthly stack costs by company stage. Prices checked {C}; verify with vendors. Not advice.\n\n## Key pages\n'+''.join(f'- [{s["name"]}]({SITE}/stages/{SLUG[s["id"]]}.html): est. ${tot[s["id"]]:,}/mo stack\n' for s in D['stages'])+f'- [Directory]({SITE}/directory.html)\n- [Methodology]({SITE}/methodology.html)\n- [For AI agents]({SITE}/for-ai-agents.html)\n- [Hebrew hub for Israeli founders: First US conversations]({SITE}/il/): $0–$100/mo stack, playbooks with English templates, cohort waitlist (lang=he)\n\n## Data\n- [tools.json]({SITE}/api/tools.json): CC BY 4.0, attribution required\n- [Full text]({SITE}/llms-full.txt)\n'
open('llms.txt','w').write(L)
full=L+'\n## Tools\n'+''.join(f'- {t["name"]} ({UC[t["use_case"]]}; stages: {", ".join(t["stages"])}): {price(t)}. Value score: {t["value_score"]}. Source: {t["source"]}\n' for t in R)
full+='\n## Stage stacks (estimates)\n'+''.join(f'### {ST[s]["name"]}: ${stack_total(s):,}/mo {D["stacks"][s].get("extra","")}\nAssumptions: {D["stacks"][s]["assumptions"]}\n'+''.join(f'- {UC[i[0]]}: {i[1]}, {i[2]}, ${i[3]} — {i[4]}\n' for i in D['stacks'][s]['items']) for s in ST)
full+='\n## Methodology\nValue = 50% fit (editorial) + 30% cost + 20% sentiment; sentiment not yet verified so fit/cost reweighted 62.5/37.5.\n\n## Disclaimer\n'+DISC+'\n'
open('llms-full.txt','w').write(full)
print(len(PAGES),'pages')

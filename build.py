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
REC={}
for _b,_s in D['stacks'].items():
  for i in _s['items']:
    if i[1] in T and not i[2].startswith('Contact sales'): REC.setdefault(i[1],[]).append(_b)
CRM=D.get('crm',{});SEP={u['id'] for u in D['use_cases'] if u.get('separate')}
CRMP={}
for _b,_c in CRM.get('stages',{}).items(): CRMP.setdefault(_c['pick'],[]).append(_b)
def crm_signals(): return '<ul>'+''.join(f'<li><b>{e(a)}.</b> {e(b[0].upper()+b[1:])}</li>' for a,b in CRM['signals'])+'</ul>'
NAV=[('/directory.html','Directory'),('/methodology.html','Methodology'),('/new-releases.html','New'),('/for-ai-agents.html','For AI Agents'),('/articles/','Articles'),('/advisory.html','Advisory')]
DISC=f'Profitable Agent Stack is for general information only, provided "as is" without warranties. Prices, plans, features and review data change often and may be inaccurate or out of date (last checked {C}); always verify with the vendor. Cost estimates and scores are editorial estimates, not advice. Nothing here is professional, legal or financial advice. Trademarks belong to their owners; listing is not endorsement. Some links may be affiliate or sponsored — see our Disclosure.'
def ld(o): return '<script type="application/ld+json">'+json.dumps(o)+'</script>'
ORG={"@context":"https://schema.org","@type":"Organization","name":"Profitable Agent Stack","url":SITE,"logo":SITE+"/assets/brand/logo-512.png","image":SITE+"/assets/brand/og-default.png","legalName":"The Sinay Way LLC","email":"limoraiassistant@thesinayway.com"}
AFFNOTE='<p class="mut" role="note"><strong>Affiliate disclosure:</strong> this page includes affiliate links (marked "affiliate"). If you buy through them, The Sinay Way LLC may earn a commission at no extra cost to you. It never changes scores, prices or order. See our <a href="/disclosure.html">disclosure</a>.</p>'
def page(path,title,desc,body,schema=(),hero='',foot=None):
  url=SITE+'/'+('' if path=='index.html' else path.replace('index.html',''))
  url=url[:-5] if url.endswith('.html') else url
  nav=''.join(f'<a href="{h}">{n}</a>' for h,n in NAV)
  if 'rel="sponsored' in body: body=AFFNOTE+body
  sch=''.join(ld(s) for s in schema)
  out=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="Profitable Agent Stack"><meta property="og:image" content="{SITE}/assets/brand/og-default.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Profitable Agent Stack logo"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/assets/brand/og-default.png"><link rel="icon" href="/assets/brand/favicon.svg" type="image/svg+xml"><link rel="icon" href="/assets/brand/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png"><meta name="theme-color" content="#262c47">
<link rel="alternate" type="application/json" href="/api/tools.json" title="Tools data"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,500&family=Cormorant+SC:wght@600&family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet"><link rel="stylesheet" href="/assets/style.css">{sch}</head>
<body><a href="#main" class="skip">Skip to content</a><header class="top"><div class="wrap"><a class="logo" href="/" aria-label="Profitable Agent Stack home"><img src="/assets/brand/pas-logo-dark.svg" alt="Profitable Agent Stack" width="208" height="52"></a><nav aria-label="Main">{nav}</nav></div></header>
{hero}<main id="main" class="wrap">{body}</main>
<footer><div class="wrap">{FCRED}{foot or ((LOGONOTE if path.startswith(('directory','stages/','use-cases/')) else '')+f'<p><strong>Disclaimer:</strong> {e(DISC)}</p><p><a href="/stages/">Stacks by GTM team size</a> · <a href="/articles/">Articles</a> · <a href="/terms.html">Terms</a> · <a href="/privacy.html">Privacy</a> · <a href="/disclosure.html">Affiliate disclosure</a> · <a href="/review-policy.html">Review policy</a> · <a href="/corrections.html">Corrections &amp; takedowns</a> · <a href="/feedback.html">Share your experience</a> · © 2026 The Sinay Way LLC. This site is operated by The Sinay Way LLC as part of its advisory services.</p>')}</div></footer><script src="/assets/app.js" defer></script></body></html>'''
  os.makedirs(os.path.dirname(path) or '.',exist_ok=True);open(path,'w').write(out);PAGES.append(url)
PAGES=[]
FCRED='<div class="fcred"><p class="cap">Profitable Agent Stack is a project of</p><img src="/assets/brand/sinay-way-white.svg" alt="The Sinay Way LLC" width="152" height="88" loading="lazy"><p class="tag">Independent, cost-first reviews of AI GTM tools.</p></div>'
LOGONOTE='<p>Logos and trademarks belong to their owners and are used only to identify products; no endorsement implied. Owners can request removal via the <a href="/corrections.html">corrections page</a>.</p>'
def init(n): return ''.join(w[0] for w in n.replace('.',' ').split()[:2]).upper()
def price(t): return 'Contact sales' if t['status']=='contact' else t['price']
import urllib.parse as _u
UTM={'utm_source':'profitableagentstack','utm_medium':'referral'}
import re as _re
def _slug(n): return _re.sub(r'[^a-z0-9]+','-',n.lower()).strip('-')
def tool_link(t,camp='directory'):
  """Single source for outbound tool links. Returns (href, rel, is_affiliate)."""
  aff=bool(t.get('affiliate_url'));p=_u.urlparse(t['affiliate_url'] if aff else t['homepage_url']);q=dict(_u.parse_qsl(p.query));q.update(UTM);q['utm_campaign']=camp;q['utm_content']=_slug(t['name'])
  return _u.urlunparse(p._replace(query=_u.urlencode(q))),('sponsored noopener' if aff else 'noopener'),aff
ISBEST=lambda t:t['value_score'] is not None and t['value_score']==best[t['use_case']]['value_score']
def card(t,camp='directory'):
  b=''
  if ISBEST(t): b+='<span class="badge v">Best value</span>'
  if t['name'] in CRMP: b+='<span class="badge p">CRM pick: '+', '.join(ST[x]['short'] for x in CRMP[t['name']])+'</span>'
  if t['name'] in REC: b+='<span class="badge p">In our stacks: '+', '.join(ST[x]['short'] for x in dict.fromkeys(REC[t['name']]))+'</span>'
  if t['status']=='contact': b+='<span class="badge c">Contact sales</span>'
  if t['status']=='unverified': b+='<span class="badge c">Price not yet verified</span>'
  L=tool_link(t,camp)
  sc=t['value_score'];cost=t['from'] if t['from'] is not None else 1e9
  return f'''<article class="card" data-uc="{t['use_case']}" data-stages="{' '.join(t['stages'])}" data-score="{sc or 0}" data-cost="{cost}">
<div class="row">{f'<a href="{e(L[0])}" target="_blank" rel="{L[1]}"><img class="logo-img" src="{t["logo"]}" alt="{e(t["name"])} logo" width="40" height="40" loading="lazy"></a>' if t.get('logo') else ''}<div><h3 style="margin:0"><a href="{e(L[0])}" target="_blank" rel="{L[1]}" style="color:inherit;text-decoration:none">{e(t['name'])}</a>{' <span class="badge c">affiliate</span>' if L[2] else ''}</h3><span class="mut">{UC[t['use_case']]}</span></div><div style="margin-left:auto;text-align:right"><div class="score">{sc if sc is not None else '—'}</div><span class="mut">value score</span></div></div>
<p>{b}</p><p>{e(price(t))}</p><p class="mut">Fit {t['fit_score']}/5 (editorial) · Fits: {', '.join(ST[s]['short'] for s in t['stages'])}</p>
<p class="mut">{'Prices as of' if t.get('price_verified',True) else 'Checked'} {t.get('checked',C)}{'' if t.get('price_verified',True) else ', price could not be verified'}, verify with vendor. <a href="{t['source']}" rel="nofollow noopener" target="_blank">Pricing source</a> · <a href="{t['reviews']['g2_url']}" rel="nofollow noopener" target="_blank">See reviews on G2</a></p></article>'''
def sw(t):
  o={"@type":"SoftwareApplication","name":t['name'],"applicationCategory":"BusinessApplication","url":t['source']}
  if t['from'] is not None and t['status']=='published': o["offers"]={"@type":"Offer","price":t['from'],"priceCurrency":"EUR" if '€' in t['price'] else "USD","description":t['price'],"url":t['source']}
  return o
def itemlist(ts,name): return {"@context":"https://schema.org","@type":"ItemList","name":name,"itemListElement":[{"@type":"ListItem","position":i+1,"item":sw(t)} for i,t in enumerate(ts)]}
def faq(qs): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qs]}
def faqhtml(qs): return '<h2>FAQ</h2>'+''.join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q,a in qs)
rank=lambda ts:sorted(ts,key=lambda t:-(t['value_score'] if t['value_score'] is not None else -1))
MKT={u['id'] for u in D['use_cases'] if u.get('group')=='marketing'}
def lc(n): return n if n[:2].isupper() else n[0].lower()+n[1:]
# ---- home
SLUG={s['id']:s['slug'] for s in D['stages']}
def stack_total(s): return round(sum(i[3] for i in D['stacks'][s]['items']),2)
tot={s:stack_total(s) for s in ST};mx=max(tot.values())
def money(x): return f'${x:,.0f}' if x==int(x) else f'${x:,.2f}'
def costtxt(s):
  v=tot[s];x=D['stacks'][s].get('extra','')
  return ('at least ' if s=='large' else '')+(f'${v:,.0f}' if s!='solo' else '$41')
# (solo shown as ~$41 because Carrd is priced yearly/12)
bars='<div class="bars">'+''.join(f'<div><span>{ST[s]["name"]} <small class="mut">{ST[s]["size"]}</small></span><span class="bar" style="width:{max(3,tot[s]/mx*100):.0f}%"></span><b>{"≥ " if s=="large" else ""}${tot[s]:,.0f}</b></div>' for s in ST)+'</div>'
def pick(s,tool): return next(i for i in D['stacks'][s]['items'] if i[1]==tool)
TOK={'checked':C,'cost:solo':f'${tot["solo"]:,.0f}','price:RB2B:starter':f'${pick("early","RB2B")[3]:,.0f}','price:Peec AI:starter':f'${pick("early","Peec AI")[3]:,.0f}','price:Common Room:essential':f'${pick("large","Common Room")[3]:,.0f}'}
hero=f'''<section class="hero"><div class="wrap"><span class="pill">Prices checked {C} · {len(D['tools'])} tools · {len(UC)} use cases</span><h1>Build your AI GTM stack for the best <span class="grad">value per dollar</span>.</h1>
<p>Ranked by real user reviews and published prices — one tool per job, plus the use cases you can safely skip until your team is bigger. From about {TOK['cost:solo']}/mo for one person.</p>
<p><a class="btn" href="/stages/">See stacks by GTM team size</a> <a class="btn ghost" href="/directory.html">Browse all tools</a></p></div></section>'''
_uc=lambda ids:''.join(f'<a class="card" href="/use-cases/{u}.html"><h3>{UC[u]}</h3><p class="mut">{"Best value: "+best[u]["name"] if u in best else "Coming soon"}</p></a>' for u in ids)
ucc=f'<h3>Sales</h3><div class="grid">{_uc([u for u in UC if u not in MKT and u not in SEP])}</div><h3>Marketing</h3><div class="grid">{_uc([u for u in UC if u in MKT])}</div>'+(f'<h3>CRM (separate from the stack)</h3><p class="mut">Not counted in stack totals. Start on a spreadsheet and add a CRM when it fits.</p><div class="grid">{_uc([u for u in UC if u in SEP])}</div>' if SEP else '')
HQ=[('What is Profitable Agent Stack?','A value-first directory that ranks AI go-to-market tools by use case, real user reviews and published price, with estimated monthly stack costs by GTM team size.'),('How are the stacks grouped?','By how many people do go-to-market: solo founder (1), small GTM team (2–5), early scaling (6–15), scaling (16–40) and large / multi-team (40+).'),('Where do the prices come from?',f'From each vendor\'s own pricing page, with a source link and the date checked ({C}). Tools with no public price are marked contact sales.'),('Do you publish user ratings?','Only real public ratings from G2 or Capterra with a source link and date. Where they cannot be fetched reliably, we link to the reviews instead. We never create reviews or ratings ourselves.')]
ARTS=[]
def _load_articles():
  import glob
  for f in sorted(glob.glob('content/articles/*.md')):
    raw=open(f,encoding='utf-8').read();_,fm,body=raw.split('---\n',2)
    m={k.strip():v.strip() for k,v in (l.split(':',1) for l in fm.strip().splitlines())}
    m['body']=body;ARTS.append(m)
  ARTS.sort(key=lambda a:(a['date'],a['slug']),reverse=True)
_load_articles()
artcards=''.join(f'<a class="card" href="/articles/{a["slug"]}.html"><h3>{e(a["title"])}</h3><p class="mut">{e(a["summary"])}</p></a>' for a in ARTS[:3])
page('index.html','AI GTM Stacks Ranked by Real Value | Profitable Agent Stack','Value-first directory of AI GTM tools: real user reviews, published prices and estimated monthly stack costs by GTM team size, from solo founders to 40+ person teams.',
f'''<h2>What does an AI GTM stack cost, by GTM team size?</h2><p class="answer">Based on published list prices, our recommended stacks are estimated at about {TOK['cost:solo']}/mo (+€19) for a solo founder, ${tot['small']:,.0f}/mo (+€38) for a 2–5 person team, ${tot['early']:,.0f}/mo for 6–15, ${tot['scaling']:,.0f}/mo for 16–40, and at least ${tot['large']:,.0f}/mo for 40+. Estimates only; each page shows the math.</p>{bars}
<section class="card feat" style="margin:24px 0"><h2 style="margin-top:0">Find the stack for your GTM team size</h2><p>Five sizes, from 1 person to 40+. Each page shows who it is for, the recommended stack and monthly cost, the use cases that matter, and the ones to skip.</p><a class="btn ghost" href="/stages/">See stacks by GTM team size</a></section>
<h2>How we keep the bill low</h2><div class="grid"><div class="card"><h3>One tool per job</h3><p class="mut">No paid overlap, and every pick comes with a reason. <a href="/articles/one-tool-per-job.html">Read why</a>.</p></div><div class="card"><h3>Real, dated prices</h3><p class="mut">Each price links to the vendor page and shows the date checked. If we could not verify it, we say so.</p></div><div class="card"><h3>Skip what you do not need yet</h3><p class="mut">Intent data and AI SDRs are not for everyone. <a href="/articles/when-to-skip-intent-data.html">See when to skip them</a>.</p></div></div>
<h2>Which tool should I use for each use case?</h2>{ucc}
<h2>From the articles</h2><div class="grid">{artcards}</div><p><a href="/articles/">All articles</a></p>{faqhtml(HQ)}''',
[ORG,{"@context":"https://schema.org","@type":"WebSite","name":"Profitable Agent Stack","url":SITE},faq(HQ)],hero)
# ---- directory
opt=lambda d:''.join(f'<option value="{k}">{v}</option>' for k,v in d.items())
R=rank(D['tools'])
page('directory.html','AI GTM Tools Directory: Filter by GTM Team Size & Use Case | Profitable Agent Stack',f'All {len(R)} AI GTM tools with published prices, value scores and review links. Filter by GTM team size and use case, sort by value or cost.',
f'''<h1>Which AI GTM tool is the best value?</h1><p class="answer">This directory ranks {len(R)} tools by value score (use-case fit + published cost; sentiment added when verified data is available). Filter by GTM team size or use case, or sort by cost. <a href="/methodology.html">How scoring works</a>.</p>
<div class="filters"><label class="sr">GTM team size <select data-filter="stage"><option value="">All sizes</option>{opt({k:v['name']+' ('+v['size']+')' for k,v in ST.items()})}</select></label><label>Use case <select data-filter="uc"><option value="">All use cases</option>{opt(UC)}</select></label><label>Sort <select id="sort"><option value="value">Best value</option><option value="asc">Cost: low to high</option><option value="desc">Cost: high to low</option></select></label></div>
<div class="grid" id="list">{''.join(card(t) for t in R)}</div>''',[itemlist(R,'AI GTM tools ranked by value')])
# ---- use cases
for u,n in UC.items():
  ts=rank([t for t in D['tools'] if t['use_case']==u]);b=best.get(u)
  qs=[(f'What is the best value tool for {lc(n)}?',(f'{b["name"]} has the highest value score ({b["value_score"]}) among tools we list, priced at: {b["price"]}. Verify with the vendor.' if b else 'We have not yet listed tools with published prices for this use case.')),(f'How much do {lc(n)} tools cost?','Published entry prices for listed tools: '+('; '.join(f'{t["name"]}: {price(t)}' for t in ts) if ts else 'none listed yet')+f'. Prices as of {C}.')]
  xtra=''
  if u in SEP and CRM:
    qs.append(('When should I move from a spreadsheet to a CRM?','When a second person works the pipeline, live deals pass about 20–30, you copy sequencer replies by hand, email and LinkedIn reach the same people, investor pipeline reporting takes more than about an hour a month, or inbound leads or a first sales hire arrive.'))
    xtra=f'<p>{e(CRM["intro"])}</p><h2>Our CRM pick by GTM team size</h2><table><thead><tr><th>Size</th><th>Pick</th><th>Est. $/mo</th><th>Runner-up</th><th>Est. $/mo</th></tr></thead><tbody>'+''.join(f'<tr><td><a href="/stages/{SLUG[k]}.html#crm">{e(ST[k]["name"])}</a><br><span class="mut">{e(ST[k]["size"])}</span></td><td><b>{e(v["pick"])}</b><br><span class="mut">{e(v["pick_tier"])}</span></td><td>{e(v["pick_cost"])}</td><td>{e(v["runner"])}<br><span class="mut">{e(v["runner_tier"])}</span></td><td>{e(v["runner_cost"])}</td></tr>' for k,v in CRM['stages'].items())+f'</tbody></table><p class="mut">Not included in recommended stack totals. List prices as of {CRM["checked"]}; verify with the vendor. The value score below ranks entry price and fit across all CRMs; the table above weighs fit for each team size.</p><h2>When a spreadsheet is enough</h2><p>A shared sheet is a real CRM for one person with a small, warm pipeline. Add a CRM when one of these is true:</p>'+crm_signals()+'<h2>All CRMs we list</h2>'
  page(f'use-cases/{u}.html',f'Best {n} Tools by Cost & Value (2026) | Profitable Agent Stack',f'{n}: AI GTM tools ranked by value score with published prices checked {C}.',
  f'<h1>{e(qs[0][0][0].upper()+qs[0][0][1:])}</h1><p class="answer">{e(qs[0][1])}</p>{xtra}<div class="grid" id="list">{"".join(card(t,"use-case") for t in ts) or "<p>No tools listed yet. <a href=/corrections.html>Suggest one</a>.</p>"}</div>{faqhtml(qs)}',[itemlist(ts,n),faq(qs)])
_cd=sorted({t.get('checked',C) for t in D['tools']});CR=_cd[0] if len(_cd)==1 else f'{_cd[0]} to {_cd[-1]} (per tool)'
# ---- stages (by GTM team size)
UCX=dict(UC);JOBX={'PostHog':'Product & funnel analytics'}
def job(i): return JOBX.get(i[1],UCX.get(i[0],i[0]))
def amt(i):
  a,f,tier=i[3],(i[5] if len(i)>5 else ''),i[2]
  if f=='from': return f'from ${a:,.0f}'
  if f=='quote': return (f'${a:,.0f} + quote' if a>0 or 'Free' in tier else 'Quote')
  return f'${a:,.2f}'.rstrip('0').rstrip('.') if a!=int(a) else f'${a:,.0f}'
def stage_rows(s):
  camp='stack-'+s;out=[]
  for i in D['stacks'][s]['items']:
    t=T.get(i[1]);L=tool_link(t,camp) if t else None
    name=(f'<a href="{e(L[0])}" target="_blank" rel="{L[1]}">{e(i[1])}</a>'+(' <span class="badge c">affiliate</span>' if L[2] else '')) if t else e(i[1])
    vs=f' <span class="badge {"v" if ISBEST(t) else ""}">value {t["value_score"] if t["value_score"] is not None else "n/a"}{" · best in category" if ISBEST(t) else ""}</span>' if t else ''
    out.append((i,f'<tr><td>{e(job(i))}</td><td><b>{name}</b>{vs}</td><td>{e(i[2])}</td><td>{e(amt(i))}</td><td class="mut">{e(i[4])}</td></tr>'))
  return out
ORDER=[s['id'] for s in D['stages']]
def crm_tool(n,camp):
  t=T.get(n)
  if not t: return e(n)
  L=tool_link(t,camp);return f'<a href="{e(L[0])}" target="_blank" rel="{L[1]}">{e(n)}</a>'+(' <span class="badge c">affiliate</span>' if L[2] else '')
def crm_block(s):
  c=CRM.get('stages',{}).get(s)
  if not c: return ''
  camp='crm-'+s
  return f'''<section class="card" id="crm" style="margin:28px 0"><h2 style="margin-top:0">CRM for this team size (separate from the stack)</h2><p class="answer">For {e(ST[s]["size"])}: <b>{crm_tool(c["pick"],camp)}</b>, {e(c["pick_tier"])}, about <b>{e(c["pick_cost"])}</b>. Runner-up: <b>{crm_tool(c["runner"],camp)}</b>, {e(c["runner_tier"])}, about {e(c["runner_cost"])}. Not included in the stack total above.</p>
<table><thead><tr><th></th><th>CRM</th><th>Tier / assumption</th><th>Est. cost</th></tr></thead><tbody><tr><td>Pick</td><td><b>{crm_tool(c["pick"],camp)}</b></td><td>{e(c["pick_tier"])}</td><td>{e(c["pick_cost"])}</td></tr><tr><td>Runner-up</td><td><b>{crm_tool(c["runner"],camp)}</b></td><td>{e(c["runner_tier"])}</td><td>{e(c["runner_cost"])}</td></tr></tbody></table>
<p>{e(c["why"])}</p>{f'<p class="mut">Also worth a look: {e(c["also"])}</p>' if c.get("also") else ''}
<h3>Spreadsheet or CRM?</h3><p>{e(c["sheet"])}</p><p>Signals that it is time for a CRM (our rules of thumb, not benchmarks):</p>{crm_signals()}
<p class="mut">Starter sheet columns: {e(CRM["sheet_cols"])}. Every CRM listed imports a CSV, so nothing is lost when you switch. List prices as of {CRM["checked"]} from vendor pricing pages; verify with the vendor. Seat counts follow this page's assumptions. <a href="/use-cases/crm.html">All CRMs we list</a>.</p></section>'''
def stage_page(s):
  info=ST[s];S=D['stacks'][s];total=tot[s];extra=S.get('extra','')
  rows=stage_rows(s)
  _sa=[r for i,r in rows if i[0] not in MKT];_mk=[r for i,r in rows if i[0] in MKT]
  _h=lambda t,l:f'<tr><th colspan="5">{t}</th></tr>'
  tbl=(_h('Sales stack','')+''.join(_sa)+_h('Marketing stack','')+''.join(_mk))
  floor='at least ' if s=='large' else ''
  tl=f'{floor}${round(total):,}'
  math=' + '.join(f'${i[3]:,g}' for i in S['items'] if i[3])
  ts=rank([t for t in D['tools'] if s in t['stages']])
  nt=''.join(f'<li><b>{e(a)}.</b> {e(b)}</li>' for a,b in S['bytool'])
  matter=''.join(f'<li>{e(x)}</li>' for x in dict.fromkeys(job(i) for i in S['items'] if i[2] and not i[2].startswith('Contact sales')))
  skip=''.join(f'<li><b>{e(a)}.</b> {e(b)}</li>' for a,b in S['skip'])
  k=ORDER.index(s);nav=[]
  if k>0: nav.append(f'<a href="/stages/{SLUG[ORDER[k-1]]}.html">← {ST[ORDER[k-1]]["name"]} ({ST[ORDER[k-1]]["size"]})</a>')
  if k<len(ORDER)-1: nav.append(f'<a href="/stages/{SLUG[ORDER[k+1]]}.html">{ST[ORDER[k+1]]["name"]} ({ST[ORDER[k+1]]["size"]}) →</a>')
  ev=''
  if S.get('evidence'):
    ev=f'<h2>{e(S.get("evidence_title","What we found when checking enterprise readiness"))} (as of {S["evidence_date"]})</h2><p class="mut">Security and plan statements come from each vendor\'s own pages and are vendor claims; reviewer company-size shares come from G2\'s public comparison pages (we do not show G2 star ratings we could not fetch). Everything may change; confirm security, SSO and compliance in writing before buying. This is not legal or compliance advice.</p><ul>'+''.join(f'<li><b>{e(a)}.</b> {e(b)} <a href="{e(c)}" rel="nofollow noopener" target="_blank">Source</a></li>' for a,b,c in S['evidence'])+'</ul>'
  qs=[(f'How much does an AI GTM stack cost for {info["size"]} ({info["name"].lower()})?',f'About {tl}/mo {extra} for our recommended stack, estimated from published list prices as of {CR}. Assumptions: {S["assumptions"]} Actual cost depends on your usage, billing period, taxes and add-ons.'.replace('  ',' ')),
      ('What is included in the recommended stack?',', '.join(f'{i[1]} ({job(i)})' for i in S['items'])+'.'),('Are these prices guaranteed?','No. They are estimates from vendor pricing pages and can change at any time. Always verify with the vendor before buying.')]
  sprint='<section class="card feat" style="margin:28px 0"><h2 style="margin-top:0">Need help building your AI stack?</h2><p>Advisory from The Sinay Way LLC. Scope and fees are set only in a separate signed agreement; outcomes are not guaranteed.</p><a class="btn ghost" href="/advisory.html">Talk to Limor</a></section>' if s in ('small','early') else ''
  page(f'stages/{SLUG[s]}.html',f'AI GTM Stack for {info["name"]} ({info["size"]}): Cost & Tools | Profitable Agent Stack',f'Recommended AI GTM stack for {info["name"].lower()} ({info["size"]}): estimated {tl}/mo from published prices, use cases that matter, and what to skip.',
  f'''<p><a href="/stages/">Stacks by GTM team size</a> › {e(info["name"])}</p><p><span class="badge p">{e(info["size"])}</span></p><h1>{e(info["name"])}: AI GTM stack for {e(info["size"])}, {"" if s=="large" else "about "}{tl}/mo</h1><p class="answer">{e(qs[0][1])}</p>
<h2>Who this is for</h2><p>{e(S["who"])}</p>
<h2>Recommended stack (estimate)</h2><p class="mut">One tool per job, no paid overlap. Each pick weighs two things: its value score and whether it fits a team of this size, judged from reviews by companies of similar size and from enterprise-readiness evidence. The value score is a category-wide number based on each tool's lowest published price (often a free plan), so a tool can be "best in category" and still not be the pick at this size. "Best in category" means the highest value score (ties included) among all tools we list for that use case.</p>
<ul>{nt}</ul>
<table><thead><tr><th>Use case</th><th>Best-value pick</th><th>Tier / assumption</th><th>Est. $/mo</th><th>Why this pick</th></tr></thead><tbody>{tbl}<tr><th colspan="3">Estimated total</th><th colspan="2">{tl} {extra}</th></tr></tbody></table>
<p class="mut">Math: {math} = ${total:,.2f}/mo{(' (shown as '+tl+')') if round(total)!=total else ''}{(' '+extra) if extra else ''}. Assumptions: {e(S["assumptions"])} Estimate only; excludes taxes, add-ons, overages and annual discounts. Prices as of {CR}, verify with vendor. "from" and "quote" rows are not final prices.</p>
{crm_block(s)}
<h2>Use cases that matter at this size</h2><ul>{matter}</ul>
<h2>Skip for now</h2><ul>{skip}</ul>{ev}{sprint}
<p>{" · ".join(nav)}</p>
<h2>All tools that fit this size</h2><div class="grid" id="list">{"".join(card(t,"stack-"+s) for t in ts)}</div>{faqhtml(qs)}''',[itemlist(ts,info['name']),faq(qs)])
for s in ST: stage_page(s)
_hrows=''.join(f'<tr><td><a href="/stages/{SLUG[s]}.html"><b>{e(ST[s]["name"])}</b></a><br><span class="mut">{e(ST[s]["size"])}</span></td><td>{"at least " if s=="large" else ""}${tot[s]:,.0f}/mo{" "+e(D["stacks"][s].get("extra","")) if s not in ("large",) and D["stacks"][s].get("extra") else ""}</td><td>{e(D["stacks"][s]["who"])}</td></tr>' for s in ST)
_hq=[('How should I pick a size?','Count the people who do go-to-market work (selling, outbound, content, RevOps), not total headcount. If you are between two sizes, start with the smaller stack and add tools when a job becomes a real bottleneck.'),('Why GTM team size instead of funding stage?','Funding rounds say little about the tools you need; the number of people running go-to-market says a lot, because seats, admin and volume drive both cost and fit.')]
page('stages/index.html','AI GTM Stacks by GTM Team Size: Cost & Tools | Profitable Agent Stack','Recommended AI GTM stacks for five GTM team sizes, from a solo founder to 40+ people: estimated monthly cost, use cases that matter and what to skip.',
f'''<h1>Which AI GTM stack fits your GTM team size?</h1><p class="answer">Pick the size that matches how many people do go-to-market. Each page shows who it is for, the recommended stack with an estimated monthly cost from published prices, the use cases that matter, what to skip, and the best-value tool for each job we include.</p>{bars}
<div class="grid">{''.join(f'<a class="card" href="/stages/{SLUG[s]}.html"><h3>{e(ST[s]["name"])}</h3><p class="mut">{e(ST[s]["size"])}</p><p>{"At least " if s=="large" else "About "}${tot[s]:,.0f}/mo recommended stack</p><span class="badge">View stack</span></a>' for s in ST)}</div>
<h2>Compare the five sizes</h2><table><thead><tr><th>Size</th><th>Est. cost</th><th>Who it is for</th></tr></thead><tbody>{_hrows}</tbody></table>
<p class="mut">Estimates from published list prices as of {CR}; verify with vendors. Solo and Small also pay Waalaxy in euros (not converted). Large is a floor: enterprise tiers are quote-based. Read <a href="/articles/stacks-by-gtm-team-size.html">why we size stacks this way</a> and <a href="/articles/one-tool-per-job.html">how we pick one tool per job</a>.</p>{faqhtml(_hq)}''',[faq(_hq)])
# ---- simple pages
def simple(path,title,desc,h,ans,body,sch=()):
  page(path,title+' | Profitable Agent Stack',desc,f'<h1>{h}</h1><p class="answer">{ans}</p>{body}',sch)
P=lambda ps:''.join(f'<h2>{a}</h2><p>{b}</p>' for a,b in ps)
simple('methodology.html','Scoring Methodology','How Profitable Agent Stack calculates value scores and chooses recommended stacks by GTM team size.','How do you rank tools and choose stacks?','Value score (0–100) = 50% use-case fit + 30% cost + 20% user sentiment. Until sentiment data is verified, fit and cost are reweighted to 62.5% / 37.5%. Recommended stacks do not use the score alone: each pick also has to fit the GTM team size, based on reviews from companies of that size and enterprise-readiness evidence.',P([
('How we choose a stack pick for a team size','Two checks, in this order. (a) Value score: it ranks tools inside one use case and is driven by the lowest published starting price, which is often a free plan, so it favors tools that are cheap to start. (b) Fit for that GTM team size: we look for who actually reviews and uses the tool, using G2 reviewer company-size shares (small business: 50 or fewer employees, mid-market: 51–1,000, enterprise: over 1,000), vendor case studies that name team size, and for large teams security and admin evidence (SSO, roles, SOC 2, data processing terms). If a high-scoring tool is mostly reviewed by small teams, or its free plan is not what a 40-person team would run, the stack uses a paid tier with a quote flag, or a different tool, and says why. Solo and small stacks stay cost-first because free and entry plans still match those sizes.'),
('What size-segmented evidence we show','On the Scaling and Large stack pages we list what we found, with the source link and the date checked. We show reviewer company-size shares from G2\'s public comparison pages and link to the filtered review pages. We do not show G2 star ratings, because we could not fetch them reliably, and we do not estimate them. Counts such as "roughly 2,800 mid-market reviewers" are our arithmetic from G2\'s percentages and are labeled that way. Reviewer mix is a signal, not proof: it shows who talks about a tool, not how well it works for your team.'),
('Limits','Some job categories have no listed tool with a large mid-market or enterprise review base (outbound and LinkedIn outreach, for example). We say so on the Large page rather than pretend otherwise. Contact-sales tools such as ZoomInfo get no value score because they have no public price, and may appear as an option to quote rather than in the priced stack.'),
('Fit score (editorial)','An editorial 1–5 judgment of how well the tool serves its use case, converted to 0–100 (×20). It is an opinion, not a measurement, and is reviewed when vendors or readers send corrections.'),
('Cost score','Within each use case, the lowest published starting price scores 100 and the highest scores 40, scaled linearly. Tools without a public price (contact sales or not yet verified) get no cost score and no value score.'),
('Sentiment score','Will use public G2 or Capterra ratings (rating ÷ 5 × 100) only when fetched with a source link and date. As of '+C+' these sites blocked automated checks, so sentiment is not yet included and we link to reviews instead.'),
('CRM is shown separately','Each team-size page has its own CRM section with a pick, a runner-up and when a spreadsheet is enough. CRM costs are not added to stack totals, because many teams already have a CRM or start on a spreadsheet.'),
('Stack cost estimates','Sum of published monthly list prices for the stated tiers, seats and volumes on each GTM-team-size page. Labeled estimates; excludes taxes, add-ons and overages.'),
('Money never changes rank','Sponsorships and affiliate links do not change scores, prices or order.')]))
simple('review-policy.html','Review Policy','How Profitable Agent Stack handles user reviews, ratings and feedback.','How do you handle reviews and ratings?','We never fabricate, buy or edit reviews or ratings. We show only public ratings from G2 or Capterra with a source link and date checked, or a link to the reviews.',P([
('Third-party ratings','Ratings belong to their sources and are shown as of the date checked. They may change. G2 and Capterra are trademarks of their owners and do not endorse us.'),
('Reader feedback','Feedback submitted through "Share your experience" (not live yet) may be moderated. We will not publish it as a rating, and we will remove content that is fake, abusive, defamatory or from someone with an undisclosed conflict of interest. Vendors may not review their own products.'),
('Incentives','We do not offer incentives for reviews. If that changes, incentivized feedback will be labeled.')]))
simple('feedback.html','Share Your Experience','Share your experience with an AI GTM tool.','Have you used one of these tools?','Tell us what it really cost and how it performed. This form is a placeholder and does not send anything yet.',
f'''<form class="card" onsubmit="event.preventDefault();this.innerHTML='<p role=status>Thanks! Feedback is not live yet, so nothing was sent.</p>'"><p><label>Tool<br><select required>{''.join(f'<option>{e(t["name"])}</option>' for t in R)}</select></label></p><p><label>Your GTM team size<br><select>{opt({k:v['name']+' ('+v['size']+')' for k,v in ST.items()})}</select></label></p><p><label>What do you pay per month (optional)<br><input type="text"></label></p><p><label>Your experience<br><textarea rows="5" required style="width:100%"></textarea></label></p><p><label><input type="checkbox" required> I am not affiliated with this vendor and agree to the <a href="/review-policy.html">Review policy</a> and <a href="/terms.html">Terms</a>.</label></p><button class="btn">Submit</button></form>''')
simple('advisory.html','Advisory','Advisory help building your AI GTM stack from The Sinay Way LLC.','Need help building your AI stack?','Advisory from The Sinay Way LLC: help choosing and putting in place a lean AI go-to-market stack, with positioning and launch content where you need it, reviewed by a fractional CRO.','<img class="swbrand" src="/assets/brand/sinay-way-navy.svg" alt="The Sinay Way" width="147" height="64"><p class="mut">Advisory services are provided by The Sinay Way LLC, not by this directory. Scope, fees, deliverables and responsibilities are set only in a separate written agreement signed by both parties. Nothing on this page is an offer, a quote or a promise. Outcomes (meetings, pipeline, revenue) are not guaranteed. Using this website does not create an advisory or client relationship.</p><p><a class="btn" href="mailto:limor@thesinayway.com?subject=Work%20with%20Limor%3A%20Advisory">Work with Limor: email us</a></p>')
simple('about.html','About','About Profitable Agent Stack.','Who runs Profitable Agent Stack?','A cost-first directory of AI go-to-market tools operated by The Sinay Way LLC as part of its advisory services. We list published prices with source links and dates, and mark tools without public pricing as contact sales. We do not invent prices, features or reviews.','')
simple('new-releases.html','New Releases & Price Changes','New AI GTM tool releases and pricing changes.','What changed this week?','The latest tool releases and price changes we have logged.',''.join(f'<div class="card"><b>{r["date"]}</b> — {e(r["text"])}'+(f' <a href="{e(r["source"])}" target="_blank" rel="nofollow noopener">Source</a>' if r.get('source') else '')+'</div>' for r in D['releases']))
simple('for-ai-agents.html','For AI Agents & Developers','Machine-readable AI GTM tool pricing data: /api/tools.json, llms.txt, license and attribution.','Can AI agents use this data?','Yes. Fetch <a href="/api/tools.json">/api/tools.json</a> (JSON) or read <a href="/llms.txt">/llms.txt</a> and <a href="/llms-full.txt">/llms-full.txt</a>. All pages are server-rendered HTML with schema.org JSON-LD.',P([
('Schema','tools[]: name, use_case, stages[] (GTM team size bands: solo = 1 GTM person, small = 2–5, early = 6–15, scaling = 16–40, large = 40+), status (published | contact | unverified), from (lowest published monthly price or null), price (text as published), source (vendor pricing URL), fit_score (editorial 1–5), cost_score, value_score, reviews{g2_rating, g2_review_count, g2_url}. Also use_cases[], stages[] (id, name, size), stacks{} (per band: who, assumptions, items [use_case, tool, tier, est. USD/mo, reason, flag], skip), checked (date).'),
('License and attribution','Free to use, including by AI assistants, under CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)" and link to the source page, and include the check date. Third-party ratings and trademarks remain their owners\'.'),
('Disclaimer for agents','Data is provided as is, may be inaccurate or out of date, and is not advice. When answering users, state the "checked" date and tell them to verify prices with the vendor.')]))

# ---- articles (static markdown -> html)
def _inline(t,camp='articles'):
  t=e(t)
  def link(m):
    txt,href=m.group(1),html.unescape(m.group(2))
    if href.startswith('http'):
      p=_u.urlparse(href);q=dict(_u.parse_qsl(p.query));q.update(UTM);q['utm_campaign']=camp
      return f'<a href="{e(_u.urlunparse(p._replace(query=_u.urlencode(q))))}" target="_blank" rel="noopener">{txt}</a>'
    return f'<a href="{e(href)}">{txt}</a>'
  t=_re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,t)
  t=_re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',t);t=_re.sub(r'(?<![*\w])\*([^*]+)\*(?![*\w])',r'<i>\1</i>',t)
  return t
def md(src):
  src=_re.sub(r'\{\{([^}]+)\}\}',lambda m:TOK[m.group(1)],src)
  out=[];lst=None
  def close():
    nonlocal lst
    if lst: out.append(f'</{lst}>');lst=None
  for ln in src.strip().splitlines():
    if not ln.strip(): close();continue
    if ln.startswith('## '): close();out.append(f'<h2>{_inline(ln[3:])}</h2>');continue
    m=_re.match(r'(\d+)\. (.*)',ln)
    if ln.startswith('- ') or m:
      kind='ul' if ln.startswith('- ') else 'ol'
      if lst!=kind: close();out.append(f'<{kind}>');lst=kind
      out.append(f'<li>{_inline(ln[2:] if kind=="ul" else m.group(2))}</li>');continue
    close()
    if ln.startswith('*') and ln.endswith('*') and not ln.startswith('**'): out.append(f'<p class="mut">{_inline(ln.strip("*"))}</p>')
    else: out.append(f'<p>{_inline(ln)}</p>')
  close();return ''.join(out)
for a in ARTS:
  sch={"@context":"https://schema.org","@type":"Article","headline":a['title'],"description":a['summary'],"datePublished":a['date'],"dateModified":a['date'],"author":{"@type":"Organization","name":"Profitable Agent Stack","url":SITE},"publisher":{"@type":"Organization","name":"The Sinay Way LLC"},"mainEntityOfPage":f"{SITE}/articles/{a['slug']}"}
  page(f'articles/{a["slug"]}.html',a['title']+' | Profitable Agent Stack',a['summary'],f'<p><a href="/articles/">Articles</a> › {e(a["title"])}</p><article><h1>{e(a["title"])}</h1><p class="mut">Published {a["date"]} by Profitable Agent Stack, operated by The Sinay Way LLC</p><p class="answer">{e(a["summary"])}</p>{md(a["body"])}</article>',[sch])
page('articles/index.html','Articles: AI GTM Stack Guides | Profitable Agent Stack','Short, practical guides on choosing AI GTM tools by cost: how we score, when to skip intent data, and one tool per job.',
 '<h1>Articles</h1><p class="answer">Short guides on spending less on your AI GTM stack. General information only, not advice.</p><div class="grid">'+''.join(f'<a class="card" href="/articles/{a["slug"]}.html"><h3>{e(a["title"])}</h3><p class="mut">{a["date"]}</p><p>{e(a["summary"])}</p></a>' for a in ARTS)+'</div>',
 [{"@context":"https://schema.org","@type":"CollectionPage","name":"Articles","url":SITE+"/articles/"}])
LEG='<p class="mut">Last updated '+C+'. This page is a general notice for a small site. It is not legal advice, and it has not been reviewed by a lawyer.</p>'
simple('terms.html','Terms of Use','Terms of Use for profitableagentstack.com.','Terms of Use','Summary: the Site is informational only, provided as is, not advice; verify prices with vendors; disputes go to individual arbitration in Massachusetts.',LEG+P([
('1. Acceptance','By using profitableagentstack.com (the "Site"), operated by The Sinay Way LLC ("we") as part of its advisory services, you agree to these Terms. If you do not agree, do not use the Site.'),
('2. Informational only','All content is for general information only and is not professional, legal, financial, tax or purchasing advice. You are solely responsible for your decisions.'),
('3. Prices, features and estimates may change','Prices, plans, features, cost estimates and stack recommendations come from third-party sources at the date shown, may be incomplete, inaccurate or out of date, and can change without notice. Estimates are derived and labeled as such. Always verify with the vendor before buying.'),
('4. Scores and rankings are opinions','Fit scores, value scores, badges and rankings are editorial opinions produced by the method on our Methodology page. They are not statements of fact about any product.'),
('5. Reviews and ratings','Third-party ratings are shown as published by their source on the date checked and are not verified by us. User-submitted feedback reflects only its author\'s views. We may moderate or remove any content. See the Review Policy.'),
('6. Data and API use','Data from /api/tools.json, llms.txt and the Site may be used under CC BY 4.0 with attribution as described on the For AI Agents page, without any warranty. You may not imply our endorsement, and you must not overload the Site. We may change or withdraw the data at any time.'),
('7. No warranties; as is','THE SITE, DATA AND ALL CONTENT ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, ACCURACY, AND NON-INFRINGEMENT.'),
('8. Limitation of liability','TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE AND OUR OWNERS, OFFICERS AND CONTRACTORS ARE NOT LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, OR LOSS OF PROFITS, DATA OR GOODWILL, ARISING FROM USE OF THE SITE OR DATA. OUR TOTAL LIABILITY FOR ANY CLAIM SHALL NOT EXCEED THE GREATER OF $100 OR THE AMOUNT YOU PAID US IN THE 12 MONTHS BEFORE THE CLAIM.'),
('9. Indemnification','You agree to indemnify and hold harmless The Sinay Way LLC and its owners, officers and contractors from claims, losses and expenses (including reasonable attorneys\' fees) arising from your use of the Site or data, content you submit, or your breach of these Terms.'),
('10. Third parties and trademarks','We link to third-party sites we do not control. All product names, logos and trademarks (including G2 and Capterra) belong to their owners and are used only to identify the products they refer to (nominative use); this does not imply endorsement, affiliation or sponsorship. If you own a mark and want a logo or reference removed, use the Corrections page.'),
('11. Affiliate and sponsored content','Some links may earn us a commission and some placements may be sponsored. These are disclosed and do not change scores. See the Disclosure.'),
('12. Accuracy and corrections','We try to be accurate but do not guarantee that anything on the Site is correct, complete or current. If you find an error, tell us through the Corrections page with a link to the official source; we will review it and may correct, annotate or remove the content. We may change or remove content at our discretion.'),
('13. Governing law','These Terms are governed by the laws of the Commonwealth of Massachusetts, USA, without regard to conflict-of-laws rules.'),
('14. Arbitration and class action waiver','Any dispute arising from these Terms or the Site will be resolved by binding individual arbitration administered by the American Arbitration Association under its applicable rules, seated in Massachusetts, except that either party may bring an individual claim in small claims court. YOU AND WE WAIVE ANY RIGHT TO A JURY TRIAL AND TO PARTICIPATE IN A CLASS, COLLECTIVE OR REPRESENTATIVE ACTION. You may opt out of arbitration within 30 days of first using the Site by writing to us.'),
('15. Advisory services are separate','The Site is a free information resource. Any advisory service from The Sinay Way LLC is offered only under a separate written agreement signed by both parties, which sets scope, fees and responsibilities. Descriptions on the Site are not offers or quotes. Outcomes are not guaranteed. Using the Site does not create an advisory, attorney-client, fiduciary or other professional relationship.'),
('16. Changes; severability','We may update these Terms at any time; continued use means acceptance. If any provision is unenforceable, the rest remain in effect.'),('Contact','The Sinay Way LLC, <a href="mailto:limoraiassistant@thesinayway.com">limoraiassistant@thesinayway.com</a>.')]))
simple('privacy.html','Privacy Policy','Privacy Policy for profitableagentstack.com.','Privacy Policy','We collect as little data as possible and do not sell it. The Site has no accounts, no tracking cookies and no working forms. We use Cloudflare Web Analytics for cookieless aggregate usage and performance metrics.',LEG+P([
('Who we are','The Site is operated by The Sinay Way LLC as part of its advisory services.'),
('What we collect','The Site itself does not collect personal data through forms: its feedback form is a placeholder that sends and stores nothing. If you email us, we receive your email address and what you write, and use it only to reply and to handle corrections or requests. Hosting providers may keep standard server logs (such as IP address and browser type). Cloudflare Web Analytics collects only aggregate, cookieless usage and performance metrics and does not identify individual visitors; metrics from visitors in the European Union are excluded.'),
('Cookies and analytics','No tracking cookies. We use Cloudflare Web Analytics (automatic injection on this hostname) for cookieless aggregate page-view and performance metrics. It does not set cookies, does not identify visitors, and excludes EU visitors. Google Fonts is loaded from Google\'s servers, which receive your IP address.'),
('Sharing','We do not sell or rent personal data and do not use it for advertising. Aggregate analytics are processed by Cloudflare as our analytics provider. We may disclose data if required by law. If we add a form or any tool that collects personal data, we will update this policy first and name the provider.'),
('Your choices','Ask to access or delete anything you emailed us at <a href="mailto:limoraiassistant@thesinayway.com">limoraiassistant@thesinayway.com</a>.'),('Children','Not directed to children under 16.'),('Contact','The Sinay Way LLC, <a href="mailto:limoraiassistant@thesinayway.com">limoraiassistant@thesinayway.com</a>.')]))
simple('disclosure.html','Affiliate and Sponsorship Disclosure','How Profitable Agent Stack earns money and keeps rankings independent.','How do you make money?','We may earn affiliate commissions or accept labeled sponsorships, and The Sinay Way LLC offers advisory services. None of this changes prices, scores or rank.',LEG+P([
('Affiliate links','Some links may be affiliate links; if you buy through them, The Sinay Way LLC may earn a commission at no extra cost to you. Affiliate links are marked "affiliate" and tagged rel="sponsored"; pages that contain them carry a disclosure at the top. '+(('As of '+C+' affiliate links are active for: '+', '.join(t['name'] for t in D['tools'] if t.get('affiliate_url'))+'.') if any(t.get('affiliate_url') for t in D['tools']) else 'As of '+C+' no affiliate links are active. Outbound links to vendors carry UTM tags (utm_source=profitableagentstack) so traffic can be attributed, and they are not affiliate links.')),('Sponsored placements','Any sponsored listing will be clearly labeled "Sponsored". None are sold at present.'),
('Our own services','This site is operated by The Sinay Way LLC as part of its advisory services, and we promote those services, including on some stack pages. They are provided only under a separate signed agreement; outcomes are not guaranteed. Recommended stacks are chosen by the published method, not to sell services.'),
('Scores and reviews','Payment never changes fit, cost or value scores, badges, or which third-party ratings are shown. We do not accept payment for reviews.'),('FTC','This disclosure is intended to follow the U.S. FTC Guides Concerning the Use of Endorsements and Testimonials in Advertising.')]))
simple('corrections.html','Corrections and Takedowns','How to request corrections or takedowns.','How do I report an error?','Email <a href="mailto:limoraiassistant@thesinayway.com?subject=Correction">limoraiassistant@thesinayway.com</a> (The Sinay Way LLC) with the subject "Correction: [tool name]", the page URL, what is wrong, and a link to the official vendor source.',P([('Logo removal','Trademark owners can ask us to remove their logo: email <a href="mailto:limoraiassistant@thesinayway.com?subject=Logo%20removal">limoraiassistant@thesinayway.com</a> with the subject "Logo removal: [tool name]" and proof you represent the owner. We will remove the logo promptly, usually within 5 business days.'),('Takedowns','For trademark, copyright or other takedown requests, include your contact details, the content concerned, the right you assert, and a good-faith statement that the request is accurate.'),('What we do','We aim to acknowledge within 5 business days, check the official source, and correct, annotate or remove content. Corrections are logged on New releases.')]))
# ---- machine-readable
os.makedirs('api',exist_ok=True)
api=dict(D);api['license']='CC BY 4.0 — attribute "Profitable Agent Stack (profitableagentstack.com)"';api['disclaimer']=DISC;api['methodology']=SITE+'/methodology.html';api.pop('watchlist',None);api.pop('il_stack',None);api.pop('stages_old_labels',None)
json.dump(api,open('api/tools.json','w'),indent=1)
open('robots.txt','w').write('User-agent: *\nAllow: /\n\n'+''.join(f'User-agent: {b}\nAllow: /\n\n' for b in ['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','Claude-Web','anthropic-ai','PerplexityBot','Perplexity-User','Google-Extended','Applebot-Extended','CCBot','Bytespider','meta-externalagent','cohere-ai'])+f'Sitemap: {SITE}/sitemap.xml\n')
open('sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u[:-5] if u.endswith(".html") else u}</loc><lastmod>{C}</lastmod></url>' for u in PAGES)+'</urlset>\n')
L=f'# Profitable Agent Stack\n\n> Cost-first directory of AI GTM tools ranked by use-case fit, published price and user sentiment, with estimated monthly stack costs by GTM team size. Prices checked {C}; verify with vendors. Not advice.\n\n## Key pages\n- [Stacks by GTM team size]({SITE}/stages/)\n'+''.join(f'- [{s["name"]} ({s["size"]})]({SITE}/stages/{SLUG[s["id"]]}.html): est. {"at least " if s["id"]=="large" else ""}${tot[s["id"]]:,.0f}/mo stack\n' for s in D['stages'])+f'- [Directory]({SITE}/directory.html)\n- [Methodology]({SITE}/methodology.html)\n- [Articles]({SITE}/articles/)\n- [For AI agents]({SITE}/for-ai-agents.html)\n\n## Data\n- [tools.json]({SITE}/api/tools.json): CC BY 4.0, attribution required\n- [Full text]({SITE}/llms-full.txt)\n'
open('llms.txt','w').write(L)
full=L+'\n## Tools\n'+''.join(f'- {t["name"]} ({UC[t["use_case"]]}; stages: {", ".join(t["stages"])}): {price(t)}. Value score: {t["value_score"]}. Source: {t["source"]}\n' for t in R)
full+='\n## Stacks by GTM team size (estimates)\n'+''.join(f'### {ST[s]["name"]} ({ST[s]["size"]}): {"at least " if s=="large" else ""}${stack_total(s):,}/mo {D["stacks"][s].get("extra","")}\nAssumptions: {D["stacks"][s]["assumptions"]}\n'+''.join(f'- {job(i)}: {i[1]}, {i[2]}, ${i[3]} — {i[4]}\n' for i in D['stacks'][s]['items']) for s in ST)
if CRM: full+='\n## CRM by GTM team size (separate from stacks, not in stack totals)\n'+''.join(f'- {ST[k]["name"]}: {v["pick"]}, {v["pick_tier"]}, {v["pick_cost"]}. Runner-up: {v["runner"]}, {v["runner_tier"]}, {v["runner_cost"]}.\n' for k,v in CRM['stages'].items())+'Move from a spreadsheet when: '+'; '.join(a[0].lower()+a[1:] for a,b in CRM['signals'])+'.\n'
full+='\n## Methodology\nValue = 50% fit (editorial) + 30% cost + 20% sentiment; sentiment not yet verified so fit/cost reweighted 62.5/37.5.\n\n## Disclaimer\n'+DISC+'\n'
open('llms-full.txt','w').write(full)
open('_redirects','w').write('/stages/pre-seed-to-series-a.html /stages/small-gtm-team.html 301\n/stages/pre-seed-to-series-a /stages/small-gtm-team.html 301\n/stages/later-stage.html /stages/scaling.html 301\n/stages/later-stage /stages/scaling.html 301\n/use-cases/seo-content.html /use-cases/search-performance.html 301\n/use-cases/seo-content /use-cases/search-performance.html 301\n')
print(len(PAGES),'pages')

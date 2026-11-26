#!/usr/bin/env python3
"""Build static site from tools.json (source of truth). Run: python3 build.py"""
import json,os,html,shutil,glob,re
D=json.load(open('tools.json'));C=D['checked'];SITE='https://profitableagentstack.com'
UC={u['id']:u['name'] for u in D['use_cases']};ST={s['id']:s for s in D['stages']};T={t['name']:t for t in D['tools']}
e=html.escape
_re=re
def _slug(n): return _re.sub(r'[^a-z0-9]+','-',n.lower()).strip('-')
# ---- reviews: merge /workspace/pas-ops/reviews/batch*.json into content/reviews.json (keyed by tool id)
# Future batches drop in as batchN.json and are merged here (newer date_checked wins).
SENT_PRIOR=4.3; SENT_M=50
SENT_LO,SENT_HI=3.0,5.0  # map 3.0->0, 5.0->100, clipped
SEGMENT_FOR_SIZE={'solo':'small','small':'small','early':'mid','scaling':'mid','large':'enterprise'}
REVIEW_ALIASES={'artisan (ai sdr)':'artisan','surfer (surferseo)':'surfer','surfer seo':'surfer'}
# Proxy listings: show the rating, but label the actual G2 card (names taken from the batch notes).
PROXY_LABELS={
  'zoominfo':'G2 rating for GTM Workspace powered by ZoomInfo',
  '6sense-bdr-agent':'G2 rating for 6sense Revenue Marketing',
  'qualified':'G2 rating for Qualified',
  'ahrefs-free':'G2 rating for Ahrefs',
  'apollo-built-in-crm':'G2 rating for Apollo (same product listing)',
}
BATCH_DIR='/workspace/pas-ops/reviews'; REVIEWS_CANON='content/reviews.json'
def _is_product_url(url):
  return bool(url) and '/products/' in url and '/search?' not in url
def _url_uncertain(rec):
  return 'slug not confirmed' in (rec.get('notes') or '').lower()
def _tid_from_batch_name(name, valid):
  key=name.strip().lower()
  if key in REVIEW_ALIASES: return REVIEW_ALIASES[key]
  if key in valid: return key
  s=_slug(name)
  if s in valid: return s
  s=_slug(_re.sub(r'\s*\([^)]*\)\s*',' ',name))
  return s if s in valid else None
def _label_for(tid, default='G2'):
  return PROXY_LABELS.get(tid, default)
def merge_reviews():
  valid={_slug(t['name']):t['name'] for t in D['tools']}
  canon={'prior':SENT_PRIOR,'prior_weight':SENT_M,'rating_map':'3.0->0, 5.0->100, clipped','tools':{}}
  if os.path.exists(REVIEWS_CANON):
    prev=json.load(open(REVIEWS_CANON,encoding='utf-8'));canon['tools']=prev.get('tools') or {}
  unmatched=[]
  if os.path.isdir(BATCH_DIR):
    for path in sorted(glob.glob(os.path.join(BATCH_DIR,'batch*.json'))):
      for rec in json.load(open(path,encoding='utf-8')):
        tid=_tid_from_batch_name(rec.get('tool',''),valid)
        if not tid:
          unmatched.append((os.path.basename(path),rec.get('tool')));continue
        url=rec.get('url') or None
        uncertain=_url_uncertain(rec)
        product=_is_product_url(url) and not uncertain
        # Only fall back to a G2 search URL when we have a rating but no confirmed product page (e.g. Artisan).
        # Tools with rating null and no URL stay without a link (no listing found).
        if rec.get('rating') is not None and not product:
          q='Artisan+AI+SDR' if tid=='artisan' else valid[tid].replace(' ','+')
          url=url or f'https://www.g2.com/search?query={q}'
          if uncertain:
            q='Artisan+AI+SDR' if tid=='artisan' else valid[tid].replace(' ','+')
            url=f'https://www.g2.com/search?query={q}'
            product=False
        entry={'id':tid,'name':valid[tid],'source':'g2','source_label':_label_for(tid),'url':url,'url_is_product':bool(product),
               'rating':rec.get('rating'),'review_count':rec.get('review_count'),
               'segment_pct':rec.get('segment_pct') or {'small':None,'mid':None,'enterprise':None},
               'segment_rating':rec.get('segment_rating') or {'small':None,'mid':None,'enterprise':None},
               'date_checked':rec.get('date_checked'),'notes':rec.get('notes') or '','batch':os.path.basename(path)}
        old=canon['tools'].get(tid)
        if old and old.get('date_checked') and entry.get('date_checked') and old['date_checked']>entry['date_checked']:
          continue
        canon['tools'][tid]=entry
  # Apollo (built-in CRM) shares Apollo's G2 product listing; reuse rating/count and say so.
  if 'apollo' in canon['tools'] and 'apollo-built-in-crm' in valid:
    src=canon['tools']['apollo']
    if src.get('rating') is not None:
      crm=dict(src)
      crm['id']='apollo-built-in-crm'
      crm['name']=valid['apollo-built-in-crm']
      crm['source_label']=_label_for('apollo-built-in-crm')
      extra="Apollo (built-in CRM) reuses Apollo's G2 rating and review count because they share the same G2 product listing."
      notes=src.get('notes') or ''
      crm['notes']=(notes+' ' if notes else '')+extra
      crm['batch']=src.get('batch','')+' + apollo-crm-reuse'
      old=canon['tools'].get('apollo-built-in-crm')
      if not (old and old.get('date_checked') and crm.get('date_checked') and old['date_checked']>crm['date_checked']):
        canon['tools']['apollo-built-in-crm']=crm
  dates=[x['date_checked'] for x in canon['tools'].values() if x.get('date_checked')]
  canon['checked']=max(dates) if dates else C
  os.makedirs(os.path.dirname(REVIEWS_CANON) or '.',exist_ok=True)
  json.dump(canon,open(REVIEWS_CANON,'w',encoding='utf-8'),indent=2,ensure_ascii=False);open(REVIEWS_CANON,'a',encoding='utf-8').write('\n')
  if unmatched:
    print('Unmatched review records:', unmatched)
  return canon
REV=merge_reviews()
def _bayes(rating,n,prior=SENT_PRIOR,m=SENT_M):
  return (m*prior+n*rating)/(m+n)
def _sentiment_from(rating,n):
  if rating is None or n is None: return None
  return round(max(0,min(100,(_bayes(rating,n)-SENT_LO)/(SENT_HI-SENT_LO)*100)))
def sentiment_score(t, segment=None):
  """Category-wide sentiment uses the overall G2 rating. If a segment is given and a matching
  segment rating exists, use that rating (and segment share of reviews as the count when published).
  Stack size mapping: solo/small->small, early/scaling->mid, large->enterprise."""
  rec=REV['tools'].get(_slug(t['name']))
  if not rec or rec.get('rating') is None or rec.get('review_count') is None: return None
  rating,n=rec['rating'],rec['review_count']
  if segment:
    key=SEGMENT_FOR_SIZE.get(segment,segment)
    sr=(rec.get('segment_rating') or {}).get(key)
    if sr is not None:
      rating=sr
      pct=(rec.get('segment_pct') or {}).get(key)
      if pct is not None: n=max(1,round(n*pct/100.0))
  return _sentiment_from(rating,n)
# ---- scoring: value = 0.5 fit + 0.3 cost + 0.2 sentiment when review data exists;
# sentiment missing -> reweight fit .625 / cost .375 and label "no review data yet".
# Contact-sales / no public price: no cost score and no value score (sentiment may still be shown).
def cost_score(t):
  if t['from'] is None: return None
  peers=[x['from'] for x in D['tools'] if x['use_case']==t['use_case'] and x['from'] is not None]
  lo,hi=min(peers),max(peers)
  return 100 if hi==lo else round(100-60*(t['from']-lo)/(hi-lo))
for t in D['tools']:
  rec=REV['tools'].get(_slug(t['name']))
  r=dict(t.get('reviews') or {})
  if rec and rec.get('rating') is not None:
    r.update({'g2_rating':rec['rating'],'g2_review_count':rec['review_count'],'g2_url':rec['url'],
              'url_is_product':rec.get('url_is_product'),'date_checked':rec.get('date_checked'),
              'source':rec.get('source_label','G2'),
              'segment_pct':rec.get('segment_pct'),'segment_rating':rec.get('segment_rating')})
    if rec.get('notes'): r['note']=rec['notes']
  else:
    # Do not surface undated ratings from tools.json until a dated batch confirms them.
    r['g2_rating']=None; r['g2_review_count']=None; r.pop('date_checked',None); r.pop('source',None)
    r['url_is_product']=_is_product_url(r.get('g2_url'))
  t['reviews']=r
  f=t['fit_score']*20;c=cost_score(t);s=sentiment_score(t)
  t['cost_score']=c; t['sentiment_score']=s; t['has_review_data']=s is not None
  if c is None: t['value_score']=None
  elif s is not None: t['value_score']=round(.5*f+.3*c+.2*s)
  else: t['value_score']=round(.625*f+.375*c)
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
NAV=[('/directory','Directory'),('/methodology','Methodology'),('/new-releases','New'),('/for-ai-agents','For AI Agents'),('/articles/','Articles'),('/advisory','Advisory')]
DISC=f'Profitable Agent Stack is for general information only, provided "as is" without warranties. Prices, plans, features and review data change often and may be inaccurate or out of date (last checked {C}); always verify with the vendor. Cost estimates and scores are editorial estimates, not advice. Nothing here is professional, legal or financial advice. Trademarks belong to their owners; listing is not endorsement. Some links may be affiliate or sponsored — see our Disclosure.'
def ld(o): return '<script type="application/ld+json">'+json.dumps(o)+'</script>'
ORG={"@context":"https://schema.org","@type":"Organization","name":"Profitable Agent Stack","url":SITE,"logo":SITE+"/assets/brand/logo-512.png","image":SITE+"/assets/brand/og-default.png","legalName":"The Sinay Way LLC","email":"limoraiassistant@thesinayway.com","description":"Cost-first directory of AI go-to-market tools with published vendor prices, source links and last-verified dates, plus recommended stacks with estimated monthly cost by GTM team size.","keywords":"AI GTM tools, AI sales tools pricing, GTM stack by team size, AI SDR pricing, cold email tools, sales tools directory","knowsAbout":["AI GTM tools","AI sales tools","Go-to-market stack","AI SDR","Cold email software","Sales intelligence","CRM","Answer engine optimization"],"contactPoint":{"@type":"ContactPoint","contactType":"customer support","email":"limoraiassistant@thesinayway.com","url":SITE+"/contact","availableLanguage":["English"]},"address":{"@type":"PostalAddress","addressRegion":"MA","addressCountry":"US"},"sameAs":["https://limorsinay.com/"],"founder":{"@type":"Person","name":"Limor Sinay","url":"https://limorsinay.com/","sameAs":["https://limorsinay.com/","https://www.linkedin.com/in/limor-sinay/"]}}
AFFNOTE='<p class="mut" role="note"><strong>Affiliate disclosure:</strong> this page includes affiliate links (marked "affiliate"). If you buy through them, The Sinay Way LLC may earn a commission at no extra cost to you. It never changes scores, prices or order. See our <a href="/disclosure">disclosure</a>.</p>'
def _he_pair(path):
  """Hebrew URL path under /il when a counterpart exists. Head-only hreflang; no visible English-site language link. Paths are canonical (no .html)."""
  m={'index.html':'/','directory.html':'/directory','methodology.html':'/methodology','privacy.html':'/privacy','disclosure.html':'/disclosure','about.html':'/about','articles/index.html':'/articles/','articles/how-companies-use-ai-for-gtm.html':'/articles/how-companies-use-ai-for-gtm','articles/smartlead-vs-instantly-vs-lemlist.html':'/articles/smartlead-vs-instantly-vs-lemlist','stages/index.html':'/stages/'}
  for slug in ('solo-founder','small-gtm-team','early-scaling','scaling','large-multi-team'):
    m['stages/'+slug+'.html']='/stages/'+slug
  return m.get(path)
def page(path,title,desc,body,schema=(),hero='',foot=None,index=True,lastmod=None):
  url=SITE+'/'+('' if path=='index.html' else path.replace('index.html',''))
  url=url[:-5] if url.endswith('.html') else url
  nav=''.join(f'<a href="{h}">{n}</a>' for h,n in NAV)
  if 'rel="sponsored' in body: body=AFFNOTE+body
  sch=''.join(ld(s) for s in schema)
  robots='' if index else '<meta name="robots" content="noindex">'
  canon=f'<link rel="canonical" href="{url}">' if index else ''
  hepath=_he_pair(path)
  hl=(f'<link rel="alternate" hreflang="en" href="{url}"><link rel="alternate" hreflang="x-default" href="{url}">'+(f'<link rel="alternate" hreflang="he" href="{SITE}/il{hepath}">' if hepath else '')) if index else ''
  out=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">{robots}{canon}{hl}
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="Profitable Agent Stack"><meta property="og:image" content="{SITE}/assets/brand/og-default.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Profitable Agent Stack logo"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/assets/brand/og-default.png"><link rel="icon" href="/assets/brand/favicon.svg" type="image/svg+xml"><link rel="icon" href="/assets/brand/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png"><meta name="theme-color" content="#262c47">
<link rel="alternate" type="application/json" href="/api/tools.json" title="Tools data"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,500&family=Cormorant+SC:wght@600&family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet"><link rel="stylesheet" href="/assets/style.css?v=4">{sch}</head>
<body><a href="#main" class="skip">Skip to content</a><header class="top"><div class="wrap"><a class="logo" href="/" aria-label="Profitable Agent Stack home"><img src="/assets/brand/pas-logo-dark.svg?v=2" alt="Profitable Agent Stack" width="209" height="57"></a><nav aria-label="Main">{nav}</nav></div></header>
{hero}<main id="main" class="wrap">{body}</main>
<footer><div class="wrap">{FCRED}{foot or ((LOGONOTE if path.startswith(('directory','stages/','use-cases/')) else '')+f'<p><strong>Disclaimer:</strong> {e(DISC)}</p><p><a href="/stages/">Stacks by GTM team size</a> · <a href="/articles/">Articles</a> · <a href="/terms.html">Terms</a> · <a href="/privacy.html">Privacy</a> · <a href="/disclosure.html">Affiliate disclosure</a> · <a href="/review-policy.html">Review policy</a> · <a href="/corrections.html">Corrections &amp; takedowns</a> · <a href="/feedback.html">Share your experience</a> · <a href="/contact.html">Contact</a> · <a href="/answers.html">Quick answers</a> · <a href="/developers.html">Developers &amp; API</a> · <a href="/llms.txt">llms.txt</a> · © 2026 The Sinay Way LLC. This site is operated by The Sinay Way LLC as part of its advisory services.</p>')}</div></footer><script src="/assets/app.js" defer></script></body></html>'''
  out=_rewrite_html_hrefs(out)
  os.makedirs(os.path.dirname(path) or '.',exist_ok=True);open(path,'w').write(out)
  if index: PAGES.append(url);LASTMOD.setdefault(url,lastmod or C)
def _canon_href(href):
  """Internal *.html hrefs -> extensionless canonical path. Keep query, hash, and off-site URLs."""
  if not href or href.startswith(('mailto:','tel:','javascript:','data:','#','//')): return href
  prefix=''
  for host in ('https://www.profitableagentstack.com','http://www.profitableagentstack.com','https://profitableagentstack.com','http://profitableagentstack.com'):
    if href.startswith(host): prefix=host; href=href[len(host):]; break
  if href.startswith('http://') or href.startswith('https://'): return prefix+href if prefix else href
  hashpart=''; query=''
  if '#' in href: href,hashpart=href.split('#',1); hashpart='#'+hashpart
  if '?' in href: href,query=href.split('?',1); query='?'+query
  if href.endswith('.html'): href=href[:-5]
  return prefix+href+query+hashpart
def _rewrite_html_hrefs(html_doc):
  return _re.sub(r'href=(["\'])([^"\']+)\1', lambda m: f'href={m.group(1)}{_canon_href(m.group(2))}{m.group(1)}', html_doc)
PAGES=[];LASTMOD={}
FCRED='<div class="fcred"><p class="cap">Profitable Agent Stack is a project of</p><a href="https://limorsinay.com/" aria-label="The Sinay Way LLC: Limor Sinay advisory (limorsinay.com)"><img src="/assets/brand/sinay-way-white.svg" alt="The Sinay Way LLC" width="152" height="88" loading="lazy"></a><p class="tag">Independent, cost-first reviews of AI GTM tools.</p></div>'
LOGONOTE='<p>Logos and trademarks belong to their owners and are used only to identify products; no endorsement implied. Owners can request removal via the <a href="/corrections.html">corrections page</a>.</p>'
def init(n): return ''.join(w[0] for w in n.replace('.',' ').split()[:2]).upper()
def price(t): return 'Contact sales' if t['status']=='contact' else t['price']
import urllib.parse as _u
UTM={'utm_source':'profitableagentstack','utm_medium':'referral'}
def tool_dest(t,camp='directory'):
  """Final vendor or affiliate URL, with PAS UTM tags."""
  aff=bool(t.get('affiliate_url'));p=_u.urlparse(t['affiliate_url'] if aff else t['homepage_url']);q=dict(_u.parse_qsl(p.query));q.update(UTM);q['utm_campaign']=camp;q['utm_content']=_slug(t['name'])
  return _u.urlunparse(p._replace(query=_u.urlencode(q))),aff
def tool_link(t,camp='directory'):
  """Outbound tool links. Affiliate clicks go through /go/{slug} so cookieless analytics can count them."""
  dest,aff=tool_dest(t,camp)
  if aff: return f'/go/{_slug(t["name"])}/','sponsored nofollow noopener',True
  return dest,'noopener',False
def write_go_pages():
  """Static /go/{slug}/ hop pages: short delay so Web Analytics can record the path, then redirect."""
  import json as _json
  for t in D['tools']:
    if not t.get('affiliate_url'): continue
    sid=_slug(t['name']); dest,_=tool_dest(t,'go'); dest_e=e(dest)
    html_doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Opening '+e(t['name'])+'</title><meta name="robots" content="noindex,nofollow"><meta http-equiv="refresh" content="1;url='+dest_e+'"></head><body><p>Opening <a href="'+dest_e+'" rel="sponsored nofollow noopener">'+e(t['name'])+'</a>.</p><script>setTimeout(function(){location.replace('+_json.dumps(dest)+')},400);</script></body></html>'
    os.makedirs('go/'+sid, exist_ok=True); open('go/'+sid+'/index.html','w').write(html_doc)
def review_html(t):
  """Rating, count, source link and date when verified; otherwise 'no review data yet'.
  'See reviews on G2' only when the URL is a confirmed product page."""
  r=t.get('reviews') or {}; url=r.get('g2_url') or ''
  if t.get('has_review_data') and r.get('g2_rating') is not None:
    n=r['g2_review_count']; ntxt=f'{n:,} review'+('' if n==1 else 's')
    src=r.get('source') or 'G2'
    label=(f"{src}: {r['g2_rating']}/5 · {ntxt} · checked {r.get('date_checked')}"
           if src.startswith('G2 rating for') else
           f"{src} {r['g2_rating']}/5 · {ntxt} · checked {r.get('date_checked')}")
    if r.get('url_is_product') and url:
      return f'<a href="{e(url)}" rel="nofollow noopener" target="_blank">{e(label)}</a>'
    if url:
      return f'{e(label)} (<a href="{e(url)}" rel="nofollow noopener" target="_blank">G2 search</a>; product page not confirmed)'
    return e(label)
  bits=['No review data yet']
  if url and _is_product_url(url):
    bits.append(f'<a href="{e(url)}" rel="nofollow noopener" target="_blank">See reviews on G2</a>')
  return ' · '.join(bits)
def review_md(t):
  r=t.get('reviews') or {}; url=r.get('g2_url') or ''
  if t.get('has_review_data') and r.get('g2_rating') is not None:
    n=r['g2_review_count']; ntxt=f'{n:,} review'+('' if n==1 else 's')
    src=r.get('source') or 'G2'
    label=(f"{src}: {r['g2_rating']}/5 · {ntxt} · checked {r.get('date_checked')}"
           if src.startswith('G2 rating for') else
           f"{src} {r['g2_rating']}/5 · {ntxt} · checked {r.get('date_checked')}")
    if r.get('url_is_product') and url: return f'[{label}]({url})'
    if url: return f'{label} ([G2 search]({url}); product page not confirmed)'
    return label
  if url and _is_product_url(url): return f'No review data yet. [See reviews on G2]({url})'
  return 'No review data yet'
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
  return f'''<article class="card" id="{_slug(t['name'])}" data-uc="{t['use_case']}" data-stages="{' '.join(t['stages'])}" data-score="{sc or 0}" data-cost="{cost}">
<div class="row">{f'<a href="{e(L[0])}" target="_blank" rel="{L[1]}"><img class="logo-img" src="{t["logo"]}" alt="{e(t["name"])} logo" width="40" height="40" loading="lazy"></a>' if t.get('logo') else ''}<div><h3 style="margin:0"><a href="{e(L[0])}" target="_blank" rel="{L[1]}" style="color:inherit;text-decoration:none">{e(t['name'])}</a>{' <span class="badge c">affiliate</span>' if L[2] else ''}</h3><span class="mut">{UC[t['use_case']]}</span></div><div style="margin-left:auto;text-align:right"><div class="score">{sc if sc is not None else '—'}</div><span class="mut">value score</span></div></div>
<p>{b}</p><p>{e(price(t))}</p><p class="mut">Fit {t['fit_score']}/5 (editorial){" · sentiment "+str(t['sentiment_score']) if t.get('has_review_data') else ''} · Fits: {', '.join(ST[s]['short'] for s in t['stages'])}</p>
<p class="mut">{review_html(t)}</p>
<p class="mut">{'Prices as of' if t.get('price_verified',True) else 'Checked'} {t.get('checked',C)}{'' if t.get('price_verified',True) else ', price could not be verified'}, verify with vendor. <a href="{t['source']}" rel="nofollow noopener" target="_blank">Pricing source</a></p></article>'''
def sw(t):
  o={"@type":"SoftwareApplication","@id":SITE+'/use-cases/'+t['use_case']+'#'+_slug(t['name']),"name":t['name'],"applicationCategory":"BusinessApplication","applicationSubCategory":UC[t['use_case']],"operatingSystem":"Web","url":t['homepage_url']}
  if t['from'] is not None and t['status']=='published': o["offers"]={"@type":"Offer","price":t['from'],"priceCurrency":"EUR" if '€' in t['price'] else "USD","description":t['price']+' (list price as of '+t.get('checked',C)+')',"url":t['source'],"validFrom":t.get('checked',C)}
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
# Price-check note stays under the hero CTAs as muted text, not a top-of-hero pill.
# Editing index.html alone is overwritten on the next python3 build.py run.
hero=f'''<section class="hero"><div class="wrap"><h1>Build your AI GTM stack for the best <span class="grad">value per dollar</span>.</h1>
<p>Scored on fit, published price and verified G2 user ratings, math shown — one tool per job, plus the use cases you can safely skip until your team is bigger. From about {TOK['cost:solo']}/mo for one person.</p>
<p><a class="btn" href="/stages/">See stacks by GTM team size</a> <a class="btn ghost" href="/directory.html">Browse all tools</a></p>
<p class="price-check">Prices checked {C} · {len(D['tools'])} tools · {len(UC)} use cases</p></div></section>'''
_uc=lambda ids:''.join(f'<a class="card" href="/use-cases/{u}.html"><h3>{UC[u]}</h3><p class="mut">{"Best value: "+best[u]["name"] if u in best else "Coming soon"}</p></a>' for u in ids)
ucc=f'<h3>Sales</h3><div class="grid">{_uc([u for u in UC if u not in MKT and u not in SEP])}</div><h3>Marketing</h3><div class="grid">{_uc([u for u in UC if u in MKT])}</div>'+(f'<h3>CRM (separate from the stack)</h3><p class="mut">Not counted in stack totals. Start on a spreadsheet and add a CRM when it fits.</p><div class="grid">{_uc([u for u in UC if u in SEP])}</div>' if SEP else '')
HQ=[('What is Profitable Agent Stack?','A value-first directory that scores AI go-to-market tools on use-case fit, published price and verified G2 user ratings (math shown), with estimated monthly stack costs by GTM team size.'),('How are the stacks grouped?','By how many people do go-to-market: solo founder (1), small GTM team (2–5), early scaling (6–15), scaling (16–40) and large / multi-team (40+).'),('Where do the prices come from?',f'From each vendor\'s own pricing page, with a source link and the date checked ({C}). Tools with no public price are marked contact sales.'),('What changed in AI GTM tool prices this week?',next((f'As of {r["date"]}: '+r['text'].replace('Weekly price check: ','',1) for r in D['releases'] if r['text'].startswith('Weekly price check')),'See New Releases & Price Changes for the latest log.')+' Full log: https://profitableagentstack.com/new-releases.html'),('Do you publish user ratings?','Yes, when we have a verified public G2 rating with a source link and the date checked. That rating feeds the 20% sentiment part of the value score, shrunk toward a neutral prior when the review count is low. Tools we have not yet checked are labeled "no review data yet" and are scored on fit and cost only. We never create reviews or ratings ourselves.')]
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
page('index.html','AI GTM Stacks Scored on Fit, Price and Verified Ratings | Profitable Agent Stack','Value-first directory of AI GTM tools scored on fit, published price and verified G2 user ratings, with estimated monthly stack costs by GTM team size, from solo founders to 40+ person teams.',
f'''<h2>What does an AI GTM stack cost, by GTM team size?</h2><p class="answer">Based on published list prices, our recommended stacks are estimated at about {TOK['cost:solo']}/mo (+€19) for a solo founder, ${tot['small']:,.0f}/mo (+€38) for a 2–5 person team, ${tot['early']:,.0f}/mo for 6–15, ${tot['scaling']:,.0f}/mo for 16–40, and at least ${tot['large']:,.0f}/mo for 40+. Estimates only; each page shows the math.</p>{bars}
<section class="card feat" style="margin:24px 0"><h2 style="margin-top:0">Find the stack for your GTM team size</h2><p>Five sizes, from 1 person to 40+. Each page shows who it is for, the recommended stack and monthly cost, the use cases that matter, and the ones to skip.</p><a class="btn ghost" href="/stages/">See stacks by GTM team size</a></section>
<h2>How we keep the bill low</h2><div class="grid"><div class="card"><h3>One tool per job</h3><p class="mut">No paid overlap, and every pick comes with a reason. <a href="/articles/one-tool-per-job.html">Read why</a>.</p></div><div class="card"><h3>Real, dated prices</h3><p class="mut">Each price links to the vendor page and shows the date checked. If we could not verify it, we say so.</p></div><div class="card"><h3>Skip what you do not need yet</h3><p class="mut">Intent data and AI SDRs are not for everyone. <a href="/articles/when-to-skip-intent-data.html">See when to skip them</a>.</p></div></div>
<section class="card feat" style="margin:24px 0"><h2 style="margin-top:0">How companies use AI for GTM</h2><p>Sourced stories from named companies, with the tools they used and the results they published, plus a side-by-side of Smartlead, Instantly and lemlist.</p><p><a class="btn ghost" href="/articles/how-companies-use-ai-for-gtm">Read the case studies</a> <a class="btn ghost" href="/articles/smartlead-vs-instantly-vs-lemlist">Compare outbound tools</a></p></section>
<h2>Which tool should I use for each use case?</h2>{ucc}
<h2>From the articles</h2><div class="grid">{artcards}</div><p><a href="/articles/">All articles</a></p>{faqhtml(HQ)}''',
[ORG,{"@context":"https://schema.org","@type":"WebSite","name":"Profitable Agent Stack","url":SITE},faq(HQ)],hero,lastmod='2026-11-26')
# ---- directory
opt=lambda d:''.join(f'<option value="{k}">{v}</option>' for k,v in d.items())
R=rank(D['tools'])
_nv=[t['name'] for t in D['tools'] if t.get('checked')!=C]
DQ=[('How many AI GTM tools does the directory list?',f'{len(R)} tools across {len(UC)} use cases, as of {C}. Each card links to the vendor pricing page and shows the date its price was last checked.'),('When were prices last checked?',f'Our weekly price check ran on {C}: {len(R)-len(_nv)} of {len(R)} tools were re-verified on the vendor pricing page that day.'+(f' Not re-verified this week (page blocked or prices render client-side), so the last verified price and date are shown: {", ".join(_nv)}.' if _nv else ''))]
page('directory.html','AI GTM Tools Directory: Filter by GTM Team Size & Use Case | Profitable Agent Stack',f'All {len(R)} AI GTM tools with published prices, value scores and verified G2 ratings when we have them. Filter by GTM team size and use case, sort by value or cost.',
f'''<h1>Which AI GTM tool is the best value?</h1><p class="answer">This directory ranks {len(R)} tools by value score (use-case fit, published cost, and verified G2 ratings when we have them; math on the methodology page). Tools without a dated G2 check are labeled "no review data yet" and are scored on fit and cost only. Filter by GTM team size or use case, or sort by cost. <a href="/methodology">How scoring works</a>. New guides: <a href="/articles/how-companies-use-ai-for-gtm">How companies use AI for GTM</a> · <a href="/articles/smartlead-vs-instantly-vs-lemlist">Smartlead vs Instantly vs lemlist</a>.</p>
<div class="filters"><label class="sr">GTM team size <select data-filter="stage"><option value="">All sizes</option>{opt({k:v['name']+' ('+v['size']+')' for k,v in ST.items()})}</select></label><label>Use case <select data-filter="uc"><option value="">All use cases</option>{opt(UC)}</select></label><label>Sort <select id="sort"><option value="value">Best value</option><option value="asc">Cost: low to high</option><option value="desc">Cost: high to low</option></select></label></div>
<div class="grid" id="list">{''.join(card(t) for t in R)}</div>{faqhtml(DQ)}''',[itemlist(R,'AI GTM tools ranked by value'),faq(DQ)],lastmod='2026-11-26')
# ---- use cases
for u,n in UC.items():
  ts=rank([t for t in D['tools'] if t['use_case']==u]);b=best.get(u)
  qs=[(f'What is the best value tool for {lc(n)}?',(f'{b["name"]} has the highest value score ({b["value_score"]}) among tools we list, priced at: {b["price"]}. Verify with the vendor.' if b else 'We have not yet listed tools with published prices for this use case.')),(f'How much do {lc(n)} tools cost?','Published entry prices for listed tools: '+('; '.join(f'{t["name"]}: {price(t)}' for t in ts) if ts else 'none listed yet')+f'. Prices as of {C}.')]
  _ps=[t for t in ts if t['status']=='published' and t['from'] is not None and '€' not in t['price']]
  if _ps:
    _lo=min(t['from'] for t in _ps);_ch=[t for t in _ps if t['from']==_lo]
    qs.append((f'What is the cheapest {lc(n)} tool?','By published entry price, '+' and '.join(t['name'] for t in _ch)+(' start free' if _lo==0 else f' start at ${_lo:,g}/mo')+'. Free plans and entry tiers have limits, so check them against your volume. '+f'List prices as of {C}; verify with the vendor.'))
  UC_GUIDE={
    'positioning': '<section class="card" style="margin:0 0 24px"><h2 style="margin-top:0">Positioning work before you buy a tool</h2><p>This use case is for message and offer research: who you sell to, why they buy, and the words that sound like them. We have not yet listed a dedicated positioning tool with a published price, so this page is a buying guide rather than a ranked list. For most seed and Series A teams, a shared spreadsheet, recorded customer calls and win/loss notes are enough.</p><p>Consider a paid research workspace later if interviews are piling up unanalyzed, several people need to share the same evidence, or you are preparing a category or pricing change. Until then, put the time into conversations, not software.</p><h2>Related reading</h2><ul><li><a href="/articles/how-companies-use-ai-for-gtm">How real companies use AI for GTM</a> — sourced examples, with links to the original write-ups.</li><li><a href="/use-cases/landing-pages">Landing pages and sites</a> and <a href="/use-cases/content-optimization">Content optimization</a> — where positioning usually shows up in the stack.</li><li><a href="/advisory">Advisory</a> if you want help on positioning as part of a US go-to-market motion (separate from this directory; scope and fees only in a signed agreement).</li></ul></section>',
    'content-optimization': '<section class="card" style="margin:0 0 24px"><h2 style="margin-top:0">When a content-optimization tool is worth it</h2><p>These tools help you brief, draft or revise pages so they have a better chance of ranking or being cited. They do not replace a clear offer or a page that answers the question a buyer is actually asking. A 2–5 person GTM team can often start with a search-performance tool they already pay for, a style guide, and reviews from customers, then add a dedicated optimizer when the writing volume justifies another seat.</p><p>We currently list tools with published prices below. Compare them against <a href="/use-cases/search-performance">search performance</a> and <a href="/use-cases/aeo">answer engine optimization (AEO)</a> so you do not pay twice for the same job. See also <a href="/articles/when-to-add-aeo">when to add AEO</a>.</p></section>'
  }
  xtra=UC_GUIDE.get(u,'')
  if u in SEP and CRM:
    qs.append(('When should I move from a spreadsheet to a CRM?','When a second person works the pipeline, live deals pass about 20–30, you copy sequencer replies by hand, email and LinkedIn reach the same people, investor pipeline reporting takes more than about an hour a month, or inbound leads or a first sales hire arrive.'))
    xtra=f'<p>{e(CRM["intro"])}</p><h2>Our CRM pick by GTM team size</h2><table><thead><tr><th>Size</th><th>Pick</th><th>Est. $/mo</th><th>Runner-up</th><th>Est. $/mo</th></tr></thead><tbody>'+''.join(f'<tr><td><a href="/stages/{SLUG[k]}.html#crm">{e(ST[k]["name"])}</a><br><span class="mut">{e(ST[k]["size"])}</span></td><td><b>{e(v["pick"])}</b><br><span class="mut">{e(v["pick_tier"])}</span></td><td>{e(v["pick_cost"])}</td><td>{e(v["runner"])}<br><span class="mut">{e(v["runner_tier"])}</span></td><td>{e(v["runner_cost"])}</td></tr>' for k,v in CRM['stages'].items())+f'</tbody></table><p class="mut">Not included in recommended stack totals. List prices as of {CRM["checked"]}; verify with the vendor. The value score below ranks entry price and fit across all CRMs; the table above weighs fit for each team size.</p><h2>When a spreadsheet is enough</h2><p>A shared sheet is a real CRM for one person with a small, warm pipeline. Add a CRM when one of these is true:</p>'+crm_signals()+'<h2>All CRMs we list</h2>'
  page(f'use-cases/{u}.html',f'Best {n} Tools by Cost & Value (2026) | Profitable Agent Stack',f'{n}: AI GTM tools ranked by value score with published prices checked {C}.',
  f'<h1>{e(qs[0][0][0].upper()+qs[0][0][1:])}</h1><p class="answer">{e(qs[0][1])}</p>{xtra}<div class="grid" id="list">{"".join(card(t,"use-case") for t in ts) or "<p>No tools listed yet. <a href=/corrections>Suggest one</a>.</p>"}</div>{faqhtml(qs)}',[itemlist(ts,n),faq(qs)],lastmod='2026-11-26' if u in UC_GUIDE else None)
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
    ev=f'<h2>{e(S.get("evidence_title","What we found when checking enterprise readiness"))} (as of {S["evidence_date"]})</h2><p class="mut">Security and plan statements come from each vendor\'s own pages and are vendor claims; reviewer company-size shares come from G2\'s public comparison pages . Overall G2 star ratings and review counts, when we have a dated check, appear on each tool card and feed the sentiment part of the value score. Company-size segment ratings are not in the file yet (G2 product pages were blocked). Everything may change; confirm security, SSO and compliance in writing before buying. This is not legal or compliance advice.</p><ul>'+''.join(f'<li><b>{e(a)}.</b> {e(b)} <a href="{e(c)}" rel="nofollow noopener" target="_blank">Source</a></li>' for a,b,c in S['evidence'])+'</ul>'
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
def simple(path,title,desc,h,ans,body,sch=(),lastmod=None):
  page(path,title+' | Profitable Agent Stack',desc,f'<h1>{h}</h1><p class="answer">{ans}</p>{body}',sch,lastmod=lastmod)
P=lambda ps:''.join(f'<h2>{a}</h2><p>{b}</p>' for a,b in ps)
simple('methodology.html','Scoring Methodology','How Profitable Agent Stack calculates value scores and chooses recommended stacks by GTM team size.','How do you rank tools and choose stacks?','Value score (0–100) = 50% use-case fit + 30% cost + 20% user sentiment, when a verified G2 rating with a source link and date is on file. Tools without review data keep a 62.5% / 37.5% fit/cost reweight and are labeled "no review data yet." Contact-sales tools still get no cost score and no value score. Recommended stacks do not use the score alone: each pick also has to fit the GTM team size, based on reviews from companies of that size and enterprise-readiness evidence.',P([
('How we choose a stack pick for a team size','Two checks, in this order. (a) Value score: it ranks tools inside one use case and is driven by the lowest published starting price, which is often a free plan, so it favors tools that are cheap to start. (b) Fit for that GTM team size: we look for who actually reviews and uses the tool, using G2 reviewer company-size shares (small business: 50 or fewer employees, mid-market: 51–1,000, enterprise: over 1,000), vendor case studies that name team size, and for large teams security and admin evidence (SSO, roles, SOC 2, data processing terms). If a high-scoring tool is mostly reviewed by small teams, or its free plan is not what a 40-person team would run, the stack uses a paid tier with a quote flag, or a different tool, and says why. Solo and small stacks stay cost-first because free and entry plans still match those sizes.'),
('What size-segmented evidence we show','On the Scaling and Large stack pages we list what we found, with the source link and the date checked. We show reviewer company-size shares from G2\'s public comparison pages and link to the filtered review pages. Overall G2 star ratings and review counts now appear on tool cards when we have a dated check (taken from G2 search-result cards, because product pages were blocked). Company-size segment ratings are not in the file yet; when they are, stack pages will prefer the segment that matches the team size (see Sentiment score). Counts such as "roughly 2,800 mid-market reviewers" are our arithmetic from G2\'s percentages and are labeled that way. Reviewer mix is a signal, not proof: it shows who talks about a tool, not how well it works for your team.'),
('Limits','Some job categories have no listed tool with a large mid-market or enterprise review base (outbound and LinkedIn outreach, for example). We say so on the Large page rather than pretend otherwise. Contact-sales tools such as ZoomInfo get no value score because they have no public price, and may appear as an option to quote rather than in the priced stack.'),
('Fit score (editorial)','An editorial 1–5 judgment of how well the tool serves its use case, converted to 0–100 (×20). It is an opinion, not a measurement, and is reviewed when vendors or readers send corrections.'),
('Cost score','Within each use case, the lowest published starting price scores 100 and the highest scores 40, scaled linearly. Tools without a public price (contact sales or not yet verified) get no cost score and no value score.'),
('Sentiment score','When we have a verified public G2 rating (source link and date checked), we convert it to a 0–100 sentiment score with a confidence shrink for low review counts, then give it 20% of the value score.</p><p>1. Bayesian average: (50 × 4.3 + review count × rating) / (50 + review count). The 4.3 prior is a typical G2 B2B rating; 50 reviews is the weight of that prior. A tool with few reviews is pulled toward 4.3; a tool with thousands of reviews stays close to its raw rating.</p><p>2. Map 3.0 → 0 and 5.0 → 100, and clip to that range: sentiment = clip((Bayesian average − 3.0) / 2.0 × 100, 0, 100), then round to an integer.</p><p>Example: Instantly\'s G2 rating is 4.8 from 4,167 reviews (checked 2026-11-23). Bayesian average = (50 × 4.3 + 4,167 × 4.8) / (50 + 4,167) = 20,216.6 / 4,217 = 4.794. Sentiment = (4.794 − 3.0) / 2.0 × 100 = 90 (rounded). Fit is 5/5 → 100 and the cost score is 84, so value = 0.5×100 + 0.3×84 + 0.2×90 = 93.</p><p>Capterra figures, when we have them, stay in the notes for context and are not used in the score. We never invent ratings.</p><p>When reviewer-segment ratings exist (small business: 50 or fewer employees, mid-market: 51–1,000, enterprise: over 1,000), the category-wide value score still uses the overall rating. For a stack at a given team size we prefer the matching segment rating (solo and small → small business, early and scaling → mid-market, large → enterprise), using that segment\'s share of reviews as the count when a share is published. If a segment rating is missing, we fall back to the overall rating. Segment ratings are not in the current data (G2 product pages were blocked; TrustRadius install figures are not used as review segments), so every score today uses the overall rating.</p><p>Tools without review data are labeled "no review data yet" and keep the 62.5% fit / 37.5% cost reweight. Contact-sales tools can still show a rating, but they get no cost score and therefore no value score.'),
('CRM is shown separately','Each team-size page has its own CRM section with a pick, a runner-up and when a spreadsheet is enough. CRM costs are not added to stack totals, because many teams already have a CRM or start on a spreadsheet.'),
('Stack cost estimates','Sum of published monthly list prices for the stated tiers, seats and volumes on each GTM-team-size page. Labeled estimates; excludes taxes, add-ons and overages.'),
('Money never changes rank','Sponsorships and affiliate links do not change scores, prices or order.')]))
simple('review-policy.html','Review Policy','How Profitable Agent Stack handles user reviews, ratings and feedback.','How do you handle reviews and ratings?','We never fabricate, buy or edit reviews or ratings. We show only public ratings from G2 or Capterra with a source link and date checked, or a link to the reviews.',P([
('Third-party ratings','Ratings belong to their sources and are shown as of the date checked. They may change. G2 and Capterra are trademarks of their owners and do not endorse us.'),
('Reader feedback','Feedback submitted through "Share your experience" (not live yet) may be moderated. We will not publish it as a rating, and we will remove content that is fake, abusive, defamatory or from someone with an undisclosed conflict of interest. Vendors may not review their own products.'),
('Incentives','We do not offer incentives for reviews. If that changes, incentivized feedback will be labeled.')]))
simple('feedback.html','Share Your Experience','Share your experience with an AI GTM tool.','Have you used one of these tools?','Tell us what it really cost and how it performed. This form is a placeholder and does not send anything yet.',
f'''<form class="card" onsubmit="event.preventDefault();this.innerHTML='<p role=status>Thanks! Feedback is not live yet, so nothing was sent.</p>'"><p><label>Tool<br><select required>{''.join(f'<option>{e(t["name"])}</option>' for t in R)}</select></label></p><p><label>Your GTM team size<br><select>{opt({k:v['name']+' ('+v['size']+')' for k,v in ST.items()})}</select></label></p><p><label>What do you pay per month (optional)<br><input type="text"></label></p><p><label>Your experience<br><textarea rows="5" required style="width:100%"></textarea></label></p><p><label><input type="checkbox" required> I am not affiliated with this vendor and agree to the <a href="/review-policy.html">Review policy</a> and <a href="/terms.html">Terms</a>.</label></p><button class="btn">Submit</button></form>''')
simple('advisory.html','Advisory','Advisory help building your AI GTM stack from The Sinay Way LLC.','Need help building your AI stack?','Advisory from The Sinay Way LLC: help choosing and putting in place a lean AI go-to-market stack, with positioning and launch content where you need it, reviewed by a fractional CRO.','<a href="https://limorsinay.com/" aria-label="The Sinay Way: Limor Sinay advisory"><img class="swbrand" src="/assets/brand/sinay-way-navy.svg" alt="The Sinay Way" width="147" height="64"></a><section class="bio" aria-labelledby="about-limor"><picture><source srcset="/assets/limor-sinay.webp" type="image/webp"><img src="/assets/limor-sinay.jpg" alt="Limor Sinay" width="480" height="600" loading="lazy" decoding="async"></picture><div><h2 id="about-limor">About Limor Sinay</h2><p>Limor Sinay is a fractional CRO and GTM advisor. She works through The Sinay Way LLC, helping seed and Series A companies build the go-to-market motion they need, primarily to enter the US market.</p><ul><li><strong>20+ years</strong> building GTM, pre-sales, and revenue teams</li><li><strong>100+ employees</strong> hired, led, and developed across B2B SaaS</li><li><strong>US launches</strong> from first ICP to repeatable pipeline</li><li>Organizes the <strong>AI Tinkerers GTM chapter in Boston</strong>, where founders and GTM leaders test what actually works when AI enters the revenue motion</li></ul><blockquote><p>“Limor is a true go-to-market leader who helps broaden my strategy and scale IO River. She consistently brings creative and innovative ideas that challenge me as a CEO and push me to explore better alternatives. I’m grateful to have her on my advisory board.”</p><cite>Edward Tsinovoi, Co-Founder &amp; CEO, IO River</cite></blockquote><p><a href="https://limorsinay.com/">Learn more at limorsinay.com</a> · <a href="https://www.linkedin.com/in/limor-sinay/" target="_blank" rel="noopener">Connect on LinkedIn</a></p></div></section><p class="mut">Advisory services are provided by The Sinay Way LLC, not by this directory. Scope, fees, deliverables and responsibilities are set only in a separate written agreement signed by both parties. Nothing on this page is an offer, a quote or a promise. Outcomes (meetings, pipeline, revenue) are not guaranteed. Using this website does not create an advisory or client relationship.</p><p><a class="btn" href="https://calendar.google.com/appointments/schedules/AcZssZ12VAju-VteCC4l7yZJ7bBRh07uePkQrLDxnDTNclKvR0cgpmTyUq1-DrfmGVGyEKeolg0RRC2G" target="_blank" rel="noopener">Book A Call</a></p><p class="mut">or email <a href="mailto:limor@thesinayway.com?subject=Book%20a%20call">limor@thesinayway.com</a></p>',[{"@context":"https://schema.org","@type":"Person","name":"Limor Sinay","jobTitle":"Fractional CRO & GTM Advisor","url":"https://limorsinay.com/","image":SITE+"/assets/limor-sinay.jpg","sameAs":["https://limorsinay.com/","https://www.linkedin.com/in/limor-sinay/"],"worksFor":{"@type":"Organization","name":"The Sinay Way LLC"}}])
simple('about.html','About','About Profitable Agent Stack, a cost-first directory of AI go-to-market tools operated by The Sinay Way LLC.','Who runs Profitable Agent Stack?','A cost-first directory of AI go-to-market tools operated by The Sinay Way LLC as part of its advisory services. We list published prices with source links and dates, and mark tools without public pricing as contact sales. We do not invent prices, features or reviews.',
'<h2>Who this directory is for</h2><p>Founders and GTM operators who need to choose AI sales and marketing tools without overspending. It is not a paid ranking, and it is not a substitute for vendor docs or your own trial.</p><h2>What you can do here</h2><ul><li><a href="/directory">Browse every tool we list</a>, with published prices, the date we last checked them, and a value score when we can compute one.</li><li><a href="/stages/">See a recommended stack by GTM team size</a>, from a solo founder to a 40+ person team, with an estimated monthly cost.</li><li>Read short guides, including <a href="/articles/how-companies-use-ai-for-gtm">how companies use AI for GTM</a> and a <a href="/articles/smartlead-vs-instantly-vs-lemlist">comparison of Smartlead, Instantly and lemlist</a>.</li><li><a href="/methodology">Read how scoring works</a> — use-case fit, published cost, and verified G2 ratings when we have them.</li></ul><h2>Editorial rules</h2><p>We list published prices with a source link and a check date. Tools without public pricing are marked contact sales. Some links are affiliates; that never changes scores, prices or order. See the <a href="/disclosure">disclosure</a>.</p><h2>Who operates the site</h2><p>The site is operated by The Sinay Way LLC as part of its advisory services. <a href="/advisory">Advisory help</a> is a separate engagement, with scope and fees only in a signed agreement. Outcomes are not guaranteed.</p><p><a href="/contact">Contact</a>. Corrections and takedowns are on the <a href="/corrections">corrections page</a>.</p>',lastmod='2026-11-26')
simple('new-releases.html','New Releases & Price Changes','New AI GTM tool releases and pricing changes, logged weekly with sources.','What changed this week?',f'Updated {C}. The latest AI GTM tool releases and price changes we have logged, newest first, each with a source link.',''.join(f'<div class="card"><b>{r["date"]}</b> — {e(r["text"])}'+(f' <a href="{e(r["source"])}" target="_blank" rel="nofollow noopener">Source</a>' if r.get('source') else '')+'</div>' for r in D['releases']),sch=[{"@context":"https://schema.org","@type":"CollectionPage","name":"New Releases & Price Changes","url":SITE+"/new-releases.html","dateModified":C,"isPartOf":{"@type":"WebSite","name":"Profitable Agent Stack","url":SITE},"mainEntity":{"@type":"ItemList","itemListOrder":"https://schema.org/ItemListOrderDescending","itemListElement":[{"@type":"ListItem","position":k+1,"name":r['text'][:150],**({"url":r['source']} if r.get('source') else {})} for k,r in enumerate(D['releases'][:20])]}}])
simple('for-ai-agents.html','For AI Agents & Developers','Machine-readable AI GTM tool pricing data: /api/tools.json, llms.txt, license and attribution.','Can AI agents use this data?','Yes. Use the versioned JSON API at <a href="/api/v1/index.json">/api/v1</a> (OpenAPI 3.1: <a href="/openapi.json">/openapi.json</a>), the read-only MCP server at <code>https://profitableagentstack.com/mcp</code>, the Markdown version of any page (add <code>.md</code> or send <code>Accept: text/markdown</code>), or the original <a href="/api/tools.json">/api/tools.json</a>. Docs and examples: <a href="/developers.html">Developers</a>. Or read <a href="/llms.txt">/llms.txt</a> and <a href="/llms-full.txt">/llms-full.txt</a>. All pages are server-rendered HTML with schema.org JSON-LD.',P([
('Schema','tools[]: name, use_case, stages[] (GTM team size bands: solo = 1 GTM person, small = 2–5, early = 6–15, scaling = 16–40, large = 40+), status (published | contact | unverified), from (lowest published monthly price or null), price (text as published), source (vendor pricing URL), fit_score (editorial 1–5), cost_score, sentiment_score, value_score, reviews{g2_rating, g2_review_count, g2_url, date_checked, source}. Tools without a dated G2 check are labeled no review data yet. Also use_cases[], stages[] (id, name, size), stacks{} (per band: who, assumptions, items [use_case, tool, tier, est. USD/mo, reason, flag], skip), checked (date).'),
('License and attribution','Free to use, including by AI assistants, under CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)" and link to the source page, and include the check date. Third-party ratings and trademarks remain their owners\'.'),
('Disclaimer for agents','Data is provided as is, may be inaccurate or out of date, and is not advice. When answering users, state the "checked" date and tell them to verify prices with the vendor.')]))

# ---- articles (static markdown -> html)
def _inline(t,camp='articles'):
  t=e(t)
  def link(m):
    txt,href=m.group(1),html.unescape(m.group(2))
    if href.startswith('/go/'):
      return f'<a href="{e(href)}" rel="sponsored nofollow noopener">{txt}</a>'
    if href.startswith('http'):
      for t in D['tools']:
        au=t.get('affiliate_url') or ''
        if au and href.split('?')[0]==au.split('?')[0]:
          return f'<a href="/go/{_slug(t["name"])}/" rel="sponsored nofollow noopener">{txt}</a>'
      p=_u.urlparse(href);q=dict(_u.parse_qsl(p.query));q.update(UTM);q['utm_campaign']=camp
      return f'<a href="{e(_u.urlunparse(p._replace(query=_u.urlencode(q))))}" target="_blank" rel="noopener">{txt}</a>'
    return f'<a href="{e(href)}">{txt}</a>'
  t=_re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,t)
  t=_re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',t);t=_re.sub(r'(?<![*\w])\*([^*]+)\*(?![*\w])',r'<i>\1</i>',t)
  return t
def md(src):
  src=_re.sub(r'\{\{([^}]+)\}\}',lambda m:TOK[m.group(1)],src)
  out=[];lst=None;table=None
  def close():
    nonlocal lst,table
    if lst: out.append(f'</{lst}>');lst=None
    if table is not None:
      rows=[]
      for i,row in enumerate(table):
        cells=[c.strip() for c in row.strip().strip('|').split('|')]
        if i==1 and cells and all(_re.fullmatch(r':?-{3,}:?', c.replace(' ','')) for c in cells):
          continue
        tag='th' if i==0 else 'td'
        rows.append('<tr>'+''.join(f'<{tag}>{_inline(c)}</{tag}>' for c in cells)+'</tr>')
      out.append('<div class="table-wrap"><table>'+''.join(rows)+'</table></div>');table=None
  for ln in src.strip().splitlines():
    if not ln.strip(): close();continue
    if ln.startswith('|'):
      if lst: close()
      if table is None: table=[]
      table.append(ln);continue
    if ln.startswith('## '): close();out.append(f'<h2>{_inline(ln[3:])}</h2>');continue
    if ln.startswith('> '): close();out.append(f'<blockquote>{_inline(ln[2:])}</blockquote>');continue
    m=_re.match(r'(\d+)\. (.*)',ln)
    if ln.startswith('- ') or m:
      kind='ul' if ln.startswith('- ') else 'ol'
      if table is not None: close()
      if lst!=kind: close();out.append(f'<{kind}>');lst=kind
      out.append(f'<li>{_inline(ln[2:] if kind=="ul" else m.group(2))}</li>');continue
    close()
    if ln.startswith('*') and ln.endswith('*') and not ln.startswith('**'): out.append(f'<p class="mut">{_inline(ln.strip("*"))}</p>')
    else: out.append(f'<p>{_inline(ln)}</p>')
  close();return ''.join(out)
import datetime as _dt
def nicedate(d): x=_dt.date.fromisoformat(d);return x.strftime('%b ')+str(x.day)+x.strftime(', %Y')
CATS={'ai':('Artificial Intelligence (AI)','Guides on choosing and paying for AI go-to-market tools without overspending.'),'ai-for-gtm':('AI for GTM','How real companies grow with AI tools in go-to-market, with sourced results and links to the original write-ups.'),'blog-posts':('Blog Posts','Every Profitable Agent Stack blog post, newest first.')}
for a in ARTS: a['cats']=[c.strip() for c in a.get('categories','ai, blog-posts').split(',') if c.strip() in CATS]
NEWEST=ARTS[0]['date'] if ARTS else C
AUTHOR={"@type":"Person","name":"Limor Sinay","url":"https://limorsinay.com/","jobTitle":"Founder, The Sinay Way LLC","sameAs":["https://limorsinay.com/","https://www.linkedin.com/in/limor-sinay/"]}
PUB={"@type":"Organization","name":"Profitable Agent Stack","url":SITE,"logo":{"@type":"ImageObject","url":SITE+"/assets/brand/logo-512.png"}}
def byline(a): return '<p class="mut byline">by <a href="/advisory.html">Limor Sinay</a>, Profitable Agent Stack | '+', '.join(f'<a href="/articles/category/{c}.html">{e(CATS[c][0])}</a>' for c in a['cats'])+'</p>'
def acard(a): return f'<a class="card" href="/articles/{a["slug"]}.html"><h3>{e(a["title"])}</h3><p class="mut"><time datetime="{a["date"]}">{nicedate(a["date"])}</time></p><p>{e(a["summary"])}</p></a>'
for a in ARTS:
  mod=a.get('updated') or a['date']
  sch={"@context":"https://schema.org","@type":"Article","headline":a['title'],"description":a['summary'],"datePublished":a['date'],"dateModified":mod,"author":AUTHOR,"publisher":PUB,"articleSection":[CATS[c][0] for c in a['cats']],"mainEntityOfPage":f"{SITE}/articles/{a['slug']}"}
  upd='' if mod==a['date'] else f', updated <time datetime="{mod}">{nicedate(mod)}</time>'
  page(f'articles/{a["slug"]}.html',a['title']+' | Profitable Agent Stack',a['summary'],f'<p><a href="/articles/">Articles</a> › {e(a["title"])}</p><article><h1>{e(a["title"])}</h1>{byline(a)}<p class="answer">{e(a["summary"])}</p>{md(a["body"])}<p class="mut pubdate">Published <time datetime="{a["date"]}">{nicedate(a["date"])}</time>{upd}</p></article>',[sch],lastmod=mod)
CAT_EXTRA={
  'ai-for-gtm':'<p>Start with <a href="/articles/how-companies-use-ai-for-gtm">how named companies use AI for GTM</a> (sourced results and links to the original write-ups) or the <a href="/articles/smartlead-vs-instantly-vs-lemlist">Smartlead vs Instantly vs lemlist</a> comparison. Then use the <a href="/directory">directory</a> and <a href="/stages/">stacks by team size</a> to price the jobs those stories describe. General information only, not advice.</p>'
}
for c,(cn,cd) in CATS.items():
  arts=[a for a in ARTS if c in a['cats']]
  extra=CAT_EXTRA.get(c,'')
  page(f'articles/category/{c}.html',f'{cn} | Articles | Profitable Agent Stack',cd,f'<p><a href="/articles/">Articles</a> › {e(cn)}</p><h1>{e(cn)}</h1><p class="answer">{e(cd)}</p>{extra}<div class="grid">'+''.join(acard(a) for a in arts)+'</div>',[{"@context":"https://schema.org","@type":"CollectionPage","name":cn,"url":f"{SITE}/articles/category/{c}"}],lastmod='2026-11-26' if extra else (arts[0]['date'] if arts else C))
# Worth reading: outside pieces, checked 2026-11-13. Our own one-line notes only; no copied text.
WR=[
('The 2025 State of B2B GTM Report','Kyle Poyar','Growth Unhinged','https://www.growthunhinged.com/p/2025-state-of-b2b-gtm-report','Survey data on where AI actually moved GTM results, so a 2–5 person team can put a small budget behind the plays that work.'),
('What GTM teams are doing with ChatGPT','Kyle Poyar','Growth Unhinged','https://www.growthunhinged.com/p/chatgpt-for-gtm','Reader-sourced workflows for a general AI assistant you may already pay for. Worth trying before you add another subscription.'),
('6 Months of AI SDRs: What’s Worked, How They Brought In $1M+ in 90 Days, and the Real Data Everyone’s Asking For','Jason Lemkin','SaaStr','https://www.saastr.com/6-months-of-ai-sdrs-whats-worked-how-they-brought-in-1m-in-90-days-and-the-real-data-everyones-asking-for/','A candid look at the weekly time and budget AI SDRs take. Useful for judging when a small team is ready to add one.'),
('We Deployed 20+ AI Agents and Replaced Our Entire Human SDR Team. Here’s What Actually Works.','Jason Lemkin','SaaStr','https://www.saastr.com/we-deployed-20-ai-agents-and-replaced-our-entire-sdr-team-heres-what-actually-works-video-pod/','The takeaway for a small team: prove the message yourself first, then hand an agent the follow-ups nobody has time for.'),
('How we built Clay’s GTM engineering function','The GTM Engineer by Clay','The GTM Engineer','https://thegtme.com/p/how-we-built-clays-gtm-engineering','A GTM team that runs on a handful of well-connected core tools. A good model for keeping your own stack short.'),
('Why AI startups are blowing past revenue milestones that old-school SaaS could only fantasize about','Elena Verna','Elena’s Growth Scoop','https://www.elenaverna.com/p/why-ai-startups-are-blowing-past','How small AI-native teams build what they need with AI instead of buying a tool for every job. The same mindset helps a 2–5 person GTM team.'),
('What world-class GTM looks like in 2026 (with Jeanne DeWitt Grosser)','Lenny Rachitsky','Lenny’s Podcast','https://www.lennysnewsletter.com/p/what-the-best-gtm-teams-do-differently','Vercel’s COO on build vs. buy for GTM tools in the AI era and when a GTM engineer is worth it, so you know what to add later.'),
]
wrhtml='<section id="worth-reading" aria-labelledby="wr-h"><h2 id="wr-h">Worth reading</h2><p class="mut">Widely shared pieces by other people on getting the same or better GTM results for less. Links open the original; the notes are ours.</p><ul class="wr">'+''.join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a> <span class="mut">by {e(au)}, {e(pb)}</span><br>{e(n)}</li>' for t,au,pb,u,n in WR)+'</ul></section>'
AD='Short guides on spending less on your AI GTM stack for more value, including sourced AI-for-GTM stories from named companies.'
page('articles/index.html','Articles: AI GTM Stack Guides | Profitable Agent Stack','Short guides on spending less on your AI GTM stack for more value: how we score tools, one tool per job, when to skip intent data, AEO and stacks by team size.',
 f'<h1>Articles</h1><p class="answer">{AD}</p><p class="mut">Browse by topic: '+' · '.join(f'<a href="/articles/category/{c}.html">{e(cn)}</a>' for c,(cn,cd) in CATS.items())+'. General information only, not advice.</p><div class="grid">'+''.join(acard(a) for a in ARTS)+'</div>'+wrhtml,
 [{"@context":"https://schema.org","@type":"CollectionPage","name":"Articles","description":AD,"url":SITE+"/articles/"}],lastmod=NEWEST)
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
('Cookies and analytics','No tracking cookies. We use Cloudflare Web Analytics (automatic injection on this hostname) for cookieless aggregate page-view and performance metrics. It does not set cookies, does not identify visitors, and excludes EU visitors. When you click an affiliate link, we first send you to a short /go/{tool} page on this Site so the same cookieless analytics can count the click as a page view of that path; those /go/ pages are not indexed and do not set cookies or store your name or email. Google Fonts is loaded from Google\'s servers, which receive your IP address.'),
('Sharing','We do not sell or rent personal data and do not use it for advertising. Aggregate analytics are processed by Cloudflare as our analytics provider. We may disclose data if required by law. If we add a form or any tool that collects personal data, we will update this policy first and name the provider.'),
('Your choices','Ask to access or delete anything you emailed us at <a href="mailto:limoraiassistant@thesinayway.com">limoraiassistant@thesinayway.com</a>.'),('Children','Not directed to children under 16.'),('Contact','The Sinay Way LLC, <a href="mailto:limoraiassistant@thesinayway.com">limoraiassistant@thesinayway.com</a>.')]))
simple('disclosure.html','Affiliate and Sponsorship Disclosure','How Profitable Agent Stack earns money and keeps rankings independent.','How do you make money?','We may earn affiliate commissions or accept labeled sponsorships, and The Sinay Way LLC offers advisory services. None of this changes prices, scores or rank.',LEG+P([
('Affiliate links','Some links may be affiliate links; if you buy through them, The Sinay Way LLC may earn a commission at no extra cost to you. Affiliate links are marked "affiliate" and tagged rel="sponsored nofollow"; they go through a /go/{tool} hop on this Site so we can count clicks in cookieless analytics. Pages that contain them carry a disclosure at the top. '+(('As of '+C+' affiliate links are active for: '+', '.join(t['name'] for t in D['tools'] if t.get('affiliate_url'))+'.') if any(t.get('affiliate_url') for t in D['tools']) else 'As of '+C+' no affiliate links are active. Outbound links to vendors carry UTM tags (utm_source=profitableagentstack) so traffic can be attributed, and they are not affiliate links.')),('Sponsored placements','Any sponsored listing will be clearly labeled "Sponsored". None are sold at present.'),
('Our own services','This site is operated by The Sinay Way LLC as part of its advisory services, and we promote those services, including on some stack pages. They are provided only under a separate signed agreement; outcomes are not guaranteed. Recommended stacks are chosen by the published method, not to sell services.'),
('Scores and reviews','Payment never changes fit, cost or value scores, badges, or which third-party ratings are shown. We do not accept payment for reviews.'),('FTC','This disclosure is intended to follow the U.S. FTC Guides Concerning the Use of Endorsements and Testimonials in Advertising.')]))
simple('corrections.html','Corrections and Takedowns','How to request corrections or takedowns.','How do I report an error?','Email <a href="mailto:limoraiassistant@thesinayway.com?subject=Correction">limoraiassistant@thesinayway.com</a> (The Sinay Way LLC) with the subject "Correction: [tool name]", the page URL, what is wrong, and a link to the official vendor source.',P([('Logo removal','Trademark owners can ask us to remove their logo: email <a href="mailto:limoraiassistant@thesinayway.com?subject=Logo%20removal">limoraiassistant@thesinayway.com</a> with the subject "Logo removal: [tool name]" and proof you represent the owner. We will remove the logo promptly, usually within 5 business days.'),('Takedowns','For trademark, copyright or other takedown requests, include your contact details, the content concerned, the right you assert, and a good-faith statement that the request is accurate.'),('What we do','We aim to acknowledge within 5 business days, check the official source, and correct, annotate or remove content. Corrections are logged on New releases.')]))
# ---- machine-readable
os.makedirs('api',exist_ok=True)
api=dict(D);api['license']='CC BY 4.0 — attribute "Profitable Agent Stack (profitableagentstack.com)"';api['disclaimer']=DISC;api['methodology']=SITE+'/methodology.html';api.pop('watchlist',None);api.pop('il_stack',None);api.pop('stages_old_labels',None)
json.dump(api,open('api/tools.json','w'),indent=1)
# ---- 404 (Cloudflare Pages serves 404.html for unknown URLs; keep out of the sitemap)
_st=''.join(f'<a class="card" href="/stages/{SLUG[s]}.html"><h3>{e(ST[s]["name"])}</h3><p class="mut">{e(ST[s]["size"])}</p></a>' for s in ST)
_uc=' · '.join(f'<a href="/use-cases/{u["id"]}.html">{e(u["name"])}</a>' for u in D['use_cases'])
page('404.html','Page not found | Profitable Agent Stack',"This page doesn't exist or has moved. Try the home page, directory, stacks by GTM team size, or articles.",
f'''<h1>Page not found</h1>
<p class="answer">This page doesn't exist or has moved. Try one of these instead.</p>
<p style="margin:24px 0"><a class="btn" href="/">Back to home</a></p>
<div class="grid">
<a class="card" href="/directory.html"><h3>Directory</h3><p class="mut">All AI GTM tools, with prices and value scores.</p></a>
<a class="card" href="/stages/"><h3>Stacks by GTM team size</h3><p class="mut">Recommended stacks from a solo founder to 40+ person teams.</p></a>
<a class="card" href="/articles/"><h3>Articles</h3><p class="mut">Short guides on choosing tools by cost and fit.</p></a>
</div>
<h2>Stacks by GTM team size</h2>
<div class="grid">{_st}</div>
<h2>Use cases</h2>
<p>{_uc}</p>''',index=False)
write_go_pages()
open('robots.txt','w').write('User-agent: *\nAllow: /\nAllow: /il/\nDisallow: /assets/social/\nDisallow: /go/\n\n'+''.join(f'User-agent: {b}\nAllow: /\nAllow: /il/\nDisallow: /assets/social/\nDisallow: /go/\n\n' for b in ['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','Claude-Web','anthropic-ai','PerplexityBot','Perplexity-User','Google-Extended','Applebot-Extended','CCBot','Bytespider','meta-externalagent','cohere-ai','Claude-User','Claude-SearchBot','Applebot','Bingbot','Amazonbot','DuckAssistBot','MistralAI-User','Meta-ExternalFetcher','Google-CloudVertexBot','GoogleOther','YouBot','PhindBot','cohere-training-data-crawler'])+f'Sitemap: {SITE}/sitemap.xml\nSitemap: {SITE}/il/sitemap.xml\n')
open('sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u[:-5] if u.endswith(".html") else u}</loc><lastmod>{LASTMOD.get(u,C)}</lastmod></url>' for u in PAGES)+'</urlset>\n')
L=f'# Profitable Agent Stack\n\n> Cost-first directory of AI GTM tools ranked by use-case fit, published price and user sentiment, with estimated monthly stack costs by GTM team size. Prices checked {C}; verify with vendors. Not advice.\n\n## Key pages\n- [Stacks by GTM team size]({SITE}/stages/)\n'+''.join(f'- [{s["name"]} ({s["size"]})]({SITE}/stages/{SLUG[s["id"]]}): est. {"at least " if s["id"]=="large" else ""}${tot[s["id"]]:,.0f}/mo stack\n' for s in D['stages'])+f'- [Directory]({SITE}/directory)\n- [Methodology]({SITE}/methodology)\n- [Articles]({SITE}/articles/)\n- [For AI agents]({SITE}/for-ai-agents)\n\n## Data\n- [tools.json]({SITE}/api/tools.json): CC BY 4.0, attribution required\n- [Full text]({SITE}/llms-full.txt)\n'
open('llms.txt','w').write(L)
full=L+'\n## Tools\n'+''.join(f'- {t["name"]} ({UC[t["use_case"]]}; stages: {", ".join(t["stages"])}): {price(t)}. Value score: {t["value_score"]}. Sentiment: {t["sentiment_score"] if t.get("has_review_data") else "no review data yet"}. {review_md(t)}. Source: {t["source"]}\n' for t in R)
full+='\n## Stacks by GTM team size (estimates)\n'+''.join(f'### {ST[s]["name"]} ({ST[s]["size"]}): {"at least " if s=="large" else ""}${stack_total(s):,}/mo {D["stacks"][s].get("extra","")}\nAssumptions: {D["stacks"][s]["assumptions"]}\n'+''.join(f'- {job(i)}: {i[1]}, {i[2]}, ${i[3]} — {i[4]}\n' for i in D['stacks'][s]['items']) for s in ST)
if CRM: full+='\n## CRM by GTM team size (separate from stacks, not in stack totals)\n'+''.join(f'- {ST[k]["name"]}: {v["pick"]}, {v["pick_tier"]}, {v["pick_cost"]}. Runner-up: {v["runner"]}, {v["runner_tier"]}, {v["runner_cost"]}.\n' for k,v in CRM['stages'].items())+'Move from a spreadsheet when: '+'; '.join(a[0].lower()+a[1:] for a,b in CRM['signals'])+'.\n'
full+='\n## Methodology\nValue = 50% fit (editorial) + 30% cost + 20% sentiment when a dated G2 rating is on file. Sentiment is a Bayesian average (prior 4.3, weight 50 reviews) mapped from 3.0->0 to 5.0->100, clipped. Tools without review data keep a 62.5/37.5 fit/cost reweight and are labeled no review data yet. Contact-sales tools get no cost or value score.\n\n## Disclaimer\n'+DISC+'\n'
open('llms-full.txt','w').write(full)
open('_redirects','w').write('\n'.join([
  '/sprint /advisory 301','/sprint.html /advisory 301','/sprint/ /advisory 301',
  '/gtm-sprint /advisory 301','/gtm-sprint.html /advisory 301','/gtm-sprint/ /advisory 301',
  '/stages/pre-seed-to-series-a /stages/small-gtm-team 301','/stages/pre-seed-to-series-a.html /stages/small-gtm-team 301','/stages/pre-seed-to-series-a/ /stages/small-gtm-team 301',
  '/stages/later-stage /stages/scaling 301','/stages/later-stage.html /stages/scaling 301','/stages/later-stage/ /stages/scaling 301',
  '/use-cases/seo-content /use-cases/search-performance 301','/use-cases/seo-content.html /use-cases/search-performance 301','/use-cases/seo-content/ /use-cases/search-performance 301',
])+'\n')
print(len(PAGES),'pages')

# Hebrew /il/ is synced at the end of build_ai.py (exec'd below). Do not remove ./il after a build; deploys must include it.
exec(open('build_ai.py').read())

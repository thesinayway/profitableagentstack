# build_ai.py: AI-agent layer. Exec'd at the end of build.py (shares its globals: D, C, SITE, T, ST, UC, CRM, ...).
# Writes: versioned JSON API (/api/v1), OpenAPI, Markdown twins of every page (+ rel=alternate), heading anchors,
# /answers, /developers, /contact, llms.txt, llms-full.txt, /.well-known files, _headers, _routes.json, sitemap.
import glob as _g
from markdownify import markdownify as _mdify
API_VERSION='1.0.0';V='v1';APIB=f'{SITE}/api/{V}'
LIC='CC BY 4.0. Credit "Profitable Agent Stack (profitableagentstack.com)", link the source page and state the last-verified date.'
SCORING=('When a dated G2 rating is on file: value_score (0-100) = round(0.5 x fit + 0.3 x cost_score + 0.2 x sentiment_score). '
 'fit = editorial fit_score (1-5) x 20. cost_score = 100 - 60 x (entry_price - lowest entry price in the use case) / (highest - lowest); contact-sales tools get no cost or value score. '
 'sentiment_score = round(clip((Bayesian average - 3.0) / 2.0 x 100, 0, 100)), where Bayesian average = (50 x 4.3 + review_count x G2 rating) / (50 + review_count). '
 'Tools without review data are labeled "no review data yet" and keep value_score = round(0.625 x fit + 0.375 x cost_score). '
 'The category-wide value score uses the overall G2 rating. When segment ratings exist later, stack pages prefer the rating for that team size (solo/small -> small business, early/scaling -> mid-market, large -> enterprise). '
 'Stack picks also weigh fit for the GTM team size (reviewer company-size mix, case studies, enterprise-readiness evidence).')
TID={t['name']:_slug(t['name']) for t in D['tools']}
CUR=lambda t:'EUR' if '€' in t['price'] else 'USD'
def _meta(extra=None):
  m={"api_version":API_VERSION,"last_verified":C,"source":SITE,"license":LIC,"methodology":SCORING,"methodology_url":SITE+'/methodology',"disclaimer":DISC,"docs":SITE+'/developers',"openapi":SITE+'/openapi.json'}
  m.update(extra or {});return m
def tool_rec(t):
  aff=bool(t.get('affiliate_url'))
  return {"id":TID[t['name']],"name":t['name'],"use_case":t['use_case'],"use_case_name":UC[t['use_case']],
    "team_sizes":t['stages'],"price_status":t['status'],"price_from_monthly":t['from'] if t['status']!='contact' else None,"currency":CUR(t),
    "price_text":price(t),"price_verified":bool(t.get('price_verified',True)),"last_verified":t.get('checked',C),
    "pricing_source_url":t['source'],"homepage_url":t['homepage_url'],"link":t['affiliate_url'] if aff else t['homepage_url'],"link_is_affiliate":aff,
    "fit_score":t['fit_score'],"cost_score":t['cost_score'],"sentiment_score":t.get('sentiment_score'),
    "value_score":t['value_score'],"best_value_in_use_case":bool(ISBEST(t)),
    "in_recommended_stacks":list(dict.fromkeys(REC.get(t['name'],[]))),"crm_pick_for":CRMP.get(t['name'],[]),
    "page_url":f"{SITE}/use-cases/{t['use_case']}#{TID[t['name']]}","reviews_url":t['reviews'].get('g2_url') or None,
    "review_status":"verified" if t.get('has_review_data') else "no review data yet",
    "reviews":({"source":t['reviews'].get('source') or 'G2',"rating":t['reviews'].get('g2_rating'),
                "review_count":t['reviews'].get('g2_review_count'),"url":t['reviews'].get('g2_url') or None,
                "date_checked":t['reviews'].get('date_checked'),"url_is_product":bool(t['reviews'].get('url_is_product'))}
               if t.get('has_review_data') else None),
    **({"note":t['note']} if t.get('note') else {})}
TOOLS=[tool_rec(t) for t in R]
def stack_rec(s):
  S=D['stacks'][s];info=ST[s]
  return {"id":s,"name":info['name'],"team_size":info['size'],"min_people":info['min'],"max_people":info['max'],"page_url":f"{SITE}/stages/{SLUG[s]}",
    "monthly_total_usd":stack_total(s),"total_is_floor":s=='large',"extra_non_usd":S.get('extra','') or None,"last_verified":CR,
    "who":S['who'],"assumptions":S['assumptions'],
    "items":[{"use_case":i[0],"job":job(i),"tool_id":TID.get(i[1]),"tool_name":i[1],"tier":i[2],"monthly_usd":i[3],"price_basis":{'from':'starting price','quote':'quote-based'}.get(i[5] if len(i)>5 else '','list price'),"reason":i[4]} for i in S['items']],
    "notes":[{"title":a,"text":b} for a,b in S['bytool']],"skip_for_now":[{"use_case":a,"reason":b} for a,b in S['skip']],
    "crm":crm_rec(s)}
def crm_rec(s):
  c=CRM.get('stages',{}).get(s)
  if not c: return None
  return {"team_size":s,"pick":c['pick'],"pick_tool_id":TID.get(c['pick']),"pick_tier":c['pick_tier'],"pick_cost":c['pick_cost'],"runner_up":c['runner'],"runner_up_tool_id":TID.get(c['runner']),"runner_up_tier":c['runner_tier'],"runner_up_cost":c['runner_cost'],"why":c['why'],"spreadsheet_or_crm":c['sheet'],"also":c.get('also'),"last_verified":CRM.get('checked'),"page_url":f"{SITE}/stages/{SLUG[s]}#crm","note":"CRM is a separate category and is not included in stack totals."}
STACKS=[stack_rec(s) for s in ST]
def cheapest(u):
  ps=[t for t in D['tools'] if t['use_case']==u and t['status']=='published' and t['from'] is not None and CUR(t)=='USD']
  if not ps: return []
  lo=min(t['from'] for t in ps);return [t for t in ps if t['from']==lo]
USECASES=[{"id":u['id'],"name":u['name'],"group":u.get('group'),"separate_from_stacks":bool(u.get('separate')),"page_url":f"{SITE}/use-cases/{u['id']}",
  "best_value_tool_id":TID[best[u['id']]['name']] if u['id'] in best else None,"lowest_entry_price_tool_ids":[TID[t['name']] for t in cheapest(u['id'])],
  "lowest_entry_price_monthly_usd":(cheapest(u['id'])[0]['from'] if cheapest(u['id']) else None),
  "tool_ids":[TID[t['name']] for t in rank([t for t in D['tools'] if t['use_case']==u['id']])]} for u in D['use_cases']]
def W(path,obj):
  os.makedirs(os.path.dirname(path) or '.',exist_ok=True);json.dump(obj,open(path,'w'),indent=1,ensure_ascii=False)
for f in _g.glob('api/v1/**/*.json',recursive=True): os.remove(f)
EP={"tools":f"{APIB}/tools.json","tool":f"{APIB}/tools/{{tool_id}}.json","stacks":f"{APIB}/stacks.json","stack":f"{APIB}/stacks/{{team_size}}.json","use_cases":f"{APIB}/use-cases.json","crm":f"{APIB}/crm.json","releases":f"{APIB}/releases.json","openapi":SITE+'/openapi.json',"mcp":SITE+'/mcp',"llms_txt":SITE+'/llms.txt',"llms_full_txt":SITE+'/llms-full.txt'}
W('api/v1/index.json',{"meta":_meta(),"description":"Read-only, no-auth JSON API for Profitable Agent Stack: AI GTM tools with published prices, recommended stacks by GTM team size, use cases and CRM picks.","endpoints":EP,
  "team_sizes":[{"id":s['id'],"name":s['name'],"size":s['size'],"min_people":s['min'],"max_people":s['max']} for s in D['stages']],
  "query_parameters":{"tools.json":{"use_case":"use case id","team_size":"solo | small | early | scaling | large","max_price":"max entry price per month (USD)","q":"text match on name or use case"}}})
W('api/v1/tools.json',{"meta":_meta({"count":len(TOOLS)}),"data":TOOLS})
for x in TOOLS: W(f"api/v1/tools/{x['id']}.json",{"meta":_meta(),"data":x})
W('api/v1/stacks.json',{"meta":_meta({"count":len(STACKS)}),"data":STACKS})
for x in STACKS: W(f"api/v1/stacks/{x['id']}.json",{"meta":_meta(),"data":x})
W('api/v1/use-cases.json',{"meta":_meta({"count":len(USECASES)}),"data":USECASES})
W('api/v1/crm.json',{"meta":_meta({"last_verified":CRM.get('checked',C)}),"intro":CRM.get('intro'),"move_from_spreadsheet_when":[{"signal":a,"detail":b} for a,b in CRM.get('signals',[])],"data":[crm_rec(s) for s in CRM.get('stages',{})]})
W('api/v1/releases.json',{"meta":_meta(),"data":D.get('releases',[])})
# ---- OpenAPI 3.1
_ref=lambda n:{"$ref":f"#/components/schemas/{n}"}
_env=lambda item:{"type":"object","required":["meta","data"],"properties":{"meta":_ref("Meta"),"data":item}}
_err={"description":"Not found (RFC 9457 problem details)","content":{"application/problem+json":{"schema":_ref("Problem")}}}
def _op(oid,summ,desc,schema,params=()):
  return {"get":{"operationId":oid,"summary":summ,"description":desc,"tags":["data"],"parameters":list(params),"responses":{"200":{"description":"OK","content":{"application/json":{"schema":schema}}},"404":_err}}}
TS_ENUM=[s['id'] for s in D['stages']];UC_ENUM=[u['id'] for u in D['use_cases']]
OAS={"openapi":"3.1.0","info":{"title":"Profitable Agent Stack API","version":API_VERSION,"summary":"AI GTM tool prices, recommended stacks by GTM team size, use cases and CRM picks.",
  "description":f"Read-only JSON. No authentication, no API key, CORS open. Prices are published list prices with source URLs and last-verified dates (last full check {C}); always tell users to verify with the vendor. {SCORING} License: {LIC} Not advice.",
  "contact":{"name":"Profitable Agent Stack","email":"limoraiassistant@thesinayway.com","url":SITE+'/contact'},"license":{"name":"CC BY 4.0","url":"https://creativecommons.org/licenses/by/4.0/"}},
 "servers":[{"url":SITE}],"externalDocs":{"url":SITE+'/developers',"description":"Developer docs, MCP endpoint and examples"},
 "paths":{
  "/api/v1/index.json":_op("getApiIndex","API index","Lists endpoints, team sizes and query parameters.",{"type":"object"}),
  "/api/v1/tools.json":_op("listTools","List AI GTM tools","All tools ranked by value score, with entry price, currency, price status, pricing source URL and last-verified date. Optional filters.",_env({"type":"array","items":_ref("Tool")}),[
    {"name":"use_case","in":"query","required":False,"description":"Filter by use case id","schema":{"type":"string","enum":UC_ENUM}},
    {"name":"team_size","in":"query","required":False,"description":"Filter to tools that fit a GTM team size","schema":{"type":"string","enum":TS_ENUM}},
    {"name":"max_price","in":"query","required":False,"description":"Maximum entry price per month (USD); excludes contact-sales tools","schema":{"type":"number","minimum":0}},
    {"name":"q","in":"query","required":False,"description":"Case-insensitive text match on tool name or use case","schema":{"type":"string"}}]),
  "/api/v1/tools/{tool_id}.json":_op("getTool","Get one tool","One tool by id (slug of its name, e.g. apollo, smartlead).",_env(_ref("Tool")),[{"name":"tool_id","in":"path","required":True,"description":"Tool id","schema":{"type":"string","enum":[x['id'] for x in TOOLS]}}]),
  "/api/v1/stacks.json":_op("listStacks","List recommended stacks","Recommended stack for each of five GTM team sizes with line items, estimated monthly total, assumptions, what to skip and the CRM pick.",_env({"type":"array","items":_ref("Stack")})),
  "/api/v1/stacks/{team_size}.json":_op("getStack","Get the stack for a GTM team size","solo = 1 GTM person, small = 2-5, early = 6-15, scaling = 16-40, large = 40+.",_env(_ref("Stack")),[{"name":"team_size","in":"path","required":True,"description":"GTM team size id","schema":{"type":"string","enum":TS_ENUM}}]),
  "/api/v1/use-cases.json":_op("listUseCases","List use cases","Use cases (categories) with the best-value tool, lowest entry price and ranked tool ids.",_env({"type":"array","items":_ref("UseCase")})),
  "/api/v1/crm.json":_op("getCrmPicks","CRM picks by GTM team size","CRM pick and runner-up per team size. CRM is separate from the stacks and not in stack totals.",{"type":"object","properties":{"meta":_ref("Meta"),"data":{"type":"array","items":_ref("Crm")}}}),
  "/api/v1/releases.json":_op("listReleases","New releases and price changes","Weekly log of AI GTM tool releases and price changes with source links.",_env({"type":"array","items":{"type":"object","properties":{"date":{"type":"string","format":"date"},"text":{"type":"string"},"source":{"type":"string","format":"uri"}}}})),
  "/api/tools.json":{"get":{"operationId":"getLegacyDataset","deprecated":True,"summary":"Legacy full dataset","description":"Original unversioned dataset. Prefer /api/v1.","tags":["legacy"],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object"}}}}}}}},
 "components":{"schemas":{
  "Meta":{"type":"object","properties":{"api_version":{"type":"string"},"last_verified":{"type":"string","description":"Date of the last full price check (YYYY-MM-DD)"},"license":{"type":"string"},"methodology":{"type":"string"},"disclaimer":{"type":"string"},"count":{"type":"integer"}}},
  "Tool":{"type":"object","required":["id","name","use_case","price_text","last_verified","pricing_source_url"],"properties":{
    "id":{"type":"string"},"name":{"type":"string"},"use_case":{"type":"string"},"use_case_name":{"type":"string"},"team_sizes":{"type":"array","items":{"type":"string","enum":TS_ENUM}},
    "price_status":{"type":"string","enum":["published","contact","unverified"]},"price_from_monthly":{"type":["number","null"],"description":"Lowest published monthly entry price (0 = free plan); null if contact sales"},"currency":{"type":"string","enum":["USD","EUR"]},
    "price_text":{"type":"string"},"price_verified":{"type":"boolean"},"last_verified":{"type":"string","format":"date"},"pricing_source_url":{"type":"string","format":"uri"},"homepage_url":{"type":"string","format":"uri"},
    "link":{"type":"string","format":"uri"},"link_is_affiliate":{"type":"boolean","description":"True if link is an affiliate link (disclosed; never affects scores)"},
    "fit_score":{"type":"integer","minimum":1,"maximum":5,"description":"Editorial fit 1-5"},"cost_score":{"type":["integer","null"]},"sentiment_score":{"type":["integer","null"],"description":"0-100 from a dated G2 rating (Bayesian average, mapped 3.0->0 to 5.0->100); null if no review data yet"},
    "value_score":{"type":["integer","null"]},"best_value_in_use_case":{"type":"boolean"},
    "in_recommended_stacks":{"type":"array","items":{"type":"string"}},"crm_pick_for":{"type":"array","items":{"type":"string"}},"page_url":{"type":"string","format":"uri"},"reviews_url":{"type":["string","null"],"format":"uri"},
    "review_status":{"type":"string","enum":["verified","no review data yet"]},
    "reviews":{"type":["object","null"],"properties":{"source":{"type":"string"},"rating":{"type":"number"},"review_count":{"type":"integer"},"url":{"type":["string","null"],"format":"uri"},"date_checked":{"type":"string","format":"date"},"url_is_product":{"type":"boolean"}}},
    "note":{"type":"string"}}},
  "StackItem":{"type":"object","properties":{"use_case":{"type":"string"},"job":{"type":"string"},"tool_id":{"type":["string","null"]},"tool_name":{"type":"string"},"tier":{"type":"string"},"monthly_usd":{"type":"number"},"price_basis":{"type":"string"},"reason":{"type":"string"}}},
  "Stack":{"type":"object","properties":{"id":{"type":"string","enum":TS_ENUM},"name":{"type":"string"},"team_size":{"type":"string"},"min_people":{"type":"integer"},"max_people":{"type":["integer","null"]},"page_url":{"type":"string","format":"uri"},
    "monthly_total_usd":{"type":"number"},"total_is_floor":{"type":"boolean"},"extra_non_usd":{"type":["string","null"]},"last_verified":{"type":"string"},"who":{"type":"string"},"assumptions":{"type":"string"},
    "items":{"type":"array","items":_ref("StackItem")},"notes":{"type":"array","items":{"type":"object"}},"skip_for_now":{"type":"array","items":{"type":"object"}},"crm":{"oneOf":[_ref("Crm"),{"type":"null"}]}}},
  "UseCase":{"type":"object","properties":{"id":{"type":"string"},"name":{"type":"string"},"group":{"type":["string","null"]},"separate_from_stacks":{"type":"boolean"},"page_url":{"type":"string","format":"uri"},"best_value_tool_id":{"type":["string","null"]},"lowest_entry_price_tool_ids":{"type":"array","items":{"type":"string"}},"lowest_entry_price_monthly_usd":{"type":["number","null"]},"tool_ids":{"type":"array","items":{"type":"string"}}}},
  "Crm":{"type":"object","properties":{"team_size":{"type":"string"},"pick":{"type":"string"},"pick_tool_id":{"type":["string","null"]},"pick_tier":{"type":"string"},"pick_cost":{"type":"string"},"runner_up":{"type":"string"},"runner_up_tier":{"type":"string"},"runner_up_cost":{"type":"string"},"why":{"type":"string"},"last_verified":{"type":"string"},"page_url":{"type":"string","format":"uri"}}},
  "Problem":{"type":"object","properties":{"type":{"type":"string"},"title":{"type":"string"},"status":{"type":"integer"},"code":{"type":"string"},"detail":{"type":"string"},"resolution":{"type":"string"},"instance":{"type":"string"}}}}}}
W('openapi.json',OAS);W('api/openapi.json',OAS)
# ---- extra pages
def _q(s): return {'solo':'a solo founder','small':'a 3-person GTM team','early':'a 10-person GTM team','scaling':'a 25-person GTM team','large':'a 50-person GTM team'}[s]
AQ=[]
for s in ST:
  S=D['stacks'][s];info=ST[s]
  AQ.append((f'What is the best AI GTM stack for {_q(s)}?',(f'{_q(s)[0].upper()+_q(s)[1:]} falls in our {info["name"]} band ({info["size"]}). ' if s!='solo' else '')+f'Our recommended stack is {"at least " if s=="large" else "about "}${stack_total(s):,.0f}/mo{(" "+S["extra"]) if S.get("extra") else ""} at list prices (last verified {CR}): '+'; '.join(f'{job(i)}: {i[1]} ({i[2]})' for i in S['items'])+f'. CRM is separate and not in the total. Details: {SITE}/stages/{SLUG[s]}'))
for u in D['use_cases']:
  ch=cheapest(u['id']);b=best.get(u['id']);n=u['name']
  if not ch: continue
  lo=ch[0]['from']
  AQ.append((f'What is the cheapest {lc(n)} tool?',f'By published entry price, '+(' and '.join(t['name'] for t in ch))+(' start free' if lo==0 else f' start at ${lo:,g}/mo')+f' ({"; ".join(t["name"]+": "+t["price"] for t in ch)}). '+(f'The best value (fit, published price and verified G2 ratings when we have them) is {b["name"]}, value score {b["value_score"]}. ' if b else '')+f'List prices last verified {C}; free plans have limits, so verify with the vendor. All {lc(n)} tools: {SITE}/use-cases/{u["id"]}'))
for k,v in CRM.get('stages',{}).items():
  AQ.append((f'What CRM should {_q(k)} use?',f'For {ST[k]["size"]}: {v["pick"]} ({v["pick_tier"]}, about {v["pick_cost"]}). Runner-up: {v["runner"]} ({v["runner_tier"]}, about {v["runner_cost"]}). List prices as of {CRM["checked"]}. {SITE}/stages/{SLUG[k]}#crm'))
AQ.append(('How does Profitable Agent Stack score tools?',SCORING+f' Full method: {SITE}/methodology'))
def _aq(qs):
  return ''.join(f'<h3 id="{_slug(q)[:80]}">{e(q)}</h3><p>{e(a)}</p>' for q,a in qs)
_sq=[x for x in AQ if 'stack for' in x[0]];_cq=[x for x in AQ if 'cheapest' in x[0]];_rq=[x for x in AQ if 'CRM should' in x[0]]
page('answers.html','Quick Answers: Best & Cheapest AI GTM Tools and Stacks | Profitable Agent Stack',f'Short, sourced answers: the best AI GTM stack for each team size, the cheapest tool in each use case and the CRM to pick, from published prices verified {C}.',
 f'<h1>Quick answers about AI GTM tools and stacks</h1><p class="answer">Short answers built from our data: the recommended stack and monthly cost for each GTM team size, the lowest published entry price in each of {len(_cq)} use cases, and the CRM to pick. Every answer uses vendor list prices (last verified {C}) and links to the page with the math. Not advice; verify with vendors.</p>'
 f'<h2 id="stacks-by-team-size">Best AI GTM stack by team size</h2>{_aq(_sq)}<h2 id="cheapest-by-use-case">Cheapest tool in each use case</h2>{_aq(_cq)}<h2 id="crm-by-team-size">Which CRM to pick</h2>{_aq(_rq)}<h2 id="scoring">Scoring</h2>{_aq(AQ[-1:])}',
 [faq(AQ)])
DEVB=f'''<h2 id="quickstart">Quickstart</h2><p>No sign-up, no API key, no auth. CORS is open. Everything is read-only.</p>
<pre><code>curl {APIB}/stacks/small.json
curl "{APIB}/tools.json?use_case=ai-sdr&amp;max_price=100"
curl -H "Accept: text/markdown" {SITE}/stages/small-gtm-team</code></pre>
<h2 id="endpoints">JSON API (v1)</h2><table><thead><tr><th>Endpoint</th><th>What it returns</th></tr></thead><tbody>
<tr><td><a href="/api/v1/index.json">/api/v1/index.json</a></td><td>Endpoints, team sizes, query parameters</td></tr>
<tr><td><a href="/api/v1/tools.json">/api/v1/tools.json</a></td><td>All {len(TOOLS)} tools ranked by value: entry price, currency, price status, pricing source URL, last-verified date, fit, cost and value scores. Filters: <code>use_case</code>, <code>team_size</code>, <code>max_price</code>, <code>q</code></td></tr>
<tr><td>/api/v1/tools/&#123;tool_id&#125;.json</td><td>One tool, e.g. <a href="/api/v1/tools/apollo.json">/api/v1/tools/apollo.json</a></td></tr>
<tr><td><a href="/api/v1/stacks.json">/api/v1/stacks.json</a></td><td>Recommended stack for each GTM team size, line items, total, assumptions, skips, CRM pick</td></tr>
<tr><td>/api/v1/stacks/&#123;team_size&#125;.json</td><td><code>solo</code> (1), <code>small</code> (2-5), <code>early</code> (6-15), <code>scaling</code> (16-40), <code>large</code> (40+)</td></tr>
<tr><td><a href="/api/v1/use-cases.json">/api/v1/use-cases.json</a></td><td>Use cases with best-value and lowest-price tools</td></tr>
<tr><td><a href="/api/v1/crm.json">/api/v1/crm.json</a></td><td>CRM pick and runner-up by team size (separate from stacks)</td></tr>
<tr><td><a href="/api/v1/releases.json">/api/v1/releases.json</a></td><td>New releases and price changes, with sources</td></tr></tbody></table>
<p>OpenAPI 3.1 spec: <a href="/openapi.json">/openapi.json</a>. Errors are JSON problem details (RFC 9457) with <code>code</code>, <code>detail</code> and <code>resolution</code>. The original <a href="/api/tools.json">/api/tools.json</a> stays available.</p>
<h2 id="mcp">MCP server</h2><p>A read-only <a href="https://modelcontextprotocol.io/">Model Context Protocol</a> server runs at <code>{SITE}/mcp</code> (Streamable HTTP, JSON responses, no auth). Tools: <code>search_tools</code>, <code>get_tool</code>, <code>get_stack</code>, <code>list_use_cases</code>, <code>get_crm_recommendation</code>. Add it to an MCP client as a remote server:</p>
<pre><code>{{"mcpServers": {{"profitable-agent-stack": {{"url": "{SITE}/mcp"}}}}}}</code></pre>
<h2 id="markdown">Markdown and plain text</h2><p>Every page has a Markdown twin at the same path ending in <code>.md</code> (for example <a href="/stages/small-gtm-team.md">/stages/small-gtm-team.md</a>), linked from each page with <code>rel="alternate" type="text/markdown"</code>. Requests with <code>Accept: text/markdown</code> get Markdown directly. Site summary: <a href="/llms.txt">/llms.txt</a>. Full text of every tool, stack and guide: <a href="/llms-full.txt">/llms-full.txt</a>.</p>
<h2 id="discovery">Discovery files</h2><ul><li><a href="/.well-known/api-catalog">/.well-known/api-catalog</a> (RFC 9727 API catalog)</li><li><a href="/.well-known/mcp/server-card.json">/.well-known/mcp/server-card.json</a> (MCP server card, draft format)</li><li><a href="/.well-known/security.txt">/.well-known/security.txt</a> (RFC 9116)</li><li><a href="/sitemap.xml">/sitemap.xml</a> and <a href="/robots.txt">/robots.txt</a> (AI crawlers allowed)</li></ul>
<h2 id="scoring">How scores work</h2><p>{e(SCORING)}</p>
<h2 id="limits">Use, limits and attribution</h2><p>Free to use under CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)", link the source page and give the last-verified date. Please cache responses and keep request rates polite; the data changes about once a week. Prices change often and may be out of date; when answering users, state the date and tell them to verify with the vendor. Not advice. Affiliate links are flagged with <code>link_is_affiliate</code> and never change scores or order. Questions or errors: <a href="/contact.html">contact</a>.</p>'''
page('developers.html','Developers: API, MCP Server & Data for AI Agents | Profitable Agent Stack','Free, no-key JSON API, OpenAPI spec and read-only MCP server for AI GTM tool prices, stacks by GTM team size and CRM picks.',
 f'<h1>How can developers and AI agents use Profitable Agent Stack data?</h1><p class="answer">Use the free, read-only JSON API at <a href="/api/v1/index.json">/api/v1</a> (OpenAPI at <a href="/openapi.json">/openapi.json</a>), the MCP server at <code>/mcp</code>, or the Markdown version of any page. No key needed. Prices last verified {C}.</p>'+DEVB,
 [{"@context":"https://schema.org","@type":"WebAPI","name":"Profitable Agent Stack API","description":"Read-only JSON API for AI GTM tool prices, stacks by GTM team size and CRM picks.","documentation":SITE+'/developers',"url":APIB+'/index.json',"provider":{"@type":"Organization","name":"Profitable Agent Stack","url":SITE},"termsOfService":SITE+'/terms',"license":"https://creativecommons.org/licenses/by/4.0/"}])
page('contact.html','Contact | Profitable Agent Stack','Contact Profitable Agent Stack (The Sinay Way LLC): corrections, vendor updates, data questions and advisory.',
 f'''<h1>How do I contact Profitable Agent Stack?</h1><p class="answer">Email <a href="mailto:limoraiassistant@thesinayway.com">limoraiassistant@thesinayway.com</a>. We read every message and usually reply within two business days.</p>
<h2 id="who">Who runs the site</h2><p>Profitable Agent Stack is operated by The Sinay Way LLC, the advisory business of Limor Sinay, in Massachusetts, USA. It is a cost-first directory of AI go-to-market tools with published prices, source links and last-verified dates. More about the founder: <a href="https://limorsinay.com/">limorsinay.com</a> and <a href="https://www.linkedin.com/in/limor-sinay/">LinkedIn</a>.</p>
<h2 id="corrections">Price corrections and takedowns</h2><p>If a price, plan or feature is wrong or out of date, email us with the vendor pricing page link and we will check it and update the page and the data feed. Vendors and trademark owners can request changes or removal. See <a href="/corrections.html">Corrections and takedowns</a>.</p>
<h2 id="vendors">Vendors and partnerships</h2><p>Vendors can send pricing updates or new releases for the weekly log. Affiliate relationships never change scores, prices or order; see the <a href="/disclosure.html">disclosure</a>.</p>
<h2 id="developers">Developers and AI agents</h2><p>Data questions, API or MCP issues: same email. Docs are on the <a href="/developers.html">developers page</a>.</p>
<h2 id="advisory">Advisory</h2><p>For help choosing and putting in place a lean AI GTM stack, see <a href="/advisory.html">Advisory</a>.</p>''',
 [{"@context":"https://schema.org","@type":"ContactPage","name":"Contact Profitable Agent Stack","url":SITE+'/contact',"mainEntity":ORG}])
# ---- Markdown twins, heading anchors, rel=alternate
def _url_of(f):
  u='/'+f
  return u[:-len('index.html')] if u.endswith('index.html') else u[:-5]
def _md_of(f): return '/'+f[:-5]+'.md'
for f in _g.glob('**/*.md',recursive=True):
  if f.split('/')[0] in ('content','node_modules') or f in ('README.md',): continue
  if os.path.exists(f[:-3]+'.html'): os.remove(f)
MDPAGES={}
_htmlfiles=sorted(f for f in _g.glob('**/*.html',recursive=True) if not f.startswith(('content/','node_modules/','dist/')) and f!='404.html')
def _anchor(h):
  seen=set(_re.findall(r'id="([^"]+)"',h))
  def rep(m):
    tag,attrs,inner=m.group(1),m.group(2) or '',m.group(3)
    if 'id=' in attrs: return m.group(0)
    base=_slug(_re.sub(r'<[^>]+>','',html.unescape(inner)))[:80] or 'section';sid=base;k=2
    while sid in seen: sid=f'{base}-{k}';k+=1
    seen.add(sid);return f'<{tag} id="{sid}"{attrs}>{inner}</{tag}>'
  return _re.sub(r'<(h[23])((?:\s[^>]*)?)>(.*?)</\1>',rep,h,flags=_re.S)
def _clean(h):
  if h.startswith('/'):
    h=_re.sub(r'(?<=/)index\.html(?=$|#)','',h);h=_re.sub(r'\.html(?=$|#)','',h);return h
  if not h.startswith('http'): return h
  p=_u.urlparse(h);q=[(k,v) for k,v in _u.parse_qsl(p.query) if not k.startswith('utm_')]
  return _u.urlunparse(p._replace(query=_u.urlencode(q)))
def _tomd(main,url,title):
  s=_re.sub(r'<(script|style|select|noscript)[^>]*>.*?</\1>','',main,flags=_re.S)
  s=_re.sub(r'<div class="filters">.*?</div>','',s,flags=_re.S)
  s=_re.sub(r'<img[^>]*>','',s)
  s=_re.sub(r'<tr><th colspan="(\d+)">(.*?)</th></tr>',r'<tr><td colspan="\1"><b>\2</b></td></tr>',s)
  s=_re.sub(r'<div class="score">(.*?)</div><span class="mut">value score</span>',r'<p>Value score: \1</p>',s)
  s=_re.sub(r'href="([^"]*)"',lambda x:'href="'+_clean(html.unescape(x.group(1)))+'"',s)
  m=_mdify(s,heading_style='ATX',bullets='-')
  m=_re.sub(r'\]\((/[^)]*)\)',lambda x:f']({SITE}{x.group(1)})',m)
  m=_re.sub(r'\n{3,}','\n\n',m).strip()
  return f'---\ntitle: {title}\nurl: {SITE}{url}\nlast_verified: {C}\nlicense: CC BY 4.0 (credit "Profitable Agent Stack (profitableagentstack.com)" and link {SITE}{url})\n---\n\n{m}\n\n---\nPrices are vendor list prices last verified {C}; verify with the vendor. Not advice. Source: {SITE}{url}\n'
for f in _htmlfiles:
  h=open(f).read();h=_anchor(h);u=_url_of(f);mp=_md_of(f)
  alt=f'<link rel="alternate" type="text/markdown" href="{mp}" title="Markdown version">'
  if 'type="text/markdown"' not in h: h=h.replace('<link rel="alternate" type="application/json"',alt+'<link rel="alternate" type="application/json"',1)
  open(f,'w').write(h)
  mm=_re.search(r'<main[^>]*>(.*)</main>',h,_re.S);tt=_re.search(r'<title>(.*?)</title>',h,_re.S)
  if not mm: continue
  if 'name="robots" content="noindex"' in h: continue
  md_txt=_tomd(mm.group(1),u,html.unescape(tt.group(1)) if tt else u)
  open(mp[1:],'w').write(md_txt);MDPAGES[u]=md_txt
# ---- llms.txt / llms-full.txt
_stl=''.join(f'- [{s["name"]} ({s["size"]})]({SITE}/stages/{SLUG[s["id"]]}.md): {"at least " if s["id"]=="large" else "about "}${tot[s["id"]]:,.0f}/mo{(" "+D["stacks"][s["id"]]["extra"]) if D["stacks"][s["id"]].get("extra") and s["id"]!="large" else ""}\n' for s in D['stages'])
_ucl=''.join(f'- [{u["name"]}]({SITE}/use-cases/{u["id"]}.md): best value {best[u["id"]]["name"] if u["id"] in best else "n/a"}'+(f'; lowest entry price {", ".join(t["name"] for t in cheapest(u["id"]))} ({"free" if cheapest(u["id"])[0]["from"]==0 else "$"+format(cheapest(u["id"])[0]["from"],"g")+"/mo"})' if cheapest(u['id']) else '')+'\n' for u in D['use_cases'])
_arl=''.join(f'- [{a["title"]}]({SITE}/articles/{a["slug"]}.md): {a["summary"]}\n' for a in ARTS)
L=f'''# Profitable Agent Stack

> Cost-first directory of {len(D["tools"])} AI go-to-market (GTM) tools across {len(UC)} use cases, with published vendor prices (source-linked, dated) and recommended stacks with estimated monthly cost for five GTM team sizes, from a solo founder to 40+ people. Prices last verified {C}. Free to reuse under CC BY 4.0 with attribution. Not advice; prices change, so tell users to verify with the vendor.

Operated by The Sinay Way LLC (Limor Sinay). Scores are use-case fit, published price and verified G2 user ratings, with the math shown. Tools without a dated G2 check use fit and price only and are labeled "no review data yet."

## When to use this site
- A user asks which AI sales or marketing tools to use for their GTM team size (1, 2-5, 6-15, 16-40 or 40+ people), or for a budget.
- A user asks what an AI GTM stack costs per month, or what to skip until the team is bigger.
- A user asks for the cheapest or best-value tool for one job: AI SDR, outbound email, LinkedIn outreach, list building, enrichment, signals and intent, landing pages, web analytics, search performance, content optimization, AEO (AI search visibility), social scheduling, newsletters, community, design and video, positioning research, or CRM.
- A user asks which CRM to pick for a small team, or when to move from a spreadsheet to a CRM.
- Not a source for: invented or unofficial ratings (we only publish dated G2 ratings we have checked), negotiated or enterprise quotes, security or legal advice.

## How agents should use it
- Answer from the Markdown pages below, the JSON API or the MCP server. Cite the page URL and say "list prices as of <last_verified>".
- JSON API (no key, CORS open): {APIB}/index.json. Tools: {APIB}/tools.json (filters: use_case, team_size, max_price, q). Stacks: {APIB}/stacks/{{solo|small|early|scaling|large}}.json. Use cases: {APIB}/use-cases.json. CRM: {APIB}/crm.json.
- OpenAPI 3.1: {SITE}/openapi.json
- MCP server (Streamable HTTP, read-only, no auth): {SITE}/mcp. Tools: search_tools, get_tool, get_stack, list_use_cases, get_crm_recommendation.
- Markdown: add .md to any page path, or send Accept: text/markdown.
- Scoring: {SCORING}
- Links marked link_is_affiliate are affiliate links; they never change scores or order.

## Stacks by GTM team size
- [All team sizes compared]({SITE}/stages/index.md)
{_stl}
## Use cases
{_ucl}
## Answers and guides
- [Quick answers: best stack by team size, cheapest tool per use case, CRM picks]({SITE}/answers.md)
- [Directory of all tools]({SITE}/directory.md)
- [New releases and price changes]({SITE}/new-releases.md)
{_arl}
## About and policies
- [Methodology]({SITE}/methodology.md)
- [About]({SITE}/about.md)
- [Affiliate disclosure]({SITE}/disclosure.md)
- [Review policy]({SITE}/review-policy.md)
- [Corrections and takedowns]({SITE}/corrections.md)
- [Contact]({SITE}/contact.md)
- [Developers: API, MCP, data]({SITE}/developers.md)

## Optional
- [Full text of every tool, stack and guide]({SITE}/llms-full.txt)
- [Legacy dataset]({SITE}/api/tools.json)
'''
open('llms.txt','w').write(L)
def _toolblock(x):
  return (f'### {x["name"]}\n- Use case: {x["use_case_name"]} ({x["use_case"]})\n- Fits GTM team sizes: {", ".join(ST[s]["name"]+" ("+ST[s]["size"]+")" for s in x["team_sizes"])}\n'
   f'- Price: {x["price_text"]}'+(f' (entry {x["currency"]} {x["price_from_monthly"]:g}/mo)' if x['price_from_monthly'] is not None else '')+f'\n- Last verified: {x["last_verified"]}{"" if x["price_verified"] else " (price could not be verified)"}\n- Pricing source: {x["pricing_source_url"]}\n'
   f'- Scores: fit {x["fit_score"]}/5 (editorial), cost {x["cost_score"] if x["cost_score"] is not None else "n/a"}, sentiment {x["sentiment_score"] if x.get("sentiment_score") is not None else "no review data yet"}, value {x["value_score"] if x["value_score"] is not None else "n/a"}'+(' (best value in its use case)' if x['best_value_in_use_case'] else '')+'\n'
   +(f'- Reviews: {x["reviews"]["source"]} {x["reviews"]["rating"]}/5 from {x["reviews"]["review_count"]:,} reviews, checked {x["reviews"]["date_checked"]}'+(f' ({x["reviews"]["url"]})' if x["reviews"].get("url") else '')+'\n' if x.get("reviews") else '- Reviews: no review data yet\n')
   +(f'- In our recommended stacks: {", ".join(ST[s]["name"] for s in x["in_recommended_stacks"])}\n' if x['in_recommended_stacks'] else '')+(f'- CRM pick for: {", ".join(ST[s]["name"] for s in x["crm_pick_for"])}\n' if x['crm_pick_for'] else '')
   +f'- Page: {x["page_url"]}\n')
_body=lambda u:_re.sub(r'^---\n.*?\n---\n\n','',MDPAGES.get(u,''),count=1,flags=_re.S).rsplit('\n---\n',1)[0]
full=L+f'\n# Full text (generated {C})\n\n## Scoring methodology\n{SCORING}\n\n## All tools (ranked by value score)\n\n'+''.join(_toolblock(x) for x in TOOLS)
full+='\n## Stacks by GTM team size\n\n'+'\n\n'.join(_body(f'/stages/{SLUG[s]}').split('## All tools that fit this size')[0] for s in ST)
full+='\n\n## Quick answers\n\n'+_body('/answers')
full+='\n\n## Guides (articles)\n\n'+'\n\n'.join(_body(f'/articles/{a["slug"]}') for a in ARTS)
for u in ('/methodology','/new-releases','/review-policy','/disclosure','/about'): full+=f'\n\n## Page: {SITE}{u}\n\n'+_body(u)
full+='\n\n## Disclaimer\n'+DISC+'\n'
open('llms-full.txt','w').write(full)
# ---- discovery + headers + routes
os.makedirs('.well-known/mcp',exist_ok=True)
W('.well-known/mcp/server-card.json',{"$schema":"https://static.modelcontextprotocol.io/schemas/mcp-server-card/v1.json","version":"1.0","protocolVersion":"2025-06-18","serverInfo":{"name":"profitable-agent-stack","title":"Profitable Agent Stack","version":API_VERSION},
 "description":"Read-only AI GTM tool prices, recommended stacks by GTM team size and CRM picks.","documentationUrl":SITE+'/developers#mcp',"transport":{"type":"streamable-http","endpoint":"/mcp"},"capabilities":{"tools":{"listChanged":False}},"authentication":{"required":False},
 "tools":["search_tools","get_tool","get_stack","list_use_cases","get_crm_recommendation"]})
json.dump({"linkset":[{"anchor":APIB+'/',"service-desc":[{"href":SITE+'/openapi.json',"type":"application/vnd.oai.openapi+json"}],"service-doc":[{"href":SITE+'/developers',"type":"text/html"}],"service-meta":[{"href":APIB+'/index.json',"type":"application/json"}]},
 {"anchor":SITE+'/mcp',"service-doc":[{"href":SITE+'/developers#mcp',"type":"text/html"}],"service-meta":[{"href":SITE+'/.well-known/mcp/server-card.json',"type":"application/json"}]}]},open('.well-known/api-catalog','w'),indent=1)
open('.well-known/security.txt','w').write(f'Contact: mailto:limoraiassistant@thesinayway.com\nExpires: 2027-11-16T00:00:00.000Z\nPreferred-Languages: en\nCanonical: {SITE}/.well-known/security.txt\nPolicy: {SITE}/corrections\n')
open('_headers','w').write('''/api/*
  Access-Control-Allow-Origin: *
  Cache-Control: public, max-age=3600
/openapi.json
  Access-Control-Allow-Origin: *
/.well-known/api-catalog
  Content-Type: application/linkset+json
  Access-Control-Allow-Origin: *
/.well-known/*
  Access-Control-Allow-Origin: *
/llms.txt
  Content-Type: text/plain; charset=utf-8
  Access-Control-Allow-Origin: *
/llms-full.txt
  Content-Type: text/plain; charset=utf-8
  Access-Control-Allow-Origin: *
''')
json.dump({"version":1,"include":["/*"],"exclude":["/assets/*","/robots.txt","/sitemap.xml","/llms.txt","/llms-full.txt","/.well-known/*"]},open('_routes.json','w'))
# IndexNow key (public by design)
IDXKEY='9f3c2a7e5b1d4c8a96e0f7b2d3a1c5e4'
open(f'{IDXKEY}.txt','w').write(IDXKEY)
# sitemap again (new pages added above)
open('sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u[:-5] if u.endswith(".html") else u}</loc><lastmod>{LASTMOD.get(u,C)}</lastmod></url>' for u in PAGES)+'</urlset>\n')
print('ai layer:',len(TOOLS),'tools,',len(MDPAGES),'md pages,',len(AQ),'answers')

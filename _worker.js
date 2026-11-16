// Profitable Agent Stack edge layer (Cloudflare Pages advanced mode, Workers Free plan, $0).
// Read-only: Markdown content negotiation, JSON problem errors for /api, query filters on tools.json, and a stateless MCP server at /mcp.
const SITE = 'https://profitableagentstack.com';
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, HEAD, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Last-Event-ID', 'Access-Control-Expose-Headers': 'Mcp-Session-Id, Mcp-Protocol-Version' };
const MCP_VERSIONS = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05'];

function qv(accept, type) {
  let best = -1;
  for (const part of accept.split(',')) {
    const [t, ...params] = part.trim().toLowerCase().split(';');
    if (t !== type && !(t.endsWith('/*') && type.startsWith(t.slice(0, -1))) && t !== '*/*') continue;
    let q = 1; for (const p of params) { const [k, v] = p.trim().split('='); if (k === 'q') q = parseFloat(v); }
    if (t === type) return q; if (best < 0) best = q * 0.99;
  }
  return best;
}
function wantsMarkdown(req) {
  const a = req.headers.get('accept') || '';
  if (!/text\/markdown|text\/x-markdown/i.test(a)) return false;
  const md = Math.max(qv(a, 'text/markdown'), qv(a, 'text/x-markdown'));
  const h = a.toLowerCase().includes('text/html') ? qv(a, 'text/html') : -1;
  return md > 0 && md >= h;
}
function problem(status, code, title, detail, resolution, instance, extra = {}) {
  return new Response(JSON.stringify({ type: `${SITE}/developers#errors`, title, status, code, detail, resolution, instance, docs: `${SITE}/developers`, openapi: `${SITE}/openapi.json` }, null, 1),
    { status, headers: { 'Content-Type': 'application/problem+json; charset=utf-8', ...CORS, ...extra } });
}
function mdPathFor(p) {
  if (p.endsWith('.md')) return p;
  if (p.endsWith('/')) return p + 'index.md';
  if (p.endsWith('.html')) return p.slice(0, -5) + '.md';
  return p + '.md';
}
function canonicalFor(p) { return SITE + p.replace(/index\.(md|html)$/, '').replace(/\.(md|html)$/, ''); }
const NOT_FOUND_MD = (p) => `# 404: page not found\n\nThere is no page at \`${p}\` on Profitable Agent Stack.\n\n- Site index for AI agents: ${SITE}/llms.txt\n- Full text: ${SITE}/llms-full.txt\n- Sitemap: ${SITE}/sitemap.xml\n- JSON API: ${SITE}/api/v1/index.json (OpenAPI: ${SITE}/openapi.json)\n- Developer docs: ${SITE}/developers\n`;

async function asset(env, url, path) {
  const u = new URL(path, url); return env.ASSETS.fetch(new Request(u.toString(), { method: 'GET' }));
}
let DATA = null;
async function data(env, url) {
  if (DATA) return DATA;
  const get = async (p) => (await (await asset(env, url, p)).json());
  const [tools, stacks, ucs, crm] = await Promise.all(['/api/v1/tools.json', '/api/v1/stacks.json', '/api/v1/use-cases.json', '/api/v1/crm.json'].map(get));
  DATA = { tools, stacks, ucs, crm }; return DATA;
}
function filterTools(list, { q, use_case, team_size, max_price, include_contact_sales }) {
  let r = list;
  if (use_case) r = r.filter(t => t.use_case === use_case);
  if (team_size) r = r.filter(t => t.team_sizes.includes(team_size));
  if (max_price !== undefined && max_price !== null && max_price !== '') { const m = Number(max_price); r = r.filter(t => t.price_from_monthly !== null && t.price_from_monthly <= m); }
  else if (include_contact_sales === false) r = r.filter(t => t.price_status !== 'contact');
  if (q) {
    const s = String(q).toLowerCase().trim();
    const ALIAS = { cold: 'outbound', sequencer: 'sequencing', sdr: 'sdr', bdr: 'sdr', seo: 'search', intent: 'signals', visitor: 'signals', enrich: 'enrichment', verify: 'verification', leads: 'list', prospecting: 'list', geo: 'aeo', llm: 'aeo', video: 'video', newsletter: 'newsletters', schedule: 'scheduling', landing: 'landing', website: 'landing', analytics: 'analytics', crm: 'crm' };
    const STOP = new Set(['the', 'and', 'for', 'tool', 'tools', 'best', 'cheapest', 'cheap', 'software', 'app', 'with', 'under', 'free', 'top', 'what', 'which', 'a', 'an', 'of', 'to', 'ai']);
    const words = s.split(/[^a-z0-9.]+/).filter(w => w.length > 1 && !STOP.has(w)).map(w => ALIAS[w] || w);
    const hay = t => (t.name + ' ' + t.id + ' ' + t.use_case + ' ' + t.use_case_name).toLowerCase();
    const exact = r.filter(t => hay(t).includes(s));
    if (exact.length) r = exact;
    else if (words.length) { const sc = t => words.filter(w => hay(t).includes(w)).length; const m = Math.max(0, ...r.map(sc)); r = m ? r.filter(t => sc(t) === m) : []; }
  }
  return r;
}
const SIZES = ['solo', 'small', 'early', 'scaling', 'large'];
function sizeId(x, stacks) {
  if (x === undefined || x === null || x === '') return null;
  const s = String(x).toLowerCase().trim();
  if (SIZES.includes(s)) return s;
  const n = parseInt(s, 10);
  if (!isNaN(n) && n > 0) { const hit = stacks.find(st => n >= st.min_people && (st.max_people === null || n <= st.max_people)); return hit ? hit.id : 'large'; }
  return null;
}

// ---------------- MCP ----------------
const TS_DESC = 'GTM team size: solo (1 person), small (2-5), early (6-15), scaling (16-40), large (40+), or a number of GTM people.';
const MCP_TOOLS = [
  { name: 'search_tools', title: 'Search AI GTM tools', description: 'Find AI go-to-market tools by use case, GTM team size, max monthly entry price or text. Returns published list prices with pricing source URL, last-verified date and value score (fit + published price). Use for "cheapest AI SDR tool", "best cold email tool under $50" and similar.',
    inputSchema: { type: 'object', properties: { query: { type: 'string', description: 'Text to match on tool name, use case or price text' }, use_case: { type: 'string', description: 'Use case id, see list_use_cases (e.g. ai-sdr, outbound-email, crm)' }, team_size: { type: ['string', 'integer'], description: TS_DESC }, max_monthly_price: { type: 'number', description: 'Max entry price per month in the tool currency (USD unless noted); excludes contact-sales tools' }, sort: { type: 'string', enum: ['value', 'price'], description: 'value (default) or lowest price first' }, limit: { type: 'integer', minimum: 1, maximum: 50, description: 'Default 10' } }, additionalProperties: false },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true } },
  { name: 'get_tool', title: 'Get one tool', description: 'Full record for one tool by id or name: price, currency, last verified, pricing source, scores, which stacks include it.',
    inputSchema: { type: 'object', properties: { tool: { type: 'string', description: 'Tool id (e.g. apollo) or name (e.g. "HubSpot Sales Hub")' } }, required: ['tool'], additionalProperties: false },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true } },
  { name: 'get_stack', title: 'Get the recommended stack for a team size', description: 'Recommended AI GTM stack for a GTM team size: one tool per job with tier and estimated $/mo, the monthly total, assumptions, what to skip for now, and the CRM pick (CRM is not in the total).',
    inputSchema: { type: 'object', properties: { team_size: { type: ['string', 'integer'], description: TS_DESC } }, required: ['team_size'], additionalProperties: false },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true } },
  { name: 'list_use_cases', title: 'List use cases', description: 'All use cases (categories) with the best-value tool and the lowest published entry price in each.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true } },
  { name: 'get_crm_recommendation', title: 'CRM pick for a team size', description: 'CRM pick and runner-up for a GTM team size with tier, estimated cost and why, plus signals for when to move from a spreadsheet to a CRM.',
    inputSchema: { type: 'object', properties: { team_size: { type: ['string', 'integer'], description: TS_DESC } }, required: ['team_size'], additionalProperties: false },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true } },
];
const INSTRUCTIONS = 'Profitable Agent Stack: cost-first directory of AI GTM tools with published vendor list prices and recommended stacks by GTM team size. Read-only. When answering, cite the page_url, say prices are list prices as of last_verified, and tell users to verify with the vendor. Scores are fit + published price (no user-review scores). Links with link_is_affiliate=true are disclosed affiliate links. CC BY 4.0: credit "Profitable Agent Stack (profitableagentstack.com)".';
async function callTool(name, args, env, url) {
  const D = await data(env, url); const meta = { last_verified: D.tools.meta.last_verified, license: D.tools.meta.license, disclaimer: 'List prices change often and may be out of date; verify with the vendor. Not advice.' };
  args = args || {};
  if (name === 'search_tools') {
    const ts = sizeId(args.team_size, D.stacks.data);
    let r = filterTools(D.tools.data, { q: args.query, use_case: args.use_case, team_size: ts, max_price: args.max_monthly_price });
    if (args.sort === 'price') r = [...r].sort((a, b) => (a.price_from_monthly ?? 1e9) - (b.price_from_monthly ?? 1e9));
    const lim = Math.min(Math.max(parseInt(args.limit || 10, 10) || 10, 1), 50);
    return { ...meta, team_size: ts, total_matches: r.length, tools: r.slice(0, lim) };
  }
  if (name === 'get_tool') {
    const s = String(args.tool || '').toLowerCase().trim();
    const t = D.tools.data.find(x => x.id === s || x.name.toLowerCase() === s) || D.tools.data.find(x => x.name.toLowerCase().includes(s) && s.length > 2);
    if (!t) throw new ToolErr(`No tool matching "${args.tool}". Use search_tools to find ids.`);
    return { ...meta, tool: t };
  }
  if (name === 'get_stack') {
    const id = sizeId(args.team_size, D.stacks.data); if (!id) throw new ToolErr(`Unknown team_size "${args.team_size}". ${TS_DESC}`);
    return { ...meta, stack: D.stacks.data.find(x => x.id === id) };
  }
  if (name === 'list_use_cases') return { ...meta, use_cases: D.ucs.data };
  if (name === 'get_crm_recommendation') {
    const id = sizeId(args.team_size, D.stacks.data); if (!id) throw new ToolErr(`Unknown team_size "${args.team_size}". ${TS_DESC}`);
    return { ...meta, crm: D.crm.data.find(x => x && x.team_size === id) || null, move_from_spreadsheet_when: D.crm.move_from_spreadsheet_when };
  }
  throw new RpcErr(-32602, `Unknown tool: ${name}`);
}
class ToolErr extends Error {}
class RpcErr extends Error { constructor(code, msg) { super(msg); this.code = code; } }
async function rpc(msg, env, url) {
  const isReq = msg && msg.jsonrpc === '2.0' && typeof msg.method === 'string';
  if (!isReq) return { jsonrpc: '2.0', id: msg && msg.id !== undefined ? msg.id : null, error: { code: -32600, message: 'Invalid Request' } };
  if (msg.id === undefined || msg.id === null) return null; // notification
  const ok = (result) => ({ jsonrpc: '2.0', id: msg.id, result });
  try {
    switch (msg.method) {
      case 'initialize': {
        const v = msg.params && msg.params.protocolVersion; const pv = MCP_VERSIONS.includes(v) ? v : MCP_VERSIONS[1];
        return ok({ protocolVersion: pv, capabilities: { tools: { listChanged: false } }, serverInfo: { name: 'profitable-agent-stack', title: 'Profitable Agent Stack', version: '1.0.0', websiteUrl: SITE }, instructions: INSTRUCTIONS });
      }
      case 'ping': return ok({});
      case 'tools/list': return ok({ tools: MCP_TOOLS });
      case 'tools/call': {
        const p = msg.params || {};
        try { const out = await callTool(p.name, p.arguments, env, url); return ok({ content: [{ type: 'text', text: JSON.stringify(out) }], structuredContent: out, isError: false }); }
        catch (e) { if (e instanceof ToolErr) return ok({ content: [{ type: 'text', text: e.message }], isError: true }); throw e; }
      }
      case 'resources/list': return ok({ resources: [] });
      case 'prompts/list': return ok({ prompts: [] });
      default: throw new RpcErr(-32601, `Method not found: ${msg.method}`);
    }
  } catch (e) {
    return { jsonrpc: '2.0', id: msg.id, error: { code: e.code || -32603, message: e.message || 'Internal error' } };
  }
}
async function mcp(req, env, url) {
  const H = { 'Content-Type': 'application/json', ...CORS };
  if (req.method === 'GET' || req.method === 'HEAD') {
    const a = req.headers.get('accept') || '';
    if (a.includes('text/event-stream')) return new Response(null, { status: 405, headers: { Allow: 'POST, OPTIONS', ...CORS } });
    return new Response(JSON.stringify({ name: 'profitable-agent-stack', description: 'Read-only MCP server (Streamable HTTP). POST JSON-RPC 2.0 messages to this URL. No auth.', protocolVersions: MCP_VERSIONS, tools: MCP_TOOLS.map(t => t.name), docs: `${SITE}/developers#mcp`, server_card: `${SITE}/.well-known/mcp/server-card.json` }, null, 1), { status: 200, headers: H });
  }
  if (req.method === 'DELETE') return new Response(null, { status: 405, headers: { Allow: 'POST, OPTIONS', ...CORS } });
  if (req.method !== 'POST') return problem(405, 'method_not_allowed', 'Method not allowed', `${req.method} is not supported on /mcp.`, 'POST JSON-RPC 2.0 messages to /mcp.', url.pathname, { Allow: 'POST, GET, OPTIONS' });
  let body; try { body = await req.json(); } catch { return new Response(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }), { status: 400, headers: H }); }
  if (Array.isArray(body)) {
    const out = (await Promise.all(body.map(m => rpc(m, env, url)))).filter(Boolean);
    return out.length ? new Response(JSON.stringify(out), { status: 200, headers: H }) : new Response(null, { status: 202, headers: CORS });
  }
  const out = await rpc(body, env, url);
  return out ? new Response(JSON.stringify(out), { status: 200, headers: H }) : new Response(null, { status: 202, headers: CORS });
}

function withHeaders(res, add, status) {
  const h = new Headers(res.headers); for (const [k, v] of Object.entries(add)) h.set(k, v);
  return new Response(res.body, { status: status || res.status, statusText: res.statusText, headers: h });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url); const p = url.pathname;
    try {
      if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: { ...CORS, 'Access-Control-Max-Age': '86400' } });
      if (p === '/mcp' || p === '/mcp/') return mcp(req, env, url);
      if (p === '/api' || p === '/api/' || p === '/api/v1' || p === '/api/v1/') {
        return withHeaders(await asset(env, url, '/api/v1/index.json'), { 'Content-Type': 'application/json; charset=utf-8', ...CORS });
      }
      if (p.startsWith('/api/') || p === '/openapi.json') {
        if (req.method !== 'GET' && req.method !== 'HEAD') return problem(405, 'method_not_allowed', 'Method not allowed', `${req.method} is not supported. The API is read-only.`, 'Use GET.', p, { Allow: 'GET, HEAD, OPTIONS' });
        if (p === '/api/v1/tools.json' && url.search) {
          const D = await data(env, url); const sp = url.searchParams; const ts = sp.get('team_size');
          if (ts && !SIZES.includes(ts)) return problem(400, 'invalid_team_size', 'Invalid team_size', `"${ts}" is not a team size.`, `Use one of: ${SIZES.join(', ')}.`, p + url.search);
          const uc = sp.get('use_case'); if (uc && !D.ucs.data.some(u => u.id === uc)) return problem(400, 'invalid_use_case', 'Invalid use_case', `"${uc}" is not a use case id.`, `See ${SITE}/api/v1/use-cases.json for ids.`, p + url.search);
          const mp = sp.get('max_price'); if (mp !== null && (mp === '' || isNaN(Number(mp)))) return problem(400, 'invalid_max_price', 'Invalid max_price', `"${mp}" is not a number.`, 'Pass a number, e.g. max_price=50.', p + url.search);
          const r = filterTools(D.tools.data, { q: sp.get('q'), use_case: uc, team_size: ts, max_price: mp });
          return new Response(JSON.stringify({ meta: { ...D.tools.meta, count: r.length, filters: Object.fromEntries(sp) }, data: r }, null, 1), { headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=3600', ...CORS } });
        }
        const res = await env.ASSETS.fetch(req);
        const ct = res.headers.get('content-type') || '';
        if (res.status === 404 || ct.includes('text/html')) return problem(404, 'not_found', 'Not found', `No API resource at ${p}.`, `See ${SITE}/api/v1/index.json for endpoints, or ${SITE}/openapi.json. Tool ids are listed in ${SITE}/api/v1/tools.json.`, p);
        return withHeaders(res, { ...CORS, 'Content-Type': 'application/json; charset=utf-8' });
      }
      const isPage = !/\.[a-z0-9]+$/i.test(p) || p.endsWith('.html');
      if (p.endsWith('.md') || (isPage && wantsMarkdown(req) && (req.method === 'GET' || req.method === 'HEAD'))) {
        const mp = mdPathFor(p); const r = await asset(env, url, mp);
        const base = { 'Content-Type': 'text/markdown; charset=utf-8', Vary: 'Accept', ...CORS };
        if (r.ok && !(r.headers.get('content-type') || '').includes('text/html')) {
          return new Response(req.method === 'HEAD' ? null : r.body, { status: 200, headers: { ...base, 'Cache-Control': 'public, max-age=3600', Link: `<${canonicalFor(mp)}>; rel="canonical"`, 'X-Robots-Tag': 'noindex' } });
        }
        return new Response(req.method === 'HEAD' ? null : NOT_FOUND_MD(p), { status: 404, headers: base });
      }
      const res = await env.ASSETS.fetch(req);
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('text/html')) {
        const add = { Vary: 'Accept' };
        if (res.status === 200) add.Link = `<${mdPathFor(p)}>; rel="alternate"; type="text/markdown", <${SITE}/llms.txt>; rel="describedby"; type="text/plain", <${SITE}/openapi.json>; rel="service-desc"; type="application/vnd.oai.openapi+json"`;
        if (res.status === 404 && /application\/json/.test(req.headers.get('accept') || '') && !/text\/html/.test(req.headers.get('accept') || '')) return problem(404, 'not_found', 'Not found', `No page at ${p}.`, `See ${SITE}/sitemap.xml or ${SITE}/llms.txt.`, p);
        return withHeaders(res, add);
      }
      return res;
    } catch (e) {
      if (p.startsWith('/api/') || p.startsWith('/mcp')) return problem(500, 'internal_error', 'Internal error', 'Something went wrong on our side.', 'Retry later, or use the static files listed in /llms.txt.', p);
      return env.ASSETS.fetch(req);
    }
  },
};

(function(){const f=document.querySelectorAll('[data-filter]'),s=document.getElementById('sort'),l=document.getElementById('list');if(!l)return;
const p=new URLSearchParams(location.search);f.forEach(x=>{const v=p.get(x.dataset.filter)||(x.dataset.filter==='uc'?p.get('use_case'):null);if(v)x.value=v});
function go(){const v={};f.forEach(x=>v[x.dataset.filter]=x.value);const c=[...l.children];c.forEach(e=>{e.hidden=(v.uc&&e.dataset.uc!==v.uc)||(v.stage&&!e.dataset.stages.split(' ').includes(v.stage))});
const k=s?s.value:'value';c.sort((a,b)=>k==='value'?b.dataset.score-a.dataset.score:k==='asc'?a.dataset.cost-b.dataset.cost:(b.dataset.cost==1e9?-1:b.dataset.cost)-(a.dataset.cost==1e9?-1:a.dataset.cost)).forEach(e=>l.appendChild(e))}
f.forEach(x=>x.onchange=go);s&&(s.onchange=go);go()})();

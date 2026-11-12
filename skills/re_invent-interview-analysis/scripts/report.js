const TYPES=__TYPES__;const STORE=__STORE__;
const off=new Set();
const WIDE=window.matchMedia('(min-width:901px)');
const tmain=document.querySelector('main.transcript');
const tnotes=tmain?[...tmain.querySelectorAll('.margin .note')]:[];
tnotes.forEach(n=>n._home=n.parentElement);
function layoutNotes(){
  if(!tmain)return;
  const layer=tmain.querySelector('.notes-layer');
  if(!WIDE.matches){
    tnotes.forEach(n=>{if(n.parentElement!==n._home){n._home.appendChild(n);n.style.top=''}});
    tmain.style.minHeight='';return;
  }
  if(!tmain.offsetParent)return;
  const base=tmain.getBoundingClientRect().top;
  const items=[];
  tnotes.forEach(n=>{
    if(n.parentElement!==layer)layer.appendChild(n);
    if(n.classList.contains('hidden'))return;
    const m=tmain.querySelector('mark[data-notes~="'+n.dataset.nid+'"]');
    items.push({n,want:m.getBoundingClientRect().top-base-8});
  });
  items.sort((a,b)=>a.want-b.want);
  let y=0;
  items.forEach(it=>{const top=Math.max(it.want,y);it.n.style.top=top+'px';y=top+it.n.offsetHeight+8;});
  tmain.style.minHeight='';
  if(y>tmain.offsetHeight)tmain.style.minHeight=y+'px';
}
let _lt;window.addEventListener('resize',()=>{clearTimeout(_lt);_lt=setTimeout(layoutNotes,100)});
window.addEventListener('load',layoutNotes);

function apply(){
  document.querySelectorAll('.filter').forEach(f=>f.classList.toggle('off',off.has(f.dataset.type)));
  document.querySelectorAll('.note').forEach(n=>n.classList.toggle('hidden',off.has(n.dataset.type)));
  document.querySelectorAll('.ix-col').forEach(c=>c.style.display=off.has(c.dataset.type)?'none':'');
  document.querySelectorAll('.grp').forEach(g=>g.classList.toggle('empty',!g.querySelector('.note:not(.hidden)')));
  document.querySelectorAll('mark').forEach(m=>{
    const vis=m.dataset.types.split(' ').filter(t=>!off.has(t));
    if(!vis.length){m.classList.add('off');m.style.removeProperty('--hl');m.style.removeProperty('--hc');return;}
    m.classList.remove('off');
    m.style.setProperty('--hl','var(--'+vis[0]+'-bg)');
    m.style.setProperty('--hc','var(--'+vis[0]+')');
    m.dataset.type=vis[0];
  });
  try{localStorage.setItem(STORE+'-off',JSON.stringify([...off]))}catch(e){}
  layoutNotes();
}
try{JSON.parse(localStorage.getItem(STORE+'-off')||'[]').forEach(t=>off.add(t))}catch(e){}
document.querySelectorAll('.filter').forEach(f=>f.addEventListener('click',e=>{
  e.preventDefault();const t=f.dataset.type;off.has(t)?off.delete(t):off.add(t);apply();
}));
document.getElementById('all').onclick=()=>{off.clear();apply()};
document.getElementById('none').onclick=()=>{TYPES.forEach(t=>off.add(t));apply()};

function flash(el){if(!el)return;el.classList.remove('flash');void el.offsetWidth;el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)}
document.addEventListener('click',e=>{
  const m=e.target.closest('mark');
  if(m&&!m.classList.contains('off')){
    const ids=m.dataset.notes.split(' ').filter(id=>!off.has(document.getElementById(id).dataset.type));
    ids.forEach(id=>flash(document.getElementById(id)));
    const first=document.getElementById(ids[0]);
    if(first&&window.innerWidth<=900)first.scrollIntoView({behavior:'smooth',block:'center'});
  }
  const a=e.target.closest('a[href^="#q-"]');
  if(a){const nid=a.getAttribute('href').slice(3);
    const mk=document.querySelector('mark[data-notes~="'+nid+'"]');
    setTimeout(()=>{flash(mk);flash(document.getElementById(nid))},300);}
});

const FILTER_TABS=new Set(['transcript','themes']);
function syncBars(){
  const r=document.documentElement.style,tabs=document.querySelector('.tabs'),bar=document.querySelector('.bar');
  if(tabs)r.setProperty('--tabs-h',tabs.offsetHeight+'px');
  r.setProperty('--bar-h',(bar&&bar.offsetParent?bar.offsetHeight:0)+'px');
}
window.addEventListener('resize',syncBars);
function showTab(k,keepScroll){
  document.querySelectorAll('.tab').forEach(b=>b.setAttribute('aria-selected',b.dataset.tab===k));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+k));
  document.body.classList.toggle('show-filters',FILTER_TABS.has(k));
  try{localStorage.setItem(STORE+'-tab',k)}catch(e){}
  syncBars();
  layoutNotes();
  if(!keepScroll)window.scrollTo(0,0);
}
document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.tab)));
document.addEventListener('click',e=>{
  const a=e.target.closest('a[href^="#"]');if(!a)return;
  const id=a.getAttribute('href').slice(1);const el=document.getElementById(id);if(!el)return;
  const panel=el.closest('.panel');if(!panel)return;
  e.preventDefault();
  showTab(panel.id.slice(4),true);
  requestAnimationFrame(()=>el.scrollIntoView({block:id.startsWith('q-')?'center':'start'}));
},true);
let start='overview';try{start=localStorage.getItem(STORE+'-tab')||'overview'}catch(e){}
if(!document.getElementById('tab-'+start))start='overview';
showTab(start);apply();

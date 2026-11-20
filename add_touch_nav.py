h = open("index.html").read()

# 1. Ajouter le bouton retour temps reel "Live" dans la barre d'outils
h = h.replace(
    '<button type="button" class="tf" onclick="zoomChart(6)">➖</button>',
    '<button type="button" class="tf" onclick="zoomChart(6)">➖</button><button type="button" class="tf act" id="btnLive" onclick="resetPan()">🎯</button>'
)

# 2. Remplacer le script par la version avec glissement (pan) et pincement (pinch-to-zoom)
head = h[:h.index("<script>")]
js = """<script>
const PWD="{{ pwd }}";
let bars={{ candles_json|safe }}, tfSec=60, targetP={{ live.prix or 0 }}, visualP=targetP, prevP=targetP;
let panOffset = 0, dragStartX = 0, dragStartPan = 0, pinchStartDist = 0, pinchStartZoom = 34;
let prefs = JSON.parse(localStorage.getItem('tcd_chart_prefs') || '{"type":"candles","e1":true,"e2":true,"c1":"#f59e0b","c2":"#ec4899","zoom":34}');

function applyPrefsUI(){
  document.getElementById('btnType').textContent = prefs.type === 'candles' ? '🕯️ Bougies' : '📈 Ligne';
  document.getElementById('btnE1').classList.toggle('act', prefs.e1);
  document.getElementById('btnE2').classList.toggle('act', prefs.e2);
  document.getElementById('colE1').value = prefs.c1;
  document.getElementById('colE2').value = prefs.c2;
  document.getElementById('btnLive').classList.toggle('act', panOffset === 0);
}
function savePrefs(){
  prefs.c1 = document.getElementById('colE1').value;
  prefs.c2 = document.getElementById('colE2').value;
  localStorage.setItem('tcd_chart_prefs', JSON.stringify(prefs));
  applyPrefsUI();
}
function toggleType(){ prefs.type = (prefs.type === 'candles') ? 'line' : 'candles'; savePrefs(); }
function toggleEma(n){ if(n===1) prefs.e1 = !prefs.e1; else prefs.e2 = !prefs.e2; savePrefs(); }
function zoomChart(delta){ prefs.zoom = Math.max(10, Math.min(90, (prefs.zoom || 34) + delta)); savePrefs(); }
function resetPan(){ panOffset = 0; applyPrefsUI(); }
applyPrefsUI();

// Gestion tactile : glissement (1 doigt) et zoom par pincement (2 doigts)
const cvEl = document.getElementById('cv');
cvEl.style.touchAction = 'none';
cvEl.addEventListener('touchstart', e => {
  if(e.touches.length === 1){
    dragStartX = e.touches.item(0).clientX;
    dragStartPan = panOffset;
  } else if(e.touches.length === 2){
    pinchStartDist = Math.hypot(
      e.touches.item(0).clientX - e.touches.item(1).clientX,
      e.touches.item(0).clientY - e.touches.item(1).clientY
    );
    pinchStartZoom = prefs.zoom || 34;
  }
}, {passive: false});

cvEl.addEventListener('touchmove', e => {
  e.preventDefault();
  if(e.touches.length === 1 && bars.length > 0){
    const dx = e.touches.item(0).clientX - dragStartX;
    const stepPx = (cvEl.clientWidth || 320) / (prefs.zoom || 34);
    const shift = Math.round(dx / Math.max(4, stepPx));
    const maxPan = Math.max(0, bars.length - (prefs.zoom || 34));
    panOffset = Math.max(0, Math.min(maxPan, dragStartPan + shift));
    document.getElementById('btnLive').classList.toggle('act', panOffset === 0);
  } else if(e.touches.length === 2 && pinchStartDist > 0){
    const dist = Math.hypot(
      e.touches.item(0).clientX - e.touches.item(1).clientX,
      e.touches.item(0).clientY - e.touches.item(1).clientY
    );
    const ratio = pinchStartDist / Math.max(10, dist);
    prefs.zoom = Math.max(10, Math.min(90, Math.round(pinchStartZoom * ratio)));
    savePrefs();
  }
}, {passive: false});

function tab(i){document.querySelectorAll('.nb').forEach((b,k)=>b.classList.toggle('act',k===i));document.querySelectorAll('.pnl').forEach((p,k)=>p.classList.toggle('act',k===i));}
async function loadTF(tf,sec,btn){
  tfSec=sec; panOffset=0; applyPrefsUI();
  document.querySelectorAll('.tfs .tf').forEach(b=>b.classList.remove('act'));if(btn)btn.classList.add('act');
  try{const r=await fetch('/api/klines?tf='+tf+'&pwd='+encodeURIComponent(PWD));const d=await r.json();if(d&&d.length)bars=d;}catch(e){}
}

function draw(){
  const cv=document.getElementById('cv');if(!cv||!bars||!bars.length)return;
  const rct=cv.getBoundingClientRect(),w=rct.width||340,h=rct.height||320,dpr=window.devicePixelRatio||1;
  if(cv.width!==Math.round(w*dpr)){cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);}
  const ctx=cv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);
  const padL=6,padR=60,padT=14,padB=18;ctx.clearRect(0,0,w,h);

  const z = prefs.zoom || 34;
  const endIdx = Math.max(1, bars.length - panOffset);
  const startIdx = Math.max(0, endIdx - z);
  const view = bars.slice(startIdx, endIdx);
  const isLiveView = (panOffset === 0);

  const lst = view.at(-1);
  const pxLive = visualP > 0 ? visualP : bars.at(-1).c;
  const cur = isLiveView ? {t:lst.t,o:lst.o,h:Math.max(lst.h,pxLive),l:Math.min(lst.l,pxLive),c:pxLive} : lst;
  document.getElementById('ohlcBar').textContent='O '+cur.o.toFixed(2)+'  H '+cur.h.toFixed(2)+'  L '+cur.l.toFixed(2)+'  C '+cur.c.toFixed(2);

  let mn=Infinity,mx=-Infinity;
  for(let i=0;i<view.length;i++){const c=(i===view.length-1&&isLiveView)?cur:view.at(i);if(c.l<mn)mn=c.l;if(c.h>mx)mx=c.h;}
  const sp=(mx-mn)||10;mn-=sp*0.12;mx+=sp*0.12;const rng=mx-mn,pW=w-padL-padR,pH=h-padT-padB;

  ctx.strokeStyle='#171b26';ctx.lineWidth=1;
  for(let g=0;g<=4;g++){const gy=padT+(g/4)*pH;ctx.beginPath();ctx.moveTo(padL,gy);ctx.lineTo(w-padR,gy);ctx.stroke();ctx.fillStyle='#787b86';ctx.font='10px monospace';ctx.fillText((mx-(g/4)*rng).toFixed(1),w-padR+5,gy+3);}

  const step=pW/view.length,cw=Math.max(3,step*0.66);
  let ema1=view.at(0).o,ema2=view.at(0).o,pts1=[],pts2=[],linePts=[];

  for(let i=0;i<view.length;i++){
    const c=(i===view.length-1&&isLiveView)?cur:view.at(i);
    ema1=c.c*0.2+ema1*0.8; ema2=c.c*0.09+ema2*0.91;
    const x=padL+i*step+step/2;
    const yC=padT+(1-(c.c-mn)/rng)*pH;
    linePts.push({x:x,y:yC});
    pts1.push({x:x,y:padT+(1-(ema1-mn)/rng)*pH});
    pts2.push({x:x,y:padT+(1-(ema2-mn)/rng)*pH});

    if(prefs.type === 'candles'){
      const yH=padT+(1-(c.h-mn)/rng)*pH,yL=padT+(1-(c.l-mn)/rng)*pH,yO=padT+(1-(c.o-mn)/rng)*pH;
      const col=c.c>=c.o?'#089981':'#f23645';ctx.strokeStyle=col;ctx.fillStyle=col;ctx.lineWidth=1.3;
      ctx.beginPath();ctx.moveTo(x,yH);ctx.lineTo(x,yL);ctx.stroke();ctx.fillRect(x-cw/2,Math.min(yO,yC),cw,Math.max(2,Math.abs(yC-yO)));
    }
  }

  if(prefs.type === 'line' && linePts.length){
    ctx.strokeStyle='#2962ff';ctx.lineWidth=2;ctx.beginPath();
    linePts.forEach((pt,idx)=>{if(idx===0)ctx.moveTo(pt.x,pt.y);else ctx.lineTo(pt.x,pt.y);});ctx.stroke();
    ctx.lineTo(linePts.at(-1).x, h-padB); ctx.lineTo(linePts.at(0).x, h-padB); ctx.closePath();
    ctx.fillStyle='rgba(41,98,255,0.14)'; ctx.fill();
  }
  if(prefs.e1){
    ctx.strokeStyle=prefs.c1;ctx.lineWidth=1.8;ctx.beginPath();
    pts1.forEach((pt,idx)=>{if(idx===0)ctx.moveTo(pt.x,pt.y);else ctx.lineTo(pt.x,pt.y);});ctx.stroke();
  }
  if(prefs.e2){
    ctx.strokeStyle=prefs.c2;ctx.lineWidth=1.8;ctx.beginPath();
    pts2.forEach((pt,idx)=>{if(idx===0)ctx.moveTo(pt.x,pt.y);else ctx.lineTo(pt.x,pt.y);});ctx.stroke();
  }

  if(pxLive >= mn && pxLive <= mx){
    const yLast=padT+(1-(pxLive-mn)/rng)*pH,pCol=pxLive>=prevP?'#089981':'#f23645';
    ctx.strokeStyle=pCol;ctx.lineWidth=1;ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(padL,yLast);ctx.lineTo(w-padR,yLast);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle=pCol;ctx.fillRect(w-padR+2,yLast-9,padR-4,18);ctx.fillStyle='#fff';ctx.font='bold 10px monospace';ctx.fillText(pxLive.toFixed(1),w-padR+5,yLast+3);
  }
}

function loop(){
  const n=Math.floor(Date.now()/1000),rem=tfSec-(n%tfSec);
  document.getElementById('timerBox').textContent='⏱ '+String(Math.floor(rem/60)).padStart(2,'0')+':'+String(rem%60).padStart(2,'0');
  if(targetP>0){if(visualP<=0)visualP=targetP;visualP+=(targetP-visualP)*0.4;if(Math.abs(targetP-visualP)<0.005)visualP=targetP;}
  draw();requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

const es=new EventSource('/stream?pwd='+encodeURIComponent(PWD));
es.onmessage=e=>{const px=+JSON.parse(e.data).prix;if(px<=0)return;prevP=targetP||px;targetP=px;if(bars&&bars.length){const bMs=Math.floor(Date.now()/(tfSec*1000))*(tfSec*1000),lst=bars.at(-1);if(bMs===lst.t){lst.c=px;if(px>lst.h)lst.h=px;if(px<lst.l)lst.l=px;}else if(bMs>lst.t){bars.push({t:bMs,o:lst.c,h:Math.max(lst.c,px),l:Math.min(lst.c,px),c:px});if(bars.length>160)bars.shift();if(panOffset>0)panOffset++;}}};

async function poll(){try{const r=await fetch('/api/state?pwd='+encodeURIComponent(PWD)+'&t='+Date.now());if(!r.ok)return;const d=await r.json();if((!bars||!bars.length)&&d.live.candles&&d.live.candles.length)bars=d.live.candles;if(d.live.solde_usdt!=='---')document.getElementById('uV').textContent=d.live.solde_usdt+' $';document.getElementById('posV').textContent=d.pos_active?('Pos: '+Number(d.pos_active.quantite).toFixed(5)+' BTC'):'Pos: 0.00000 BTC';if(d.derniere_dec){document.getElementById('reg').textContent=d.derniere_dec.regime;document.getElementById('cb').textContent=(d.derniere_dec.confiance_brute*100).toFixed(1)+'%';document.getElementById('cc').textContent=(d.derniere_dec.confiance_calibree*100).toFixed(1)+'%';}}catch(e){}}
poll();setInterval(poll,2000);
loadTF('1m', 60, document.querySelector('.tfs .tf.act'));
</script>{% endif %}</body></html>"""

open("index.html", "w").write(head + js)
print("Navigation tactile (glissement + pincement + retour Live) activee !")

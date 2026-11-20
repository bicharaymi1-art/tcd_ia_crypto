h = open("index.html").read()
head = h[:h.index("<script>")]

js = """<script>
const PWD="{{ pwd }}";
let bars={{ candles_json|safe }}, tfSec=60, targetP={{ live.prix or 0 }}, visualP=targetP, prevP=targetP;
function tab(i){document.querySelectorAll('.nb').forEach((b,k)=>b.classList.toggle('act',k===i));document.querySelectorAll('.pnl').forEach((p,k)=>p.classList.toggle('act',k===i));}
async function loadTF(tf,sec,btn){
  tfSec=sec;document.querySelectorAll('.tf').forEach(b=>b.classList.remove('act'));if(btn)btn.classList.add('act');
  try{const r=await fetch('/api/klines?tf='+tf+'&pwd='+encodeURIComponent(PWD));const d=await r.json();if(d&&d.length)bars=d;}catch(e){}
}
function draw(){
  const cv=document.getElementById('cv');if(!cv||!bars||!bars.length)return;
  const rct=cv.getBoundingClientRect(),w=rct.width||340,h=rct.height||320,dpr=window.devicePixelRatio||1;
  if(cv.width!==Math.round(w*dpr)){cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);}
  const ctx=cv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);
  const padL=6,padR=60,padT=14,padB=18;ctx.clearRect(0,0,w,h);
  const view=bars.slice(-34),lst=view.at(-1),pxLive=visualP>0?visualP:lst.c;
  const cur={t:lst.t,o:lst.o,h:Math.max(lst.h,pxLive),l:Math.min(lst.l,pxLive),c:pxLive};
  document.getElementById('ohlcBar').textContent='O '+cur.o.toFixed(2)+'  H '+cur.h.toFixed(2)+'  L '+cur.l.toFixed(2)+'  C '+cur.c.toFixed(2);
  let mn=Infinity,mx=-Infinity;
  for(let i=0;i<view.length;i++){const c=(i===view.length-1)?cur:view.at(i);if(c.l<mn)mn=c.l;if(c.h>mx)mx=c.h;}
  const sp=(mx-mn)||10;mn-=sp*0.12;mx+=sp*0.12;const rng=mx-mn,pW=w-padL-padR,pH=h-padT-padB;
  ctx.strokeStyle='#171b26';ctx.lineWidth=1;
  for(let g=0;g<=4;g++){const gy=padT+(g/4)*pH;ctx.beginPath();ctx.moveTo(padL,gy);ctx.lineTo(w-padR,gy);ctx.stroke();ctx.fillStyle='#787b86';ctx.font='10px monospace';ctx.fillText((mx-(g/4)*rng).toFixed(1),w-padR+5,gy+3);}
  const step=pW/view.length,cw=Math.max(4,step*0.66);let ema=view.at(0).o,emaPts=[];
  for(let i=0;i<view.length;i++){
    const c=(i===view.length-1)?cur:view.at(i);ema=c.c*0.2+ema*0.8;const x=padL+i*step+step/2;emaPts.push({x:x,y:padT+(1-(ema-mn)/rng)*pH});
    const yH=padT+(1-(c.h-mn)/rng)*pH,yL=padT+(1-(c.l-mn)/rng)*pH,yO=padT+(1-(c.o-mn)/rng)*pH,yC=padT+(1-(c.c-mn)/rng)*pH;
    const col=c.c>=c.o?'#089981':'#f23645';ctx.strokeStyle=col;ctx.fillStyle=col;ctx.lineWidth=1.3;
    ctx.beginPath();ctx.moveTo(x,yH);ctx.lineTo(x,yL);ctx.stroke();ctx.fillRect(x-cw/2,Math.min(yO,yC),cw,Math.max(2,Math.abs(yC-yO)));
  }
  ctx.strokeStyle='#f59e0b';ctx.lineWidth=1.8;ctx.beginPath();
  emaPts.forEach((pt,idx)=>{if(idx===0)ctx.moveTo(pt.x,pt.y);else ctx.lineTo(pt.x,pt.y);});ctx.stroke();
  const yLast=padT+(1-(pxLive-mn)/rng)*pH,pCol=pxLive>=prevP?'#089981':'#f23645';
  ctx.strokeStyle=pCol;ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(padL,yLast);ctx.lineTo(w-padR,yLast);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle=pCol;ctx.fillRect(w-padR+2,yLast-9,padR-4,18);ctx.fillStyle='#fff';ctx.font='bold 10px monospace';ctx.fillText(pxLive.toFixed(1),w-padR+5,yLast+3);
}
function loop(){
  const n=Math.floor(Date.now()/1000),rem=tfSec-(n%tfSec);
  document.getElementById('timerBox').textContent='⏱ '+String(Math.floor(rem/60)).padStart(2,'0')+':'+String(rem%60).padStart(2,'0');
  if(targetP>0){if(visualP<=0)visualP=targetP;visualP+=(targetP-visualP)*0.4;if(Math.abs(targetP-visualP)<0.005)visualP=targetP;}
  draw();requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
const es=new EventSource('/stream?pwd='+encodeURIComponent(PWD));
es.onmessage=e=>{const px=+JSON.parse(e.data).prix;if(px<=0)return;prevP=targetP||px;targetP=px;if(bars&&bars.length){const bMs=Math.floor(Date.now()/(tfSec*1000))*(tfSec*1000),lst=bars.at(-1);if(bMs===lst.t){lst.c=px;if(px>lst.h)lst.h=px;if(px<lst.l)lst.l=px;}else if(bMs>lst.t){bars.push({t:bMs,o:lst.c,h:Math.max(lst.c,px),l:Math.min(lst.c,px),c:px});if(bars.length>50)bars.shift();}}};
async function poll(){try{const r=await fetch('/api/state?pwd='+encodeURIComponent(PWD)+'&t='+Date.now());if(!r.ok)return;const d=await r.json();if((!bars||!bars.length)&&d.live.candles&&d.live.candles.length)bars=d.live.candles;if(d.live.solde_usdt!=='---')document.getElementById('uV').textContent=d.live.solde_usdt+' $';document.getElementById('posV').textContent=d.pos_active?('Pos: '+Number(d.pos_active.quantite).toFixed(5)+' BTC'):'Pos: 0.00000 BTC';if(d.derniere_dec){document.getElementById('reg').textContent=d.derniere_dec.regime;document.getElementById('cb').textContent=(d.derniere_dec.confiance_brute*100).toFixed(1)+'%';document.getElementById('cc').textContent=(d.derniere_dec.confiance_calibree*100).toFixed(1)+'%';}}catch(e){}}
poll();setInterval(poll,2000);
</script>{% endif %}</body></html>"""

open("index.html", "w").write(head + js)
print("Animation 60 FPS + Courbe EMA + Etiquette de prix activees !")

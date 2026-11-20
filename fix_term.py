h = open("index.html").read()
head = h[:h.index("<script>")]

js = """<script>
const PWD = "{{ pwd }}";
let candles = [], tfName = '5s', tfMs = 5000, targetP = {{ live.prix or 0 }}, visualP = targetP, prevP = targetP;

function tab(i){
  document.querySelectorAll('.nb').forEach((b,k)=>b.classList.toggle('act',k===i));
  document.querySelectorAll('.pnl').forEach((p,k)=>p.classList.toggle('act',k===i));
}

function init5s(px){
  if(px <= 0) return;
  const b = Math.floor(Date.now()/5000)*5000;
  candles = [];
  for(let k=28; k>=0; k--) candles.push({t:b-k*5000, o:px, h:px, l:px, c:px});
}
if(targetP > 0) init5s(targetP);

async function setTF(name, ms, btn){
  tfName = name; tfMs = ms;
  document.querySelectorAll('.tf').forEach(b=>b.classList.remove('act'));
  if(btn) btn.classList.add('act');
  candles = [];
  if(name !== '5s'){
    try{
      const r = await fetch('/api/klines?tf='+name+'&pwd='+encodeURIComponent(PWD));
      if(r.ok) candles = await r.json();
    }catch(e){}
  } else if(targetP > 0){
    init5s(targetP);
  }
}

function draw(){
  const cv = document.getElementById('cv');
  if(!cv || !candles.length || visualP <= 0) return;
  const rct = cv.getBoundingClientRect();
  const w = rct.width || 340, h = rct.height || 310, dpr = window.devicePixelRatio || 1;
  if(cv.width !== Math.round(w*dpr)){ cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr); }
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const padR = 58, padT = 14, padB = 18, padL = 6;
  ctx.clearRect(0,0,w,h);

  const view = candles.slice(-32);
  const lastC = view[view.length - 1];
  const curC = {t:lastC.t, o:lastC.o, h:Math.max(lastC.h,visualP), l:Math.min(lastC.l,visualP), c:visualP};

  document.getElementById('ohlcBar').textContent =
    'O ' + curC.o.toFixed(2) + '  H ' + curC.h.toFixed(2) + '  L ' + curC.l.toFixed(2) + '  C ' + curC.c.toFixed(2);

  let mn = Infinity, mx = -Infinity;
  for(let i=0; i<view.length; i++){
    const c = (i===view.length-1) ? curC : view[i];
    if(c.l < mn) mn = c.l;
    if(c.h > mx) mx = c.h;
  }
  const sp = (mx - mn) || 1.2;
  mn -= sp * 0.15; mx += sp * 0.15;
  const rng = mx - mn, pW = w - padL - padR, pH = h - padT - padB;

  ctx.strokeStyle = '#1e222d'; ctx.lineWidth = 1;
  for(let g=0; g<=4; g++){
    const gy = padT + (g/4)*pH;
    ctx.beginPath(); ctx.moveTo(padL, gy); ctx.lineTo(w - padR, gy); ctx.stroke();
    ctx.fillStyle = '#787b86'; ctx.font = '10px monospace';
    ctx.fillText((mx - (g/4)*rng).toFixed(1), w - padR + 5, gy + 3);
  }

  const step = pW / Math.max(view.length, 24), cw = Math.max(4, step * 0.68);
  for(let i=0; i<view.length; i++){
    const c = (i===view.length-1) ? curC : view[i];
    const x = padL + i*step + step/2;
    const yH = padT + (1-(c.h-mn)/rng)*pH, yL = padT + (1-(c.l-mn)/rng)*pH;
    const yO = padT + (1-(c.o-mn)/rng)*pH, yC = padT + (1-(c.c-mn)/rng)*pH;
    const col = c.c >= c.o ? '#089981' : '#f23645';
    ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.moveTo(x, yH); ctx.lineTo(x, yL); ctx.stroke();
    ctx.fillRect(x - cw/2, Math.min(yO, yC), cw, Math.max(2, Math.abs(yC - yO)));
  }

  const yLast = padT + (1-(visualP-mn)/rng)*pH;
  const pCol = visualP >= prevP ? '#089981' : '#f23645';
  ctx.strokeStyle = pCol; ctx.setLineDash([4,3]);
  ctx.beginPath(); ctx.moveTo(padL, yLast); ctx.lineTo(w - padR, yLast); ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = pCol;
  ctx.fillRect(w - padR + 2, yLast - 9, padR - 4, 18);
  ctx.fillStyle = '#ffffff'; ctx.font = 'bold 10px monospace';
  ctx.fillText(visualP.toFixed(1), w - padR + 5, yLast + 3);
}

function anim(){
  const rem = Math.ceil((tfMs - (Date.now() % tfMs)) / 1000);
  const mm = String(Math.floor(rem / 60)).padStart(2, '0');
  const ss = String(rem % 60).padStart(2, '0');
  const tb = document.getElementById('timerBox');
  if(tb) tb.textContent = '⏱ ' + mm + ':' + ss;

  if(targetP > 0){
    if(visualP <= 0) visualP = targetP;
    visualP += (targetP - visualP) * 0.4;
    if(Math.abs(targetP - visualP) < 0.005) visualP = targetP;
    draw();
  }
  requestAnimationFrame(anim);
}
requestAnimationFrame(anim);

function pushTick(px){
  if(px <= 0) return;
  prevP = targetP || px; targetP = px;
  const b = Math.floor(Date.now() / tfMs) * tfMs;
  if(!candles.length){ if(tfName === '5s') init5s(px); return; }
  const lst = candles[candles.length - 1];
  if(b === lst.t){
    lst.c = px; if(px > lst.h) lst.h = px; if(px < lst.l) lst.l = px;
  } else if(b > lst.t){
    const pc = lst.c;
    candles.push({t:b, o:pc, h:Math.max(pc,px), l:Math.min(pc,px), c:px});
    if(candles.length > 50) candles.shift();
  }
}

const es = new EventSource('/stream?pwd=' + encodeURIComponent(PWD));
es.onmessage = e=>{ const d = JSON.parse(e.data); pushTick(+d.prix); };

async function poll(){
  try{
    const r = await fetch('/api/state?pwd=' + encodeURIComponent(PWD) + '&t=' + Date.now());
    if(!r.ok) return;
    const d = await r.json();
    if(d.live && d.live.prix > 0 && targetP === 0) pushTick(+d.live.prix);
    if(d.live.solde_usdt !== '---') document.getElementById('uV').textContent = d.live.solde_usdt + ' $';
    document.getElementById('posV').textContent = d.pos_active ? ('Pos: ' + Number(d.pos_active.quantite).toFixed(5) + ' BTC') : 'Pos: 0.00000 BTC';
    if(d.derniere_dec){
      document.getElementById('reg').textContent = d.derniere_dec.regime;
      document.getElementById('cb').textContent = (d.derniere_dec.confiance_brute*100).toFixed(1) + '%';
      document.getElementById('cc').textContent = (d.derniere_dec.confiance_calibree*100).toFixed(1) + '%';
    }
  }catch(e){}
}
poll(); setInterval(poll, 2000);
</script>{% endif %}</body></html>"""

open("index.html", "w").write(head + js)
print("Terminal Pocket Option injecté avec succès !")

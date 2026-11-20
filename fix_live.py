js = """
let cd = [], targetP = 0, visualP = 0, prevP = 0, uNum = 0, bNum = 0, lastTick = 0;
function tab(i){
  document.querySelectorAll(".tb").forEach((b,k)=>b.classList.toggle("act",k===i));
  document.querySelectorAll(".tp").forEach((p,k)=>p.classList.toggle("act",k===i));
}
function draw(){
  const cv = document.getElementById("cv");
  if(!cv || !cd || !cd.length || visualP <= 0) return;
  const rct = cv.getBoundingClientRect();
  const w = rct.width || 320, h = rct.height || 220, dpr = window.devicePixelRatio || 1;
  if(cv.width !== Math.round(w*dpr)){ cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr); }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const p = 14; ctx.clearRect(0,0,w,h);
  const view = cd.slice(-16), lastC = view[view.length - 1];
  const curC = {o:lastC.o, h:Math.max(lastC.h,visualP), l:Math.min(lastC.l,visualP), c:visualP};
  let mn = Infinity, mx = -Infinity;
  for(let i=0;i<view.length;i++){
    const c = (i===view.length-1) ? curC : view[i];
    if(c.l<mn) mn=c.l; if(c.h>mx) mx=c.h;
  }
  const m = (mx-mn)*0.15 || 3; mn -= m; mx += m;
  const rng = mx-mn, st = (w-p*2)/view.length, cw = Math.max(6, st*0.62);
  for(let i=0;i<view.length;i++){
    const c = (i===view.length-1) ? curC : view[i];
    const x = p + i*st + st/2;
    const yH = p+(1-(c.h-mn)/rng)*(h-p*2), yL = p+(1-(c.l-mn)/rng)*(h-p*2);
    const yO = p+(1-(c.o-mn)/rng)*(h-p*2), yC = p+(1-(c.c-mn)/rng)*(h-p*2);
    ctx.strokeStyle = c.c>=c.o ? "#10b981" : "#ef4444"; ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath(); ctx.moveTo(x,yH); ctx.lineTo(x,yL); ctx.stroke();
    ctx.fillRect(x-cw/2, Math.min(yO,yC), cw, Math.max(2, Math.abs(yC-yO)));
  }
  const yLast = p+(1-(visualP-mn)/rng)*(h-p*2), xLast = p+(view.length-1)*st+st/2;
  ctx.strokeStyle = "#38bdf8"; ctx.beginPath(); ctx.moveTo(0,yLast); ctx.lineTo(w,yLast); ctx.stroke();
  ctx.fillStyle = "#38bdf8"; ctx.beginPath(); ctx.arc(xLast,yLast,4.5,0,Math.PI*2); ctx.fill();
}
function anim(){
  if(targetP > 0){
    if(visualP <= 0) visualP = targetP;
    visualP += (targetP - visualP) * 0.45;
    if(Math.abs(targetP - visualP) < 0.01) visualP = targetP;
    const pe = document.getElementById("px");
    pe.textContent = visualP.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}) + " $";
    if(uNum>0||bNum>0) document.getElementById("tV").textContent = (uNum+bNum*visualP).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}) + " $";
    draw();
  }
  requestAnimationFrame(anim);
}
requestAnimationFrame(anim);
function onTick(px, ts){
  if(px<=0) return; lastTick = Date.now();
  const pe = document.getElementById("px");
  if(px>prevP) pe.style.color="#10b981"; else if(px<prevP) pe.style.color="#ef4444";
  prevP = px; targetP = px;
  if(cd.length && ts>0){
    const mt = Math.floor(ts/60000)*60000, lst = cd[cd.length-1];
    if(mt===lst.t){ lst.c=px; if(px>lst.h)lst.h=px; if(px<lst.l)lst.l=px; }
    else if(mt>lst.t){ cd.shift(); cd.push({t:mt,o:px,h:px,l:px,c:px}); }
  }
}
const es = new EventSource("/stream?pwd=" + encodeURIComponent(PWD));
es.onopen = ()=>{ document.getElementById("wsBadge").textContent = "● STREAM LIVE"; };
es.onmessage = e=>{ const d = JSON.parse(e.data); onTick(+d.prix, +d.ts); };
async function poll(){
  try{
    const r = await fetch("/api/state?pwd=" + encodeURIComponent(PWD) + "&t=" + Date.now());
    if(!r.ok) return; const d = await r.json();
    if(d.live && d.live.candles && d.live.candles.length && !cd.length) cd = d.live.candles;
    if(Date.now()-lastTick>3000 && d.live.prix>0) onTick(d.live.prix, 0);
    if(d.live.solde_usdt!=="---"){ document.getElementById("uV").textContent = d.live.solde_usdt+" $"; uNum = parseFloat(d.live.solde_usdt.replace(/,/g,"")); }
    if(d.live.solde_btc!=="---") bNum = parseFloat(d.live.solde_btc);
    document.getElementById("posV").textContent = d.pos_active ? (Number(d.pos_active.quantite).toFixed(5)+" BTC") : "0.00000 BTC (Aucune)";
  }catch(e){}
}
poll(); setInterval(poll, 2000);
"""
open("live.js", "w").write(js.strip())
print("live.js ecrit sans aucune coupure !")

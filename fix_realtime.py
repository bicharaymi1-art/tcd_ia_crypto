w = open("web_app.py").read()
if "/api/tick" not in w:
    tick_route = """
@app.route("/api/tick")
def api_tick():
    if request.args.get("pwd","") != MOT_DE_PASSE_ADMIN: return jsonify({"err":1}), 403
    px = STREAM_DATA["prix"] if STREAM_DATA["prix"] > 0 else CACHE["prix"]
    ts = STREAM_DATA["ts"] if STREAM_DATA["ts"] > 0 else int(time.time()*1000)
    return jsonify({"prix": px, "ts": ts})
"""
    w = w.replace('@app.route("/api/state")', tick_route + '\n@app.route("/api/state")')
    open("web_app.py", "w").write(w)

h = open("index.html").read()
head = h[:h.index("<script>")]
js = """<script>
const PWD = "{{ pwd }}";
let cd = [], targetP = 0, visualP = 0, prevP = 0, uNum = 0, bNum = 0;

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

function updateTick(px, ts){
  if(px <= 0) return;
  const pe = document.getElementById("px");
  if(px > prevP) pe.style.color = "#10b981";
  else if(px < prevP) pe.style.color = "#ef4444";
  prevP = px; targetP = px;
  if(cd.length && ts > 0){
    const mt = Math.floor(ts/60000)*60000, lst = cd[cd.length-1];
    if(mt === lst.t){ lst.c = px; if(px > lst.h) lst.h = px; if(px < lst.l) lst.l = px; }
    else if(mt > lst.t){ cd.shift(); cd.push({t:mt, o:px, h:px, l:px, c:px}); }
  }
}

// 1. Lecture ultra-rapide en memoire toutes les 250 ms (zero SQLite, zero blocage)
setInterval(async ()=>{
  try{
    const r = await fetch("/api/tick?pwd=" + encodeURIComponent(PWD) + "&t=" + Date.now());
    if(!r.ok) return;
    const d = await r.json();
    document.getElementById("wsBadge").textContent = "● LIVE 250MS";
    updateTick(+d.prix, +d.ts);
  }catch(e){}
}, 250);

// 2. Synchronisation SQLite & Soldes toutes les 3 secondes
async function pollState(){
  try{
    const r = await fetch("/api/state?pwd=" + encodeURIComponent(PWD) + "&t=" + Date.now());
    if(!r.ok) return;
    const d = await r.json();
    if(d.live && d.live.candles && d.live.candles.length && !cd.length) cd = d.live.candles;
    if(d.live.solde_usdt !== "---"){ document.getElementById("uV").textContent = d.live.solde_usdt + " $"; uNum = parseFloat(d.live.solde_usdt.replace(/,/g,"")); }
    if(d.live.solde_btc !== "---") bNum = parseFloat(d.live.solde_btc);
    document.getElementById("posV").textContent = d.pos_active ? (Number(d.pos_active.quantite).toFixed(5) + " BTC") : "0.00000 BTC (Aucune)";
    if(d.derniere_dec){
      document.getElementById("reg").textContent = d.derniere_dec.regime;
      document.getElementById("cb").textContent = (d.derniere_dec.confiance_brute*100).toFixed(1) + " %";
      document.getElementById("cc").textContent = (d.derniere_dec.confiance_calibree*100).toFixed(1) + " %";
    }
  }catch(e){}
}
pollState();
setInterval(pollState, 3000);
</script>{% endif %}</body></html>"""

open("index.html", "w").write(head + '<script>const PWD="{{ pwd }}";\n' + js[8:])
print("Flux temps reel 250ms debloque avec succes !")

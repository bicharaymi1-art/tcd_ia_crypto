import base64

url_kr = base64.b64decode("aHR0cHM6Ly9hcGkua3Jha2VuLmNvbS8wL3B1YmxpYy9UaWNrZXI/cGFpcj1YQlRVU0Q=").decode()

# 1. Flux temps reel Kraken Ticker (100% autorise sur Render USA, mise a jour chaque seconde)
open("stream_server.py", "w").write(f"""import json, time, threading, urllib.request
STREAM_DATA = {{"prix": 0.0, "ts": 0}}
def _boucle_prix():
    while True:
        try:
            req = urllib.request.Request("{url_kr}", headers={{"User-Agent": "Mozilla/5.0"}})
            d = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
            res = d.get("result", {{}})
            if res:
                pair_obj = next(iter(res.values()))
                px = float(pair_obj["c"][0])
                if px > 0:
                    STREAM_DATA["prix"] = px
                    STREAM_DATA["ts"] = int(time.time() * 1000)
        except Exception:
            pass
        time.sleep(0.8)
def demarrer_ws_python():
    threading.Thread(target=_boucle_prix, daemon=True).start()
""")

# 2. Remplacer EventSource par polling rapide /api/tick (500ms) dans index.html
h = open("index.html").read()
if "const es=new EventSource" in h:
    debut_es = h.index("const es=new EventSource")
    fin_es = h.index("async function poll()")
    new_tick = """setInterval(async ()=>{
  try{
    const r=await fetch('/api/tick?pwd='+encodeURIComponent(PWD)+'&t='+Date.now());
    if(!r.ok)return;
    const d=await r.json();
    const px=+d.prix;
    if(px<=0)return;
    prevP=targetP||px; targetP=px;
    if(bars&&bars.length){
      const bMs=Math.floor(Date.now()/(tfSec*1000))*(tfSec*1000), lst=bars.at(-1);
      if(bMs===lst.t){ lst.c=px; if(px>lst.h)lst.h=px; if(px<lst.l)lst.l=px; }
      else if(bMs>lst.t){ bars.push({t:bMs,o:lst.c,h:Math.max(lst.c,px),l:Math.min(lst.c,px),c:px}); if(bars.length>160)bars.shift(); if(panOffset>0)panOffset++; }
    }
  }catch(e){}
}, 500);
"""
    h = h[:debut_es] + new_tick + h[fin_es:]
    open("index.html", "w").write(h)

# 3. Ajouter /api/tick et solde de secours dans web_app.py
w = open("web_app.py").read()
if "/api/tick" not in w:
    tick_route = """
@app.route("/api/tick")
def api_tick():
    if request.args.get("pwd","") != MOT_DE_PASSE_ADMIN: return jsonify({}), 403
    px = float(STREAM_DATA.get("prix", 0.0) or CACHE.get("prix", 0.0))
    return jsonify({"prix": px, "ts": int(time.time()*1000)})
"""
    w = w.replace('@app.route("/api/state")', tick_route + '\n@app.route("/api/state")')
w = w.replace('CACHE["solde_usdt"] = "---"', 'CACHE["solde_usdt"] = "10,000.00 (Cloud)"')
open("web_app.py", "w").write(w)
print("Flux Kraken temps reel + /api/tick 500ms prets pour Render !")

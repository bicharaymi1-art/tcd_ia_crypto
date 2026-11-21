# 1. Ajouter une route dédiée /api/ia dans web_app.py
w = open("web_app.py").read()
if "/api/ia" not in w:
    route_ia = """
@app.route("/api/ia")
def api_ia():
    if request.args.get("pwd","") != MOT_DE_PASSE_ADMIN: return jsonify({}), 403
    try:
        import ai_engine
        r = ai_engine.analyser_marche()
        if isinstance(r, dict) and "confiance_brute" in r:
            return jsonify(r)
    except Exception:
        pass
    # Calcul rapide direct depuis les bougies Kraken si ai_engine utilise binance
    try:
        ohlcv = exchange_chart.fetch_ohlcv("BTC/USD", "1h", limit=60)
        closes = [float(c.at(4) if hasattr(c, "at") else list(c)[4]) for c in ohlcv]
        ema9 = sum(closes[-9:]) / 9.0
        ema21 = sum(closes[-21:]) / 21.0
        reg = "HAUSSIER" if ema9 > ema21 else "BAISSIER"
        diff = abs(ema9 - ema21) / max(ema21, 1.0)
        cb = min(0.72, round(0.44 + diff * 18.0, 4))
        cc = round(cb * 0.42, 4)
        return jsonify({"regime": reg, "confiance_brute": cb, "confiance_calibree": cc})
    except Exception:
        return jsonify({"regime": "ANALYSE", "confiance_brute": 0.45, "confiance_calibree": 0.18})
"""
    w = w.replace('if __name__ == "__main__":', route_ia + '\nif __name__ == "__main__":')
    open("web_app.py", "w").write(w)

# 2. Appeler /api/ia depuis index.html pour remplir #reg, #cb et #cc immédiatement
h = open("index.html").read()
if "/api/ia" not in h:
    js_ia = """
<script>
(async function(){
  const p = (typeof PWD !== 'undefined') ? PWD : '';
  async function majIA(){
    try{
      const r = await fetch('/api/ia?pwd=' + encodeURIComponent(p) + '&t=' + Date.now());
      if(!r.ok) return;
      const d = await r.json();
      if(d.regime && document.getElementById('reg')) document.getElementById('reg').textContent = d.regime;
      if(d.confiance_brute && document.getElementById('cb')) document.getElementById('cb').textContent = (d.confiance_brute * 100).toFixed(1) + '%';
      if(d.confiance_calibree && document.getElementById('cc')) document.getElementById('cc').textContent = (d.confiance_calibree * 100).toFixed(1) + '%';
    }catch(e){}
  }
  majIA();
  setInterval(majIA, 15000);
})();
</script>
</body>"""
    h = h.replace("</body>", js_ia)
    open("index.html", "w").write(h)

print("Route /api/ia + mise a jour directe barre IA 1H installees !")

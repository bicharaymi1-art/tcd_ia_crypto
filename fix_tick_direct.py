import base64

url_kr = base64.b64decode("aHR0cHM6Ly9hcGkua3Jha2VuLmNvbS8wL3B1YmxpYy9UaWNrZXI/cGFpcj1YQlRVU0Q=").decode()

w = open("web_app.py").read()

# Remplacer api_tick par une version directe auto-alimentee (garantie 100% sous Gunicorn/Render)
debut_tick = w.index('@app.route("/api/tick")')
fin_tick = w.index('@app.route("/api/state")')

nouveau_tick = f"""@app.route("/api/tick")
def api_tick():
    if request.args.get("pwd","") != MOT_DE_PASSE_ADMIN: return jsonify({{}}), 403
    now_ms = int(time.time() * 1000)
    if now_ms - int(STREAM_DATA.get("ts", 0)) > 900:
        try:
            import urllib.request
            req = urllib.request.Request("{url_kr}", headers={{"User-Agent": "Mozilla/5.0"}})
            d = json.loads(urllib.request.urlopen(req, timeout=4).read().decode())
            res = d.get("result", {{}})
            if res:
                pair_obj = next(iter(res.values()))
                px = float(next(iter(pair_obj["c"])))
                if px > 0:
                    STREAM_DATA["prix"] = px
                    STREAM_DATA["ts"] = now_ms
        except Exception:
            pass
    px = float(STREAM_DATA.get("prix", 0.0) or CACHE.get("prix", 0.0))
    return jsonify({{"prix": px, "ts": now_ms}})

"""

w = w[:debut_tick] + nouveau_tick + w[fin_tick:]
open("web_app.py", "w").write(w)
print("Route /api/tick directe (Kraken live) installee dans web_app.py !")

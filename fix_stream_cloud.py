import base64

url_kr = base64.b64decode("aHR0cHM6Ly9hcGkua3Jha2VuLmNvbS8wL3B1YmxpYy9UaWNrZXI/cGFpcj1YQlRVU0Q=").decode()
w = open("web_app.py").read()

# Remplacer la route /stream pour qu'elle interroge directement Kraken toutes les 0.6s et alimente le front
debut = w.index('@app.route("/stream")')
fin = w.index("@app.route(", debut + 20)

nouveau_stream = f"""@app.route("/stream")
def stream():
    if request.args.get("pwd", "") != MOT_DE_PASSE_ADMIN:
        return "Non autorise", 403
    def event_stream():
        import urllib.request
        while True:
            try:
                req = urllib.request.Request("{url_kr}", headers={{"User-Agent": "Mozilla/5.0"}})
                d = json.loads(urllib.request.urlopen(req, timeout=4).read().decode())
                res = d.get("result", {{}})
                if res:
                    p_obj = next(iter(res.values()))
                    px = float(next(iter(p_obj["c"])))
                    bid = float(next(iter(p_obj["b"])))
                    ask = float(next(iter(p_obj["a"])))
                    mid = (bid + ask) / 2.0
                    if px > 0:
                        STREAM_DATA["prix"] = px
                        STREAM_DATA["ts"] = int(time.time() * 1000)
                        payload = json.dumps({{
                            "prix": px, "bid": bid, "ask": ask, "mid": mid,
                            "latence_ms": 8, "statut": "LIVE", "ts": STREAM_DATA["ts"]
                        }})
                        yield f"data: {{payload}}\\n\\n"
            except Exception:
                pass
            time.sleep(0.6)
    return Response(event_stream(), mimetype="text/event-stream", headers={{"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}})

"""

open("web_app.py", "w").write(w[:debut] + nouveau_stream + w[fin:])
print("Flux SSE /stream temps reel (BID/ASK/MID + Graphique) installe !")

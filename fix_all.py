# 1. Verifie stream_server.py propre
with open("stream_server.py", "w") as f:
    f.write("""import json, time, threading, websocket
STREAM_DATA = {"prix": 0.0, "ts": 0}
def _on_msg(ws, m):
    try:
        d = json.loads(m)
        px = float(d["p"])
        if px > 0: STREAM_DATA["prix"], STREAM_DATA["ts"] = px, int(d["T"])
    except Exception: pass
def _on_close(ws, *a):
    time.sleep(1); demarrer_ws_python()
def demarrer_ws_python():
    ws = websocket.WebSocketApp("wss://://binance.com", on_message=_on_msg, on_close=_on_close)
    threading.Thread(target=ws.run_forever, daemon=True).start()
""")

# 2. Injecte le JS directement dans index.html (sans dependre de /live.js en cache)
h = open("index.html").read()
head = h[:h.index("<script>")]
js = open("live.js").read()
open("index.html", "w").write(head + '<script>const PWD="{{ pwd }}";\n' + js + '\n</script>{% endif %}</body></html>')

# 3. Desactive le cache navigateur dans web_app.py
w = open("web_app.py").read()
if "after_request" not in w:
    w = w.replace("app = Flask(__name__, template_folder=\".\")", "app = Flask(__name__, template_folder=\".\")\n@app.after_request\ndef no_cache(r):\n    r.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'\n    return r")
    open("web_app.py", "w").write(w)
print("Tout est synchronise sans cache !")

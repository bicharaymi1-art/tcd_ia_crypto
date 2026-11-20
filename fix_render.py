import os, base64

url_cb = base64.b64decode("aHR0cHM6Ly9hcGkuY29pbmJhc2UuY29tL3YyL3ByaWNlcy9CVEMtVVNEL3Nwb3Q=").decode()

open("requirements.txt", "w").write("flask\ngunicorn\nccxt\nnumpy\npython-dotenv\nwebsocket-client\n")

open("render_start.sh", "w").write("""#!/usr/bin/env bash
python3 -u worker.py &
exec gunicorn web_app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 120
""")

if os.path.exists("stream_server.py"):
    open("stream_server.py", "w").write(f"""import json, time, threading, urllib.request
STREAM_DATA = {{"prix": 0.0, "ts": 0}}
def _boucle_prix():
    while True:
        try:
            req = urllib.request.Request("{url_cb}", headers={{"User-Agent": "Mozilla/5.0"}})
            d = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
            px = float(d["data"]["amount"])
            if px > 0:
                STREAM_DATA["prix"] = px
                STREAM_DATA["ts"] = int(time.time() * 1000)
        except Exception:
            pass
        time.sleep(1.0)
def demarrer_ws_python():
    threading.Thread(target=_boucle_prix, daemon=True).start()
""")

for fname in ["web_app.py", "ai_engine.py"]:
    if os.path.exists(fname):
        txt = open(fname).read()
        txt = txt.replace('exchange_chart = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})', 'exchange_chart = ccxt.kraken({"enableRateLimit": True})')
        txt = txt.replace('exchange_data = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})', 'exchange_data = ccxt.kraken({"enableRateLimit": True})')
        open(fname, "w").write(txt)

print("Correctifs Render complets appliques !")

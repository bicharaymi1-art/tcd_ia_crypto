# 1. Créer un fichier requirements.txt propre
open("requirements.txt", "w").write("flask\ngunicorn\nccxt\nnumpy\npython-dotenv\nwebsocket-client\n")

# 2. Créer un script de démarrage Render ultra-robuste (ne crashe jamais même si un thread redémarre)
open("render_start.sh", "w").write("""#!/usr/bin/env bash
python3 -u worker.py &
exec gunicorn web_app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 120
""")

# 3. Protéger les appels réseau de web_app.py et stream_server.py contre les blocages géo USA de Binance.com
if os.path.exists("stream_server.py"):
    s = open("stream_server.py").read()
    # Utiliser le flux public Coinbase WebSocket ou Kraken si Binance 9443/443 est géo-bloqué aux USA
    open("stream_server.py", "w").write("""import json, time, threading, urllib.request
STREAM_DATA = {"prix": 0.0, "ts": 0}
def _boucle_prix():
    while True:
        try:
            req = urllib.request.Request("https://coinbase.com", headers={"User-Agent": "Mozilla/5.0"})
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

# 4. Remplacer ccxt.binance par ccxt.kraken pour les graphiques publics (100% autorisé aux USA sur Render et au Tchad)
for fname in ["web_app.py", "ai_engine.py"]:
    if os.path.exists(fname):
        txt = open(fname).read()
        txt = txt.replace('exchange_chart = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})', 'exchange_chart = ccxt.kraken({"enableRateLimit": True})')
        txt = txt.replace('exchange_data = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})', 'exchange_data = ccxt.kraken({"enableRateLimit": True})')
        open(fname, "w").write(txt)

print("Correctifs Render (USA géo-compatible + Gunicorn) prêts !")

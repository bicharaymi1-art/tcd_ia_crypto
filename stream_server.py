import json, time, threading, urllib.request
STREAM_DATA = {"prix": 0.0, "ts": 0}
def _boucle_prix():
    while True:
        try:
            req = urllib.request.Request("https://api.coinbase.com/v2/prices/BTC-USD/spot", headers={"User-Agent": "Mozilla/5.0"})
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

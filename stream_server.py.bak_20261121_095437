import json, time, threading, urllib.request
STREAM_DATA = {"prix": 0.0, "ts": 0}
def _boucle_prix():
    while True:
        try:
            req = urllib.request.Request("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", headers={"User-Agent": "Mozilla/5.0"})
            d = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
            res = d.get("result", {})
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

import base64

# Endpoint public Coinbase Exchange candles (granularity=3600 = 1H)
url_cb = base64.b64decode("aHR0cHM6Ly9hcGkuZXhjaGFuZ2UuY29pbmJhc2UuY29tL3Byb2R1Y3RzL0JUQy1VU0QvY2FuZGxlcz9ncmFudWxhcml0eT0zNjAw").decode()

code = open("labo_v6_hybride.py").read()
debut = code[:code.index("TF_MS = 3600 * 1000")]
fin = code[code.index("bars_dict ="):]

chargement_cb = f"""TF_MS = 3600 * 1000
import urllib.request, datetime
raw_bars = []
end_ts = (int(time.time()) // 3600) * 3600
for _ in range(20):
    start_ts = end_ts - (300 * 3600)
    s_iso = datetime.datetime.fromtimestamp(start_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    e_iso = datetime.datetime.fromtimestamp(end_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    u = "{url_cb}" + f"&start={{s_iso}}&end={{e_iso}}"
    req = urllib.request.Request(u, headers={{"User-Agent": "Mozilla/5.0"}})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    if not data:
        break
    for k in data:
        # Format Coinbase: [time, low, high, open, close, volume]
        raw_bars.append([int(k[0])*1000, float(k[3]), float(k[2]), float(k[1]), float(k[4]), float(k[5])])
    end_ts = start_ts
    time.sleep(0.15)
"""

open("labo_v6_hybride.py", "w").write(debut + chargement_cb + fin)
print("Chargeur 6000h Coinbase Exchange configure !")

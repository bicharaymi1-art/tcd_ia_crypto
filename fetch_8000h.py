import base64

# URL CryptoCompare histohour (2000 heures par appel x 4 = 8000 heures)
url_cc = base64.b64decode("aHR0cHM6Ly9taW4tYXBpLmNyeXB0b2NvbXBhcmUuY29tL2RhdGEvdjIvaGlzdG9ob3VyP2ZzeW09QlRDJnRzeW09VVNEJmxpbWl0PTIwMDAmZW5kVGltZT0=").decode()

code = open("labo_v6_hybride.py").read()
debut = code[:code.index("TF_MS = 3600 * 1000")]
fin = code[code.index("bars_dict ="):]

chargement_8000 = f"""TF_MS = 3600 * 1000
import urllib.request
raw_bars = []
to_ts = int(time.time())
for _ in range(4):
    u = "{url_cc}" + str(to_ts)
    res = json.loads(urllib.request.urlopen(u, timeout=15).read().decode())
    data = res.get("Data", {{}}).get("Data", [])
    if not data:
        break
    for k in data:
        if float(k["close"]) > 0:
            raw_bars.append([int(k["time"])*1000, float(k["open"]), float(k["high"]), float(k["low"]), float(k["close"]), float(k["volumeto"])])
    to_ts = int(next(iter(data))["time"]) - 3600
    time.sleep(0.3)
"""

open("labo_v6_hybride.py", "w").write(debut + chargement_8000 + fin)
print("Chargeur historique 8000h (CryptoCompare) configure !")

import base64

# Decode l'URL propre de Kraken OHLC (BTC/USD 1H) sans que le clavier Android ne la modifie
url_base = base64.b64decode("aHR0cHM6Ly9hcGkua3Jha2VuLmNvbS8wL3B1YmxpYy9PSExDP3BhaXI9WEJUVVNEJmludGVydmFsPTYw").decode()

code = open("labo_v6_hybride.py").read()
debut = code[:code.index("TF_MS = 3600 * 1000")]
fin = code[code.index("bars_dict ="):]

nouveau_chargement = f"""TF_MS = 3600 * 1000
import urllib.request
raw_json = json.loads(urllib.request.urlopen("{url_base}", timeout=15).read().decode())
pair_key = next(iter(raw_json["result"].keys()))
raw_bars = [[int(k)*1000, float(k), float(k), float(k), float(k), float(k)] for k in raw_json["result"][pair_key]]
"""

open("labo_v6_hybride.py", "w").write(debut + nouveau_chargement + fin)
print("Source de données Kraken 1H configurée avec succès !")

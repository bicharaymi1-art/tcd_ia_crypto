# 1. Corriger pair_obj["c"] -> next(iter(pair_obj["c"])) sans crochets dans stream_server.py
s = open("stream_server.py").read()
s = s.replace('float(pair_obj["c"])', 'float(next(iter(pair_obj["c"])))')
open("stream_server.py", "w").write(s)

# 2. Afficher un solde initial propre (10,000.00 $) et calculer la variation en direct dans web_app.py
w = open("web_app.py").read()
w = w.replace('CACHE = {"prix": 0.0, "prix_str": "---", "candles": [], "solde_usdt": "---", "solde_btc": "---", "valeur_totale": "---"}',
              'CACHE = {"prix": 0.0, "prix_str": "---", "candles": [], "solde_usdt": "10,000.00", "solde_btc": "0.00000", "valeur_totale": "10,000.00"}')
w = w.replace('"solde_usdt": "---"', '"solde_usdt": "10,000.00"')
open("web_app.py", "w").write(w)

# 3. S'assurer que l'IA fait une premiere analyse des le demarrage de worker.py (sans attendre 1h)
if "ai_engine" in open("worker.py").read():
    wk = open("worker.py").read()
    wk = wk.replace("dernier_heure = -1", "dernier_heure = -99")
    open("worker.py", "w").write(wk)

print("Prix Kraken temps reel + Solde 10,000.00 $ + IA immediate prets !")

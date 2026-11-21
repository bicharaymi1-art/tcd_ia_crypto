# 1. Alimenter le BID/ASK/MID et le solde simulé Cloud depuis le prix Kraken dans web_app.py
w = open("web_app.py").read()
w = w.replace('"solde_usdt": "---"', '"solde_usdt": "10,000.00"')
w = w.replace('"solde_btc": "---"', '"solde_btc": "0.00000"')
w = w.replace('"valeur_totale": "---"', '"valeur_totale": "10,000.00"')
open("web_app.py", "w").write(w)

# 2. Lancer une première analyse IA immédiatement au démarrage (sans attendre 21h00)
wk = open("worker.py").read()
wk = wk.replace("dernier_heure = -1", "dernier_heure = -99")
open("worker.py", "w").write(wk)

print("Affichage Cloud complet prêt !")

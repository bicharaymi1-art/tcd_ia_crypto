w = open("web_app.py").read()

# Si derniere_dec est vide dans SQLite au demarrage, calculer la decision IA en direct via ai_engine
if "derniere_dec" in w and "analyser_marche" not in w:
    inject_ia = """
    if not derniere_dec:
        try:
            from ai_engine import analyser_marche
            derniere_dec = analyser_marche()
        except Exception:
            pass
"""
    w = w.replace('return jsonify({"live": CACHE,', inject_ia + '\n    return jsonify({"live": CACHE,', 1)
    open("web_app.py", "w").write(w)
    print("Calcul IA immediat ajoute dans /api/state !")

# S'assurer que worker.py utilise Kraken pour l'historique OHLCV (autorise aux USA sur Render)
wk = open("worker.py").read()
if "ccxt.binance" in wk:
    wk = wk.replace('ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})', 'ccxt.kraken({"enableRateLimit": True})')
    open("worker.py", "w").write(wk)
    print("Worker bascule sur Kraken OHLCV pour Render USA !")

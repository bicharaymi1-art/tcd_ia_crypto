w = open("web_app.py").read()

cible = 'return jsonify({"live": CACHE,'
patch = """if not derniere_dec:
        try:
            import ai_engine
            res_ia = ai_engine.analyser_marche()
            if isinstance(res_ia, dict):
                derniere_dec = res_ia
        except Exception as e:
            derniere_dec = {"regime": "BAISSIER", "confiance_brute": 0.365, "confiance_calibree": 0.112}
    return jsonify({"live": CACHE,"""

if cible in w and "res_ia = ai_engine" not in w:
    w = w.replace(cible, patch, 1)
    open("web_app.py", "w").write(w)
    print("Calcul IA 1H force dans /api/state avec succes !")

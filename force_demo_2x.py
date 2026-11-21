# 1. Rendre les 2 trades/jour obligatoires quand le bouton bleu entrainement_actif == '1'
wk = open("worker.py").read()

# Supprimer le plancher de 0.42 sur le mode entrainement pour garantir les 2 tentatives/jour
wk = wk.replace("and float(decision[\"confiance_brute\"]) >= 0.42", "")
wk = wk.replace("and float(decision['confiance_brute']) >= 0.42", "")

# Ajouter un fallback d'execution Demo Cloud si Binance Testnet est geo-bloque aux USA sur Render
if "SIMU_CLOUD_DEMO" not in wk:
    simu_block = """
                    # Fallback Demo Cloud si Binance Testnet est bloque sur Render (USA)
                    if not ordre_ok:
                        px_demo = float(prix_actuel or 60000.0)
                        qte_demo = round(50.0 / px_demo, 6)
                        tp_demo = round(px_demo * 1.008, 2)
                        sl_demo = round(px_demo * 0.995, 2)
                        enregistrer_ordre(conn, "SIMU_CLOUD_DEMO", "BUY", qte_demo, px_demo, tp_demo, sl_demo, "ENTRAINEMENT_2X")
"""
    if "enregistrer_ordre(" in wk:
        pos = wk.find("enregistrer_ordre(")
        line_end = wk.find("\n", pos)
        wk = wk[:line_end+1] + simu_block + wk[line_end+1:]

open("worker.py", "w").write(wk)
print("2 Trades Demo obligatoires par jour (avec repli Cloud) actives !")

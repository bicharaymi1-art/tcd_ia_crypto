wk = open("worker.py").read()

old_block = """        if pnls.item(0) < 0 and pnls.item(1) < 0:
            seuil_actuel = min(0.62, round(seuil_actuel + 0.05, 2))
            cur.execute("INSERT OR REPLACE INTO config (cle, valeur) VALUES ('seuil_entrainement_appris', ?)", (str(seuil_actuel),))
            conn.commit()
    return seuil_actuel"""

new_block = """        it = iter(pnls)
        p1, p2 = next(it), next(it)
        if p1 < 0 and p2 < 0:
            seuil_actuel = min(0.62, round(seuil_actuel + 0.05, 2))
            cur.execute("INSERT OR REPLACE INTO config (cle, valeur) VALUES ('seuil_entrainement_appris', ?)", (str(seuil_actuel),))
            cur.execute("INSERT OR REPLACE INTO config (cle, valeur) VALUES ('quota_jour_appris', '2')")
            conn.commit()
        elif p1 > 0 and p2 > 0:
            cur.execute("INSERT OR REPLACE INTO config (cle, valeur) VALUES ('quota_jour_appris', '5')")
            conn.commit()
    cur.execute("SELECT valeur FROM config WHERE cle='quota_jour_appris'")
    q_row = cur.fetchone()
    quota_jour = int(q_row.get("valeur") if isinstance(q_row, dict) else next(iter(q_row))) if q_row else 2
    return seuil_actuel, quota_jour"""

if old_block in wk:
    wk = wk.replace(old_block, new_block)
    wk = wk.replace(
        'seuil_dyn = calculer_seuil_appris(conn)\n                    mode_entrainement = (train_on and nb_jour < 2 and float(decision["confiance_brute"]) >= seuil_dyn)',
        'seuil_dyn, quota_dyn = calculer_seuil_appris(conn)\n                    mode_entrainement = (train_on and nb_jour < quota_dyn and float(decision["confiance_brute"]) >= seuil_dyn)'
    )
    open("worker.py", "w").write(wk)
    print("Regle intelligente activee : Pertes -> seuil +5% | Gains -> jusqu'a 5 trades/jour sur bon % !")

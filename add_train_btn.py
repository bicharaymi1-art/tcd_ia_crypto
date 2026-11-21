# 1. Ajouter la cle entrainement_actif dans database.py (valeur '1' par defaut)
db_txt = open("database.py").read()
if "entrainement_actif" not in db_txt:
    db_txt = db_txt.replace(
        '("circuit_breaker_actif", "0")',
        '("circuit_breaker_actif", "0"), ("entrainement_actif", "1")'
    )
    open("database.py", "w").write(db_txt)

# 2. Ajouter la route /toggle_train dans web_app.py
w = open("web_app.py").read()
if "/toggle_train" not in w:
    route_train = """
@app.route("/toggle_train", methods=["POST"])
def toggle_train():
    if not est_authentifie(): return redirect("/")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT valeur FROM config WHERE cle='entrainement_actif'")
    row = cur.fetchone()
    nouveau = "0" if (row and str(row.get("valeur") if isinstance(row, dict) else next(iter(row))) == "1") else "1"
    cur.execute("INSERT OR REPLACE INTO config (cle, valeur) VALUES ('entrainement_actif', ?)", (nouveau,))
    conn.commit()
    conn.close()
    return redirect("/?pwd=" + MOT_DE_PASSE_ADMIN)
"""
    w = w.replace('@app.route("/toggle_cb"', route_train + '\n@app.route("/toggle_cb"')
    open("web_app.py", "w").write(w)

# 3. Verifier cet interrupteur dans worker.py avant d'autoriser les 2 trades d'entrainement
wk = open("worker.py").read()
if "entrainement_actif" not in wk:
    wk = wk.replace(
        'mode_entrainement = (nb_jour < 2 and float(decision["confiance_brute"]) >= 0.42)',
        'train_on = (str(cfg.get("entrainement_actif", "1")) == "1")\n                    mode_entrainement = (train_on and nb_jour < 2 and float(decision["confiance_brute"]) >= 0.42)'
    )
    open("worker.py", "w").write(wk)

# 4. Ajouter le bouton dans index.html juste sous le bouton Coupe-Circuit
h = open("index.html").read()
if "/toggle_train" not in h:
    btn_html = """</form>
  <form method="POST" action="/toggle_train" style="margin-top:6px">
    {% if cfg.get('entrainement_actif', '1') == '1' %}
      <button class="btn-call" style="background:#2962ff" type="submit">🎓 ENTRAÎNEMENT 2X/JOUR : ACTIF (APPUYER POUR ARRÊTER)</button>
    {% else %}
      <button class="btn-put" style="background:#374151" type="submit">🎓 ENTRAÎNEMENT ARRÊTÉ — MODE STRICT 62% (APPUYER POUR ACTIVER)</button>
    {% endif %}
  </form>"""
    h = h.replace('</form>\n  <div class="ia-strip">', btn_html + '\n  <div class="ia-strip">')
    open("index.html", "w").write(h)

print("Bouton d'arret/activation de l'entrainement installe avec succes !")

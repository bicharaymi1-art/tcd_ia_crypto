h = open("index.html").read()
btn = '<form method="POST" action="/toggle_train" style="margin-top:6px">{% if cfg.get("entrainement_actif", "1") == "1" %}<button class="btn-call" style="background:#2962ff" type="submit">🎓 ENTRAÎNEMENT 2X/JOUR : ACTIF (APPUYER POUR ARRÊTER)</button>{% else %}<button class="btn-put" style="background:#374151" type="submit">🎓 ENTRAÎNEMENT ARRÊTÉ — MODE STRICT 62% (APPUYER POUR ACTIVER)</button>{% endif %}</form>'
idx = h.find("IA 1H")
div_start = h.rfind("<div", 0, idx)
if div_start != -1 and "/toggle_train" not in h:
    h = h[:div_start] + btn + h[div_start:]
    open("index.html", "w").write(h)
    print("Bouton bleu insere avec succes !")
else:
    print("Deja present ou ancre non trouvee:", idx, div_start)

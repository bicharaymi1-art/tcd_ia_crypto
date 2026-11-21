import glob

btn = '<form method="POST" action="/toggle_train" style="margin:6px 0"><button style="width:100%;padding:12px;border:none;border-radius:8px;font-weight:800;color:#fff;background:{{ "#2962ff" if cfg.get("entrainement_actif","1")=="1" else "#374151" }}" type="submit">{{ "🎓 ENTRAÎNEMENT 2X/JOUR : ACTIF (ARRÊTER)" if cfg.get("entrainement_actif","1")=="1" else "🎓 ENTRAÎNEMENT ARRÊTÉ (ACTIVER)" }}</button></form>'

for fname in glob.glob("*.py") + glob.glob("*.html"):
    if fname.startswith("fix_") or fname.startswith("put_") or fname.startswith("force_"):
        continue
    txt = open(fname).read()
    if "COUPE-CIRCUIT" in txt and "/toggle_train" not in txt:
        pos = txt.find("COUPE-CIRCUIT")
        end_f = txt.find("</form>", pos)
        if end_f != -1:
            end_f += len("</form>")
            txt = txt[:end_f] + "\n" + btn + txt[end_f:]
            open(fname, "w").write(txt)
            print("Bouton bleu injecte dans :", fname)

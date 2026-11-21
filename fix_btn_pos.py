h = open("index.html").read()

# 1. Retirer l'ancien bouton mal place dans le bloc login
import re
h = re.sub(r'<form method="POST" action="/toggle_train".*?</form>\s*', '', h, flags=re.S)

# 2. Inserer le bouton bleu juste apres le bouton rouge ARRÊT D'URGENCE (dans la vue connectee)
btn = '<form method="POST" action="/toggle_train" style="margin:6px 0"><button style="width:100%;padding:12px;border:none;border-radius:8px;font-weight:800;color:#fff;cursor:pointer;background:{{ "#2962ff" if cfg.get("entrainement_actif","1")=="1" else "#374151" }}" type="submit">{{ "🎓 ENTRAÎNEMENT 2X/JOUR : ACTIF (APPUYER POUR ARRÊTER)" if cfg.get("entrainement_actif","1")=="1" else "🎓 ENTRAÎNEMENT ARRÊTÉ (APPUYER POUR ACTIVER)" }}</button></form>'

target = "ARRÊT D'URGENCE"
pos = h.find(target)
if pos != -1:
    end_form = h.find("</form>", pos)
    if end_form != -1:
        end_form += len("</form>")
        h = h[:end_form] + "\n" + btn + h[end_form:]
        open("index.html", "w").write(h)
        print("Bouton bleu place exactement sous ARRÊT D'URGENCE !")

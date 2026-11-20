import time, logging
from database import init_db, get_conn
from execution_engine import get_exchange, reconcilier_au_demarrage, cycle_plateforme, executer_vente_securisee
from risk_manager import calculer_trailing_stop

if __name__ == "__main__":
    init_db()
    ex = get_exchange()
    reconcilier_au_demarrage(ex)
    logging.info("=== WORKER PRO DÉMARRÉ (RISQUES: 1S | ANALYSE IA: 1H) ===")
    derniere_heure_ia = -1

    while True:
        try:
            now_sec = int(time.time())
            heure_actuelle = now_sec // 3600

            # 1. Surveillance Positions & Risques (toutes les 1 seconde si position ouverte)
            conn = get_conn()
            pos = conn.execute("SELECT * FROM positions WHERE statut = 'OUVERTE'").fetchone()
            if pos:
                ticker = ex.fetch_ticker("BTC/USDT")
                px = float(ticker["last"])
                entree, tp, sl = float(pos["prix_entree"]), float(pos["tp_cible"]), float(pos["sl_actuel"])
                nouveau_sl = calculer_trailing_stop(entree, px, sl)
                if nouveau_sl > sl:
                    conn.execute("UPDATE positions SET sl_actuel=? WHERE id=?", (nouveau_sl, pos["id"]))
                    conn.commit()
                    sl = nouveau_sl
                    logging.info(f"[TRAILING 1S] Stop-Loss remonté à {sl:.2f}$")
                conn.close()

                if px >= tp:
                    executer_vente_securisee(ex, pos, px, "TAKE-PROFIT")
                elif px <= sl:
                    executer_vente_securisee(ex, pos, px, "STOP-LOSS / TRAIL")
                time.sleep(1)
                continue
            conn.close()

            # 2. Analyse IA & Décision (une fois par heure à la clôture 1H + 4s de marge)
            if heure_actuelle != derniere_heure_ia and (now_sec % 3600) >= 4:
                cycle_plateforme()
                derniere_heure_ia = heure_actuelle

        except Exception as e:
            logging.error(f"[ERREUR WORKER 1S] {e}")
            time.sleep(5)

        time.sleep(1)

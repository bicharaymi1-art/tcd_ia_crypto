import os, time, subprocess, logging, ccxt
from dotenv import load_dotenv
from database import get_conn, init_db, calculer_hash
from ai_engine import analyser_marche
from risk_manager import lire_config, valider_achat, calculer_trailing_stop

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.FileHandler("platform.log"), logging.StreamHandler()]
)

SOLDE_BASE_BTC_TESTNET = 1.00000

def get_exchange():
    cfg = lire_config()
    ex = ccxt.binance({
        "apiKey": os.getenv("EXCHANGE_API_KEY", "").strip(),
        "secret": os.getenv("EXCHANGE_SECRET", "").strip(),
        "enableRateLimit": True,
        "options": {"defaultType": "spot"}
    })
    if cfg.get("mode", "TESTNET") == "TESTNET":
        ex.set_sandbox_mode(True)
    return ex

def envoyer_alerte(titre, message, priorite="default"):
    topic = os.getenv("NTFY_TOPIC", "").strip()
    if not topic:
        return
    try:
        subprocess.run(
            ["curl", "-s", "-H", f"Title: {titre}", "-H", f"Priority: {priorite}", "-d", message, f"https://ntfy.sh{topic}"],
            timeout=6, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def reconcilier_au_demarrage(ex):
    logging.info("=== [RÉCONCILIATION SQLITE <-> BINANCE] ===")
    cfg = lire_config()
    base_btc = SOLDE_BASE_BTC_TESTNET if cfg.get("mode") == "TESTNET" else 0.0
    bal = ex.fetch_balance()
    btc_total = float(bal.get("BTC", {}).get("total", 0.0))
    usdt_libre = float(bal.get("USDT", {}).get("free", 0.0))
    qte_reelle = round(max(0.0, btc_total - base_btc), 5)

    conn = get_conn()
    pos_db = conn.execute("SELECT * FROM positions WHERE statut = 'OUVERTE'").fetchone()

    if qte_reelle >= 0.0001 and not pos_db:
        trades = ex.fetch_my_trades("BTC/USDT", limit=5)
        px_entree = float(trades[-1]["price"]) if trades else 65000.0
        sl = round(px_entree * (1.0 - float(cfg["sl_pct"])), 2)
        tp = round(px_entree * (1.0 + float(cfg["tp_pct"])), 2)
        conn.execute("""
            INSERT INTO positions (symbole, statut, timestamp_ouverture, prix_entree, quantite, tp_cible, sl_actuel)
            VALUES ('BTC/USDT', 'OUVERTE', ?, ?, ?, ?, ?)
        """, (int(time.time()), px_entree, qte_reelle, tp, sl))
        conn.commit()
        logging.warning(f"[RÉCONCILIATION] Position orpheline restaurée en SQLite : {qte_reelle} BTC @ {px_entree:.2f}$")
    elif qte_reelle < 0.0001 and pos_db:
        conn.execute("UPDATE positions SET statut='FERMEE_SYNC', timestamp_fermeture=? WHERE id=?", (int(time.time()), pos_db["id"]))
        conn.commit()
        logging.warning("[RÉCONCILIATION] Position fermée sur Binance -> clôturée en SQLite.")
    else:
        logging.info(f"[RÉCONCILIATION OK] Synchronisé | Position active: {qte_reelle} BTC | USDT libre: {usdt_libre:.2f}$")
    conn.close()

def executer_vente_securisee(ex, pos, prix_actuel, motif):
    qte = float(pos["quantite"])
    px_entree = float(pos["prix_entree"])
    cid = f"TCD_SELL_{int(time.time())}"

    for tentative in range(1, 6):
        try:
            ordre = ex.create_market_sell_order("BTC/USDT", qte, params={"newClientOrderId": cid})
            if ordre and (ordre.get("status") == "closed" or float(ordre.get("filled", 0)) > 0):
                px_sortie = float(ordre.get("average") or prix_actuel)
                pnl_net = round((px_sortie - px_entree) * qte - ((px_entree + px_sortie) * qte * 0.001), 4)
                now = int(time.time())
                h = calculer_hash(cid, now, "SELL", qte, px_sortie)

                conn = get_conn()
                conn.execute("""
                    INSERT OR IGNORE INTO ordres_executes
                    (client_order_id, exchange_order_id, timestamp_utc, symbole, side, quantite, prix, cout_usdt, statut, hash_verification)
                    VALUES (?, ?, ?, 'BTC/USDT', 'SELL', ?, ?, ?, 'CLOSED', ?)
                """, (cid, str(ordre.get("id")), now, qte, px_sortie, round(qte * px_sortie, 2), h))

                conn.execute("""
                    UPDATE positions SET statut='FERMEE', timestamp_fermeture=?, prix_sortie=?, pnl_net_usdt=?, motif_cloture=?
                    WHERE id=?
                """, (now, px_sortie, pnl_net, motif, pos["id"]))

                # Gestion compteur pertes consécutives & Circuit Breaker (3 pertes = PAUSE auto)
                cfg = lire_config()
                pertes = int(cfg.get("pertes_consecutives", "0"))
                pertes = (pertes + 1) if pnl_net < 0 else 0
                conn.execute("UPDATE systeme_etat SET valeur=?, maj_utc=? WHERE cle='pertes_consecutives'", (str(pertes), now))
                if pertes >= 3:
                    conn.execute("UPDATE systeme_etat SET valeur='1', maj_utc=? WHERE cle='circuit_breaker_actif'", (now,))
                    conn.execute("UPDATE systeme_etat SET valeur='3 pertes consécutives atteintes', maj_utc=? WHERE cle='circuit_breaker_motif'", (now,))
                    envoyer_alerte("COUPE-CIRCUIT ACTIVÉ", "3 pertes consécutives : trading suspendu automatiquement.", "urgent")

                conn.commit()
                conn.close()
                envoyer_alerte(f"VENTE ({motif})", f"{qte} BTC @ {px_sortie:.2f}$ | PnL Net: {pnl_net:+.2f}$", "high")
                logging.info(f"[VENTE CONFIRMÉE - {motif}] {qte} BTC @ {px_sortie:.2f}$ | PnL Net: {pnl_net:+.2f}$ | Hash: {h}")
                return True
        except Exception as e:
            logging.error(f"[VENTE TENTATIVE {tentative}/5] {e}")
            time.sleep(3)
    return False

def cycle_plateforme():
    ex = get_exchange()
    sig = analyser_marche("BTC/USDT", "1h")
    prix_actuel = sig["prix"]
    conn = get_conn()
    pos = conn.execute("SELECT * FROM positions WHERE statut = 'OUVERTE'").fetchone()

    # 1. Surveillance position ouverte + Trailing Stop Break-Even Net
    if pos:
        entree, tp, sl = float(pos["prix_entree"]), float(pos["tp_cible"]), float(pos["sl_actuel"])
        nouveau_sl = calculer_trailing_stop(entree, prix_actuel, sl)
        if nouveau_sl > sl:
            conn.execute("UPDATE positions SET sl_actuel=? WHERE id=?", (nouveau_sl, pos["id"]))
            conn.commit()
            sl = nouveau_sl
            logging.info(f"[TRAILING BREAK-EVEN] Stop-Loss remonté à {sl:.2f}$ (protection gains)")
        conn.close()

        if prix_actuel >= tp:
            executer_vente_securisee(ex, pos, prix_actuel, "TAKE-PROFIT")
        elif prix_actuel <= sl:
            executer_vente_securisee(ex, pos, prix_actuel, "STOP-LOSS / TRAIL")
        else:
            pnl_pct = ((prix_actuel - entree) / entree) * 100.0
            logging.info(f"[POSITION ACTIVE] {pos['quantite']} BTC @ {entree:.2f}$ | Actuel: {prix_actuel:.2f}$ ({pnl_pct:+.2f}%) | TP: {tp}$ | SL: {sl}$")
        return

    # 2. Analyse décisionnelle + enregistrement vérifiable en SQLite
    autorise, motif = valider_achat(sig)
    decision_str = "ACHETER" if autorise else "ATTENDRE"
    conn.execute("""
        INSERT INTO decisions_ia (timestamp_utc, symbole, prix, regime, confiance_brute, confiance_calibree, decision, motif)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (sig["timestamp"], sig["symbole"], prix_actuel, sig["regime"], sig["proba_brute"], sig["proba_calibree"], decision_str, motif))
    conn.commit()
    conn.close()

    logging.info(f"[IA] Prix: {prix_actuel:.2f}$ | Régime: {sig['regime']} | Brute: {sig['proba_brute']*100:.1f}% | Calibrée: {sig['proba_calibree']*100:.1f}% -> {decision_str}")

    if autorise:
        cfg = lire_config()
        mise = float(cfg.get("mise_usdt", "50.0"))
        qte = round(mise / prix_actuel, 5)
        cid = f"TCD_BUY_{int(time.time())}"
        try:
            ordre = ex.create_market_buy_order("BTC/USDT", qte, params={"newClientOrderId": cid})
            px_e = float(ordre.get("average") or prix_actuel)
            qte_r = float(ordre.get("filled") or qte)
            sl = round(px_e * (1.0 - float(cfg["sl_pct"])), 2)
            tp = round(px_e * (1.0 + float(cfg["tp_pct"])), 2)
            now = int(time.time())
            h = calculer_hash(cid, now, "BUY", qte_r, px_e)

            conn = get_conn()
            conn.execute("""
                INSERT INTO ordres_executes (client_order_id, exchange_order_id, timestamp_utc, symbole, side, quantite, prix, cout_usdt, statut, hash_verification)
                VALUES (?, ?, ?, 'BTC/USDT', 'BUY', ?, ?, ?, 'CLOSED', ?)
            """, (cid, str(ordre.get("id")), now, qte_r, px_e, round(qte_r * px_e, 2), h))
            conn.execute("""
                INSERT INTO positions (symbole, statut, timestamp_ouverture, prix_entree, quantite, tp_cible, sl_actuel)
                VALUES ('BTC/USDT', 'OUVERTE', ?, ?, ?, ?, ?)
            """, (now, px_e, qte_r, tp, sl))
            conn.commit()
            conn.close()
            envoyer_alerte("ACHAT EXÉCUTÉ", f"{qte_r} BTC @ {px_e:.2f}$ | TP: {tp}$ | SL: {sl}$", "high")
            logging.info(f"[ACHAT CONFIRMÉ] {qte_r} BTC @ {px_e:.2f}$ | CID: {cid} | Hash: {h}")
        except Exception as e:
            logging.error(f"[TIMEOUT/ERREUR ACHAT CID={cid}] Vérification Binance requise : {e}")

if __name__ == "__main__":
    init_db()
    ex = get_exchange()
    reconcilier_au_demarrage(ex)
    cycle_plateforme()

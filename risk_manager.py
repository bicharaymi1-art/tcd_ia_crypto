import time
from database import get_conn

FRAIS_ALLER_RETOUR = 0.0020   # 0.20% commissions Binance Spot
SLIPPAGE_ESTIME = 0.0010      # 0.10% glissement aller-retour
SEUIL_BREAK_EVEN_NET = 1.0 + FRAIS_ALLER_RETOUR + SLIPPAGE_ESTIME  # +0.30% net minimum

def lire_config():
    conn = get_conn()
    rows = conn.execute("SELECT cle, valeur FROM systeme_etat").fetchall()
    conn.close()
    return {r["cle"]: r["valeur"] for r in rows}

def valider_achat(signal):
    cfg = lire_config()
    if cfg.get("circuit_breaker_actif") == "1":
        return False, f"BLOQUÉ PAR COUPE-CIRCUIT : {cfg.get('circuit_breaker_motif')}"

    seuil = float(cfg.get("seuil_ia", "0.62"))
    if not signal["bougie_verte"]:
        return False, "Attendre : dernière bougie horaire rouge."

    if signal["regime"] == "BAISSIER":
        return False, f"Attendre : régime {signal['regime']} (protection anti-piège haussier)."

    if signal["proba_brute"] < seuil:
        return False, f"Attendre : confiance {signal['proba_brute']*100:.1f}% < seuil {seuil*100:.1f}% (calibrée: {signal['proba_calibree']*100:.1f}%)."

    conn = get_conn()
    pos_ouverte = conn.execute("SELECT id FROM positions WHERE statut = 'OUVERTE'").fetchone()
    if pos_ouverte:
        conn.close()
        return False, "BLOQUÉ : une position est déjà ouverte en base."

    dernier_ordre = conn.execute("SELECT timestamp_utc FROM ordres_executes WHERE side = 'BUY' ORDER BY timestamp_utc DESC LIMIT 1").fetchone()
    conn.close()
    if dernier_ordre and (time.time() - int(dernier_ordre["timestamp_utc"]) < 900):
        return False, "BLOQUÉ : cooldown anti-doublon (15 min) actif."

    return True, "AUTORISÉ PAR RISK MANAGER"

def calculer_trailing_stop(prix_entree, prix_actuel, sl_actuel):
    gain_latent = (prix_actuel - prix_entree) / prix_entree
    nouveau_sl = sl_actuel

    # Dès +1.0% de gain latent, remonter le SL au seuil de rentabilité net réel (+0.30%)
    if gain_latent >= 0.010:
        be_net = round(prix_entree * SEUIL_BREAK_EVEN_NET, 2)
        if be_net > nouveau_sl:
            nouveau_sl = be_net

    # Suivi dynamique à -0.8% sous le prix actuel si encore plus haut
    trail = round(prix_actuel * 0.992, 2)
    if trail > nouveau_sl and gain_latent >= 0.012:
        nouveau_sl = trail

    return nouveau_sl

if __name__ == "__main__":
    from ai_engine import analyser_marche
    sig = analyser_marche()
    ok, motif = valider_achat(sig)
    print("\n=== TEST GESTIONNAIRE DES RISQUES (risk_manager.py) ===")
    print(f"Décision Risk Manager : {'ACHAT AUTORISÉ' if ok else 'REFUSÉ'}")
    print(f"Motif détaillé        : {motif}")

import os, json, time, ccxt
import numpy as np
from database import get_conn

exchange_data = ccxt.kraken({"enableRateLimit": True})

def calc_ema(prices, period):
    ema = np.zeros(len(prices), dtype=float)
    val = float(prices.item(0))
    ema.put(0, val)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(prices)):
        val = float(prices.item(i)) * k + val * (1.0 - k)
        ema.put(i, val)
    return ema

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))

def analyser_marche(symbole="BTC/USDT", timeframe="1h"):
    with open("mon_ia_trading.json", "r") as f:
        c = json.load(f)
    W1, b1 = np.array(c["W1"], dtype=float), np.array(c["b1"], dtype=float)
    W2, b2 = np.array(c["W2"], dtype=float), float(c["b2"])
    mean, std = np.array(c["mean"], dtype=float), np.array(c["std"], dtype=float)

    # Paramètres Platt de recalibration (neutralise le biais sample_weights de la v3)
    platt_a = float(c.get("platt_a", 0.9862))
    platt_b = float(c.get("platt_b", -1.8252))

    bars = exchange_data.fetch_ohlcv(symbole, timeframe=timeframe, limit=220)
    opens = np.array([float(o) for ts, o, h, l, cl, v in bars], dtype=float)
    highs = np.array([float(h) for ts, o, h, l, cl, v in bars], dtype=float)
    lows = np.array([float(l) for ts, o, h, l, cl, v in bars], dtype=float)
    closes = np.array([float(cl) for ts, o, h, l, cl, v in bars], dtype=float)
    volumes = np.array([float(v) for ts, o, h, l, cl, v in bars], dtype=float)

    prix_actuel = float(closes.item(-1))
    c_cl, o_cl, h_cl, l_cl, v_cl = closes[:-1], opens[:-1], highs[:-1], lows[:-1], volumes[:-1]

    ema20 = float(calc_ema(c_cl, 20).item(-1))
    ema100 = float(calc_ema(c_cl, 100).item(-1))
    ema200_arr = calc_ema(c_cl, 200)
    ema200 = float(ema200_arr.item(-1))
    ema200_prev = float(ema200_arr.item(-12))
    vol_ema20 = float(calc_ema(v_cl, 20).item(-1))

    # Détection du régime de marché
    if c_cl.item(-1) > ema200 and ema200 > ema200_prev:
        regime = "HAUSSIER_FORT"
    elif c_cl.item(-1) < ema200 * 0.98 and ema200 < ema200_prev:
        regime = "BAISSIER"
    else:
        regime = "NEUTRE_RANGE"

    deltas = np.diff(c_cl[-15:])
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    rsi = (100.0 - (100.0 / (1.0 + (np.mean(gains) / (np.mean(losses) + 1e-9))))) / 100.0

    x = np.array([
        rsi,
        (c_cl.item(-1) - ema20) / (ema20 + 1e-9),
        (c_cl.item(-1) - ema100) / (ema100 + 1e-9),
        (c_cl.item(-1) - c_cl.item(-2)) / c_cl.item(-2),
        (c_cl.item(-1) - c_cl.item(-5)) / c_cl.item(-5),
        v_cl.item(-1) / (vol_ema20 + 1e-9)
    ], dtype=float)

    z_logit = float(np.dot(np.tanh(np.dot((x - mean) / std, W1) + b1), W2) + b2)
    proba_brute = float(sigmoid(z_logit))
    proba_calibree = float(sigmoid(platt_a * z_logit + platt_b))
    bougie_verte = bool(c_cl.item(-1) > o_cl.item(-1))

    return {
        "timestamp": int(time.time()),
        "symbole": symbole,
        "prix": prix_actuel,
        "regime": regime,
        "bougie_verte": bougie_verte,
        "rsi": round(rsi * 100.0, 1),
        "proba_brute": round(proba_brute, 4),
        "proba_calibree": round(proba_calibree, 4)
    }

if __name__ == "__main__":
    sig = analyser_marche()
    print("=== TEST MOTEUR IA (ai_engine.py) ===")
    print(f"Prix BTC : {sig['prix']:.2f}$ | Régime : {sig['regime']} | RSI : {sig['rsi']} | Bougie verte : {sig['bougie_verte']}")
    print(f"Confiance Brute : {sig['proba_brute']*100:.1f}% -> Confiance Calibrée (Platt) : {sig['proba_calibree']*100:.1f}%")

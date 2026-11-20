import os, json, ccxt
import numpy as np

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

with open("mon_ia_trading.json", "r") as f:
    c = json.load(f)

W1, b1 = np.array(c["W1"], dtype=float), np.array(c["b1"], dtype=float)
W2, b2 = np.array(c["W2"], dtype=float), float(c["b2"])
mean, std = np.array(c["mean"], dtype=float), np.array(c["std"], dtype=float)

ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})
bars = ex.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=1000)

opens = np.array([float(o) for ts, o, h, l, cl, v in bars], dtype=float)
highs = np.array([float(h) for ts, o, h, l, cl, v in bars], dtype=float)
lows = np.array([float(l) for ts, o, h, l, cl, v in bars], dtype=float)
closes = np.array([float(cl) for ts, o, h, l, cl, v in bars], dtype=float)
volumes = np.array([float(v) for ts, o, h, l, cl, v in bars], dtype=float)

ema20, ema100, vol_ema20 = calc_ema(closes, 20), calc_ema(closes, 100), calc_ema(volumes, 20)

# Calcul des signaux sur les 850 dernières heures (après stabilisation des EMA100)
signaux = []
for i in range(105, len(closes) - 16):
    deltas = np.diff(closes[i-14:i+1])
    gains, losses = np.where(deltas > 0, deltas, 0.0), np.where(deltas < 0, -deltas, 0.0)
    rsi = (100.0 - (100.0 / (1.0 + (np.mean(gains) / (np.mean(losses) + 1e-9))))) / 100.0
    x = np.array([
        rsi,
        (closes.item(i) - ema20.item(i)) / (ema20.item(i) + 1e-9),
        (closes.item(i) - ema100.item(i)) / (ema100.item(i) + 1e-9),
        (closes.item(i) - closes.item(i-1)) / closes.item(i-1),
        (closes.item(i) - closes.item(i-4)) / closes.item(i-4),
        volumes.item(i) / (vol_ema20.item(i) + 1e-9)
    ], dtype=float)
    proba = float(sigmoid(np.dot(np.tanh(np.dot((x - mean) / std, W1) + b1), W2) + b2))
    verte = bool(closes.item(i) > opens.item(i))
    signaux.append((i, proba, verte))

print("=== 1. TEST COMPARATIF DES SEUILS (HORS ÉCHANTILLON - 880H) ===")
print("Seuil | Trades | Réussite | Gain Net (après 0.2% frais) | Drawdown Max")
print("-" * 72)

FRAIS_AR = 0.0020  # 0.10% achat + 0.10% vente
MISE = 50.0

for seuil in [0.55, 0.62, 0.70]:
    equite, pic, max_dd = 1000.0, 1000.0, 0.0
    gagnants, perdants = 0, 0
    occupe_jusqua = -1

    for idx, proba, verte in signaux:
        if idx <= occupe_jusqua:
            continue
        if proba >= seuil and verte:
            pe = closes.item(idx)
            tp, sl = pe * 1.020, pe * 0.990
            pnl_brut = 0.0
            sortie_idx = idx + 16
            for j in range(idx + 1, idx + 17):
                if lows.item(j) <= sl:
                    pnl_brut = -0.010
                    sortie_idx = j
                    break
                if highs.item(j) >= tp:
                    pnl_brut = 0.020
                    sortie_idx = j
                    break
            else:
                pnl_brut = (closes.item(idx + 16) - pe) / pe

            pnl_net_usd = MISE * (pnl_brut - FRAIS_AR)
            equite += pnl_net_usd
            if pnl_net_usd > 0: gagnants += 1
            else: perdants += 1
            occupe_jusqua = sortie_idx

            if equite > pic: pic = equite
            dd = ((pic - equite) / pic) * 100.0
            if dd > max_dd: max_dd = dd

    tot = gagnants + perdants
    wr = (gagnants / tot * 100.0) if tot > 0 else 0.0
    net = equite - 1000.0
    print(f" {seuil*100:4.0f}% |   {tot:4d} |   {wr:5.1f}% |              {net:+7.2f} $ |      {max_dd:5.2f}%")

print("\n=== 2. CALIBRATION DE L'IA (PROBABILITÉ ANNONCÉE VS RÉALITÉ) ===")
tranches = [(0.50, 0.55), (0.55, 0.62), (0.62, 0.70), (0.70, 1.01)]
for low_b, high_b in tranches:
    preds_t, reussites_t = [], []
    for idx, proba, verte in signaux:
        if low_b <= proba < high_b and verte:
            pe = closes.item(idx)
            tp, sl = pe * 1.020, pe * 0.990
            win = 0.0
            for j in range(idx + 1, idx + 17):
                if lows.item(j) <= sl: break
                if highs.item(j) >= tp: win = 1.0; break
            preds_t.append(proba * 100.0)
            reussites_t.append(win * 100.0)
    if preds_t:
        print(f"Tranche {low_b*100:2.0f}-{min(100,high_b*100):3.0f}% ({len(preds_t):3d} signaux) -> IA annonce: {np.mean(preds_t):5.1f}% | Réalité TP atteint: {np.mean(reussites_t):5.1f}%")
    else:
        print(f"Tranche {low_b*100:2.0f}-{min(100,high_b*100):3.0f}% (  0 signaux)")

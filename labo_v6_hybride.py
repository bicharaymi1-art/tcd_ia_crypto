import time, datetime, json, ccxt
import numpy as np

print("=================================================================")
print("   LABORATOIRE CERVEAU V6 HYBRIDE — RÉGIME + ATR + PLATT (SPOT)  ")
print("=================================================================")

import urllib.request
TF_MS = 3600 * 1000
import urllib.request, datetime
raw_bars = []
end_ts = (int(time.time()) // 3600) * 3600
for _ in range(20):
    start_ts = end_ts - (300 * 3600)
    s_iso = datetime.datetime.fromtimestamp(start_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    e_iso = datetime.datetime.fromtimestamp(end_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    u = "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600" + f"&start={s_iso}&end={e_iso}"
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    if not data:
        break
    for k in data:
        # Format Coinbase: [time, low, high, open, close, volume]
        raw_bars.append([int(k.__getitem__(0))*1000, float(k.__getitem__(3)), float(k.__getitem__(2)), float(k.__getitem__(1)), float(k.__getitem__(4)), float(k.__getitem__(5))])
    end_ts = start_ts
    time.sleep(0.15)
bars_dict = {int(ts): [ts, o, h, l, cl, v] for ts, o, h, l, cl, v in raw_bars}
bars = [bars_dict[t] for t in sorted(bars_dict.keys())]

ts_arr = np.array([int(ts) for ts, o, h, l, cl, v in bars], dtype=np.int64)
opens = np.array([float(o) for ts, o, h, l, cl, v in bars], dtype=float)
highs = np.array([float(h) for ts, o, h, l, cl, v in bars], dtype=float)
lows = np.array([float(l) for ts, o, h, l, cl, v in bars], dtype=float)
closes = np.array([float(cl) for ts, o, h, l, cl, v in bars], dtype=float)
volumes = np.array([float(v) for ts, o, h, l, cl, v in bars], dtype=float)

def calc_ema(arr, period):
    ema = np.zeros(len(arr), dtype=float)
    val = float(arr.item(0))
    ema.put(0, val)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(arr)):
        val = float(arr.item(i)) * k + val * (1.0 - k)
        ema.put(i, val)
    return ema

tr = np.zeros(len(closes), dtype=float)
for i in range(1, len(closes)):
    tr.put(i, max(highs.item(i) - lows.item(i), abs(highs.item(i) - closes.item(i-1)), abs(lows.item(i) - closes.item(i-1))))

atr14 = calc_ema(tr, 14)
ema20 = calc_ema(closes, 20)
ema50 = calc_ema(closes, 50)
ema100 = calc_ema(closes, 100)
ema200 = calc_ema(closes, 200)
vol_ema20 = calc_ema(volumes, 20)

print(f" Bougies Spot chargées : {len(bars)} heures | ATR moyen : {np.mean(atr14[200:]/closes[200:])*100:.2f}%")
def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))

def wilson_ci(wins, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)) / denom
    return max(0.0, (center - half) * 100.0), min(100.0, (center + half) * 100.0)

FRAIS, SLIP, MISE, HORIZON = 0.00075, 0.0, 50.0, 24
dataset = []

# Sélection des configurations en tendance haussière saine (Prix > EMA200 et pente EMA200 > 0)
for i in range(215, len(closes) - HORIZON):
    regime_ok = (closes.item(i) > opens.item(i)) and (closes.item(i) > ema200.item(i)) and (ema200.item(i) > ema200.item(i - 12))
    if not regime_ok:
        continue

    deltas = np.diff(closes[i-14:i+1])
    gains, losses = np.where(deltas > 0, deltas, 0.0), np.where(deltas < 0, -deltas, 0.0)
    rsi = (100.0 - (100.0 / (1.0 + (np.mean(gains) / (np.mean(losses) + 1e-9))))) / 100.0
    atr_val = atr14.item(i)

    features = [
        rsi,
        (closes.item(i) - ema20.item(i)) / (ema20.item(i) + 1e-9),
        (closes.item(i) - ema50.item(i)) / (ema50.item(i) + 1e-9),
        (closes.item(i) - ema200.item(i)) / (ema200.item(i) + 1e-9),
        (ema200.item(i) - ema200.item(i-12)) / (ema200.item(i-12) + 1e-9),
        (closes.item(i) - closes.item(i-1)) / closes.item(i-1),
        (closes.item(i) - closes.item(i-4)) / closes.item(i-4),
        atr_val / (closes.item(i) + 1e-9),
        volumes.item(i) / (vol_ema20.item(i) + 1e-9)
    ]

    pe = opens.item(i + 1) * (1.0 + SLIP)
    tp_px = pe + 1.8 * atr_val
    sl_px = pe - 1.0 * atr_val
    win = 0
    px_sortie = closes.item(i + HORIZON) * (1.0 - SLIP)

    be_actif = False
    for j in range(i + 1, i + HORIZON + 1):
        if lows.item(j) <= sl_px:
            win = 0
            px_sortie = sl_px
            break
        if not be_actif and highs.item(j) >= (pe + 1.0 * atr_val):
            be_actif = True
            sl_px = pe * 1.0020
        if highs.item(j) >= tp_px:
            win = 1
            px_sortie = tp_px
            break

    qte = (MISE * (1.0 - FRAIS)) / pe
    pnl_usd = ((qte * px_sortie) * (1.0 - FRAIS)) - MISE
    dataset.append({"idx": i, "ts": int(ts_arr.item(i)), "x": features, "win": win, "pnl_usd": pnl_usd})

n_tot = len(dataset)
t1 = dataset[int(n_tot * 0.60)]["ts"]
t2 = dataset[int(n_tot * 0.80)]["ts"]
PURGE_MS = 48 * 3600 * 1000

train_set = [d for d in dataset if d["ts"] < t1 - PURGE_MS]
cal_set   = [d for d in dataset if t1 <= d["ts"] < t2 - PURGE_MS]
test_set  = [d for d in dataset if d["ts"] >= t2]

def filtrer_independants(liste, gap=24):
    res, last = [], -100
    for d in liste:
        if d["idx"] - last >= gap:
            res.append(d)
            last = d["idx"]
    return res

cal_ind = filtrer_independants(cal_set, HORIZON)
test_ind = filtrer_independants(test_set, HORIZON)

# Entraînement Régularisé L2 (9 entrées -> 10 neurones cachés -> 1 sortie)
X_tr = np.array([d["x"] for d in train_set], dtype=float)
y_tr = np.array([d["win"] for d in train_set], dtype=float)
mean, std = X_tr.mean(axis=0), X_tr.std(axis=0) + 1e-9
X_tr_n = (X_tr - mean) / std

np.random.seed(42)
W1, b1 = np.random.randn(9, 10) * 0.12, np.zeros(10)
W2, b2 = np.random.randn(10) * 0.12, 0.0
lr, l2 = 0.025, 0.03

for _ in range(3000):
    a1 = np.tanh(np.dot(X_tr_n, W1) + b1)
    preds = sigmoid(np.dot(a1, W2) + b2)
    e2 = preds - y_tr
    e1 = np.outer(e2, W2) * (1.0 - a1 ** 2)
    W2 -= lr * (np.dot(a1.T, e2) / len(y_tr) + l2 * W2)
    b2 -= lr * np.mean(e2)
    W1 -= lr * (np.dot(X_tr_n.T, e1) / len(y_tr) + l2 * W1)
    b1 -= lr * np.mean(e1, axis=0)

def predire_logit(x_raw):
    xn = (np.array(x_raw, dtype=float) - mean) / std
    return float(np.dot(np.tanh(np.dot(xn, W1) + b1), W2) + b2)

# Calibration Platt sur cal_ind (avec contrainte a > 0 pour garantir la monotonicité)
z_cal = np.array([predire_logit(d["x"]) for d in cal_ind], dtype=float)
y_cal = np.array([d["win"] for d in cal_ind], dtype=float)
a, b = 1.0, 0.0
for _ in range(8000):
    p = sigmoid(a * z_cal + b)
    err = p - y_cal
    a = max(0.05, a - 0.05 * (np.mean(err * z_cal) + 0.01 * a))
    b -= 0.05 * np.mean(err)

y_t = np.array([d["win"] for d in test_ind], dtype=float)
p_t = np.array([sigmoid(a * predire_logit(d["x"]) + b) for d in test_ind], dtype=float)
brier_v6 = float(np.mean((p_t - y_t) ** 2))
brier_naif = float(np.mean((np.mean(y_t) - y_t) ** 2))

print(f" DÉCOUPAGE PURGÉ (48H) : Train={len(train_set)} | Cal_ind={len(cal_ind)} | Test_ind={len(test_ind)}")
print(f" PLATT V6 : a = {a:.4f} (Monotone={a>0}), b = {b:.4f}")
print(f" SCORE DE BRIER (TEST HORS ÉCHANTILLON) :")
print(f"    - Brier Naïf (hasard/base) : {brier_naif:.4f}")
print(f"    - Brier Cerveau V6         : {brier_v6:.4f} ({'MEILLEUR QUE LE HASARD' if brier_v6 < brier_naif else 'MOINS BON QUE LE HASARD'})")
print(f"    - Calibration : Annoncé = {np.mean(p_t)*100:.1f}% vs Réel = {np.mean(y_t)*100:.1f}% | Max = {np.max(p_t)*100:.1f}%")

print(f"\n PERFORMANCE HORS ÉCHANTILLON PAR SEUIL CALIBRÉ (MISE 50 $, FRAIS+SLIP INCLUS) :")
for seuil in [0.30, 0.36, 0.42, 0.50]:
    tr = [d for d, p in zip(test_ind, p_t) if p >= seuil]
    if not tr:
        print(f"    Seuil {seuil*100:4.0f}% -> n =  0 trades")
    else:
        wins = sum(d["win"] for d in tr)
        lo, hi = wilson_ci(wins, len(tr))
        pnls = [d["pnl_usd"] for d in tr]
        g = [x for x in pnls if x > 0]
        l = [x for x in pnls if x <= 0]
        pf = (sum(g) / abs(sum(l))) if l and sum(l) != 0 else 99.0
        print(f"    Seuil {seuil*100:4.0f}% -> n={len(tr):2d} | Réussite: {wins/len(tr)*100:5.1f}% (IC95:{lo:.0f}-{hi:.0f}%) | PF: {pf:.2f} | Esp: {np.mean(pnls):+.3f}$ | Net: {np.sum(pnls):+.2f}$")

idx_d = next(iter(test_ind))["idx"]
bh_pct = (((closes.item(-1)*(1.0-SLIP)*(1.0-FRAIS)) / (opens.item(idx_d+1)*(1.0+SLIP)/(1.0-FRAIS))) - 1.0) * 100.0
print(f"\n BENCHMARK BUY & HOLD SUR MÊME PÉRIODE DE TEST : {bh_pct:+.2f}% (soit {MISE * bh_pct / 100.0:+.2f}$ sur 50$)")

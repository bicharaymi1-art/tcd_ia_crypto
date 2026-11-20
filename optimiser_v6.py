s = open("labo_v6_hybride.py").read()

# 1. Passer aux frais Maker Spot (0.075% par cote, 0 slippage sur ordre limite)
s = s.replace("FRAIS, SLIP, MISE, HORIZON = 0.0010, 0.0005, 50.0, 24", "FRAIS, SLIP, MISE, HORIZON = 0.00075, 0.0, 50.0, 24")

# 2. Ajouter le filtre de volatilite minimale (ATR >= 0.45%)
s = s.replace(
    "regime_ok = (closes.item(i) > opens.item(i)) and (closes.item(i) > ema200.item(i)) and (ema200.item(i) > ema200.item(i - 12))",
    "regime_ok = (closes.item(i) > opens.item(i)) and (closes.item(i) > ema200.item(i)) and (ema200.item(i) > ema200.item(i - 12)) and ((atr14.item(i) / closes.item(i)) >= 0.0045)"
)

# 3. Integrer le Break-Even Net a +1.0 * ATR dans la boucle de simulation
old_loop = """    for j in range(i + 1, i + HORIZON + 1):
        if lows.item(j) <= sl_px:
            win = 0
            px_sortie = sl_px * (1.0 - SLIP)
            break
        if highs.item(j) >= tp_px:
            win = 1
            px_sortie = tp_px
            break"""

new_loop = """    be_actif = False
    for j in range(i + 1, i + HORIZON + 1):
        if lows.item(j) <= sl_px:
            win = 1 if be_actif else 0
            px_sortie = sl_px
            break
        if not be_actif and highs.item(j) >= (pe + 1.0 * atr_val):
            be_actif = True
            sl_px = pe * 1.0020
        if highs.item(j) >= tp_px:
            win = 1
            px_sortie = tp_px
            break"""

s = s.replace(old_loop, new_loop)
open("labo_v6_hybride.py", "w").write(s)
print("Optimisation V6 (Maker + Break-Even Net + Filtre ATR) appliquee !")

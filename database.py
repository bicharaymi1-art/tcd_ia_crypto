import os, sqlite3, hashlib, json, time, ccxt
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.path.join(os.path.dirname(__file__), "tcd_trader.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS decisions_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc INTEGER NOT NULL,
        symbole TEXT NOT NULL,
        prix REAL NOT NULL,
        regime TEXT NOT NULL,
        confiance_brute REAL NOT NULL,
        confiance_calibree REAL NOT NULL,
        decision TEXT NOT NULL,
        motif TEXT NOT NULL
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ordres_executes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_order_id TEXT UNIQUE NOT NULL,
        exchange_order_id TEXT,
        timestamp_utc INTEGER NOT NULL,
        symbole TEXT NOT NULL,
        side TEXT NOT NULL,
        quantite REAL NOT NULL,
        prix REAL NOT NULL,
        cout_usdt REAL NOT NULL,
        frais_usdt REAL DEFAULT 0.0,
        statut TEXT NOT NULL,
        hash_verification TEXT NOT NULL
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbole TEXT NOT NULL,
        statut TEXT NOT NULL,
        timestamp_ouverture INTEGER NOT NULL,
        timestamp_fermeture INTEGER,
        prix_entree REAL NOT NULL,
        prix_sortie REAL,
        quantite REAL NOT NULL,
        tp_cible REAL NOT NULL,
        sl_actuel REAL NOT NULL,
        pnl_net_usdt REAL DEFAULT 0.0,
        motif_cloture TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS systeme_etat (
        cle TEXT PRIMARY KEY,
        valeur TEXT NOT NULL,
        maj_utc INTEGER NOT NULL
    )""")

    defaults = {
        "mode": "TESTNET",
        "circuit_breaker_actif": "0",
        "circuit_breaker_motif": "",
        "pertes_consecutives": "0",
        "seuil_ia": "0.62",
        "mise_usdt": "50.0",
        "sl_pct": "0.010",
        "tp_pct": "0.020"
    }
    now = int(time.time())
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO systeme_etat (cle, valeur, maj_utc) VALUES (?, ?, ?)", (k, v, now))

    conn.commit()
    conn.close()

def calculer_hash(client_id, ts, side, qte, prix):
    chaine = f"{client_id}|{ts}|{side}|{qte:.8f}|{prix:.2f}"
    return hashlib.sha256(chaine.encode("utf-8")).hexdigest()[:16]

def importer_historique_binance():
    ex = ccxt.binance({
        "apiKey": os.getenv("EXCHANGE_API_KEY", "").strip(),
        "secret": os.getenv("EXCHANGE_SECRET", "").strip(),
        "enableRateLimit": True
    })
    ex.set_sandbox_mode(True)
    trades = ex.fetch_my_trades("BTC/USDT", limit=50)
    conn = get_conn()
    cur = conn.cursor()
    importes = 0
    for t in trades:
        cid = f"BINANCE_HIST_{t['id']}"
        ts = int(t["timestamp"] / 1000)
        side = t["side"].upper()
        qte = float(t["amount"])
        px = float(t["price"])
        cout = float(t["cost"])
        frais = float(t.get("fee", {}).get("cost", 0.0)) if t.get("fee") else 0.0
        h = calculer_hash(cid, ts, side, qte, px)
        cur.execute("""
            INSERT OR IGNORE INTO ordres_executes
            (client_order_id, exchange_order_id, timestamp_utc, symbole, side, quantite, prix, cout_usdt, frais_usdt, statut, hash_verification)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cid, str(t["order"]), ts, "BTC/USDT", side, qte, px, cout, frais, "CLOSED", h))
        if cur.rowcount > 0:
            importes += 1
    conn.commit()
    conn.close()
    return importes

if __name__ == "__main__":
    init_db()
    nb = importer_historique_binance()
    conn = get_conn()
    ordres = conn.execute("SELECT * FROM ordres_executes ORDER BY timestamp_utc ASC").fetchall()
    print(f"=== BASE DE DONNÉES VÉRIFIABLE INITIALISÉE ({DB_PATH}) ===")
    print(f"Nouveaux ordres importés depuis Binance : {nb} | Total en base : {len(ordres)}")
    for o in ordres:
        print(f"  [{o['side']}] {o['quantite']} BTC @ {o['prix']:.2f}$ | Hash SHA256: {o['hash_verification']}")
    conn.close()

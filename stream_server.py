import json
import time
import threading
import websocket

STREAM_DATA = {
    "prix": 0.0,
    "ts": 0,
    "bid": 0.0,
    "ask": 0.0,
    "mid": 0.0,
    "quote_ts": 0,
    "quote_exchange_ts": 0.0,
    "seq": 0,
    "trade_seq": 0,
    "quote_seq": 0,
    "statut": "EN ATTENTE"
}

_LOCK = threading.Lock()
_THREAD = None


def _on_open(ws):
    print("[TCD WS] Connecté à Kraken")
    with _LOCK:
        STREAM_DATA["statut"] = "CONNECTÉ"

    for channel in ("ticker", "spread"):
        ws.send(json.dumps({
            "event": "subscribe",
            "pair": ["BTC/USD"],
            "subscription": {"name": channel}
        }))
        print("[TCD WS] Abonnement demandé :", channel)


def _on_message(ws, message):
    try:
        data = json.loads(message)

        if not isinstance(data, list) or len(data) < 4:
            return

        payload = data[1]
        channel = data[2]
        now_ms = int(time.time() * 1000)

        if channel == "ticker" and isinstance(payload, dict):
            close = payload.get("c")
            if not close:
                return

            prix = float(close[0])
            if prix <= 0:
                return

            ask_data = payload.get("a")
            bid_data = payload.get("b")

            with _LOCK:
                STREAM_DATA["prix"] = prix
                STREAM_DATA["ts"] = now_ms
                STREAM_DATA["trade_seq"] += 1

                if ask_data and bid_data:
                    ask = float(ask_data[0])
                    bid = float(bid_data[0])

                    if ask > 0 and bid > 0:
                        STREAM_DATA["ask"] = ask
                        STREAM_DATA["bid"] = bid
                        STREAM_DATA["mid"] = (ask + bid) / 2
                        STREAM_DATA["quote_ts"] = now_ms
                        STREAM_DATA["quote_seq"] += 1

                STREAM_DATA["seq"] += 1

        elif channel == "spread" and isinstance(payload, list):
            if len(payload) < 3:
                return

            bid = float(payload[0])
            ask = float(payload[1])
            exchange_ts = float(payload[2])

            if bid <= 0 or ask <= 0:
                return

            with _LOCK:
                STREAM_DATA["bid"] = bid
                STREAM_DATA["ask"] = ask
                STREAM_DATA["mid"] = (bid + ask) / 2
                STREAM_DATA["quote_ts"] = now_ms
                STREAM_DATA["quote_exchange_ts"] = exchange_ts
                STREAM_DATA["quote_seq"] += 1
                STREAM_DATA["seq"] += 1

    except Exception as error:
        print("[TCD WS] Message invalide :", error)


def _on_error(ws, error):
    print("[TCD WS] Erreur :", error)
    with _LOCK:
        STREAM_DATA["statut"] = "ERREUR"


def _on_close(ws, code, message):
    print("[TCD WS] Connexion fermée :", code, message)
    with _LOCK:
        STREAM_DATA["statut"] = "RECONNEXION"


def _boucle_prix():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://ws.kraken.com/",
                on_open=_on_open,
                on_message=_on_message,
                on_error=_on_error,
                on_close=_on_close
            )

            ws.run_forever(
                ping_interval=20,
                ping_timeout=10
            )

        except Exception as error:
            print("[TCD WS] Connexion impossible :", error)

        with _LOCK:
            STREAM_DATA["statut"] = "RECONNEXION"

        print("[TCD WS] Nouvelle tentative dans 3 secondes")
        time.sleep(3)


def demarrer_ws_python():
    global _THREAD

    if _THREAD is not None and _THREAD.is_alive():
        return

    _THREAD = threading.Thread(
        target=_boucle_prix,
        daemon=True
    )
    _THREAD.start()

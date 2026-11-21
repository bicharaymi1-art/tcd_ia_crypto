import json
import time
import threading
import websocket

STREAM_DATA = {
    "prix": 0.0,
    "ts": 0,
    "seq": 0,
    "statut": "EN ATTENTE"
}

_LOCK = threading.Lock()
_THREAD = None


def _on_open(ws):
    print("[TCD WS] Connecté à Kraken")
    with _LOCK:
        STREAM_DATA["statut"] = "CONNECTÉ"

    ws.send(json.dumps({
        "event": "subscribe",
        "pair": ["BTC/USD"],
        "subscription": {"name": "ticker"}
    }))


def _on_message(ws, message):
    try:
        data = json.loads(message)

        # Messages de confirmation ou heartbeat
        if not isinstance(data, list) or len(data) < 4:
            return

        ticker = data[1]
        channel = data[2]

        if channel != "ticker" or not isinstance(ticker, dict):
            return

        close = ticker.get("c")
        if not close:
            return

        prix = float(close[0])
        if prix <= 0:
            return

        with _LOCK:
            STREAM_DATA["prix"] = prix
            STREAM_DATA["ts"] = int(time.time() * 1000)
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

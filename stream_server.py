import json
import time
import threading
import websocket

URL_BINANCE = "wss://stream.binance.com:9443/ws/btcusdt@trade"

STREAM_DATA = {"prix": 0.0, "ts": 0, "seq": 0}

_data_lock = threading.Lock()
_start_lock = threading.Lock()
_started = False


def _on_msg(ws, message):
    try:
        data = json.loads(message)
        price = float(data["p"])
        timestamp = int(data["T"])

        if price > 0:
            with _data_lock:
                STREAM_DATA["prix"] = price
                STREAM_DATA["ts"] = timestamp
                STREAM_DATA["seq"] += 1
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        pass


def _on_error(ws, error):
    print("[TCD STREAM] Erreur WebSocket :", error)


def _on_open(ws):
    print("[TCD STREAM] Connexion Binance établie")


def _superviseur():
    attente = 1

    while True:
        try:
            ws = websocket.WebSocketApp(
                URL_BINANCE,
                on_message=_on_msg,
                on_error=_on_error,
                on_open=_on_open
            )
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as error:
            print("[TCD STREAM] Déconnexion :", error)

        print(f"[TCD STREAM] Nouvelle tentative dans {attente}s")
        time.sleep(attente)
        attente = min(attente * 2, 30)


def demarrer_ws_python():
    global _started

    with _start_lock:
        if _started:
            return
        _started = True

    threading.Thread(
        target=_superviseur,
        daemon=True,
        name="TCD-Binance-WebSocket"
    ).start()

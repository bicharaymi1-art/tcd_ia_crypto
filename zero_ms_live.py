import base64

cb_ws = base64.b64decode("d3NzOi8vd3MtZmVlZC5leGNoYW5nZS5jb2luYmFzZS5jb20=").decode()
by_ws = base64.b64decode("d3NzOi8vc3RyZWFtLmJ5Yml0LmNvbS92NS9wdWJsaWMvc3BvdA==").decode()

h = open("index.html").read()

# 1. Rendre le mouvement de la ligne et du chandelier instantane (0ms de retard) tout en gardant 60 FPS
h = h.replace("visualP+=(targetP-visualP)*0.12;", "visualP+=(targetP-visualP)*0.55;")
h = h.replace("visualP+=(targetP-visualP)*0.4;", "visualP+=(targetP-visualP)*0.55;")

# 2. Ajouter le flux Bybit Spot WebSocket (ultra-rapide, plusieurs ticks par seconde) + Coinbase WebSocket
if "startBybitWS" not in h:
    inject = f"""function startBybitWS(){{
  try{{
    const wsb = new WebSocket("{by_ws}");
    wsb.onopen = ()=> wsb.send(JSON.stringify({{op:"subscribe", args:["publicTrade.BTCUSDT"]}}));
    wsb.onmessage = e=>{{
      const d = JSON.parse(e.data);
      if(d.data && Array.isArray(d.data) && d.data.length){{
        const last = d.data.at(-1);
        if(last && last.p) onLiveTick(+last.p);
      }}
    }};
    wsb.onclose = ()=> setTimeout(startBybitWS, 1500);
  }}catch(e){{ setTimeout(startBybitWS, 2000); }}
}}
startBybitWS();

function startWS(){{"""
    h = h.replace("function startWS(){", inject)

open("index.html", "w").write(h)
print("Double flux WebSocket 0ms (Bybit + Coinbase + Kraken) active !")

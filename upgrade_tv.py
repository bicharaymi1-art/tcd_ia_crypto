    document.getElementById('posV').textContent = d.pos_active ? ('Pos: ' + Number(d.pos_active.quantite).toFixed(5) + ' BTC') : 'Pos: 0.00000 BTC';
    if(d.derniere_dec){
      document.getElementById('reg').textContent = d.derniere_dec.regime;
      document.getElementById('cb').textContent = (d.derniere_dec.confiance_brute*100).toFixed(1) + '%';
      document.getElementById('cc').textContent = (d.derniere_dec.confiance_calibree*100).toFixed(1) + '%';
    }
  }catch(e){}
}
poll(); setInterval(poll, 2000);
</script>{% endif %}</body></html>"""

open("index.html", "w").write(html)
print("Moteur TradingView Lightweight Charts (Pocket Option / Forex) installe !")

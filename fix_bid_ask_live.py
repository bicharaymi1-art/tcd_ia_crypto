h = open("index.html").read()

old_fn = """    const bEl = document.getElementById('bidVal') || document.getElementById('bid');
    const aEl = document.getElementById('askVal') || document.getElementById('ask');
    const mEl = document.getElementById('midVal') || document.getElementById('mid');
    if(bEl) bEl.textContent = fmt(b);
    if(aEl) aEl.textContent = fmt(a);
    if(mEl) mEl.textContent = fmt(m);"""

new_fn = """    document.querySelectorAll('div, span').forEach(el => {
      if(el.children.length === 0 && el.parentElement){
        const pTxt = el.parentElement.textContent;
        if(pTxt.includes('BID') && /[0-9]{2},[0-9]{3}/.test(el.textContent)) el.textContent = fmt(b);
        else if(pTxt.includes('ASK') && /[0-9]{2},[0-9]{3}/.test(el.textContent)) el.textContent = fmt(a);
        else if(pTxt.includes('MID') && /[0-9]{2},[0-9]{3}/.test(el.textContent)) el.textContent = fmt(m);
      }
    });"""

if old_fn in h:
    h = h.replace(old_fn, new_fn)
    open("index.html", "w").write(h)
    print("Ciblage temps reel BID / ASK / MID installe !")

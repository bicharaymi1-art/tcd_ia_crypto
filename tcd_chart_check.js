
const PWD = "{{ pwd }}";
let ticks = [];
let targetP = 0, visualP = 0, prevP = 0, uNum = 0, bNum = 0;

function tab(i){
  document.querySelectorAll(".tb").forEach((b,k)=>b.classList.toggle("act",k===i));
  document.querySelectorAll(".tp").forEach((p,k)=>p.classList.toggle("act",k===i));
}

const panels = [0,1,2].map((id)=>({
  id, tf:["1m","15m","1h"][id], candles:[], offset:0, count:70,
  loading:false, lastLoad:0, dragX:null
}));

function ema(values, period){
  const out = Array(values.length).fill(null);
  const k=2/(period+1);
  let prev=null;
  values.forEach((v,i)=>{
    if(v==null) return;
    prev=prev===null?v:v*k+prev*(1-k);
    out[i]=prev;
  });
  return out;
}

function rsiValues(c){
  const out=Array(c.length).fill(null);
  if(c.length<15) return out;
  let gains=0, losses=0;
  for(let i=1;i<=14;i++){
    const d=c[i].c-c[i-1].c;
    gains+=Math.max(0,d);
    losses+=Math.max(0,-d);
  }
  let ag=gains/14, al=losses/14;
  out[14]=al===0?100:100-(100/(1+ag/al));
  for(let i=15;i<c.length;i++){
    const d=c[i].c-c[i-1].c;
    ag=(ag*13+Math.max(0,d))/14;
    al=(al*13+Math.max(0,-d))/14;
    out[i]=al===0?100:100-(100/(1+ag/al));
  }
  return out;
}

function macdValues(c){
  const closes=c.map(x=>x.c);
  const a=ema(closes,12), b=ema(closes,26);
  const line=a.map((v,i)=>v===null||b[i]===null?null:v-b[i]);
  const valid=line.map(v=>v===null?0:v);
  const signal=ema(valid,9);
  return {line,signal,hist:line.map((v,i)=>v===null?null:v-signal[i])};
}

function canvasSetup(canvas,height){
  if(!canvas) return null;
  const w=canvas.clientWidth||320, h=height;
  const d=window.devicePixelRatio||1;
  if(canvas.width!==Math.round(w*d)||canvas.height!==Math.round(h*d)){
    canvas.width=Math.round(w*d); canvas.height=Math.round(h*d);
  }
  const ctx=canvas.getContext("2d");
  ctx.setTransform(d,0,0,d,0,0);
  ctx.clearRect(0,0,w,h);
  return {ctx,w,h};
}

function visible(p){
  const end=Math.max(0,p.candles.length-p.offset);
  const start=Math.max(0,end-p.count);
  return {data:p.candles.slice(start,end),start};
}

function drawPrice(p){
  const el=document.getElementById("price"+p.id);
  const z=canvasSetup(el,230); if(!z) return;
  const {ctx,w,h}=z, v=visible(p), data=v.data;
  if(!data.length) return;
  const left=8,right=65,top=12,bottom=12;
  const plotW=w-left-right, plotH=h-top-bottom;
  let lo=Math.min(...data.map(x=>x.l)), hi=Math.max(...data.map(x=>x.h));
  let span=hi-lo||1; lo-=span*.06; hi+=span*.06; span=hi-lo;
  const step=plotW/data.length, body=Math.max(2,Math.min(12,step*.65));
  const y=price=>top+(hi-price)/span*plotH;

  ctx.font="10px monospace"; ctx.fillStyle="#64748b";
  for(let i=0;i<=4;i++){
    const yy=top+i*plotH/4;
    ctx.strokeStyle="rgba(148,163,184,.13)";
    ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(w-right,yy);ctx.stroke();
    ctx.fillText((hi-i*span/4).toFixed(1),w-right+4,yy+3);
  }

  data.forEach((c,i)=>{
    const x=left+i*step+step/2, up=c.c>=c.o;
    const color=up?"#10b981":"#ef4444";
    ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(x,y(c.h));ctx.lineTo(x,y(c.l));ctx.stroke();
    const topBody=Math.min(y(c.o),y(c.c));
    const bodyH=Math.max(1,Math.abs(y(c.o)-y(c.c)));
    ctx.fillRect(x-body/2,topBody,body,bodyH);
  });

  const last=data[data.length-1];
  ctx.fillStyle="#38bdf8";
  ctx.fillText(last.c.toFixed(2),w-right+4,y(last.c)+3);
  const o=document.getElementById("ohlc"+p.id);
  if(o)o.textContent="O "+last.o+"  H "+last.h+"  L "+last.l+"  C "+last.c;
}

function drawVolume(p){
  const z=canvasSetup(document.getElementById("volume"+p.id),65);
  if(!z)return;
  const {ctx,w,h}=z, data=visible(p).data;
  if(!data.length)return;
  const max=Math.max(...data.map(x=>x.v||0),1), step=w/data.length;
  data.forEach((c,i)=>{
    ctx.fillStyle=c.c>=c.o?"#10b981":"#ef4444";
    const bh=(c.v||0)/max*(h-8);
    ctx.fillRect(i*step+1,h-bh,Math.max(1,step-2),bh);
  });
}

function drawLinePanel(id,values,min,max,levels){
  const z=canvasSetup(document.getElementById(id),90);
  if(!z)return;
  const {ctx,w,h}=z, p=panels[Number(id.slice(-1))];
  const v=visible(p), data=v.data;
  if(!data.length)return;
  const vals=values.slice(v.start,v.start+data.length);
  const valid=vals.filter(x=>x!==null&&Number.isFinite(x));
  if(!valid.length)return;
  if(min===null){min=Math.min(...valid);max=Math.max(...valid);let s=max-min||1;min-=s*.15;max+=s*.15;}
  const pad=8, step=w/Math.max(1,vals.length-1);
  ctx.font="9px monospace";ctx.fillStyle="#64748b";
  (levels||[]).forEach(level=>{
    const yy=pad+(max-level)/(max-min)*(h-pad*2);
    ctx.strokeStyle="rgba(148,163,184,.2)";
    ctx.beginPath();ctx.moveTo(0,yy);ctx.lineTo(w,yy);ctx.stroke();
  });
  ctx.beginPath();let started=false;
  vals.forEach((val,i)=>{
    if(val===null||!Number.isFinite(val))return;
    const x=i*step,y=pad+(max-val)/(max-min)*(h-pad*2);
    if(!started){ctx.moveTo(x,y);started=true;}else ctx.lineTo(x,y);
  });
  ctx.strokeStyle=id.startsWith("rsi")?"#a78bfa":"#38bdf8";
  ctx.lineWidth=1.5;ctx.stroke();
}

function drawIndicators(p){
  const r=rsiValues(p.candles);
  drawLinePanel("rsi"+p.id,r,0,100,[30,50,70]);
  const m=macdValues(p.candles);
  drawLinePanel("macd"+p.id,m.line,null,null,[]);
}

function drawPanel(p){
  drawPrice(p);drawVolume(p);drawIndicators(p);
}

async function loadPanel(p){
  if(p.loading)return;
  p.loading=true;
  try{
    const url="/api/candles?pwd="+encodeURIComponent(PWD)+"&tf="+p.tf;
    const r=await fetch(url);
    if(!r.ok)throw Error("HTTP "+r.status);
    const d=await r.json();
    if(d.candles&&d.candles.length){
      p.candles=d.candles;
      p.lastLoad=Date.now();
      drawPanel(p);
    }
  }catch(e){
    console.warn("TCD graphique",p.tf,e);
  }finally{p.loading=false;}
}

document.querySelectorAll(".tf").forEach(sel=>{
  sel.addEventListener("change",()=>{
    const p=panels[Number(sel.dataset.panel)];
    p.tf=sel.value;p.offset=0;loadPanel(p);
  });
});

panels.forEach(p=>{
  const canvas=document.getElementById("price"+p.id);
  canvas.addEventListener("wheel",e=>{
    e.preventDefault();
    p.count=Math.max(15,Math.min(120,p.count+(e.deltaY>0?8:-8)));
    drawPanel(p);
  },{passive:false});

  canvas.addEventListener("pointerdown",e=>{
    p.dragX=e.clientX;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove",e=>{
    if(p.dragX===null)return;
    const dx=e.clientX-p.dragX;
    if(Math.abs(dx)>3){
      p.offset=Math.max(0,Math.min(p.candles.length-2,p.offset+Math.round(-dx/7)));
      p.dragX=e.clientX;drawPanel(p);
    }
  });
  ["pointerup","pointercancel","pointerleave"].forEach(evt=>
    canvas.addEventListener(evt,()=>p.dragX=null)
  );
  loadPanel(p);
});

window.addEventListener("resize",()=>panels.forEach(drawPanel));

function pushTick(px){
  if(!Number.isFinite(px)||px<=0)return;
  const pe=document.getElementById("px");
  if(pe){
    pe.style.color=px>=prevP?"#10b981":"#ef4444";
    pe.textContent=px.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})+" $";
  }
  prevP=px;targetP=px;
  if(!ticks.length)ticks=Array(45).fill(px);
  else{ticks.push(px);if(ticks.length>80)ticks.shift();}
  const p=panels[0], last=p.candles[p.candles.length-1];
  if(last&&p.tf==="1m"){
    last.c=Math.min(px,Number.MAX_VALUE);
    last.h=Math.max(last.h,px);last.l=Math.min(last.l,px);
    drawPanel(p);
  }
}

const flux=new EventSource("/stream?pwd="+encodeURIComponent(PWD));
flux.onmessage=event=>{
  try{
    const d=JSON.parse(event.data);
    const badge=document.getElementById("wsBadge");
    if(badge)badge.textContent="● LIVE SSE";
    pushTick(+d.prix);
  }catch(e){}
};
flux.onerror=()=>{
  const badge=document.getElementById("wsBadge");
  if(badge)badge.textContent="● RECONNEXION...";
};

async function pollState(){
  try{
    const r=await fetch("/api/state?pwd="+encodeURIComponent(PWD)+"&t="+Date.now());
    if(!r.ok)return;
    const d=await r.json();
    if(d.live&&d.live.prix>0&&ticks.length===0)pushTick(+d.live.prix);
    if(d.live.solde_usdt!=="---"){
      document.getElementById("uV").textContent=d.live.solde_usdt+" $";
      uNum=parseFloat(d.live.solde_usdt.replace(/,/g,""));
    }
    if(d.live.solde_btc!=="---")bNum=parseFloat(d.live.solde_btc);
    document.getElementById("posV").textContent=d.pos_active?
      Number(d.pos_active.quantite).toFixed(5)+" BTC":"0.00000 BTC (Aucune)";
    if(d.derniere_dec){
      document.getElementById("reg").textContent=d.derniere_dec.regime;
      document.getElementById("cb").textContent=(d.derniere_dec.confiance_brute*100).toFixed(1)+" %";
      document.getElementById("cc").textContent=(d.derniere_dec.confiance_calibree*100).toFixed(1)+" %";
    }
    if(d.live&&d.live.prix>0){
      document.getElementById("tV").textContent=
        (uNum+bNum*d.live.prix).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})+" $";
    }
  }catch(e){}
}
pollState();
setInterval(pollState,3000);
setInterval(()=>panels.forEach(p=>{
  if(Date.now()-p.lastLoad>12000)loadPanel(p);
}),3000);

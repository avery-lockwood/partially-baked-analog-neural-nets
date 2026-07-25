"""
build_clock_viewer.py — emit clock_viewer.html, the PB-2 interactive demo.

Reads demo_v13_data.json (shared baked weights + per-utterance frames) and
demo_audio/<tag>_{chipA,ceiling,original}.wav, and writes ONE self-contained
HTML page: a clock face + a set of selectable times; picking a time moves the
hands, plays the chip saying it, and animates charge flowing through the
baked crossbar tiles into the programmable memristor head, with live LPC
output meters. All audio is inlined as base64 so the page is portable (drop
it on a website, open it offline).

The baked weights are drawn once and are identical for every time — only the
input one-hot track and the resulting activations change per utterance, which
is the whole point: one fixed chip speaks the entire clock.
"""
import base64
import json
import os

data = json.load(open("demo_v13_data.json"))

# phone-symbol order (row labels for the L1 one-hot input blocks); the JSON
# predates this field, so pull it from the corpus cache when absent.
if "phone_syms" not in data:
    try:
        import numpy as np
        data["phone_syms"] = [
            str(s) for s in np.load("corpus_v13.npz", allow_pickle=True)["inv_phones"]
        ]
    except Exception as e:
        print(f"warning: no phone_syms ({e}) — input rows will be unlabeled")
        data["phone_syms"] = []

# inline every showcase utterance's three voices as base64 wavs
wavs = {}
voices = ["chipA", "float", "ceiling", "original"]
voices += [f"drift{w}" for w in data.get("drift_weeks", [])]
for u in data["utterances"]:
    for voice in voices:
        p = f"demo_audio/{u['tag']}_{voice}.wav"
        if os.path.exists(p):
            wavs[f"{u['tag']}_{voice}"] = base64.b64encode(open(p, "rb").read()).decode()

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PB-2 talking clock — analog baked-core TTS chip</title>
<style>
:root{
 --bg:#140d07; --panel:#1e1209; --line:#3a2712; --copper:#e09b4c;
 --oxide:#43b0a6; --mem:#a184e0; --pulse:#ffe9a8; --ink:#e8dcc8;
 --dim:#8f7f66; --good:#9ec97f;
}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);
 font:13px/1.5 ui-monospace,'Cascadia Mono','JetBrains Mono',Menlo,monospace;
 padding:18px 20px 34px;max-width:1180px;margin:0 auto}
h1{font-size:15px;letter-spacing:.2em;font-weight:600;text-transform:uppercase}
h1 b{color:var(--copper)}
.sub{color:var(--dim);font-size:11.5px;margin:3px 0 16px;letter-spacing:.03em;max-width:820px}
button{background:var(--panel);color:var(--ink);border:1px solid var(--line);
 padding:6px 12px;font:inherit;letter-spacing:.06em;cursor:pointer;border-radius:2px}
button:hover{border-color:var(--copper)}
button[aria-pressed=true]{border-color:var(--copper);color:var(--copper)}
button:focus-visible{outline:2px solid var(--pulse);outline-offset:2px}
main{display:grid;grid-template-columns:280px minmax(0,1fr) 232px;gap:18px;align-items:start}
section.left{display:flex;flex-direction:column;gap:14px}
.clock{width:100%;aspect-ratio:1;background:var(--panel);border:1px solid var(--line);
 border-radius:6px}
.times{display:flex;flex-wrap:wrap;gap:5px}
.times button{padding:5px 8px;font-size:11px}
.readout{font-size:15px;letter-spacing:.1em;min-height:22px}
.readout .ph{color:var(--pulse)}
.voices{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.voices span{color:var(--dim);font-size:11px}
canvas{width:100%;height:auto;display:block;background:var(--panel);
 border:1px solid var(--line);border-radius:4px}
#scrub{width:100%;accent-color:var(--copper);margin-top:10px}
.drift #drift{width:100%;accent-color:var(--mem)}
.drift .driftlab{font-size:10.5px;color:var(--dim);line-height:1.5;margin-top:5px}
.drift .driftlab b{color:var(--mem);font-weight:600}
#phones{position:relative;height:20px;margin-top:2px;font-size:10px;color:var(--dim)}
#phones span{position:absolute;top:0;border-left:1px solid var(--line);padding-left:3px}
#phones span.on{color:var(--pulse);border-left-color:var(--pulse)}
aside{border:1px solid var(--line);background:var(--panel);border-radius:4px;padding:12px 13px}
aside h2{font-size:10.5px;letter-spacing:.18em;color:var(--dim);text-transform:uppercase;margin-bottom:9px}
.meter{margin-bottom:7px}
.meter .lab{display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim)}
.meter .lab b{color:var(--ink);font-weight:500}
.meter .tr{height:6px;background:#120b05;border:1px solid var(--line);border-radius:2px;overflow:hidden;margin-top:2px}
.meter .fl{height:100%;background:var(--copper);width:0%}
.meter.mF0 .fl{background:var(--good)}.meter.mvoice .fl{background:var(--oxide)}
.legend{margin-top:12px;font-size:10.5px;color:var(--dim);line-height:1.7}
.sw{display:inline-block;width:9px;height:9px;border-radius:1px;vertical-align:-1px;margin-right:5px}
.play{min-width:104px}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
footer{margin-top:16px;color:var(--dim);font-size:11px;line-height:1.7}
footer b{color:var(--ink);font-weight:500}
@media (max-width:960px){main{grid-template-columns:1fr}.clock{max-width:280px}}
@media (prefers-reduced-motion:reduce){.flow{display:none}}
</style></head><body>
<h1><b>PB-2</b> · analog baked-core talking clock</h1>
<p class="sub">One printed analog chip speaks any time of day. Layers L1/L2 are
<b>baked</b> (fixed printed-resistor crossbars, shared by every utterance);
only the small L3 <b>memristor head</b> is programmable and is calibrated
per-chip. Pick a time — the chip says it while you watch <b>current heat the
devices it flows through</b> and charge collect on the bitline capacitors.
LPC-10 vocoder output (TMS5100 / Speak&amp;Spell lineage), time-domain, no ADC
in the signal path.</p>
<div class="bar">
 <button class="play" id="play">▶ speak</button>
 <span style="color:var(--dim)">voice:</span>
 <button class="src" data-k="chipA" aria-pressed="true">baked chip</button>
 <button class="src" data-k="float" aria-pressed="false">software ideal</button>
 <button class="src" data-k="ceiling" aria-pressed="false">LPC ceiling</button>
 <button class="src" data-k="original" aria-pressed="false">MBROLA teacher</button>
 <span class="readout">“<span id="txt"></span>” · <span class="ph" id="curph"></span></span>
</div>
<main>
 <section class="left">
  <svg class="clock" id="clock" viewBox="0 0 200 200" role="img" aria-label="clock face"></svg>
  <div>
   <h2 style="font-size:10.5px;letter-spacing:.18em;color:var(--dim);text-transform:uppercase;margin-bottom:7px">pick a time</h2>
   <div class="times" id="times"></div>
  </div>
  <div class="drift">
   <h2 style="font-size:10.5px;letter-spacing:.18em;color:var(--dim);text-transform:uppercase;margin-bottom:7px">memristor aging</h2>
   <input id="drift" type="range" min="0" max="12" step="1" value="0"
    aria-label="weeks of memristor drift">
   <div class="driftlab"><b id="driftLab">fresh</b> — drift hits the
    <span style="color:var(--mem)">memristor head</span> only; the baked core
    is immune. Re-calibrating the head resets it.</div>
  </div>
 </section>
 <div>
  <canvas id="die" width="1000" height="600" role="img"
   aria-label="Three crossbar tiles with live charge flow"></canvas>
  <input id="scrub" type="range" min="0" max="0" value="0" aria-label="frame scrubber">
  <div id="phones"></div>
 </div>
 <aside>
  <h2>LPC output · 10 ms frame</h2>
  <div id="meters"></div>
  <div class="legend">
   <div><span class="sw" style="background:var(--copper)"></span>baked layer (printed R)</div>
   <div><span class="sw" style="background:var(--mem)"></span>memristor head</div>
   <div><span class="sw" style="background:var(--pulse)"></span>current flowing now</div>
   <div style="margin-top:8px">cell brightness = <b>current through that
   device this instant</b> (active input row × its conductance) — dark = no
   charge there.<br><br>bottom bars = <b>bitline capacitors</b> filling with
   the integrated charge ∫i·dt = that neuron's value; one tile's caps drive
   the next tile's rows.</div>
  </div>
 </aside>
</main>
<footer>
<b>What you're seeing.</b> The same fixed baked core (L1 92×64, L2 64×32 printed
resistor crossbars, drawn once) drives every time on the clock; only the
32×<span id="nout"></span> memristor head is programmable (≈5% of weights) and
is write-verify calibrated to this individual chip. Trained on the full
720-minute corpus. Voices, worst→best reference: <b>baked chip</b> = the
trained chip in imperfect analog hardware (what you'd build); <b>software
ideal</b> = same trained network with no analog noise (the gap to it is the
analog-hardware penalty); <b>LPC ceiling</b> = the vocoder on perfect
coefficients (no chip at all — the codec's own limit); <b>MBROLA teacher</b>
= the speech the chip learned from. The die animation always shows the
physical baked chip. Fidelity holds across the whole clock — the fixed core
does not saturate as the vocabulary grows. Simulation; see the paper for
methods and literature validation.
</footer>
<script>
const D=__DATA__, WAV=__WAV__;
const cv=document.getElementById('die'),cx=cv.getContext('2d');
const C={copper:'#e09b4c',oxide:'#43b0a6',mem:'#a184e0',pulse:'#ffe9a8',
 line:'#3a2712',dim:'#8f7f66',panel:'#1e1209'};
const motion=!matchMedia('(prefers-reduced-motion: reduce)').matches;
document.getElementById('nout').textContent=D.layers[2].cols;

// ---- tile geometry (weights shared across all utterances) ----
const tiles=[];{let x=58;
 D.layers.forEach((L,k)=>{
  const cap=k===0?6.2:(k===1?9:15), cw=Math.min(cap,470/L.rows), ch=cw;
  const t={W:L.W,rows:L.rows,cols:L.cols,x:x,y:24,cw:cw,ch:ch,baked:L.baked,
   name:L.name.toUpperCase().replace(/X/g,'×')};
  t.h=L.rows*ch; t.w=L.cols*cw; t.max=Math.max(...L.W.flat().map(Math.abs));
  tiles.push(t); x+=t.w+78;});}

// live memristor head: drifts with the week slider (baked tiles never change).
// physical power law G(t)=G0*(t/t0)^-nu applied to each differential cell.
const H=D.head; let driftWeeks=0, curOut=null;
function driftedHeadW(w){const Gp=H.Gp,Gn=H.Gn,s=H.scale;
 if(w<=0) return Gp.map((row,r)=>row.map((g,c)=>(g-Gn[r][c])*s));
 const ratio=Math.max(w,H.t0_weeks)/H.t0_weeks;
 return Gp.map((row,r)=>row.map((g,c)=>
   (g*Math.pow(ratio,-H.nup[r][c])-Gn[r][c]*Math.pow(ratio,-H.nun[r][c]))*s));}
function setHead(w){driftWeeks=w;const W3=driftedHeadW(w);
 tiles[2].W=W3;tiles[2].max=Math.max(1e-9,...W3.flat().map(Math.abs));}
setHead(0);
// head output for a frame = clip(relu(a2·W3 + b3)); baked a2 is drift-independent
function computeOut(a2f){const W3=tiles[2].W,b=H.b3,nc=W3[0].length,o=new Array(nc).fill(0);
 for(let r=0;r<a2f.length;r++){const a=a2f[r];if(a<=0)continue;const row=W3[r];
  for(let c=0;c<nc;c++)o[c]+=a*row[c];}
 for(let c=0;c<nc;c++)o[c]=Math.min(H.out_clip,Math.max(0,o[c]+b[c]));return o;}
function hexA(h,a){const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),
 b=parseInt(h.slice(5,7),16);return`rgba(${r},${g},${b},${a})`;}
function rgb(h){return[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function mixA(h1,h2,t,a){const x=rgb(h1),y=rgb(h2);
 return`rgba(${Math.round(x[0]+(y[0]-x[0])*t)},${Math.round(x[1]+(y[1]-x[1])*t)},${Math.round(x[2]+(y[2]-x[2])*t)},${a})`;}
// current density 0..1 through one device THIS frame -> colour. At rest the
// cell is a barely-visible tile tint (dark); as charge flows it heats toward
// cream. This is the "where is the charge right now" map.
function heat(base,cu){if(cu<0.02)return hexA(base,0.05);
 const t=Math.min(1,cu);return mixA(base,C.pulse,Math.pow(t,0.55),0.16+0.84*Math.pow(t,0.7));}

let U=null, N=0, dash=0, cur=-1;
// L1 input rows are one-hot phone letters: [0,n) prev phone, [n,2n) current,
// [2n,3n) next, [3n,3n+5) position-in-phone lines.
function rowLab(r){const S=D.phone_syms,n=S.length;
 return r<3*n?S[r%n]:('p'+(r-3*n+1));}
function drawInputLabels(t,inMap){const S=D.phone_syms;if(!S||!S.length)return;
 const n=S.length;
 cx.textAlign='right';
 for(let r=0;r<t.rows;r++){const yy=t.y+r*t.ch+t.ch*0.85;
  if(inMap[r]){cx.fillStyle=C.pulse;cx.font='bold 8px ui-monospace,monospace';}
  else{cx.fillStyle=hexA(C.dim,0.55);cx.font='4.5px ui-monospace,monospace';}
  cx.fillText(rowLab(r),t.x-5,yy);}
 cx.textAlign='left';
 const blocks=[[0,n,'prev'],[n,2*n,'now'],[2*n,3*n,'next'],[3*n,t.rows,'pos']];
 blocks.forEach(([r0,r1,name])=>{
  if(r0>0){const y=t.y+r0*t.ch;
   cx.strokeStyle=hexA(C.dim,0.6);cx.beginPath();cx.moveTo(t.x-54,y);cx.lineTo(t.x-2,y);cx.stroke();
   cx.strokeStyle=hexA(C.dim,0.15);cx.beginPath();cx.moveTo(t.x,y);cx.lineTo(t.x+t.w,y);cx.stroke();}
  cx.save();cx.translate(t.x-46,t.y+(r0+r1)/2*t.ch);cx.rotate(-Math.PI/2);
  cx.textAlign='center';cx.fillStyle=C.dim;cx.font='9px ui-monospace,monospace';
  cx.fillText(name,0,0);cx.restore();});}
function draw(f){
 cx.fillStyle=C.panel;cx.fillRect(0,0,cv.width,cv.height);
 if(!U)return;
 const fr=U.frames, inMap={};fr.input[f].forEach(i=>inMap[i]=1);
 const drive=[inMap,fr.a1[f],fr.a2[f]];          // what drives each tile's rows
 const dCeil=[1,D.ceilings[0],D.ceilings[1]];
 const col=[fr.a1[f],fr.a2[f],curOut];            // charge collected on each bitline (head = live/aged)
 tiles.forEach((t,k)=>{
  cx.strokeStyle=C.line;cx.strokeRect(t.x-1,t.y-1,t.w+2,t.h+2);
  cx.fillStyle=C.dim;cx.font='10px ui-monospace,monospace';cx.fillText(t.name,t.x,t.y-8);
  const base=t.baked?C.copper:C.mem;
  // per-device current = (active input on its row) x (its conductance)
  for(let r=0;r<t.rows;r++){
   const dr=k===0?(drive[0][r]||0):Math.min(1,drive[k][r]/dCeil[k]);
   const y=t.y+r*t.ch;
   for(let c=0;c<t.cols;c++){
    cx.fillStyle=heat(base,dr*Math.abs(t.W[r][c])/t.max);
    cx.fillRect(t.x+c*t.cw,y,t.cw-0.7,t.ch-0.7);}}
  if(k===0)drawInputLabels(t,inMap);
  // bitline capacitors filling with integrated charge (= the neuron value)
  const oc=D.ceilings[k],bh=42;
  for(let c=0;c<t.cols;c++){
   const q=Math.min(1,Math.max(0,col[k][c]/oc)),bx=t.x+c*t.cw,by=t.y+t.h+8;
   cx.fillStyle='#0d0805';cx.fillRect(bx,by,t.cw-0.7,bh);
   cx.fillStyle=mixA(base,C.pulse,q*0.55,0.32+0.68*q);cx.fillRect(bx,by+bh-bh*q,t.cw-0.7,bh*q);
   cx.strokeStyle=hexA(base,0.3);cx.strokeRect(bx+0.3,by+0.3,t.cw-1.3,bh-0.6);}
  cx.fillStyle=C.dim;cx.font='9px ui-monospace,monospace';cx.fillText('∫ i dt · bitline caps',t.x,t.y+t.h+66);
  // charge leaving charged columns feeds the next tile's rows
  if(k<2){const nt=tiles[k+1];
   for(let c=0;c<t.cols;c++){const q=Math.min(1,col[k][c]/oc);if(q<0.05)continue;
    const r=c%nt.rows;cx.strokeStyle=hexA(C.pulse,0.05+0.4*q);cx.lineWidth=0.8+1.5*q;
    cx.setLineDash(motion?[5,6]:[]);cx.lineDashOffset=-dash;
    cx.beginPath();cx.moveTo(t.x+c*t.cw+t.cw/2,t.y+t.h+8+bh);
    cx.bezierCurveTo(t.x+t.w+54,t.y+t.h+8+bh,nt.x-54,nt.y+r*nt.ch+nt.ch/2,nt.x-40,nt.y+r*nt.ch+nt.ch/2);
    cx.stroke();cx.setLineDash([]);}}});
 const t3=tiles[2];cx.strokeStyle=hexA(C.mem,0.8);cx.lineWidth=2;
 cx.strokeRect(t3.x-1,t3.y-1,t3.w+2,t3.h+2);
 cx.fillStyle=C.mem;cx.font='9px ui-monospace,monospace';
 cx.fillText('write-verify bus',t3.x,t3.y+t3.h+80);
}
// ---- meters ----
const mDiv=document.getElementById('meters');
D.param_names.forEach((n,i)=>mDiv.insertAdjacentHTML('beforeend',
 `<div class="meter m${n}"><div class="lab"><span>${n}</span><b id="mv${i}">–</b></div>
  <div class="tr"><div class="fl" id="mf${i}"></div></div></div>`));
function meters(f){const o=curOut;o.forEach((v,i)=>{
 document.getElementById('mf'+i).style.width=Math.min(100,100*v/1.05)+'%';
 const phys=v*D.scale[i];
 document.getElementById('mv'+i).textContent=D.param_names[i]==='F0'?phys.toFixed(0)+' Hz':phys.toFixed(2);});}
// ---- clock face ----
const clk=document.getElementById('clock');
function buildClock(){let s='<circle cx="100" cy="100" r="92" fill="none" stroke="'+C.line+'" stroke-width="2"/>';
 for(let i=0;i<12;i++){const a=i*30*Math.PI/180,x1=100+80*Math.sin(a),y1=100-80*Math.cos(a),
  x2=100+88*Math.sin(a),y2=100-88*Math.cos(a);
  s+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${C.dim}" stroke-width="${i%3?1:2}"/>`;}
 s+='<line id="hh" x1="100" y1="100" x2="100" y2="46" stroke="'+C.copper+'" stroke-width="4" stroke-linecap="round"/>';
 s+='<line id="mh" x1="100" y1="100" x2="100" y2="26" stroke="'+C.pulse+'" stroke-width="2.5" stroke-linecap="round"/>';
 s+='<circle cx="100" cy="100" r="3.5" fill="'+C.copper+'"/>';clk.innerHTML=s;}
function setHands(h,m){const ha=((h%12)+m/60)*30,ma=m*6;
 document.getElementById('hh').setAttribute('transform',`rotate(${ha} 100 100)`);
 document.getElementById('mh').setAttribute('transform',`rotate(${ma} 100 100)`);}
// ---- audio ----
let key='chipA', selTag=null;
const audio=new Audio();
function nearestDrift(w){const pts=D.drift_weeks||[];if(w<2||!pts.length)return 0;
 let b=pts[0];pts.forEach(p=>{if(Math.abs(p-w)<Math.abs(b-w))b=p;});return b;}
function audioName(){let vk=key;                 // baked-chip voice ages with the slider
 if(key==='chipA'){const w=nearestDrift(driftWeeks);if(w>0)vk='drift'+w;}
 const k=selTag+'_'+vk;return WAV[k]?('data:audio/wav;base64,'+WAV[k]):'';}
function setSrc(){const t=audio.currentTime,was=!audio.paused;audio.src=audioName();
 if(was){audio.currentTime=t;audio.play();}}
document.querySelectorAll('.src').forEach(b=>b.onclick=()=>{key=b.dataset.k;
 document.querySelectorAll('.src').forEach(x=>x.setAttribute('aria-pressed',x.dataset.k===key));setSrc();});
// ---- phone ruler ----
const phDiv=document.getElementById('phones');
function buildRuler(){phDiv.innerHTML='';let last='';
 U.phones.forEach((p,f)=>{if(p!==last){const s=document.createElement('span');
  s.textContent=p;s.style.left=(100*f/N)+'%';s.dataset.f=f;phDiv.appendChild(s);last=p;}});}
// ---- selection ----
function select(u){U=u;N=u.frames.out.length;selTag=u.tag;cur=-1;
 document.getElementById('txt').textContent=u.text;
 setHands(u.h,u.m);buildRuler();
 document.getElementById('scrub').max=N-1;document.getElementById('scrub').value=0;
 audio.src=audioName();render(0);
 document.querySelectorAll('.tbtn').forEach(b=>b.setAttribute('aria-pressed',+b.dataset.i===u._i));}
// time buttons
const tDiv=document.getElementById('times');
D.utterances.forEach((u,i)=>{u._i=i;const b=document.createElement('button');
 b.className='tbtn';b.dataset.i=i;b.setAttribute('aria-pressed','false');
 b.textContent=`${u.h}:${String(u.m).padStart(2,'0')}`;b.title=u.text;
 b.onclick=()=>select(u);tDiv.appendChild(b);});
// ---- play/scrub/loop ----
const playBtn=document.getElementById('play'),scrub=document.getElementById('scrub');
playBtn.onclick=()=>{audio.paused?audio.play():audio.pause();};
audio.onplay=()=>playBtn.textContent='❚❚ pause';
audio.onpause=()=>playBtn.textContent='▶ speak';
audio.onended=()=>playBtn.textContent='▶ speak';
scrub.oninput=()=>{audio.currentTime=scrub.value*D.frame_ms/1000;render(+scrub.value);};
const driftEl=document.getElementById('drift'),driftLab=document.getElementById('driftLab');
driftEl.oninput=()=>{setHead(+driftEl.value);
 driftLab.textContent=driftWeeks===0?'fresh':('aged '+driftWeeks+' week'+(driftWeeks>1?'s':''));
 if(key==='chipA')setSrc();          // hear the aged chip
 const f=Math.max(0,cur);cur=-1;render(f);};   // force redraw of current frame
function render(f){f=Math.max(0,Math.min(N-1,f));if(f===cur&&!motion)return;cur=f;
 curOut=computeOut(U.frames.a2[f]);
 draw(f);meters(f);document.getElementById('curph').textContent=U.phones[f]||'';
 [...phDiv.children].forEach(s=>s.classList.toggle('on',U.phones[+s.dataset.f]===U.phones[f]&&+s.dataset.f<=f));
 scrub.value=f;}
function loop(){if(U&&!audio.paused)render(Math.floor(audio.currentTime*1000/D.frame_ms));
 if(motion){dash+=0.9;if(U&&!audio.paused)draw(cur<0?0:cur);}requestAnimationFrame(loop);}
buildClock();select(D.utterances[0]);requestAnimationFrame(loop);
</script></body></html>"""

out = HTML.replace("__DATA__", json.dumps(data)).replace("__WAV__", json.dumps(wavs))
open("clock_viewer.html", "w").write(out)
print(f"clock_viewer.html  {len(out)//1024} kB  ({len(wavs)} audio clips)")

# also emit a fragment (no <!doctype>/<html>/<head>/<body>) for publishing as
# a claude.ai Artifact, which supplies its own document skeleton.
i, j = out.index("<style>"), out.index("</body></html>")
frag = out[i:j].replace("</head><body>", "\n")
open("clock_viewer_fragment.html", "w").write(frag)
print(f"clock_viewer_fragment.html  {len(frag)//1024} kB  (Artifact-ready)")

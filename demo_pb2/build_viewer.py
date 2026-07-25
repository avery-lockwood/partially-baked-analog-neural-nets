"""build_viewer.py — emits chip_viewer.html: die layout + charge flow + audio."""
import json, base64

viz = json.load(open("viz_data.json"))
wavs = {k: base64.b64encode(open(f"{f}.wav", "rb").read()).decode()
        for k, f in [("orig", "v7_mbrola_original"), ("ceil", "v7_vocoder_ceiling"),
                     ("chipA", "v7_chip_A"), ("chipB", "v7_chip_B"),
                     ("drift", "v7_chip_A_drifted")]}

html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PB-1 talking-clock die — charge-flow viewer</title>
<style>
:root{
  --substrate:#150d07; --panel:#1f130a; --line:#3a2712;
  --copper:#e09b4c; --oxide:#43b0a6; --mem:#a184e0; --pulse:#ffe9a8;
  --ink:#e8dcc8; --dim:#8f7f66; --good:#9ec97f;
}
*{box-sizing:border-box;margin:0}
body{background:var(--substrate);color:var(--ink);
  font:13px/1.5 ui-monospace,'Cascadia Mono','JetBrains Mono',Menlo,monospace;
  padding:18px 22px 30px}
h1{font-size:15px;letter-spacing:.22em;font-weight:600;text-transform:uppercase}
h1 b{color:var(--copper)}
.sub{color:var(--dim);font-size:11.5px;margin:2px 0 14px;letter-spacing:.04em}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
button{background:var(--panel);color:var(--ink);border:1px solid var(--line);
  padding:7px 14px;font:inherit;letter-spacing:.08em;cursor:pointer;border-radius:2px}
button:hover{border-color:var(--copper)}
button[aria-pressed=true]{border-color:var(--copper);color:var(--copper)}
button:focus-visible{outline:2px solid var(--pulse);outline-offset:2px}
#play{min-width:96px}
.phrase{margin-left:auto;font-size:15px;letter-spacing:.14em}
.phrase .ph{color:var(--pulse)}
main{display:grid;grid-template-columns:minmax(0,1fr) 250px;gap:18px}
canvas{width:100%;height:auto;display:block;background:var(--panel);
  border:1px solid var(--line);border-radius:3px}
aside{border:1px solid var(--line);background:var(--panel);border-radius:3px;
  padding:12px 14px}
.meter .tr{height:5px}
aside h2{font-size:11px;letter-spacing:.2em;color:var(--dim);
  text-transform:uppercase;margin-bottom:10px}
.meter{margin-bottom:9px}
.meter .lab{display:flex;justify-content:space-between;font-size:11px;color:var(--dim)}
.meter .lab b{color:var(--ink);font-weight:500}
.meter .tr{height:7px;background:#120b05;border:1px solid var(--line);
  border-radius:2px;overflow:hidden;margin-top:2px}
.meter .fl{height:100%;background:var(--copper);width:0%}
.meter.mF0 .fl{background:var(--good)}
.meter.mfric .fl{background:var(--oxide)}
.legend{margin-top:14px;font-size:11px;color:var(--dim);line-height:1.7}
.sw{display:inline-block;width:9px;height:9px;border-radius:1px;
  vertical-align:-1px;margin-right:5px}
#scrub{width:100%;accent-color:var(--copper);margin-top:12px}
#phones{position:relative;height:22px;margin-top:2px;font-size:10px;color:var(--dim)}
#phones span{position:absolute;top:0;border-left:1px solid var(--line);padding-left:3px}
#phones span.on{color:var(--pulse);border-left-color:var(--pulse)}
footer{margin-top:14px;color:var(--dim);font-size:11px;max-width:760px;line-height:1.7}
@media (max-width:820px){main{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.flow{display:none}}
</style></head><body>
<h1><b>PB-1</b> · partial-baked talking-clock die · charge-flow viewer</h1>
<p class="sub">71 one-hot input lines → L1+L2 baked printed resistors (differential pairs) → L3 programmable memristor head → 6 analog pulse-width outputs → formant synth. Time-domain chained, R=32.</p>
<div class="bar">
  <button id="play">▶ run chip</button>
  <span style="color:var(--dim)">voice:</span>
  <button class="src" data-k="chipA" aria-pressed="true">chip A</button>
  <button class="src" data-k="chipB" aria-pressed="false">chip B</button>
  <button class="src" data-k="drift" aria-pressed="false">chip A · drifted</button>
  <button class="src" data-k="ceil" aria-pressed="false">LPC ceiling</button>
  <button class="src" data-k="orig" aria-pressed="false">MBROLA original</button>
  <span class="phrase">"it is three thirty" · <span class="ph" id="curph">PAU</span></span>
</div>
<main>
  <div>
    <canvas id="die" width="1040" height="620" role="img"
      aria-label="Physical layout of three crossbar tiles with live charge flow"></canvas>
    <input id="scrub" type="range" min="0" max="0" value="0"
      aria-label="frame scrubber">
    <div id="phones"></div>
  </div>
  <aside>
    <h2>output lines (10 ms frame)</h2>
    <div id="meters"></div>
    <div class="legend">
      <div><span class="sw" style="background:var(--copper)"></span>baked G+ (copper print)</div>
      <div><span class="sw" style="background:var(--oxide)"></span>baked G− (return pair)</div>
      <div><span class="sw" style="background:var(--mem)"></span>programmable memristor</div>
      <div><span class="sw" style="background:var(--pulse)"></span>active charge path</div>
      <div style="margin-top:8px">cell brightness ∝ conductance.<br>
      row glow ∝ input pulse width;<br>column bar ∝ integrated charge.</div>
    </div>
  </aside>
</main>
<footer>
Each tile is drawn at physical aspect: rows are wordlines entering from the left,
columns are bitlines integrating downward into the charge rail. The L3 tile is the
only one with programming lines (drawn as the violet write bus). Voices: two fab
draws of the same mask (A/B — the fab lottery), a drifted memristor head, and the
float teacher. Animation shows chip A's measured activations for all voices.
</footer>
<script>
const V=__VIZ__;
const WAV={orig:"__W_O__",ceil:"__W_C__",chipA:"__W_A__",chipB:"__W_B__",drift:"__W_D__"};
const N=V.frames.input.length, FMS=V.frame_ms;
const cv=document.getElementById('die'),cx=cv.getContext('2d');
const css=getComputedStyle(document.documentElement);
const C={sub:css.getPropertyValue('--substrate').trim(),
  copper:'#e09b4c',oxide:'#43b0a6',mem:'#a184e0',pulse:'#ffe9a8',
  line:'#3a2712',dim:'#8f7f66',ink:'#e8dcc8',panel:'#1f130a'};
// ---- layout ----
const tiles=[];{let x=66;
 V.layers.forEach((L,k)=>{
   const cap=k===0?6.5:(k===1?9:15);
   const cw=Math.min(cap,520/L.rows), ch=cw;
   tiles.push({W:L.W,rows:L.rows,cols:L.cols,x:x,y:26,cw:cw,ch:ch,
     baked:L.baked,name:L.name.toUpperCase().replace('X','×')});
   x+=L.cols*cw+80;});}
tiles.forEach(t=>{t.h=t.rows*t.ch;t.w=t.cols*t.cw;
  t.max=Math.max(...t.W.flat().map(Math.abs));});
function cellColor(w,max,baked){
  const a=Math.min(1,Math.abs(w)/max);
  const base=baked?(w>=0?C.copper:C.oxide):C.mem;
  return hexA(base,0.14+0.86*a*a);
}
function hexA(h,a){const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),
  b=parseInt(h.slice(5,7),16);return `rgba(${r},${g},${b},${a})`;}
let dash=0;
function draw(f){
  cx.fillStyle=C.panel;cx.fillRect(0,0,cv.width,cv.height);
  const acts=[null,V.frames.a1[f],V.frames.a2[f],V.frames.out[f]];
  const rowIn=[V.frames.input[f].reduce((m,i)=>(m[i]=1,m),{}),
               V.frames.a1[f],V.frames.a2[f]];
  tiles.forEach((t,k)=>{
    // frame + name
    cx.strokeStyle=C.line;cx.strokeRect(t.x-1,t.y-1,t.w+2,t.h+2);
    cx.fillStyle=C.dim;cx.font='10px ui-monospace,monospace';
    cx.fillText(t.name,t.x,t.y-8);
    // cells
    for(let r=0;r<t.rows;r++)for(let c=0;c<t.cols;c++){
      cx.fillStyle=cellColor(t.W[r][c],t.max,t.baked);
      cx.fillRect(t.x+c*t.cw,t.y+r*t.ch,t.cw-1,t.ch-1);}
    // wordline glow ∝ input pulse width
    const ceil=k===0?1:V.ceilings[k-1];
    for(let r=0;r<t.rows;r++){
      const v=k===0?(rowIn[0][r]||0):Math.min(1,rowIn[k][r]/ceil);
      if(v>0.02){
        cx.strokeStyle=hexA(C.pulse,0.15+0.75*v);
        cx.lineWidth=k===0?1.4:1+2.2*v;
        cx.setLineDash(motion?[6,5]:[]);cx.lineDashOffset=-dash;
        cx.beginPath();cx.moveTo(t.x-40,t.y+r*t.ch+t.ch/2);
        cx.lineTo(t.x+t.w,t.y+r*t.ch+t.ch/2);cx.stroke();
        cx.setLineDash([]);}}
    // bitline charge bars
    const out=acts[k+1],oc=V.ceilings[k];
    cx.fillStyle=C.dim;
    for(let c=0;c<t.cols;c++){
      const q=Math.min(1,Math.max(0,out[c]/oc));
      const bx=t.x+c*t.cw,by=t.y+t.h+6;
      cx.fillStyle='#120b05';cx.fillRect(bx,by,t.cw-1,40);
      cx.fillStyle=hexA(k===2?C.mem:C.copper,0.35+0.65*q);
      cx.fillRect(bx,by+40-40*q,t.cw-1,40*q);}
    cx.fillStyle=C.dim;cx.font='9px ui-monospace,monospace';
    cx.fillText('∫ i dt',t.x,t.y+t.h+60);
    // inter-tile bundle
    if(k<2){const nt=tiles[k+1];
      for(let c=0;c<t.cols;c++){
        const v=Math.min(1,acts[k+1][c]/oc);if(v<0.03)continue;
        const r=c%nt.rows;
        cx.strokeStyle=hexA(C.pulse,0.06+0.5*v);cx.lineWidth=1;
        cx.beginPath();
        cx.moveTo(t.x+c*t.cw+t.cw/2,t.y+t.h+46);
        cx.bezierCurveTo(t.x+t.w+58,t.y+t.h+46,
          nt.x-60,nt.y+r*nt.ch+nt.ch/2,nt.x-46,nt.y+r*nt.ch+nt.ch/2);
        cx.stroke();}}
  });
  // L3 write bus
  const t3=tiles[2];
  cx.strokeStyle=hexA(C.mem,0.8);cx.lineWidth=2;
  cx.strokeRect(t3.x-1,t3.y-1,t3.w+2,t3.h+2);
  cx.fillStyle=C.mem;cx.font='9px ui-monospace,monospace';
  cx.fillText('write-verify bus',t3.x,t3.y+t3.h+74);
  cx.strokeStyle=hexA(C.mem,0.5);cx.lineWidth=1;
  cx.beginPath();cx.moveTo(t3.x,t3.y+t3.h+66);cx.lineTo(t3.x+t3.w,t3.y+t3.h+66);cx.stroke();
}
// ---- meters ----
const mDiv=document.getElementById('meters');
const units=['Hz','','Hz','Hz','Hz',''];
V.param_names.forEach((n,i)=>{
  mDiv.insertAdjacentHTML('beforeend',
   `<div class="meter m${n}"><div class="lab"><span>${n}</span><b id="mv${i}">–</b></div>
    <div class="tr"><div class="fl" id="mf${i}"></div></div></div>`);});
function meters(f){
  const o=V.frames.out[f];
  o.forEach((v,i)=>{
    const phys=v*V.scale[i];
    document.getElementById('mf'+i).style.width=Math.min(100,100*v/1.05)+'%';
    document.getElementById('mv'+i).textContent=
      units[i]==='Hz'?phys.toFixed(0)+' Hz':phys.toFixed(2);});}
// ---- phones ruler ----
const ph=document.getElementById('phones');
let last='',spans=[];
V.phones.forEach((p,f)=>{if(p!==last){
  const s=document.createElement('span');s.textContent=p;s.style.left=(100*f/N)+'%';
  s.dataset.f=f;ph.appendChild(s);spans.push(s);last=p;}});
// ---- audio + loop ----
const motion=!matchMedia('(prefers-reduced-motion: reduce)').matches;
let key='chipA';
const audio=new Audio();
function setSrc(k){key=k;audio.src='data:audio/wav;base64,'+WAV[k];
  document.querySelectorAll('.src').forEach(b=>
    b.setAttribute('aria-pressed',b.dataset.k===k));}
setSrc('chipA');
// voices differ slightly in length; map time->frame via chip frame grid
document.querySelectorAll('.src').forEach(b=>b.onclick=()=>{
  const t=audio.currentTime,was=!audio.paused;setSrc(b.dataset.k);
  audio.currentTime=t;if(was)audio.play();});
const playBtn=document.getElementById('play'),scrub=document.getElementById('scrub');
scrub.max=N-1;
playBtn.onclick=()=>{audio.paused?audio.play():audio.pause();};
audio.onplay=()=>playBtn.textContent='❚❚ pause';
audio.onpause=()=>playBtn.textContent='▶ run chip';
audio.onended=()=>{playBtn.textContent='▶ run chip';};
scrub.oninput=()=>{audio.currentTime=scrub.value*FMS/1000;render(+scrub.value);};
let cur=-1;
function render(f){f=Math.max(0,Math.min(N-1,f));
  if(f===cur&&!motion)return;cur=f;
  draw(f);meters(f);
  document.getElementById('curph').textContent=V.phones[f];
  spans.forEach(s=>s.classList.toggle('on',
    V.phones[+s.dataset.f]===V.phones[f]&&+s.dataset.f<=f));
  scrub.value=f;}
function loop(){
  if(!audio.paused){render(Math.floor(audio.currentTime*1000/FMS));}
  if(motion)dash+=0.9;
  if(motion&&!audio.paused)draw(cur<0?0:cur);
  requestAnimationFrame(loop);}
render(0);requestAnimationFrame(loop);
</script></body></html>"""

html = html.replace("__VIZ__", json.dumps(viz))
for k, tok in [("orig", "__W_O__"), ("ceil", "__W_C__"), ("chipA", "__W_A__"),
               ("chipB", "__W_B__"), ("drift", "__W_D__")]:
    html = html.replace(tok, wavs[k])
open("chip_viewer.html", "w").write(html)
print("chip_viewer.html", len(html) // 1024, "kB")

/* Lightweight responsive SVG charts, no CDN or dependencies. */
window.escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
window.fmt=(v,d=0)=>v==null||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
window.hhmm=m=>String(Math.floor(m/60)).padStart(2,'0')+':'+String(Math.round(m%60)).padStart(2,'0');
window.showTip=(html,x,y)=>{let t=document.getElementById('tooltip');t.innerHTML=html;t.style.display='block';let w=t.offsetWidth,h=t.offsetHeight;t.style.left=Math.max(8,Math.min(x+14,innerWidth-w-10))+'px';t.style.top=Math.max(8,Math.min(y+12,innerHeight-h-10))+'px'};
window.hideTip=()=>{document.getElementById('tooltip').style.display='none'};
window.Chart={
 colors:['#58e1b4','#6dbaff','#f7bd66','#bdabff','#ff8990','#5ed5df','#a5d484'],
 line(el,series,opt={}){
  if(typeof el==='string')el=document.getElementById(el);if(!el)return;
  let W=Math.max(340,el.clientWidth||780),H=el.clientHeight||240,P={l:57,r:18,t:22,b:34},all=series.flatMap(s=>s.data).filter(p=>Number.isFinite(p[0])&&Number.isFinite(p[1]));
  if(!all.length){el.innerHTML='<div class="empty">No data for this selection</div>';return}
  let xmin=opt.xmin??(opt.time?0:Math.min(...all.map(p=>p[0]))),xmax=opt.xmax??(opt.time?1440:Math.max(...all.map(p=>p[0]))),ymin=opt.ymin??Math.min(0,...all.map(p=>p[1])),ymax=opt.ymax??Math.max(...all.map(p=>p[1]))*1.09;
  if(xmax===xmin)xmax=xmin+1;if(ymax===ymin)ymax=ymin+1;
  let X=x=>P.l+(x-xmin)/(xmax-xmin)*(W-P.l-P.r),Y=y=>H-P.b-(y-ymin)/(ymax-ymin)*(H-P.t-P.b),s='';
  for(let i=0;i<5;i++){let y=ymin+(ymax-ymin)*i/4;s+=`<line x1="${P.l}" x2="${W-P.r}" y1="${Y(y)}" y2="${Y(y)}" stroke="#25384a" stroke-dasharray="3 5"/><text x="${P.l-12}" y="${Y(y)+4}" fill="#6d8ca4" font-size="10" text-anchor="end">${fmt(y,ymax<15?1:0)}</text>`}
  for(let i=0;i<5;i++){let x=xmin+(xmax-xmin)*i/4;s+=`<text x="${X(x)}" y="${H-10}" fill="#6d8ca4" font-size="10" text-anchor="middle">${opt.time?hhmm(x):fmt(x,Math.abs(xmax)<30?1:0)}</text>`}
  series.forEach((a,i)=>{let color=a.color||this.colors[i%7],pts=a.data.filter(p=>Number.isFinite(p[0])&&Number.isFinite(p[1]));if(!pts.length)return;let path=pts.map((p,j)=>(j?'L':'M')+X(p[0])+','+Y(p[1])).join(' ');
   if(a.fill)s+=`<defs><linearGradient id="g-${el.id}-${i}" x1="0" y1="0" x2="0" y2="1"><stop stop-color="${color}" stop-opacity=".2"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs><path d="${path} L${X(pts.at(-1)[0])},${Y(ymin)} L${X(pts[0][0])},${Y(ymin)} Z" fill="url(#g-${el.id}-${i})"/>`;
   if(opt.scatter||a.scatter){pts.forEach(p=>{s+=`<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="2.7" fill="${color}" opacity=".7"/>`})}else s+=`<path d="${path}" fill="none" stroke="${color}" stroke-width="${a.width||2}" ${a.dash?'stroke-dasharray="5 4"':''} stroke-linecap="round" stroke-linejoin="round"/>`;
  });
  (opt.bands||[]).forEach(b=>{s+=`<line x1="${P.l}" x2="${W-P.r}" y1="${Y(b.y)}" y2="${Y(b.y)}" stroke="${b.color||'#f7bd66'}" stroke-dasharray="6 5"/><text x="${W-P.r}" y="${Y(b.y)-5}" font-size="9" fill="${b.color||'#f7bd66'}" text-anchor="end">${escapeHTML(b.label)}</text>`});
  if(opt.time)s+=`<line class="time-cursor" x1="${X(720)}" x2="${X(720)}" y1="${P.t}" y2="${H-P.b}" stroke="#58e1b4" opacity=".3" stroke-dasharray="2 4"/>`;
  s+=`<line class="crosshair" x1="0" x2="0" y1="${P.t}" y2="${H-P.b}" stroke="#a0bbc9" stroke-dasharray="3 4" visibility="hidden"/><text x="${P.l}" y="10" fill="#7795ae" font-size="9">${escapeHTML(opt.unit||'')}</text>`;
  el.innerHTML=`<svg ${opt.time?`data-timeplot="true" data-plot-left="${P.l}" data-plot-right="${P.r}"`:""} viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="${escapeHTML(opt.label||series.map(s=>s.name).join(', '))}">${s}</svg>`;
  el.onpointermove=e=>{let box=el.getBoundingClientRect(),px=(e.clientX-box.left)/box.width*W,x=xmin+(px-P.l)/(W-P.l-P.r)*(xmax-xmin);x=Math.max(xmin,Math.min(xmax,x));let html=`<strong>${opt.time?hhmm(x):(opt.xlabel||'X')+' '+fmt(x,2)}</strong>`;series.forEach((a,i)=>{let p=a.data.reduce((v,p)=>Math.abs(p[0]-x)<Math.abs(v[0]-x)?p:v,a.data[0]);if(p)html+=`<div><span style="color:${a.color||this.colors[i%7]}">●</span> ${escapeHTML(a.name)}: <b>${fmt(p[1],opt.decimals??1)}</b> ${escapeHTML(opt.unit||'')}</div>`});showTip(html,e.clientX,e.clientY);let line=el.querySelector('.crosshair');line.setAttribute('x1',X(x));line.setAttribute('x2',X(x));line.setAttribute('visibility','visible')};el.onpointerleave=()=>{hideTip();el.querySelector('.crosshair')?.setAttribute('visibility','hidden')};
 },
 bars(el,entries,opt={}){
  if(typeof el==='string')el=document.getElementById(el);if(!el)return;let max=Math.max(...entries.map(x=>x.value),1),sum=entries.reduce((a,b)=>a+b.value,0);
  el.innerHTML=entries.map((x,i)=>`<div class="bar-row" style="margin:12px 0;cursor:${opt.click?'pointer':'default'}" data-index="${i}"><div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:7px"><span style="color:#9fb6ca">${escapeHTML(x.label)}</span><span>${fmt(x.value,opt.decimals??0)} <small>${escapeHTML(opt.unit||'kWh')}</small> ${opt.percent?'<small> · '+fmt(100*x.value/sum,1)+'%</small>':''}</span></div><div class="progress"><i style="width:${100*x.value/max}%;background:${x.color||this.colors[i%7]}"></i></div></div>`).join('');
  if(opt.click)el.querySelectorAll('.bar-row').forEach(row=>row.onclick=()=>opt.click(entries[+row.dataset.index]));
 },
 legend(series){return '<div class="legend">'+series.map((s,i)=>`<span><i style="background:${s.color||this.colors[i%7]}"></i>${escapeHTML(s.name)}</span>`).join('')+'</div>'}
};

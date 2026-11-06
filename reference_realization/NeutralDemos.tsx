import React from 'react';

export type DemoId='document_dive'|'paper_curl'|'line_carry'|'layer_explode'|'title_layout';
export type DemoProps={time:number};
export const demoSpecs=[
 {id:'document_dive',label:'纸面聚焦推进',duration:6.7,frames:402,fps:60,width:1920,height:1080},
 {id:'paper_curl',label:'斜向纸页翻卷',duration:3.6,frames:216,fps:60,width:1920,height:1080},
 {id:'line_carry',label:'线条接力横移',duration:6.4,frames:384,fps:60,width:1920,height:1080},
 {id:'layer_explode',label:'材料分层展开',duration:5.4,frames:324,fps:60,width:1920,height:1080},
 {id:'title_layout',label:'标题压印与构图变化',duration:6.7,frames:402,fps:60,width:1920,height:1080},
] as const;

export const C={paper:'#f5f1e7',white:'#fffdf7',ink:'#283b33',green:'#214b41',orange:'#cf6842',gold:'#e6b85c',sage:'#9aab91',muted:'#7c887b',line:'#d7d7c5'};
export const clamp=(x:number,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const mix=(a:number,b:number,p:number)=>a+(b-a)*p;
export const out=(x:number)=>1-Math.pow(1-clamp(x),3);
export const io=(x:number)=>(x=clamp(x))<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
const ramp=(t:number,a:number,d:number,e=out)=>e((t-a)/d);
const n=(v:number)=>Number(v.toFixed(4));
const serif='"Microsoft YaHei", sans-serif';

function Txt({x,y,children,size=28,color=C.ink,weight=500,anchor='start',opacity=1}:any){
 return <text x={x} y={y} fontFamily={serif} fontSize={size} fontWeight={weight} fill={color} textAnchor={anchor} opacity={opacity}>{children}</text>;
}
function Rule({x,y,w,p=1,color=C.orange,width=5}:any){
 return <path d={`M${x} ${y}Q${x+w*.45} ${y-4} ${x+w} ${y-1}`} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1-clamp(p)}/>;
}
function Check({x,y,p=1,s=1}:any){
 return <g transform={`translate(${x} ${y}) scale(${s})`}><path d="M0 13L11 25L37 0" fill="none" stroke={C.green} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1-clamp(p)}/></g>;
}
function Defs({id}:{id:string}){
 return <defs>
  <filter id={`${id}-soft`} x="-35%" y="-40%" width="180%" height="195%"><feDropShadow dx="-1" dy="8" stdDeviation="7" floodColor="#594d31" floodOpacity=".13"/></filter>
  <filter id={`${id}-foldShadow`} x="-60%" y="-60%" width="220%" height="220%"><feDropShadow dx="4" dy="6" stdDeviation="8" floodColor="#4c463b" floodOpacity=".19"/></filter>
  <linearGradient id={`${id}-paper`} x1="0" y1="0" x2=".7" y2="1"><stop stopColor="#fffffa"/><stop offset="1" stopColor="#eee8d7"/></linearGradient>
  <linearGradient id={`${id}-fold`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#fffdf9"/><stop offset=".58" stopColor="#eee5d2"/><stop offset="1" stopColor="#d9d2be"/></linearGradient>
  <linearGradient id={`${id}-green`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#477868"/><stop offset=".62" stopColor={C.green}/><stop offset="1" stopColor="#153a31"/></linearGradient>
  <radialGradient id={`${id}-warm`}><stop stopColor="#e9d7ad" stopOpacity=".42"/><stop offset="1" stopColor="#e9d7ad" stopOpacity="0"/></radialGradient>
  <pattern id={`${id}-grain`} width="83" height="71" patternUnits="userSpaceOnUse"><circle cx="3" cy="7" r=".55" fill="#756c50" opacity=".11"/><circle cx="51" cy="29" r=".5" fill="#756c50" opacity=".1"/><circle cx="20" cy="53" r=".5" fill="#756c50" opacity=".11"/><path d="M61 61h2M27 26h1" stroke="#fffef8" opacity=".45"/></pattern>
  <pattern id={`${id}-grid`} width="18" height="18" patternUnits="userSpaceOnUse"><path d="M18 0H0V18" fill="none" stroke="#7f8c77" strokeOpacity=".1" strokeWidth=".7"/></pattern>
  <clipPath id={`${id}-stage`}><rect x="30" y="192" width="1220" height="438" rx="4"/></clipPath>
 </defs>;
}
function Sheet({id,title,kicker,children}:any){
 return <svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1280 720" style={{fontFamily:serif}}>
  <Defs id={id}/><rect width="1280" height="720" fill={C.paper}/><ellipse cx="1110" cy="260" rx="700" ry="500" fill={`url(#${id}-warm)`}/><rect width="1280" height="720" fill={`url(#${id}-grain)`}/>
  <Txt x={46} y={57} size={22} color={C.green} weight={750}>纸面动效研究</Txt><Txt x={1235} y={57} size={13} color={C.muted} anchor="end">PAPER MOTION</Txt>
  <path d="M38 92H1242" stroke={C.line}/><Txt x={48} y={131} size={14} color={C.orange} weight={650}>{kicker}</Txt><Txt x={48} y={174} size={36} weight={750}>{title}</Txt>
  <g clipPath={`url(#${id}-stage)`}>{children}</g><Txt x={46} y={687} size={12} color={C.muted}>探索 · 层次 · 表达</Txt>
 </svg>;
}

function Document({id,x=0,y=0,s=1,rot=0,value='',label='信息卡'}:any){
 return <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s}) translate(-105 -130)`} filter={`url(#${id}-soft)`}>
  <path d="M0 0H181L210 30V250L199 258L188 250L177 258L166 250L155 258L144 250L133 258L122 250L111 258L100 250L89 258L78 250L67 258L56 250L45 258L34 250L23 258L12 250L0 258Z" fill={`url(#${id}-paper)`} stroke="#d1d3c2" strokeWidth="1"/>
  <path d="M181 0V30H210" fill="#e4e5d8" stroke="#d1d3c2" strokeWidth="1"/>
  <Txt x={99} y={43} size={21} color={C.orange} weight={750} anchor="middle">{label}</Txt><path d="M21 57H188M21 61H188" stroke="#d2a38d" strokeWidth=".8"/>
  <Txt x={23} y={88} size={11} color={C.muted}>结构与内容</Txt><Txt x={182} y={88} size={11} color={C.muted} anchor="end">状态</Txt>
  <path d="M22 96H188V174H22ZM139 96V174M22 122H188M22 148H188" stroke="#bdc6b6" strokeWidth=".85" fill="none"/>
  <Txt x={32} y={114} size={13} weight={600}>方案要点</Txt><Txt x={32} y={141} size={12}>探索与选择</Txt><Txt x={32} y={168} size={12}>路径与层次</Txt>
  <path d="M24 190H113M24 217H82M24 226H67" stroke="#b8c2af" strokeWidth="3" strokeLinecap="round"/>
  <Txt x={185} y={211} size={value?30:15} color={value?C.green:C.muted} weight={value?750:500} anchor="end">{value||'就绪'}</Txt>
  <circle cx="160" cy="238" r="13" stroke={C.orange} strokeWidth="1" fill="none"/><circle cx="160" cy="238" r="9" stroke={C.orange} strokeWidth=".5" fill="none"/>
 </g>;
}
function Material({id,x,y,s=1,rot=0,label='材料'}:any){
 return <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s}) translate(-65 -78)`} filter={`url(#${id}-soft)`}>
  <path d="M8 13L123 7L130 145L12 153Z" fill="#d8d9c6" stroke="#b7c1ab"/>
  <rect x="0" y="0" width="122" height="146" rx="5" fill={`url(#${id}-paper)`} stroke="#cbd0bd"/>
  <path d="M0 7Q0 0 7 0H115Q122 0 122 7V45H0Z" fill={`url(#${id}-green)`}/><Txt x={61} y={29} size={16} color={C.white} weight={650} anchor="middle">{label}</Txt>
  <path d="M19 66H101M19 83H90M19 101H101M19 118H68" stroke="#bac3af" strokeWidth="3" strokeLinecap="round"/>
  <path d="M91 124V153L102 145L112 153V124" fill={C.orange}/>
 </g>;
}
function LayoutFrame({id,x,y,w,h,p=1,rot=0,zoom=1}:any){
 return <g transform={`translate(${x} ${y}) rotate(${rot} ${w/2} ${h/2})`} opacity={p} filter={`url(#${id}-soft)`}>
  <rect width={w} height={h} rx="10" fill={C.white} stroke="#d4d5c6"/><defs><clipPath id={`${id}-layoutClip`}><rect x="7" y="7" width={w-14} height={h-38} rx="5"/></clipPath></defs>
  <g clipPath={`url(#${id}-layoutClip)`}><rect x="7" y="7" width={w-14} height={h-38} fill="#eae3d6"/><g transform={`translate(${w/2} ${h*.45}) scale(${zoom}) translate(${-w/2} ${-h*.45})`}><rect x="7" y="7" width={w-14} height={h-38} fill={`url(#${id}-grid)`}/><Txt x={w/2} y={h*.44} size={w<220?16:21} color={C.muted} anchor="middle">布局区域</Txt><Txt x={w/2} y={h*.44+30} size={12} color={C.muted} anchor="middle">内容位置示意</Txt></g></g>
  <Txt x={w/2} y={h-12} size={14} color={C.green} weight={650} anchor="middle">可变构图</Txt>
 </g>;
}
function arcPoint(t:number){const q=io(t),u=1-q;return {x:u*u*u*536+3*u*u*q*638+3*u*q*q*655+q*q*q*768,y:u*u*u*405+3*u*u*q*274+3*u*q*q*270+q*q*q*353};}

export function DocumentDive({time}:DemoProps){
 const t=clamp(time,0,6.7),id='dive',dive=ramp(t,1.9,1.55,io),tilt=mix(.64,1,dive),zoom=mix(.88,1.47,dive),roll=mix(-7,0,dive),pick=16*ramp(t,1.45,.5),exit=ramp(t,.2,1.05,io),arc=arcPoint((t-.6)/1.25);
 return <Sheet id={id} kicker="01 / 探索与选择" title="从整体，到关键">
  <LayoutFrame id={id} x={mix(48,18,exit)} y={mix(303,360,exit)} w={mix(192,150,exit)} h={mix(266,212,exit)} p={1-exit} rot={mix(-1,-5,exit)} zoom={1.03}/>
  <g transform={`translate(${mix(790,638,exit)} 405) rotate(${roll}) scale(${zoom} ${zoom*tilt}) translate(${-mix(700,865,dive)} ${-mix(395,377,dive)})`}>
   <rect x="365" y="232" width="825" height="335" rx="16" fill="#e4dac4" stroke="#ccc4af"/>
   <Material id={id} x={453} y={395} s={.7} rot={-7} label="材料一"/><Material id={id} x={545} y={393} s={.7} rot={2} label="材料二"/>
   <Document id={id} x={866} y={386-pick} s={1.13} rot={mix(8,0,dive)} value={t>=4.15?'128':''}/>
   <g opacity={1-dive}><Material id={id} x={1110} y={365} s={.85} rot={-10} label="方案要点"/></g>
   {t>=.6&&t<1.95&&<><ellipse cx={mix(536,768,io((t-.6)/1.25))} cy="490" rx={39-13*Math.sin(Math.PI*clamp((t-.6)/1.25))} ry="6" fill="#334b30" opacity=".1"/><Material id={id} x={arc.x} y={arc.y} s={.67} rot={mix(-10,7,io((t-.6)/1.25))} label="信息"/></>}
  </g>
  <g opacity={ramp(t,4.15,.25)} transform={`translate(0 ${12*(1-ramp(t,4.15,.3))})`}><Txt x={1090} y={378} size={83} color={C.orange} weight={750} anchor="middle">128</Txt><Txt x={1090} y={424} size={21} color={C.muted} anchor="middle">信息已就位</Txt><Check x={1074} y={462} p={ramp(t,4.5,.5)} s={.95}/></g>
 </Sheet>;
}

type Point={x:number;y:number};
function clipPolygon(poly:Point[],normal:Point,c:number,positive=true){
 const result:Point[]=[];
 for(let i=0;i<poly.length;i++){
  const a=poly[i],b=poly[(i+1)%poly.length],da=normal.x*a.x+normal.y*a.y-c,db=normal.x*b.x+normal.y*b.y-c,ia=positive?da>=0:da<=0,ib=positive?db>=0:db<=0;
  if(ia)result.push(a);if(ia!==ib){const q=da/(da-db);result.push({x:mix(a.x,b.x,q),y:mix(a.y,b.y,q)});}
 }return result;
}
const points=(p:Point[])=>p.map(q=>`${n(q.x)},${n(q.y)}`).join(' ');
function CurlPage({id,x,y,w,h,phase,t}:any){
 return <g transform={`translate(${x} ${y})`}>
  <rect width={w} height={h} rx="5" fill={phase?C.white:'#e9e2d0'} stroke="#d4d3c2"/>
  <Txt x={48} y={64} size={15} color={C.orange} weight={650}>{phase?'阶段二':'阶段一'}</Txt><Txt x={48} y={122} size={47} color={C.green} weight={750}>{phase?'继续探索':'从这里开始'}</Txt>
  <Rule x={49} y={143} w={phase?265:310} p={phase?ramp(t,.8,.7):1}/>
  <Txt x={50} y={205} size={25} color={C.muted}>{phase?'新的路径，逐步展开':'把信息组织成清晰的层次'}</Txt>
  <g opacity={phase?ramp(t,1.15,.5):1}><Material id={id} x={w-174} y={h*.52} s={1.3} rot={phase?5:-8} label={phase?'新方向':'方案要点'}/></g>
  <path d={`M50 ${h-67}H${w-50}`} stroke="#d8d6c5"/><Txt x={50} y={h-33} size={14} color={C.muted}>{phase?'保持连续，进入下一页':'一页，一步'}</Txt>
 </g>;
}
export function PaperCurl({time}:DemoProps){
 const t=clamp(time,0,3.6),id='curl',x=165,y=212,w=955,h=383,p=ramp(t,.35,1.2,io),normal={x:-.92198,y:-.38723},corner={x:x+w,y:y+h},s=(.92198*w+.38723*h+8)*p,c=s+normal.x*corner.x+normal.y*corner.y;
 const box=[{x,y},{x:x+w,y},{x:x+w,y:y+h},{x,y:y+h}],old=clipPolygon(box,normal,c),flap=clipPolygon(box,normal,c,false).map(q=>{const z=2*(c-normal.x*q.x-normal.y*q.y);return{x:q.x+z*normal.x,y:q.y+z*normal.y};});
 return <Sheet id={id} kicker="02 / 连续揭示" title="翻开新的一页">
  <CurlPage id={id} x={x} y={y} w={w} h={h} phase={1} t={t}/>
  {p<.999&&<><defs><clipPath id={`${id}-old`}><polygon points={points(old)}/></clipPath></defs><g clipPath={`url(#${id}-old)`}><CurlPage id={id} x={x} y={y} w={w} h={h} phase={0} t={t}/></g><polygon points={points(flap)} fill={`url(#${id}-fold)`} stroke="#fffef8" strokeWidth="2" filter={`url(#${id}-foldShadow)`}/></>}
 </Sheet>;
}

const LINE_POINTS=[[224,540],[1920,540],[1920,210],[2400,210],[2400,540],[1920,540]];
const LINE_LENGTHS=LINE_POINTS.slice(1).map((p,i)=>Math.hypot(p[0]-LINE_POINTS[i][0],p[1]-LINE_POINTS[i][1]));
const TOTAL_LINE=LINE_LENGTHS.reduce((a,b)=>a+b,0);
function tipAt(distance:number){let remain=clamp(distance,0,TOTAL_LINE);for(let i=0;i<LINE_LENGTHS.length;i++){if(remain<=LINE_LENGTHS[i]){const p=remain/LINE_LENGTHS[i];return{x:mix(LINE_POINTS[i][0],LINE_POINTS[i+1][0],p),y:mix(LINE_POINTS[i][1],LINE_POINTS[i+1][1],p)};}remain-=LINE_LENGTHS[i];}return{x:1920,y:540};}
export function LineCarry({time}:DemoProps){
 const t=clamp(time,0,6.4),id='line',cam=1280*ramp(t,1.733,1.867,io),drawn=t<1.4?432*ramp(t,.08,1.12):t<1.733?mix(432,763,ramp(t,1.4,.333,io)):t<3.6?763+cam:mix(2043,TOTAL_LINE,ramp(t,3.6,.8,io)),tip=tipAt(drawn),closed=t>=4.4,headOpacity=1-ramp(t,4.4,.2),poster=ramp(t,4.4,.75);
 return <Sheet id={id} kicker="03 / 路径连接" title="跟随线条，进入下一页">
  <g transform={`translate(${-cam} 0)`}>
   <g filter={`url(#${id}-soft)`}><rect x="177" y="237" width="516" height="335" rx="18" fill={`url(#${id}-paper)`} stroke="#d9d7c5"/></g>
   <Txt x={224} y={291} size={18} color={C.muted}>信息整理</Txt><Txt x={224} y={400} size={100} color={C.green} weight={750}>{Math.round(128*clamp(drawn/432))}</Txt>
   <Txt x={224} y={453} size={25} color={t>=1.2?C.orange:C.muted} weight={650}>{t>=1.2?'准备完成':'正在探索'}</Txt><path d="M224 540H656" stroke="#d4d5c4" strokeWidth="5.5"/>
   {[0,1,2,3,4,5,6,7,8].map(i=><path key={i} d={`M${800+i*120} 552v${i%3===0?20:10}`} stroke={C.line} strokeWidth="1.5" opacity={ramp(drawn+224,800+i*120,40)}/>)}
   <g opacity={ramp(t,3.25,.6)}><Txt x={1400} y={315} size={17} color={C.orange} weight={650}>下一站</Txt><Txt x={1400} y={382} size={45} color={C.green} weight={750}>路径连接</Txt><Txt x={1400} y={431} size={24} color={C.muted}>信息已就位</Txt></g>
   {closed&&<g opacity={poster}>
    <rect x="1920" y="210" width="480" height="330" fill="#f8eedc"/>
    <circle cx="2265" cy={mix(590,360,ramp(t,4.55,.65))} r="91" fill={C.orange}/>
    <path d={`M1920 540Q2080 ${mix(620,390,ramp(t,4.7,.6))} 2240 540Z`} fill={C.ink}/><path d={`M2110 540Q2260 ${mix(650,372,ramp(t,4.8,.6))} 2400 540Z`} fill={C.green}/>
    <Txt x={1951} y={267} size={26} color={C.green} weight={750}>新的方向</Txt><Txt x={1951} y={303} size={17} color={C.muted}>从连接，到展开</Txt>
   </g>}
   <path d="M224 540H1920V210H2400V540H1920" fill="none" stroke={C.ink} strokeWidth="5.5" strokeLinecap="square" strokeLinejoin="miter" strokeDasharray={`${drawn} ${TOTAL_LINE+20}`}/>
   {headOpacity>0&&<g opacity={headOpacity}><circle cx={tip.x} cy={tip.y} r="19" fill={C.orange} opacity=".15"/><circle cx={tip.x} cy={tip.y} r="9" fill={C.orange}/></g>}
  </g>
 </Sheet>;
}

export function LayerExplode({time}:DemoProps){
 const t=clamp(time,0,5.4),id='layers',p=ramp(t,.4,1.35,io),camera=1+.025*ramp(t,1,4.4),labels=['信息层','结构层','要点层'],results=['结构清晰','顺序明确','要点聚焦'];
 return <Sheet id={id} kicker="04 / 材料分层" title="展开层次，看见重点">
  <g transform={`translate(640 410) scale(${camera}) translate(-640 -410)`}>
   {[2,1,0].map(i=>{const yy=mix(390+i*7,280+i*115,p),r=mix(-10,-5,p),green=i===0;return <g key={i} transform={`translate(${mix(366,336,p)} ${yy}) rotate(${r}) skewX(-18) scale(1 .67)`}>
    <path d="M0 8H420V145H0Z" fill={green?'#193d32':'#d4d2bd'} opacity=".8"/>
    <rect width="420" height="138" rx="3" fill={green?`url(#${id}-green)`:i===1?'#e7e1c4':`url(#${id}-paper)`} stroke={green?'#507465':'#c8cbb9'} filter={`url(#${id}-soft)`}/>
    <path d="M29 109H387" stroke={green?'#86a391':'#bdc3af'} strokeWidth="1"/><Txt x={212} y={77} size={30} color={green?C.white:C.green} weight={750} anchor="middle">{labels[i]}</Txt>
    <path d="M370 0V39L382 31L393 39V0" fill={C.orange}/>
   </g>;})}
   {results.map((s,i)=>{const q=ramp(t,1.8+i*.55,.55);return <g key={s} opacity={q}><path d={`M${745} ${317+i*111}L${822} ${278+i*111}H855`} fill="none" stroke={C.sage} strokeWidth="2" pathLength={1} strokeDasharray="1" strokeDashoffset={1-q}/><Check x={871} y={260+i*111} p={q} s={.8}/><Txt x={925} y={288+i*111} size={31} color={C.green} weight={650}>{s}</Txt></g>;})}
  </g>
 </Sheet>;
}

function PressedWords({text,x,y,size,t,id}:any){
 const chars=[...text],groups=Array.from({length:Math.ceil(chars.length/3)},(_,i)=>chars.slice(i*3,i*3+3).join(''));
 return <>{groups.map((part,i)=>{const p=ramp(t,i*.13,.3),scale=1+.28*(1-p);return <g key={part+i} transform={`translate(${x+i*3*size} ${y+10*(1-p)}) scale(${scale})`} opacity={p} style={{filter:p<.999?`blur(${7*(1-p)}px)`:'none'}}><Txt x={0} y={0} size={size} color={C.green} weight={750}>{part}</Txt></g>;})}</>;
}
export function TitleLayout({time}:DemoProps){
 const t=clamp(time,0,6.7),id='title',exit=ramp(t,5.95,1.3,io),x=mix(48,20,exit),y=mix(175,310,exit),w=mix(302,190,exit),h=mix(425,260,exit),intro=out(t/.3);
 return <Sheet id={id} kicker="05 / 构图与表达" title="让想法，井然成形">
  <LayoutFrame id={id} x={x} y={y} w={w} h={h} p={1-exit} rot={mix(-1.5,-4,exit)} zoom={1+.045*ramp(t,.2,5)}/>
  <g transform={`translate(${-85*exit} 0)`}>
   <PressedWords id={id} text="让想法" x={410} y={335} size={70} t={t-.08}/><PressedWords id={id} text="井然成形" x={410} y={438} size={75} t={t-.27}/>
   <Rule x={412} y={468} w={535} p={ramp(t,.75,.7)}/><Txt x={412} y={533} size={25} color={C.muted} opacity={ramp(t,1,.5)}>从探索，到表达</Txt>
   <g opacity={intro}><Document id={id} x={1110} y={357} s={.62} rot={10-3*ramp(t,0,6.7)} label="方案要点"/></g>
  </g>
 </Sheet>;
}

const components={document_dive:DocumentDive,paper_curl:PaperCurl,line_carry:LineCarry,layer_explode:LayerExplode,title_layout:TitleLayout};
export function DemoFrame({id,time}:{id:DemoId;time:number}){const Component=components[id];return <Component time={time}/>;}

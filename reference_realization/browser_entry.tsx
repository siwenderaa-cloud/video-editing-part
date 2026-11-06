import React from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import {DemoFrame,demoSpecs,DemoId} from './NeutralDemos';

const $=(id:string)=>document.getElementById(id)!;
const specs=demoSpecs;
const master=$('master') as HTMLVideoElement,select=$('demoSelect') as HTMLSelectElement,versionSelect=$('versionSelect') as HTMLSelectElement,seek=$('seek') as HTMLInputElement;
const replay=createRoot($('replay'));
let current:typeof specs[number]=specs[0],mode='movie',version='silent',raf=0,renderedTime=0,renderedKey='';
type SoundCue={id:string;file:string;start_seconds:number;gain_db:number;duration_seconds:number;label:string};
const motionAudio=$('motionAudio') as HTMLAudioElement;
let cues:SoundCue[]=[],soundBase='',soundTime=0,soundLoad=0,soundRequest=0,pendingAudition:SoundCue|null=null;

function audioRoute(){return version==='silent'?'silent':mode==='movie'?'mp4':'wav';}
function soundNote(){
 const route=audioRoute();
 return route==='silent'?'当前无声版：视频和源码重演均不播放动作声。':route==='mp4'?'当前有声视频：只播放MP4自带音轨，不再叠加小音频。':'当前有声源码重演：主视频静音，按同一时钟触发小音频；拖动不补播。';
}
function routeAudio(){
 const route=audioRoute();master.muted=route!=='mp4';master.defaultMuted=route!=='mp4';master.volume=1;
 $('soundStatus').dataset.route=route;$('soundStatus').textContent=soundNote();
}
function resetCounters(){$('soundStatus').dataset.triggerCount='0';$('soundStatus').dataset.lastSound='';}
function stopSounds(){pendingAudition=null;soundRequest++;motionAudio.pause();if(motionAudio.readyState)motionAudio.currentTime=0;}
function playSound(cue:SoundCue,manual=false){
 if(manual&&!master.paused){pendingAudition=cue;master.pause();return;}
 stopSounds();const request=++soundRequest;
 motionAudio.src=soundBase+encodeURIComponent(cue.file);motionAudio.volume=Math.min(1,Math.pow(10,Number(cue.gain_db||0)/20));
 $('soundStatus').textContent='正在试听：'+cue.label;
 motionAudio.play().then(()=>{if(request===soundRequest){$('soundStatus').dataset.triggerCount=String(Number($('soundStatus').dataset.triggerCount||0)+1);$('soundStatus').dataset.lastSound=cue.label;}}).catch(e=>{if(e.name!=='AbortError'&&request===soundRequest)$('soundStatus').textContent='音效未能播放，请点击试听按钮重试。';});
}
function syncSounds(t:number){
 const prior=soundTime;soundTime=t;
 if(version!=='with_sound'||mode!=='source'||master.paused||master.seeking||t<prior||t-prior>.35)return;
 for(const cue of cues)if(prior<cue.start_seconds&&cue.start_seconds<=t)playSound(cue);
}
async function loadSounds(id:string){
 const revision=++soundLoad;stopSounds();cues=[];
 soundBase=`prompts/${id}/motion_music/Specific_motion_${id}/`;$('soundList').replaceChildren();
 try{
  const response=await fetch(soundBase+'cue.json');if(!response.ok)throw Error('No sound cues');
  const data=await response.json();if(revision!==soundLoad)return;
  cues=(Array.isArray(data.cues)?data.cues:[]).slice(0,5);
  for(const cue of cues){const button=document.createElement('button');button.type='button';button.textContent=`试听 ${cue.label} · ${cue.duration_seconds.toFixed(2)}秒`;button.title=`动画${cue.start_seconds.toFixed(3)}秒处触发`;button.addEventListener('click',()=>playSound(cue,true));$('soundList').append(button);}
  routeAudio();
 }catch{if(revision===soundLoad)$('soundStatus').textContent='此组小音频暂不可用；两版MP4仍可分别播放。';}
}
const limit=(t:number)=>Math.max(0,Math.min(current.duration,Number(t)||0));
function draw(t:number){
 const local=limit(t),frame=Math.min(current.frames-1,Math.floor(local*current.fps)),key=current.id+':'+frame;
 renderedTime=frame/current.fps;
 if(mode==='source'&&key!==renderedKey){flushSync(()=>replay.render(<DemoFrame id={current.id as DemoId} time={renderedTime}/>));renderedKey=key;}
 seek.value=String(local);$('time').textContent=`${local.toFixed(3)} / ${current.duration.toFixed(3)}秒`;
}
function tick(){draw(master.currentTime);syncSounds(master.currentTime);if(!master.paused&&!master.ended)raf=requestAnimationFrame(tick);}
function fail(e:any){$('error').textContent=String(e?.message||e);}
function updateLinks(){
 const id=current.id,silent=`prompts/${id}/None_Specific_motion_${id}.md`,sound=`prompts/${id}/Specific_motion_${id}.md`;
 ($('silentPrompt') as HTMLAnchorElement).href=silent;($('soundPrompt') as HTMLAnchorElement).href=sound;
 $('silentPrompt').setAttribute('aria-current',String(version==='silent'));$('soundPrompt').setAttribute('aria-current',String(version==='with_sound'));
 ($('download') as HTMLAnchorElement).href=`assets/${id}/${version}.mp4`;
 ($('download') as HTMLAnchorElement).download=`${id}_${version}.mp4`;
 $('download').textContent=version==='silent'?'下载无声版':'下载有声版';
 $('spec').textContent=`${current.duration.toFixed(1)}秒 · ${current.frames}帧 · ${current.width}×${current.height} · ${current.fps}fps · ${version==='silent'?'无声MP4':'有动作声MP4'}`;
}
function loadMedia(){
 master.pause();cancelAnimationFrame(raf);stopSounds();soundTime=0;resetCounters();
 master.src=`assets/${current.id}/${version}.mp4`;master.poster=`assets/${current.id}/poster.jpg`;master.load();
 versionSelect.value=version;seek.max=String(current.duration);$('error').textContent='';renderedKey='';draw(0);updateLinks();routeAudio();
}
function setVersion(value:string){version=value==='with_sound'?'with_sound':'silent';loadMedia();}
function setMode(value:string){
 stopSounds();soundTime=master.currentTime;resetCounters();mode=value==='source'?'source':'movie';
 master.style.opacity=mode==='movie'?'1':'0';$('replay').style.display=mode==='source'?'block':'none';
 $('movieMode').setAttribute('aria-pressed',String(mode==='movie'));$('sourceMode').setAttribute('aria-pressed',String(mode==='source'));
 $('modeNote').textContent=mode==='source'?'源码重演：运行本地TSX编译产物，画面采样与视频共用时钟。':'视频模式：播放所选版本的实际MP4。';
 routeAudio();draw(master.currentTime);
}
function seekTo(t:number){master.pause();stopSounds();const local=limit(t);soundTime=local;master.currentTime=local;draw(local);routeAudio();}
async function selectDemo(id:string){
 const next=specs.find(d=>d.id===id);if(!next)throw Error('未知样段');current=next;select.value=id;$('demoTitle').textContent=current.label;
 loadMedia();await loadSounds(id);return current;
}
for(const s of specs){const option=document.createElement('option');option.value=s.id;option.textContent=s.label;select.append(option);}
select.addEventListener('change',()=>selectDemo(select.value).catch(fail));
versionSelect.addEventListener('change',()=>setVersion(versionSelect.value));
$('movieMode').addEventListener('click',()=>setMode('movie'));
$('sourceMode').addEventListener('click',()=>setMode('source'));
$('play').addEventListener('click',()=>{if(master.paused){if(master.ended)seekTo(0);master.play().catch(fail);}else master.pause();});
$('restart').addEventListener('click',()=>{seekTo(0);resetCounters();master.play().catch(fail);});
seek.addEventListener('input',()=>seekTo(Number(seek.value)));
master.addEventListener('play',()=>{stopSounds();soundTime=master.currentTime;routeAudio();$('play').textContent='暂停';cancelAnimationFrame(raf);tick();});
master.addEventListener('pause',()=>{const audition=pendingAudition;stopSounds();routeAudio();cancelAnimationFrame(raf);$('play').textContent='播放';draw(master.currentTime);if(audition)playSound(audition,true);});
master.addEventListener('seeking',()=>{stopSounds();soundTime=master.currentTime;});
master.addEventListener('seeked',()=>{soundTime=master.currentTime;draw(master.currentTime);});
master.addEventListener('timeupdate',()=>{if(master.paused)draw(master.currentTime);});
master.addEventListener('ended',()=>{stopSounds();$('play').textContent='播放';draw(current.duration);routeAudio();});
master.addEventListener('error',()=>fail('所选MP4读取失败，请确认两版文件已归位并通过本地HTTP打开。'));
motionAudio.addEventListener('ended',()=>routeAudio());
(window as any).demoApi={selectDemo,setMode,setVersion,seek:seekTo,state:()=>({id:current.id,mode,version,audioRoute:audioRoute(),localTime:master.currentTime,renderedTime,duration:current.duration,mainMuted:master.muted})};
selectDemo(current.id).catch(fail);setMode('movie');

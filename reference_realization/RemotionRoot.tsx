import React from 'react';
import {AbsoluteFill,Composition,registerRoot,useCurrentFrame,useVideoConfig} from 'remotion';
import {DemoFrame,demoSpecs,DemoId} from './NeutralDemos';

function Film({id}:{id:DemoId}){const f=useCurrentFrame(),{fps}=useVideoConfig();return <AbsoluteFill><DemoFrame id={id} time={f/fps}/></AbsoluteFill>;}
function Root(){return <>{demoSpecs.map(s=><Composition key={s.id} id={s.id.replaceAll('_','-')} component={Film} defaultProps={{id:s.id}} width={s.width} height={s.height} fps={s.fps} durationInFrames={s.frames}/>)}</>;}
registerRoot(Root);

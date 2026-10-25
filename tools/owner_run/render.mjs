import puppeteer from 'puppeteer-core';import fs from 'fs';import {execSync} from 'child_process';
const [,,which,ts,v,out,glb='/varnethryl-owner-test/owner-animated.glb']=process.argv;
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage();p.on('pageerror',e=>console.log('ERR',e.message));p.on('console',m=>{if(!/404/.test(m.text()))console.log('PAGE',m.text())});
await p.setViewport({width:1280,height:540});await p.goto('http://localhost:8731/or/rh.html');await p.waitForFunction('window.ready');
await p.evaluate(u=>setup(u),glb);const dur=await p.evaluate((w,t)=>useClip(w,+t),which,ts);
// slide metric (clip local time, in-place clip + body moving at v)
const m=await p.evaluate((v,d,ts)=>{const res={};const N=600;const THREE=null;return null},+v,dur,+ts);
const dir='frames_'+which;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir);
const fps=30,secs=4;for(let i=0;i<fps*secs;i++){const d=await p.evaluate((t,v)=>frame(t,v),i/fps,+v);fs.writeFileSync(`${dir}/f${String(i).padStart(4,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64'));}
await b.close();
execSync(`ffmpeg -y -loglevel error -framerate ${fps} -i ${dir}/f%04d.jpg -c:v libx264 -pix_fmt yuv420p -crf 20 ${out}`);console.log('wrote',out,'clip',dur);

import puppeteer from 'puppeteer-core';import fs from 'fs';import {execSync} from 'child_process';
const [,,mode,glb,out]=process.argv;
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage();p.on('pageerror',e=>console.log('ERR',e.message));await p.setViewport({width:1280,height:540});
await p.goto('http://localhost:8731/or/rh.html');await p.waitForFunction('window.ready');await p.evaluate(g=>setup(g),glb);await p.evaluate(m=>seqInit(m),mode);
const dir='frames_seq_'+mode;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir);const fps=30;
for(let i=0;i<fps*6;i++){const [d,v,m]=await p.evaluate((t,dt)=>seqFrame(t,dt),i/fps,1/fps);if(i%15==0)console.log(i/fps,v,m);fs.writeFileSync(`${dir}/f${String(i).padStart(4,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64'));}
await b.close();execSync(`ffmpeg -y -loglevel error -framerate ${fps} -i ${dir}/f%04d.jpg -c:v libx264 -pix_fmt yuv420p -crf 20 ${out}`);

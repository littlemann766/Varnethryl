import puppeteer from 'puppeteer-core';import fs from 'fs';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage();p.on('pageerror',e=>console.log('ERR',e.message));await p.goto('http://localhost:8731/or/rh.html');await p.waitForFunction('window.ready');
await p.evaluate(()=>setup('/or/orig.glb'));const r=await p.evaluate(()=>shiftedOldRun());fs.writeFileSync('oldrun_shift.json',JSON.stringify(r));console.log('td',r.td);await b.close();

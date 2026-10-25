import puppeteer from 'puppeteer-core';
const [,,which,ts,v,glb='/varnethryl-owner-test/owner-animated.glb']=process.argv;
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage();p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('http://localhost:8731/or/rh.html');await p.waitForFunction('window.ready');
await p.evaluate(g=>setup(g),glb);const dur=await p.evaluate((w,t)=>useClip(w,+t),which,ts);
const r=await p.evaluate((v,ts,dur)=>{const out={};const N=600;const realDur=dur/ts;
 for(const s of ['Left','Right']){const rows=[];for(let i=0;i<=N;i++){const t=realDur*i/N;window.frameNoRender(t);const q=window.toe(s);rows.push([t,q[1],q[2]+v*t]);}out[s]=rows;}return {out,realDur};},+v,+ts,dur);
let worst=0,sum=0,n=0;const rep={};
for(const s of ['Left','Right']){const rows=r.out[s];const ymin=Math.min(...rows.map(x=>x[1]));const st=[];
 for(let i=1;i<rows.length;i++){if(rows[i][1]<ymin+(+process.env.TH||0.012)&&rows[i-1][1]<ymin+(+process.env.TH||0.012)){const sp=Math.abs((rows[i][2]-rows[i-1][2])/(rows[i][0]-rows[i-1][0]));st.push(sp);}}
 st.sort((a,b)=>a-b);rep[s]={stanceFrac:+(st.length/rows.length).toFixed(3),medianSlide:+st[st.length>>1].toFixed(3),maxSlide:+st.at(-1).toFixed(3),meanSlide:+(st.reduce((a,b)=>a+b,0)/st.length).toFixed(3)};}
console.log(JSON.stringify({which,timeScale:+ts,groundV:+v,cycleSec:+r.realDur.toFixed(3),stepsPerMin:Math.round(120/r.realDur),rep}));await b.close();

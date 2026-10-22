/* CombatHUD: presentation only. Subscribes to CombatController events and reads its state; never computes damage.
   Perf: all nodes are built once; per frame we only write a style/text when the displayed value changed. Floating numbers come from a fixed pool. */
import { ABILITIES, OWNER_SKILLS, OWNER_CLUSTER, TUNING } from './data.js';
import { OWNER_ICON } from './ownericons.js';
const CSS = `
#cb{position:fixed;inset:0;z-index:40;display:none;pointer-events:none;font:700 12px system-ui,sans-serif;color:#fff;user-select:none;-webkit-user-select:none}
#cb *{box-sizing:border-box}#cb button{pointer-events:auto;touch-action:none;font:inherit;color:#fff;cursor:pointer}
#cb .tp{position:absolute;left:50%;top:max(52px,calc(env(safe-area-inset-top) + 46px));transform:translateX(-50%);width:min(210px,52vw);padding:4px 8px 6px;border:1px solid #fff6;border-radius:8px;background:#000b;display:none;text-align:center}
#cb .tp .nm{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#cb .tp .sub{font-size:10px;color:#ccd;margin-bottom:3px}
#cb .tp.boss{top:max(4px,env(safe-area-inset-top));width:min(560px,92vw);padding:3px 10px 5px}#cb .tp.boss .nm{font-size:15px;letter-spacing:.12em;color:#f0c98b;text-shadow:0 2px 4px #000}
#cb .bar{position:relative;height:12px;border:1px solid #000;border-radius:6px;background:#2a2a2a;overflow:hidden}#cb .tp.boss .bar{height:16px}#cb .tp.boss .bar:after{content:'';position:absolute;left:50%;top:0;bottom:0;width:2px;background:#ffd56e;opacity:.8;z-index:2}#cb .tp.boss.enr .nm{color:#ff6a3a;text-shadow:0 0 8px #ff3a1a}#cb .tp.boss.enr .bar>i{filter:hue-rotate(-20deg) saturate(1.6)}#cb .tp.boss.tel .nm:after{content:' \u26A0';color:#ffd56e}
#cb .bar i{position:absolute;left:0;top:0;bottom:0;width:100%;transform-origin:left;will-change:transform}
#cb .bar b{position:absolute;inset:0;text-align:center;font-size:9px;line-height:11px;text-shadow:0 1px 1px #000}#cb .tp.boss .bar b{line-height:15px;font-size:11px}
#cb .hp i{background:linear-gradient(#ff6b6b,#c21f1f)}#cb .mp i{background:linear-gradient(#6bb8ff,#1f5fd0)}#cb .sp i{background:linear-gradient(#7dff8a,#1fa83a)}
#cb .vit{position:absolute;left:max(10px,env(safe-area-inset-left));bottom:max(184px,calc(env(safe-area-inset-bottom) + 178px));width:min(176px,44vw);display:flex;gap:6px;align-items:center}
#cb .por{flex:none;width:42px;height:42px;border-radius:50%;border:2px solid #fff;background:radial-gradient(#4a6ea8,#1b2a48);display:flex;align-items:center;justify-content:center;font:900 18px system-ui;position:relative}
#cb .por small{position:absolute;bottom:-5px;right:-5px;background:#000c;border:1px solid #fff8;border-radius:8px;font:700 9px system-ui;padding:0 3px}
#cb .bars{flex:1;display:flex;flex-direction:column;gap:3px}
#cb .fy i{background:linear-gradient(#ffd27a,#c9741a)}#cb .fy{display:none}#cb.own .fy{display:block}
#cb .cx{position:absolute;right:max(10px,env(safe-area-inset-right));bottom:max(10px,env(safe-area-inset-bottom));width:clamp(210px,min(48vw,66vh),270px);aspect-ratio:1}
#cb .sl{position:absolute;aspect-ratio:1;border-radius:50%;border:2px solid #caa35c;background:radial-gradient(circle at 40% 25%,#4c453c,#242322 48%,#100f12 85%);box-shadow:inset 0 0 0 2px #19120d,inset 0 0 14px #0009,0 3px 12px #000c,0 0 0 1px #58432b;padding:0;overflow:hidden;color:#f8e3b7}
/* fighting-pad layout: LARGE basic in the corner, A/B/C-style staggered arc of skills 1-3, ultimate high on the right */
#cb .sl.b0{width:42%;right:0;bottom:0;border-width:4px}#cb .sl.b1{width:25%;right:46%;bottom:2%}#cb .sl.b2{width:25%;right:58%;bottom:30%}#cb .sl.b3{width:25%;right:32%;bottom:46%}
#cb .ulp{position:absolute;right:0;bottom:92%;display:none;flex-direction:column;gap:6px;z-index:4}#cb .ulp.open{display:flex}#cb .ulp button{min-height:48px;padding:6px 14px;border-radius:12px;border:2px solid #ffd56e;background:#241a35;color:#fff;font:inherit;font-weight:700}#cb .ulp button[data-u=unholy]{border-color:#8a5cf6;background:#120c1c}#cb .ulp button[data-u=holy]{background:#4a4030;color:#fff3c4}#cb .swp{position:absolute;right:31%;bottom:84%;width:44px;height:44px;border-radius:50%;border:2px solid #ffd56e;background:#241a35;color:#fff;font-size:20px;display:none;z-index:3}#cb .sl.b4.u-unholy{border-color:#8a5cf6}#cb .sl.b4.u-unholy .ic{filter:hue-rotate(250deg) saturate(.7) brightness(.55)}#cb .sl.b4.u-holy .ic{filter:saturate(.45) brightness(1.55)}#cb .sl.b4.u-holy{border-color:#fff3c4}#cb .sl.b4{width:30%;right:0;bottom:58%;border:3px solid #ffd56e;background:radial-gradient(circle,#852723,#321224 54%,#110c19)}
#cb .sl:focus-visible,#cb .cl button:focus-visible,#cb .ulp button:focus-visible{outline:3px solid #f9e0a2;outline-offset:3px}
#cb .tp.boss{background:linear-gradient(180deg,#2e211ce8,#0d1018ed);border:2px solid #a9804b;box-shadow:inset 0 0 0 1px #4d3727,0 5px 18px #000b}
#cb .vit .por{border-color:#caa35c;box-shadow:0 0 0 2px #281a11,0 4px 12px #000b}
#cb .sl .ic{position:absolute;inset:18%;display:flex;align-items:center;justify-content:center}#cb .sl svg{width:100%;height:100%;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
#cb .sl .k{position:absolute;left:0;right:0;bottom:5%;text-align:center;font-size:9px;color:#ffe9a8;text-shadow:0 1px 2px #000}
#cb .sl.oi{border-color:transparent;background:none;box-shadow:0 3px 10px #000b}#cb .sl.oi .ic{inset:0}#cb .sl.oi svg{stroke:none;stroke-width:0}#cb .sl.oi.b4.rdy{box-shadow:0 0 18px #ff7a2a}#cb .sl.oi .k{text-shadow:0 1px 3px #000,0 0 4px #000}#cb .sl .rg{position:absolute;inset:0;border-radius:50%;background:conic-gradient(#000d var(--p,0%),transparent 0)}#cb .sl .ct{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:900 16px system-ui;text-shadow:0 1px 2px #000}
#cb .sl.fr .rg{background:conic-gradient(#e8a02c66 var(--p,0%),transparent 0)}#cb .sl.rdy{box-shadow:inset 0 0 0 2px #141010,0 0 16px #ff8a3c}
#cb .sl.off{filter:grayscale(1) brightness(.55)}#cb .sl.nores{border-color:#f66}#cb .sl:active:not(.off){transform:scale(.93)}
#cb .cl{position:absolute;right:calc(max(10px,env(safe-area-inset-right)) + clamp(210px,min(48vw,66vh),270px) + 8px);bottom:max(10px,env(safe-area-inset-bottom));display:grid;grid-template-columns:repeat(3,46px);gap:5px}
#cb .cl button{position:relative;width:46px;height:46px;border-radius:50%;border:2px solid #fffb;background:#0c2438dd;font-size:9px;line-height:1.05;padding:0;overflow:hidden}
#cb .cl button .g{display:block;font:400 19px system-ui;line-height:20px}#cb .cl button.on{background:#2aa;border-color:#9ff}
#cb .cl button .cdv{position:absolute;left:0;right:0;bottom:0;height:0;background:#000b}#cb .cl button .q{position:absolute;right:3px;top:2px;font-size:9px;color:#ffe9a8}
#cb .fn{position:absolute;transform:translate3d(-50px,-50px,0);font:900 20px system-ui;color:#ffe066;text-shadow:0 0 3px #000,0 2px 2px #000;white-space:nowrap;display:none;will-change:transform,opacity}
#cb .fn.crit{color:#ff9d2e;font-size:27px}#cb .fn.pl{color:#ff5a5a}#cb .fn.heal{color:#7dff8a}
#cb .oh{position:absolute;left:0;top:0;width:54px;height:7px;border:1px solid #000;border-radius:4px;background:#500;overflow:hidden;display:none;will-change:transform}#cb .oh i{display:block;height:100%;width:100%;background:#e33;transform-origin:left}
#cb .oh.lock{border-color:#ffd54a;box-shadow:0 0 6px #ffd54a}
#cb .msg{position:absolute;left:50%;top:34%;transform:translate(-50%,-50%);font:900 24px system-ui;text-shadow:0 2px 8px #000;display:none;text-align:center}
#cb .flash{position:absolute;inset:0;background:radial-gradient(transparent 40%,#f00a);opacity:0;transition:opacity .25s}
#cb .top{position:absolute;right:max(10px,env(safe-area-inset-right));top:max(78px,calc(env(safe-area-inset-top) + 72px));display:flex;flex-direction:column;gap:4px;align-items:flex-end;text-shadow:0 1px 2px #000}
#cb .top button{min-height:26px;padding:3px 9px;border-radius:10px;border:1px solid #fff7;background:#000a;font-size:11px}
#cb .stat{position:absolute;left:max(10px,env(safe-area-inset-left));top:max(76px,calc(env(safe-area-inset-top) + 70px));font-size:11px;text-shadow:0 1px 2px #000;line-height:1.35}
@media (orientation:portrait){#cb .cl{grid-template-columns:repeat(2,46px);right:max(10px,env(safe-area-inset-right));bottom:calc(max(10px,env(safe-area-inset-bottom)) + clamp(210px,min(48vw,66vh),270px) + 6px)}#cb .vit{bottom:calc(max(10px,env(safe-area-inset-bottom)) + 150px)}}
/* ==== RESTYLE to /workspace/hudui prototype (Owner Combat HUD): gold-rimmed dark panels, Georgia labels, prototype bar colours, fighting-pad positions,
   skill names under each button. Overrides only; structure, ids and behaviour above are Lucky's and unchanged. ==== */
#cb{--gold:#d6ae6a;--line:#947444}
#cb .vit{flex-wrap:wrap;width:min(320px,47vw);padding:8px 10px;background:#0a0d16bb;border:1px solid #96743f;border-radius:10px;box-shadow:0 8px 30px #0009;bottom:auto;top:calc(max(6px,env(safe-area-inset-top)) + 54px);left:max(12px,env(safe-area-inset-left))}
#cb .vit .lab{flex:0 0 100%;order:-1;font:400 10px system-ui,sans-serif;letter-spacing:.13em;color:#e8cb92;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px}
#cb .por{width:52px;height:52px;border:2px solid #c49c60;background:#392c2c;font:700 22px Georgia,serif;color:#f6e9d0}
#cb .por small{border-color:#c49c60;color:#f2d3a0}
#cb .vit .bar{height:12px;background:#08090d;border:1px solid #9b8567;border-radius:2px}
#cb .vit .hp i,#cb .tp .hp i{background:linear-gradient(90deg,#762126,#f54340)}#cb .vit .mp i{background:linear-gradient(90deg,#16457e,#399dfb)}#cb .vit .sp i{background:linear-gradient(90deg,#1d5e2c,#5fd77a)}#cb .vit .fy i{background:linear-gradient(90deg,#8c4b17,#ffbd3f)}
#cb .vit .bar b{font:600 9px system-ui,sans-serif;color:#f6e9d0}
#cb .tp{background:#0a0d16cc;border-color:#96743f;font-family:Georgia,serif;color:#f6e9d0}#cb .tp .sub{color:#dfccac}#cb .tp .bar{border-color:#9b8567;background:#08090d;border-radius:2px}
#cb .stat{top:calc(max(6px,env(safe-area-inset-top)) + 150px);font-family:Georgia,serif;color:#f6e9d0}
#cb .cx{width:min(410px,49vw);height:min(310px,51vh);aspect-ratio:auto;right:max(15px,env(safe-area-inset-right));bottom:max(24px,env(safe-area-inset-bottom))}
#cb .sl{overflow:visible;box-shadow:inset 0 0 0 3px #141010,0 4px 14px #000b,0 0 14px #da98}
#cb .sl.b0{width:auto;height:48%;right:1%;bottom:0;border-width:4px;box-shadow:inset 0 0 0 4px #1d1211,0 0 20px #eda54b5f}
#cb .sl.b1,#cb .sl.b2,#cb .sl.b3{width:auto;height:32%}
#cb .sl.b1{right:39%;bottom:2%}#cb .sl.b2{right:64%;bottom:36%}#cb .sl.b3{right:33%;bottom:50%}
#cb .sl.b4{width:auto;height:40%;right:1%;bottom:52%;box-shadow:0 0 24px #ec421e9c,inset 0 0 16px #ef8f3c}
#cb .ulp{bottom:102%}
#cb .sl .k{font:600 10px system-ui,sans-serif;color:#f2d3a0;bottom:7%}
#cb .sl .nmL{position:absolute;left:50%;bottom:-17px;transform:translateX(-50%);white-space:nowrap;font:600 9px system-ui,sans-serif;color:#e8c887;text-shadow:0 2px 4px #000;pointer-events:none}
#cb .sl.b4 .nmL{bottom:auto;left:auto;right:0;top:-14px;transform:none;text-transform:uppercase;letter-spacing:.06em}
#cb .sl .ct{font:700 18px system-ui,sans-serif}
#cb .msg{font:700 clamp(13px,3vw,19px) Georgia,serif;color:#ffe2a8;letter-spacing:.03em;max-width:min(72vw,290px);line-height:1.3;text-wrap:balance}
#cb .cl{right:calc(max(15px,env(safe-area-inset-right)) + min(410px,49vw) + 8px);bottom:max(24px,env(safe-area-inset-bottom))}
#cb .cl button{border-color:#bd9451;background:radial-gradient(circle at 45% 30%,#29344b,#101521 58%,#080c15);color:#f2d3a0}#cb .cl button.on{background:#5a4320;border-color:#ffd56e}
#cb .top button{border-color:#96743f;background:#0a0d16bb;color:#f6e9d0;font-family:Georgia,serif}
@media (max-height:470px){#cb .cx{height:58vh;width:min(43vw,77vh)}#cb .cl{right:calc(max(15px,env(safe-area-inset-right)) + min(43vw,77vh) + 8px)}}
@media (orientation:portrait){#cb .cx{width:70vw;height:53vw}#cb .cl{right:max(10px,env(safe-area-inset-right));bottom:calc(max(24px,env(safe-area-inset-bottom)) + 53vw + 30px)}#cb .vit{width:min(320px,62vw)}}

/* VARNETHRYL v1.2 — royal fantasy combat UI. All old button handlers, skills and
   controller permissions stay intact. This is visual only, not a fake demo HUD. */
#cb{--bronze:#ae8754;--gold:#eccd8b;--blue:#182838;--surface:#101621;--ruby:#a42a31;color:#f8efdc;font-family:Georgia,'Times New Roman',serif}
#cb .vit{width:min(316px,45vw);border:2px solid #ba9355;border-radius:6px;
 background:linear-gradient(146deg,#303039f0,#111b26f3 55%,#080d16f0);
 box-shadow:0 5px 0 #08090e99,inset 0 0 0 2px #42351e,0 9px 27px #0008}
#cb .vit:after{content:'⚜ VARNETHRYL ⚜';position:absolute;top:-12px;left:50%;transform:translateX(-50%);
 font:700 9px Georgia,serif;letter-spacing:.22em;white-space:nowrap;color:#f6d493;
 padding:3px 13px;background:linear-gradient(#293445,#121a27);border:1px solid #ab8a57;border-radius:16px;
 text-shadow:0 1px 4px #09080b}
#cb .vit .lab{font:700 11px Georgia,serif;color:#f6dfa8;letter-spacing:.1em;margin-top:2px}
#cb .por{background:radial-gradient(circle at 39% 33%,#766240,#342d35 50%,#0c121a);border:3px ridge #cfaf73;
 box-shadow:inset 0 0 6px #000c,0 0 9px #b9894255}
#cb .cx{filter:drop-shadow(0 8px 9px #0009)}
#cb .sl{border:3px solid #ad8c5c;background:
 radial-gradient(circle at 46% 30%,#304359,#16202e 52%,#080d16 82%);
 box-shadow:0 0 0 2px #0a0d14,0 0 0 3px #46381f,inset 0 0 0 2px #69522c,0 4px 12px #000d;
 transition:filter .1s,box-shadow .1s}
#cb .sl .ic{color:#ffdf96;filter:drop-shadow(0 0 3px #db8a3388)}
#cb .sl .nmL{font:700 10px Georgia,serif;color:#fff0c9;letter-spacing:.012em;
 text-shadow:0 2px 2px #000,0 0 7px #000,0 0 9px #000}
#cb .sl.b0{border-color:#e2bd78;background:radial-gradient(circle at 45% 30%,#5a3c24,#252232 58%,#0e1622)}
#cb .sl.b0 .nmL{font-size:11px}
#cb .sl.b4{border:4px ridge #e9ad5d;background:radial-gradient(circle at 43% 35%,#ae4a20,#432027 56%,#160b15);
 box-shadow:inset 0 0 0 3px #ffd28d4b,0 0 19px #ff7d3766}
#cb .sl.b4 .nmL{color:#ffe2ad;font-size:10px;top:-18px}
#cb .sl.b4.rdy{animation:varnUltGlow 2s ease-in-out infinite}
@keyframes varnUltGlow{50%{box-shadow:inset 0 0 13px #ebbd71,0 0 25px #f0833599}}
#cb .sl.off{opacity:.60;filter:grayscale(.85)}
#cb .sl .k{font:700 10px Georgia,serif;bottom:6%;color:#fff2cf}
#cb .cl button{border:2px ridge #aa8b5c;background:radial-gradient(circle at 42% 27%,#334459,#111b29 60%,#090d15);
 box-shadow:inset 0 0 0 1px #71603e,0 3px 9px #0009;
 color:#f4ddab;font:700 10px Georgia,serif}
#cb .cl button .g{color:#e8b86f}
#cb .tp{border:2px ridge #ac8a58;border-radius:5px;background:linear-gradient(110deg,#101721ee,#2c2029ee,#101721ee);
 box-shadow:inset 0 0 0 2px #352b23,0 5px 16px #000c}
#cb .tp.boss .nm{font:700 17px Georgia,serif;color:#ffcf84;text-shadow:0 2px 5px #000}
#cb .tp.boss .bar{border:1px solid #bba173}
#cb .top button{font:700 11px Georgia,serif;border:1px solid #c09d63;background:linear-gradient(#233144dd,#0e1624ee);border-radius:5px}
#cb .stat{color:#f4e0ac}
#cb .ulp button{font:700 13px Georgia,serif;background:linear-gradient(#2d2a3f,#101421);box-shadow:0 5px 10px #0007}
@media(orientation:portrait){
 #cb .vit{width:min(274px,59vw)}
 #cb .cx{right:max(8px,env(safe-area-inset-right));bottom:max(14px,env(safe-area-inset-bottom));width:64vw;height:49vw}
 #cb .sl .nmL{font-size:8px}
 #cb .cl{right:max(8px,env(safe-area-inset-right));bottom:calc(max(14px,env(safe-area-inset-bottom)) + 49vw + 33px)}
}
@media(orientation:landscape) and (max-height:490px){
 #cb .vit{top:calc(max(3px,env(safe-area-inset-top)) + 38px);padding:5px 8px}
 #cb .stat{display:none}
 #cb .cx{height:61vh;width:min(39vw,70vh)}
 #cb .sl .nmL{font-size:8px}
}

/* Unified Varnethryl chrome - match the title screen without changing live combat handlers. */
@font-face{font-family:VarnCinzel;src:url('./fonts/Cinzel.woff') format('woff');font-display:swap}
#cb{color:#f7e8c8;font-family:VarnCinzel,Georgia,serif}
#cb .vit{background:linear-gradient(135deg,#25344bee,#0a1120f6);border:2px ridge #c5a064;box-shadow:inset 0 0 0 2px #f0d49a22,0 8px 24px #000a}
#cb .vit:after{background:linear-gradient(#253449,#0a1322);border-color:#bc995a;font:700 9px VarnCinzel,Georgia,serif}
#cb .vit .lab{font-family:VarnCinzel,Georgia,serif}
#cb .tp{background:linear-gradient(120deg,#1a2840f4,#0a1120f0);border:2px ridge #c09a58}
#cb .tp .nm{color:#f7da92;font-family:VarnCinzel,Georgia,serif}
#cb .tp.boss .nm{color:#f0c47b;font-family:VarnCinzel,Georgia,serif}
#cb .sl{border-color:#b99457;background:radial-gradient(circle at 43% 29%,#304158,#0c1728 69%,#070d18);box-shadow:0 0 0 2px #0a101c,inset 0 0 0 2px #765d33,0 5px 14px #000a}
#cb .sl.b0{border-color:#e2bc70;background:radial-gradient(circle at 43% 29%,#614a2f,#263044 59%,#0b1321)}
#cb .sl.b4{border:4px ridge #e4bd73;background:radial-gradient(circle at 45% 33%,#853d31,#381c2c 53%,#100b1e)}
#cb .sl .nmL{font:700 10px VarnCinzel,Georgia,serif;color:#f5ddb0}
#cb .sl .k{font-family:VarnCinzel,Georgia,serif;color:#f4dda6}
#cb .cl button{border:2px ridge #b99558;background:radial-gradient(circle at 45% 30%,#30435c,#111e30 70%,#0c1120);font:700 10px VarnCinzel,Georgia,serif}
#cb .top button,#cb .ulp button{border:1px solid #bc9553;border-radius:6px;background:linear-gradient(#28394e,#0b1526);color:#f8e4b8;font-family:VarnCinzel,Georgia,serif}
#cb .oh{border:1px solid #ccaa62;background:#1d0e15}
#cb .oh i{background:linear-gradient(90deg,#82272b,#eb5c51)}
#cb .stat{color:#f0d8a4}
@media(orientation:landscape) and (max-height:490px){#cb .sl .nmL{font-size:9px}}


/* 75% combat HUD: retain all combat controls and accessible taps while clearing sightlines. */
#cb .cx{width:min(308px,37vw)!important;height:min(233px,38vh)!important;right:max(10px,env(safe-area-inset-right))!important;bottom:max(14px,env(safe-area-inset-bottom))!important}
#cb .vit{transform:scale(.75);transform-origin:top left;left:max(9px,env(safe-area-inset-left))!important}
#cb .top{transform:scale(.75);transform-origin:top right;right:8px!important;top:max(55px,calc(env(safe-area-inset-top) + 48px))!important}
#cb .tp{transform:translateX(-50%) scale(.75);transform-origin:top center}
#cb .tp.boss{width:min(480px,95vw)}
#cb .cl{grid-template-columns:repeat(3,35px)!important;gap:4px!important;right:calc(max(10px,env(safe-area-inset-right)) + min(308px,37vw) + 7px)!important;bottom:max(15px,env(safe-area-inset-bottom))!important}
#cb .cl button{width:35px!important;height:35px!important;font-size:8px!important}
#cb .cl button .g{font-size:14px!important;line-height:16px!important}
#cb .sl .nmL{font-size:8px!important}
#cb .sl .k{font-size:8px!important}
#cb .ulp button{min-height:36px!important;padding:5px 9px!important;font-size:10px!important}
@media(orientation:portrait){
#cb .cx{width:48vw!important;height:36.75vw!important;bottom:max(15px,env(safe-area-inset-bottom))!important}
#cb .cl{grid-template-columns:repeat(2,35px)!important;right:max(8px,env(safe-area-inset-right))!important;bottom:calc(max(15px,env(safe-area-inset-bottom)) + 36.75vw + 20px)!important}
#cb .vit{transform:scale(.75);width:min(274px,59vw)}
}
@media(orientation:landscape) and (max-height:490px){
#cb .cx{width:min(29.25vw,52.5vh)!important;height:45.75vh!important}
#cb .cl{right:calc(max(10px,env(safe-area-inset-right)) + min(29.25vw,52.5vh) + 7px)!important}
}


/* Varnethryl forge: the same antique gold, obsidian, and violet gemstones
   used by the supplied chest/lantern/reference HUD concept. */
#cb{--crystal:#af4bfe;--antique:#d8b675;--darkwood:#221727;--ember:#d896ec;color:#f7e7c8}
#cb .vit{
 background:linear-gradient(145deg,#33203cfa,#090d1bfa 55%,#2a152ef6)!important;
 border:3px ridge #caa66b!important;
 border-radius:11px!important;
 box-shadow:inset 0 0 0 2px #824aa333,inset 0 0 17px #76489b6a,0 5px 16px #000b!important
}
#cb .vit:after{content:'✦ VARNETHRYL ✦';color:#f4d695;border:1px solid #b78b64;background:linear-gradient(#3c2546,#101321);text-shadow:0 0 7px #a04cde;box-shadow:0 0 8px #aa67de61}
#cb .por{
 border:3px ridge #e0bc7a!important;
 background:radial-gradient(circle at 45% 35%,#834abc,#33174f 65%,#161221)!important;
 box-shadow:inset 0 0 6px #a854f0,0 0 10px #8d39bf99!important
}
#cb .bar,#cb .tp .bar{border:1px ridge #e0b16e!important;border-radius:12px!important;background:#0f0b19!important;box-shadow:inset 0 0 6px #000}
#cb .vit .hp i{background:linear-gradient(90deg,#631124,#c72a39,#ff677b)!important}
#cb .vit .mp i{background:linear-gradient(90deg,#22266b,#6a50c9,#8cadf5)!important}
#cb .vit .sp i{background:linear-gradient(90deg,#54267f,#a037e0,#ec9cff)!important}
#cb .vit .fy i{background:linear-gradient(90deg,#654024,#c28a36,#f8d08a)!important}
#cb .tp{background:linear-gradient(145deg,#342043f6,#0a1020f8 52%,#3d2345f6)!important;border:3px ridge #d2aa6b!important;border-radius:12px!important;box-shadow:inset 0 0 0 2px #b754e635,0 2px 12px #000b,0 0 12px #8f3bd15c!important}
#cb .tp:before,#cb .tp:after{content:'◆';position:absolute;top:50%;font-size:16px;line-height:0;color:#c484ff;text-shadow:0 0 5px #db75ff,0 0 8px #b56ae9}
#cb .tp:before{left:-10px}#cb .tp:after{right:-10px}
#cb .tp.boss .nm{color:#f7d89d!important;font:700 16px VarnCinzel,Georgia,serif!important;letter-spacing:.07em;text-shadow:0 1px 6px #ab4df2a4!important}
#cb .tp .hp i{background:linear-gradient(90deg,#5c2681,#9c3dda,#ed9aff)!important}
#cb .tp .bar{border:2px ridge #c8a064!important;border-radius:10px!important}
#cb .sl{border:3px ridge #d7ad71!important;background:radial-gradient(circle at 38% 31%,#503067,#21152f 65%,#0f1220)!important;box-shadow:inset 0 0 0 2px #9c52c945,0 3px 10px #0009,0 0 7px #a242e855!important}
#cb .sl.rdy{box-shadow:inset 0 0 0 2px #d5ad744d,0 0 12px #ca79f2b9!important}
#cb .sl.b0{border:4px ridge #e5b974!important;background:radial-gradient(circle at 40% 32%,#70358e,#291a46 58%,#121226)!important}
#cb .sl.b4{border:4px ridge #f4c783!important;background:radial-gradient(circle at 42% 32%,#b04ae3,#4f2377 55%,#171223)!important}
#cb .sl .ic{color:#e8b6ff!important;filter:drop-shadow(0 0 5px #bb5bf2)!important}
#cb .sl .nmL,#cb .sl .k{color:#f7deb8!important;font-family:VarnCinzel,Georgia,serif!important;text-shadow:0 1px 4px #000,0 0 3px #7c39ba}
#cb .cl button,#cb .top button{border:2px ridge #c8a46a!important;background:linear-gradient(145deg,#362142,#10172a)!important;color:#e9cfab!important;box-shadow:inset 0 0 6px #8133b34d!important}
#cb .cl button.on{background:linear-gradient(130deg,#7941a0,#321f48)!important;color:#fff5e5!important}
#cb .msg{color:#fbe1ae!important;text-shadow:0 0 8px #a35ce1,0 2px 5px #000!important}
#cb .ulp button{border:2px ridge #d5ac76!important;color:#f8e3b8!important;background:linear-gradient(#432955,#130f22)!important}
#cb .stat{color:#dbc6a9}

/* True combat EXP: decorative amethyst frame, persistent left-to-right fill.
   Keep metal endcaps fixed; only the inner track scales. No blue background. */
#cb .vn-exp{position:absolute;left:50%;bottom:max(7px,env(safe-area-inset-bottom));transform:translateX(-50%);width:min(500px,40vw);height:61px;pointer-events:none;color:#fbecc8;text-shadow:0 1px 4px #000,0 0 4px #2a132e;font:700 11px VarnCinzel,Georgia,serif;z-index:4;filter:drop-shadow(0 3px 7px #000c)}
#cb .vn-exp .vn-exp-track{position:absolute;left:10.5%;right:10.5%;top:43%;height:22%;background:linear-gradient(#13091c,#35103f 50%,#0d0818);border:1px solid #8e5b40;overflow:hidden}
#cb .vn-exp .vn-exp-fill{position:absolute;inset:0;transform-origin:left center;transform:scaleX(0);background:linear-gradient(180deg,#ffe0ff 0%,#de86ff 14%,#9a31e6 45%,#6424ab 77%,#410f7e);box-shadow:inset 0 2px 5px #fff5,0 0 12px #ba58fb;will-change:transform;transition:transform .55s cubic-bezier(.2,.7,.2,1)}
#cb .vn-exp .vn-exp-fill:after{content:'';position:absolute;inset:0;background:repeating-linear-gradient(105deg,transparent 0 23px,#ffdbff26 24px 27px,transparent 28px 40px)}
#cb .vn-exp .vn-exp-art{position:absolute;inset:0;width:100%;height:100%;background:url('assets/hud/exp-frame.svg') center/100% 100% no-repeat;z-index:2}
#cb .vn-exp .vn-exp-level,#cb .vn-exp .vn-exp-value{position:absolute;z-index:3;left:50%;transform:translateX(-50%);white-space:nowrap;font-variant-numeric:tabular-nums}
#cb .vn-exp .vn-exp-level{top:0;font-size:10px;letter-spacing:.11em;color:#ffdfa6}
#cb .vn-exp .vn-exp-value{bottom:0;font-size:10px;letter-spacing:.02em;color:#f7dcff}
#cb .vn-exp.vn-level-up .vn-exp-art{filter:drop-shadow(0 0 8px #df8dff)}
@media(orientation:portrait){#cb .vn-exp{width:min(350px,86vw);bottom:calc(max(5px,env(safe-area-inset-bottom)) + 145px);height:52px;filter:drop-shadow(0 2px 5px #000a)}#cb .vn-exp .vn-exp-level{font-size:9px}#cb .vn-exp .vn-exp-value{font-size:9px}}
@media(orientation:landscape) and (max-height:440px){#cb .vn-exp{height:43px;width:min(365px,43vw);bottom:max(3px,env(safe-area-inset-bottom))}#cb .vn-exp .vn-exp-level,#cb .vn-exp .vn-exp-value{font-size:9px}}
@media(prefers-reduced-motion:reduce){#cb .vn-exp .vn-exp-fill{transition:none!important}}

/* Gold-purple combat frame correction: nine-slice, fixed-size ornamentation.
   Preserves EXP bar markup, fill, position, progression and level-up animation.
   Do not put oversized crystal corner images behind the boss name or HP. */
#cb .tp,#cb .tp.boss{
  background:linear-gradient(145deg,#281631ef,#120d19ef)!important;
  border:9px solid transparent!important;
  border-image-source:url('assets/hud/label-long.svg')!important;
  border-image-slice:42 122!important;
  border-image-width:9px 13px!important;
  border-image-outset:0!important;
  border-image-repeat:stretch!important;
  border-radius:0!important;
  padding:3px 8px 5px!important;
  box-shadow:0 6px 19px #000b!important;
  max-width:calc(100vw - 22px);
}
#cb .tp:before,#cb .tp:after{content:none!important}
#cb .tp.boss{min-height:60px}
#cb .tp.boss .nm{color:#ffdfae!important;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#cb .vit{
  background:linear-gradient(140deg,#25172ff6,#140e1bf6)!important;
  border:10px solid transparent!important;
  border-image-source:url('assets/hud/panel-wide.svg')!important;
  border-image-slice:92!important;
  border-image-width:10px!important;
  border-image-outset:0!important;
  border-image-repeat:stretch!important;
  border-radius:0!important;
  padding:6px 9px!important;
  overflow:visible;
}
#cb .vit:after{
  border:1px solid #99724d!important;
  background:linear-gradient(#3e234c,#1a1225)!important;
}
#cb .cl button,#cb .sl{background:radial-gradient(circle at 42% 29%,#553069,#281534 55%,#0d0a17)!important}
@media(orientation:portrait) and (max-width:440px){
  #cb .vit{max-width:calc(100vw - 16px);border-width:8px!important;border-image-width:8px!important;padding:5px 8px!important}
  #cb .tp,#cb .tp.boss{border-width:7px!important;border-image-width:7px 10px!important}
}
@media(orientation:landscape) and (max-height:490px){
  #cb .vit{border-width:7px!important;border-image-width:7px!important;padding:4px 7px!important}
  #cb .tp,#cb .tp.boss{border-width:6px!important;border-image-width:6px 9px!important;padding:2px 7px 3px!important}
}

/* Varnethryl combat controls: one five-ability row with a compact anchored action strip.
   Basic Attack → 1 → 2 → 3 → Ultimate. No event handlers or combat logic changed. */
#cb .cx{
 display:flex!important;flex-flow:row nowrap;align-items:center;justify-content:space-between;
 gap:clamp(5px,.7vw,9px);width:min(430px,52vw)!important;height:auto!important;
 aspect-ratio:auto!important;right:max(12px,env(safe-area-inset-right))!important;
 bottom:calc(max(9px,env(safe-area-inset-bottom)) + 51px)!important;
 padding:8px 9px 24px;border:1px solid #aa814b;border-radius:17px;
 background:linear-gradient(155deg,#191024e8,#110f1dcc 58%,#191426c9);
 box-shadow:inset 0 0 0 1px #804d9b66,0 6px 20px #000b;
 filter:drop-shadow(0 5px 10px #0009)
}
#cb .cx>.sl{
 position:relative!important;inset:auto!important;right:auto!important;bottom:auto!important;
 display:block;flex:1 1 0;width:auto!important;height:auto!important;min-width:0;
 aspect-ratio:1!important;margin:0!important;border-width:3px!important;transform-origin:center;
 -webkit-tap-highlight-color:transparent
}
#cb .cx>.sl.b0{flex-grow:1.26;border-width:4px!important}
#cb .cx>.sl.b4{flex-grow:1.18;border-width:4px!important}
#cb .cx>.sl .nmL,#cb .cx>.sl.b4 .nmL{
 left:50%;right:auto;top:auto;bottom:-17px;transform:translateX(-50%);
 max-width:calc(100% + 15px);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
 font-size:9px!important;line-height:13px;text-align:center;letter-spacing:0;text-transform:none
}
#cb .cx>.sl .k{font-size:9px!important;bottom:3%}
#cb .cl{
 position:absolute!important;left:auto!important;right:2px!important;
 bottom:calc(100% + 9px)!important;width:min(300px,100%)!important;
 display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;
 grid-auto-flow:row;gap:5px!important;z-index:3;pointer-events:none
}
#cb .cl button{
 pointer-events:auto;position:relative;min-width:0;width:100%!important;height:45px!important;
 min-height:40px;padding:5px 1px 3px!important;border-radius:10px!important;
 display:flex;flex-direction:column;align-items:center;justify-content:center;
 font:700 8px/1.05 VarnCinzel,Georgia,serif!important;text-transform:capitalize;
 -webkit-tap-highlight-color:transparent
}
#cb .cl button .g{font:400 19px/21px system-ui!important;flex:none}
#cb .cl button .q{display:none}
/* Potion count must remain visible; all keyboard prompts are hidden on the touch strip. */
#cb .cl button[data-a="potion"] .q{display:block;right:-3px;top:-6px;padding:2px 3px;
 color:#ffe8b3;background:#291437;border:1px solid #cba367;border-radius:7px;
 font:700 9px system-ui;line-height:1;z-index:2}
#cb .cl button .cdv{pointer-events:none}
#cb .ulp{right:0!important;bottom:calc(100% + 65px)!important;width:min(210px,70vw);gap:6px;z-index:6}
#cb .ulp button{width:100%;min-height:44px!important;padding:8px!important;
 font-size:11px!important;white-space:normal;line-height:1.3}
@media(orientation:portrait){
 #cb .cx{width:calc(100vw - 20px)!important;max-width:400px!important;
  right:max(10px,env(safe-area-inset-right))!important;
  bottom:calc(max(8px,env(safe-area-inset-bottom)) + 188px)!important;
  gap:clamp(3px,1vw,7px);padding:7px 7px 22px}
 #cb .cx>.sl .nmL,#cb .cx>.sl.b4 .nmL{font-size:8px!important;bottom:-15px}
 #cb .cl{width:min(300px,92%)!important;bottom:calc(100% + 9px)!important;gap:4px!important}
 #cb .cl button{height:43px!important;font-size:8px!important}
 #cb .vn-exp{bottom:max(3px,env(safe-area-inset-bottom))!important;
  width:min(355px,92vw)!important;height:43px!important}
}
@media(orientation:landscape) and (max-height:490px){
 #cb .cx{width:min(380px,51vw)!important;height:auto!important;
  bottom:calc(max(4px,env(safe-area-inset-bottom)) + 47px)!important;
  gap:5px;padding:6px 7px 19px}
 #cb .cx>.sl .nmL,#cb .cx>.sl.b4 .nmL{font-size:8px!important;bottom:-13px}
 #cb .cl{width:min(288px,100%)!important;bottom:calc(100% + 7px)!important}
 #cb .cl button{height:41px!important;min-height:40px;font-size:7px!important}
 #cb .cl button .g{font-size:17px!important;line-height:18px!important}
}
@media(max-width:350px) and (orientation:portrait){
 #cb .cx{gap:3px;padding:6px 5px 22px}
 #cb .cx>.sl .nmL{font-size:7px!important;max-width:calc(100% + 8px)}
 #cb .cl button{font-size:7px!important}
}


/* 1.3.7 portrait HUD: compact right-hand gamepad. Keep the player's center view
   and the lower-left walk/run joystick unobstructed. Original ability art stays. */
@media (orientation:portrait){
 #cb .cx{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  grid-template-rows:repeat(2,auto)!important;
  justify-items:center!important;align-items:center!important;
  column-gap:5px!important;row-gap:21px!important;
  width:min(248px,46vw)!important;max-width:248px!important;height:auto!important;
  min-height:0!important;aspect-ratio:auto!important;
  right:max(7px,env(safe-area-inset-right))!important;
  bottom:calc(max(6px,env(safe-area-inset-bottom)) + 73px)!important;
  padding:7px 6px 20px!important;
  border-radius:14px!important;
 }
 #cb .cx>.sl{position:relative!important;display:block!important;
  width:clamp(44px,9vw,67px)!important;height:clamp(44px,9vw,67px)!important;
  min-width:0!important;max-width:100%!important;aspect-ratio:1!important;
  margin:0!important;flex:none!important}
 #cb .cx>.sl.b0{grid-column:1 / span 2!important;grid-row:2!important;
  width:clamp(54px,10.5vw,76px)!important;height:clamp(54px,10.5vw,76px)!important}
 #cb .cx>.sl.b1{grid-column:1!important;grid-row:1!important}
 #cb .cx>.sl.b2{grid-column:2!important;grid-row:1!important}
 #cb .cx>.sl.b3{grid-column:3!important;grid-row:1!important}
 #cb .cx>.sl.b4{grid-column:3!important;grid-row:2!important;
  width:clamp(54px,10.5vw,76px)!important;height:clamp(54px,10.5vw,76px)!important}
 #cb .cx>.sl .nmL,#cb .cx>.sl.b4 .nmL{
  bottom:-15px!important;top:auto!important;left:50%!important;right:auto!important;
  transform:translateX(-50%)!important;
  max-width:min(76px,18vw)!important;
  font-size:8px!important;line-height:12px!important;white-space:nowrap!important;
  text-overflow:ellipsis!important;overflow:hidden!important;letter-spacing:0!important
 }
 #cb .cl{right:0!important;left:auto!important;bottom:calc(100% + 6px)!important;
  width:100%!important;display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:4px!important}
 #cb .cl button{height:43px!important;min-height:41px!important;padding:3px 0!important;
  font-size:8px!important;line-height:1!important;border-radius:9px!important}
 #cb .cl button .g{font-size:18px!important;line-height:20px!important}
 #cb .ulp{right:0!important;bottom:calc(100% + 99px)!important;width:100%!important}
 #cb .ulp button{min-height:44px!important}
 /* The EXP frame remains unchanged; only its location/width are corrected so
    it no longer runs beneath the joystick or the WALK/JUMP buttons. */
 #cb .vn-exp{left:auto!important;right:max(8px,env(safe-area-inset-right))!important;
  transform:none!important;bottom:max(4px,env(safe-area-inset-bottom))!important;
  width:min(330px,55vw)!important;height:43px!important}
}
@media(orientation:landscape) and (max-height:490px){
 #cb .cx{width:min(400px,49vw)!important;bottom:calc(max(4px,env(safe-area-inset-bottom)) + 47px)!important}
 #cb .cx>.sl .nmL,#cb .cx>.sl.b4 .nmL{font-size:8px!important}
 #cb .cl{width:min(295px,100%)!important}
}


/* v1.4.0: quiet gameplay layout. Extra defensive/utility moves remain in
   CombatController and keyboard/gesture handlers; they are not a second action
   bar occupying the left-hand movement zone. */
#cb .cx>.cl, #cb .cl, body.vn-hud-editing #cb .cl{display:none!important;pointer-events:none!important}
#cb .vn-exp{
  top:max(7px,env(safe-area-inset-top))!important;bottom:auto!important;
  left:50%!important;right:auto!important;transform:translateX(-50%)!important;
  width:min(440px,56vw)!important;height:71px!important;
  max-height:none!important;z-index:70!important;
}
#cb .vn-exp .vn-exp-level{font-size:11px!important}
#cb .vn-exp .vn-exp-value{font-size:11px!important}
#cb .vit{
  top:calc(max(8px,env(safe-area-inset-top)) + 137px)!important;
  bottom:auto!important;
}
#cb .stat{top:calc(max(8px,env(safe-area-inset-top)) + 258px)!important}
#cb .cx{
  right:max(10px,env(safe-area-inset-right))!important;
  bottom:calc(max(8px,env(safe-area-inset-bottom)) + 10px)!important;
}
@media(orientation:portrait){
 #cb .vn-exp{
  top:max(4px,env(safe-area-inset-top))!important;bottom:auto!important;
  left:50%!important;right:auto!important;
  width:min(440px,56vw)!important;height:70px!important;
  transform:translateX(-50%)!important;
 }
 #cb .vit{top:calc(max(9px,env(safe-area-inset-top)) + 139px)!important}
 #cb .stat{top:calc(max(10px,env(safe-area-inset-top)) + 258px)!important}
 #cb .cx{bottom:calc(max(6px,env(safe-area-inset-bottom)) + 21px)!important}
}
@media(orientation:portrait) and (max-width:560px){
 #cb .vn-exp{left:8px!important;right:auto!important;
  transform:none!important;width:calc(100vw - 156px)!important;height:66px!important}
 #cb .vn-exp .vn-exp-level,#cb .vn-exp .vn-exp-value{font-size:9px!important}
}
@media(orientation:landscape) and (max-height:520px){
 #cb .vn-exp{top:max(3px,env(safe-area-inset-top))!important;height:45px!important;
  width:min(330px,40vw)!important}
 #cb .vit{top:calc(max(6px,env(safe-area-inset-top)) + 56px)!important}
 #cb .stat{top:calc(max(6px,env(safe-area-inset-top)) + 136px)!important}
 #cb .cx{bottom:calc(max(6px,env(safe-area-inset-bottom)) + 22px)!important}
}
/* 1.5.1: Keep owner commands completely below the interactive minimap.
   Both normal and expanded minimaps have separate responsive clearance. */
#cb .top{
 top:calc(max(90px,env(safe-area-inset-top) + 76px) + 160px)!important;
 right:max(9px,env(safe-area-inset-right))!important;
}
body:has(#vnMiniMap.expanded) #cb .top{
 top:calc(max(90px,env(safe-area-inset-top) + 76px) + 260px)!important;
}
/* Full skill names remain in aria-label/title. On narrow touch screens the
   five labels otherwise overlap each other; show one readable name on focus
   or contact instead of stacking five clipped words. */
#cb .skill-name-callout{display:none;position:absolute;right:0;bottom:calc(100% + 10px);
 max-width:min(220px,74vw);padding:5px 10px;border:2px ridge #d6b679;
 border-radius:9px;background:linear-gradient(155deg,#3d2652ee,#121625f5);
 color:#fbe9be;font:700 11px VarnCinzel,Georgia,serif;
 text-align:center;text-shadow:0 1px 3px #000;line-height:1.3;
 box-shadow:0 3px 14px #000a;pointer-events:none;white-space:normal;overflow-wrap:anywhere;
 z-index:8}
@media(orientation:portrait) and (max-width:560px){
 #cb .cx>.sl .nmL{display:none!important}
 #cb .skill-name-callout.show{display:block}
 #cb .top{top:calc(max(12px,env(safe-area-inset-top)) + 187px)!important}
 body:has(#vnMiniMap.expanded) #cb .top{
   top:calc(max(12px,env(safe-area-inset-top)) + 269px)!important
 }
}
@media(orientation:landscape) and (max-height:450px){
 #cb .top{top:calc(max(54px,env(safe-area-inset-top) + 48px) + 122px)!important}
 body:has(#vnMiniMap.expanded) #cb .top{
  top:calc(max(54px,env(safe-area-inset-top) + 48px) + 182px)!important
 }
}

`;
/* simple SVG icons (no emoji): 24x24 stroke paths */
const SV = p => '<svg viewBox="0 0 24 24" aria-hidden="true">' + p + '</svg>';
const ICONS = {
  basic: SV('<path d="M5 19L17 7M14 4l6 0 0 6M5 19l-1 1M7 15l2 2"/>'), slash: SV('<path d="M4 18C8 8 14 5 20 5M8 20C11 13 15 10 20 9"/>'), chains: SV('<ellipse cx="9" cy="9" rx="4" ry="2.6" transform="rotate(-35 9 9)"/><ellipse cx="15" cy="15" rx="4" ry="2.6" transform="rotate(-35 15 15)"/>'),
  bolt: SV('<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>'), meteor: SV('<circle cx="15" cy="15" r="5"/><path d="M11 11L3 3M9 15L3 12M15 9L12 3"/>'), lock: SV('<rect x="6" y="11" width="12" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>'),
  heavy: SV('<path d="M6 20L18 8M13 3l8 8-3 3-8-8z"/>'), push: SV('<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/>'), throw: SV('<path d="M4 20L16 8M14 4l6 0 0 6"/>'), shield: SV('<path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6z"/>'), storm: SV('<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 018 8"/>'),
};
const ownerIconKey = (key, a) => key === 0 ? 'basic' : (a.owner ? a.id : null);
Object.assign(ICONS, {
  ring: SV('<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/>'), dash: SV('<path d="M3 12h13M12 6l7 6-7 6M3 7h6M3 17h6"/>'), lion: SV('<path d="M5 19V9l3 3 4-6 4 6 3-3v10zM9 15h6"/>'),
  arrow: SV('<path d="M3 21L19 5M13 5h6v6M5 15l4 4"/>'), line: SV('<path d="M3 12h18M17 8l4 4-4 4M3 8v8"/>'), trap: SV('<path d="M4 18l4-8 4 5 4-9 4 12zM4 21h16"/>'), volley: SV('<path d="M4 20L12 4M10 20L18 4M16 20l4-8"/>'),
  flame: SV('<path d="M12 3c1 4 5 6 5 11a5 5 0 01-10 0c0-3 2-4 3-7 1 1 2 2 2-4z"/>'), wave: SV('<path d="M3 16c3-8 9-10 18-10-4 3-6 6-7 12M3 20c4-4 8-5 12-5"/>'), sun: SV('<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>'),
  heal: SV('<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>'), heal2: SV('<path d="M12 21C5 15 3 11 3 8a5 5 0 019-3 5 5 0 019 3c0 3-2 7-9 13z"/>'), dagger: SV('<path d="M5 19L15 9M13 5l6 0 0 6M3 13l3 3M8 18l3 3"/>'),
  blink: SV('<path d="M4 20L12 12M12 12l8-8M14 4h6v6M4 14v6h6"/>'), poison: SV('<path d="M12 3c4 5 6 8 6 11a6 6 0 01-12 0c0-3 2-6 6-11zM10 14h4"/>'),
});
const LEGACY_ICON = ['basic', 'heavy', 'push', 'throw', 'shield', 'storm'];
const NUM_POOL = 24, OH_POOL = 16;
export class CombatHUD {
  /* api: {use(i), dodge(), block(on), jump(), lock(), switchTarget(), potion(), swap(), exit(), summon()} - plain callbacks into the host.
     project(x,y,z,out) -> true if on screen (out[0],out[1] px). Heights are supplied by the host per entity (e.top). */
  constructor(cc, api, project) {
    this.cc = cc; this.api = api; this.project = project; this.cache = {}; this.nums = []; this.ohs = []; this.numI = 0; this.sc = [0, 0];
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    const r = this.root = document.createElement('div'); r.id = 'cb';
    r.innerHTML = '<div class="flash"></div><div class="tp"><div class="nm"></div><div class="sub"></div><div class="bar hp"><i></i><b></b></div></div>' +
      '<div class="stat"></div><div class="top"><button type="button" data-a="summon">Summon Titan</button><button type="button" data-a="exit">Exit fight</button></div>' +
      '<div class="vit"><div class="lab"></div><div class="por"><span>?</span><small>1</small></div><div class="bars"><div class="bar hp"><i></i><b></b></div><div class="bar mp"><i></i><b></b></div><div class="bar sp"><i></i><b></b></div><div class="bar fy"><i></i><b></b></div></div></div>' +
      '<div class="vn-exp" role="progressbar" aria-label="Experience to next level" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="vn-exp-track"><i class="vn-exp-fill"></i></div><i class="vn-exp-art" aria-hidden="true"></i><span class="vn-exp-level">LV 40</span><span class="vn-exp-value">0 / 0 XP</span></div>' +
      '<div class="cx"><div class="skill-name-callout" role="status" aria-live="polite"></div><div class="ulp"><button type="button" data-u="holy">Holy Destruction</button><button type="button" data-u="unholy">Unholy Destruction</button></div>' + [0, 1, 2, 3, 4].map(i => '<button type="button" class="sl b' + i + '" data-s="' + i + '"><span class="ic"></span><span class="k">' + (i ? (i === 4 ? 'ULT' : i) : '') + '</span><span class="rg"></span><span class="ct"></span><span class="nmL"></span></button>').join('') + '</div>' +
      '<div class="cl"><button type="button" data-a="dodge"><span class="g">\u21BA</span>Dodge<span class="q">Spc</span><span class="cdv"></span></button><button type="button" data-a="block"><span class="g">\u26E8</span>Block<span class="q">RMB</span></button>' +
      '<button type="button" data-a="jump"><span class="g">\u2191</span>Jump<span class="q">J</span></button><button type="button" data-a="lock"><span class="g">\u25CE</span>Lock<span class="q">Q</span></button>' +
      '<button type="button" data-a="potion"><span class="g">\u2697</span>Potion<span class="q">R</span><span class="cdv"></span></button><button type="button" data-a="swap"><span class="g">\u2694</span>Weapon<span class="q">E</span></button></div><div class="msg"></div>';
    document.body.appendChild(r);
    // Anchor all six movement/defense buttons to the same responsive pad.
    r.querySelector('.cx').appendChild(r.querySelector('.cl'));
    const $ = s => r.querySelector(s), $$ = s => Array.from(r.querySelectorAll(s));
    this.tp = $('.tp'); this.tpNm = $('.tp .nm'); this.tpSub = $('.tp .sub'); this.tpBar = $('.tp .bar i'); this.tpTxt = $('.tp .bar b');
    const vb = n => ({ i: $('.vit .' + n + ' i'), b: $('.vit .' + n + ' b') }); this.vhp = vb('hp'); this.vmp = vb('mp'); this.vsp = vb('sp'); this.vfy = vb('fy');
    this.exp = $('.vn-exp'); this.expFill = $('.vn-exp-fill'); this.expLevel = $('.vn-exp-level'); this.expValue = $('.vn-exp-value'); this.expKey = '';
    this.por = $('.por span'); this.lab = $('.vit .lab'); this.lvl = $('.por small'); this.stat = $('.stat'); this.msg = $('.msg'); this.flash = $('.flash'); this.sumBtn = $('[data-a=summon]');
    $$('.sl').forEach((b, i) => { b.setAttribute('aria-label', i === 0 ? 'Basic attack' : i === 4 ? 'Ultimate ability' : 'Skill ' + i); b.title = b.getAttribute('aria-label'); });
    this.slots = $$('.sl').map(b => ({ b, ic: b.querySelector('.ic'), rg: b.querySelector('.rg'), ct: b.querySelector('.ct'), nm: b.querySelector('.nmL'), cd: -1, st: '', key: '' }));
    const skillNameCallout = $('.skill-name-callout');
    const showSkillName = b => {
      if (!b || !skillNameCallout) return;
      skillNameCallout.textContent = b.getAttribute('aria-label') || b.title || '';
      skillNameCallout.classList.add('show');
      clearTimeout(this._skillLabelTimer);
      this._skillLabelTimer = setTimeout(() => skillNameCallout.classList.remove('show'), 1600);
    };
    r.addEventListener('focusin', e => showSkillName(e.target.closest?.('.sl')));
    r.addEventListener('pointerdown', e => showSkillName(e.target.closest?.('.sl')));
    this.btn = {}; $$('.cl button').forEach(b => { this.btn[b.dataset.a] = { b, cdv: b.querySelector('.cdv'), cd: -1 }; });
    for (let i = 0; i < NUM_POOL; i++) { const e = document.createElement('div'); e.className = 'fn'; r.appendChild(e); this.nums.push({ e, t: 9 }); }
    for (let i = 0; i < OH_POOL; i++) { const e = document.createElement('div'); e.className = 'oh'; e.innerHTML = '<i></i>'; r.appendChild(e); this.ohs.push({ e, f: e.firstChild, on: false, last: -1 }); }
    const stop = e => { e.preventDefault(); e.stopPropagation(); };
    r.addEventListener('pointerdown', e => {
      const b = e.target.closest('button'); if (!b) return; stop(e);
      if (b.dataset.u) { if (this.cc.ownerOk()) { this.cc.ultSel = b.dataset.u; try { localStorage.setItem('varn.ultsel', b.dataset.u); } catch (x) {} } r.querySelector('.ulp').classList.remove('open'); return; }
      if (b.dataset.s === '4' && this.cc.ownerOk()) {   // ONE ultimate button: tap = fire selected, long-press (0.45 s) = popup to switch Holy/Unholy
        const pop = r.querySelector('.ulp'); pop.classList.remove('open'); this.ultP = { id: e.pointerId, long: false, t: setTimeout(() => { if (this.ultP) { this.ultP.long = true; pop.classList.add('open'); } }, 450) }; return;
      }
      r.querySelector('.ulp').classList.remove('open');
      if (b.dataset.s !== undefined) { const k = this.slotAbility(+b.dataset.s); if (k !== null) api.use(k); } else { const a = b.dataset.a; if (a === 'block') { this.blockPtr = e.pointerId; api.block(true); } else api[a] && api[a](); }
    });
    const up = e => { if (this.ultP && this.ultP.id === e.pointerId) { const u = this.ultP; this.ultP = null; clearTimeout(u.t); if (!u.long && e.type === 'pointerup') { const k = this.slotAbility(4); if (k !== null) api.use(k); } } if (this.blockPtr === e.pointerId) { this.blockPtr = null; api.block(false); } };
    addEventListener('pointerup', up); addEventListener('pointercancel', up);
    addEventListener('blur', () => { if (this.ultP) { clearTimeout(this.ultP.t); this.ultP = null; } if (this.blockPtr !== undefined && this.blockPtr !== null) { this.blockPtr = null; api.block(false); } r.querySelector('.ulp')?.classList.remove('open'); });
    r.addEventListener('contextmenu', e => e.preventDefault());
    cc.on('damage', d => this.onDamage(d)).on('heal', h => this.floatAt(h.x, 2.4 * cc.HS, h.z, '+' + h.n, 'heal')).on('hero', () => this.heroInfo())
      .on('experience', p => this.expInfo(p))
      .on('denied', d => this.say(d.why, 900)).on('playerDown', () => this.say('You fell...', 2200)).on('reward', rw => this.say('+' + rw.xp + ' XP   +' + rw.gold + ' gold', 1300));
    this.heroInfo();
  }
  /* cluster slot (0 basic,1-3 skills,4 ult) -> ability key for the controller (index into ABILITIES, or an OWNER_SKILLS id). The controller re-validates everything. */
  slotAbility(i) { if (i === 0) return 0; if (this.cc.ownerOk()) return i === 4 ? (this.cc.ultSel || 'holy') : OWNER_CLUSTER[i - 1]; if (this.cc.kit) return this.cc.kit.skills[i - 1].id; return i === 4 ? 5 : i; }
  show(v) { this.root.style.display = v ? 'block' : 'none'; const d = document.getElementById('diagBtn'); if (d) { if (v) { this._dd = d.style.display; d.style.display = 'none'; } else if (this._dd !== undefined) d.style.display = this._dd; } }   /* #diagBtn sits under the first ability slot */
  heroInfo() { const h = this.cc.hero; this.por.textContent = (h.name || '?')[0]; if (this.lab) this.lab.textContent = (h.name || 'Hero') + ' \u00b7 LV ' + (h.level || 1) + ' \u00b7 ' + (this.cc.kit && this.cc.kit.role ? this.cc.kit.role : (h.className || 'Adventurer')); this.lvl.textContent = h.level; this.cache.k = ''; }
  expInfo(p) {
    if(!p||!this.exp)return;
    clearTimeout(this._expRollover);clearTimeout(this._expPulse);
    const level=Math.max(1,Math.floor(Number(p.level)||1));
    const max=Math.max(0,Math.floor(Number(p.needed)||0));
    const xp=Math.max(0,Math.min(max,Math.floor(Number(p.xp)||0)));
    const fraction=max?xp/max:1;
    const key=String(p.id||this.cc.hero.id||'hero');
    const first=this.expKey!==key || !this.expLast;
    const leveled=!first&&(Number(p.levels)>0||level>this.expLast.level);
    this.expKey=key;this.expLast={level,xp,max};
    this.expLevel.textContent='LEVEL '+level+(max?'':' · MAX');
    this.expValue.textContent=max?xp.toLocaleString()+' / '+max.toLocaleString()+' XP':'MAX LEVEL';
    this.exp.setAttribute('aria-valuemin','0');
    this.exp.setAttribute('aria-valuemax',String(max||1));
    this.exp.setAttribute('aria-valuenow',String(max?xp:1));
    this.exp.setAttribute('aria-valuetext',max?('Level '+level+', '+xp+' of '+max+' experience'):('Level '+level+', maximum level'));
    if(first){this.expFill.style.transition='none';this.expFill.style.transform='scaleX('+fraction+')';requestAnimationFrame(()=>{if(this.expFill)this.expFill.style.transition='';});return;}
    if(leveled){
      this.exp.classList.add('vn-level-up');
      this.expFill.style.transition='transform .4s ease-out';
      this.expFill.style.transform='scaleX(1)';
      this._expRollover=setTimeout(()=>{
        this.expFill.style.transition='none';
        this.expFill.style.transform='scaleX(0)';
        requestAnimationFrame(()=>{this.expFill.style.transition='';this.expFill.style.transform='scaleX('+fraction+')';});
        this._expPulse=setTimeout(()=>this.exp.classList.remove('vn-level-up'),1050);
      },430);
    }else{
      this.expFill.style.transition='';
      this.expFill.style.transform='scaleX('+fraction+')';
    }
  }
  say(t, ms) { this.msg.textContent = t; this.msg.style.display = 'block'; clearTimeout(this._mt); this._mt = setTimeout(() => { this.msg.style.display = 'none'; }, ms || 1500); }
  floatAt(x, y, z, txt, cls) {
    const n = this.nums[this.numI++ % NUM_POOL]; if (!this.project(x, y, z, this.sc)) return;
    n.e.className = 'fn ' + (cls || ''); n.e.textContent = txt; n.x = this.sc[0]; n.y = this.sc[1]; n.t = 0; n.e.style.display = 'block';
  }
  onDamage(d) {
    const e = d.e;
    if (d.toPlayer) { this.floatAt(this.cc.p.x, 2.8 * this.cc.HS, this.cc.p.z, '-' + d.dmg, 'pl'); this.flash.style.opacity = '1'; setTimeout(() => { this.flash.style.opacity = '0'; }, 110); }
    else this.floatAt(e.x, (e.top || 2.4 * this.cc.HS) , e.z, (d.crit ? 'CRIT ' : '') + d.dmg, d.crit ? 'crit' : '');
  }
  setv(c, key, v, fn) { if (this.cache[key] !== v) { this.cache[key] = v; fn(v); } }
  bar(o, key, cur, max) { const f = Math.round(Math.max(0, cur) / max * 200) / 200; this.setv(null, key + 'f', f, v => { o.i.style.transform = 'scaleX(' + v + ')'; }); const t = Math.ceil(cur); this.setv(null, key + 't', t, v => { o.b.textContent = v + ' / ' + max; }); }
  /* once per frame */
  update(dt, enemies) {
    const cc = this.cc, R = cc.res;
    this.bar(this.vhp, 'hp', R.hp, R.max.hp); this.bar(this.vmp, 'mp', R.mp, R.max.mp); this.bar(this.vsp, 'sp', R.sp, R.max.sp);
    // target panel
    const t = cc.shownTarget();
    if (t) {
      this.setv(null, 'tid', t.id + (t.def.boss ? 'b' : ''), () => { this.tp.className = 'tp' + (t.def.boss ? ' boss' : ''); this.tpNm.textContent = t.def.name; this.tpSub.textContent = 'Lv ' + t.def.level + ' \u2022 ' + t.def.cls + (cc.tgt.locked ? ' \u2022 LOCKED' : ''); this.tp.style.display = 'block'; });
      this.setv(null, 'tlk', cc.tgt.locked, () => { this.tpSub.textContent = 'Lv ' + t.def.level + ' \u2022 ' + t.def.cls + (cc.tgt.locked ? ' \u2022 LOCKED' : ''); });
      if (t.def.boss || t.def.patterns) { const st = (t.phase === 2 ? 'E' : '') + (t.state === 'telegraph' && t.pat ? t.pat.id : '');   // boss bar: ENRAGED tint (phase 2), current attack name while telegraphing, 50% marker
        this.setv(null, 'bph', st + t.id, () => { this.tp.classList.toggle('enr', t.phase === 2); this.tp.classList.toggle('tel', !!(t.state === 'telegraph' && t.pat)); this.tpSub.textContent = 'Lv ' + t.def.level + ' \u2022 ' + t.def.cls + (t.phase === 2 ? ' \u2022 ENRAGED' : '') + (t.state === 'telegraph' && t.pat ? ' \u2022 ' + t.pat.name.toUpperCase() : ''); }); }
      const f = Math.round(t.hp / t.max * 400) / 400; this.setv(null, 'tf' + t.id, f, v => { this.tpBar.style.transform = 'scaleX(' + v + ')'; }); this.setv(null, 'tt' + t.id, Math.ceil(t.hp), v => { this.tpTxt.textContent = v + ' / ' + t.max; });
    } else if (this.cache.tid) { this.cache.tid = 0; this.tp.style.display = 'none'; }
    // ability cluster (basic + 3 skills + ultimate); owner skills only while the controller says Owner-gated
    const own = cc.ownerOk(); this.setv(null, 'own', own, v => { this.root.classList.toggle('own', v); });
    for (let i = 0; i < 5; i++) {
      const s = this.slots[i], key = this.slotAbility(i), a = cc.skillDef(key);
      const kk = String(key) + (own ? 'o' : '') + (cc.kit ? 'k' : ''); if (kk !== s.key) { s.key = kk; s.ic.innerHTML = own && ownerIconKey(key, a) ? OWNER_ICON[ownerIconKey(key, a)] : (ICONS[a.kit || a.owner ? a.icon : LEGACY_ICON[key]] || ICONS.basic); s.b.style.borderColor = a.kit && cc.kit ? cc.kit.color : ''; s.b.style.color = a.kit && cc.kit ? cc.kit.color : ''; s.b.title = a.name; s.b.setAttribute('aria-label', a.name); s.nm.textContent = i === 0 ? 'Basic Attack' : a.name; s.cd = -1; }
      const left = cc.cd.left(a.id), use = cc.slotUsable(key), noRes = !R.can(a.cost), isUlt = a.fury, fr = isUlt && use && left <= 0 && !cc.furyReady();
      const q = Math.round(left * 10) / 10 + (fr ? Math.round(cc.fury) / 1000 : 0); if (q !== s.cd) { s.cd = q; const p = left > 0 ? Math.round(cc.cd.frac(a.id) * 100) : fr ? Math.round(cc.fury) : 0; s.rg.style.setProperty('--p', p + '%'); s.ct.textContent = left > 0.05 ? (left >= 10 ? Math.ceil(left) : left.toFixed(1)) : ''; }
      const lock = !use && i === 4, oi = own && ownerIconKey(key, a), st = (i === 4 && own ? 'u-' + key + ' ' : '') + (oi ? 'oi ' : '') + (use ? '' : 'off ') + (fr && left <= 0 ? 'fr ' : '') + (use && noRes && left <= 0 ? 'nores ' : '') + (isUlt && use && left <= 0 && !fr ? 'rdy' : ''); if (st !== s.st) { s.st = st; s.b.className = 'sl b' + i + ' ' + st; if (lock) s.ic.innerHTML = ICONS.lock; }
    }
    this.bar(this.vfy, 'fy', cc.fury, TUNING.ult.fury);
    for (const k of ['dodge', 'potion']) { const o = this.btn[k], l = Math.round(cc.cd.left(k) * 5) / 5; if (l !== o.cd) { o.cd = l; o.cdv.style.height = l > 0 ? Math.round(cc.cd.frac(k) * 100) + '%' : '0'; } }
    this.setv(null, 'lockon', cc.tgt.locked, v => { this.btn.lock.b.classList.toggle('on', v); });
    this.setv(null, 'blk', cc.blocking, v => { this.btn.block.b.classList.toggle('on', v); });
    this.setv(null, 'pot', cc.potions, v => { this.btn.potion.b.querySelector('.q').textContent = 'x' + v; });
    this.setv(null, 'stat', cc.kills + '|' + cc.xp + '|' + cc.gold + '|' + cc.hero.saber, () => { this.stat.innerHTML = 'Kills ' + cc.kills + ' &bull; XP ' + cc.xp + ' &bull; Gold ' + cc.gold + (cc.hero.saber ? '' : '<br>Pick the Owner for the lightsaber'); });
    // floating numbers (transform only)
    for (const n of this.nums) { if (n.t >= 9) continue; n.t += dt; if (n.t > 0.9) { n.t = 9; n.e.style.display = 'none'; continue; } n.e.style.transform = 'translate3d(' + (n.x - 20) + 'px,' + (n.y - 56 * n.t) + 'px,0)'; n.e.style.opacity = n.t < 0.5 ? 1 : (0.9 - n.t) / 0.4; }
    // overhead bars (nearest few, pooled)
    let k = 0;
    for (const e of enemies) {
      if (e.state === 'defeated' || k >= OH_POOL) continue;
      if (!this.project(e.x, e.top || 2.4 * cc.HS, e.z, this.sc)) continue;
      if (e.def.boss) continue;
      const o = this.ohs[k++]; if (!o.on) { o.on = true; o.e.style.display = 'block'; }
      o.e.style.transform = 'translate3d(' + (this.sc[0] - 27) + 'px,' + this.sc[1] + 'px,0)';
      const f = Math.round(e.hp / e.max * 50) / 50; if (f !== o.last) { o.last = f; o.f.style.transform = 'scaleX(' + f + ')'; }
      const lk = cc.tgt.target === e; if (lk !== o.lk) { o.lk = lk; o.e.classList.toggle('lock', lk); }
    }
    for (; k < OH_POOL; k++) { const o = this.ohs[k]; if (o.on) { o.on = false; o.e.style.display = 'none'; } }
  }
}

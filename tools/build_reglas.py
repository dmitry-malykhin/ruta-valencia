# -*- coding: utf-8 -*-
"""reglas.html — отработка окончаний правильных глаголов: -ar, -er, -ir.

Четыре шага на группу: таблица со звуком, ввод по порядку, ввод вразброс, на слух.
Лица él/ella/usted и ellos/ustedes всегда показываются одной строкой:
у них одно окончание, и это надо запомнить визуально.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBS = json.load(open(os.path.join(ROOT, "data", "verbs.json"), encoding="utf-8"))

REGULAR = [v for v in VERBS if v.get("day") and not v["irr"]]
GROUPS = [
    {"id": "ar", "name": "-ar", "ends": ["o", "as", "a", "amos", "áis", "an"],
     "why": "Самая большая группа: hablar, trabajar, comprar. Окончания -o, -as, -a, -amos, -áis, -an."},
    {"id": "er", "name": "-er", "ends": ["o", "es", "e", "emos", "éis", "en"],
     "why": "Вторая группа: comer, beber, leer. Отличие от -ir только в мы и вы: -emos, -éis."},
    {"id": "ir", "name": "-ir", "ends": ["o", "es", "e", "imos", "ís", "en"],
     "why": "Третья группа: vivir, escribir, abrir. Совпадает с -er везде, кроме мы и вы: -imos, -ís."},
]
for g in GROUPS:
    g["verbs"] = [{"v": v["v"], "ru": v["ru"], "f": v["f"]}
                  for v in REGULAR if v["v"].endswith(g["id"])]

CSS = open(os.path.join(ROOT, "verbos.html"), encoding="utf-8").read().split("<style>")[1].split("</style>")[0]
CSS += """
.grp{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 12px}
.grp button{background:var(--surface-2);border:1px solid var(--line);color:var(--ink-soft);
border-radius:999px;padding:7px 16px;font-size:15px;cursor:pointer;font-family:"IBM Plex Mono",monospace}
.grp button.on{background:var(--cobalt);border-color:transparent;color:#fff;font-weight:600}
.grp button.done{border-color:var(--verde);color:var(--verde)}
.endrow{display:grid;grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(3,auto);
grid-auto-flow:column;gap:10px 16px;margin-top:14px}
@media(max-width:640px){.endrow{grid-template-columns:1fr;grid-auto-flow:row}}
.endcell{display:flex;align-items:center;gap:10px;background:var(--surface-2);
border:1px solid var(--line);border-radius:11px;padding:10px 12px;flex-wrap:wrap}
.endcell .who2{flex:1 1 150px;font-size:13px;color:var(--ink-soft);min-width:0}
.endcell .who2 b{display:block;color:var(--ink);font-size:14.5px;font-weight:600}
.endcell .form2{font-size:19px;font-weight:600;flex:1 1 120px;min-width:0}
.endcell .form2 u{text-decoration:none;color:var(--naranja);font-weight:700}
.endcell input{flex:1 1 120px;min-width:0;background:var(--surface);border:1px solid var(--line);
border-radius:10px;padding:10px 12px;font-size:16.5px;color:var(--ink)}
.endcell.ok{border-color:var(--verde)}
.endcell.ok input{background:var(--verde-soft);border-color:transparent;color:var(--verde);font-weight:600}
.endcell.bad{border-color:var(--naranja)}
.stem{font-size:clamp(24px,5vw,36px);font-weight:700;text-align:center;margin-bottom:4px}
.stem u{text-decoration:none;color:var(--naranja)}
.endcell .hintbtn{width:34px;height:34px;font-weight:700;flex:0 0 auto}
.endcell .mini{flex:0 0 auto}
"""

JS = r"""
var GROUPS=__GROUPS__;
var WHO=[{id:"dmitry",name:"Дмитрий"},{id:"yulia",name:"Юлия"},{id:"mihail",name:"Михаил"}];
var P=[["yo","я"],["tú","ты"],["él / ella / usted","он, она, Вы"],
       ["nosotros","мы"],["vosotros","вы"],["ellos / ustedes","они, Вы мн."]];
var MODES=[{k:"table",t:"1. Таблица окончаний"},{k:"order",t:"2. По порядку"},
           {k:"mix",t:"3. Вразброс"},{k:"oido",t:"4. На слух"}];
var ROUND=6;
var S={who:"dmitry",g:0,mode:0,queue:[],idx:0,ok:0,wrong:0,vi:0};

function el(i){return document.getElementById(i)}
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}}
function sh(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t}return a}
function norm(s){return (s||"").toLowerCase().trim().replace(/[.,!?¡¿]/g,"")
  .normalize("NFD").replace(/[̀-ͯ]/g,"").replace(/\s+/g," ")}
function mkey(gi,mi){return "reg_"+S.who+"_"+GROUPS[gi].id+"_"+MODES[mi].k}
function modeDone(gi,mi){return ls(mkey(gi,mi))==="1"}
function markMode(){ls(mkey(S.g,S.mode),"1")}
function groupDone(gi){return MODES.every(function(m,mi){return modeDone(gi,mi)})}
function group(){return GROUPS[S.g]}
function stem(v){return v.slice(0,-2)}

/* ---------- голос ---------- */
var VOICES=[], esVoice=null;
function vrank(v){var n=(v.name||"").toLowerCase(),l=(v.lang||"").toLowerCase(),r=0;
  if(l.indexOf("es-es")===0)r+=100; if(/premium|enhanced|natural/.test(n))r+=40;
  if(/m[oó]nica|marisol|paulina/.test(n))r+=20; if(/compact|eloquence/.test(n))r-=30; return r}
function collectVoices(){
  var v=[];try{v=speechSynthesis.getVoices()||[]}catch(e){}
  VOICES=v.filter(function(x){return /^es[-_]?/i.test(x.lang||"")}).sort(function(a,b){return vrank(b)-vrank(a)});
  var saved=ls("esp_voice");
  esVoice=VOICES.filter(function(x){return x.name===saved})[0]||VOICES[0]||null;
  var sel=el("voice"); if(!sel) return;
  sel.innerHTML=VOICES.length?VOICES.map(function(x){
    return '<option value="'+x.name.replace(/"/g,"")+'"'+(esVoice&&x.name===esVoice.name?" selected":"")+'>'+
      x.name+'</option>'}).join(""):'<option>голосов нет</option>';
}
function speakAt(t,rate){try{if(!esVoice)collectVoices();
  var u=new SpeechSynthesisUtterance(t);u.lang=(esVoice&&esVoice.lang)||"es-ES";u.rate=rate||.85;
  if(esVoice)u.voice=esVoice;speechSynthesis.cancel();speechSynthesis.speak(u)}catch(e){}}
function speak(t){speakAt(t,.85)}

/* ---------- каркас ---------- */
function renderWho(){el("who").innerHTML=WHO.map(function(w){
  return '<button data-who="'+w.id+'"'+(w.id===S.who?' class="on"':'')+'>'+w.name+'</button>'}).join("")}
function renderGroups(){
  el("groups").innerHTML=GROUPS.map(function(g,i){
    return '<button data-g="'+i+'" class="'+(i===S.g?"on ":"")+(groupDone(i)?"done":"")+'">'+
      g.name+(groupDone(i)?" ✓":"")+'</button>'}).join("");
}
function renderModes(){
  el("modes").innerHTML=MODES.map(function(m,i){
    return '<div class="md'+(i===S.mode?" on":"")+(modeDone(S.g,i)?" done":"")+'" data-mode="'+i+'">'+
      m.t+(modeDone(S.g,i)?" ✓":"")+'</div>'}).join("");
}
function head(){
  return '<div class="counter"><span class="pill learn">Ошибок: '+S.wrong+'</span>'+
    '<span class="mono">Осталось: '+Math.max(0,S.queue.length-S.idx)+'</span>'+
    '<span class="pill know">Верно: '+S.ok+'</span></div>';
}
function endingsLine(){
  var g=group();
  return g.ends.map(function(e,i){return P[i][0]+' → <b>-'+e+'</b>'}).join(' · ');
}
function startMode(){
  renderGroups(); renderModes();
  el("why").innerHTML='<b>Группа '+group().name+'</b><br>'+group().why;
  S.idx=0; S.ok=0; S.wrong=0; S.vi=0;
  var k=MODES[S.mode].k, pool=group().verbs;
  if(k==="table"){ S.queue=sh(pool).slice(0,3); return rTable() }
  if(k==="order"){ S.queue=sh(pool).slice(0,3); return rOrder() }
  if(k==="mix"){
    var q=[];
    sh(pool).slice(0,ROUND).forEach(function(v){ q.push({v:v,p:Math.floor(Math.random()*6)}) });
    S.queue=q; return rMix();
  }
  var q2=[];
  sh(pool).slice(0,ROUND).forEach(function(v){ q2.push({v:v,p:Math.floor(Math.random()*6)}) });
  S.queue=q2; return rOido();
}
function modeDoneScreen(){
  markMode(); renderGroups(); renderModes();
  var last=S.mode>=MODES.length-1;
  el("stage").innerHTML='<div class="panel done"><div class="big">✓</div>'+
    '<h2>'+MODES[S.mode].t+' пройден</h2>'+
    '<p class="hint" style="margin:8px 0 16px">Верно '+S.ok+', ошибок '+S.wrong+'</p>'+
    (last?'<button class="btn" id="nextg">Следующая группа</button> '
         :'<button class="btn" id="go">Дальше</button> ')+
    '<button class="btn ghost" id="re">Ещё раз</button></div>';
  if(el("go")) el("go").onclick=function(){S.mode++;startMode()};
  if(el("nextg")) el("nextg").onclick=function(){
    S.g=(S.g+1)%GROUPS.length; S.mode=0; startMode()};
  el("re").onclick=startMode;
}

/* ---------- 1. таблица окончаний ---------- */
function rTable(){
  if(S.vi>=S.queue.length) return modeDoneScreen();
  var v=S.queue[S.vi], g=group(), st=stem(v.v);
  var rows=P.map(function(p,i){
    return '<div class="endcell"><div class="who2"><b>'+p[0]+'</b>'+p[1]+'</div>'+
      '<div class="form2">'+st+'<u>'+g.ends[i]+'</u></div>'+
      '<button class="mini" data-say="'+v.f[i]+'">🔊</button></div>'}).join("");
  el("stage").innerHTML=head()+
    '<div class="card"><div class="stem">'+st+'<u>'+g.id+'</u></div>'+
    '<div class="ru">'+v.ru+'</div>'+
    '<button class="audio" id="spk">🔊</button>'+
    '<div class="endrow">'+rows+'</div></div>'+
    '<div class="acts"><button class="btn ghost" id="all">🔊 Все формы</button>'+
    '<button class="btn" id="next">Запомнил, дальше</button></div>'+
    '<p class="tip">Оранжевым выделено окончание · 🔊 у каждой строки читает свою форму</p>';
  el("spk").onclick=function(){speak(v.v)};
  el("all").onclick=function(){speak(v.f.join(", "))};
  el("stage").querySelector(".endrow").onclick=function(e){
    var b=e.target.closest("[data-say]"); if(!b) return; speak(b.dataset.say);
  };
  el("next").onclick=function(){S.vi++;S.ok++;rTable()};
  setTimeout(function(){speak(v.v)},300);
}

/* ---------- 2. по порядку ---------- */
function rOrder(){
  if(S.vi>=S.queue.length) return modeDoneScreen();
  var v=S.queue[S.vi], g=group(), st=stem(v.v), solved={}, left=6;
  var rows=P.map(function(p,i){
    return '<div class="endcell" data-i="'+i+'"><div class="who2"><b>'+p[0]+'</b>'+p[1]+'</div>'+
      '<input data-i="'+i+'" autocomplete="off" autocapitalize="off" spellcheck="false" '+
      'placeholder="'+st+'…">'+
      '<button class="mini hintbtn" data-hint="'+i+'" title="подсказать окончание для '+p[0]+'">?</button>'+
      '<button class="mini" data-play="'+i+'" disabled>🔊</button></div>'}).join("");
  el("stage").innerHTML=head()+
    '<div class="panel"><div class="stem">'+st+'<u>'+g.id+'</u></div>'+
    '<p class="hint" style="text-align:center;margin-bottom:6px">'+v.ru+'</p>'+
    '<div class="endrow">'+rows+'</div>'+
    '<div class="acts" style="margin-top:12px">'+
    '<button class="btn ghost" id="hint">Показать окончания</button>'+
    '<button class="btn" id="done" disabled>Дальше</button></div>'+
    '<p class="tip">Сверху вниз: '+endingsLine()+'</p></div>';
  var inputs=el("stage").querySelectorAll(".endrow input");
  function check(i){
    if(solved[i]) return;
    var inp=inputs[i], cell=inp.parentNode;
    if(norm(inp.value)===norm(v.f[i])){
      solved[i]=true; S.ok++; left--;
      cell.classList.remove("bad"); cell.classList.add("ok");
      inp.value=v.f[i]; inp.readOnly=true;
      var b=el("stage").querySelector('[data-play="'+i+'"]');
      b.disabled=false; b.onclick=function(){speak(v.f[i])};
      var h=el("stage").querySelector('[data-hint="'+i+'"]'); if(h) h.disabled=true;
      speak(v.f[i]);
      if(!left){ el("done").disabled=false; el("done").focus() }
      else { for(var j=0;j<6;j++) if(!solved[j]){inputs[j].focus();break} }
    } else if(inp.value.trim()){
      S.wrong++; cell.classList.add("bad");
      setTimeout(function(){cell.classList.remove("bad")},900);
    }
  }
  Array.prototype.forEach.call(inputs,function(inp,i){
    inp.onkeydown=function(e){ if(e.key==="Enter"){e.preventDefault();check(i)} };
    inp.onblur=function(){ if(inp.value.trim()) check(i) };
  });
  el("stage").querySelector(".endrow").onclick=function(e){
    var b=e.target.closest(".hintbtn"); if(!b) return;
    var i=+b.dataset.hint;
    if(solved[i]) return;
    S.wrong++;
    var inp=inputs[i];
    inp.placeholder=st+"-"+g.ends[i];
    inp.focus();
    el("stage").querySelector(".tip").innerHTML=
      'Окончание для <b>'+P[i][0]+'</b> — <b>-'+g.ends[i]+'</b>. Слово наберите целиком.';
  };
  el("hint").onclick=function(){
    el("stage").querySelector(".tip").innerHTML='<b>'+endingsLine()+'</b>';
  };
  el("done").onclick=function(){S.vi++;rOrder()};
  inputs[0].focus();
}

/* ---------- 3. вразброс ---------- */
function rMix(){
  if(S.idx>=S.queue.length) return modeDoneScreen();
  var q=S.queue[S.idx], v=q.v, st=stem(v.v), ans=v.f[q.p];
  el("stage").innerHTML=head()+
    '<div class="card"><div class="stem">'+st+'<u>'+group().id+'</u></div>'+
    '<div class="ru">'+v.ru+'</div>'+
    '<div class="taskline">Форма для <b>'+P[q.p][0]+'</b> · '+P[q.p][1]+'</div></div>'+
    '<div class="type"><input id="inp" autocomplete="off" autocapitalize="off" spellcheck="false" '+
    'placeholder="слово целиком"><button class="btn" id="ok">Проверить</button></div><div id="v"></div>'+
    '<div class="acts" style="margin-top:8px">'+
    '<button class="btn ghost" id="hintend">? Подсказать окончание</button></div>'+
    '<p class="tip">Пишите глагол целиком, не только окончание</p>';
  var inp=el("inp"); inp.focus(); var locked=false, retype=false;
  el("hintend").onclick=function(){
    if(locked) return;
    S.wrong++;
    el("v").innerHTML='<div class="verdict bad">окончание для <b>'+P[q.p][0]+'</b> — <b>-'+
      group().ends[q.p]+'</b></div>';
    inp.placeholder=st+"-"+group().ends[q.p]; inp.focus();
  };
  function check(){
    if(locked) return; var a=norm(inp.value); if(!a) return;
    if(retype){
      if(a!==norm(ans)){el("v").innerHTML='<div class="verdict bad">наберите <b>'+ans+'</b></div>';return}
      locked=true; speak(ans); S.idx++; setTimeout(rMix,800); return;
    }
    if(a===norm(ans)){
      locked=true; S.ok++; S.idx++;
      el("v").innerHTML='<div class="verdict ok"><b>'+ans+'</b> — '+P[q.p][0]+'</div>';
      speak(ans); setTimeout(rMix,1000); return;
    }
    S.wrong++; retype=true; S.queue.push(q);
    el("v").innerHTML='<div class="verdict bad"><b>'+ans+'</b> · наберите сами</div>';
    speak(ans); inp.value=""; inp.placeholder="наберите: "+ans; inp.focus();
  }
  el("ok").onclick=check; inp.onkeydown=function(e){if(e.key==="Enter")check()};
}

/* ---------- 4. на слух ---------- */
function rOido(){
  if(S.idx>=S.queue.length) return modeDoneScreen();
  var q=S.queue[S.idx], v=q.v, ans=v.f[q.p];
  el("stage").innerHTML=head()+
    '<div class="card"><div class="hint">послушайте форму и напишите её</div>'+
    '<button class="audio" id="spk">🔊</button>'+
    '<div class="taskline">глагол <b>'+v.v+'</b> · '+v.ru+'</div>'+
    '<div id="heard" class="frase-ru" style="min-height:20px"></div></div>'+
    '<div class="type"><input id="inp" autocomplete="off" autocapitalize="off" spellcheck="false" '+
    'placeholder="что услышали"><button class="btn" id="ok">Проверить</button></div><div id="v"></div>'+
    '<div class="acts" style="margin-top:8px">'+
    '<button class="btn ghost" id="slow">🐢 Медленнее</button>'+
    '<button class="btn ghost" id="face">Подсказать лицо</button></div>'+
    '<p class="tip">Лицо не показано специально: узнаём его по окончанию</p>';
  el("spk").onclick=function(){speak(ans)};
  el("slow").onclick=function(){speakAt(ans,.55)};
  el("face").onclick=function(){
    S.wrong++;
    el("heard").innerHTML='подсказка: <b>'+P[q.p][0]+'</b>';
  };
  setTimeout(function(){speak(ans)},350);
  var inp=el("inp"); inp.focus(); var locked=false;
  function check(){
    if(locked) return; var a=norm(inp.value); if(!a) return; locked=true;
    var good=a===norm(ans);
    if(good){S.ok++} else {S.wrong++; S.queue.push(q)}
    el("v").innerHTML='<div class="verdict '+(good?"ok":"bad")+'"><b>'+ans+'</b> — '+
      P[q.p][0]+' · '+P[q.p][1]+'</div>';
    speak(ans); inp.disabled=true; el("ok").disabled=true;
    S.idx++; setTimeout(rOido, good?1000:2000);
  }
  el("ok").onclick=check; inp.onkeydown=function(e){if(e.key==="Enter")check()};
}

function boot(){
  var whoFromUrl=(location.search.match(/who=([a-z]+)/)||[])[1];
  if(whoFromUrl && WHO.some(function(p){return p.id===whoFromUrl})) ls("esp_who",whoFromUrl);
  S.who=ls("esp_who")||"dmitry";
  if(!WHO.filter(function(w){return w.id===S.who}).length) S.who="dmitry";
  renderWho();
  el("who").onclick=function(e){var b=e.target.closest("button[data-who]");if(!b)return;
    S.who=b.dataset.who;ls("esp_who",S.who);renderWho();startMode()};
  el("groups").onclick=function(e){var b=e.target.closest("button[data-g]");if(!b)return;
    S.g=+b.dataset.g;S.mode=0;startMode()};
  el("modes").onclick=function(e){var d=e.target.closest(".md");if(!d)return;
    S.mode=+d.dataset.mode;startMode()};
  el("voice").onchange=function(){
    var name=this.value, v=VOICES.filter(function(x){return x.name===name})[0];
    if(v){esVoice=v;ls("esp_voice",v.name);speak("hablo, hablas, habla")}};
  try{speechSynthesis.onvoiceschanged=collectVoices}catch(e){}
  collectVoices();
  for(var i=0;i<GROUPS.length;i++){ if(!groupDone(i)){S.g=i;break} }
  for(var m=0;m<MODES.length;m++){ if(!modeDone(S.g,m)){S.mode=m;break} }
  startMode();
}
boot();
"""

body = """<div class="wrap">
  <p class="eyebrow"><a href="./hoy.html" style="text-decoration:none">← Мой день</a> ·
     <a href="./trainer.html" style="text-decoration:none">слова</a> ·
     <a href="./verbos.html" style="text-decoration:none">спряжение</a> ·
     <a href="./temas.html" style="text-decoration:none">темы</a> ·
     <a href="./shadow.html" style="text-decoration:none">эхо</a> ·
     <a href="./numeros.html" style="text-decoration:none">числа</a> ·
     <span style="opacity:.55">окончания</span> ·
     <a href="./" style="text-decoration:none;opacity:.55">все ссылки</a></p>
  <h1>Отработка окончаний</h1>
  <p style="color:var(--ink-soft);margin-top:6px">Правильные глаголы спрягаются по правилу.
     Здесь оно доводится до автоматизма: таблица, ввод по порядку, вразброс и на слух.</p>
  <div class="who" id="who"></div>
  <div class="panel">
    <div class="grp" id="groups"></div>
    <div class="why" id="why">—</div>
    <div style="display:flex;gap:8px;align-items:center;padding-top:10px;border-top:1px dashed var(--line)">
      <span class="hint">Голос</span><select id="voice" style="flex:1;max-width:360px"></select>
    </div>
    <div class="modes" id="modes"></div>
  </div>
  <div id="stage"></div>
  <footer>Прогресс хранится в этом браузере, у каждого свой.</footer>
</div>"""

head_html = ('<link rel="icon" type="image/svg+xml" href="./favicon.svg">\n'
             '<link rel="apple-touch-icon" href="./favicon.svg">\n'
             '<meta name="theme-color" content="#C60B1E">\n'
             '<title>Окончания · Ruta Valencia</title>\n'
             '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
             'family=Bitter:wght@500;700&family=IBM+Plex+Mono:wght@500;600&'
             'family=IBM+Plex+Sans:wght@400;500;600&display=swap">\n')

out = head_html + "<style>" + CSS + "</style>\n" + body + "\n<script>" + \
      JS.replace("__GROUPS__", json.dumps(GROUPS, ensure_ascii=False)) + "</script>"
open(os.path.join(ROOT, "reglas.html"), "w", encoding="utf-8").write(out)
print("reglas.html:", len(out) // 1024, "КБ · глаголов по группам:",
      {g["id"]: len(g["verbs"]) for g in GROUPS})

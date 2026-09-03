/* Проверки страниц сайта. Запуск: node tools/tests/run.js */
const { JSDOM } = require("jsdom");
const fs = require("fs");
const path = require("path");

const SITE = path.join(__dirname, "..", "..");
let passed = 0;
const failed = [];

function ok(name, cond, extra) {
  if (cond) { passed++; return }
  failed.push(name + (extra ? "  → " + extra : ""));
}

function load(file, query, sharedStorage) {
  const html = fs.readFileSync(path.join(SITE, file), "utf8");
  return new JSDOM("<!doctype html><html><body>" + html + "</body></html>", {
    runScripts: "dangerously",
    pretendToBeVisual: true,
    url: "https://example.org/" + (query || ""),
    beforeParse(win) {
      const store = sharedStorage ? null : {};
      if (sharedStorage) {
        Object.defineProperty(win, "localStorage", { value: sharedStorage });
      } else {
        Object.defineProperty(win, "localStorage", { value: {
          getItem: k => (k in store ? store[k] : null),
          setItem: (k, v) => { store[k] = String(v) },
          removeItem: k => { delete store[k] },
          key: i => Object.keys(store)[i] || null,
          get length() { return Object.keys(store).length },
        } });
      }
      win.speechSynthesis = { getVoices: () => [], speak() {}, cancel() {}, speaking: false, pending: false };
      win.SpeechSynthesisUtterance = function (text) { this.text = text };
    },
  });
}
const wait = ms => new Promise(r => setTimeout(r, ms));
const click = (dom, sel) => {
  const el = dom.window.document.querySelector(sel);
  if (!el) return false;
  el.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  return true;
};
const type = (dom, sel, value) => {
  const el = dom.window.document.querySelector(sel);
  if (!el) return false;
  el.value = value;
  el.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  return true;
};

/* ---------------- окончания правильных глаголов ---------------- */
async function testReglas() {
  const dom = load("reglas.html");
  const doc = dom.window.document;
  await wait(120);
  const w = dom.window;

  ok("окончания: три группы", w.GROUPS.length === 3, w.GROUPS.map(g => g.name).join(" | "));
  const ENDS = {
    ar: "o,as,a,amos,áis,an",
    er: "o,es,e,emos,éis,en",
    ir: "o,es,e,imos,ís,en",
  };
  const wrongEnds = w.GROUPS.filter(g => g.ends.join(",") !== ENDS[g.id]);
  ok("окончания: таблицы совпадают с правилом", wrongEnds.length === 0,
     wrongEnds.map(g => g.id + ": " + g.ends.join(",")).join(" | "));

  ok("окончания: у каждой группы есть глаголы",
     w.GROUPS.every(g => g.verbs.length >= 5),
     w.GROUPS.map(g => g.id + ":" + g.verbs.length).join(" "));
  ok("окончания: в группе только её глаголы",
     w.GROUPS.every(g => g.verbs.every(v => v.v.endsWith(g.id))),
     "");
  ok("окончания: формы собраны по правилу",
     w.GROUPS.every(g => g.verbs.every(v =>
       v.f.join(",") === g.ends.map(e => v.v.slice(0, -2) + e).join(","))),
     w.GROUPS.flatMap(g => g.verbs.filter(v =>
       v.f.join(",") !== g.ends.map(e => v.v.slice(0, -2) + e).join(",")).map(v => v.v)).join(","));

  ok("окончания: четыре режима", w.MODES.length === 4, w.MODES.map(m => m.t).join(" | "));
  ok("окончания: лица показаны парами",
     w.P[2][0] === "él / ella / usted" && w.P[5][0] === "ellos / ustedes",
     w.P[2][0] + " | " + w.P[5][0]);

  // 1. таблица
  ok("таблица: шесть строк", doc.querySelectorAll(".endcell").length === 6,
     doc.querySelectorAll(".endcell").length + " строк");
  const css = fs.readFileSync(path.join(SITE, "reglas.html"), "utf8").split("<style>")[1];
  const endrow = (css.match(/\.endrow\{[^}]*\}/g) || [])[0] || "";
  ok("таблица: две колонки по три",
     /grid-template-columns:repeat\(2,1fr\)/.test(endrow) &&
     /grid-template-rows:repeat\(3,auto\)/.test(endrow) &&
     /grid-auto-flow:column/.test(endrow), endrow);
  ok("таблица: порядок в разметке yo, tú, él, nosotros, vosotros, ellos",
     [...doc.querySelectorAll(".endcell .who2 b")].map(x => x.textContent).join("|") ===
     w.P.map(p => p[0]).join("|"),
     [...doc.querySelectorAll(".endcell .who2 b")].map(x => x.textContent).join("|"));
  ok("таблица: на узком экране колонка одна",
     /@media\(max-width:640px\)\{\.endrow\{grid-template-columns:1fr/.test(css));
  ok("таблица: окончание выделено", doc.querySelectorAll(".form2 u").length === 6);
  ok("таблица: у каждой строки своя озвучка",
     doc.querySelectorAll(".endrow [data-say]").length === 6);
  ok("таблица: перевод показан", !!doc.querySelector(".ru") && doc.querySelector(".ru").textContent.length > 2,
     doc.querySelector(".ru") ? doc.querySelector(".ru").textContent : "нет перевода");
  const spoken = [];
  w.speechSynthesis.speak = u => spoken.push(String(u && u.text || ""));
  const verbNow = w.S.queue[w.S.vi];
  doc.querySelectorAll(".endrow [data-say]")[3]
     .dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  await wait(20);
  ok("таблица: звучит именно эта форма", spoken[spoken.length - 1] === verbNow.f[3],
     spoken.join(","));

  // 2. по порядку
  w.S.mode = 1; w.startMode(); await wait(40);
  const inputs = () => [...doc.querySelectorAll(".endrow input")];
  ok("по порядку: шесть полей", inputs().length === 6, inputs().length + " полей");
  ok("по порядку: подписи идут yo, tú, él…",
     [...doc.querySelectorAll(".who2 b")].map(x => x.textContent).join("|") ===
     w.P.map(p => p[0]).join("|"),
     [...doc.querySelectorAll(".who2 b")].map(x => x.textContent).join("|"));
  const v1 = w.S.queue[w.S.vi];
  inputs().forEach((inp, i) => {
    inp.value = v1.f[i];
    inp.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await wait(40);
  ok("по порядку: все шесть приняты", doc.querySelectorAll(".endcell.ok").length === 6,
     doc.querySelectorAll(".endcell.ok").length + " верных");
  ok("по порядку: «Дальше» открылась", !doc.getElementById("done").disabled);

  // подсказка окончания в шаге «по порядку»
  w.S.mode = 1; w.startMode(); await wait(40);
  const hints = [...doc.querySelectorAll(".endrow .hintbtn")];
  ok("подсказка: кнопка у каждой из шести строк", hints.length === 6, "кнопок " + hints.length);
  ok("подсказка: в title названо лицо",
     hints.every((b, i) => b.getAttribute("title").indexOf(w.P[i][0]) > -1),
     hints.map(b => b.getAttribute("title")).join(" | "));
  const g = w.GROUPS[w.S.g];
  const before = w.S.wrong;
  hints[4].dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  await wait(20);
  ok("подсказка: показывает окончание нужной строки",
     doc.querySelector(".tip").textContent.indexOf("-" + g.ends[4]) > -1 &&
     doc.querySelector(".tip").textContent.indexOf(w.P[4][0]) > -1,
     doc.querySelector(".tip").textContent);
  ok("подсказка: слово всё равно набирать самому",
     [...doc.querySelectorAll(".endrow input")][4].value === "",
     [...doc.querySelectorAll(".endrow input")][4].value);
  ok("подсказка: засчитана как ошибка", w.S.wrong === before + 1, "ошибок " + w.S.wrong);
  const v2 = w.S.queue[w.S.vi];
  const inp4 = [...doc.querySelectorAll(".endrow input")][4];
  inp4.value = v2.f[4];
  inp4.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await wait(30);
  ok("подсказка: у решённой строки кнопка гаснет",
     doc.querySelector('[data-hint="4"]').disabled);

  // 3. вразброс
  w.S.mode = 2; w.startMode(); await wait(40);
  ok("вразброс: спрашивается случайное лицо",
     w.S.queue.length === 6 && !!doc.getElementById("inp"),
     "вопросов " + w.S.queue.length);
  const q = w.S.queue[w.S.idx];
  type(dom, "#inp", q.v.f[q.p]);
  await wait(40);
  ok("вразброс: верная форма засчитана", /verdict ok/.test(doc.getElementById("v").innerHTML),
     doc.getElementById("v").textContent);

  // подсказка окончания в разнобое
  w.S.mode = 2; w.startMode(); await wait(40);
  ok("вразброс: есть кнопка подсказки", !!doc.getElementById("hintend"));
  const q3 = w.S.queue[w.S.idx];
  doc.getElementById("hintend").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  await wait(20);
  ok("вразброс: подсказка даёт окончание, а не слово",
     doc.getElementById("v").textContent.indexOf("-" + w.GROUPS[w.S.g].ends[q3.p]) > -1 &&
     doc.getElementById("v").textContent.indexOf(q3.v.f[q3.p]) === -1,
     doc.getElementById("v").textContent);
  ok("вразброс: после подсказки можно ответить",
     !doc.getElementById("inp").disabled);

  // 4. на слух
  w.S.mode = 3; w.startMode(); await wait(60);
  ok("на слух: лицо не показано заранее",
     doc.getElementById("stage").textContent.indexOf("Форма для") === -1);
  ok("на слух: есть замедление и подсказка лица",
     !!doc.getElementById("slow") && !!doc.getElementById("face"));
  const q2 = w.S.queue[w.S.idx];
  type(dom, "#inp", q2.v.f[q2.p]);
  await wait(40);
  ok("на слух: ответ засчитан и лицо названо",
     /verdict ok/.test(doc.getElementById("v").innerHTML) &&
     doc.getElementById("v").textContent.indexOf(w.P[q2.p][0]) > -1,
     doc.getElementById("v").textContent);
}

/* ---------------- страница подключена к остальному ---------------- */
async function testReglasWired() {
  const html = fs.readFileSync(path.join(SITE, "reglas.html"), "utf8");
  ok("страница: заголовок вкладки", /<title>Окончания · Ruta Valencia<\/title>/.test(html));
  ok("страница: значок подключён", /favicon\.svg/.test(html));
  ok("страница: ведёт в «Мой день»", /href="\.\/hoy\.html"/.test(html));

  const hoy = fs.readFileSync(path.join(SITE, "hoy.html"), "utf8");
  ok("чек-лист: есть ссылка на отработку окончаний", /reglas\.html/.test(hoy),
     "блок не добавлен");

  const dom = load("hoy.html");
  await wait(60);
  const block = [...dom.window.document.querySelectorAll(".blk")]
    .find(b => /Окончания/.test(b.textContent));
  ok("чек-лист: блок отрисовался", !!block,
     [...dom.window.document.querySelectorAll(".blk .t")].map(x => x.textContent).join(" | "));
  if (block) ok("чек-лист: блок дополнительный", block.className.indexOf("opt") > -1, block.className);
}

(async () => {
  console.log("Прогоняю тесты...\n");
  await testReglas();
  await testReglasWired();
  console.log(`пройдено: ${passed}   провалено: ${failed.length}`);
  if (failed.length) {
    console.log("\nПРОВАЛЕНЫ:");
    failed.forEach(f => console.log("  ✗ " + f));
    process.exit(1);
  }
  console.log("все проверки зелёные");
})();

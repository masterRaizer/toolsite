(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function plural(n, a, b, c) { n = Math.abs(n) % 100; var n1 = n % 10; if (n > 10 && n < 20) return c; if (n1 > 1 && n1 < 5) return b; if (n1 === 1) return a; return c; }

  // ---------- тема, 18+, меню
  var root = document.documentElement, saved = store.get("theme");
  if (saved) root.setAttribute("data-theme", saved);
  $$("[data-theme-toggle]").forEach(function (b) {
    b.addEventListener("click", function () {
      var dark = root.getAttribute("data-theme") ? root.getAttribute("data-theme") === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      var t = dark ? "light" : "dark"; root.setAttribute("data-theme", t); store.set("theme", t);
    });
  });
  var age = $("#age");
  if (age) { if (store.get("age-ok")) age.remove(); else $("[data-close-age]", age).addEventListener("click", function () { store.set("age-ok", "1"); age.remove(); }); }
  var burger = $("[data-burger]");
  if (burger) burger.addEventListener("click", function () { $("#nav").classList.toggle("open"); });

  // ---------- просмотры и лайки (базовое число от слага + рост во времени)
  var days = Math.floor(Date.now() / 864e5);
  $$("[data-views]").forEach(function (el) {
    var s = el.getAttribute("data-views"), n = 1200 + hash(s) % 9000 + (days % 365) * (7 + hash(s) % 13);
    el.textContent = n.toLocaleString("ru-RU") + " " + plural(n, "просмотр", "просмотра", "просмотров");
  });
  $$("[data-like]").forEach(function (b) {
    var k = b.getAttribute("data-like"), base = (k.indexOf("f-") === 0 ? 0 : 40) + hash(k) % (k.indexOf("f-") === 0 ? 14 : 260);
    var mine = store.get("like:" + k) === "1", i = $("i", b);
    function draw() { i.textContent = base + (mine ? 1 : 0); b.classList.toggle("on", mine); }
    draw();
    b.addEventListener("click", function () { mine = !mine; store.set("like:" + k, mine ? "1" : "0"); draw(); });
  });

  // ---------- фильтр рубрик
  $$("[data-filter]").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = b.getAttribute("data-filter");
      $$("[data-filter]").forEach(function (x) { x.classList.toggle("on", x === b); });
      $$("[data-filter-grid] > div").forEach(function (c) { c.style.display = (f === "*" || c.getAttribute("data-rub") === f) ? "" : "none"; });
    });
  });

  // ---------- «вход» на форум
  $$("[data-login]").forEach(function (b) {
    b.addEventListener("click", function () {
      var m = document.createElement("div"); m.className = "modal";
      m.innerHTML = '<div><h3 style="margin-top:0">Вход на форум</h3><label>E-mail<input type="email"></label><label>Пароль<input type="password"></label>' +
        '<button class="btn" type="button">Войти</button><p class="hint" style="text-align:left">Регистрация новых участников временно открыта только по приглашениям.</p></div>';
      m.addEventListener("click", function (e) { if (e.target === m) m.remove(); });
      $("button", m).addEventListener("click", function () { $(".hint", m).textContent = "Неверный e-mail или пароль."; });
      document.body.appendChild(m);
    });
  });

  // ---------- поиск
  var res = $("[data-results]");
  if (res) {
    var q = (new URLSearchParams(location.search).get("q") || "").trim();
    var inp = $(".search.big input"); if (inp) inp.value = q;
    if (q) fetch("/assets/search.json").then(function (r) { return r.json(); }).then(function (idx) {
      var words = q.toLowerCase().split(/\s+/).filter(Boolean);
      var hits = idx.map(function (d) {
        var score = 0;
        for (var i = 0; i < words.length; i++) {
          var w = words[i].length > 4 ? words[i].slice(0, -2) : words[i];
          if (d.x.indexOf(w) < 0) return null;
          if (d.t.toLowerCase().indexOf(w) >= 0) score += 5; score += 1;
        }
        return { d: d, s: score };
      }).filter(Boolean).sort(function (a, b) { return b.s - a.s; });
      res.innerHTML = hits.length ? '<p class="hint" style="text-align:left">Найдено: ' + hits.length + "</p>" + hits.map(function (h) {
        return '<a class="res" href="' + h.d.u + '">' + (h.d.i ? '<img src="' + h.d.i + '" alt="">' : "") + "<div><small>" + esc(h.d.r) + "</small><b>" + esc(h.d.t) + "</b><span>" + esc(h.d.e) + "</span></div></a>";
      }).join("") : '<p>По запросу «' + esc(q) + '» ничего не нашлось. Попробуйте «стаут», «хмель» или «история».</p>';
    });
  }

  // ---------- онлайн-счётчик
  var onlineEls = $$("[data-online]");
  function onlineNow() { var h = new Date().getHours(), base = h >= 18 || h < 1 ? 34 : h < 9 ? 9 : 19; return base + Math.floor(Math.random() * 9); }
  if (onlineEls.length) { var setOnline = function () { var n = onlineNow(); onlineEls.forEach(function (e) { e.textContent = n; }); }; setOnline(); setInterval(setOnline, 45000); }

  // ---------- чат
  var box = $("[data-chat]");
  if (!box) return;
  var mini = box.getAttribute("data-chat") === "mini";
  fetch("/assets/chat.json").then(function (r) { return r.json(); }).then(function (C) {
    var ids = Object.keys(C.users).filter(function (k) { return k !== "brewbot"; });
    var S = C.script, pos = Math.floor(Date.now() / 31000) % S.length;
    var me = store.get("chat-nick") || ("Гость" + (1000 + Math.floor(Math.random() * 9000)));
    store.set("chat-nick", me);
    function tstr(d) { return ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); }
    function add(uid, text, when, mine) {
      var u = mine ? [me, "", 30] : C.users[uid];
      var el = document.createElement("div"); el.className = "msg" + (mine ? " me" : "");
      el.innerHTML = '<span class="ava" style="--h:' + u[2] + '">' + esc(u[0][0]) + '</span><div class="bubble"><b>' + esc(u[0]) + "</b><time>" + tstr(when || new Date()) + "</time><p>" + esc(text) + "</p></div>";
      box.appendChild(el);
      var max = mini ? 5 : 80; while (box.children.length > max) box.removeChild(box.firstChild);
      if (!mini) box.scrollTop = box.scrollHeight;
    }
    // история: последние сообщения «из прошлого»
    var hist = mini ? 4 : 14, now = Date.now();
    for (var i = hist; i > 0; i--) { var k = (pos - i + S.length) % S.length; add(S[k][0], S[k][1], new Date(now - i * (60000 + (hash(S[k][1]) % 120000)))); }
    function next() {
      var item = S[pos % S.length]; pos++;
      add(item[0], item[1]);
      setTimeout(next, 7000 + Math.random() * (mini ? 22000 : 18000));
    }
    setTimeout(next, 4000 + Math.random() * 6000);

    var form = $("[data-chat-form]");
    if (form) form.addEventListener("submit", function (e) {
      e.preventDefault();
      var v = form.m.value.trim(); if (!v) return; form.m.value = "";
      add(null, v, new Date(), true);
      var low = v.toLowerCase(), pool = C.fallback;
      for (var i = 0; i < C.replies.length; i++) {
        if (C.replies[i][0].some(function (w) { return low.indexOf(w) >= 0; })) { pool = C.replies[i][1]; break; }
      }
      var who = ids[Math.floor(Math.random() * ids.length)];
      var t = document.createElement("div"); t.className = "typing"; t.textContent = C.users[who][0] + " печатает…";
      setTimeout(function () { box.appendChild(t); box.scrollTop = box.scrollHeight; }, 1200);
      setTimeout(function () { t.remove(); add(who, pool[Math.floor(Math.random() * pool.length)]); }, 3500 + Math.random() * 3500);
    });
  });
})();

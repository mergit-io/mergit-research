/*
 * Reading aids for the paper pages: a progress bar, a chapter indicator with time left, marks for the
 * sections you have read, a prompt to continue where you stopped, and keyboard navigation.
 * Everything here is stored in your own browser. Nothing is sent anywhere.
 */
(function () {
  "use strict";
  var article = document.getElementById("content");
  if (!article) return;
  var body = document.body;
  var rev = body.getAttribute("data-rev") || "draft";
  var slug = body.getAttribute("data-slug") || "doc";
  var WPM = 230;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var store = {
    get: function (k) {
      try {
        return JSON.parse(localStorage.getItem(k));
      } catch (e) {
        return null;
      }
    },
    set: function (k, v) {
      try {
        localStorage.setItem(k, JSON.stringify(v));
      } catch (e) {
        /* ignore */
      }
    },
  };
  var READ_KEY = "mergit-read:" + slug + ":" + rev;
  var POS_KEY = "mergit-pos:" + slug + ":" + rev;

  /* ---------- structure ---------- */
  var chapters = Array.prototype.slice.call(article.querySelectorAll(":scope > section[id]"));
  var sections = Array.prototype.slice.call(article.querySelectorAll("section[id]")).filter(function (s) {
    return s.querySelector(":scope > h2, :scope > h3");
  });
  var totalWords = (article.textContent || "").trim().split(/\s+/).length;

  function headingOf(s) {
    var h = s.querySelector(":scope > h2, :scope > h3, :scope > h4");
    if (!h) return "";
    var clone = h.cloneNode(true);
    clone.querySelectorAll(".anchor").forEach(function (a) { a.remove(); });
    return clone.textContent.trim();
  }

  /* ---------- progress bar and chapter pill ---------- */
  var bar = document.querySelector(".progress i");
  var pillTitle = document.querySelector(".pill-title");
  var pillTime = document.querySelector(".pill-time");

  function progress() {
    var top = article.getBoundingClientRect().top + window.scrollY;
    var span = article.offsetHeight - window.innerHeight * 0.6;
    return Math.min(1, Math.max(0, (window.scrollY - top + window.innerHeight * 0.3) / Math.max(1, span)));
  }

  function currentChapter() {
    var line = window.innerHeight * 0.3;
    var current = null;
    for (var i = 0; i < chapters.length; i += 1) {
      if (chapters[i].getBoundingClientRect().top <= line) current = chapters[i];
      else break;
    }
    return current;
  }

  function paint() {
    var p = progress();
    if (bar) bar.style.transform = "scaleX(" + p.toFixed(4) + ")";
    var ch = currentChapter();
    if (pillTitle) pillTitle.textContent = ch ? headingOf(ch) : "Abstract";
    if (pillTime) {
      var left = Math.max(1, Math.ceil((totalWords * (1 - p)) / WPM));
      pillTime.textContent = p > 0.985 ? "Done" : left + " min left";
    }
  }

  /* ---------- read marks ---------- */
  var read = store.get(READ_KEY) || {};
  var tocLinks = {};
  document.querySelectorAll("details.toc a[href^='#']").forEach(function (a) {
    tocLinks[decodeURIComponent(a.getAttribute("href").slice(1))] = a;
  });

  /* A section counts as read only if it sat in the middle of the screen for a moment and the reader
     then moved past it. Jumping straight to a section, or flicking past one, does not count. */
  var dwell = {};
  function markRead() {
    var top = window.innerHeight * 0.25;
    var bottom = window.innerHeight * 0.75;
    var changed = false;
    sections.forEach(function (s) {
      if (read[s.id]) return;
      var r = s.getBoundingClientRect();
      if (r.height <= 0) return;
      // Short sections need only a glance; long ones need a moment longer.
      var need = Math.min(2500, 700 + r.height * 2);
      var inBand = r.top < bottom && r.bottom > top;
      if (inBand) {
        var d = dwell[s.id] || (dwell[s.id] = { t: 0, last: performance.now() });
        var now = performance.now();
        d.t += Math.min(400, now - d.last);
        d.last = now;
      } else if (dwell[s.id]) {
        dwell[s.id].last = performance.now();
      }
      if (dwell[s.id] && dwell[s.id].t >= need && r.bottom < window.innerHeight * 0.4) {
        read[s.id] = 1;
        changed = true;
      }
    });
    if (changed) {
      store.set(READ_KEY, read);
      applyMarks();
    }
  }
  function applyMarks() {
    Object.keys(read).forEach(function (id) {
      if (tocLinks[id]) tocLinks[id].classList.add("read");
    });
    var done = chapters.filter(function (c) { return read[c.id]; }).length;
    var count = document.querySelector(".pill-count");
    if (count) count.textContent = done + " of " + chapters.length + " read";
  }

  /* ---------- scroll handling ---------- */
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      paint();
      markRead();
      ticking = false;
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  setInterval(function () { if (!document.hidden) markRead(); }, 400);
  paint();
  applyMarks();

  /* ---------- remember the place, offer to continue ---------- */
  var saveTimer = null;
  window.addEventListener(
    "scroll",
    function () {
      clearTimeout(saveTimer);
      saveTimer = setTimeout(function () {
        var ch = currentChapter();
        if (progress() > 0.04) store.set(POS_KEY, { id: ch ? ch.id : null, y: Math.round(window.scrollY), t: Date.now() });
      }, 400);
    },
    { passive: true }
  );

  function toast(message, actions) {
    var t = document.createElement("div");
    t.className = "toast";
    t.setAttribute("role", "status");
    var span = document.createElement("span");
    span.textContent = message;
    t.appendChild(span);
    actions.forEach(function (a) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = a.label;
      b.className = a.primary ? "primary" : "";
      b.addEventListener("click", function () {
        t.remove();
        a.run();
      });
      t.appendChild(b);
    });
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add("in"); }, 30);
    return t;
  }

  var saved = store.get(POS_KEY);
  if (saved && saved.y > 600 && !location.hash && window.scrollY < 80) {
    var target = saved.id ? document.getElementById(saved.id) : null;
    var name = target ? headingOf(target) : null;
    var t = toast(name ? "Continue from " + name + "?" : "Continue where you left off?", [
      { label: "Continue", primary: true, run: function () { window.scrollTo({ top: saved.y, behavior: reduce ? "auto" : "smooth" }); } },
      { label: "Start over", run: function () { store.set(POS_KEY, null); } },
    ]);
    setTimeout(function () { if (t.parentNode) t.remove(); }, 14000);
  }

  /* ---------- keyboard ---------- */
  function jump(dir) {
    var line = 90;
    var idx = -1;
    for (var i = 0; i < chapters.length; i += 1) {
      if (chapters[i].getBoundingClientRect().top <= line + 4) idx = i;
    }
    var to = Math.min(chapters.length - 1, Math.max(0, idx + dir));
    if (dir > 0 && idx < 0) to = 0;
    chapters[to].scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }

  var help = null;
  function toggleHelp(force) {
    if (help) {
      help.remove();
      help = null;
      if (!force) return;
    }
    if (force === false) return;
    help = document.createElement("div");
    help.className = "keys";
    help.setAttribute("role", "dialog");
    help.setAttribute("aria-label", "Keyboard shortcuts");
    help.innerHTML =
      "<div class='keys-in'><h2>Keyboard</h2><dl>" +
      "<dt><kbd>j</kbd> <kbd>k</kbd></dt><dd>Next and previous chapter</dd>" +
      "<dt><kbd>f</kbd></dt><dd>Focus mode: hide the chrome</dd>" +
      "<dt><kbd>d</kbd></dt><dd>Switch light and dark</dd>" +
      "<dt><kbd>?</kbd></dt><dd>This list</dd>" +
      "<dt><kbd>Esc</kbd></dt><dd>Close</dd></dl>" +
      "<button type='button' class='btn-s'>Close</button></div>";
    help.addEventListener("click", function (e) {
      if (e.target === help || e.target.tagName === "BUTTON") toggleHelp(false);
    });
    document.body.appendChild(help);
    var btn = help.querySelector("button");
    if (btn) btn.focus();
  }

  function focusMode() {
    var on = body.classList.toggle("focus-mode");
    var b = document.querySelector("[data-act='focus']");
    if (b) b.setAttribute("aria-pressed", on ? "true" : "false");
  }

  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (e.target && e.target.tagName) || "";
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag) || (e.target && e.target.isContentEditable)) return;
    if (e.key === "Escape") return toggleHelp(false);
    if (e.key === "j") jump(1);
    else if (e.key === "k") jump(-1);
    else if (e.key === "f") focusMode();
    else if (e.key === "d") {
      var t = document.querySelector(".theme");
      if (t) t.click();
    } else if (e.key === "?") toggleHelp(true);
  });

  document.querySelectorAll("[data-act]").forEach(function (b) {
    b.addEventListener("click", function () {
      var act = b.getAttribute("data-act");
      if (act === "focus") focusMode();
      else if (act === "keys") toggleHelp(true);
    });
  });
})();

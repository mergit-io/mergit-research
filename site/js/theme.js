/* Light and dark theme toggle. The page already follows the system; this lets a reader override it. */
(function () {
  "use strict";
  var KEY = "mergit-theme";
  var html = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function effective() {
    var t = html.getAttribute("data-theme");
    if (t === "light" || t === "dark") return t;
    return mq && mq.matches ? "dark" : "light";
  }

  function sync() {
    var mode = effective();
    document.querySelectorAll(".theme").forEach(function (b) {
      b.setAttribute("data-mode", mode);
      b.setAttribute("aria-label", mode === "dark" ? "Switch to light theme" : "Switch to dark theme");
      b.setAttribute("title", mode === "dark" ? "Light theme" : "Dark theme");
    });
  }

  function set(mode) {
    html.setAttribute("data-theme", mode);
    try {
      localStorage.setItem(KEY, mode);
    } catch (e) {
      /* private mode: the choice lasts for this page only */
    }
    sync();
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".theme");
    if (!b) return;
    set(effective() === "dark" ? "light" : "dark");
  });
  if (mq && mq.addEventListener) mq.addEventListener("change", sync);
  sync();
})();

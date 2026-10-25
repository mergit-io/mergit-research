/* Home page behaviour: a light that follows the pointer, and chapter tiles that fill in as you read. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var hero = document.querySelector(".hero");
  if (hero && !reduce) {
    var raf = 0;
    hero.addEventListener(
      "pointermove",
      function (e) {
        if (raf) return;
        raf = requestAnimationFrame(function () {
          var r = hero.getBoundingClientRect();
          hero.style.setProperty("--mx", ((e.clientX - r.left) / r.width).toFixed(3));
          hero.style.setProperty("--my", ((e.clientY - r.top) / r.height).toFixed(3));
          raf = 0;
        });
      },
      { passive: true }
    );
  }

  /* Mark chapters the reader has already finished, using the same store the paper page writes. */
  var tiles = document.querySelectorAll(".chap[data-id]");
  if (tiles.length) {
    var rev = document.body.getAttribute("data-rev") || "draft";
    var read = null;
    try {
      read = JSON.parse(localStorage.getItem("mergit-read:paper:" + rev));
    } catch (e) {
      read = null;
    }
    if (read) {
      var done = 0;
      tiles.forEach(function (t) {
        if (read[t.getAttribute("data-id")]) {
          t.classList.add("done");
          done += 1;
        }
      });
      var label = document.querySelector(".chaps-progress");
      if (label && done) label.textContent = done + " of " + tiles.length + " chapters read";
    }
  }
})();

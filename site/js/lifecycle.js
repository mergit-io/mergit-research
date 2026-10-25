/*
 * Section 4.2 and Figure 1 talk to each other. Point at a step in the list and its messages light up in the
 * figure; point at the figure and the matching step lights up in the list. Or press play and watch all nine.
 */
(function () {
  "use strict";
  var sec = document.getElementById("task-lifecycle");
  if (!sec) return;
  var svg = sec.querySelector("svg.live-fig");
  var list = sec.querySelector("ol");
  if (!svg || !list) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var items = Array.prototype.slice.call(list.children);
  var groups = Array.prototype.slice.call(svg.querySelectorAll(".st"));
  var pinned = 0;
  var playing = 0;

  function steps(g) {
    return (g.getAttribute("data-step") || "").split(" ").map(Number);
  }

  function show(n) {
    if (!n) {
      svg.classList.remove("dim");
      groups.forEach(function (g) { g.classList.remove("on"); });
      items.forEach(function (li) { li.classList.remove("lf-on"); });
      return;
    }
    svg.classList.add("dim");
    groups.forEach(function (g) { g.classList.toggle("on", steps(g).indexOf(n) >= 0); });
    items.forEach(function (li, i) { li.classList.toggle("lf-on", i + 1 === n); });
  }

  items.forEach(function (li, i) {
    var n = i + 1;
    li.classList.add("lf-item");
    li.tabIndex = 0;
    li.setAttribute("aria-label", "Step " + n + ". Show it in the figure.");
    li.addEventListener("mouseenter", function () { if (!playing) show(n); });
    li.addEventListener("mouseleave", function () { if (!playing) show(pinned); });
    li.addEventListener("focus", function () { if (!playing) show(n); });
    li.addEventListener("blur", function () { if (!playing) show(pinned); });
    li.addEventListener("click", function () {
      if (playing) return;
      pinned = pinned === n ? 0 : n;
      show(pinned);
    });
  });

  groups.forEach(function (g) {
    g.addEventListener("mouseenter", function () { if (!playing) show(steps(g)[0]); });
    g.addEventListener("mouseleave", function () { if (!playing) show(pinned); });
    g.addEventListener("click", function () {
      if (playing) return;
      var n = steps(g)[0];
      pinned = pinned === n ? 0 : n;
      show(pinned);
      var li = items[n - 1];
      if (li && pinned) li.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
    });
  });

  /* play, one step at a time */
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn-s primary lf-play";
  btn.textContent = "Play the nine steps";
  var bar = document.createElement("div");
  bar.className = "lf-bar";
  var hint = document.createElement("span");
  hint.textContent = "Point at a step, or at the figure, to follow one message through the system.";
  bar.appendChild(btn);
  bar.appendChild(hint);
  var fig = svg.closest("figure");
  if (fig && fig.parentNode) fig.parentNode.insertBefore(bar, fig);

  function stop() {
    clearInterval(playing);
    playing = 0;
    btn.textContent = "Play the nine steps";
    show(pinned);
  }
  btn.addEventListener("click", function () {
    if (playing) return stop();
    var n = 0;
    btn.textContent = "Stop";
    if (fig) fig.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
    playing = setInterval(function () {
      n += 1;
      if (n > 9) return stop();
      show(n);
    }, reduce ? 900 : 1700);
    show(1);
    n = 1;
  });
})();

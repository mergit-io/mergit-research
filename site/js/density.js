/*
 * "Who should get the work?": paper section 8.4 and 8.8. Two agents, one ranked by success rate and one by
 * value density D = E[success] / E[cost], a ratio of expectations. Move the sliders and watch the order flip.
 * Defaults are the paper's illustration. Illustrative numbers, nothing here is measured.
 */
(function (root) {
  "use strict";
  var UI = root.MergitUI;
  if (!UI) return;
  var el = UI.el;
  var ROW = 3.4; // rem
  var BUDGET = 10;

  function mount(host) {
    var agents = [
      { key: "X", name: "Agent X", theta: 0.95, cost: 1.8, color: "var(--ink3)" },
      { key: "Y", name: "Agent Y", theta: 0.88, cost: 0.6, color: "var(--azure)" },
    ];

    function dens(a) { return a.theta / a.cost; }

    /* ---- controls ---- */
    var outs = [];
    function agentControls(a) {
      var oT = el("output", {});
      var oC = el("output", {});
      var tIn = el("input", { type: "range", min: "0.05", max: "1", step: "0.01", value: a.theta, "aria-label": a.name + " success rate", oninput: function (e) { a.theta = +e.target.value; render(); } });
      var cIn = el("input", { type: "range", min: "0.1", max: "4", step: "0.05", value: a.cost, "aria-label": a.name + " mean cost per task", oninput: function (e) { a.cost = +e.target.value; render(); } });
      outs.push(function () { oT.textContent = UI.pct(a.theta); oC.textContent = "$" + a.cost.toFixed(2); });
      return el(
        "div",
        { class: "de-agent" },
        el("div", { class: "de-name" }, el("span", { class: "de-swatch", style: "background:" + a.color }), a.name),
        el("div", { class: "ctl" }, el("label", {}, "Success rate"), tIn, oT),
        el("div", { class: "ctl" }, el("label", {}, "Mean cost per task"), cIn, oC)
      );
    }

    /* ---- the two rankings ---- */
    function ranking(title, sub) {
      var list = el("div", { class: "de-list", style: "height:" + agents.length * ROW + "rem" });
      var rowsByKey = {};
      agents.forEach(function (a) {
        var bar = el("span", { class: "de-bar", style: "background:" + a.color });
        var val = el("span", { class: "de-val" });
        var rank = el("span", { class: "de-rank" });
        var row = el("div", { class: "de-row" }, rank, el("span", { class: "de-who" }, a.name), el("span", { class: "de-track" }, bar), val);
        list.appendChild(row);
        rowsByKey[a.key] = { row: row, bar: bar, val: val, rank: rank };
      });
      return { node: el("div", { class: "de-col" }, el("h4", {}, title), el("p", { class: "de-sub" }, sub), list), rows: rowsByKey };
    }
    var byQ = ranking("Ranked by quality", "Success rate alone");
    var byD = ranking("Ranked by value density", "Expected successes per dollar");

    /* ---- what a budget buys ---- */
    var budget = el("div", { class: "de-budget" });
    var verdict = el("p", { class: "de-verdict", "aria-live": "polite" });

    function dots(a) {
      var n = Math.min(24, BUDGET * dens(a));
      var full = Math.floor(n + 1e-9);
      var frac = n - full;
      var wrap = el("span", { class: "de-dots", "aria-hidden": "true" });
      for (var i = 0; i < full; i += 1) wrap.appendChild(el("i", { style: "background:" + a.color }));
      if (frac > 0.05 && full < 24) wrap.appendChild(el("i", { class: "part", style: "background:linear-gradient(90deg," + a.color + " " + Math.round(frac * 100) + "%, var(--sunken) 0)" }));
      return wrap;
    }

    function layout(set, order, value, fmt) {
      var max = Math.max.apply(null, order.map(value));
      order.forEach(function (a, i) {
        var r = set.rows[a.key];
        r.row.style.top = i * ROW + "rem";
        r.rank.textContent = String(i + 1);
        r.bar.style.width = Math.max(2, (value(a) / max) * 100) + "%";
        r.val.textContent = fmt(value(a));
      });
    }

    var lastOrder = "";
    function render() {
      outs.forEach(function (f) { f(); });
      var qOrder = agents.slice().sort(function (a, b) { return b.theta - a.theta; });
      var dOrder = agents.slice().sort(function (a, b) { return dens(b) - dens(a); });
      layout(byQ, qOrder, function (a) { return a.theta; }, UI.pct);
      layout(byD, dOrder, dens, function (v) { return v.toFixed(2); });

      var signature = qOrder[0].key + dOrder[0].key;
      byQ.node.classList.toggle("de-differs", qOrder[0].key !== dOrder[0].key);
      byD.node.classList.toggle("de-differs", qOrder[0].key !== dOrder[0].key);

      budget.textContent = "";
      agents.forEach(function (a) {
        var n = BUDGET * dens(a);
        budget.appendChild(
          el("div", { class: "de-spend" }, el("span", { class: "de-who" }, a.name), dots(a), el("span", { class: "de-count" }, n.toFixed(1) + " validated successes"))
        );
      });

      var hi = dOrder[0], lo = dOrder[1];
      var ratio = dens(hi) / dens(lo);
      if (ratio < 1.02) verdict.textContent = "Dead even on value density, so cost and quality cancel out.";
      else
        verdict.textContent =
          hi.name + " delivers " + ratio.toFixed(1) + "× the validated successes per dollar of " + lo.name + "." +
          (qOrder[0].key !== hi.key ? " Quality-only ranking would pick " + qOrder[0].name + " every time." : " Both rankings agree here.");
      lastOrder = signature;
    }

    var wrap = el(
      "div",
      { class: "de" },
      el("div", { class: "de-controls" }, agents.map(agentControls)),
      el("div", { class: "de-ranks" }, byQ.node, byD.node),
      el("div", { class: "de-spend-h" }, "A $" + BUDGET + " budget buys, on average:"),
      budget,
      verdict
    );
    host.appendChild(wrap);
    render();
  }

  function auto() {
    document.querySelectorAll("[data-widget='density']").forEach(mount);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
  else auto();
})(window);

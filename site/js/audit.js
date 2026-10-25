/*
 * "How much stake buys how little auditing": the paper's section 7.2 and 7.5 as a live chart.
 * It uses the same functions as the calculator (calculator/core.js), which are tested against the numbers
 * printed in the paper. Illustrative model, nothing here is measured.
 */
(function (root) {
  "use strict";
  var UI = root.MergitUI;
  var A = root.MergitAudit;
  if (!UI || !A) return;
  var el = UI.el;

  var X0 = 2, X1 = 1000, Y0 = 0.002, Y1 = 1;
  var W = 620, H = 300, PL = 52, PR = 16, PT = 14, PB = 38;
  var lx0 = Math.log(X0), lx1 = Math.log(X1), ly0 = Math.log(Y0), ly1 = Math.log(Y1);

  function sx(S) { return PL + ((Math.log(S) - lx0) / (lx1 - lx0)) * (W - PL - PR); }
  function sy(p) { return PT + (1 - (Math.log(Math.max(Y0, Math.min(Y1, p))) - ly0) / (ly1 - ly0)) * (H - PT - PB); }
  function invx(px) { return Math.exp(lx0 + ((px - PL) / (W - PL - PR)) * (lx1 - lx0)); }

  function mount(host) {
    var st = { S: 30, V: 2, q: 0, nCap: 5, theta: 0.95, cExec: 1, lambda: 1, cAudit: 0.02 };

    function inputs(S) {
      return { V: st.V, cExec: st.cExec, theta: st.theta, S: S, lambda: st.lambda, q: st.q, agentSeesPredicate: true };
    }
    function oneShot(S) {
      var pReq = A.requiredDetection(inputs(S));
      return { pReq: pReq, p: A.auditRate(pReq, st.q) };
    }

    /* ---- controls ---- */
    var outs = {};
    function slider(label, key, min, max, step, fmt, log) {
      var out = el("output", {});
      outs[key] = out;
      var toVal = log ? function (t) { return Math.exp(Math.log(min) + (t / 1000) * (Math.log(max) - Math.log(min))); } : null;
      var toPos = log ? function (v) { return ((Math.log(v) - Math.log(min)) / (Math.log(max) - Math.log(min))) * 1000; } : null;
      var input = el("input", {
        type: "range",
        min: log ? 0 : min,
        max: log ? 1000 : max,
        step: log ? 1 : step,
        value: log ? toPos(st[key]) : st[key],
        "aria-label": label,
        oninput: function (e) {
          var v = log ? toVal(+e.target.value) : +e.target.value;
          st[key] = key === "nCap" ? Math.round(v) : v;
          render();
        },
      });
      var row = el("div", { class: "ctl" }, el("label", {}, label), input, out);
      row.update = function () {
        out.textContent = fmt(st[key]);
        if (log) input.value = toPos(st[key]);
      };
      return row;
    }
    var rows = [
      slider("Stake the agent posts", "S", X0, X1, 1, function (v) { return "$" + (v < 10 ? v.toFixed(1) : Math.round(v)); }, true),
      slider("Payment for the task", "V", 0.5, 10, 0.1, function (v) { return "$" + v.toFixed(2); }),
      slider("Chance a false receipt is challenged", "q", 0, 0.2, 0.005, function (v) { return UI.pct(v); }),
      slider("Tasks one agent runs at once", "nCap", 1, 30, 1, function (v) { return String(v); }),
    ];
    var more = el(
      "details",
      { class: "ex-more" },
      el("summary", {}, "Change the example's other numbers"),
      slider("Chance honest work passes", "theta", 0.05, 1, 0.01, function (v) { return v.toFixed(2); }),
      slider("Cost to do the work", "cExec", 0.1, 5, 0.05, function (v) { return "$" + v.toFixed(2); })
    );
    rows.push(more.children[1], more.children[2]);

    /* ---- chart ---- */
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, class: "au-chart", role: "img", "aria-label": "Required audit rate against stake, on log scales" });
    var readout = el("div", { class: "au-read", "aria-live": "polite" });
    var bars = el("div", { class: "au-bars" });

    function line(x1, y1, x2, y2, cls) { return el("line", { x1: x1, y1: y1, x2: x2, y2: y2, class: cls }); }
    function txt(x, y, s, cls, anchor) { return el("text", { x: x, y: y, class: cls || "au-t", "text-anchor": anchor || "middle" }, s); }

    function drawChart() {
      svg.textContent = "";
      var i;
      // grid and ticks
      [0.002, 0.01, 0.1, 1].forEach(function (p) {
        svg.appendChild(line(PL, sy(p), W - PR, sy(p), "au-grid"));
        svg.appendChild(txt(PL - 8, sy(p) + 4, UI.pct(p), "au-t", "end"));
      });
      [2, 5, 10, 30, 100, 300, 1000].forEach(function (s) {
        svg.appendChild(line(sx(s), PT, sx(s), H - PB, "au-grid"));
        svg.appendChild(txt(sx(s), H - PB + 18, "$" + s));
      });
      svg.appendChild(txt((PL + W - PR) / 2, H - 4, "Stake posted (log scale)", "au-axis"));
      svg.appendChild(el("text", { x: 12, y: (PT + H - PB) / 2, class: "au-axis", "text-anchor": "middle", transform: "rotate(-90 12 " + (PT + H - PB) / 2 + ")" }, "Share of receipts audited (log scale)"));

      // region where no audit rate can deter
      var g = Math.max(st.cExec + (1 - st.theta) * st.V, st.V);
      var sMin = (g - st.V) / st.lambda;
      if (sMin > X0) {
        svg.appendChild(el("rect", { x: sx(X0), y: PT, width: Math.max(0, sx(Math.min(sMin, X1)) - sx(X0)), height: H - PT - PB, class: "au-void" }));
        svg.appendChild(txt(sx(X0) + 6, PT + 16, "cannot be deterred", "au-t au-void-t", "start"));
      }

      // curves
      var d1 = "", d2 = "", k, S, o, pn;
      var N = 70;
      for (k = 0; k <= N; k += 1) {
        S = Math.exp(lx0 + (k / N) * (lx1 - lx0));
        o = oneShot(S);
        var y1 = o.p === null ? Y1 : o.p <= 0 ? Y0 : o.p;
        d1 += (k ? "L" : "M") + sx(S).toFixed(1) + " " + sy(y1).toFixed(1);
        pn = A.rateForConcurrency(inputs(S), st.nCap === undefined ? 1 : st.nCap);
        var yN = pn === null ? Y1 : pn <= 0 ? Y0 : Math.max(pn, Y0);
        d2 += (k ? "L" : "M") + sx(S).toFixed(1) + " " + sy(yN).toFixed(1);
      }
      svg.appendChild(el("path", { d: d2, class: "au-line au-line-n" }));
      svg.appendChild(el("path", { d: d1, class: "au-line au-line-1" }));

      // legend
      svg.appendChild(line(W - PR - 215, PT + 8, W - PR - 193, PT + 8, "au-line au-line-1"));
      svg.appendChild(txt(W - PR - 187, PT + 12, "One task at a time", "au-t", "start"));
      svg.appendChild(line(W - PR - 215, PT + 26, W - PR - 193, PT + 26, "au-line au-line-n"));
      svg.appendChild(txt(W - PR - 187, PT + 30, st.nCap + " tasks at once", "au-t", "start"));

      // current point
      var cur = oneShot(st.S);
      var yc = cur.p === null ? Y1 : cur.p <= 0 ? Y0 : cur.p;
      svg.appendChild(line(sx(st.S), PT, sx(st.S), H - PB, "au-cursor"));
      svg.appendChild(el("circle", { cx: sx(st.S), cy: sy(yc), r: 5.5, class: "au-dot" }));
    }

    function drawReadout() {
      var cur = oneShot(st.S);
      var pn = A.rateForConcurrency(inputs(st.S), st.nCap);
      var oneIn = function (p) { return p === null ? "not deterrable" : p <= 0 ? "none needed" : "1 in " + Math.max(1, Math.round(1 / p)); };
      readout.textContent = "";
      readout.appendChild(
        el("div", { class: "au-card" }, el("span", { class: "au-k" }, "Audit rate, one task"), el("strong", { class: "au-big" }, cur.p === null ? "no rate works" : cur.p <= 0 ? "none" : UI.pct(cur.p)), el("span", { class: "au-sub" }, oneIn(cur.p) + (cur.p > 0 && cur.p !== null ? " receipts" : "")))
      );
      readout.appendChild(
        el("div", { class: "au-card" }, el("span", { class: "au-k" }, st.nCap + " tasks at once"), el("strong", { class: "au-big" }, pn === null ? "no rate works" : pn <= 0 ? "none" : UI.pct(pn)), el("span", { class: "au-sub" }, oneIn(pn) + (pn > 0 && pn !== null ? " receipts" : "")))
      );
      var cost = cur.p === null ? null : st.cAudit * cur.p;
      bars.textContent = "";
      var reBar = el("span", { class: "au-bar au-bar-re", style: "width:100%" });
      var auPct = cost === null ? 0 : Math.max(0.35, (cost / st.cExec) * 100);
      var auBar = el("span", { class: "au-bar au-bar-au", style: "width:" + auPct + "%" });
      bars.appendChild(el("div", { class: "au-row" }, el("span", { class: "au-lab" }, "Re-run the work to check it"), el("span", { class: "au-track" }, reBar), el("span", { class: "au-val" }, UI.money(st.cExec))));
      bars.appendChild(el("div", { class: "au-row" }, el("span", { class: "au-lab" }, "Audit the evidence at that rate"), el("span", { class: "au-track" }, auBar), el("span", { class: "au-val" }, cost === null ? "n/a" : cost <= 0 ? "$0" : UI.money(cost))));
      var ratio = cost && cost > 0 ? Math.round(st.cExec / cost) : null;
      bars.appendChild(
        el("p", { class: "au-ratio" }, cost === null ? "At this stake no audit rate makes forging unprofitable. Raise the stake or lower the payment." : ratio === null ? "No routine audit is needed here: challengers alone deter forgery." : "About " + ratio.toLocaleString("en-US") + " times cheaper than re-running the work, in this model.")
      );
    }

    function render() {
      rows.forEach(function (r) { r.update(); });
      drawChart();
      drawReadout();
    }

    // clicking or dragging on the chart sets the stake
    function setFromPointer(e) {
      var r = svg.getBoundingClientRect();
      var px = ((e.clientX - r.left) / r.width) * W;
      st.S = UI.clamp(invx(px), X0, X1);
      render();
    }
    var dragging = false;
    svg.addEventListener("pointerdown", function (e) { dragging = true; svg.setPointerCapture(e.pointerId); setFromPointer(e); });
    svg.addEventListener("pointermove", function (e) { if (dragging) setFromPointer(e); });
    svg.addEventListener("pointerup", function () { dragging = false; });

    var wrap = el(
      "div",
      { class: "au" },
      el("div", { class: "au-left" }, rows.slice(0, 4), more),
      el("div", { class: "au-right" }, svg, readout, bars)
    );
    host.appendChild(wrap);
    render();
  }

  function auto() {
    document.querySelectorAll("[data-widget='audit']").forEach(mount);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
  else auto();
})(window);

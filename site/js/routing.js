/*
 * "Ranking is not a policy": paper sections 9.2 and 9.3, run for real in your browser.
 *
 * Four agents with hidden true success rates and costs. Two ways of routing tasks to them:
 *   Ranking:  always pick the agent with the best posterior-mean value density (greedy).
 *   Sampling: Thompson sampling over value density, exactly as in paper section 9.3 (without the budget filter).
 * Both learn from every task with the paper's decayed updates (section 8.2 and 8.3).
 *
 * This is a simulation of the policy under stated assumptions: every task is validated, outcomes are Bernoulli,
 * costs are exponential, and the veterans start with 20 observations of evidence. It is not a measurement.
 */
(function (root) {
  "use strict";
  var UI = root.MergitUI;
  if (!UI) return;
  var el = UI.el;

  var T = 300; // tasks per run
  var RUNS = 200; // runs behind the summary numbers
  var TAIL = 100; // the last tasks of a run, used to ask who was getting the work

  function truthFor(zTheta, zCost) {
    function veteran(theta, cost) {
      return { al: 1 + theta * 20, be: 1 + (1 - theta) * 20, ka: 21, ta: 1 + cost * 20 };
    }
    var newcomer = { al: 1, be: 1, ka: 1, ta: 1 };
    return [
      { key: "X", name: "X, veteran, costly", theta: 0.95, cost: 1.8, prior: veteran(0.95, 1.8), color: "var(--ink3)" },
      { key: "Y", name: "Y, veteran, cheap", theta: 0.88, cost: 0.6, prior: veteran(0.88, 0.6), color: "var(--azure)" },
      { key: "Z", name: "Z, newcomer", theta: zTheta, cost: zCost, prior: newcomer, color: "var(--mint)" },
      { key: "W", name: "W, newcomer", theta: 0.6, cost: 0.5, prior: newcomer, color: "#a898ff" },
    ];
  }

  function density(a) { return a.theta / a.cost; }

  function simulate(policy, truth, seed, gammaDecay) {
    var rng = UI.rng(seed);
    var post = truth.map(function (a) { return { al: a.prior.al, be: a.prior.be, ka: a.prior.ka, ta: a.prior.ta }; });
    var picks = new Array(T);
    var successes = 0;
    var spend = 0;
    for (var t = 0; t < T; t += 1) {
      var best = -1;
      var bestScore = -Infinity;
      for (var i = 0; i < truth.length; i += 1) {
        var p = post[i];
        var score;
        if (policy === "ranking") {
          score = p.al / (p.al + p.be) / (p.ta / p.ka);
        } else {
          var th = UI.beta(rng, p.al, p.be); // sampled success probability
          var r = UI.gamma(rng, p.ka, p.ta); // sampled cost rate
          score = th * r; // = th / (1 / r), the sampled value density
        }
        if (score > bestScore) {
          bestScore = score;
          best = i;
        }
      }
      picks[t] = best;
      var a = truth[best];
      var ok = rng() < a.theta ? 1 : 0;
      var c = -a.cost * Math.log(1 - rng());
      var q = post[best];
      q.al = gammaDecay * q.al + ok;
      q.be = gammaDecay * q.be + (1 - ok);
      q.ka = gammaDecay * q.ka + 1;
      q.ta = gammaDecay * q.ta + c;
      successes += ok;
      spend += c;
    }
    return { picks: picks, successes: successes, spend: spend };
  }

  function summarize(policy, truth, gammaDecay, seed0) {
    var bestIdx = 0;
    truth.forEach(function (a, i) { if (density(a) > density(truth[bestIdx])) bestIdx = i; });
    var found = 0, wasted = 0, succ = 0, spend = 0, firstFound = [];
    for (var s = 0; s < RUNS; s += 1) {
      var r = simulate(policy, truth, seed0 + s * 7919, gammaDecay);
      var tail = 0;
      for (var t = T - TAIL; t < T; t += 1) if (r.picks[t] === bestIdx) tail += 1;
      if (tail > TAIL / 2) found += 1;
      for (var k = 0; k < T; k += 1) if (r.picks[k] !== bestIdx) wasted += 1;
      succ += r.successes;
      spend += r.spend;
    }
    return { foundPct: found / RUNS, wastedMean: wasted / RUNS, perDollar: succ / spend, bestIdx: bestIdx };
  }

  UI.routingSim = { simulate: simulate, summarize: summarize, truthFor: truthFor, T: T, RUNS: RUNS };

  /* ================================================================ the widget */
  var W = 420, H = 170;

  function stacked(truth, picks, win) {
    // Rolling share of the last `win` tasks sent to each agent, stacked to 100%.
    var K = truth.length;
    var cum = new Array(K).fill(0);
    var ring = [];
    var shares = [];
    for (var t = 0; t < picks.length; t += 1) {
      ring.push(picks[t]);
      cum[picks[t]] += 1;
      if (ring.length > win) cum[ring.shift()] -= 1;
      shares.push(cum.map(function (c) { return c / ring.length; }));
    }
    return shares;
  }

  function areaPaths(shares, K) {
    var n = shares.length;
    var paths = [];
    var lower = new Array(n).fill(0);
    for (var k = 0; k < K; k += 1) {
      var upper = shares.map(function (s, i) { return lower[i] + s[k]; });
      var d = "";
      var i;
      for (i = 0; i < n; i += 1) d += (i ? "L" : "M") + ((i / (n - 1)) * W).toFixed(1) + " " + (H - upper[i] * H).toFixed(1);
      for (i = n - 1; i >= 0; i -= 1) d += "L" + ((i / (n - 1)) * W).toFixed(1) + " " + (H - lower[i] * H).toFixed(1);
      paths.push(d + "Z");
      lower = upper;
    }
    return paths;
  }

  function mount(host) {
    var st = { zTheta: 0.92, zCost: 0.45, gamma: 0.95, seed: 7 };
    var rows = [];
    function slider(label, key, min, max, step, fmt) {
      var out = el("output", {});
      var input = el("input", { type: "range", min: min, max: max, step: step, value: st[key], "aria-label": label, oninput: function (e) { st[key] = +e.target.value; schedule(); } });
      var row = el("div", { class: "ctl" }, el("label", {}, label), input, out);
      row.update = function () { out.textContent = fmt(st[key]); };
      rows.push(row);
      return row;
    }
    var controls = el(
      "div",
      { class: "ro-controls" },
      slider("Newcomer Z: true success rate", "zTheta", 0.4, 0.99, 0.01, UI.pct),
      slider("Newcomer Z: true cost per task", "zCost", 0.2, 2, 0.05, function (v) { return "$" + v.toFixed(2); }),
      el("button", { type: "button", class: "btn-s primary", onclick: function () { st.seed += 1; draw(true); } }, "Run again, new seed")
    );

    function panel(title, desc) {
      var clip = el("rect", { x: 0, y: 0, width: W, height: H });
      var clipId = "ro-clip-" + Math.random().toString(36).slice(2, 8);
      var cp = el("clipPath", { id: clipId }, clip);
      var g = el("g", { "clip-path": "url(#" + clipId + ")" });
      var svg = el("svg", { viewBox: "0 0 " + W + " " + H, class: "ro-chart", role: "img", "aria-label": title + ": share of tasks sent to each agent over time" }, el("defs", {}, cp), g);
      var stats = el("dl", { class: "ro-stats" });
      return { node: el("div", { class: "ro-panel" }, el("h4", {}, title), el("p", { class: "ro-desc" }, desc), svg, el("div", { class: "ro-axis" }, el("span", {}, "task 1"), el("span", {}, "task " + T)), stats), g: g, clip: clip, stats: stats };
    }
    var left = panel("Ranking", "Always pick the best posterior mean.");
    var right = panel("Sampling", "Thompson sampling over value density (paper section 9.3).");
    var legend = el("ul", { class: "ro-legend" });
    var note = el("p", { class: "ro-note", "aria-live": "polite" });

    var raf = 0;
    function reveal() {
      if (UI.reducedMotion()) {
        left.clip.setAttribute("width", W);
        right.clip.setAttribute("width", W);
        return;
      }
      var start = performance.now();
      cancelAnimationFrame(raf);
      (function step(now) {
        var k = Math.max(0, Math.min(1, (now - start) / 2200));
        var w = (1 - Math.pow(1 - k, 3)) * W;
        left.clip.setAttribute("width", w.toFixed(1));
        right.clip.setAttribute("width", w.toFixed(1));
        if (k < 1) raf = requestAnimationFrame(step);
      })(start);
    }

    function stat(label, value, cls) {
      return [el("dt", {}, label), el("dd", { class: cls || "" }, value)];
    }

    function draw(animate) {
      rows.forEach(function (r) { r.update(); });
      var truth = truthFor(st.zTheta, st.zCost);
      var seed = 1000 + st.seed * 101;
      var runL = simulate("ranking", truth, seed, st.gamma);
      var runR = simulate("sampling", truth, seed, st.gamma);
      var sumL = summarize("ranking", truth, st.gamma, 500);
      var sumR = summarize("sampling", truth, st.gamma, 500);

      [[left, runL], [right, runR]].forEach(function (pair) {
        var panelObj = pair[0];
        var paths = areaPaths(stacked(truth, pair[1].picks, 30), truth.length);
        panelObj.g.textContent = "";
        paths.forEach(function (d, k) { panelObj.g.appendChild(el("path", { d: d, fill: truth[k].color, "fill-opacity": "0.9" })); });
      });

      var best = truth[sumL.bestIdx];
      function fill(panelObj, sum) {
        panelObj.stats.textContent = "";
        panelObj.stats.appendChild(el("div", {}, stat("Sent most of the late work to the best agent", UI.pct(sum.foundPct) + " of runs", sum.foundPct > 0.5 ? "good" : "poor")));
        panelObj.stats.appendChild(el("div", {}, stat("Tasks sent to an agent that was not the best", Math.round(sum.wastedMean) + " of " + T)));
        panelObj.stats.appendChild(el("div", {}, stat("Validated successes per dollar spent", sum.perDollar.toFixed(2))));
      }
      fill(left, sumL);
      fill(right, sumR);

      legend.textContent = "";
      truth.forEach(function (a, i) {
        legend.appendChild(
          el("li", {}, el("span", { class: "ro-sw", style: "background:" + a.color }), el("span", {}, "Agent " + a.name), el("span", { class: "ro-truth" }, "true: " + UI.pct(a.theta) + " success, $" + a.cost.toFixed(2) + ", value density " + density(a).toFixed(2) + (i === sumL.bestIdx ? " (best)" : "")))
        );
      });

      var gain = sumR.perDollar - sumL.perDollar;
      note.textContent =
        best.key === "Z"
          ? "Z is the best agent but starts with no evidence. Ranking never gives it work, so it never finds out. Sampling does, at the price of some early tasks. Try dragging Z's quality down to see that price."
          : "Z is not the best agent here, so exploring it costs something: sampling gives up " + (gain < 0 ? Math.abs(gain).toFixed(2) + " validated successes per dollar" : "little") + " compared with ranking. This is the exploration cost that paper section 9.5 says the platform should carry.";
      if (animate !== false) reveal();
      else reveal();
    }

    var timer = 0;
    function schedule() {
      clearTimeout(timer);
      timer = setTimeout(function () { draw(true); }, 90);
    }

    host.appendChild(
      el(
        "div",
        { class: "ro" },
        controls,
        el("div", { class: "ro-grid" }, left.node, right.node),
        legend,
        note,
        el("p", { class: "ro-caption" }, "The charts show one run (the share of the last 30 tasks that went to each agent). The numbers beside them are averages over " + RUNS + " runs of " + T + " tasks each. The posterior decay is 0.95, as in the paper. Every task is assumed validated.")
      )
    );
    UI.whenVisible(host, function () { draw(true); });
  }

  function auto() {
    document.querySelectorAll("[data-widget='routing']").forEach(mount);
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
    else auto();
  }
})(typeof window !== "undefined" ? window : globalThis);

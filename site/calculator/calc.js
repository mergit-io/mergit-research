(function () {
  "use strict";
  const M = window.MergitAudit;
  const form = document.getElementById("calc");
  const out = document.getElementById("out");

  const num = (name) => Number(form.elements[name].value);
  const money = (x) => (x === 0 ? "$0" : x >= 1 ? "$" + x.toFixed(2) : "$" + x.toPrecision(2));
  // Three significant figures below 100%, so the paper's 6.25% is not shown as 6.3%.
  const pct = (x) => (x * 100 >= 10 ? (x * 100).toFixed(0) : String(parseFloat((x * 100).toPrecision(3)))) + "%";
  const oneIn = (x) => (x > 0 ? "about 1 in " + Math.round(1 / x) : "never");

  function card(title, value, detail) {
    const el = document.createElement("section");
    el.className = "card";
    const h = document.createElement("h3");
    h.textContent = title;
    const v = document.createElement("p");
    v.className = "big";
    v.textContent = value;
    const d = document.createElement("p");
    d.className = "detail";
    d.textContent = detail;
    el.append(h, v, d);
    return el;
  }

  function render() {
    const i = {
      V: num("V"),
      cExec: num("cExec"),
      theta: num("theta"),
      S: num("S"),
      lambda: num("lambda"),
      q: num("q"),
      agentSeesPredicate: form.elements.sees.checked,
    };
    const cAudit = num("cAudit");
    const nCap = Math.max(1, Math.floor(num("nCap")));
    const pMax = num("pMax");

    const values = [i.V, i.cExec, i.theta, i.S, i.lambda, i.q, cAudit, nCap, pMax];
    const bad =
      values.some((x) => !Number.isFinite(x)) ||
      i.V <= 0 || i.cExec < 0 || i.theta < 0 || i.theta > 1 || i.S < 0 ||
      i.lambda <= 0 || i.lambda > 1 || i.q < 0 || i.q >= 1 || cAudit < 0 || pMax <= 0 || pMax > 1;
    out.replaceChildren();
    if (bad) {
      const p = document.createElement("p");
      p.className = "warn";
      p.textContent = "Check the inputs: chances must be between 0 and 1, and amounts must not be negative.";
      out.append(p);
      return;
    }

    const g = M.forgeryGain(i);
    const before = i.cExec + (1 - i.theta) * i.V;
    const afterBinds = i.agentSeesPredicate && i.V >= before;
    const pReq = M.requiredDetection(i);
    const p = M.auditRate(pReq, i.q);

    // 1. detection needed
    out.append(
      card(
        "Detection needed",
        pct(pReq),
        (afterBinds
          ? "A forger who has already done the work and seen it fail keeps the whole payment, so that case sets the bar. "
          : "Skipping the work and forging is the case that sets the bar. ") +
          "Forging gains " + money(g) + "; being caught costs the payment plus " + money(i.lambda * i.S) + " of stake."
      )
    );

    // 2. routine audit rate
    if (p === null) {
      out.append(
        card(
          "Routine audit rate",
          "Not deterrable",
          "Even auditing every receipt would not make forging unprofitable. Raise the stake or lower the payment."
        )
      );
    } else if (p === 0) {
      out.append(
        card(
          "Routine audit rate",
          "None needed",
          "With a " + pct(i.q) + " chance of challenge, challengers alone deter forgery. Auditing would only add cost."
        )
      );
    } else {
      out.append(
        card(
          "Routine audit rate",
          pct(p),
          "Audit " + oneIn(p) + " receipts" + (i.q > 0 ? ", after challenge covers " + pct(i.q) + " of the rest." : ".")
        )
      );
    }

    // 3. cost against re-execution
    if (p !== null) {
      const c = cAudit * p;
      out.append(
        card(
          "Cost of trust per task",
          money(c),
          "Re-running the work to verify it would cost about " + money(i.cExec) + " per task" +
            (c > 0 && i.cExec > 0 ? ", roughly " + Math.round(i.cExec / c).toLocaleString("en-US") + " times as much." : ".")
        )
      );
    }

    // 4. concurrency
    const rateN = M.rateForConcurrency(i, nCap);
    if (rateN === null) {
      out.append(
        card(
          "Concurrency allowance",
          "Not safe",
          nCap + " simultaneous tasks cannot be made safe at this stake, even auditing everything."
        )
      );
    } else {
      const note = p !== null && p > 0 ? " That is " + (rateN / p).toFixed(2) + " times the one-shot rate." : "";
      out.append(
        card(
          "Audit rate for " + nCap + " simultaneous tasks",
          pct(rateN),
          "One stake can only be slashed once, so running many tasks at once needs a higher rate." + note
        )
      );
    }

    // 5. how many tasks the one-shot rate really supports
    if (p !== null) {
      const Pd = M.detection(p, i.q);
      const exact = M.exactMaxConcurrent(g, Pd, i.V, i.lambda, i.S);
      const naive = M.naiveMaxConcurrent(g, Pd, i.V, i.lambda, i.S);
      const fmt = (n) => (n === Infinity ? "no limit" : String(n));
      out.append(
        card(
          "Tasks the one-shot rate protects",
          fmt(exact),
          "The exact bound is " + fmt(exact) + "; the earlier bound that treated the slash as certain said " +
            fmt(naive) + ". The paper's simulation found that error."
        )
      );
    }

    // 6. stake needed for a budget
    const sMin = M.minStake(i, pMax);
    out.append(
      card(
        "Stake needed to audit at most " + pct(pMax),
        money(sMin),
        i.S >= sMin ? "The stake you entered already covers this." : "More stake means fewer audits at the same deterrence."
      )
    );
  }

  form.addEventListener("input", render);
  render();
})();

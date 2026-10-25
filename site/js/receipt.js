/*
 * "Break a receipt": a live, hash-chained receipt with real SHA-256 running in the browser.
 *
 * It mirrors paper section 6.2: steps are numbered and hash-chained, h_i = H(h_{i-1} || s_i), and a
 * Merkle root covers all of them. Edit, remove or reorder a step and the verifier says what broke.
 * Switch the commitment off and you become the runtime: you can write anything and it still verifies,
 * which is the point of paper section 6.4 and why attestation exists.
 *
 * Illustrative model. The step contents and costs are the paper's running example, not measurements.
 */
(function (root) {
  "use strict";
  var UI = root.MergitUI;
  if (!UI) return;
  var el = UI.el;
  var sha = UI.sha256;

  var HEADER = "task=payments/test_refund.py::test_partial_refund | phi=suite exits 0, diff within payments/ | budget=$2.00";

  var DEFAULTS = [
    { type: "model call", text: "plan the fix", cost: 0.21 },
    { type: "read", text: "payments/refund.py", cost: 0.02 },
    { type: "run tests", text: "exit 1", cost: 0.08 },
    { type: "write", text: "payments/refund.py", cost: 0.31 },
    { type: "run tests", text: "exit 0", cost: 0.07 },
    { type: "diff", text: "paths within payments/", cost: 0.01 },
  ];


  var SUB = ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"];
  function sub(n) {
    return String(n)
      .split("")
      .map(function (d) {
        return SUB[+d] || d;
      })
      .join("");
  }

  function canon(s, seq) {
    return seq + "|" + s.type + "|" + s.text + "|" + Number(s.cost).toFixed(2);
  }

  function build(list) {
    var chain = [];
    var leaves = [];
    var prev = sha(HEADER);
    list.forEach(function (s) {
      var c = canon(s, s.seq);
      prev = sha(prev + "‖" + c);
      chain.push(prev);
      leaves.push(sha(c));
    });
    return { chain: chain, leaves: leaves, terminal: chain.length ? chain[chain.length - 1] : sha(HEADER), root: UI.merkleRoot(leaves), n: list.length };
  }

  function make(host, opts) {
    opts = opts || {};
    var hero = !!opts.hero;
    var nextId = 1;
    var items;
    var renumber = false;
    var committed = true;
    var sealed;
    var introDone = !hero || UI.reducedMotion();

    function fresh() {
      nextId = 1;
      items = DEFAULTS.map(function (d, i) {
        return { id: nextId++, seq0: i + 1, type: d.type, text: d.text, cost: d.cost, removed: false };
      });
    }

    function effective() {
      var out = [];
      items.forEach(function (it) {
        if (it.removed) return;
        out.push({ id: it.id, seq: renumber ? out.length + 1 : it.seq0, type: it.type, text: it.text, cost: it.cost });
      });
      return out;
    }

    fresh();
    sealed = build(effective());

    /* ---------- DOM ---------- */
    var rootNode = el("div", { class: "rx" + (hero ? " rx-hero" : "") });
    var commitChip = el("code", { class: "rx-hash" });
    var rootChip = el("code", { class: "rx-hash" });
    var commitBox = el(
      "div",
      { class: "rx-commit", "aria-label": "Commitment" },
      el("span", { class: "rx-label" }, "Commitment"),
      el("span", { class: "rx-kv" }, el("span", {}, "terminal hash "), commitChip),
      el("span", { class: "rx-kv" }, el("span", {}, "Merkle root "), rootChip)
    );

    var chainList = el("ol", { class: "rx-chain" });
    var verdict = el("div", { class: "rx-verdict", role: "status", "aria-live": "polite" });
    var note = el("p", { class: "rx-note" });

    var commitSwitch = el("input", { type: "checkbox", id: "rx-c-" + Math.random().toString(36).slice(2, 7), checked: true });
    var renumberSwitch = el("input", { type: "checkbox", id: "rx-r-" + Math.random().toString(36).slice(2, 7) });
    var controls = el(
      "div",
      { class: "rx-controls" },
      el("label", { class: "rx-toggle", for: commitSwitch.id }, commitSwitch, el("span", {}, "Receipt is committed")),
      el("label", { class: "rx-toggle", for: renumberSwitch.id }, renumberSwitch, el("span", {}, "Hide a gap by renumbering")),
      el("button", { type: "button", class: "rx-btn", onclick: function () { reset(); } }, "Reset"),
      hero ? el("button", { type: "button", class: "rx-btn rx-btn-primary", onclick: function () { demo(); } }, "Show me") : null
    );

    rootNode.appendChild(commitBox);
    rootNode.appendChild(chainList);
    rootNode.appendChild(verdict);
    rootNode.appendChild(controls);
    rootNode.appendChild(note);
    host.appendChild(rootNode);

    var cards = [];

    function structure() {
      chainList.textContent = "";
      cards = [];
      items.forEach(function (it, pos) {
        if (it.removed) {
          var ghost = el(
            "li",
            { class: "rx-step rx-ghost", "data-state": "ghost" },
            el("span", { class: "rx-ghost-text" }, "step " + it.seq0 + " removed"),
            el("button", { type: "button", class: "rx-mini", onclick: function () { it.removed = false; structure(); refresh(); } }, "Restore")
          );
          chainList.appendChild(ghost);
          cards.push({ item: it, node: ghost, ghost: true });
          return;
        }
        var seqNode = el("span", { class: "rx-seq" });
        var typeNode = el("span", { class: "rx-type" }, it.type);
        var text = el("input", {
          class: "rx-text",
          type: "text",
          value: it.text,
          maxlength: "46",
          spellcheck: "false",
          autocomplete: "off",
          "aria-label": "What step " + it.seq0 + " did",
          oninput: function (e) {
            it.text = e.target.value;
            refresh();
          },
        });
        var cost = el("input", {
          class: "rx-cost",
          type: "number",
          step: "0.01",
          min: "0",
          value: it.cost.toFixed(2),
          "aria-label": "Metered cost of step " + it.seq0 + ", in dollars",
          oninput: function (e) {
            var v = parseFloat(e.target.value);
            it.cost = isNaN(v) || v < 0 ? 0 : v;
            refresh();
          },
        });
        var hashNode = el("code", { class: "rx-hash" });
        var was = el("code", { class: "rx-was" });
        var left = el("button", { type: "button", class: "rx-mini", "aria-label": "Move step " + it.seq0 + " earlier", onclick: function () { move(pos, -1); } }, "◀");
        var right = el("button", { type: "button", class: "rx-mini", "aria-label": "Move step " + it.seq0 + " later", onclick: function () { move(pos, 1); } }, "▶");
        var del = el("button", { type: "button", class: "rx-mini", "aria-label": "Remove step " + it.seq0, onclick: function () { it.removed = true; structure(); refresh(); } }, "✕");
        var node = el(
          "li",
          { class: "rx-step", "data-state": "ok" },
          el("div", { class: "rx-row" }, seqNode, typeNode, el("span", { class: "rx-tools" }, left, right, del)),
          text,
          el("div", { class: "rx-row" }, el("span", { class: "rx-dollar" }, "$"), cost),
          el("div", { class: "rx-hashrow" }, hashNode, was)
        );
        chainList.appendChild(node);
        cards.push({ item: it, node: node, seqNode: seqNode, hashNode: hashNode, was: was, text: text });
      });
    }

    function move(pos, dir) {
      var to = pos + dir;
      if (to < 0 || to >= items.length) return;
      var t = items[pos];
      items[pos] = items[to];
      items[to] = t;
      structure();
      refresh();
    }

    function verify(cur, eff) {
      var issues = [];
      var i;
      for (i = 1; i < eff.length; i += 1) {
        if (eff[i].seq !== eff[i - 1].seq + 1) {
          issues.push(
            eff[i].seq < eff[i - 1].seq
              ? "Steps are out of order: step " + eff[i - 1].seq + " is followed by step " + eff[i].seq + "."
              : "Sequence numbers jump from " + eff[i - 1].seq + " to " + eff[i].seq + ". A gap is itself evidence of tampering."
          );
        }
      }
      var m = Math.min(cur.chain.length, sealed.chain.length);
      var first = -1;
      for (i = 0; i < m; i += 1) {
        if (cur.chain[i] !== sealed.chain[i]) {
          first = i;
          break;
        }
      }
      if (first < 0 && cur.chain.length !== sealed.chain.length) first = m;
      if (cur.n !== sealed.n) issues.push("The receipt has " + cur.n + " steps, but the commitment covers " + sealed.n + ".");
      if (first >= 0 && first < cur.n) {
        issues.push("The hash chain breaks at step " + eff[first].seq + ". Its hash no longer matches the commitment, and neither does any hash after it.");
      } else if (first >= 0) {
        issues.push("The chain ends early. Steps the commitment covers are missing.");
      }
      if (cur.terminal !== sealed.terminal) issues.push("The terminal hash differs from the signed commitment.");
      if (cur.root !== sealed.root) issues.push("The Merkle root differs from the committed root.");
      return { ok: issues.length === 0, issues: issues, first: first };
    }

    var lastOk = true;

    function refresh() {
      var eff = effective();
      var cur = build(eff);
      if (!committed) sealed = cur;
      var v = verify(cur, eff);

      commitChip.textContent = UI.short(sealed.terminal, 10);
      rootChip.textContent = UI.short(sealed.root, 10);

      var idx = 0;
      cards.forEach(function (c) {
        if (c.ghost) return;
        var h = cur.chain[idx];
        var sh = sealed.chain[idx];
        var bad = committed && (sh === undefined || h !== sh) && v.first >= 0 && idx >= v.first;
        c.seqNode.textContent = "s" + sub(eff[idx].seq);
        c.hashNode.textContent = "h" + sub(idx + 1) + " " + UI.short(h, 8);
        c.was.textContent = bad && sh ? "was " + UI.short(sh, 8) : "";
        c.node.setAttribute("data-state", bad ? "bad" : "ok");
        c.node.style.setProperty("--d", (idx * 70) + "ms");
        idx += 1;
      });

      var passMsg = "Chain intact. " + cur.n + " steps; the terminal hash and Merkle root match the commitment.";
      verdict.className = "rx-verdict " + (v.ok ? "ok" : "bad");
      verdict.textContent = "";
      verdict.appendChild(el("strong", { class: "rx-verdict-head" }, v.ok ? "PASS" : "FAIL"));
      if (v.ok) {
        verdict.appendChild(el("span", { class: "rx-verdict-body" }, passMsg));
      } else {
        verdict.appendChild(
          el("ul", { class: "rx-issues" }, v.issues.map(function (t) { return el("li", {}, t); }))
        );
      }

      if (!committed) {
        note.className = "rx-note warn";
        note.textContent =
          "Nothing is committed yet, so whoever runs the runtime can write any history and it will verify. This is why a receipt is only as good as the attestation behind it (paper sections 5.2 and 6.4).";
      } else if (v.ok && isFiction()) {
        note.className = "rx-note warn";
        note.textContent =
          "Valid, and not necessarily true. A hash chain proves a record was not changed after it was committed. It cannot prove the steps happened. Only attestation binds the record to real execution, and if that is broken only outside contradiction remains (paper sections 6.4 and 12.5).";
      } else {
        note.className = "rx-note";
        note.textContent =
          "Interactive model of paper section 6.2. The steps and costs are the paper's running example, and nothing here is measured. The hashes are real SHA-256, computed in your browser.";
      }

      if (lastOk !== v.ok) {
        rootNode.classList.remove("flash-ok", "flash-bad");
        void rootNode.offsetWidth;
        rootNode.classList.add(v.ok ? "flash-ok" : "flash-bad");
        lastOk = v.ok;
      }
    }

    /* After a re-commit the receipt may differ from the original, so say so once it is a different story. */
    function isFiction() {
      var eff = effective();
      if (eff.length !== DEFAULTS.length) return true;
      return eff.some(function (e, i) {
        return e.text !== DEFAULTS[i].text || Math.abs(e.cost - DEFAULTS[i].cost) > 1e-9 || e.type !== DEFAULTS[i].type;
      });
    }

    function reset() {
      fresh();
      renumber = false;
      committed = true;
      renumberSwitch.checked = false;
      commitSwitch.checked = true;
      sealed = build(effective());
      lastOk = true;
      structure();
      refresh();
    }

    commitSwitch.addEventListener("change", function () {
      committed = commitSwitch.checked;
      if (committed) sealed = build(effective());
      refresh();
    });
    renumberSwitch.addEventListener("change", function () {
      renumber = renumberSwitch.checked;
      refresh();
    });

    /* ---------- the guided moment ---------- */
    function demo() {
      reset();
      var target = cards.filter(function (c) { return !c.ghost; })[2];
      if (!target) return;
      var input = target.text;
      var from = "exit 1";
      var to = "exit 0";
      input.focus({ preventScroll: true });
      var i = from.length - 1;
      var step = function () {
        // Replace only the last character, the way a person would fix a failing test by editing the record.
        input.value = from.slice(0, i) + to.slice(i);
        target.item.text = input.value;
        refresh();
      };
      if (UI.reducedMotion()) return step();
      setTimeout(function () {
        input.value = from.slice(0, i);
        target.item.text = input.value;
        refresh();
        setTimeout(step, 420);
      }, 380);
    }

    /* ---------- the introduction ---------- */
    function scramble(node, final, ms) {
      if (UI.reducedMotion()) {
        node.textContent = final;
        return;
      }
      var start = performance.now();
      var chars = "0123456789abcdef";
      function frame(now) {
        var t = Math.min(1, (now - start) / ms);
        var out = "";
        for (var i = 0; i < final.length; i += 1) {
          out += final[i] === " " || i < final.length * t * 0.9 - 2 || t === 1 ? final[i] : chars[Math.floor(Math.random() * 16)];
        }
        node.textContent = out;
        if (t < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }

    function intro() {
      if (introDone) return;
      introDone = true;
      rootNode.classList.add("rx-intro");
      var nodes = chainList.children;
      for (var i = 0; i < nodes.length; i += 1) {
        (function (n, k) {
          n.style.setProperty("--i", String(k));
          var hash = n.querySelector(".rx-hash");
          var final = hash ? hash.textContent : "";
          if (hash) hash.textContent = "";
          setTimeout(function () {
            n.classList.add("in");
            if (hash) scramble(hash, final, 520);
          }, 260 + k * 230);
        })(nodes[i], i);
      }
      setTimeout(function () {
        rootNode.classList.add("sealed");
        rootNode.classList.remove("rx-intro");
      }, 260 + nodes.length * 230 + 500);
    }

    structure();
    refresh();
    if (hero && !UI.reducedMotion()) {
      rootNode.classList.add("rx-pre");
      UI.whenVisible(rootNode, function () {
        rootNode.classList.remove("rx-pre");
        introDone = false;
        intro();
      });
    }

    return { reset: reset, demo: demo, state: function () { return { items: items, sealed: sealed }; } };
  }

  UI.receipt = { mount: make, build: build, HEADER: HEADER, DEFAULTS: DEFAULTS };

  function auto() {
    document.querySelectorAll("[data-widget='receipt']").forEach(function (n) {
      make(n, { hero: false });
    });
    document.querySelectorAll("[data-widget='receipt-hero']").forEach(function (n) {
      make(n, { hero: true });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
  else auto();
})(window);

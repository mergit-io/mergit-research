/*
 * Shared helpers for the interactive parts of the research site.
 * Plain script, no dependencies. Everything hangs off window.MergitUI.
 */
(function (root) {
  "use strict";

  var UI = (root.MergitUI = root.MergitUI || {});

  var mq = root.matchMedia ? root.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  UI.reducedMotion = function () {
    return mq.matches;
  };

  /** Create an element: el("div", {class: "x", onclick: fn}, child, "text", ...). */
  UI.el = function (tag, attrs) {
    var node = document.createElementNS(
      tag === "svg" || tag === "g" || tag === "path" || tag === "line" || tag === "rect" || tag === "circle" || tag === "text" || tag === "polyline"
        ? "http://www.w3.org/2000/svg"
        : "http://www.w3.org/1999/xhtml",
      tag
    );
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) return;
        if (k.slice(0, 2) === "on" && typeof v === "function") node.addEventListener(k.slice(2), v);
        else if (k === "class") node.setAttribute("class", v);
        else if (k === "text") node.textContent = v;
        else node.setAttribute(k, v === true ? "" : String(v));
      });
    }
    function add(c) {
      if (c === null || c === undefined || c === false) return;
      if (Array.isArray(c)) return c.forEach(add);
      node.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
    }
    for (var i = 2; i < arguments.length; i += 1) add(arguments[i]);
    return node;
  };

  /* ---------- SHA-256 (synchronous, UTF-8 input, hex output) ---------- */
  var K = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ]);

  function utf8(str) {
    if (typeof TextEncoder !== "undefined") return new TextEncoder().encode(str);
    var s = unescape(encodeURIComponent(str));
    var out = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i += 1) out[i] = s.charCodeAt(i);
    return out;
  }

  function rotr(x, n) {
    return (x >>> n) | (x << (32 - n));
  }

  UI.sha256 = function (str) {
    var data = utf8(str);
    var len = data.length;
    var padded = new Uint8Array(((len + 9 + 63) >> 6) << 6);
    padded.set(data);
    padded[len] = 0x80;
    var bits = len * 8;
    var view = new DataView(padded.buffer);
    view.setUint32(padded.length - 8, Math.floor(bits / 4294967296), false);
    view.setUint32(padded.length - 4, bits >>> 0, false);

    var h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    var w = new Uint32Array(64);
    for (var off = 0; off < padded.length; off += 64) {
      var t;
      for (t = 0; t < 16; t += 1) w[t] = view.getUint32(off + t * 4, false);
      for (t = 16; t < 64; t += 1) {
        var s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        var s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
      }
      var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
      for (t = 0; t < 64; t += 1) {
        var S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (hh + S1 + ch + K[t] + w[t]) >>> 0;
        var S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) >>> 0;
        hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0; h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
      h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0; h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
    }
    var hex = "";
    for (var i = 0; i < 8; i += 1) hex += ("00000000" + h[i].toString(16)).slice(-8);
    return hex;
  };

  /** Merkle root over hex leaf hashes. An odd node at any level is paired with itself. */
  UI.merkleRoot = function (leaves) {
    if (!leaves.length) return UI.sha256("");
    var level = leaves.slice();
    while (level.length > 1) {
      var next = [];
      for (var i = 0; i < level.length; i += 2) {
        var left = level[i];
        var right = i + 1 < level.length ? level[i + 1] : level[i];
        next.push(UI.sha256(left + right));
      }
      level = next;
    }
    return level[0];
  };

  /* ---------- seeded randomness and distributions (for the routing simulation) ---------- */
  UI.rng = function (seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  function normal(rng) {
    var u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }

  /** Gamma(shape, rate), by Marsaglia and Tsang. */
  UI.gamma = function (rng, shape, rate) {
    if (shape < 1) {
      var u = rng();
      return UI.gamma(rng, shape + 1, rate) * Math.pow(u, 1 / shape);
    }
    var d = shape - 1 / 3;
    var c = 1 / Math.sqrt(9 * d);
    for (;;) {
      var x = normal(rng);
      var v = 1 + c * x;
      if (v <= 0) continue;
      v = v * v * v;
      var u2 = rng();
      if (u2 < 1 - 0.0331 * x * x * x * x) return (d * v) / rate;
      if (Math.log(u2) < 0.5 * x * x + d * (1 - v + Math.log(v))) return (d * v) / rate;
    }
  };

  UI.beta = function (rng, a, b) {
    var x = UI.gamma(rng, a, 1);
    var y = UI.gamma(rng, b, 1);
    return x / (x + y);
  };

  /* ---------- small formatting helpers ---------- */
  UI.short = function (hex, n) {
    return hex.slice(0, n || 8);
  };
  UI.clamp = function (x, lo, hi) {
    return Math.min(hi, Math.max(lo, x));
  };
  UI.pct = function (x) {
    var p = x * 100;
    return (p >= 10 ? p.toFixed(0) : String(parseFloat(p.toPrecision(3)))) + "%";
  };
  UI.money = function (x) {
    if (x === 0) return "$0";
    return x >= 1 ? "$" + x.toFixed(2) : "$" + String(parseFloat(x.toPrecision(2)));
  };

  /** Run fn when the element first comes near the viewport (or at once without IntersectionObserver). */
  UI.whenVisible = function (node, fn) {
    if (!("IntersectionObserver" in root)) return fn();
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) {
        io.disconnect();
        fn();
      }
    }, { rootMargin: "0px 0px -15% 0px" });
    io.observe(node);
  };

  if (typeof module !== "undefined" && module.exports) module.exports = UI;
})(typeof window !== "undefined" ? window : globalThis);

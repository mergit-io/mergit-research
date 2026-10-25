/*
 * The audit-rate arithmetic of the Mergit paper, section 7.2 and section 7.5.
 *
 * Pure functions, no DOM, so the page and the test use the same code. Everything here is
 * arithmetic on the paper's model. Nothing is measured: Mergit is pre-implementation.
 *
 *   forgery gain        g(theta)  = max(c_exec + (1 - theta)V, V)      (after-execution case)
 *   required detection  p_req     = g / (V + lambda S)
 *   audit rate          p         = (p_req - q) / (1 - q)               (challenge rate q)
 *   concurrency (7.5)   n (g - P_d V)  <=  lambda S [1 - (1 - P_d)^n]
 */
(function (root) {
  "use strict";

  /**
   * Gain from forging a receipt at the binding moment. With `agentSeesPredicate` false only the
   * before-execution case applies; the paper states the stronger case as the conservative one.
   */
  function forgeryGain(i) {
    const before = i.cExec + (1 - i.theta) * i.V;
    return i.agentSeesPredicate ? Math.max(before, i.V) : before;
  }

  /** Detection probability P_d needed so that forging is not profitable. */
  function requiredDetection(i) {
    return forgeryGain(i) / (i.V + i.lambda * i.S);
  }

  /** Routine audit rate p once challenge (rate q) does part of the work. Null if p_req > 1. */
  function auditRate(pReq, q) {
    if (pReq > 1) return null;
    if (q >= 1) return 0;
    return Math.max(0, (pReq - q) / (1 - q));
  }

  /** Detection probability when audited with probability p and challenged with probability q. */
  function detection(p, q) {
    return p + (1 - p) * q;
  }

  /** Smallest stake that makes an audit rate of at most pMax sufficient (Rule 1). */
  function minStake(i, pMax) {
    return Math.max(0, (forgeryGain(i) / pMax - i.V) / i.lambda);
  }

  /** Does defecting on n simultaneous receipts fail to pay at detection probability Pd? */
  function concurrencySafe(n, g, Pd, V, lambda, S) {
    return n * (g - Pd * V) <= lambda * S * (1 - Math.pow(1 - Pd, n)) + 1e-12;
  }

  /** Largest n for which the exact condition holds; Infinity when forging never pays. */
  function exactMaxConcurrent(g, Pd, V, lambda, S) {
    if (g - Pd * V <= 0) return Infinity;
    let n = 0;
    while (n < 100000 && concurrencySafe(n + 1, g, Pd, V, lambda, S)) n += 1;
    return n;
  }

  /** The earlier, wrong bound that charges the slash as certain. Kept to show the difference. */
  function naiveMaxConcurrent(g, Pd, V, lambda, S) {
    const d = g - Pd * V;
    return d <= 0 ? Infinity : Math.floor((lambda * S) / d);
  }

  /**
   * Smallest routine audit rate that keeps an allowance of nCap simultaneous receipts safe.
   * The inequality is monotone in P_d, so bisection finds the boundary. Null when no rate works.
   */
  function rateForConcurrency(i, nCap) {
    const g = forgeryGain(i);
    const ok = (Pd) => concurrencySafe(nCap, g, Pd, i.V, i.lambda, i.S);
    if (!ok(1)) return null;
    let lo = 0;
    let hi = 1;
    for (let k = 0; k < 80; k += 1) {
      const mid = (lo + hi) / 2;
      if (ok(mid)) hi = mid;
      else lo = mid;
    }
    const Pd = hi;
    return i.q >= 1 ? 0 : Math.max(0, (Pd - i.q) / (1 - i.q));
  }

  const api = {
    forgeryGain,
    requiredDetection,
    auditRate,
    detection,
    minStake,
    concurrencySafe,
    exactMaxConcurrent,
    naiveMaxConcurrent,
    rateForConcurrency,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.MergitAudit = api;
})(typeof window !== "undefined" ? window : globalThis);

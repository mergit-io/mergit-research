/*
 * Checks core.js against the numbers printed in the paper (section 7.2, 7.4, 7.5).
 * Run:  node site/calculator/test.js
 * A failure means either this code or the paper's table is wrong, and the output says which row.
 */
const m = require("./core.js");

let failures = 0;
function check(label, got, want, tol) {
  const ok = got !== null && Math.abs(got - want) <= tol;
  if (!ok) failures += 1;
  console.log(`${ok ? "ok  " : "FAIL"}  ${label}: got ${got === null ? "null" : got.toFixed(5)}, paper ${want}`);
}

const base = { V: 2, cExec: 1, theta: 0.95, lambda: 1, q: 0, agentSeesPredicate: true };
const at = (S, extra) => ({ ...base, S, ...extra });
const p = (i) => m.auditRate(m.requiredDetection(i), i.q);

// 7.4 table and text
check("forgery gain g", m.forgeryGain(at(30)), 2, 1e-9);
check("p* at S=$30", p(at(30)), 0.0625, 5e-5);
check("p* at S=$300", p(at(300)), 0.0066, 5e-5);
check("p* at S=$5", p(at(5)), 0.286, 5e-4);
check("p* theta=0.2 S=$30", p(at(30, { theta: 0.2 })), 0.081, 5e-4);
check("p* theta=0.2 S=$5", p(at(5, { theta: 0.2 })), 0.371, 5e-4);
check("p* theta=0.6 S=$30", p(at(30, { theta: 0.6 })), 0.0625, 5e-5);
check("p* theta=0.6 S=$5", p(at(5, { theta: 0.6 })), 0.286, 5e-4);
check("expected audit cost S=$30 (c_audit 0.02)", 0.02 * p(at(30)), 0.00125, 1e-6);
check("expected audit cost S=$300", 0.02 * p(at(300)), 0.00013, 1e-5);

// Rule 2: challenge alone suffices at q >= p_req
check("challenge threshold q", m.requiredDetection(at(30)), 0.0625, 5e-5);
check("p at q = threshold", p(at(30, { q: 0.0625 })), 0, 1e-9);

// 7.5(ii): the exact bound against the earlier one, at g = 1.10 and P_d = 0.05
check("exact n_max (g=1.1, Pd=0.05, S=30)", m.exactMaxConcurrent(1.1, 0.05, 2, 1, 30), 18, 0);
check("naive n_max (g=1.1, Pd=0.05, S=30)", m.naiveMaxConcurrent(1.1, 0.05, 2, 1, 30), 30, 0);

// 7.5(ii) table: audit rate sized for the allowance, g = $2
const table = { 5: [0.514, 0.75, 0.9], 30: [0.0714, 0.0892, 0.4], 300: [0.0067, 0.0068, 0.0072] };
for (const S of [5, 30, 300]) {
  [5, 10, 25].forEach((n, k) => {
    check(`rate for n_cap=${n} at S=$${S}`, m.rateForConcurrency(at(S), n), table[S][k], 6e-4);
  });
}

// at exactly the one-shot rate any n >= 2 is profitable (paper, 7.5(ii))
const g = m.forgeryGain(at(30));
const Pd = g / (2 + 30);
check("n=1 safe at one-shot rate", m.concurrencySafe(1, g, Pd, 2, 1, 30) ? 1 : 0, 1, 0);
check("n=2 unsafe at one-shot rate", m.concurrencySafe(2, g, Pd, 2, 1, 30) ? 1 : 0, 0, 0);

console.log(failures === 0 ? "\nall checks match the paper" : `\n${failures} mismatch(es)`);
process.exit(failures === 0 ? 0 : 1);

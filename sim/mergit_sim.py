"""Agent-based simulation of the deterrence mechanism of draft-v1 section 7.

Model-based simulation, not a measurement of a deployed system. Every quantity
it produces is a consequence of the assumptions stated here and in README.md.

Units: money in USD, time in discrete steps. One step is the time an agent needs
to execute one task; a receipt stays unresolved (inside its audit/challenge
window) for W steps after submission.

The module has two parts.

1. Closed-form quantities from the paper (sections 7.2, 7.4, 7.5) and the
   corrections this simulation motivates (exact batch condition, ex-post
   "fake on failure" deviation). These are used by the mechanisms and by the
   unit checks in test_analytics.py.
2. A vectorised simulator. One call simulates R independent replicates of a
   single agent (one strategy, one mechanism, one parameter set). Agents do not
   interact, so a population is a set of independent calls.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy.special import betaincinv
from scipy.stats import binom

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Params:
    """Platform and economic parameters. Defaults are the section 7.4 example."""

    V: float = 2.0  # task payment
    c_exec: float = 1.0  # cost of honest execution
    c_audit: float = 0.02  # cost of one Level 1 audit (paid by the platform)
    S: float = 30.0  # posted stake
    lam: float = 1.0  # slashing fraction per detection event
    q: float = 0.0  # true P(unaudited false receipt is successfully challenged)
    q_assumed: float = 0.0  # challenge rate the mechanism assumes when setting p
    gamma: float = 0.95  # posterior decay (section 8.2)
    alpha0: float = 1.0  # Beta prior (section 8.6: (1, 1))
    beta0: float = 1.0
    lcb_quantile: float = 0.05  # theta_LCB = this quantile of Beta(alpha, beta)
    W: int = 5  # audit/challenge window, steps
    rate: int = 1  # tasks requested per step in normal operation
    H: int = 1000  # horizon, steps
    theta_nominal: float = 0.95  # M0 sets p at this platform-average theta
    obs_rule: str = "audited"  # "audited" | "literal" (see README)
    probation_steps: int = 100  # M3/M4: base probation length, doubles per offence
    n_allow: int = 5  # M4: concurrency allowance the audit rate is sized for


@dataclass(frozen=True)
class Mechanism:
    name: str
    rate_rule: str  # "fixed" (M0) | "lcb" (M1-M3) | "corrected" (M4)
    cap: str  # "none" | "paper" | "exact"
    probation: bool
    sweep: bool = False  # on proven falsification, audit every unresolved receipt


MECHANISMS = {
    "M0": Mechanism("M0", "fixed", "none", False),
    "M1": Mechanism("M1", "lcb", "none", False),
    "M2": Mechanism("M2", "lcb", "paper", False),
    "M3": Mechanism("M3", "lcb", "paper", True),
    "M4": Mechanism("M4", "corrected", "exact", True),
}


@dataclass(frozen=True)
class Strategy:
    """kind:
    honest     execute every task, report the true outcome
    occasional falsify each receipt w.p. eps (without executing), else honest
    volume     honest until t_switch, idle W steps (let receipts resolve), then
               take n_attack tasks in one step, falsify all, exit
    exit       honest until t_switch, then falsify every receipt until H
    fof        "fake on failure": execute honestly; if Phi fails, submit a
               false success receipt instead of the failure
    falsifier  never execute; submit a false success receipt for every task
    Deviating strategies behave honestly while on probation (p = 1), since a
    false receipt is then detected with certainty.
    """

    name: str
    theta: float
    kind: str
    eps: float = 0.1
    t_switch: int = 500
    n_attack: object = 100  # int or int array of shape (R,)


# ---------------------------------------------------------------------------
# Closed forms (paper) and corrections
# ---------------------------------------------------------------------------


def gain_pure(theta, P: Params):
    """Per-task gain of falsifying instead of executing (section 7.2 numerator)."""
    return P.c_exec + (1.0 - np.asarray(theta, float)) * P.V


def p_star(theta, P: Params, q=None):
    """Section 7.2 required audit rate, with Rule 2 when q > 0."""
    q = P.q_assumed if q is None else q
    p_req = gain_pure(theta, P) / (P.V + P.lam * P.S)
    return np.clip((p_req - q) / (1.0 - q), 0.0, 1.0)


def n_max_paper(theta, P_d, P: Params):
    """Section 7.5(ii): lam S / [(c_exec + (1-theta) V) - P_d V]; inf if bracket <= 0."""
    bracket = gain_pure(theta, P) - np.asarray(P_d, float) * P.V
    with np.errstate(divide="ignore"):
        return np.where(bracket > 0, P.lam * P.S / np.where(bracket > 0, bracket, 1.0), np.inf)


def expected_slash(n, P_d, P: Params):
    """E[total slash] when n false receipts are each detected w.p. P_d independently.

    Each detection slashes lam*S, bounded by the stake that remains, and the
    stake is shared by all n receipts: total = S * min(K * lam, 1), K ~ Bin(n, P_d).
    """
    n = np.asarray(n)
    P_d = np.asarray(P_d, float)
    J = int(np.ceil(1.0 / P.lam - 1e-12))
    tot = 0.0
    for j in range(1, J + 1):
        w = min(P.lam, max(0.0, 1.0 - (j - 1) * P.lam))
        tot = tot + w * binom.sf(j - 1, n, P_d)
    return P.S * tot


def batch_gain(n, theta, P_d, P: Params, G=None):
    """Expected gain of falsifying n simultaneous receipts vs. executing them honestly.

    G is the per-receipt gross gain: c_exec + (1-theta)V for pure falsification
    (default), V for fake-on-failure receipts. The paper's 7.5(ii) charges the
    slash lam*S with certainty; the exact penalty charges it only if at least
    one receipt is detected.
    """
    G = gain_pure(theta, P) if G is None else G
    n = np.asarray(n, float)
    return n * (G - P_d * P.V) - expected_slash(n.astype(int), P_d, P)


def n_star_exact(theta, P_d, P: Params, G=None, n_hi=100000):
    """Largest n for which falsifying n simultaneous receipts is not profitable.

    batch_gain is convex in n with batch_gain(0) = 0, so the safe set is {0..n*}.
    """
    lo, hi = 0, 1
    while hi < n_hi and batch_gain(hi, theta, P_d, P, G) <= 1e-12:
        lo, hi = hi, hi * 2
    if hi >= n_hi:
        return np.inf
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if batch_gain(mid, theta, P_d, P, G) <= 1e-12:
            lo = mid
        else:
            hi = mid
    return lo


def p_fake_on_failure(P: Params):
    """Required detection probability against the ex-post deviation.

    After a failed honest attempt c_exec is sunk; reporting the failure pays 0,
    a false success receipt pays (1-P_d)V - P_d lam S. Deterred iff
    P_d >= V / (V + lam S), independent of theta.
    """
    return P.V / (P.V + P.lam * P.S)


@lru_cache(maxsize=None)
def _p_joint_table(V, S, lam, n_allow, q_assumed):
    """Tabulate p_joint(G) on a grid of G for M4."""
    P = Params(V=V, S=S, lam=lam, n_allow=n_allow, q_assumed=q_assumed)
    Gs = np.linspace(0.0, 3.0 * V, 601)
    ps = np.empty_like(Gs)
    ms = np.arange(1, n_allow + 1)
    for i, G in enumerate(Gs):

        def ok(p):
            Pd = p + (1 - p) * q_assumed
            return np.all(ms * (G - Pd * V) - expected_slash(ms, Pd, P) <= 1e-12)

        if ok(0.0):
            ps[i] = 0.0
            continue
        if not ok(1.0):
            ps[i] = 1.0
            continue
        lo, hi = 0.0, 1.0
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            lo, hi = (lo, mid) if ok(mid) else (mid, hi)
        ps[i] = hi
    return Gs, ps


def p_joint(G, P: Params):
    """Smallest audit rate at which n_allow simultaneous false receipts, each with
    gross gain G, are unprofitable under the exact (binomial) penalty. Clipped at 1."""
    Gs, ps = _p_joint_table(P.V, P.S, P.lam, P.n_allow, P.q_assumed)
    return np.interp(G, Gs, ps)


def corrected_gain(theta_lcb, P: Params):
    """M4 per-receipt gain: max(c_exec + (1-theta_LCB)V, V), i.e. the paper's
    numerator with theta_LCB clamped at c_exec/V."""
    return np.maximum(gain_pure(theta_lcb, P), P.V)


def theta_lcb(alpha, beta, quantile):
    return betaincinv(alpha, beta, quantile)


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------


def _schedule(strategy: Strategy, P: Params, R: int):
    """Tasks requested per step, shape (T, R), and the step after which the agent exits."""
    if strategy.kind == "volume":
        n_att = np.broadcast_to(np.asarray(strategy.n_attack, int), (R,))
        t_att = strategy.t_switch + P.W
        T = t_att + 1
        sched = np.full((T, R), P.rate, int)
        sched[strategy.t_switch : t_att] = 0
        sched[t_att] = n_att
        return sched, t_att
    return np.full((P.H, R), P.rate, int), P.H - 1


def simulate(strategy: Strategy, mech: Mechanism, P: Params, R: int, seed: int,
             honest: bool = False, record: bool = False):
    """Simulate R replicates. With honest=True the same agent (same theta, same
    task schedule, same random numbers) plays honestly: the counterfactual
    against which deviation gain is measured."""
    kind = "honest" if honest else strategy.kind
    th = strategy.theta
    V, c, S, lam, W = P.V, P.c_exec, P.S, P.lam, P.W
    sched, t_exit = _schedule(strategy, P, R)
    T = sched.shape[0]
    t_attack = strategy.t_switch + W if strategy.kind == "volume" else -1

    alpha = np.full(R, P.alpha0)
    beta = np.full(R, P.beta0)
    thL = theta_lcb(alpha, beta, P.lcb_quantile)
    stake = np.full(R, S)
    prob_until = np.zeros(R, int)
    fraud = np.zeros(R, int)
    inflight = np.zeros((W, R), int)
    pend_false = np.zeros((W, R), int)  # unaudited false receipts still in window
    pend_chal = np.zeros((W, R), int)  # of which a challenger will catch

    pay = np.zeros(R)
    cost = np.zeros(R)
    slashed = np.zeros(R)
    n_tasks = np.zeros(R)
    n_audits = np.zeros(R)
    n_false = np.zeros(R)
    n_false_undet = np.zeros(R)
    n_detect = np.zeros(R)
    n_refused = np.zeros(R)
    attack_taken = np.zeros(R)
    attack_p = np.full(R, np.nan)
    attack_thL = np.full(R, np.nan)
    attack_cap = np.full(R, np.nan)
    hist_p = np.empty((T, R)) if record else None
    hist_thL = np.empty((T, R)) if record else None

    p_fixed = float(np.clip(gain_pure(P.theta_nominal, P) / (V + lam * S), 0, 1))
    p_fixed = float(np.clip((p_fixed - P.q_assumed) / (1 - P.q_assumed), 0, 1))
    honest_only = kind == "honest"

    def detect(mask_counts, t):
        """Consequences of detection events (counts per replicate)."""
        nonlocal stake, alpha, beta, thL
        d = mask_counts
        if not np.any(d):
            return
        amt = np.minimum(d * lam * S, stake)
        stake = stake - amt
        slashed[:] += amt
        n_detect[:] += d
        _update(np.zeros(R, int), d)
        if mech.probation:
            hit = d > 0
            fraud[hit] += 1
            prob_until[hit] = t + 1 + P.probation_steps * 2 ** (fraud[hit] - 1)

    def _update(s, f):
        nonlocal alpha, beta, thL
        m = s + f
        upd = m > 0
        if not np.any(upd):
            return
        g = P.gamma ** m[upd]
        w = np.where(P.gamma < 1, (1 - g) / (m[upd] * (1 - P.gamma)), 1.0)
        alpha[upd] = g * alpha[upd] + s[upd] * w
        beta[upd] = g * beta[upd] + f[upd] * w
        thL[upd] = theta_lcb(alpha[upd], beta[upd], P.lcb_quantile)

    for t in range(T + W):
        slot = t % W
        # 1. receipts submitted at t-W leave the window; challenges resolve.
        d = pend_chal[slot].copy()
        undet = pend_false[slot] - d
        n_false_undet[:] += undet
        pay[:] -= V * d  # refund to requester
        pend_false[slot] = 0
        pend_chal[slot] = 0
        inflight[slot] = 0
        detect(d, t)
        if mech.sweep and np.any(d):
            _sweep(d > 0, pend_false, pend_chal, pay, V, detect, t, R)

        if t >= T:
            continue

        # 2. audit rate and concurrency cap for this step.
        if mech.rate_rule == "fixed":
            p = np.full(R, p_fixed)
        elif mech.rate_rule == "lcb":
            p = p_star(thL, P)
        else:
            p = p_joint(corrected_gain(thL, P), P)
        p = np.where(t < prob_until, 1.0, p)
        if mech.cap == "none":
            cap = np.full(R, np.inf)
        elif mech.cap == "paper":
            Pd_assumed = p + (1 - p) * P.q_assumed
            cap = np.floor(n_max_paper(thL, Pd_assumed, P) + 1e-9)
        else:
            cap = np.full(R, float(P.n_allow))
        if record:
            hist_p[t] = p
            hist_thL[t] = thL

        k_req = sched[t]
        busy = inflight.sum(0)
        avail = np.maximum(cap - busy, 0)
        k = np.minimum(k_req, avail).astype(int)
        n_refused[:] += k_req - k
        K = int(k_req.max())
        if t == t_attack:
            attack_taken[:] = k
            attack_p[:] = p
            attack_thL[:] = thL
            attack_cap[:] = cap
        if K == 0:
            continue

        # 3. per-slot random numbers: indexed by (seed, t), shape fixed by the
        #    schedule, so a strategy and its honest counterfactual share them.
        u = np.random.default_rng([seed, t]).random((4, R, K))
        u_s, u_a, u_c, u_d = u
        mask = np.arange(K)[None, :] < k[:, None]
        can_dev = (p < 1.0)[:, None] & mask

        if honest_only:
            fals = np.zeros((R, K), bool)
            execd = mask
        elif kind == "occasional":
            fals = can_dev & (u_d < strategy.eps)
            execd = mask & ~fals
        elif kind == "volume":
            fals = can_dev if t == t_attack else np.zeros((R, K), bool)
            execd = mask & ~fals
        elif kind == "exit":
            fals = can_dev if t >= strategy.t_switch else np.zeros((R, K), bool)
            execd = mask & ~fals
        elif kind == "falsifier":
            fals = can_dev
            execd = np.zeros((R, K), bool)  # abstains (submits nothing) on probation
        elif kind == "fof":
            execd = mask
            fals = can_dev & ~(u_s < th)
        else:
            raise ValueError(kind)

        succ = execd & (u_s < th)
        fals = fals & ~succ  # a fake-on-failure receipt only replaces a failure
        claim = succ | fals
        fail_rep = execd & ~succ & ~fals
        audited = mask & (u_a < p[:, None])
        if P.obs_rule == "literal":
            audited = audited & claim  # failure reports are observed, not audited
        det = fals & audited
        chal = fals & ~audited & (u_c < P.q)

        cost[:] += c * execd.sum(1)
        pay[:] += V * (claim & ~det).sum(1)
        n_tasks[:] += k
        n_audits[:] += audited.sum(1)
        n_false[:] += fals.sum(1)
        inflight[slot] = k
        pend_false[slot] = (fals & ~audited).sum(1)
        pend_chal[slot] = chal.sum(1)

        s_obs = (succ & audited).sum(1)
        if P.obs_rule == "literal":
            f_obs = fail_rep.sum(1)
        else:
            f_obs = (fail_rep & audited).sum(1)
        _update(s_obs, f_obs)
        nd = det.sum(1)
        detect(nd, t)
        if mech.sweep and np.any(nd):
            _sweep(nd > 0, pend_false, pend_chal, pay, V, detect, t, R)

        # 4. a continuing agent re-collateralises to S; an exited one does not.
        if t < t_exit:
            stake = np.full(R, S)

    profit = pay - cost - slashed
    out = dict(profit=profit, pay=pay, cost=cost, slashed=slashed, tasks=n_tasks,
               audits=n_audits, false=n_false, false_undet=n_false_undet,
               detections=n_detect, refused=n_refused, attack_taken=attack_taken,
               attack_p=attack_p, attack_thL=attack_thL, attack_cap=attack_cap,
               alpha=alpha, beta=beta, thL=thL)
    if record:
        out["hist_p"] = hist_p
        out["hist_thL"] = hist_thL
    return out


def _sweep(hit, pend_false, pend_chal, pay, V, detect, t, R):
    """Retroactive audit of every unresolved false receipt of a caught agent."""
    extra = np.where(hit, pend_false.sum(0), 0)
    if not np.any(extra):
        return
    pay[:] -= V * extra
    pend_false[:, hit] = 0
    pend_chal[:, hit] = 0
    detect(extra, t)


def deviation(strategy: Strategy, mech: Mechanism, P: Params, R: int, seed: int,
              record: bool = False):
    """Run a strategy and its honest counterfactual on common random numbers.

    Deviation gain = profit(strategy) - profit(best compliant alternative), where
    the alternative is honest play over the same schedule if theta V >= c_exec
    and abstention (profit 0) otherwise. No continuation value is credited
    (section 7.5(i)): the counterfactual exits when the strategy does.
    """
    dev = simulate(strategy, mech, P, R, seed, honest=False, record=record)
    hon = simulate(strategy, mech, P, R, seed, honest=True, record=False)
    base = hon["profit"] if strategy.theta * P.V >= P.c_exec else np.zeros(R)
    dev["gain"] = dev["profit"] - base
    dev["honest_profit"] = hon["profit"]
    dev["honest_tasks"] = hon["tasks"]
    return dev


def mean_ci(x, z=1.959964):
    x = np.asarray(x, float)
    m = x.mean()
    se = x.std(ddof=1) / np.sqrt(len(x))
    return m, m - z * se, m + z * se


def with_(P: Params, **kw) -> Params:
    return replace(P, **kw)

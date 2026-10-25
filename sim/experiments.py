"""Runs experiments E1-E4 and writes results/*.csv and figures/*.pdf|png.

    python experiments.py            # all experiments
    python experiments.py e1 e3      # a subset
    python experiments.py --quick    # fewer seeds, for a smoke test

Model-based simulation of draft-v1 section 7; no output is a measurement.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from mergit_sim import (MECHANISMS, Mechanism, Params, Strategy,  # noqa: E402
                        batch_gain, deviation, gain_pure, mean_ci, n_max_paper,
                        n_star_exact, p_fake_on_failure, p_star, simulate, with_)

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
SEED = 20261024
QUICK = "--quick" in sys.argv
WORKERS = int(os.environ.get("SIM_WORKERS", "6"))

BASE = Params()  # section 7.4: V=2, c_exec=1, lam=1, c_audit=0.02, S=30, q=0
STAKES = (5.0, 30.0, 300.0)
LAMS = (1.0, 0.5)
QS = (0.0, 0.034, 0.1)

STRATEGIES = [
    Strategy("honest", 0.95, "honest"),
    Strategy("occasional defector", 0.95, "occasional", eps=0.1),
    Strategy("volume attacker", 0.95, "volume", t_switch=500, n_attack=10**6),
    Strategy("patient exit scammer", 0.95, "exit", t_switch=500),
    Strategy("fake-on-failure θ=0.6", 0.6, "fof"),
    Strategy("falsifier θ=0.2", 0.2, "falsifier"),
    Strategy("fake-on-failure θ=0.95", 0.95, "fof"),
]


def strategy_for(si, P):
    """The volume attacker requests 3x the section 7.5 n_max at theta = 0.95, P_d = p*."""
    st = STRATEGIES[si]
    if st.kind == "volume":
        return replace(st, n_attack=int(np.ceil(3 * (P.V + P.lam * P.S) / 1.1)))
    return st
MECH_ORDER = ["M0", "M1", "M2", "M3", "M4"]

# ---------------------------------------------------------------- style
# Matplotlib defaults as in paper/figures/fig_audit_rate.py, sized for a
# single column (3.4 in). Mechanism colours: a categorical palette checked
# for colour-vision-deficiency separation, in fixed order; every series also
# carries a distinct marker/linestyle so identity is never colour alone.
COL = {"M0": "#2a78d6", "M1": "#eb6834", "M2": "#1baf7a", "M3": "#eda100",
       "M4": "#e87ba4", "M3+sweep": "#6250d6"}
MARK = {"M0": "o", "M1": "s", "M2": "^", "M3": "D", "M4": "v", "M3+sweep": "P"}
LS = {"M0": "-", "M1": "-", "M2": "--", "M3": "-.", "M4": ":", "M3+sweep": (0, (5, 1, 1, 1))}
LABEL = {"M0": "M0 memoryless", "M1": "M1 posterior rate", "M2": "M2 + paper cap",
         "M3": "M3 + probation", "M4": "M4 corrected", "M3+sweep": "M3 + retro-audit"}
INK = "#52514e"
plt.rcParams.update({"font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
                     "lines.linewidth": 1.4, "pdf.fonttype": 42})
W1 = 3.4  # single-column width, inches


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf/.png")


def write_csv(name, rows):
    path = os.path.join(RES, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})
    print(f"  wrote results/{name} ({len(rows)} rows)")


def pmap(fn, jobs):
    if WORKERS <= 1:
        return [fn(j) for j in jobs]
    with ProcessPoolExecutor(WORKERS) as ex:
        return list(ex.map(fn, jobs, chunksize=1))


def mech(name):
    if name == "M3+sweep":
        return Mechanism("M3+sweep", "lcb", "paper", True, sweep=True)
    return MECHANISMS[name]


def summarise(out, P):
    g = mean_ci(out["gain"])
    tasks = out["tasks"].sum()
    return dict(gain_mean=g[0], gain_lo=g[1], gain_hi=g[2],
                gain_per_task=out["gain"].sum() / max(tasks, 1),
                requester_loss_per_task=P.V * out["false_undet"].sum() / max(tasks, 1),
                audit_cost_per_task=P.c_audit * out["audits"].sum() / max(tasks, 1),
                audit_rate_realized=out["audits"].sum() / max(tasks, 1),
                tasks_mean=out["tasks"].mean(), honest_tasks_mean=out["honest_tasks"].mean(),
                refused_mean=out["refused"].mean(), detections_mean=out["detections"].mean(),
                false_receipts_mean=out["false"].mean())


# ====================================================================== E1
ALL = 10**9  # sentinel: request as many concurrent tasks as the mechanism allows

def _e1_job(job):
    S, lam, q, mname, ns, R, seed, t_build = job
    P = with_(BASE, S=S, lam=lam, q=q)
    rows = []
    # chunk n values so the attack-step random array stays small
    chunks, cur, load = [], [], 0
    for n in ns:
        if cur and load + min(n, 400) * R > 1_500_000:
            chunks.append(cur)
            cur, load = [], 0
        cur.append(n)
        load += min(n, 400) * R
    chunks.append(cur)
    n_all = int(np.ceil(P.V + P.lam * P.S)) + 1  # >= any cap: "as many as allowed"
    for ci, chunk in enumerate(chunks):
        flags = [n == ALL for n in chunk]
        chunk = [n_all if n == ALL else int(n) for n in chunk]
        n_arr = np.repeat(np.array(chunk), R)
        st = Strategy("volume", 0.95, "volume", t_switch=t_build, n_attack=n_arr)
        out = deviation(st, mech(mname), P, R=len(n_arr), seed=seed + 7919 * ci)
        for i, (n, flag) in enumerate(zip(chunk, flags)):
            sl = slice(i * R, (i + 1) * R)
            g = mean_ci(out["gain"][sl])
            pa, tl = np.median(out["attack_p"][sl]), np.median(out["attack_thL"][sl])
            Pd = pa + (1 - pa) * q
            rows.append(dict(
                S=S, lam=lam, q=q, mechanism=mname, build_steps=t_build, n_requested=int(n),
                all_allowed=bool(flag),
                n_taken_mean=float(out["attack_taken"][sl].mean()),
                gain_mean=g[0], gain_lo=g[1], gain_hi=g[2],
                requester_loss_mean=P.V * float(out["false_undet"][sl].mean()),
                p_attack_median=float(pa), thetaLCB_attack_median=float(tl),
                cap_median=float(np.median(out["attack_cap"][sl])),
                n_max_paper_at_median=float(n_max_paper(tl, pa, P)),
                n_star_exact_at_median=float(n_star_exact(0.95, Pd, P)),
                gain_closed_form_at_median=float(batch_gain(min(n, np.median(out["attack_cap"][sl])), 0.95, Pd, P)),
            ))
    return rows


def run_e1():
    print("E1 volume attack")
    R = 60 if QUICK else 400
    jobs = []
    for S in STAKES + ((10.0, 20.0, 60.0, 100.0) if not QUICK else ()):
        for lam in LAMS:
            n_ref = (BASE.V + lam * S) / 1.1
            for q in QS:
                if S not in STAKES and (lam != 1.0):
                    continue
                full = S in STAKES
                ns = (np.unique(np.round(np.linspace(1, 3 * n_ref, 24)).astype(int)) if full
                      else np.array([], int))
                ns = np.unique(np.concatenate([ns, [ALL]]))
                for m in ("M1", "M2", "M3+sweep", "M4"):
                    if not full and m == "M1":
                        continue
                    nn = ns if m != "M1" else ns[ns < ALL]
                    jobs.append((S, lam, q, m, nn, R, SEED + 1, 500))
    # long reputation-building phase: at high stake the posterior learns slowly
    # (p ~ 0.005 -> ~3 audits in 500 steps), so a patient attacker waits longer.
    for S in (30.0, 100.0, 300.0):
        for m in ("M2", "M3+sweep", "M4"):
            jobs.append((S, 1.0, 0.0, m, np.array([ALL]), R, SEED + 11, 2000 if QUICK else 20000))
    rows = [r for rs in pmap(_e1_job, jobs) for r in rs]
    rows.sort(key=lambda r: (r["build_steps"], r["S"], -r["lam"], r["q"], r["mechanism"], r["all_allowed"],
                             r["n_requested"]))
    write_csv("e1_volume.csv", rows)
    plot_e1(rows)


def _sel(rows, **kw):
    return [r for r in rows if all(r[k] == v for k, v in kw.items())]


def plot_e1(rows):
    short = [r for r in rows if r["build_steps"] == 500]
    long_ = [r for r in rows if r["build_steps"] != 500]
    fig, (a, b) = plt.subplots(2, 1, figsize=(W1, 5.6), gridspec_kw=dict(height_ratios=[1.1, 1]))
    base = dict(S=30.0, lam=1.0, q=0.0)
    for m in ("M1", "M2", "M3+sweep", "M4"):
        rs = [r for r in _sel(short, mechanism=m, **base) if not r["all_allowed"]]
        x = np.array([r["n_requested"] for r in rs])
        a.plot(x, [r["gain_mean"] for r in rs], color=COL[m], ls=LS[m], marker=MARK[m], ms=3,
               label=LABEL[m])
        a.fill_between(x, [r["gain_lo"] for r in rs], [r["gain_hi"] for r in rs],
                       color=COL[m], alpha=0.18, lw=0)
    r2 = _sel(short, mechanism="M2", all_allowed=True, **base)[0]
    nmp, nst = r2["n_max_paper_at_median"], r2["n_star_exact_at_median"]
    a.axhline(0, color=INK, lw=0.6)
    for xv, ls, txt in ((nmp, ":", rf"$n_{{\max}}$ of 7.5(ii) = {nmp:.0f}"),
                        (nst, "--", rf"exact break-even $n^*$ = {nst:.0f}")):
        a.axvline(xv, color=INK, lw=0.8, ls=ls)
        a.text(xv + 1.5, 58, txt, rotation=90, fontsize=6.5, color=INK, va="top", ha="left")
    a.set_ylim(-32, 62)
    a.set_xlabel("concurrent false receipts requested at attack, $n$")
    a.set_ylabel("deviation gain (USD per attack)")
    a.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.5)
    a.grid(alpha=0.25)
    a.text(0.98, 0.44, r"(a)  $S$ = \$30, $\lambda$ = 1, $q$ = 0", transform=a.transAxes,
           ha="right", va="center", fontsize=7, color=INK)

    for m in ("M2", "M4"):
        for q, ls in zip(QS, ("-", "--", ":")):
            rs = sorted(_sel(short, mechanism=m, lam=1.0, q=q, all_allowed=True), key=lambda r: r["S"])
            b.errorbar([r["S"] for r in rs], [r["gain_mean"] for r in rs],
                       yerr=[[r["gain_mean"] - r["gain_lo"] for r in rs],
                             [r["gain_hi"] - r["gain_mean"] for r in rs]],
                       color=COL[m], ls=ls, marker=MARK[m], ms=3, capsize=0, lw=1.1,
                       label=f"{m}, $q$ = {q:g}")
        rs = sorted(_sel(long_, mechanism=m), key=lambda r: r["S"])
        b.errorbar([r["S"] for r in rs], [r["gain_mean"] for r in rs],
                   yerr=[[r["gain_mean"] - r["gain_lo"] for r in rs],
                         [r["gain_hi"] - r["gain_mean"] for r in rs]],
                   color=COL[m], ls="none", marker=MARK[m], ms=5, mfc="white", capsize=0,
                   label=f"{m}, $q$ = 0, 20k-step record")
    b.axhline(0, color=INK, lw=0.6)
    b.set_xscale("log")
    b.set_yscale("symlog", linthresh=1.0)
    b.set_xlabel("stake $S$ (USD)")
    b.set_ylabel("gain when taking all the cap allows\n(USD per attack)")
    b.legend(frameon=False, ncol=2, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    b.grid(alpha=0.25, which="both")
    b.text(0.02, 1.02, "(b)", transform=b.transAxes, fontsize=7, color=INK)
    fig.tight_layout()
    save(fig, "e1_volume_attack")

    # supplementary: lambda x q small multiples at S = 30
    fig, axs = plt.subplots(2, 3, figsize=(7.0, 3.8), sharex=True, sharey=True)
    for i, lam in enumerate(LAMS):
        for j, q in enumerate(QS):
            ax = axs[i, j]
            for m in ("M1", "M2", "M3+sweep", "M4"):
                rs = [r for r in _sel(short, mechanism=m, S=30.0, lam=lam, q=q) if not r["all_allowed"]]
                x = [r["n_requested"] for r in rs]
                ax.plot(x, [r["gain_mean"] for r in rs], color=COL[m], ls=LS[m], marker=MARK[m],
                        ms=2.5, label=LABEL[m])
                ax.fill_between(x, [r["gain_lo"] for r in rs], [r["gain_hi"] for r in rs],
                                color=COL[m], alpha=0.18, lw=0)
            r2 = _sel(short, mechanism="M2", S=30.0, lam=lam, q=q, all_allowed=True)[0]
            ax.axvline(r2["n_max_paper_at_median"], color=INK, lw=0.7, ls=":")
            ax.axhline(0, color=INK, lw=0.6)
            ax.set_yscale("symlog", linthresh=1.0)
            ax.grid(alpha=0.25)
            ax.text(0.03, 0.95, rf"$\lambda$ = {lam:g}, $q$ = {q:g}", transform=ax.transAxes,
                    fontsize=7, va="top", color=INK)
            if j == 0:
                ax.set_ylabel("deviation gain (USD)")
    fig.supxlabel("concurrent false receipts requested at attack, $n$  ($S$ = \\$30)", fontsize=8)
    fig.legend(*axs[0, 0].get_legend_handles_labels(), frameon=False, ncol=4, fontsize=7,
               loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout()
    save(fig, "e1_volume_attack_grid")


# ====================================================================== E2
def _e2_job(job):
    si, mname, S, lam, q, R, seed = job
    P = with_(BASE, S=S, lam=lam, q=q)
    st = strategy_for(si, P)
    out = deviation(st, MECHANISMS[mname], P, R=R, seed=seed)
    return dict(strategy=st.name, theta=st.theta, mechanism=mname, S=S, lam=lam, q=q, R=R,
                **summarise(out, P))


def run_e2():
    print("E2 mechanism comparison")
    Rb = 100 if QUICK else 2000
    Rg = 60 if QUICK else 500
    base_jobs = [(si, m, BASE.S, BASE.lam, BASE.q, Rb, SEED + 2 + 101 * si)
                 for si in range(len(STRATEGIES)) for m in MECH_ORDER]
    base = pmap(_e2_job, base_jobs)
    write_csv("e2_mechanisms_baseline.csv", base)
    grid_jobs = [(si, m, S, lam, q, Rg, SEED + 3 + 101 * si)
                 for S in STAKES for lam in LAMS for q in QS
                 for si in range(len(STRATEGIES)) for m in MECH_ORDER]
    grid = pmap(_e2_job, grid_jobs)
    write_csv("e2_mechanisms_grid.csv", grid)
    plot_e2(base, grid)


def plot_e2(base, grid):
    names = [s.name for s in STRATEGIES if s.kind != "honest"]
    fig, (a, b) = plt.subplots(2, 1, figsize=(W1, 5.6), gridspec_kw=dict(height_ratios=[1.25, 1]))
    off = np.linspace(-0.3, 0.3, len(MECH_ORDER))
    for k, m in enumerate(MECH_ORDER):
        for i, nm in enumerate(names):
            r = _sel(base, strategy=nm, mechanism=m)[0]
            y = len(names) - 1 - i + off[k]
            a.errorbar(r["gain_mean"], y, xerr=[[r["gain_mean"] - r["gain_lo"]], [r["gain_hi"] - r["gain_mean"]]],
                       color=COL[m], marker=MARK[m], ms=3.5, lw=1, capsize=0,
                       label=LABEL[m] if i == 0 else None)
    a.axvline(0, color=INK, lw=0.6)
    a.set_xscale("symlog", linthresh=10)
    a.set_xlim(-3000, 3000)
    a.set_yticks(range(len(names)))
    a.set_yticklabels(names[::-1], fontsize=6.5)
    a.set_xlabel("deviation gain over 1000 steps (USD per agent, 95% CI)")
    a.grid(alpha=0.25, axis="x", which="both")
    a.legend(frameon=False, fontsize=6, ncol=3, loc="lower center", bbox_to_anchor=(0.45, 1.06),
             columnspacing=0.8, handletextpad=0.3)
    a.text(0.02, 1.01, "(a)  $S$ = \\$30, $\\lambda$ = 1, $q$ = 0", transform=a.transAxes, fontsize=7, color=INK)

    n_cfg = len(STAKES) * len(LAMS) * len(QS)
    M = np.zeros((len(names), len(MECH_ORDER)))
    for i, nm in enumerate(names):
        for k, m in enumerate(MECH_ORDER):
            M[i, k] = sum(1 for r in _sel(grid, strategy=nm, mechanism=m) if r["gain_lo"] > 0)
    im = b.imshow(M, cmap="Blues", vmin=0, vmax=n_cfg, aspect="auto")
    for i in range(M.shape[0]):
        for k in range(M.shape[1]):
            b.text(k, i, f"{int(M[i, k])}", ha="center", va="center", fontsize=7,
                   color="white" if M[i, k] > n_cfg * 0.55 else "#0b0b0b")
    b.set_xticks(range(len(MECH_ORDER)))
    b.set_xticklabels(MECH_ORDER)
    b.set_yticks(range(len(names)))
    b.set_yticklabels(names, fontsize=6.5)
    b.set_xlabel(f"mechanism  (cell: profitable configurations out of {n_cfg})")
    b.text(0.02, 1.01, r"(b)  $S\in\{5,30,300\}$, $\lambda\in\{0.5,1\}$, $q\in\{0,0.034,0.1\}$",
           transform=b.transAxes, fontsize=7, color=INK)
    fig.tight_layout()
    save(fig, "e2_mechanism_comparison")


# ====================================================================== E3
QUANTILES = (0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.001)
POP = ((0.95, 0.5), (0.8, 0.25), (0.6, 0.15), (0.4, 0.10))  # (theta, share of tasks)


def _e3_hist_job(job):
    qtl, mname, theta, R, H, seed = job
    P = with_(BASE, lcb_quantile=qtl, H=H)
    out = simulate(Strategy("h", theta, "honest"), MECHANISMS[mname], P, R=R, seed=seed, record=True)
    p = out["hist_p"]
    Pd = p + (1 - p) * P.q
    m_pure = Pd * (P.V + P.lam * P.S) - float(gain_pure(theta, P))
    m_all = Pd * (P.V + P.lam * P.S) - max(float(gain_pure(theta, P)), P.V)
    return dict(quantile=qtl, mechanism=mname, theta=theta,
                audits=float(out["audits"].sum()), tasks=float(out["tasks"].sum()),
                m_pure=m_pure.ravel().astype(np.float32), m_all=m_all.ravel().astype(np.float32))


def _e3_dev_job(job):
    qtl, mname, si, R, seed = job
    P = with_(BASE, lcb_quantile=qtl)
    out = deviation(strategy_for(si, P), MECHANISMS[mname], P, R=R, seed=seed)
    return dict(quantile=qtl, mechanism=mname, strategy=STRATEGIES[si].name, **summarise(out, P))


def run_e3():
    print("E3 theta_LCB quantile sweep")
    R = 60 if QUICK else 400
    H = 1000
    hjobs = [(qt, m, th, R, H, SEED + 4 + int(1000 * th)) for qt in QUANTILES
             for m in ("M3", "M4") for th, _ in POP]
    hist = pmap(_e3_hist_job, hjobs)
    rows = []
    for qt in QUANTILES:
        for m in ("M3", "M4"):
            hs = [h for h in hist if h["quantile"] == qt and h["mechanism"] == m]
            cost = sum(w * BASE.c_audit * h["audits"] / h["tasks"] for (th, w), h in
                       zip(POP, sorted(hs, key=lambda h: -h["theta"])))
            for key in ("m_pure", "m_all"):
                allm = np.concatenate([h[key] for h in hs])
                per_type = {f"p01_theta{h['theta']:g}": float(np.quantile(h[key], 0.01)) for h in hs}
                rows.append(dict(quantile=qt, mechanism=m, deviation_set="pure" if key == "m_pure" else "all",
                                 audit_cost_per_task=cost, margin_p01=float(np.quantile(allm, 0.01)),
                                 margin_min=float(allm.min()), margin_median=float(np.median(allm)),
                                 frac_histories_negative=float((allm < 0).mean()), **per_type))
    write_csv("e3_quantile_margin.csv", rows)
    djobs = [(qt, m, si, R, SEED + 5 + 101 * si) for qt in QUANTILES for m in ("M3", "M4")
             for si in range(1, len(STRATEGIES))]
    dev = pmap(_e3_dev_job, djobs)
    write_csv("e3_quantile_deviation.csv", dev)
    plot_e3(rows, dev)


def plot_e3(rows, dev):
    fig, (a, b) = plt.subplots(2, 1, figsize=(W1, 5.0))
    series = (("M3", "pure", "M3, pure falsification only (paper's threat model)", "M3", "-"),
              ("M3", "all", "M3, incl. fake-on-failure", "M3", "--"),
              ("M4", "all", "M4, incl. fake-on-failure", "M4", ":"))
    for m, ds, lab, ck, ls in series:
        rs = sorted(_sel(rows, mechanism=m, deviation_set=ds), key=lambda r: -r["quantile"])
        x = [1000 * r["audit_cost_per_task"] for r in rs]
        y = [r["margin_p01"] for r in rs]
        a.plot(x, y, color=COL[ck], ls=ls, marker=MARK[ck], ms=3.5, label=lab)
        if ds == "pure":
            for r, xi, yi in zip(rs, x, y):
                a.annotate(f"{r['quantile']:g}", (xi, yi), textcoords="offset points", xytext=(4, -9),
                           fontsize=6, color=INK)
        b.plot([r["quantile"] for r in rs], [r["frac_histories_negative"] for r in rs],
               color=COL[ck], ls=ls, marker=MARK[ck], ms=3.5, label=lab)
    a.axhline(0, color=INK, lw=0.6)
    a.set_xlabel(r"platform audit cost per task ($10^{-3}$ USD)")
    a.set_ylabel("1st-percentile deterrence margin\n(USD per false receipt)")
    a.grid(alpha=0.25)
    a.legend(frameon=False, fontsize=6, loc="lower center", bbox_to_anchor=(0.5, 1.08))
    a.text(0.02, 1.01, r"(a)  point labels: $\theta_{LCB}$ quantile", transform=a.transAxes, fontsize=7, color=INK)
    b.set_xscale("log")
    b.set_yscale("symlog", linthresh=1e-3)
    b.set_ylim(-1e-4, 1.5)
    b.invert_xaxis()
    b.set_xlabel(r"$\theta_{LCB}$ quantile")
    b.set_ylabel("share of reachable histories\nwith a profitable false receipt")
    b.grid(alpha=0.25, which="both")
    b.text(0.02, 1.01, "(b)", transform=b.transAxes, fontsize=7, color=INK)
    fig.tight_layout()
    save(fig, "e3_quantile_tradeoff")


# ====================================================================== E4
def _e4_job(job):
    label, theta, S, obs, R, H, seed = job
    P = with_(BASE, S=S, H=H, obs_rule=obs)
    out = simulate(Strategy("h", theta, "honest"), MECHANISMS["M1"], P, R=R, seed=seed, record=True)
    p = out["hist_p"]
    return dict(label=label, theta=theta, S=S, obs=obs, mean=p.mean(1), p10=np.quantile(p, 0.1, 1),
                p90=np.quantile(p, 0.9, 1), thl=out["hist_thL"].mean(1))


def run_e4():
    print("E4 audit concentration")
    R = 60 if QUICK else 500
    H = 3000
    jobs = []
    for S in (30.0, 300.0):
        for th in (0.95, 0.6, 0.3):
            jobs.append((f"theta={th:g}", th, S, "audited", R, H, SEED + 6 + int(100 * th)))
        jobs.append(("theta=0.95 literal", 0.95, S, "literal", R, H, SEED + 6 + 95))
    res = pmap(_e4_job, jobs)
    rows = []
    for r in res:
        for t in range(0, H, 10):
            rows.append(dict(S=r["S"], series=r["label"], theta=r["theta"], obs_rule=r["obs"], step=t,
                             p_mean=float(r["mean"][t]), p_p10=float(r["p10"][t]), p_p90=float(r["p90"][t]),
                             thetaLCB_mean=float(r["thl"][t])))
    write_csv("e4_audit_rate_over_time.csv", rows)

    # steady-state population: who receives the audits?
    groups = (("newcomers θ=0.95", 0.95, slice(0, 100), 0.20),
              ("established θ=0.95", 0.95, slice(1000, 3000), 0.60),
              ("established θ=0.6", 0.6, slice(1000, 3000), 0.15),
              ("established θ=0.3", 0.3, slice(1000, 3000), 0.05))
    share = []
    for S in (30.0, 300.0):
        tot = 0.0
        tmp = []
        for name, th, sl, w in groups:
            r = [x for x in res if x["S"] == S and x["theta"] == th and x["obs"] == "audited"][0]
            pbar = float(r["mean"][sl].mean())
            tmp.append((name, w, pbar))
            tot += w * pbar
        for name, w, pbar in tmp:
            share.append(dict(S=S, group=name, task_share=w, mean_audit_rate=pbar,
                              audit_share=w * pbar / tot))
    write_csv("e4_audit_share.csv", share)
    plot_e4(res, share, H)


def plot_e4(res, share, H):
    fig, (a, b) = plt.subplots(2, 1, figsize=(W1, 5.0), gridspec_kw=dict(height_ratios=[1.2, 1]))
    t = np.arange(H) + 1
    cols = {0.95: COL["M0"], 0.6: COL["M1"], 0.3: COL["M2"]}
    marks = {0.95: "o", 0.6: "s", 0.3: "^"}
    for r in res:
        if r["S"] != 30.0:
            continue
        th = r["theta"]
        if r["obs"] == "literal":
            a.plot(t, r["mean"], color=cols[th], ls=(0, (1, 1)), lw=1.0,
                   label=r"$\theta$ = 0.95, literal rule")
            continue
        a.plot(t, r["mean"], color=cols[th], lw=1.4, marker=marks[th], markevery=0.12, ms=3,
               label=rf"$\theta$ = {th:g}")
        a.fill_between(t, r["p10"], r["p90"], color=cols[th], alpha=0.15, lw=0)
        a.axhline(float(p_star(th, BASE)), color=cols[th], lw=0.7, ls="--")
    a.axhline(p_fake_on_failure(BASE), color=INK, lw=0.8, ls=":")
    a.text(1.3, p_fake_on_failure(BASE) * 1.03, r"$V/(V+\lambda S)$", fontsize=6.5, color=INK, va="bottom")
    a.set_xscale("log")
    a.set_xlim(1, H)
    a.set_xlabel("tasks since entry")
    a.set_ylabel("audit probability applied, $p$")
    a.grid(alpha=0.25, which="major")
    a.legend(frameon=False, fontsize=6, loc="lower left", bbox_to_anchor=(0.0, 0.12))
    a.text(0.02, 1.01, r"(a)  M1, $S$ = \$30", transform=a.transAxes, fontsize=7, color=INK)

    rs = [r for r in share if r["S"] == 30.0]
    x = np.arange(len(rs))
    b.bar(x - 0.2, [r["task_share"] for r in rs], width=0.38, color="#c3c2b7", label="share of tasks")
    b.bar(x + 0.2, [r["audit_share"] for r in rs], width=0.38, color=COL["M0"], label="share of audits")
    for xi, r in zip(x, rs):
        b.text(xi + 0.2, r["audit_share"] + 0.01, f"{r['audit_share']:.2f}", ha="center", fontsize=6, color=INK)
        b.text(xi - 0.2, r["task_share"] + 0.01, f"{r['task_share']:.2f}", ha="center", fontsize=6, color=INK)
    b.set_xticks(x)
    b.set_xticklabels([r["group"].replace(" θ", "\nθ") for r in rs], fontsize=6.5)
    b.set_ylabel("share")
    b.set_ylim(0, 0.75)
    b.legend(frameon=False, fontsize=6.5, loc="upper right")
    b.grid(alpha=0.25, axis="y")
    b.text(0.02, 1.01, "(b)  illustrative population mix, $S$ = \\$30", transform=b.transAxes,
           fontsize=7, color=INK)
    fig.tight_layout()
    save(fig, "e4_audit_concentration")


# ====================================================================== main
if __name__ == "__main__":
    os.makedirs(RES, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    which = [a for a in sys.argv[1:] if not a.startswith("--")] or ["e1", "e2", "e3", "e4"]
    for name in which:
        t0 = time.time()
        {"e1": run_e1, "e2": run_e2, "e3": run_e3, "e4": run_e4}[name]()
        print(f"  {name} done in {time.time() - t0:.0f}s")

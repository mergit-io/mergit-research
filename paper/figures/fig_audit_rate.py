"""Figure 3: required audit rate against stake, and the cost of concurrency.

Reproduces the arithmetic of draft-v1 sections 7.2, 7.4 and 7.5(ii) (corrected form).

    g(theta)       = max(c_exec + (1 - theta) V, V)        forgery gain at the binding moment
    p*(theta, S)   = g(theta) / (V + lambda S)             one-shot required detection rate
    n-allowance:   n (g - P_d V) <= lambda S [1 - (1 - P_d)^n]   for every n <= n_cap
    p_joint(S, n_cap) = smallest P_d satisfying the inequality at n_cap

Run:  python fig_audit_rate.py        -> writes fig_audit_rate.pdf and .png
"""
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

V, C_EXEC, LAM = 2.0, 1.0, 1.0
S = np.geomspace(2, 300, 300)


def g(theta):
    return np.maximum(C_EXEC + (1 - theta) * V, V)


def p_star(theta, s):
    return g(theta) / (V + LAM * s)


def p_joint(gain, s, n):
    """Smallest P_d with n(gain - P_d V) <= lam S (1 - (1-P_d)^n); clipped at 1."""
    lo, hi = 0.0, 1.0
    f = lambda P: n * (gain - P * V) - LAM * s * (1 - (1 - P) ** n)
    if f(0.0) <= 0:
        return 0.0
    if f(1.0) > 0:
        return 1.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) > 1e-12 else (lo, mid)
    return hi


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))

for theta in (0.95, 0.6, 0.2):
    ax1.plot(S, p_star(theta, S), label=rf"$\theta={theta}$")
ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlabel("stake $S$ (USD)")
ax1.set_ylabel("one-shot required audit rate $p^*$")
ax1.set_title(r"(a) Rate falls with stake; flat for $\theta\geq c_{exec}/V$")
ax1.legend(fontsize=8, frameon=False)
ax1.grid(alpha=0.25, which="both")

for n in (1, 5, 10, 25):
    ax2.plot(S, [p_joint(g(0.95), s, n) for s in S], label=rf"$n_{{cap}}={n}$")
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("stake $S$ (USD)")
ax2.set_ylabel("audit rate sized for the allowance")
ax2.set_title(r"(b) Concurrency is bought with collateral, $\theta=0.95$")
ax2.legend(fontsize=8, frameon=False)
ax2.grid(alpha=0.25, which="both")

fig.suptitle(
    rf"$V=\${V:.0f}$, $c_{{exec}}=\${C_EXEC:.0f}$, $\lambda={LAM:.0f}$, $q=0$  —  analytical, not measured",
    fontsize=9,
    y=1.02,
)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(f"fig_audit_rate.{ext}", bbox_inches="tight", dpi=200)
print("wrote fig_audit_rate.pdf / .png")

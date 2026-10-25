"""Unit checks: closed forms reproduce draft-v1 section 7.4 / 7.5, and the
simulator agrees with the closed forms where the closed forms are exact.

Run:  python test_analytics.py      (or: pytest test_analytics.py)
"""
import numpy as np

from mergit_sim import (MECHANISMS, Params, Strategy, batch_gain, deviation,
                        expected_slash, n_max_paper, n_star_exact,
                        p_fake_on_failure, p_joint, p_star, simulate)

P0 = Params()  # V=2, c_exec=1, theta=0.95 (strategy), lam=1, c_audit=0.02, q=0


def test_section_7_4_table():
    # S = 30 -> p* ~ 0.034 ; S = 300 -> 0.0036 ; expected audit cost $0.0007 / $0.00007
    p30 = p_star(0.95, Params(S=30))
    p300 = p_star(0.95, Params(S=300))
    assert round(float(p30), 3) == 0.034
    assert round(float(p300), 4) == 0.0036
    assert round(float(p30) * 0.02, 4) == 0.0007
    assert round(float(p300) * 0.02, 5) == 0.00007


def test_section_7_4_theta_spread():
    # S = 30: theta 0.95 / 0.6 / 0.2 -> 0.034 / 0.056 / 0.081 ; S = 5: 0.157 / 0.257 / 0.371
    for S, want in ((30, (0.034, 0.056, 0.081)), (5, (0.157, 0.257, 0.371))):
        got = [round(float(p_star(th, Params(S=S))), 3) for th in (0.95, 0.6, 0.2)]
        assert got == list(want), (S, got)


def test_rule_2_threshold():
    # challenge alone suffices when q >= p_req ~ 0.034 at S = 30
    assert float(p_star(0.95, Params(S=30), q=0.0344)) == 0.0


def test_n_max_paper():
    # section 7.5(ii): n_max = 30 at S = 30, P_d = 0.05; 300 at S = 300; unbounded iff P_d >= 0.55
    assert abs(float(n_max_paper(0.95, 0.05, Params(S=30))) - 30.0) < 1e-9
    assert abs(float(n_max_paper(0.95, 0.05, Params(S=300))) - 300.0) < 1e-9
    assert np.isinf(n_max_paper(0.95, 0.55, Params(S=30)))
    assert np.isfinite(n_max_paper(0.95, 0.549, Params(S=30)))


def test_exact_batch_condition():
    # The paper's n_max charges lam*S with certainty; the exact penalty charges it
    # only if at least one receipt is detected. At S=30, P_d=0.05: n* = 18, and
    # falsifying 30 at once is profitable by ~ +6.4 USD.
    P = Params(S=30)
    assert n_star_exact(0.95, 0.05, P) == 18
    assert abs(float(batch_gain(30, 0.95, 0.05, P)) - (30 - 30 * (1 - 0.95 ** 30))) < 1e-9
    assert float(batch_gain(30, 0.95, 0.05, P)) > 6.0
    # n = 1 reduces to the one-shot condition
    assert abs(float(batch_gain(1, 0.95, 0.05, P)) - (1.1 - 0.05 * 32)) < 1e-12
    # at exactly p = p*(theta) every n >= 2 is profitable (Bernoulli's inequality)
    ps = float(p_star(0.95, P))
    assert n_star_exact(0.95, ps, P) <= 1
    # lam < 1: per-event slashing bounded by remaining stake
    P5 = Params(S=30, lam=0.5)
    k = np.arange(0, 6)
    from scipy.stats import binom
    brute = sum(binom.pmf(kk, 5, 0.1) * min(kk * 15.0, 30.0) for kk in k)
    assert abs(float(expected_slash(5, 0.1, P5)) - brute) < 1e-9


def test_fake_on_failure_threshold():
    # Ex-post deviation: deterred iff P_d >= V/(V + lam S): 0.0625 at S=30, 0.0066 at S=300
    assert abs(p_fake_on_failure(Params(S=30)) - 2 / 32) < 1e-12
    assert round(p_fake_on_failure(Params(S=300)), 4) == 0.0066
    # p_joint with n_allow = 1 and G = V reproduces it
    assert abs(float(p_joint(2.0, Params(S=30, n_allow=1))) - 0.0625) < 1e-3


def test_simulator_one_shot_matches_closed_form():
    # A volume attacker with n = 1 under M0 (fixed p = p*(0.95)) has expected gain
    # ~ 0; with n = 30 under M0 the simulated mean matches batch_gain.
    P = Params(S=30)
    p0 = float(p_star(0.95, P))
    for n, R in ((1, 40000), (30, 20000)):
        st = Strategy("vol", 0.95, "volume", t_switch=5, n_attack=n)
        out = deviation(st, MECHANISMS["M0"], P, R=R, seed=7)
        want = float(batch_gain(n, 0.95, p0, P))
        se = out["gain"].std(ddof=1) / np.sqrt(R)
        assert abs(out["gain"].mean() - want) < 4 * se + 1e-3, (n, out["gain"].mean(), want, se)


def test_honest_has_zero_gain():
    st = Strategy("honest", 0.95, "honest")
    out = deviation(st, MECHANISMS["M3"], Params(H=200), R=50, seed=1)
    assert np.all(out["gain"] == 0.0)


def test_posterior_unbiased_under_audited_rule():
    P = Params(S=5, H=3000)  # high audit rate -> many observations
    out = simulate(Strategy("h", 0.8, "honest"), MECHANISMS["M1"], P, R=200, seed=3)
    post_mean = out["alpha"] / (out["alpha"] + out["beta"])
    assert abs(post_mean.mean() - 0.8) < 0.02, post_mean.mean()
    # the literal reading (failures always observed, successes only when audited)
    # biases the posterior downward
    lit = simulate(Strategy("h", 0.8, "honest"), MECHANISMS["M1"], Params(S=5, H=3000, obs_rule="literal"), R=200, seed=3)
    assert (lit["alpha"] / (lit["alpha"] + lit["beta"])).mean() < 0.7


if __name__ == "__main__":
    import inspect
    import sys

    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and inspect.isfunction(f)]
    for name, f in tests:
        f()
        print(f"ok  {name}")
    print(f"{len(tests)} checks passed")
    sys.exit(0)

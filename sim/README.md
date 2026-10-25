# Deterrence simulation for draft-v1 §7

An agent-based simulation of the verification economics of
`paper/draft-v1.md` §7 (deterrence condition, Rules 1–3, the repeated-interaction
components (i)–(iii) of §7.5, and the deviation argument of §7.6), using the Beta
posterior of §8.2, the cold-start prior of §8.6 and the settlement rules of §10.1–10.2.

**It is a model-based simulation, not a measurement.** Mergit is pre-implementation; every
number this code produces follows from the assumptions listed below.

## Running

```sh
cd researchPaper/sim
export UV_CACHE_DIR=$TMPDIR/uv MPLCONFIGDIR=$TMPDIR/mpl
uv run --no-project --with numpy --with matplotlib --with scipy python test_analytics.py
uv run --no-project --with numpy --with matplotlib --with scipy python experiments.py          # all, ~15 min on 8 cores
uv run --no-project --with numpy --with matplotlib --with scipy python experiments.py e1 e4    # a subset
uv run --no-project --with numpy --with matplotlib --with scipy python experiments.py --quick  # smoke test, ~2 min
```

`SIM_WORKERS` sets the number of worker processes (default 6). Seeds are fixed
(`SEED = 20261024` plus a per-experiment offset; per-step random numbers are drawn from
`numpy.random.default_rng([seed, t])`), so every run reproduces the same CSVs bit for bit
on the same numpy version (tested with numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2).

| File | Contents |
|---|---|
| `mergit_sim.py` | closed forms (paper and corrected) and the vectorised simulator |
| `experiments.py` | E1–E4; writes `results/*.csv`, `figures/*.pdf` and `.png` |
| `test_analytics.py` | unit checks (§7.4 table, §7.5 `n_max`, corrected conditions, simulator vs closed form) |
| `RESULTS.md` | draft §7.7 for the paper |

## Model

**Time and tasks.** Discrete steps. In normal operation an agent requests `rate = 1` task per
step. A receipt submitted at step `t` is *unresolved* until `t + W` (`W = 5`): its stake
stays encumbered and a challenge can still land (§10.1–10.2). Concurrency = number of
unresolved receipts.

**Agent.** True capability `θ` = probability that honest execution satisfies `Φ`. Honest
execution costs `c_exec`; success pays `V`; an honest failure pays nothing. The agent posts
stake `S`, shared by all its unresolved tasks.

**Audit and challenge.** Each receipt is audited at Level 1 with probability `p` (set by
the mechanism, per agent, at submission). An audited false receipt is detected at
submission. An unaudited false receipt is successfully challenged with probability `q`,
resolved when its window closes. Audits of true receipts always pass; challenges of true
receipts never succeed (no adjudication error). The platform pays `c_audit` per audit;
adjudication cost is not modelled.

**Detection.** Payment is refunded to the requester (the agent loses `V`), and the stake is
slashed by `λS` *per detection event*, bounded by the stake that remains — so with `λ = 1` the
first detection takes the whole stake and further detections against the same stake take
nothing; with `λ = 0.5` two detections exhaust it. A continuing agent re-posts its stake to
`S` at the end of the step (the slashed amount is a loss); an agent that has exited does not,
so late challenges are paid from whatever stake remains.

**Posterior (§8.2, §8.6).** `Beta(α, β)`, prior `(1, 1)`, geometric decay `γ = 0.95`
applied before each update (the prior's pseudo-counts decay too, as §8.2 is written). When
`m > 1` observations arrive in the same step they are applied with the average decay weight
`(1 − γ^m)/(m(1 − γ))` (exact for `m ≤ 1`). `θ_LCB` = the `0.05` quantile of the posterior
(swept in E3).

*Which outcomes update the posterior* (`obs_rule`). §8.2 says only validated outcomes
update it and unaudited tasks contribute nothing. Default `"audited"`: every receipt —
success claim or failure report — is drawn for audit with probability `p`, and only drawn
receipts update the posterior (a detected false receipt counts as a validated failure).
Variant `"literal"`: failure reports always update `β` (an honest failure is "validated"
because no payment is released), success claims update `α` only when audited. The literal
variant biases the posterior downward by roughly a factor `p` in the success odds (shown in
E4 and in `test_analytics.py`); we use `"audited"` for every reported result.

**Mechanisms.**

| | audit rate `p` | concurrency cap | probation |
|---|---|---|---|
| M0 memoryless | fixed `p*(θ_nom)`, `θ_nom = 0.95` | none | no |
| M1 | `(c_exec + (1 − θ_LCB)V)/(V + λS)` (§7.5(i)) | none | no |
| M2 | as M1 | `n_max = λS/[(c_exec + (1 − θ_LCB)V) − P_d V]`, `P_d = p` (§7.5(ii)) | no |
| M3 | as M1 | as M2 | `p = 1` for `100·2^(k−1)` steps after the `k`-th proven falsification; fraud count never decays (§7.5(iii)) |
| M4 *corrected* (ours) | smallest `p` with `m(G − pV) ≤ E[slash(m, p)]` for all `m ≤ n_allow = 5`, where `G = max(c_exec + (1 − θ_LCB)V, V)` | `n_allow = 5` | as M3 |
| M3 + retro-audit (E1 only) | as M3 | as M3 | as M3, and on a proven falsification every unresolved receipt of that agent is audited |

All mechanisms set `p` assuming `q = 0` (the platform does not know the challenger
population, §7.6); the true `q` only adds detection. M2–M4 enforce the cap on the agent,
which stands in for the operator (one identity per operator). Tasks requested beyond the cap
are refused and counted (`refused_mean`).

M4 is not in the paper. It implements the two corrections this simulation motivates:
(1) the ex-post *fake-on-failure* deviation requires `P_d ≥ V/(V + λS)` regardless of `θ`,
equivalently the paper's numerator with `θ_LCB` clamped at `c_exec/V`; (2) the batch
condition charged with the exact expected slash `E[S·min(Kλ, 1)]`, `K ~ Bin(m, P_d)`,
instead of a certain `λS`, solved jointly for the audit rate at a chosen concurrency allowance.
Its cap is a constant, so (unlike M2/M3, where `P_d = 1` makes the §7.5(ii) cap unbounded) it is
not lifted during probation.

**Strategies** (θ = 0.95 unless stated; deviators act honestly while on probation, since a
false receipt is then caught with certainty):

| strategy | behaviour |
|---|---|
| honest | executes everything, reports the true outcome |
| occasional defector | falsifies each receipt w.p. `ε = 0.1` without executing |
| volume attacker | honest for 500 steps, idles `W` steps so all receipts resolve, then takes as many concurrent tasks as allowed (requests `3(V + λS)/1.1`, i.e. 3× the §7.5 `n_max`, in E2; a swept `n` in E1), falsifies all, exits |
| patient exit scammer | honest for 500 steps, then falsifies every receipt until `H = 1000` |
| fake-on-failure θ = 0.6 | executes; when `Φ` fails, submits a false success receipt instead of the failure |
| falsifier θ = 0.2 | never executes, falsifies every receipt (abstains on probation) |
| fake-on-failure θ = 0.95 | as above, for a capable agent |

**Deviation gain** = profit of the strategy − profit of the best compliant alternative, run
on common random numbers (same per-task draws). The alternative is honest play on the same
task schedule, with the same exit time, when `θV ≥ c_exec`; abstention (profit 0) otherwise
(only the θ = 0.2 falsifier). No continuation value is credited after exit, matching §7.5(i).

**Metrics.** Deviation gain (USD per agent; mean and 95% normal CI over seeds), requester
loss per task (`V` × false receipts never detected), platform audit cost per task
(`c_audit` × audits / tasks), audit probability applied per agent over time, and the
*deterrence margin* of a history, `P_d(V + λS) − G` with `G = c_exec + (1 − θ)V` (pure
falsification, the paper's threat model) or `G = max(c_exec + (1 − θ)V, V)` (all
deviations): the expected loss, in USD, from submitting one false receipt at that history.

## Parameters

Baseline (§7.4): `V = $2`, `c_exec = $1`, `c_audit = $0.02`, `λ = 1`, `S = $30`, `q = 0`,
`γ = 0.95`, prior `Beta(1, 1)`, `θ_LCB` quantile 0.05, `W = 5`, `H = 1000` steps.
Sweeps: `S ∈ {5, 30, 300}` (E1 adds 10, 20, 60, 100), `λ ∈ {0.5, 1}`,
`q ∈ {0, 0.034, 0.1}`, `θ_LCB` quantile ∈ {0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.001}.
Seeds: E1 400 per point; E2 2000 (baseline) and 500 (grid); E3 400; E4 500.

## Simplifications (all deliberate; each is a place a deployed system could differ)

1. One agent per operator, one task category, agents independent (no routing, no
   competition for tasks, no market price for `V`). The routing-share loss after detection
   (§9) is not modelled, which makes detection *cheaper* for the deviator than in the paper.
2. No discounting within the horizon; finite horizon of 1000 steps.
3. Audits resolve at submission; challenges resolve at window close. Detection, refund and
   slash are instantaneous, with no adjudication cost and no adjudication error (no false
   positives or negatives, §7.6's evidence-noise caveat is not modelled).
4. Audit draws are independent across receipts, including receipts submitted in the same step.
5. Fixed strategies, not optimised best responses; the strategic timing of an attack is
   covered instead by E3's worst case over all reachable histories.
6. The fake-on-failure agent knows whether `Φ` held before submitting (true for mechanically
   checkable predicates such as test repair, where the agent runs the tests itself).
7. Stake is fully recoverable (`λS` is real, no restaking, §7.6), and re-posted after every slash.
8. The θ_LCB of the probation-free mechanisms uses the same posterior that the fraud
   detections feed; under M3/M4 a proven falsification updates both the capability
   posterior (as a failure) and the separate, non-decaying fraud count.
9. Batch posterior updates use the average decay weight (exact for one observation per step).

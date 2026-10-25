### 7.7 Simulation

To test §§7.5–7.6 rather than restate them, we simulated the mechanism (`sim/`). This is a
model-based simulation, not a measurement of a deployed system.

**Setup.** Each step, an agent with capability `θ` takes one task. Its receipt stays unresolved for
`W = 5` steps, and all unresolved receipts share one stake `S`. Receipts are audited with
probability `p`. An unaudited false receipt is challenged successfully with probability `q`.
Detection forfeits the payment and slashes `λS`, up to the stake that remains. The posterior follows
§8.2 (prior `Beta(1,1)`, `γ = 0.95`), updated only by audited outcomes, and `θ_LCB` is its 0.05
quantile.

Parameters are those of §7.4, swept over `S ∈ {5, 30, 300}`, `λ ∈ {0.5, 1}` and
`q ∈ {0, 0.034, 0.1}`. Mechanisms: M0 (memoryless, `p*` fixed at `θ = 0.95`), M1 (§7.5(i)), M2
(M1 plus the cap of §7.5(ii)), M3 (M2 plus probation, §7.5(iii)), and M4 (a correction, below).

Each faces six deviations: an occasional defector, a volume attacker, a patient exit scammer, a
`θ = 0.2` falsifier, and a *fake-on-failure* agent (`θ = 0.6` and `0.95`) that executes honestly and
forges a success receipt only when `Φ` fails.

Deviation gain is measured against honest play on identical tasks and random draws, with no credit
for continuation value. We use 400–2000 fixed seeds per cell and report 95% confidence intervals.
Unit tests reproduce the §7.4 table and `n_max = 30`.

**The cap, as derived, does not close the volume channel (Figure 4).** Without a cap (M1), the
attacker's gain grows linearly in the number of simultaneous false receipts `n`. With the §7.5(ii)
cap (M2), growth stops but the gain stays positive: +$6.3 (95% CI 4.7–8.0) at `S = $30`, where the
cap admits 24 receipts, and +$66 (52–81) at `S = $300` after a 20,000-task record.

The derivation charges the slash `λS` as certain, but it is incurred only if at least one of the
`n` receipts is detected. The exact condition is

```
n·(c_exec + (1 − θ)V − P_d·V)  ≤  λS·[1 − (1 − P_d)^n]
```

Its break-even is `n* = 18`, not 30, at the §7.4 example (`P_d = 0.05`). At the rate the posterior
actually produced, it is 11. At exactly `p = p*(θ)`, every `n ≥ 2` is profitable. A cap therefore
needs the audit rate to sit above the one-shot level.

Two repairs succeed in every configuration tested: sizing rate and cap jointly from the exact
condition (M4), and auditing every unresolved receipt of an operator once a falsification is
proven (−$20 at the cap).

With `q = 0.034`, M2's gain is no longer significantly positive at any stake.

**A deviation the one-shot rule omits (Figure 5).** §7.2 compares forging with executing, before
any work is done. An agent that has executed and seen `Φ` fail has already sunk `c_exec`, so the
whole payment is gain. The condition becomes `P_d ≥ V/(V + λS)`, independent of `θ`: 0.0625 at
`S = $30`, against the 0.034 of §7.4. A `θ = 0.95` fake-on-failure agent profits under M0–M3
(+$26.8 per 1000 tasks under M1, +$25.3 under M3; significant in 6–11 of 18 configurations). The
posterior cannot help, because its estimate of `θ` is correct.

Probation also interacts with the cap. At `P_d = 1` the §7.5(ii) cap becomes unbounded. At
`S = $5`, where the cap limits honest agents to 3–5 concurrent tasks, getting caught frees an
agent from the cap, and doing so pays in 6 of 18 configurations.

M4 clamps `θ_LCB` at `c_exec/V` (numerator `max(c_exec + (1 − θ_LCB)V, V)`), sizes `p` so that
five concurrent receipts are safe, and keeps the cap during probation.

Under M4 the mean gain is negative in all 108 strategy × configuration cells, and significantly
positive in none. The price is honest audit cost: $0.0014 against $0.0009 per task at `S = $30`,
and $0.00015 against $0.00014 at `S = $300`. That is still fractions of a cent. At `S = $5`,
however, M4 audits half of all tasks.

**Choosing the quantile (Figure 6).** For every history reachable by honest play, we computed the
expected loss from one false receipt, `P_d(V + λS) − (c_exec + (1 − θ)V)`. Histories were pooled
over `θ ∈ {0.95, 0.8, 0.6, 0.4}`.

| `θ_LCB` quantile | histories admitting a profitable forgery | audit cost per task |
|---|---|---|
| 0.05 | 2.4% | $0.00111 |
| 0.01 | 0.20% | $0.00121 (+9%) |
| 0.001 | 0.002% | $0.00132 |

At 0.01, the 1st-percentile margin is positive for every capability tested, so we adopt 0.01. No
quantile repairs fake-on-failure under the §7.5(i) rate: even at 0.001, a quarter of histories
admit it.

**Audit concentration (Figure 7).** Under M1 at `S = $30`, newcomers are audited at `p = 0.091`.
A `θ = 0.95` agent falls to 0.055 within 100 tasks and settles at 0.040; `θ = 0.6` and `0.3` agents
settle at 0.067 and 0.084. Decay caps the effective sample size near 20, so `θ_LCB` stays below
about 0.87 and established agents are audited 16% above `p*(θ)`. In an illustrative population,
newcomers carry 20% of tasks and receive 26% of audits.

Concentration is real but modest. It also depends on a rule §8.2 leaves implicit. If failures always
update the posterior while successes update it only when audited, the posterior is biased downward.
A `θ = 0.95` agent is then audited like a `θ = 0.6` one, and at `S = $300` the posterior never
leaves its prior.

**Limitations.** Strategies are fixed rather than optimized; attack timing enters only through
the worst case over reachable histories. The model has one identity per operator, independent audit
draws, error-free adjudication, no restaking, no discounting, and no loss of routing share after
detection (§9); the last makes detection cheaper for a deviator than under the paper's design.

Fake-on-failure assumes the agent can check `Φ` before submitting, as in test repair. The population
mix, the window, the concurrency allowance and the probation length are illustrative, not
calibrated. The simulation establishes which inequalities hold under the model. It does not
establish audit costs, challenger rates or attacker behaviour, all of which must be measured once
an implementation exists.

*Figures: 4 `sim/figures/e1_volume_attack.pdf` (supplement `e1_volume_attack_grid.pdf`);
5 `e2_mechanism_comparison.pdf`; 6 `e3_quantile_tradeoff.pdf`; 7 `e4_audit_concentration.pdf`.
Data: `sim/results/*.csv`.*

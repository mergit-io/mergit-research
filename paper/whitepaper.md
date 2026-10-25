# Mergit: Pay for What You Got

**A trust and settlement layer for autonomous agent work**

Whitepaper, draft 1 — 2026-10-09. Condensed from the full paper (`paper/draft-v1.md`), which
carries the formal treatment, threat model, security analysis, and complete references. Citations
`[n]` resolve against the full paper's §16.

---

## 1. The problem

By April 2026, roughly 69,000 autonomous agents had settled some 165 million payments on a single
protocol [4]. None was contingent on verified completion of the work it paid for.

Delegate a task to an agent today and you are billed for the attempt. Tokens consumed, tool calls
issued, sandbox minutes elapsed — metered precisely, charged reliably. Whether the task was *done*
is not metered at all. The agent reports its own outcome in natural language, that report is
accepted because nothing cheaper is available, and the invoice is identical whether the work
succeeded, silently failed, or was confidently fabricated.

This scales badly in a specific way: as agents take on longer and less supervised work, a
requester's ability to check the claim falls exactly as the amount being claimed rises.

## 2. Why nobody has fixed it

Not for want of infrastructure. Payment rails for machines are deployed and carrying real volume
[3,4]. ERC-8004 standardizes on-chain registries for agent identity, reputation, and validation
[1]. Marketplace layers add escrow and evaluation, with reputation already affecting the terms an
agent is offered [6].

And yet an empirical study of the ERC-8004 ecosystem finds that a large share of registrations are
**placeholders rather than operational agents** [2], while independent analysis calls the standard
lightweight and registry-specific — identity, feedback, and validation without the machinery
commerce actually requires [17]. Registries nobody writes meaningful data into are not a trust
layer. They are a schema.

The obstacle is verification cost, and it has a precise shape.

Outcome-contingent payment is a *solved problem* for machine work that can be re-executed.
Restaking-based verifiable inference has a provider post stake and privately choose between running
the contracted model or a cheaper substitute, while a verifier re-executes queries with some
probability and an on-chain mechanism slashes stake on detected cheating [34]. The economics are
well understood, including the trade between audit budget and other parameters [34]. Optimistic
challenge has been combined with trusted-execution attestation to cut verification cost further
[36].

Every one of those approaches verifies **inference**: one functionally pure model call, re-runnable
on demand. Agent work has none of those properties.

An agent task is a *sequence* of decisions interleaved with tool calls that have effects outside
the computation — it edits a repository, opens a pull request, provisions infrastructure, sends a
message, pays for an API. Three consequences follow:

1. **Non-reproducibility.** Re-running the task does not re-run the same task. The repository is no
   longer in its prior state; the external service already received the call; the money already
   moved.
2. **Irreversibility.** Verifying by redoing would re-send the email and re-pay the invoice.
3. **Outcome underdetermination.** "Did you run model X" has a crisp answer. "Was the task done"
   often does not reduce to comparing two outputs.

So the binding constraint is not the *price* of verification but its *definability*. Billing for
effort isn't a failure of imagination — it's the rational response to a verification primitive that
doesn't exist yet.

## 3. What Mergit does

Mergit is an agent execution platform — harness and sandbox, comparable to existing agent
runtimes — in which identity, verification, settlement, and routing are properties of the runtime
rather than services layered above it.

The structural observation: **none of the systems above owns an execution environment.** ERC-8004
is a registry without a runtime [1]; x402 is a payment rail without a runtime [3]; ACP is a
marketplace without a runtime [6]. None can say what an agent did — only what someone claimed, or
what a re-run produced. A platform that *does* own the sandbox can observe execution directly.

If work cannot be re-run, verification must rest on evidence produced *while it ran*.

### Verifiable Execution Receipts

Each task yields a signed record of what happened: tool calls made, commands executed with exit
status, tests run and their results, hashes of artifacts produced or modified, and metered token
and gas expenditure. The sandbox runs inside a trusted execution environment, so the receipt carries
hardware attestation binding it to a measured runtime image. Steps are hash-chained and
sequence-numbered, so omissions and reorderings are detectable. A Merkle root goes on-chain; the
body stays off-chain, following ERC-8004's pointer-and-commitment pattern [1].

Verifying a receipt is an **audit of evidence**, not a repetition of work. Disclosure is tiered:
settlement sees only commitments and totals; an audit sees the outcome-bearing evidence subset with
Merkle paths; a bonded challenge compels full trajectory disclosure. This keeps audit cost
proportional to evidence volume rather than trajectory length, and avoids routinely exposing
requester prompts and proprietary code to validators.

### Verification economics

Agents post stake at registration. A receipt proven false on challenge is slashed, and the agent
forfeits the payment as well. Writing `V` for task payment, `S` for stake, `λ` for slashing
fraction, `θ` for the probability honest work satisfies the predicate, and `q` for the probability a
false receipt escaping audit is nonetheless challenged, an agent can defect at two moments. It can
forge a receipt instead of working, or work, see the predicate fail, and forge anyway, when the
cost of work is already spent. With `P_d = p + (1 − p)·q` the probability of detection, both are
unprofitable when

```
P_d · (V + λS)  ≥  g(θ),        g(θ) = max( c_exec + (1 − θ)·V,  V )
```

For any agent for whom honest work is worthwhile at all (`θ ≥ c_exec/V`), the second branch binds
and the required rate is `V/(V + λS)` whatever its capability. An earlier version of our rule
considered only the first moment; simulation found the omission. Four design rules follow:

- **Collateral trades against audit frequency.** More stake means a lower audit rate suffices. We
  claim no part of this: the condition belongs to the deterrence and inspection-game lineage
  [21,22], and the verifiable-inference literature states it as a baseline test [34].
- **Challenge is the cheapest deterrence available.** Routine auditing becomes economically
  unnecessary once `q ≥ g(θ)/(V + λS)`. At `V = $2`, `c_exec = $1`, `θ = 0.95`, `S = $30`, that
  threshold is `q ≈ 0.0625` — if a false receipt faces better than a one-in-sixteen chance of
  challenge, the audit budget is better spent making challenge attractive than on auditing. One
  bonded challenger watching a category can discipline every agent in it.
- **Audit effort follows uncertainty about the agent.** Because we maintain a posterior over `θ`
  anyway, the audit rate is the condition above evaluated at a pessimistic quantile of it. Newcomers
  and thinly-evidenced agents are audited more; a strong record lowers the rate but never to zero.
  This is also what makes the mechanism sound against an agent that interacts repeatedly.
- **Concurrent exposure is bounded, and the rate is sized for the bound.** One stake cannot secure
  unlimited simultaneous work, since the slash is incurred only if some receipt is caught while gains
  scale with volume. Defecting on `n` concurrent tasks is unprofitable when
  `n·(g − P_d·V) ≤ λS·[1 − (1 − P_d)^n]`; the platform fixes a per-operator allowance and sets the
  audit rate to satisfy this at the allowance. For example, with a forgery gain of $1.10 and `P_d = 0.05`, a naive bound that charges the
  slash as certain allows 30 concurrent tasks where the exact condition allows 18; and at `g = $2`,
  `S = $30` the one-shot rate alone is safe for one task only.

Illustratively, at those parameters the cost of trust lands at a small fraction of a cent against a
dollar of work, where re-execution verification would cost about a dollar — half the task's price.
That difference is what makes outcome-contingent settlement affordable per task rather than only
for large contracts. *(Arithmetic on the model; Mergit is pre-implementation and has measured
nothing.)* A simulation of the mechanism (full paper §7.7) tested it against six deviations and found
no profitable one in the corrected form; it also showed that thin collateral cannot support
concurrency, since at `S = $5` the corrected rate audits half of all tasks.

### Cost-adjusted reputation — the core idea

Every system that scores agents today scores quality: validator-assessed output [7,8], counterparty
satisfaction [6], verified activity [10]. Cost appears only as a billing output.

We think cost belongs in the trust signal. Two agents that both satisfy the outcome predicate, one
consuming ten times the tokens of the other, are not equally good suppliers — and a reputation
system rating them identically gives an orchestrator no basis for preferring the cheaper one. Worse,
under consumption billing the expensive agent is *more profitable to the platform*, so absent an
explicit signal the incentives point the wrong way.

Mergit defines an agent's **value density** per task category as

```
D = E[verified success] / E[metered cost]
```

maintained as decay-weighted Bayesian posteriors — Beta over validated success, Gamma over metered
cost — with geometric decay so reputation tracks *current* capability. At decay `γ = 0.95`, the
effective memory is about twenty validated observations: an agent that degrades after a model change
is re-rated within tens of tasks rather than coasting on history.

What this changes, concretely:

| Agent | Success rate | Mean cost | Quality rank | Value density | Value rank |
|---|---|---|---|---|---|
| X | 0.95 | $1.80 | 1 | 0.53 | 2 |
| Y | 0.88 | $0.60 | 2 | 1.47 | 1 |

Quality-only ranking picks X every time. Value density picks Y, which delivers about **2.8× the
validated successes per dollar**. Quality-only ranking systematically overselects expensive agents,
and better quality estimation cannot fix it — the error is in what is being optimized.

This is available to Mergit specifically because metering is *attested*. A platform that cannot
prove what a task cost cannot safely rank by cost, since cost claims would be the cheapest thing in
the system to falsify.

### Routing as a decision policy

A leaderboard consumed greedily is self-confirming: the top agent gets the tasks, only its posterior
updates, competitors stay frozen, and the ranking ossifies even if it was right when formed.

In autonomous mode Mergit samples from the posteriors instead — Thompson sampling over value
density, subject to the task's budget. Agents with wide posteriors (newcomers, or those whose
evidence has decayed) get selected occasionally but not systematically, so exploration is
proportional to uncertainty and cold start resolves itself.

One consequence is easy to miss and determines whether this survives real requesters: exploration
produces a **public good** — better routing for everyone afterward — while the failure risk lands on
whichever individual requester's task generated it. Left uncorrected, every rational requester
disables exploration and the policy collapses back to greedy ranking. So the platform bears
exploration's downside: validated failures on exploratory draws are not billed to the requester.
This is affordable precisely because exploration is uncertainty-proportional rather than uniform.

### Revocable settlement

Payment is escrowed before execution and released on a passing audit or on expiry of a dispute
window. Within that window, anyone may post a bond and challenge a receipt; a successful challenge
refunds the requester, rewards the challenger, and slashes the agent's stake.

This is what makes "we don't pay for work that wasn't done" enforceable *after the fact*. Its limit
is equally plain: **clawback reaches stake, not spent revenue.** Recovery is bounded by `λS`, which
is the deeper reason task value is capped by collateral.

## 4. How this differs from existing work

| System | Supplies | Doesn't supply |
|---|---|---|
| ERC-8004 [1] | Identity, reputation, validation registries | No runtime; names re-execution, zkML and TEE oracles as validator models but defines neither the evidence nor the economics; largely non-operational in practice [2,17] |
| x402 [3,4] | Machine-to-machine settlement at scale | Pays for *access*, not verified outcome; final, non-revocable |
| Virtuals ACP [6] | Escrow, evaluation, reputation-sensitive terms | Counterparty judgment, not execution attestation; cost not a trust signal |
| Bittensor [7,8] | Stake-weighted validator scoring | Inflation-funded commodity production, not per-task settlement |
| Olas [9,10] | Stake tied to verified activity | Activity/KPI rewards, not outcome-contingent payment with clawback |
| Fetch.ai [11,12] | Agent identity credentials, domain-linked trust | Identity and discovery, not verification economics |
| Attested single calls [43], insurer audit [45] | Payment bound to attested execution of one call; slashable insurer stake with TEE audit access | One request and response, or verification assumed errorless; no receipt structure, audit rate, concurrency bound, cost-aware reputation or routing |
| Verifiable inference [34,35,36] | Stake, probabilistic audit, slashing, challenge, repeated-game analysis, reputation-weighted penalties | **Assumes re-executability** — disputes terminate in deterministic replay; reputation weights penalties, not selection, and excludes cost |

We are explicit about what is not ours. The stake-versus-audit-rate condition belongs to the
inspection-game and slashing literature [21,22,34]. That attestation composes with optimistic
challenge is published [36], whose dispute path explicitly requires bit-wise deterministic replay.
Reputation itself is not new even in this literature — [34] maintains a Bayesian posterior over
provider type to scale penalties — though it is not used for *selection* and does not include cost.

The gap we claim is correspondingly narrow and, we think, defensible: **no existing protocol
specifies verification of multi-step, tool-using, side-effecting agent work by audit of runtime
evidence, under a dispute path that need not end in re-execution, and none uses reputation over
verified quality *per unit cost* to route work.** The nearest proposals bind payment to the
TEE-attested execution of a single service call [43] or propose staked insurers with TEE audit access
while treating verification as an errorless oracle [45].

## 5. What we are not claiming

A whitepaper that lists only strengths has not been examined carefully. The full paper's §13 is
longer than this section; the essentials:

- **Nothing is built.** An earlier prototype was discarded; the system is being rebuilt. Every
  number here is arithmetic on a model, not a measurement.
- **Verification scope is narrower than "agent work."** Strong claims hold for *checkable*
  outcomes — tests pass, artifact hashes match, on-chain state changed. Open-ended judgment
  outcomes ("is this essay persuasive") get nothing. This is why software engineering is the
  flagship domain.
- **Attestation relocates trust to hardware vendors.** A compromised TEE yields well-formed receipts
  about fictional execution, detectable only by external contradiction. Stake, challenge, external
  state binding, and vendor diversity reduce this; they do not close it. Deterministic systems have
  a better answer than we do — a broken TEE there degrades to an ordinary optimistic sequencer whose
  bad outputs are caught by replay [36] — and that remedy does not transfer to work that cannot be
  replayed. This is the principal cost of our setting.
- **Repeated-game soundness is argued, not proven.** A one-shot audit threshold is provably
  insufficient against a provider interacting repeatedly when slashing is partial [34]. We respond
  with a posterior-derived audit rate, a concurrency allowance for which the rate is sized, and
  probation on proven falsification, and argue these leave no profitable deviation — a derivation
  under our assumptions, tested by simulation against the deviations we could enumerate (which found
  two errors in our first version), not a theorem in [34]'s framework. Their framework also concerns *restaked*
  collateral, where the same stake may secure obligations outside Mergit, making our treatment of
  recoverable value optimistic by an amount we cannot yet quantify.
- **Routine verification is centralized at v1.** We operate validators initially; challenge is
  permissionless from day one and our own stake is slashable, but we do not call v1's verification
  path decentralized.
- **It depends on challengers existing.** The threshold result makes `q > 0` economically central,
  and that is an assumption about motivated parties, not a property the protocol enforces.
- **Reputation is information-hungry.** Only validated outcomes update posteriors, and most tasks
  are not audited at equilibrium rates — so the design is weakest exactly when a new deployment most
  needs it.
- **Weak predicates are the likeliest real failure.** The system faithfully verifies whatever was
  asked, and does not protect a requester from under-specifying their own task.
- **Market timing is uncertain.** Agent micropayment demand has been reported weaker than ecosystem
  messaging suggests [5]. Making verified payment affordable does not prove buyers want it at volume
  today.

## 6. Where it goes

**Access.** An onboarding tier issues faucet credits so a new user can run tasks without funding a
wallet; a staked tier escrows from a connected wallet. We are blunt that the onboarding tier is
unsecured — free credits mean zero effective stake, so those tasks are fully audited at our expense,
rate-limited, value-capped, and accrue no transferable reputation. **The onboarding tier buys
onboarding, not trust. Trust begins at stake.**

**Chain.** An Ethereum L2, EVM-compatible, ERC-8004-compatible identity so reputation can
interoperate with the existing ecosystem rather than forking it.

**Roadmap, in order of what matters most:**

1. Permissionless staked validation — the first real decentralization milestone.
2. Predicate synthesis and strengthening — since weak predicates are the likeliest practical
   failure, this may matter more in deployment than any mechanism above.
3. `k`-of-`n` redundant execution for high-value categories, removing the single-TEE dependency.
4. Proof-based verification for sub-steps cheap enough to prove today, composing with attestation
   for the remainder.
5. Learning from verified failures — validated failure data is a corpus of exactly how agents fail,
   with attested evidence of what they did. Deliberately scoped out for now: it is a separate
   contribution and raises unresolved questions about who owns failure data.

---

## In one paragraph

Agent platforms bill for attempts because verifying outcomes has been too expensive to do routinely,
and the mechanisms that solved this for machine computation assume the work can be re-executed.
Agent work cannot be — it is multi-step, tool-using, and side-effecting, and once a repository is
modified or an API called there is no second run to compare against. Mergit attests execution
instead of reproducing it, which makes verification an audit of evidence rather than a repetition of
work, and makes attested cost available as a dimension of trust. Reputation then becomes verified
quality per unit cost, routing becomes a decision policy rather than a ranking, and settlement
becomes revocable. That is what "pay for what you got" means once stated precisely enough to
compute.

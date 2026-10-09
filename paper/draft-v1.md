# Pay for What You Got: Cost-Adjusted Reputation and Runtime-Attested Verification for Autonomous Agent Markets

**Draft v1** — 2026-10-09. Abstract and §1 drafted; remaining sections per
`docs/superpowers/specs/2026-10-09-mergit-research-paper-design.md` §8.
Citations `[n]` resolve against `paper/research.md`.

---

## Abstract

Autonomous agents now perform economically significant work, and the infrastructure to pay them
exists: an HTTP-native stablecoin payment rail processed on the order of 165 million transactions
for roughly 69,000 active agents by April 2026 [4], and an Ethereum standard defines on-chain
registries for agent identity, reputation, and validation [1]. Yet agent platforms bill for
*attempts* rather than *outcomes*. A requester pays for tokens consumed and tool calls issued
whether or not the delegated task was completed, and an agent reporting success it did not achieve
is paid identically to one that succeeded.

A substantial literature already makes outcome-contingent payment work for machine
work — restaking-based verifiable inference posts provider stake, audits probabilistically, and
slashes on detected cheating [34], with optimistic challenge and trusted-execution attestation
combined to lower verification cost [36]. That literature, however, verifies *inference*: a single,
functionally pure, re-executable model call, where the question is whether the contracted model was
run. We observe that it does not transfer to agent work, for a structural rather than economic
reason. An agent task is multi-step, tool-using, and side-effecting; once an agent has mutated a
repository, called an external API, or spent money, the task cannot be re-executed even in
principle. Verification by re-execution is therefore not merely expensive in this setting, it is
frequently undefined — and the inference literature already strains against non-reproducibility in
the far easier deterministic case [37,38].

We present Mergit, an agent execution platform in which identity, verification, settlement, and
routing are properties of the runtime rather than services layered above it. Because Mergit owns
the sandbox, it can attest execution instead of reproducing it: each task yields a *Verifiable
Execution Receipt*, a hardware-attested, tamper-evident record of tool calls, commands, test
outcomes, artifact hashes, and metered token and gas expenditure, committed on-chain by Merkle
root. Verification becomes an audit of evidence, with challenge-driven escalation where
re-execution remains meaningful.

Attested metering makes the paper's principal contribution available: **reputation as verified
quality per unit cost.** Existing systems score output quality [7,8], counterparty satisfaction
[6], or verified activity [10]; none treats cost-efficiency as a dimension of trust, though an
agent succeeding at ten times another's token spend is plainly not its equal. We maintain
decay-weighted Bayesian posteriors over verified success per agent and task category, divide by
metered expected cost, and route tasks in autonomous mode by budget-constrained Thompson sampling
over those posteriors [25,26,27]. We adapt established audit-game deterrence analysis [21,22,34] to
this setting, where the quantity being deterred is a false *attestation* rather than a substituted
computation, and make settlement revocable: a receipt may be challenged after payment, with
clawback against stake.

Mergit is pre-implementation. All results are analytical, and we state explicitly which task
classes admit the verification our claims assume.

---

## 1. Introduction

### 1.1 Agents are paid for effort, not for outcomes

By April 2026, roughly 69,000 autonomous agents had settled some 165 million payments on a single
protocol [4]. None was contingent on verified completion of the work it paid for.

Delegate a task to an autonomous agent today and you will be billed for the attempt. Tokens
consumed, tool calls issued, sandbox minutes elapsed: these are metered precisely and charged
reliably. Whether the task was *done* is not metered at all. The agent reports its own outcome in
natural language, that report is accepted because nothing cheaper is available, and the invoice is
identical whether the work succeeded, silently failed, or was confidently fabricated.

For a human contractor this arrangement would be unusual. For an autonomous one it is the default,
and it degrades in a specific way: as agents take on longer and less supervised tasks, the
requester's ability to check the claim falls exactly as the amount being claimed rises.

### 1.2 The infrastructure exists and is largely unused

Two developments make outcome-contingent agent payment look imminent. Payment rails for machine
counterparties are deployed and carrying real volume: x402 revives HTTP 402 so an agent can pay for
a resource in stablecoins settled on an Ethereum L2, reporting roughly 165 million cumulative
transactions, about $50 million in volume, and some 69,000 active agents by April 2026 [3,4]. In
parallel, ERC-8004 ("Trustless Agents") standardizes the trust primitives: an ERC-721-based
Identity registry, a Reputation registry for client-posted feedback, and a Validation registry
recording independent checks of an agent's work, with heavy artifacts off-chain behind on-chain
pointers and commitments [1]. Marketplace layers add escrow and evaluation; Virtuals Protocol's
Agent Commerce Protocol runs request, negotiation, escrow, evaluation, and settlement on-chain, and
lets accumulated reputation alter the terms an agent is offered [6].

In practice these are not being used as a verified-work market. An empirical study of the ERC-8004
ecosystem finds a large share of registrations are placeholders rather than operational agents [2],
and independent analysis characterizes the standard as lightweight and registry-specific —
supplying identity, feedback, and validation without the broader machinery commerce and trust
require [17]. Demand is also more equivocal than ecosystem messaging suggests: reporting in March
2026 found appetite for agent micropayments weaker than anticipated [5]. Registries nobody writes
meaningful data into are not a trust layer; they are a schema. The question is what prevents the
schema from being populated with claims worth believing.

### 1.3 Why verified payment works for inference but not for agent work

It is not for want of a mechanism. Outcome-contingent payment for machine work is a solved problem
in an adjacent domain. Restaking-based verifiable inference has a provider post stake and privately
choose between running the contracted model and a cheaper substitute, while a verifier re-executes
queries with some probability and an on-chain mechanism schedules audits and slashes stake on
detected cheating [34]. The economics are well understood, including the substitution between audit
budget and other mechanism parameters: raising signal responsiveness cuts the required baseline
audit rate from 0.370 to 0.145 at a discount factor of 0.95, while raising audit rates increases
verification cost linearly across every honest query [34]. Sampling-based verification has
equilibrium treatments [35], optimistic challenge has been combined with trusted-execution
attestation to cut verification cost [36], and cheap-rejection proof modes exist for
resource-constrained verifiers [39].

Every one of these verifies **inference**: one functionally pure model call, re-runnable on demand,
where the question is whether the contracted computation was performed. Agent work has none of
those properties.

An agent task is a *sequence* of decisions interleaved with tool calls, and those tool calls have
effects outside the computation. The agent edits a working tree, opens a pull request, provisions
infrastructure, sends a message, pays for an API. Three consequences follow, and they compound:

1. **Non-reproducibility.** Re-running the task does not re-run the same task. The repository is
   no longer in its prior state, the external service has already received the call, the money has
   already moved. Even where state could be restored, model sampling, tool latency, and external
   responses make the second execution a different trajectory. The inference literature already
   confronts a weak form of this — non-determinism defeats bit-exact comparison even for
   floating-point neural network evaluation [37], motivating work that makes inference
   deterministic precisely so it can be verified [38]. Agent execution is strictly harder: the
   non-determinism is not numerical noise but a different sequence of actions upon a world that has
   already changed.
2. **Irreversibility.** Re-execution as a verification strategy assumes checking is side-effect
   free. For side-effecting work it is not: verifying by redoing would re-send the email and re-pay
   the invoice.
3. **Outcome underdetermination.** "Did you run model X" has a crisp answer. "Was the task done"
   often does not reduce to comparing two outputs, because success is defined over world state
   rather than over a returned value.

So the binding constraint in our setting is not the price of verification but its *definability*.
This is why the deployed answer is billing for effort: not because outcome-contingent payment is
undesirable, nor because its economics are unknown, but because the verification primitive that
makes it work for inference does not exist for agent work.

### 1.4 Mergit: attest execution rather than reproduce it

If work cannot be re-run, verification must rest on evidence produced *while* it ran. That requires
a party positioned to observe execution — and the structural observation driving Mergit is that
none of the systems above is so positioned. ERC-8004 is a registry without a runtime [1]; x402 is a
payment rail without a runtime [3]; ACP is a marketplace without a runtime [6]. None can say what
an agent did; they can only record what some party claimed, or pay to have the work redone.

Mergit is an agent execution platform — harness and sandbox, comparable to existing agent
runtimes — and it makes the runtime an attestor. Each task produces a **Verifiable Execution
Receipt**: a structured, signed record of tool calls made, commands executed, tests run and their
outcomes, hashes of artifacts produced or modified, and metered token and gas expenditure. The
sandbox executes inside a trusted execution environment, so the receipt carries hardware
attestation binding it to a measured runtime image, and a Merkle root is committed on-chain while
the receipt body stays off-chain, following the pointer-and-commitment pattern ERC-8004 establishes
[1].

Verifying a receipt is an audit of evidence rather than a repetition of work: check the attestation,
check the commitment, check that recorded tests and artifact hashes substantiate the claimed
outcome. Where re-execution remains meaningful — a pure, replayable sub-step — it is retained as a
*challenge* escalation, in the manner of verification games for off-chain computation [23] and
optimistic dispute windows [24,36], rather than as the routine path.

We claim no novelty for combining attestation with optimistic challenge; that combination is
published [36]. The contribution is what it is applied to, and what it then makes possible.

### 1.5 Deterrence, adapted

Cheap auditing does not by itself establish honesty, since an operator or agent could emit a false
receipt and hope to escape audit. The deterrent is economic and follows established audit-game
analysis [21,22,34]: agents post stake at registration, receipts proven false on challenge are
slashed, and the audit rate is set so that falsification has negative expected value. Writing `V`
for task payment, `S` for posted stake, `λ` for the slashing fraction, `c_exec` for execution cost
and `c_audit` for audit cost, deterrence requires roughly

```
p* ≈ (V + c_exec) / (λ·S),     giving     C_trust = c_audit + p* · c_exec
```

so collateral trades against audit frequency, and the cost of trust tends toward the cost of an
audit rather than the cost of the task. We present this as an **adaptation rather than a result**:
the substitution of stake for audit budget is established in the verifiable-inference setting [34],
and our contribution is to characterize what changes when the audited object is an *attestation of
a non-reproducible trajectory* rather than a *substituted computation* — in particular, that
challenge cannot always terminate in re-execution, so disputes must resolve against receipt
evidence and attestation integrity, and that `c_audit` is bounded by evidence volume rather than by
task cost.

Identity is priced for the reason reputation systems have always had to price it: costless identity
replacement lets a poor performer discard its history and reappear as a newcomer, forcing the
system to distrust newcomers generally [18,19]. ERC-8004's rationale names this problem [1] without
pricing identity itself. Mergit requires stake at registration — the same stake securing receipts —
and lets verifiable external credentials, in the spirit of domain-linked agent identity [12], reduce
the collateral required at equal deterrence.

### 1.6 The principal contribution: reputation as verified quality per unit cost

Attested metering is a precondition for billing, which means Mergit knows, verifiably, what each
task cost. That makes cost available as a dimension of *trust* rather than merely of accounting,
and this is where our contribution is sharpest, because the prior art does not go here at all. The
verifiable-inference literature builds deterrence mechanisms, not reputation systems [34,35,36].
The agent-economy systems that do build reputation score something else: Bittensor scores output
quality through validator assessment [7,8], ACP records counterparty satisfaction [6], Olas rewards
verified activity and KPI attainment [10]. None ranks agents by verified quality *per unit cost*,
though an agent that succeeds while consuming ten times another's tokens is plainly not its equal,
and a requester paying for outcomes cares about exactly that ratio.

Mergit therefore defines reputation as the posterior expectation of verified success divided by
metered expected cost, per agent and task category, with geometric decay so that reputation tracks
current capability rather than accumulated history. Bayesian posteriors give newcomers wide
uncertainty instead of a zero score, which turns cold-start into an exploration problem rather than
a special case. Autonomous routing follows directly: sample from the posteriors and select the
agent maximizing expected verified success per unit cost within the task's budget — Thompson
sampling [25,26] adapted to a budget-constrained objective after the fashion of bandits with
knapsacks [27]. This replaces static leaderboard ranking with a decision policy, and avoids the
failure mode in which a top-ranked agent absorbs all work while better newcomers are never sampled.

### 1.7 Contributions

1. **Cost-adjusted reputation** (§8): reputation as verified quality per unit metered cost,
   maintained as decay-weighted Bayesian posteriors per task category. The formalization of "pay
   for what you got," and unclaimed in both the verifiable-inference and agent-economy literatures.
2. **The non-reproducibility argument and Verifiable Execution Receipts** (§6): agent work cannot be
   verified by re-execution because it cannot be re-executed; runtime attestation of execution
   evidence is the remaining substrate, available only to a platform that owns the sandbox.
3. **Deterrence under non-reproducible audit** (§7): an adaptation of established stake-and-audit
   analysis [34] to a setting where challenge cannot reliably terminate in re-execution, with
   explicit design rules relating stake, slashing, audit rate, and the cost of trust.
4. **Budget-constrained reputation routing** (§9): autonomous agent selection as a cost-constrained
   bandit over on-chain reputation posteriors, with principled exploration.
5. **Revocable settlement** (§10): post-settlement challenge with clawback against stake,
   transposing challenge-period semantics [24,36] to task-granular agent payment.

### 1.8 Scope and honesty conditions

Mergit is pre-implementation; an earlier prototype was discarded and the system is being rebuilt.
Every quantitative statement here is analytical, and we report no measurements.

Three limits deserve stating at the outset rather than in a closing caveat. First, a receipt
establishes what *ran*, not that an open-ended artifact was *good*: it can substantiate that a test
suite passed or that a specified transformation produced an artifact with a given hash, but it
cannot adjudicate whether an essay was persuasive. Our verification claims apply to task classes
with checkable outcomes — which is why software engineering is the flagship domain — and we are
explicit throughout about where that boundary falls. Second, attestation relocates trust rather
than eliminating it: receipt integrity rests on the trusted execution environment and its vendor,
against an active literature of microarchitectural attacks [28,29]. We treat TEE attestation as the
v1 anchor, layered with staking and challengeability so a compromised operator still faces
slashing, and discuss redundant execution and proof-based verification as the decentralization path
(§14). Third, because disputes over non-reproducible work cannot always be settled by redoing it,
some residual adjudication burden is irreducible; we characterize where it falls rather than
claiming to remove it.

### 1.9 Roadmap

Section 2 states the problem precisely. Section 3 situates Mergit against agent trust, payment, and
marketplace systems, and against the verifiable-inference literature it builds on. Section 4 gives
the design overview and trust boundaries, and Section 5 the threat model. Sections 6 through 9
develop receipts, verification economics, cost-adjusted reputation, and routing. Section 10 covers
settlement and revocability, Section 11 the combined token-and-gas cost strategy, and Section 12
the security analysis. Sections 13 and 14 state limitations and future work.

---

## 2. Problem statement

### 2.1 Setting

A **requester** delegates a **task** to an **agent**, which executes inside a **runtime** operated
by a **platform**. Execution consumes metered resources — model tokens, tool invocations, wall-clock
sandbox time, and on-chain gas where the task touches a chain. A **validator** may be asked to
assess whether the task was performed as claimed. Agents are operated by **operators**, who may run
many agents and who bear the economic consequences of an agent's conduct; the distinction matters
because reputation attaches to identities while incentives attach to operators.

A task carries a payment `V`, agreed in advance or determined by a posted price. The question this
paper addresses is what `V` should be conditional on, and what it costs to make it conditional on
anything at all.

### 2.2 What "the task was done" means

Let a task carry an **outcome predicate** `Φ` over world state: the test suite passes, the pull
request exists and modifies the specified module, the dataset contains the stated number of rows
conforming to a schema. Verification asks whether `Φ` holds after execution.

Tasks differ sharply in how `Φ` can be established, and the distinction organizes the rest of the
paper:

- **Checkable outcomes.** `Φ` reduces to a deterministic test over inspectable artifacts: exit
  codes, test results, file hashes, schema conformance, on-chain state. Establishing `Φ` is cheap
  and does not require repeating the work.
- **Attestable process, underdetermined outcome.** `Φ` is not decidable from artifacts alone, but
  the *process* can be evidenced: which tools ran, which commands executed with which exit status,
  which files changed. Partial assurance is available even where the outcome is not fully
  adjudicable.
- **Judgment outcomes.** `Φ` requires an evaluative assessment — whether an argument persuades,
  whether a design is tasteful. No execution evidence settles these.

We claim verification for the first class, partial assurance for the second, and nothing for the
third. Software engineering is the flagship domain precisely because so much of it falls in the
first class: a repository's state is inspectable and its tests are decidable.

### 2.3 Failure modes

The status quo admits six failure modes, which the design in §4 is accountable to.

**F1 — Fabricated completion.** The agent reports success it did not achieve. Natural-language
self-report is the only evidence, and it is produced by the party being paid.

**F2 — Silent failure.** The agent neither succeeds nor reports failure, because it cannot tell. A
long trajectory ends plausibly without `Φ` holding, and nothing in the billing path distinguishes
this from success.

**F3 — Cost inflation.** Billing by consumption rewards consumption. An agent that reaches the same
outcome by a longer route bills more, and no mechanism prefers the cheaper agent, because cost is
treated as an accounting output rather than a quality signal.

**F4 — Whitewashing.** An agent with a poor record abandons its identity and re-registers as a
newcomer. Where identity is free, reputation cannot be made to stick, and the rational response is
to distrust all newcomers [18,19]. ERC-8004's rationale names this problem directly [1] while
leaving identity unpriced.

**F5 — Price opacity.** The requester cannot tell whether a price reflects the work. Note that a
public ledger does not fix this: on-chain settlement makes prices *auditable after the fact*, not
*competitive at the time of quoting*. Conflating the two is a common error in this design space,
and transparency alone is not a pricing mechanism.

**F6 — Routing ossification.** Where an orchestrator selects agents by rank, the top-ranked agent
absorbs the work, accumulates further evidence, and entrenches. Better newcomers are never sampled,
so the ranking becomes self-confirming rather than informative.

### 2.4 Why self-report cannot be patched

F1 and F2 are not reporting bugs. The agent is the party paid, the report is the only artifact, and
the requester's capacity to check declines as task length grows — exactly as the amount claimed
grows. Adding a confirmation step relocates the problem to whoever confirms: requester attestation
requires the requester to do the work of checking (which is the cost being avoided) and is
vulnerable to inattention and collusion, while validator attestation requires the validator to
establish `Φ` somehow, returning us to the question of how.

The deployed answer in verifiable inference is to establish `Φ` by re-execution under stake and
probabilistic audit [34,35]. §1.3 argued this is unavailable here. We restate it as a requirement
rather than a complaint: **verification must be possible without re-executing the task.**

### 2.5 Requirements

- **R1 — Verification without re-execution.** Establish evidence for `Φ` from the execution itself,
  not from repeating it.
- **R2 — Evidence integrity.** The evidence must not be forgeable by the party being paid, nor by
  the platform if the platform is also the seller.
- **R3 — Bounded verification cost.** The expected cost of verifying a task must not scale with the
  cost of performing it.
- **R4 — Priced identity.** Registering a fresh identity must cost enough that discarding a bad
  record is not profitable, without making entry impossible for honest newcomers.
- **R5 — Cost as a first-class signal.** Resource expenditure must inform agent selection, not only
  billing.
- **R6 — Exploration under routing.** Autonomous selection must retain positive probability of
  sampling under-evidenced agents, or the ranking it consumes degrades.

R1 and R2 are in tension with R3: evidence rich enough to be convincing is expensive to produce and
check, and the integrity guarantee has to come from somewhere. §4 resolves this by making the
runtime itself the evidence producer, and §7 bounds what the resolution costs.

---

## 3. Related work

Work in this area divides into layers that each supply part of a verified-work market. We take them
in turn, then state what remains unsupplied. Throughout, we distinguish what a system *provides*
from what it *assumes*, since the assumptions are where our setting diverges.

### 3.1 Agent identity and trust registries

ERC-8004 ("Trustless Agents") extends agent-to-agent interaction with a trust layer built from
three on-chain registries: an ERC-721-based Identity registry mapping a token to an off-chain
registration document describing endpoints, wallets, and supported trust models; a Reputation
registry through which authorized clients post feedback as scores, tags, and optional URI-plus-hash
references; and a Validation registry recording independent checks of an agent's work [1]. Only
pointers and commitments are held on-chain, with artifacts kept off-chain — a pattern we adopt
directly for receipts (§6). The standard's stated goal is that capable agents should not reset to
zero when entering a new environment and that poor or malicious agents should not cheaply
reintroduce themselves [1].

Two findings qualify its current standing. An empirical study of the deployed ecosystem reports
that a large share of registrations are placeholders rather than operational agents [2], and an
independent analysis characterizes the standard as lightweight and registry-specific, providing
identity, feedback, and validation without the broader machinery that commerce and trust require
[17]. Fetch.ai approaches identity from the credential side, requiring agents to act on behalf of
identifiable users or businesses and linking agents to Web2 domains through an Agent Name Service
so that a verifiable external fact becomes a trust signal [11,12]. We reuse this idea in §8, where
credentials reduce the collateral required at equal deterrence.

What these supply is a *place to record* trust claims. What they assume is that someone, somewhere,
produces claims worth recording — which is the question [2] shows to be open in practice.

### 3.2 Payment rails

x402 revives HTTP 402 as a payment-required response: a server advertises price, accepted tokens,
and destination; the client signs a stablecoin transfer authorization and resubmits; settlement
occurs on-chain, with support across several EVM chains and Solana and zero protocol fees [3]. The
scale is material to our motivation — roughly 165 million cumulative transactions, about $50
million in volume, and some 69,000 active agents reported by April 2026 [4] — though demand for
agent micropayments has also been reported as weaker than ecosystem messaging suggests [5]. Related
proposals formalize agent-to-agent transaction substrates [13] and the broader payment and trust
infrastructure for autonomous agents [16].

The structural limitation for our purposes is that x402 settles payment for *access to a resource*.
The buyer learns whether a response arrived, not whether delegated work was performed, and
settlement is final. Neither outcome-contingency nor revocability is in scope for the rail, which
is why §10 builds them above it rather than expecting them from it.

### 3.3 Marketplaces, escrow, and agent economies

Virtuals Protocol's Agent Commerce Protocol is the closest prior art to Mergit's settlement path:
smart-contract primitives carry a transaction through request, negotiation, escrow, evaluation, and
settlement on-chain, with revenue splits and reputation, such that trusted agents receive more
favorable terms while unknown or dispute-prone agents face stricter conditions or higher fees [6].
Olas (Autonolas) supplies the nearest precedent for binding stake to work rather than to passive
holding: Proof of Active Agent rewards agents that deliver useful, verifiable outcomes — executing
on-chain actions or meeting KPIs — rather than rewarding lockup, alongside bonding for
protocol-owned liquidity and on-chain tracking of code contributions [9,10]. Its Mech Marketplace
lets agents hire one another [10].

Both establish that escrowed, reputation-sensitive agent commerce is implementable today. Both also
assume the evaluation input: ACP's evaluation is a counterparty's assessment of a delivered product,
and PoAA's is activity or KPI attainment reported against the chain. Neither attests *how execution
proceeded*, and neither treats resource expenditure as a trust dimension.

### 3.4 Validator networks and incentive design

Bittensor organizes a market for digital commodities into subnets, each setting its own incentive
mechanism with its own miners and validators: miners perform the subnet's task, validators score
them, and emissions are divided 41% to miners, 41% to validators, and 18% to the subnet owner
[7,8]. Yuma Consensus aggregates validator score vectors by computing a stake-weighted median
benchmark, clipping outlier weights, and allocating emissions proportional to the clipped
aggregate, with validator rewards accruing through exponentially smoothed bonds that penalize
deviation from consensus [8]. We borrow stake-weighted aggregation with outlier clipping for
validator attestations (§7), and note that [8] is a *critical* analysis which we cite as such.

The divergence is economic. Bittensor's rewards are inflation-funded for ongoing commodity
production assessed by sampling, not requester-funded settlements of individual delegated tasks
conditional on an audited record of execution. Scoring an agent's general output quality and
adjudicating whether a specific task was completed are different problems.

### 3.5 Verification economics and optimistic verification

The literature most directly adjacent to our mechanism concerns verifying machine computation under
economic incentives, and it is well developed. Truebit's verification game established sampled
challenge with dispute resolution for off-chain computation [23], and optimistic rollups made
challenge periods with fraud proofs standard infrastructure [24]. Naysayer proofs provide a
cheap-rejection verification mode suited to resource-constrained verifiers such as smart contracts
[39]. Proof of Sampling gives an equilibrium treatment of sampled-audit verification [35].

Most relevant, restaking-based verifiable inference analyzes precisely the incentive structure we
require: a provider posts stake and privately chooses between running the contracted model and a
cheaper substitute, a verifier re-executes queries with some probability, and an on-chain mechanism
schedules audits and slashes a fraction of stake on detected cheating [34]. That work quantifies
the substitutions available to a mechanism designer — raising signal responsiveness cuts the
required baseline audit rate from 0.370 to 0.145 at a discount factor of 0.95, while uniformly
raising audit rates increases verification cost linearly across every honest query [34]. Optimistic
TEE-rollups combine trusted-execution attestation with optimistic challenge in a three-tier design
for generative inference: provisional finality from a TEE attestation quote, a fraud-proof
"fisherman" window, and VRF-triggered stochastic zero-knowledge spot-checks at a sampling rate of
roughly 0.01 [36]. That work also scales assurance to stake at risk, applying a spot-check rate of
zero to a trivial query and one to a high-value trade [36] — a precedent we adopt in §7.2.

Three further aspects of [34] bear on our claims and we record them precisely, since a loose reading
would both over- and under-credit it. Its one-shot incentive test is explicitly *not* presented as
its contribution — it attributes the condition to existing slashing and inspection-game literature,
as we do (§7.2). Its actual thesis is an impossibility result: memoryless bounded-slashing
mechanisms admit profitable deviations under repeated interaction, which is a direct challenge to
any design resting on the one-shot rule, ours included (§7.5). And it does build a reputation
component — a Bayesian posterior over provider type used to weight *penalties* — together with a
formal treatment of whitewashing giving conditions under which respawning a fresh identity is
unprofitable, which we cite in §8.6 alongside the classical sources.

**We build on this rather than compete with it, and state plainly what it means for our claims.**
That assurance can be traded across mechanism parameters, and specifically that signal
responsiveness substitutes for baseline audit budget, is established in [34], not contributed here;
that attestation can be combined with optimistic challenge is published in [36], not contributed
here. Our §7 is an adaptation of this lineage, and §7.5 is a response to its strongest objection
rather than an extension of its favorable results.

One observation in [34] strengthens our position rather than weakening it. It notes that
re-execution audits are themselves noisy — floating-point non-determinism and hardware heterogeneity
can produce false disagreement between an honest provider and an honest auditor. If re-execution is
already an imperfect oracle for a single pure inference call, the case for treating it as the
foundation of verification for multi-step side-effecting work is weaker still.

What every one of these assumes is re-executability, and in the clearest case the assumption is
explicit rather than implicit: [36]'s dispute path has a challenger recompute the model locally
*under bit-wise deterministic settings* and compare, with divergence resolved by interactive
bisection — first over transformer layers, then over individual matrix multiplications — until a
single disputed operation can be executed on-chain. Deterministic replay is not an incidental
feature of that design but the terminating step of its dispute protocol, and bit-wise determinism is
a stated precondition.

The literature's own difficulties when the assumption weakens are instructive: non-determinism
defeats bit-exact comparison even for floating-point neural network evaluation, requiring
nondeterminism-aware protocols [37], and a parallel line of work engineers determinism into
inference specifically so that results can be verified [38]. Agent
execution violates the assumption outright and not marginally — the non-determinism is not
numerical noise but a different sequence of actions upon a world the first execution already
altered (§1.3). To our knowledge no existing protocol verifies multi-step, tool-using,
side-effecting agent work under economic incentives, and that is the gap we address.

### 3.6 Reputation systems

That costless identity undermines reputation is long established: the Sybil attack formalizes the
general case [18], and the social cost of cheap pseudonyms explains why costless identity
replacement forces systems to distrust newcomers as a class [19] — the direct motivation for pricing
registration (§8) rather than merely penalizing poor records. EigenTrust supplies classical
machinery for aggregating reputation in decentralized networks [20]. Our departure is not in the
aggregation but in what is aggregated: these systems, and the agent-economy systems of §3.3–3.4,
score quality or satisfaction, whereas we score verified quality per unit metered cost.

### 3.7 Summary

| Layer | Representative work | Supplies | Assumes / omits |
|---|---|---|---|
| Identity & trust registries | ERC-8004 [1], Fetch.ai ANAME [12] | Where to record identity, feedback, validation | Assumes claims worth recording; largely non-operational in practice [2,17] |
| Payment rails | x402 [3,4], Agent TCP/IP [13] | Machine-to-machine settlement at scale | Pays for access, not verified outcome; final, non-revocable |
| Marketplaces & escrow | Virtuals ACP [6], Olas [9,10] | Escrow, evaluation, reputation-sensitive terms | Evaluation is counterparty judgment or KPI report; no execution attestation; cost not a trust signal |
| Validator incentives | Bittensor [7,8] | Stake-weighted validator scoring at scale | Inflation-funded commodity production, not per-task settlement |
| Verification economics | Restaking inference [34], Proof of Sampling [35], optimistic TEE [36], Truebit [23], rollups [24], naysayer [39] | Stake, probabilistic audit, slashing, challenge periods; repeated-game analysis and reputation-weighted penalties [34]; tiered attestation plus ZK spot-checks [36] | **Assumes re-executability** — dispute resolution terminates in deterministic replay [36]; reputation weights penalties, not selection, and excludes cost [34] |
| Reputation theory | Sybil [18], cheap pseudonyms [19], EigenTrust [20] | Why identity must be priced; aggregation machinery | Scores quality, not quality per unit cost |

The gap is the intersection: no system verifies non-reproducible, side-effecting agent execution,
and none makes resource efficiency a dimension of trust. Mergit targets exactly that intersection,
and §4 describes how.

---

## 4. Design overview

### 4.1 Components

Mergit comprises six components, each with one responsibility and a defined interface.

1. **Attested runtime (harness and sandbox).** Executes agent tasks. Meters model tokens, tool
   invocations, and gas. Emits a signed Verifiable Execution Receipt per task with a Merkle
   commitment over its contents. Runs inside a trusted execution environment so that receipts carry
   hardware attestation binding them to a measured runtime image. This is the only component that
   can assert what happened during execution.
2. **Identity registry.** ERC-8004-compatible agent identity [1]. Stake is posted at registration;
   verifiable external credentials reduce the stake required at equal deterrence (§8). Identities
   are held by operators, who may hold several.
3. **Validation layer.** Samples submitted receipts at rate `p` derived from task value, stake, and
   slashing fraction (§7); audits sampled receipts against their commitments and attestations;
   escalates to adjudication on challenge; writes attestations to the Validation registry.
   Validator scores are aggregated stake-weighted with outlier clipping, following [8].
4. **Reputation engine.** Maintains decay-weighted Beta posteriors over verified success per
   (agent, task category) together with metered cost estimates, and exposes cost-adjusted scores
   (§8). Derives only; asserts nothing of its own.
5. **Settlement.** Holds payment in escrow, releases on validated completion, and supports
   post-settlement challenge with clawback against stake (§10). Operates in two tiers: an unsecured
   onboarding tier on faucet credits, and a staked production tier on a connected wallet,
   x402-compatible where the rail fits [3].
6. **Orchestrator.** Human-in-the-loop by default. In autonomous mode, routes tasks by
   budget-constrained Thompson sampling over reputation posteriors (§9).

### 4.2 Task lifecycle

A staked-tier task proceeds as follows.

1. **Specification.** The requester submits a task with an outcome predicate `Φ` (§2.2), a budget,
   and a category. Where `Φ` is expressed as an executable check — a test command, a schema, an
   expected artifact hash — it becomes part of the receipt's evidence requirements.
2. **Routing.** The orchestrator selects an agent: the requester's choice under human-in-the-loop,
   or a draw from the reputation posteriors under autonomous mode (§9).
3. **Escrow.** Payment `V` is locked. The agent's stake `S` is already posted and is now encumbered
   for the duration of the dispute window.
4. **Execution.** The attested runtime executes the task, metering expenditure and recording tool
   calls, commands and exit statuses, artifact hashes, and evaluations of `Φ` where executable.
5. **Receipt.** The runtime emits a signed receipt with hardware attestation; its Merkle root and a
   pointer to the body are committed on-chain.
6. **Validation.** With probability `p`, the validation layer audits the receipt: attestation
   validity, commitment consistency, and whether the recorded evidence substantiates `Φ`.
7. **Settlement.** On a passing audit — or on no audit being drawn — escrow releases to the agent.
   On a failing audit, escrow returns to the requester and slashing proceeds against `S`.
8. **Dispute window.** For a bounded period after settlement, any party may challenge the receipt,
   forcing adjudication; a successful challenge triggers clawback (§10).
9. **Reputation update.** The verified outcome and metered cost update the agent's posterior for
   that category (§8).

### 4.3 Trust boundaries

The design is only as clear as the question "who is allowed to assert what," so we state it
explicitly.

| Party | May assert | May not assert |
|---|---|---|
| Agent | Its own trajectory, as a claim subject to attestation | That its outcome was correct |
| Attested runtime | What executed, with hardware attestation | Whether the outcome satisfies a judgment predicate |
| Validation layer | That a receipt is or is not consistent with `Φ` | What happened outside the receipt |
| Reputation engine | Derived scores over validated history | Any primary fact |
| Chain | Commitments, stake, escrow state, settlement | Anything about execution content |
| Requester | The predicate `Φ` and the budget | That work failed, without challenge and adjudication |

Two consequences are worth drawing out. First, the platform is a party, not a neutral oracle: if it
both sells execution and attests to it, the attestation must be grounded in something the platform
cannot forge, which is what the TEE requirement is for (§6) and why operator stake and
challengeability are retained even under attestation (§12). Second, no component is permitted to
assert a judgment outcome, which is how the design keeps the honest-scope boundary of §2.2 from
quietly eroding under product pressure.

### 4.4 On-chain and off-chain division

On-chain: identity and stake, receipt commitments (Merkle roots and pointers), validator
attestations, escrow and settlement state, reputation posteriors or their commitments. Off-chain:
receipt bodies, execution artifacts, evidence for `Φ`, and audit workpapers. This follows ERC-8004's
pointer-and-commitment pattern [1] for the reason that motivates it there — on-chain storage of
execution evidence would be prohibitive — and it is also the lever for the gas side of the cost
analysis in §11.

### 4.5 Tiers

The onboarding tier issues faucet credits so that a new user can run tasks without funding a
wallet. Because free credits imply zero effective stake, the deterrence analysis of §7 does not
apply to that tier, and we do not pretend otherwise: onboarding-tier tasks are audited at `p = 1`
with the verification cost absorbed as a subsidy, are rate-limited and value-capped to bound that
subsidy, and do not accrue reputation that transfers to the staked tier. The onboarding tier buys
onboarding, not trust. Trust begins at stake.

---

## 5. Threat model and assumptions

### 5.1 Adversaries

**A1 — Dishonest agent.** Seeks payment without performing work. It controls its own trajectory and
its natural-language report, and may terminate early, fabricate a summary, or pursue the cheapest
path that superficially resembles completion. It cannot sign a receipt, because receipts are emitted
by the runtime rather than by the agent.

**A2 — Dishonest operator.** Controls one or more agent identities and possibly runtime
infrastructure. Capabilities: registering many identities, abandoning an identity after a poor
record (F4), and forging or selectively suppressing receipts if runtime integrity can be subverted.
This is the strongest adversary in the model, because an operator who can forge receipts defeats
the verification path entirely.

**A3 — Colluding requester.** Cooperates with an agent to manufacture favorable validated history —
submitting trivial tasks with trivially satisfiable predicates — inflating reputation for later use
against honest requesters.

**A4 — Lazy or adversarial validator.** Accepts receipts without auditing them, saving `c_audit`, or
rejects honest receipts to damage a competitor.

**A5 — Compromised trusted execution environment.** Breaks the attestation assumption through
microarchitectural or side-channel attack [28,29], thereby enabling A2's forgery.

### 5.2 Assumptions

1. **Attestation soundness (defeasible).** A TEE-attested receipt reflects what executed, unless the
   TEE is compromised (A5). We treat this as a defeasible assumption with layered fallbacks (§5.4,
   §12), not as a guarantee.
2. **Commitment integrity.** Hash and Merkle commitments are collision-resistant; chain state is
   final after standard confirmation.
3. **At least one motivated challenger.** For any task whose value exceeds the cost of challenging,
   some party — requester, competing agent, or professional challenger — is willing to challenge a
   suspicious receipt. This is the liveness assumption optimistic systems already rest on [24,36],
   and it is an assumption rather than a result.
4. **Economic rationality.** Adversaries maximize expected value and are deterred by negative
   expected value. Griefing adversaries who accept losses to harm others are addressed only
   partially (§12).
5. **Metering integrity.** Token and gas accounting is produced inside the attested runtime and so
   inherits assumption 1. Cost-adjusted reputation is only as sound as metering.

### 5.3 Out of scope

Specification failures in which an agent competently performs the wrong task because `Φ` was
mis-stated; prompt injection against agents, which the agentic-commerce security literature treats
systematically [14]; chain-level consensus attacks; and the legal enforceability of clawback against
an operator who exits. Judgment outcomes remain out of scope throughout (§2.2).

### 5.4 Two design calls this threat model forces

Two decisions follow from A2 and A4 rather than from preference, and we state them here because they
shape §6 and §7.

**Receipts commit to everything and disclose selectively.** Were a receipt to disclose only
outcome-bearing evidence, A2 could suppress inconvenient steps and present a clean subset. The
receipt therefore commits to the *complete* trajectory as a hash chain over sequentially numbered
steps, so omissions and reorderings are detectable, while *disclosure* defaults to the
outcome-bearing subset, with full disclosure compelled under challenge via Merkle paths (§6.3). This
keeps `c_audit` proportional to disclosed evidence rather than to trajectory length, and avoids
routinely exposing requester prompts, proprietary code, and credentials to validators.

**Auditing is permissioned at v1; challenging is permissionless from the start.** Bootstrapping a
staked validator market is a different problem from verifying agent work, and under assumption 1 a
routine audit is largely mechanical: check the attestation, check commitment consistency, check that
disclosed evidence substantiates `Φ`. Mergit therefore operates validators itself at v1. The
integrity of the arrangement does not rest on trusting the platform, because *challenge* is open to
anyone posting a bond (§10.3): a platform colluding with an operator to wave through false receipts
remains exposed to challenge by the requester or any observer, and the platform's own stake is
slashable. We state plainly that this leaves v1's routine verification path centralized — a fair
criticism of a system presented in a decentralization idiom — and treat a permissionless staked
validator set as the first item on the decentralization path (§14).

---

## 6. Verifiable Execution Receipts

### 6.1 What a receipt must establish

A receipt serves three distinct readers, and conflating their needs is how receipt designs become
either unusably large or uselessly thin. A **validator** needs enough to decide whether `Φ` holds.
A **challenger** needs enough to demonstrate that a validator's decision was wrong. A **reputation
engine** needs verified outcome and metered cost, and nothing else.

Accordingly a receipt must establish: that it was produced by a genuine Mergit runtime executing a
known image (attestation); that it describes one complete trajectory with nothing omitted
(completeness); that specified evidence bears on `Φ` (relevance); and that metered expenditure is
accurate (metering). Completeness is the property most easily lost and the one A2 attacks.

### 6.2 Structure

A receipt consists of a header, a hash-chained step sequence, an evidence set, and a meter.

**Header.** Task identifier, requester and agent identities, the predicate `Φ` as submitted, budget,
runtime image measurement, TEE attestation quote over the image measurement and the receipt root,
and the timestamp range of execution.

**Step sequence.** Execution is recorded as steps `s_1 … s_n`, each a tuple of monotonic sequence
number, step type (model call, tool invocation, command execution, artifact write), a digest of
inputs, a digest of outputs, exit status where applicable, and metered cost for that step. Steps are
hash-chained:

```
h_0 = H(header)
h_i = H(h_{i-1} ‖ s_i)        for i = 1 … n
root = MerkleRoot(s_1 … s_n)
```

The chain makes omission and reordering detectable: a receipt claiming `n` steps with terminal hash
`h_n` cannot drop `s_j` without recomputing every subsequent link, and the attestation covers the
terminal hash. Sequence numbers are monotonic and gapless by construction, so a gap is itself
evidence of tampering. What the chain cannot do is prove that the runtime recorded a step it chose
never to record at all — completeness relative to *reality* rests on attestation (assumption 1),
which is precisely why §5.4 keeps operator stake and permissionless challenge in place beneath it.

**Evidence set.** A distinguished subset of steps marked as outcome-bearing: test invocations and
their exit statuses, artifact hashes before and after, schema validations, on-chain transaction
hashes. Where `Φ` was submitted as an executable check, its invocation and result are necessarily
members of this set. This subset is what a validator reads by default.

**Meter.** Totals for model tokens by model, tool invocations, sandbox wall-clock time, and gas,
each reconcilable against the per-step costs in the chain. Reconcilability matters: a validator can
verify totals against the disclosed subset only partially, but any inconsistency between the
disclosed per-step figures and the claimed totals is detectable without full disclosure.

### 6.3 Commitment and selective disclosure

Only `root`, `h_n`, the attestation quote, and a pointer to the receipt body go on-chain, following
ERC-8004's pointer-and-commitment pattern [1]. The body is stored off-chain, encrypted, with
decryption keys held by the requester and escrowed for compelled disclosure.

Disclosure proceeds in three levels:

- **Level 0 (settlement).** The on-chain commitment, the meter totals, and the verdict on `Φ`. This
  is what the reputation engine consumes and the only level most tasks ever reach.
- **Level 1 (audit).** The evidence set with Merkle paths to `root`. A validator checks the paths,
  the attestation, and whether the evidence substantiates `Φ`. `c_audit` is driven by this level,
  and it is bounded by evidence volume rather than trajectory length — the property §7 requires.
- **Level 2 (challenge).** Full trajectory disclosure, compelled on a bonded challenge, with Merkle
  paths permitting verification of any step against the same `root`. Because disclosure is
  verifiable against a commitment published *before* the dispute, a party cannot revise history
  after a challenge is filed.

The motivation for tiered disclosure is not ours and we do not present it as such. [36] already
discloses only the specific divergent state during a dispute, explicitly to protect the user's
prompt, and criticizes full-trace reproduction approaches on precisely these privacy grounds. Our
contribution at this layer is narrower: extending selective disclosure from a *tensor-level
divergence point* in a deterministic computation to an *evidence subset of a multi-step trajectory*,
where there is no divergence point to isolate because there is no second execution to diverge from.

The privacy consequence is worth stating directly, since it cuts both ways. Default non-disclosure
protects requester prompts and proprietary artifacts from validators, which is necessary for the
system to be usable on real work. It also means routine audits verify less than a full replay
would, and the design accepts that: the commitment ensures a challenger can always escalate, so the
guarantee is not "every task was fully examined" but "every task remains examinable, and
examination cannot be evaded."

### 6.4 What a receipt does not establish

A receipt cannot establish that an unrecorded side effect did not occur outside the sandbox —
network egress controls, not receipts, constrain that. It cannot establish that a passing test was
an adequate test; a requester who submits a weak `Φ` gets weak assurance, and §12 discusses
predicate quality as an attack surface. It cannot adjudicate judgment outcomes (§2.2). And it
cannot, by itself, defeat A5: a compromised TEE produces well-formed receipts about fictional
execution, which is why attestation is layered with stake and challenge rather than trusted alone.

---

## 7. Verification economics

### 7.1 The quantity to bound

From R3, expected verification cost per task must not scale with execution cost. Let `p` be the
probability that a receipt is audited at Level 1, `c_audit` the cost of such an audit, `V` the task
payment, `S` the agent's posted stake, and `λ ∈ (0,1]` the slashing fraction. Write `c_exec` for
execution cost and `q` for the probability that a false receipt which escapes audit is nonetheless
challenged within the dispute window (assumption 3).

Expected platform verification cost per task is

```
C_trust(p) = c_audit · p  +  (expected adjudication cost)
```

where adjudication is incurred only on challenge and is therefore weighted by a small probability.
The contrast with re-execution verification is immediate: there, verification cost per audited task
is at least `c_exec`, so `C_trust ≈ c_exec` at `p ≈ 1`. Here `c_audit` is set by disclosed evidence
volume (§6.3), which for a typical software task is a few test invocations and artifact digests
rather than a full trajectory replay. The design goal is that `c_audit ≪ c_exec`, and the structural
reason it holds is that auditing reads evidence while re-execution reproduces work.

### 7.2 Deterrence

An agent contemplating a false receipt compares the gain from doing so against the expected penalty.
Submitting a false receipt yields `V` while avoiding `c_exec`, so the gain is `g = V + c_exec`.
Detection occurs if the receipt is audited, or if it escapes audit but is successfully challenged:

```
P(detect) = p + (1 − p)·q
```

Falsification is irrational when

```
(p + (1 − p)·q) · λ·S  >  V + c_exec
```

and in the conservative case `q = 0`, where no challenger materializes, this reduces to the familiar
inspection-game threshold

```
p*  =  (V + c_exec) / (λ·S)
```

This condition belongs to the inspection-game and proof-of-stake slashing lineage [21,22], and we
claim no part of it. [34] states the same test as its Definition 1 ("1-Round incentive
compatibility", `cαS ≥ Δ` in its notation), likewise attributing it to existing literature rather
than claiming it — **and then devotes itself to showing that it is insufficient.** Section 7.5
addresses that argument, which bears directly on whether the rules below are safe to rely on. Three
design rules follow from the one-shot condition; §7.5 then qualifies them.

*Notation warning for readers of [34]:* its `α` is our `λ` (slashing fraction), while its `λ`
denotes an exponential-weighting parameter unrelated to slashing.

**Rule 1 — Stake scales with task value.** `p* ≤ 1` requires `λ·S ≥ V + c_exec`. An agent's
accessible task value is therefore capped by its collateral: `V ≤ λ·S − c_exec`. This is the
mechanism by which Mergit refuses to let an under-collateralized agent accept a task whose
falsification it could profit from. The principle that assurance should scale with value at risk is
established: [36] varies its spot-check rate from zero on a trivial query to one on a high-value
trade. We apply it to collateral rather than to sampling rate, and extend it in §10.2 to the length
of the dispute window.

**Rule 2 — Challenge relaxes the audit requirement.** With `q > 0` the required audit rate falls to
`p* = (g/λS − q)/(1 − q)`, so a credible challenger population is economically equivalent to a
larger audit budget. This is the same substitution structure [34] identifies between mechanism
responsiveness and baseline audit rate, and it is why §5.4 makes challenge permissionless even
while auditing is not.

**Rule 3 — Verification cost is bounded by collateral, not by task cost.** Substituting `p*` into
§7.1 gives

```
C_trust(p*) = c_audit · (V + c_exec) / (λ·S)
```

which decreases in `S` and is proportional to `c_audit` rather than to `c_exec`. Since R3 asked only
that verification cost not scale with execution cost, Rule 3 satisfies it provided `c_audit` stays
bounded as `c_exec` grows — which §6.3 secures by sizing audits to evidence rather than to
trajectories.

### 7.3 What changes when work is not re-executable

The adaptation is not merely notational, and three differences matter.

**Adjudication cannot always terminate in re-execution.** In verifiable inference, a dispute ends by
recomputing the function and comparing [34,35]; in optimistic rollups, by replaying a deterministic
state transition [24]. For a side-effecting agent trajectory, neither is available in general. A
challenge therefore resolves against *evidence* — Level 2 disclosure, attestation validity,
consistency of the hash chain, and whether the disclosed trajectory substantiates `Φ` — rather than
against a recomputed ground truth. Where a sub-step *is* replayable (a pure function, a
deterministic build, a test run against a pinned artifact), re-execution is used as a bounded
sub-procedure, which recovers part of the strength of the inference setting without requiring the
whole task to be reproducible.

**The audited object is an attestation, not a computation.** Consequently the dominant residual risk
shifts from "did the provider substitute a cheaper model" to "is the attestation genuine," which is
a hardware-trust question (A5) rather than an economic one. Deterrence addresses the operator who
might forge; it does not address the vendor whose TEE is broken. This is a different risk profile
from [34]'s, and we regard it as the principal cost of our approach rather than a detail.

**Residual adjudication burden is irreducible.** Because some disputes turn on whether disclosed
evidence supports `Φ` rather than on a recomputation, a human or protocol-level judgment remains in
the loop for contested cases. We do not claim to remove it. What the design claims is narrower and,
we think, sufficient: that this burden falls only on *challenged* tasks, that it is bounded by
evidence rather than by work, and that its frequency is controllable through `S`, `λ`, and the
challenge bond rather than being incurred on every task.

### 7.4 Worked illustration

The following is illustrative arithmetic on the model above, not a measurement; Mergit is
pre-implementation (§1.8).

Take a software task with `V = $2` and `c_exec = $1` in model tokens, and suppose a Level 1 audit
costs `c_audit = $0.02` — reading a handful of test results and artifact digests with Merkle-path
checks. With `λ = 1` and `q = 0`:

- At `S = $30`, Rule 1 is satisfied and `p* = 3/30 = 0.10`. Expected verification cost is
  `0.02 × 0.10 = $0.002` per task, against `c_exec = $1`.
- At `S = $300`, `p* = 0.01`, and expected verification cost falls to `$0.0002`.
- Under re-execution verification at `p = 1`, verification would cost about `$1` per task — on the
  order of the work itself, and half the task's price.

With even a weak challenger population at `q = 0.05`, Rule 2 drops the required audit rate at
`S = $30` from 0.100 to `(0.1 − 0.05)/0.95 ≈ 0.053`.

That example exposes a threshold worth stating separately, since it is the sharpest form of Rule 2.
Challenge alone suffices — `p* ≤ 0` — exactly when

```
q  >  g / (λ·S)
```

At `S = $30` and `g = $3` the threshold is `q = 0.1`: if a false receipt faces better than a one-in-ten
chance of being challenged, routine auditing is economically unnecessary, and the platform's audit
budget can be spent entirely on making challenge attractive instead. This reframes the design target
away from "audit enough tasks" and toward "ensure challenge is credible," which is a considerably
cheaper objective — one bonded challenger watching a category can discipline every agent in it. It
also tightens the argument for permissionless challenge in §5.4: that decision is not a
decentralization gesture but the cheapest available source of deterrence.

The qualitative point is the one the paper rests on. The cost of trust lands in fractions of a cent
against a dollar of work, where re-execution verification would cost about a dollar — half the
task's price. That difference is what makes outcome-contingent settlement affordable at task
granularity rather than only for high-value contracts.

### 7.5 Repeated interaction, and why the one-shot rule is not enough

The analysis so far is one-shot: it asks whether falsifying *this* receipt has negative expected
value. [34] argues that this is the wrong question for a provider who interacts with the protocol
repeatedly, and the argument applies to us directly.

Its Definition 4 identifies a class of *memoryless bounded-slashing* mechanisms, characterized by
three properties: audit decisions are independent of history, slashing is bounded by some
`α_max · S`, and mechanism decisions depend on history only through current stake. Its Theorem 4.2
shows that mechanisms in this class admit profitable repeated-game deviations whenever slashing is
partial. **The rule of §7.2 as stated satisfies all three properties, so Mergit as specified so far
falls inside that impossibility class.** The exposure is worse than generic, because [34] reports
the gap is largest for patient providers holding high stake relative to per-query rewards — and
Rule 1 *mandates* a high stake-to-value ratio, placing a well-collateralized Mergit agent in
precisely the adverse regime.

We take this as a correction to the mechanism rather than a limitation to be noted in passing. Two
responses are available.

**Full slashing.** [34] confirms that `λ = 1` closes the repeated-game gap, and the illustration in
§7.4 already assumes it. We decline to rely on this alone, for a reason specific to our setting:
[34] observes that deployed systems retain partial slashing because false positives then destroy an
entire stake, and our false-positive risk is *higher* than in the deterministic case, since
adjudication rests on whether disclosed evidence substantiates `Φ` rather than on a recomputation
that either matches or does not (§7.3). A mechanism whose safety depends on never wrongly slashing
in full is not one we want to lean on where adjudication is judgment-laden.

**History-dependent auditing.** The more promising escape is to break the memorylessness property
itself, and the material to do so already exists in this design. §8 maintains per-agent,
per-category Bayesian posteriors over validated success; coupling the audit rate to those posteriors
makes audit decisions depend on history through something other than current stake, which violates
the first and third conditions of Definition 4. Concretely, let

```
p_t(a,k) = p* · f(posterior_{a,k})
```

with `f` increasing in posterior uncertainty and in recent validated failures, and decreasing — but
bounded strictly away from zero — over a long clean validated record. A defection becomes costly
beyond the immediate task, because it raises the agent's own future audit rate and so the cost of
every subsequent defection.

Two cautions attach to this, and they are design constraints rather than afterthoughts. First, `f`
must be bounded below: an agent whose audit rate approached zero on reputation alone would face
exactly the one-shot calculation again at a lower `p`, which is the deviation [34] identifies.
Second, the coupling runs in both directions — reputation now feeds audit scheduling while audited
outcomes feed reputation — so `f` must escalate sharply enough on failure that the expected penalty
from a defection exceeds the accumulated saving from a reduced audit rate. Tuning `f` is a mechanism
design problem in its own right.

We do not claim to have solved it. What we claim is narrower: the one-shot rule of §7.2 is
insufficient under repeated interaction, the escape route runs through history-dependent auditing,
and that route is unusually cheap for Mergit because the required posteriors are already maintained
for routing. Establishing that a particular `f` satisfies [34]'s repeated-game incentive
compatibility is stated as open work (§14), and until it is established the conservative deployment
posture is `λ = 1` with the false-positive caveat above.

---

## 8. Cost-adjusted reputation

### 8.1 Why cost belongs in trust rather than in accounting

Every system surveyed in §3 that scores agents scores some notion of quality: validator-assessed
output [7,8], counterparty satisfaction [6], or verified activity against KPIs [10]. Cost appears in
these systems only as a billing output.

One precision is required, because the nearest prior art is nearer than a casual survey suggests.
[34] does maintain a Bayesian posterior over a provider's type, and uses it to scale slashing — so
"this literature has no reputation" would be false, and we do not say it. What it does not do is use
that posterior to *select* a provider, nor include cost in it: reputation there weights punishment
after the fact, within a fixed provider relationship. Our use is different in both respects. The
posterior is a selection signal (§9), and its denominator is metered cost. The claim we defend is
therefore specific — reputation as *verified quality per unit cost*, used for *routing* — not the
broader and incorrect claim that reputation is unused in this literature. We argue it belongs in the trust signal itself, for a reason
that follows directly from what a requester is buying.

A requester delegating a task has a budget and an outcome predicate. Two agents that both satisfy
`Φ`, one consuming ten times the tokens of the other, are not equally good suppliers of that
outcome — and a reputation system that rates them identically gives the orchestrator no basis for
preferring the cheaper one. Worse, under consumption billing the expensive agent is *more*
profitable to the platform, so absent an explicit signal the incentives point the wrong way (F3).
Making efficiency part of reputation is what converts "pay for what you got" from a billing slogan
into a selection criterion.

This is available to Mergit specifically because metering is attested (§6.2). A platform that cannot
prove what a task cost cannot safely rank by cost, since cost claims would be the cheapest thing in
the system to falsify. Attested metering is therefore not a convenience here; it is the
precondition that makes the contribution possible, and it is why this section depends on §6.

### 8.2 Posterior over verified success

Fix an agent `a` and a task category `k`. Let `θ_{a,k} ∈ [0,1]` be the probability that `a` produces
a validated success in `k`. Validated outcomes are Bernoulli observations, so we maintain a Beta
posterior with geometric decay applied before each update:

```
on validated success:   α ← γ·α + 1,   β ← γ·β
on validated failure:   α ← γ·α,       β ← γ·β + 1
```

with `γ ∈ (0,1]` and prior `(α_0, β_0)`. Only *validated* outcomes update the posterior:
unaudited tasks that settle without challenge contribute nothing, which keeps the signal grounded
in evidence rather than in volume. This has a cost — most tasks are never audited at the equilibrium
rates of §7.2, so evidence accrues slowly — and §8.7 addresses what that implies for how quickly
reputation can be trusted.

Decay bounds the influence of history. The posterior's effective sample size tends to `1/(1 − γ)`,
so `γ = 0.95` corresponds to an effective memory of roughly twenty validated observations: an agent
that degrades after a model change is re-rated within tens of validated tasks rather than being
protected indefinitely by past performance. Conversely `γ = 1` recovers the undecayed case, in which
a long record becomes an unchallengeable moat.

These posteriors have two consumers rather than one. Routing samples from them (§9), and audit
scheduling is coupled to them (§7.5) to escape the memorylessness that makes a one-shot audit rule
vulnerable under repeated interaction. The second use is why the posterior must remain cheap to
maintain and difficult to manipulate: it is no longer only a selection signal but part of the
verification mechanism, so the manipulation resistance discussed in §8.7 protects deterrence and not
merely routing quality.

### 8.3 Posterior over cost

Cost is positive and continuous rather than binary, so it needs a separate treatment. Let
`c_{a,k} > 0` denote metered cost per task, taken from the receipt meter (§6.2) and therefore
attested. Modeling cost as exponential with rate `r_{a,k}` admits a conjugate Gamma posterior with
the same decay discipline:

```
shape:  κ ← γ·κ + 1
rate:   τ ← γ·τ + c_observed
```

giving posterior mean cost `Ê[c_{a,k}] = τ/κ`. We use cost observations from *all* completed tasks,
successful or not, because an agent that burns budget before failing imposes that cost on the
requester regardless of outcome — scoring cost only on successes would hide exactly the behavior
most worth penalizing.

The exponential-Gamma choice is a modeling convenience, and we flag it as such: agent task costs are
plausibly heavier-tailed than exponential, and a log-normal or Gamma likelihood with unknown shape
would fit better at the price of conjugacy. Nothing in the routing policy of §9 depends on the
particular family, only on having a posterior over cost from which to sample.

### 8.4 The score: value density

We define the **value density** of agent `a` in category `k` as

```
D_{a,k}  =  E[θ_{a,k}] / E[c_{a,k}]  =  (α / (α + β)) · (κ / τ)
```

the expected validated successes per unit expected spend.

A point of rigor deserves stating, because it is easy to get wrong: `D` is a ratio of expectations,
not the expectation of a ratio, and `E[θ]/E[c] ≠ E[θ/c]` in general. We intend the ratio of
expectations, and the justification is a renewal-reward argument rather than a convenience. A
platform routing many tasks to an agent accumulates total validated successes and total spend; by
the law of large numbers the realized ratio of those aggregates converges to `E[θ]/E[c]`, not to
`E[θ/c]`. Since what the requester and platform care about is successes per unit of money actually
spent over a stream of tasks, the ratio of expectations is the correct functional, and the
distinction is not a technicality we are eliding but the reason the definition takes this form.

### 8.5 Category structure and partial pooling

Categories are coarse task types — code modification, test repair, dependency upgrade, data
transformation, documentation — assigned at submission and recorded in the receipt header. Too few
categories and the score conflates unlike work, which is the failure mode of a single global trust
number; too many and no category ever accumulates enough validated evidence to be informative.

We therefore pool partially across categories rather than treating them as independent. Each agent
has a category-level posterior and an agent-level posterior, with the agent-level posterior serving
as the prior for a category in which evidence is thin:

```
(α_0, β_0)_{a,k}  =  (w · ᾱ_a,  w · β̄_a)
```

for a pooling weight `w` that is small relative to the evidence a category eventually accumulates.
An agent with a strong record in test repair thus begins test *authoring* with a weakly favorable
prior rather than from ignorance, while sustained category-level evidence eventually dominates the
pooled prior. This is standard hierarchical shrinkage, and it buys a practical property: the
category taxonomy can be refined over time without resetting every agent's standing.

### 8.6 Cold start

New identities receive wide posteriors rather than zero scores, which is what makes exploration
(§9) principled instead of charitable: an agent with `(α, β) = (1, 1)` has an uninformative
posterior, so Thompson sampling will occasionally draw it and generate the evidence that resolves
it.

Pricing registration is also treated formally in the staked-provider setting: [34] gives conditions
under which abandoning an identity and respawning is unprofitable, relating registration cost to the
discounted value of a continuing relationship and to the penalty an accumulated posterior implies.
That result is the closest quantitative counterpart to the classical whitewashing arguments
[18,19], and a production parameterization of Mergit's registration stake should be checked against
it rather than set by intuition.

Verified external credentials (decision 7) reduce the stake required at registration (§7.2, Rule 1).
Whether they should also sharpen the prior is a separate question, and we answer it conservatively:
credentials may shift the prior mean modestly but must not substitute for validated evidence,
because a credential attests to an operator's identity or standing elsewhere, not to this agent's
performance here. Letting credentials carry significant prior weight would reintroduce a
whitewashing path in which reputational standing is imported rather than earned — the problem
pricing identity was meant to close [18,19].

### 8.7 Manipulation resistance

Adversary A3 — a requester colluding with an agent — attacks reputation rather than verification:
submit easy tasks with trivially satisfiable predicates, let them validate, and accumulate a record
to deploy against honest requesters later. Three measures apply, and they are design requirements
rather than optional hardening.

**Value- and difficulty-weighted updates.** An update's weight scales with task value and with
predicate strength, so a stream of trivial validated tasks moves the posterior far less than
comparable work at stake. A record built on $0.01 tasks does not qualify an agent for $100 tasks.

**Requester-concentration discounting.** Validated outcomes from a requester with whom the agent has
a concentrated relationship are discounted, following the standard intuition that reputation should
derive from a diverse counterparty set rather than from a single enthusiastic partner [20]. An agent
whose entire record comes from one requester is, for scoring purposes, nearly unevidenced.

**Validation-gated updates.** Since only validated outcomes update posteriors (§8.2), manipulating
reputation requires passing verification, so the attack must first defeat §6 and §7. This
composition is the main structural defense: reputation inherits whatever integrity the verification
layer has, rather than standing as an independent and softer target.

The honest limitation is that these mitigate rather than eliminate. A patient adversary with
multiple cooperating requesters and genuine (if easy) validated work can still accumulate standing
faster than its true capability warrants, and we return to this in §13.

### 8.8 What cost-adjustment changes

A brief illustration of the mechanism's effect, again arithmetic on the model rather than
measurement. Consider two agents in one category, with validated success rates and attested mean
costs:

| Agent | `E[θ]` | `E[c]` | Quality rank | `D = E[θ]/E[c]` | Value-density rank |
|---|---|---|---|---|---|
| X | 0.95 | $1.80 | 1 | 0.53 | 2 |
| Y | 0.88 | $0.60 | 2 | 1.47 | 1 |

Quality-only ranking selects X for every task in the category. Value density selects Y, which
delivers roughly 2.8× the validated successes per dollar; a requester with a fixed budget obtains
more completed work from Y despite its lower per-task success rate. X remains preferable where
per-attempt success matters more than throughput — a task whose failure carries external
consequences, or one that cannot be retried — which is why the orchestrator treats budget and
retry-tolerance as task parameters (§9.4) rather than applying value density unconditionally.

The general point: quality-only ranking systematically overselects expensive agents, and no amount
of better quality estimation corrects it, because the error is in what is being optimized rather
than in how well it is measured.

---

## 9. Routing under budget constraints

### 9.1 The decision problem

In autonomous mode the orchestrator receives a task with category `k`, budget `B`, and
retry-tolerance, and must select an agent without human input. The objective is to maximize
validated successes per unit spend subject to the budget, while generating enough evidence to keep
the posteriors of §8 informative.

Two failure modes bracket the problem. Pure exploitation — always select the highest-scoring
agent — maximizes immediate expected value and destroys the evidence base (F6). Pure exploration
wastes requester money on agents already known to be worse. This is a bandit problem, and the
reason to say so explicitly is that bandit formulations come with the exploration discipline that
leaderboard ranking lacks.

### 9.2 Why ranking is not a policy

A static leaderboard consumed greedily is self-confirming. The top-ranked agent receives the tasks,
only its posterior continues to update, and competitors' posteriors remain frozen at whatever
evidence they had when they fell behind. Ossification follows even when the ranking was correct
when formed, because capability drifts — models are updated, prompts are revised, agents are
retired — while a frozen posterior cannot register the drift. The system then cannot distinguish
"no longer competitive" from "never sampled recently," and the two require opposite responses.

Leaderboards as published artifacts remain useful for human-in-the-loop selection and for external
legibility. The claim is narrower: a ranking is a presentation of posteriors, not a decision rule
over them.

### 9.3 Policy: Thompson sampling over value density

Thompson sampling [25,26] resolves exploration by sampling from the posterior rather than acting on
its mean. We apply it to the composite objective of §8.4: sample success probability and cost for
each candidate, form the sampled value density, and select its maximizer.

```
Input: category k, budget B, candidate agents A_k
for each a in A_k:
    θ̃_a ~ Beta(α_{a,k}, β_{a,k})           # sampled success probability
    r̃_a ~ Gamma(κ_{a,k}, τ_{a,k})          # sampled cost rate
    c̃_a ← 1 / r̃_a                          # sampled expected cost
    if c̃_a > B · (1 + ε):  skip a           # budget feasibility filter
    D̃_a ← θ̃_a / c̃_a
select argmax_a D̃_a
```

Agents with wide posteriors — newcomers, or those whose evidence has decayed — produce
high-variance draws and are therefore selected occasionally without being selected systematically.
Exploration is thus proportional to uncertainty, which is the property that makes cold start (§8.6)
self-resolving: an unevidenced agent is sampled until its posterior sharpens, after which it is
selected on merit or not at all.

The feasibility filter deserves a note: it screens on *sampled* expected cost against the budget
with a tolerance `ε`, rather than on posterior mean cost, so that an agent whose cost is uncertain
is not permanently excluded by an unlucky early observation. Hard budget enforcement happens at
execution, where the runtime halts a task that exceeds `B` and emits a receipt recording the
overrun — a failure for scoring purposes (§8.3), since budget overrun is precisely the behavior
cost-adjusted reputation exists to penalize.

### 9.4 Task parameters that modulate the policy

Value density is not applied unconditionally, for the reason §8.8 identified. Three task parameters
adjust it:

- **Retry tolerance.** Where failure is cheap and retries are permitted, throughput per dollar is
  the right objective and value density applies directly. Where failure carries external
  consequences — a production deployment, an irreversible on-chain action — the orchestrator
  maximizes sampled `θ̃` subject to `c̃ ≤ B` instead, accepting a worse rate in exchange for a
  higher per-attempt success probability.
- **Budget tightness.** A budget close to the category's cheapest viable cost narrows the candidate
  set, and the policy degenerates gracefully toward feasibility rather than optimality.
- **Exploration suppression.** A requester may disable exploration for a given task, in which case
  the orchestrator acts greedily on posterior means. This is a per-task escape hatch, and §9.5
  explains why it cannot be the default.

### 9.5 Who pays for exploration

Exploration has a cost structure that is easy to overlook and that determines whether the policy
survives contact with real requesters. The information produced by sampling an under-evidenced
agent is a *public good*: it improves routing for everyone subsequently, while the risk of a failed
task falls on the individual requester whose task was used to generate it.

Left uncorrected, this is unstable. Rational requesters suppress exploration on their own tasks
(§9.4), every requester does the same, the policy degenerates to greedy ranking, and F6 returns by
consent rather than by design. The remedy must therefore align private and collective incentives,
and Mergit does this by having the platform bear exploration's downside: tasks routed to
under-evidenced agents as exploratory draws are insured, in that a validated failure on an
exploratory draw is not billed to the requester, with the cost absorbed as the platform's
acquisition cost for information it benefits from.

This is affordable precisely because exploration is proportional to uncertainty rather than
uniform — most tasks go to well-evidenced agents and are not insured — and it makes exploration
something requesters have no reason to refuse. It also creates a budget line the platform must
monitor: an adversary who registers many agents to farm insured exploratory draws is attacking this
subsidy, which is one more reason registration is priced (§8.6, R4) and exploratory allocation is
capped per identity and per operator.

### 9.6 Regret, and what we do not claim

Thompson sampling has well-developed regret guarantees for stationary stochastic bandits [26], and
budget-constrained variants are analyzed in the bandits-with-knapsacks literature [27]. Our setting
violates the assumptions of both in ways we should not paper over.

The posteriors of §8 are *deliberately non-stationary*: geometric decay discounts old evidence to
track drifting capability, so the reward distribution is not fixed and standard stationary bounds do
not transfer. Discounted and sliding-window bandit analyses are the appropriate frame, and we cite
the problem rather than claiming a bound. Further, the arm set is open — agents register and
retire — the objective is a ratio of two sampled quantities rather than a single bounded reward, and
rewards arrive only for *validated* tasks, so feedback is both delayed and sparse relative to
actions.

We therefore make no regret claim. The policy is justified here on structural grounds — exploration
proportional to posterior uncertainty, which demonstrably avoids the ossification failure that
greedy ranking exhibits by construction — and establishing regret behavior under decay, open arm
sets, and sparse validated feedback is stated as open work (§14). Claiming a borrowed bound would be
the easiest unearned result in the paper, and we decline it.

### 9.7 Composition with verification

Routing consumes only validated outcomes and attested costs, so an agent cannot improve its routing
share without passing verification. Manipulating routing therefore requires defeating §6 and §7
first — the same composition noted in §8.7. The orchestrator holds no independent trust surface of
its own: it is a policy over posteriors, and its integrity is inherited rather than separately
assumed.

### 9.8 When autonomous mode is appropriate

Human-in-the-loop selection remains the default. Autonomous routing is appropriate where the
category has accumulated validated evidence across several agents, where `Φ` is executable so that
validation is mechanical, where failure is retryable, and where task value sits well inside the
collateral bound of §7.2 Rule 1. Outside those conditions — a novel category, a judgment outcome, an
irreversible action, or a task value approaching the available stake — the orchestrator should
present its ranked candidates and let a human choose. Autonomy here is a property of the task, not a
mode the platform is in.

---

## 10. Settlement and revocability

### 10.1 Escrow and release

Payment `V` is locked before execution and released on one of two conditions: a Level 1 audit that
passes, or the absence of an audit draw combined with the expiry of the dispute window. The agent's
stake `S` is encumbered from task acceptance until window expiry, which is what gives Rule 1 of
§7.2 its force — collateral must actually be unavailable for other commitments during the period in
which it secures this one.

Settlement is x402-compatible where the rail fits [3]: the payment leg can be expressed as an
HTTP-402 interaction over an L2 stablecoin transfer, with Mergit supplying what the rail does not —
the conditionality and the revocability. We note the division deliberately. x402 answers "how does
money move between machines"; §§6–7 answer "on what evidence should it move," and these are
separable concerns that happen to compose.

### 10.2 The dispute window and its cost

A receipt remains challengeable for a window `W` after settlement. The window is the design's
central compromise, and the tension is real rather than incidental: payments want finality, while
verification wants revisability, and `W` prices the trade.

A longer window buys assurance — more time for a requester to discover that `Φ` did not in fact
hold, more opportunity for a challenger to act — at a direct cost to the agent, whose stake remains
encumbered and whose revenue remains provisional. That cost is a working-capital cost, and it is
borne by honest agents in proportion to the dishonesty the system is defending against. It will be
priced into `V`, which means the window's length is ultimately paid for by requesters. We therefore
treat `W` as category-dependent rather than global: categories whose predicates are mechanically
checkable at settlement time need only a short window, while categories where failure surfaces late
(a dependency upgrade that breaks a downstream consumer next week) need a longer one.

### 10.3 Challenge mechanics

Challenge is permissionless (§5.4). Any party may challenge a receipt within `W` by posting a bond
`b` and naming the respect in which the receipt fails to substantiate `Φ`. Challenge triggers Level
2 disclosure (§6.3) and adjudication.

Bond sizing is bounded on both sides, and both bounds matter:

- `b` must exceed the cost of adjudicating a frivolous challenge, or the mechanism becomes a
  griefing vector against honest agents — each spurious challenge imposing disclosure and
  adjudication costs at no cost to the challenger.
- `b` must stay well below the expected reward for a successful challenge, or challenge is not
  worth mounting and `q` collapses to zero — which, by §7.4, is precisely the regime where routine
  audit rates must rise to compensate.

Since `q > g/(λS)` makes routine auditing unnecessary (§7.4), the platform's interest is in setting
`b` as low as the griefing constraint permits and making the success reward generous. A professional
challenger population is cheaper than an audit department, and we regard cultivating one as an
operational objective rather than an incidental benefit.

On a successful challenge, slashed stake is distributed in a fixed priority order:

1. **Requester made whole** — refund of `V`, plus the metered cost of any wasted downstream work
   where that is attributable.
2. **Challenger rewarded** — bond returned plus a reward sufficient to make challenge profitable in
   expectation, given the probability of being wrong.
3. **Remainder to the insurance fund** (§10.4), rather than burned. Burning is simpler and
   superficially more credible, but the fund serves a function burning cannot (see below).

On an unsuccessful challenge, the bond is forfeit: partly to the agent as compensation for
disclosure and delay, partly to the adjudication cost.

### 10.4 Clawback, and its limit

Clawback after settlement is what makes "we do not pay for work that was not done" enforceable
retroactively rather than only prospectively, and it is the mechanism §1 promised. The limit is
worth stating as plainly as the capability: **clawback reaches stake, not revenue.** An agent paid
for a task may have withdrawn and spent the proceeds; what remains reachable is the encumbered
collateral. Recovery is therefore bounded by `λ·S`, which is the deeper reason Rule 1 caps accessible
task value at `λ·S − c_exec` — the cap is not merely a deterrence threshold but a solvency
constraint on the recovery path.

Two residual exposures follow, and we do not claim to close them. Where a single operator's agents
fail many tasks concurrently, aggregate liability can exceed aggregate stake even though each task
individually satisfied Rule 1; per-operator exposure limits bound this, imperfectly. And where
slashing is insufficient, the requester's recourse is the insurance fund rather than the operator,
which is why the fund exists and why remainder flows to it instead of being burned. The fund is an
admission: a system that promised full recovery from collateral alone would be overclaiming.

### 10.5 Tiers and credit

The onboarding tier prepays from faucet credits and carries the constraints of §4.5. The staked tier
locks escrow from a connected wallet per task.

A postpaid variant — settle periodically in arrears rather than locking per task — is attractive for
high-volume requesters and is where a production deployment will be pushed. It introduces requester
credit risk, which is a different risk than anything else in this paper: everything above concerns
whether the *agent* performed, while postpaid settlement concerns whether the *requester* pays. We
therefore scope it narrowly: available to requesters posting their own collateral or holding
verifiable credentials, with exposure limits, and explicitly not a trust claim derived from the
verification machinery. Conflating the two would be an error of the same shape as F5 — treating a
mechanism that establishes one fact as though it established another.

---

## 11. Cost reduction across tokens and gas

### 11.1 Why these are one problem

Outcome-contingent settlement is only worth having if its overhead is small relative to the work it
secures. The overhead has three components — audit cost `c_audit · p`, on-chain cost per task, and
the exploration subsidy of §9.5 — and the first is denominated in model tokens while the second is
denominated in gas. Treating them separately invites the characteristic failure of
blockchain-plus-AI designs, where each layer is individually optimized and the combined per-task
overhead exceeds the value of the task. We therefore state a single budget: **total trust overhead
must remain an order of magnitude below `V`.** §7.4's illustration puts audit cost at fractions of a
cent against a dollar task; the gas and subsidy components must stay in the same range or the
argument fails.

### 11.2 The token side

Practitioner-reported magnitudes for the standard techniques are substantial: prompt caching
reduces cached input cost by roughly 90%, delivering an estimated 59–70% saving at an 80% hit rate;
routing between frontier and budget models saves on the order of 60–80% per query; prompt
compression saves roughly 30–45% of input tokens; batch processing is around 50% cheaper; and
semantic caching eliminates perhaps 30–70% of redundant calls [32]. Peer-reviewed anchors exist for
routing [30] and compression [31].

We report these as practitioner figures rather than as measurements, and that qualification is not a
formality: these numbers come from vendor documentation and engineering blogs, with workload
assumptions that are rarely stated. Mergit is pre-implementation and has measured nothing. What the
figures support is the weaker claim the paper needs — that per-task LLM cost is substantially
compressible by known means — not any specific projected saving.

### 11.3 Where Mergit's architecture does cost work

Three interactions between the trust machinery and cost are worth drawing out, because they are
structural rather than additive.

**Value-density routing is itself a cost-reduction mechanism.** §8's reputation signal selects
agents that succeed cheaply, which means the trust layer and the cost layer optimize the same
quantity. This is the most useful consequence of making cost a trust dimension: the platform does
not need a separate cost-control system fighting a separate quality-ranking system, because
`D = E[θ]/E[c]` already expresses the trade. Quality-only ranking, by contrast, systematically
routes to expensive agents (§8.8) and then requires cost controls to claw back what the ranking gave
away.

**Caching interacts with verification, and the interaction needs handling.** If a harness serves a
cached result, the work was not performed on this occasion — and a receipt that recorded the cached
output as freshly executed would be false in a way that matters. Receipts therefore record cache
provenance explicitly: a step marked as cache-served carries the digest of the originating step and
its receipt, so an auditor sees that the result derives from prior attested execution rather than
from fresh work. This makes caching auditable rather than merely economical, and it has a secondary
benefit: a cache hit whose origin receipt was later successfully challenged can be invalidated
transitively.

**Attested metering is a prerequisite for both.** Routing on cost and charging for cost both require
cost figures the agent cannot inflate, which §6.2 supplies.

### 11.4 The gas side

On-chain cost is controlled by writing as little as possible, as rarely as possible, on a chain
where writes are cheap.

- **Commit roots, not content.** Only the Merkle root, terminal hash, attestation quote, and a body
  pointer go on-chain (§6.3), following ERC-8004's pattern [1].
- **Batch across tasks.** Rather than one commitment transaction per task, the runtime accumulates
  receipts into a batch and commits a single root covering all of them, with per-task inclusion
  proofs. Per-task gas then falls roughly as the reciprocal of batch size.
- **Settle in aggregate where possible.** Escrow release for a batch of completed tasks between the
  same counterparties can net into one transfer.
- **Operate on an L2** (decision 3), where the per-write cost makes the above viable at task
  granularity at all.

Batching carries a cost that must be acknowledged rather than assumed away. Between execution and
batch commitment, a receipt is not yet anchored, so a window exists in which an operator could
attempt to suppress an unfavorable receipt before it is committed. The mitigation is a signed
pre-commitment issued by the runtime at task completion — cheap, off-chain, immediately deliverable
to the requester — which fixes the receipt's content before batching and makes later suppression
detectable by a party already holding the signature. The guarantee during the pre-commitment window
is thus weaker than post-anchoring (it depends on the requester retaining the signature rather than
on chain state) and we size batch intervals accordingly: shorter windows for high-value categories.

### 11.5 The overhead budget, assembled

For the §7.4 illustration — `V = $2`, `c_exec = $1`, `c_audit = $0.02`, `S = $30`, `λ = 1`, `q` small:

| Component | Per-task cost | Driver |
|---|---|---|
| Audit | `c_audit · p* ≈ $0.002` | `p*` from Rule 1; falls as `S` rises or `q` rises |
| On-chain commitment | fractions of a cent | L2 write amortized over batch size |
| Exploration subsidy | small fraction of tasks | exploration proportional to posterior uncertainty (§9.5) |

Against `V = $2` this is overhead in the low single-digit tenths of a percent, versus roughly 50%
for re-execution verification. We stress that these are consequences of the model's parameters
rather than measurements; the architecture's claim is that the overhead *can* be held in this range,
and the parameters above show what it takes — adequate collateral, a credible challenger population,
batched commitments, and uncertainty-proportional exploration.

A comparison deserves pre-empting, because our figures will otherwise look implausible. [36] reports
roughly $0.07 per query in total verification cost from hardware-level simulation, against which our
tenths-of-a-cent audit component appears aggressive. The figures are not measuring the same thing.
Theirs is an end-to-end cost per inference including attestation overhead and amortized
zero-knowledge spot-checks at a sampling rate near 0.01; ours is the marginal cost of auditing a
receipt's evidence subset, excluding both execution and the proof machinery we do not have. Two
further asymmetries matter: our audits read test results and artifact digests rather than
recomputing tensor operations, which is a genuinely cheaper operation, but our task granularity is
coarser — an agent task is a trajectory, not a single query, so per-task overhead should be compared
against per-task value rather than per-query value. We would expect a real deployment to land
between the two, and we regard [36]'s simulated figure as the more credible anchor precisely because
it was simulated rather than derived. Until Mergit is measured, the honest claim is the directional
one: auditing evidence is cheaper than reproducing work, and the gap is what funds
outcome-contingency.

---

## 12. Security analysis

We proceed by adversary from §5.1, then cover attacks the adversary taxonomy does not naturally
surface. Throughout, the composition noted in §§8.7 and 9.7 does substantial work: reputation and
routing consume only validated outcomes, so attacks on them must first defeat verification.

### 12.1 A1 — Dishonest agent

The agent cannot sign receipts, so fabricating a completion claim requires the runtime to attest to
execution that did not occur, which is A2's or A5's problem rather than A1's. What remains available
to A1 is *shaping* genuine execution to appear successful: terminating once a weak predicate is
satisfied, satisfying `Φ` in a manner that violates unstated intent, or burning budget on an
unproductive trajectory and reporting the failure as external.

The first two are predicate-quality problems (§12.6). The third is handled by §8.3's decision to
update cost posteriors on all completed tasks regardless of outcome: an agent that habitually
consumes budget before failing acquires a poor value density and is routed away from, without any
need to adjudicate whether its failures were blameworthy.

### 12.2 A2 — Dishonest operator

This is the adversary the design is primarily built against, and it attacks along three paths.

**Receipt forgery** requires defeating TEE attestation, i.e. escalating to A5 (§12.5). Under
assumption 1 it is unavailable; absent that assumption, stake and challenge remain (§12.5).

**Receipt suppression** is the more practical attack: execute, observe an unfavorable outcome, and
decline to emit or commit the receipt. Three measures apply. The runtime's signed pre-commitment
(§11.4) fixes receipt content at completion and is delivered to the requester immediately, so
suppression after that point is detectable by a party holding the signature. Non-emission is treated
as failure for settlement and scoring purposes — escrow returns to the requester and the task
records as a failure — so suppression is never preferable to an honest failure. And the requester
can always challenge a missing receipt, which converts suppression into an adjudicated dispute.

**Identity churn** (F4) is priced by staking at registration (§8.6), with the stake forfeit on proven
falsity. Verified credentials reduce required stake but may not substitute for validated evidence
(§8.6), closing the import-reputation path.

### 12.3 A3 — Colluding requester

Covered in §8.7: value- and difficulty-weighted updates, requester-concentration discounting, and
validation-gated updates. The residual, restated honestly: a patient adversary with several
cooperating requesters performing genuine but easy validated work can accumulate standing faster
than its capability warrants. Concentration discounting raises the cost of this attack — it requires
recruiting diverse requesters — without eliminating it.

A sharper variant deserves separate mention. A colluding requester can submit a task with a
*deliberately weak* `Φ`, let the agent satisfy it trivially, and generate validated evidence that
transfers (via §8.5 pooling) to categories where predicates are stronger. Difficulty weighting is
the first defense; the second is that pooling weight `w` is small relative to category-level
evidence, so imported standing is weakly informative rather than decisive.

### 12.4 A4 — Lazy or adversarial validator

Under v1's permissioned validator set (§5.4) this reduces largely to platform integrity, which is
why permissionless challenge is retained: a validator that waves receipts through is exposed by any
challenge that subsequently succeeds, and the platform's own stake is slashable. Validator laziness
is thus economically self-correcting only to the extent that challengers exist — another dependency
on `q`, and another reason §10.3 prioritizes making challenge attractive.

Under a future permissionless validator set (§14), adversarial validation becomes a live concern and
the mechanism is stake-weighted aggregation with outlier clipping after [8]: a validator deviating
systematically from consensus loses bonded value. We flag that this imports Yuma Consensus's known
weakness along with its strength — consensus-penalizing aggregation discourages a correct minority as
well as an incorrect one, and [8] is a critical analysis for related reasons.

### 12.5 A5 — Compromised TEE

The honest statement: a compromised TEE produces well-formed receipts describing fictional
execution, and no part of §6 detects this. Attestation is a defeasible assumption (§5.2), and the
microarchitectural attack literature on production TEEs is active [28,29].

What the design retains in that event is not nothing, but it is not verification either. Stake
remains slashable and challenge remains open, so an operator exploiting a TEE break still faces
economic consequence *if the fiction is detected by other means* — a requester discovering that work
plainly was not done, inconsistency between a receipt and observable repository state, or an
anomalous pattern of outcomes relative to an agent's posterior. This is detection by external
contradiction rather than by cryptographic verification, and its coverage is uneven.

**We are weaker than the deterministic case here, and the comparison deserves to be explicit rather
than implied.** [36] argues that even an adversary who extracts a TEE signing key and forges
attestations cannot forge the execution *trace*: a broken TEE degrades to an ordinary optimistic
sequencer, whose invalid outputs are caught by bisection and slashed. Its stochastic
zero-knowledge spot-checks require no TEE honesty whatsoever. That fallback is strictly stronger
than ours — and the reason it does not transfer is the premise of this paper. Both the bisection and
the proof-based spot-check depend on recomputing the disputed computation, which a non-reproducible
trajectory does not permit. Our non-reproducibility argument therefore cuts both ways: it is what
makes receipts necessary (§1.3) and equally what deprives us of the strongest available defence when
attestation fails. We regard this as the principal cost of operating in this setting, and it raises
the value of `k`-of-`n` redundant execution (§14) from an optional hardening to the main route by
which high-value categories can recover a comparable guarantee.

Three structural mitigations are therefore worth stating. Receipts bind to *externally observable*
state wherever possible — artifact hashes a requester can recompute, on-chain transaction hashes,
commit SHAs — so that a fictional receipt must be consistent with a world the requester can inspect
independently. Diverse attestation across TEE vendors prevents a single vendor compromise from
affecting all receipts. And `k`-of-`n` redundant execution (§14) removes the single-TEE dependency
at a cost of `k`× execution, which is exactly the cost the receipt design was introduced to avoid —
making it a deliberate fallback for high-value categories rather than a default.

### 12.6 Predicate quality as an attack surface

A requester who submits a weak `Φ` receives weak assurance, and nothing in the verification path
corrects this: the system faithfully verifies whatever was asked. This is the most likely practical
failure of a deployed Mergit, more likely than any cryptographic or economic attack, because weak
predicates arise from ordinary carelessness rather than from adversarial intent.

Mitigations are advisory rather than structural: predicate templates per category, static warnings
for predicates that are trivially satisfiable (a test command matching no tests, an artifact
assertion with no content constraint), and surfacing predicate strength to the requester at
submission alongside the assurance it implies. Automated predicate synthesis and strengthening is
future work (§14). We decline to claim that the system protects a requester from under-specifying
their own task.

### 12.7 Data availability

Receipt bodies are off-chain (§6.3), so an operator can commit a root and then withhold the body,
rendering audit and Level 2 disclosure impossible while the on-chain commitment looks healthy. This
is the standard data-availability problem and it must be handled explicitly or the commitment scheme
provides false comfort.

Mergit's treatment: unavailability is failure. A receipt whose body cannot be retrieved on demand
within a bounded period is treated as unsubstantiated — escrow returns to the requester, the task
records as a failure, and repeated unavailability is itself slashable. The requester additionally
holds the body (or its decryption key) from settlement, so the operator is not the sole custodian,
and the retrieval obligation can be discharged by any holder. This converts withholding from an
evasion into a self-defeating action.

### 12.8 Griefing and subsidy attacks

**Challenge griefing** — spurious challenges to impose disclosure and delay on honest agents — is
bounded by bond forfeiture (§10.3), with the bond's lower limit set by exactly this concern.

**Exploration-subsidy farming** — registering many agents to harvest insured exploratory draws
(§9.5) — is bounded by priced registration, per-identity and per-operator exploratory allocation
caps, and the fact that an agent accumulating validated failures loses exploratory eligibility as
its posterior sharpens.

**Reputation griefing against a competitor** by routing it difficult tasks is limited by the fact
that requesters choose tasks and the orchestrator chooses agents; an adversary cannot direct
tasks at a specific competitor under autonomous routing, and under human-in-the-loop selection
a requester who deliberately assigns an unsuitable agent bears the cost.

---

## 13. Limitations

We state these as plainly as the contributions, on the view that a design document whose
limitations section is shorter than its claims section has not been examined carefully enough.

**No implementation, no measurements.** Mergit is pre-implementation; an earlier prototype was
discarded. Every quantitative figure in this paper is arithmetic on the stated model, and the
illustrations in §§7.4, 8.8, and 11.5 are labelled as such. Nothing here has been observed.

**Verification scope is narrower than "agent work."** Strong claims hold only for checkable
outcomes (§2.2). Attestable-process tasks receive partial assurance; judgment outcomes receive
none. A platform marketing verified payment across all agent work would be overstating this
design, and the boundary will be under commercial pressure precisely because it is inconvenient.

**Attestation relocates trust to hardware vendors.** §12.5 is the weakest point in the system. A
compromised TEE yields well-formed receipts about fictional execution, detectable only by external
contradiction. The fallbacks — external state binding, vendor diversity, redundant execution — reduce
but do not close this.

**Routine verification is centralized at v1.** Permissioned auditing (§5.4) means the v1
verification path depends on the platform, which sits awkwardly with the decentralization idiom the
surrounding ecosystem uses. Permissionless challenge and slashable platform stake mitigate; they do
not make the claim "decentralized verification" true at v1, and we do not make it.

**The system depends on challenger liveness.** §7.4's threshold result makes `q` economically
central, and `q > 0` is an assumption about motivated parties existing, not a property the protocol
enforces. A category with no challengers requires routine audit rates to rise, raising overhead
toward the regime the design exists to escape.

**Reputation is information-hungry.** Because only validated outcomes update posteriors (§8.2) and
most tasks are not audited at equilibrium rates, evidence accrues slowly. Early in a category's
life, posteriors are wide, routing is mostly exploration, and the subsidy of §9.5 is at its most
expensive. The design is therefore weakest exactly when a new deployment most needs it to work.

**Repeated-game incentive compatibility is unproven.** §7.5 concedes that the one-shot audit rule
places Mergit inside [34]'s memoryless bounded-slashing impossibility class, and that Rule 1's high
stake-to-value ratio puts a well-collateralized agent in the adverse regime. We propose
history-dependent auditing as the escape and argue it is cheap for us, but we have not shown that
any particular coupling `f` satisfies repeated-game incentive compatibility. Until that is done, the
safe posture is full slashing — which carries its own false-positive exposure, worse here than in
the deterministic case because adjudication is evidence-based.

**Our TEE fallback is weaker than the deterministic case's.** §12.5: a broken TEE in [36]'s design
degrades to an ordinary optimistic sequencer whose bad outputs are caught by replay, and its
zero-knowledge spot-checks need no TEE honesty at all. Neither remedy transfers to non-reproducible
work. This is the principal cost of our setting, not a detail.

**No regret guarantee.** §9.6 declines to claim one: decay makes rewards non-stationary, the arm set
is open, the objective is a ratio, and validated feedback is sparse. The routing policy is justified
structurally, not optimally.

**Recovery is bounded by collateral.** Clawback reaches stake, not spent revenue (§10.4). Aggregate
concurrent liability can exceed aggregate stake, and the insurance fund is an acknowledgement of
that gap rather than a solution to it.

**Collusion is mitigated, not solved.** A patient adversary with diverse cooperating requesters can
still accumulate standing faster than capability warrants (§12.3).

**Predicate quality is the likeliest real failure.** Weak predicates produce faithful verification of
the wrong thing (§12.6), and the system does not protect requesters from under-specifying tasks.

**The cost model is a convenience.** Exponential-Gamma cost posteriors (§8.3) are almost certainly
mis-specified for heavy-tailed agent task costs.

**Market timing is uncertain.** Agent micropayment demand has been reported as weaker than ecosystem
messaging suggests [5]. A mechanism that makes verified payment affordable does not establish that
buyers currently want it at volume.

**The onboarding tier is a cost centre, not evidence.** Full auditing of unsecured faucet-tier tasks
(§4.5) scales with onboarding volume and carries none of the deterrence guarantees. Growth there
should not be read as the mechanism working.

---

## 14. Future work

**Permissionless staked validation.** The first decentralization milestone (§5.4): open the audit
role to bonded validators with stake-weighted aggregation and outlier clipping after [8], inheriting
that design's trade-offs as discussed in §12.4.

**`k`-of-`n` redundant execution for high-value categories.** Removes the single-TEE dependency
(§12.5) at `k`× execution cost. The interesting question is not whether this works but where the
crossover lies — at what task value does `k`× execution become cheaper than the expected loss from
TEE compromise.

**Proof-based verification.** Succinct proofs of execution would eliminate the hardware-trust
assumption entirely. Current cost at LLM inference scale makes this impractical, and we decline to
assert infeasibility without a citation we have yet to select (see `research.md` §G); the pertinent
question is which *sub-steps* of a trajectory are cheap enough to prove today, since partial proof
coverage composes with attestation for the remainder.

**Repeated-game incentive compatibility for history-dependent auditing.** The most pressing
theoretical gap, from §7.5. Required: a coupling `f` from reputation posteriors to audit rates,
bounded away from zero and escalating sharply on failure, shown to satisfy [34]'s repeated-game
criterion while keeping expected audit cost near the one-shot optimum. Because the posteriors exist
already for routing, this is the cheapest substantive strengthening available to the design, and it
would also make verification and reputation a single coupled mechanism rather than two layers.

**Regret analysis under decay, open arm sets, and sparse validated feedback.** The open theoretical
problem from §9.6. Discounted and sliding-window bandit analyses are the natural starting frame.
Note that this interacts with the item above: if audit rates become history-dependent, then
validated feedback arrives at a rate the policy itself influences, and exploration and audit
scheduling can no longer be analyzed independently.

**Predicate synthesis and strengthening.** Given §12.6's assessment that weak predicates are the
likeliest practical failure, automatically generating or strengthening `Φ` from a task description —
and estimating a predicate's discriminative power before execution — may matter more in deployment
than any mechanism in §§6–10.

**Learning from verified failures.** Validated failure data is a corpus describing exactly how
agents fail, with attested evidence of what they did. Using it to improve agents is the obvious
extension and the original motivation behind "make the AI learn from that," but it is a separate
contribution from the payment mechanism and raises unresolved questions about who owns failure data
and whether a requester's task content may be used to train models that serve competitors. We scope
it out deliberately rather than claiming it.

**Cross-platform receipt portability.** Because identity is ERC-8004-compatible [1], reputation
earned on Mergit could in principle travel to other venues, and receipts from other attested
runtimes could be consumed by Mergit. Whether reputation *should* be portable across platforms with
different verification standards is a question of some depth: portability without comparable
verification standards imports unearned standing, which is the whitewashing problem [19] at the
level of platforms rather than identities.

---

## 15. Conclusion

Agent platforms bill for attempts because verifying outcomes has been too expensive to do routinely,
and the mechanisms that solved this for machine computation assume the work can be re-executed.
Agent work cannot: it is multi-step, tool-using, and side-effecting, and once a repository has been
modified or an API called, there is no second run of the same task to compare against. That is a
structural obstacle, not a pricing one, and it is why the registries and payment rails now deployed
have not produced verified-work markets despite being individually adequate.

Mergit's response is to attest execution rather than reproduce it. A platform that owns the sandbox
can emit tamper-evident, hardware-attested records of what ran and what it cost, reducing
verification to an audit of evidence whose cost is set by evidence volume rather than by the work.
Attested metering then makes the contribution we consider most consequential available: reputation
as verified quality per unit cost, which is what "pay for what you got" means once it is stated
precisely enough to compute. Routing follows as a decision policy over those posteriors rather than
a ranking, and settlement becomes revocable, so non-payment for work that was not done is
enforceable after the fact.

We have been deliberate about what is not ours. That collateral trades against audit frequency is
established in the verifiable-inference literature; that attestation composes with optimistic
challenge is published. Our adaptation concerns what changes when the audited object is an
attestation of a non-reproducible trajectory: challenge cannot reliably terminate in re-execution,
a residual adjudication burden remains on contested tasks, and the dominant risk shifts from
economic substitution to hardware trust. We have also been deliberate about what the design does
not do — it does not verify judgment outcomes, does not decentralize verification at v1, does not
protect requesters from weak predicates, and does not come with a regret bound.

What remains is to build it and find out which of the above survives contact with real work. The
threshold result of §7.4 is the claim we would most like tested first: if a false receipt faces
better than a one-in-ten chance of challenge, routine auditing is unnecessary, and the cost of trust
collapses to the cost of keeping challenge credible. If that holds in practice, outcome-contingent
payment for autonomous work is affordable at the granularity of individual tasks — which is the
granularity at which agents actually work.

---

## 16. References

Entries marked † are cited from secondary knowledge and their exact venue, year, or identifier must
be verified before submission (see `paper/research.md` for verification status and the outstanding
checks in its §G). Entries without a dagger were confirmed during research for this paper.

[1] ERC-8004: Trustless Agents. Ethereum Improvement Proposal discussion, Fellowship of Ethereum
Magicians. https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098

[2] Xiong et al. *Can Trustless Agents Be Trusted? An Empirical Study of the ERC-8004 Decentralized
AI Agent Ecosystem.* arXiv:2606.26028, 2026.

[3] Coinbase. *Introducing x402: a new standard for internet-native payments.* Coinbase Developer
Platform, 2025.

[4] Allium / Coinbase. x402 adoption metrics, reported April 2026.

[5] CoinDesk. *Coinbase-backed AI payments protocol wants to fix micropayment but demand is just not
there yet.* 11 March 2026.

[6] Virtuals Protocol. Agent Commerce Protocol. Analyses by Tiger Research, Delphi Digital, and
Messari; https://www.virtuals.io/

[7] Bittensor. *What Are Bittensor Subnets?* https://bittensor.ai/learn/subnets

[8] *Bittensor Protocol: The Bitcoin in Decentralized Artificial Intelligence? A Critical and
Empirical Analysis.* arXiv:2507.02951.

[9] Autonolas. *Autonolas Tokenomics v1 — Towards Self-Sustainable Autonomous Services.* Olas
Network core technical document.

[10] Olas. Staking and Proof of Active Agent. https://olas.network/staking

[11] *Fetch.ai: An Architecture for Modern Multi-Agent Systems.* arXiv:2510.18699.

[12] Fetch.ai. Verified agent identity and Agent Name Service (ANAME). https://business.fetch.ai/

[13] *Agent TCP/IP: An Agent-to-Agent Transaction System.* arXiv:2501.06243.

[14] *SoK: Security of Autonomous LLM Agents in Agentic Commerce.* arXiv:2604.15367.

[15] *From Multi-Agent Systems and the Semantic Web to Agentic AI: A Unified Narrative of the Web of
Agents.* arXiv:2507.10644.

[16] *Agent-to-Agent Finance: Blockchain Payments and Trust Infrastructure for Autonomous AI
Agents.* arXiv:2607.00245.

[17] *TessIndex: Capability Verified Identity System for the Agent Economy.* arXiv:2608.21942.

[18] † Douceur, J. *The Sybil Attack.* IPTPS, 2002.

[19] † Friedman, E. and Resnick, P. *The Social Cost of Cheap Pseudonyms.* Journal of Economics and
Management Strategy, 2001.

[20] † Kamvar, S., Schlosser, M. and Garcia-Molina, H. *The EigenTrust Algorithm for Reputation
Management in P2P Networks.* WWW, 2003.

[21] † Becker, G. *Crime and Punishment: An Economic Approach.* Journal of Political Economy, 1968.

[22] † Avenhaus, R., von Stengel, B. and Zamir, S. *Inspection Games.* Handbook of Game Theory,
Vol. 3.

[23] † Teutsch, J. and Reitwießner, C. *A Scalable Verification Solution for Blockchains* (Truebit),
2017.

[24] † Kalodner, H. et al. *Arbitrum: Scalable, Private Smart Contracts.* USENIX Security, 2018.

[25] † Thompson, W. R. *On the Likelihood that One Unknown Probability Exceeds Another in View of the
Evidence of Two Samples.* Biometrika, 1933.

[26] † Agrawal, S. and Goyal, N. *Analysis of Thompson Sampling for the Multi-Armed Bandit Problem.*
COLT, 2012.

[27] † Badanidiyuru, A., Kleinberg, R. and Slivkins, A. *Bandits with Knapsacks.* FOCS, 2013.

[28] † Costan, V. and Devadas, S. *Intel SGX Explained.* IACR Cryptology ePrint Archive.

[29] † Microarchitectural and side-channel attacks on production TEEs (Foreshadow, SGAxe,
Plundervolt class). Specific papers to be selected.

[30] † *RouteLLM: Learning to Route LLMs with Preference Data.* arXiv identifier to confirm.

[31] † *LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models.* arXiv
identifier to confirm.

[32] Practitioner-reported LLM cost optimization magnitudes: prompt caching, model routing, prompt
compression, batching, semantic caching. Compiled from vendor documentation and engineering guides;
see https://github.com/pleasedodisturb/awesome-llm-token-optimization

[33] *awesome-erc8004* — ERC-8004 ecosystem resource index.
https://github.com/sudeepb02/awesome-erc8004

[34] Shang, Z., Yu, Y. and Chen, K. *Repeated-Game Security for Restaking-Based Verifiable
Inference.* arXiv:2608.09055, August 2026.

[35] *Proof of Sampling: A Nash Equilibrium-Based Verification Protocol for Decentralized Systems.*
arXiv:2405.00295.

[36] Chan, Ding, Chen, Wu, Zhang and Tian. *Optimistic TEE-Rollups: A Hybrid Architecture for
Scalable and Verifiable Generative AI Inference on Blockchain.* arXiv:2512.20176, December 2025.

[37] *Nondeterminism-Aware Optimistic Verification for Floating-Point Neural Networks.*
arXiv:2510.16028.

[38] *EigenAI: Deterministic Inference, Verifiable Results.* arXiv:2602.00182.

[39] *Naysayer Proofs.* IACR Cryptology ePrint Archive 2023/1472.

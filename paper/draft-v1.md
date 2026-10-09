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
the design overview and trust boundaries. Sections 5–9 develop receipts, verification economics,
cost-adjusted reputation, and routing. Section 10 covers settlement and revocability, Section 11
the combined token-and-gas cost strategy, and Section 12 the security analysis. Sections 13 and 14
state limitations and future work.

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
TEE-rollups further combine trusted-execution attestation with optimistic challenge to reduce
verification cost [36].

**We build on this rather than compete with it, and state plainly what it means for our claims.**
That stake trades against audit frequency is established [34], not contributed here; that
attestation can be combined with optimistic challenge is published [36], not contributed here. Our
§7 is an adaptation of this analysis.

What every one of these assumes is re-executability. The audited object is a function evaluation
that a verifier can recompute and compare. The literature's own difficulties when that assumption
weakens are instructive: non-determinism defeats bit-exact comparison even for floating-point
neural network evaluation, requiring nondeterminism-aware protocols [37], and a parallel line of
work engineers determinism into inference specifically so that results can be verified [38]. Agent
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
| Verification economics | Restaking inference [34], Proof of Sampling [35], optimistic TEE [36], Truebit [23], rollups [24], naysayer [39] | Stake, probabilistic audit, slashing, challenge periods | **Assumes re-executability**; strains under even numerical non-determinism [37,38] |
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

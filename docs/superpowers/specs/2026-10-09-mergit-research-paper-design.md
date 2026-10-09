# Mergit Research Paper — Design Brief

**Date:** 2026-10-09
**Status:** Design brief, approved decisions locked. Precedes paper drafting.
**Deliverables:** (1) full paper in Markdown, LaTeX/arXiv-convertible; (2) concise whitepaper derived from a subset of it.

---

## 1. Intent

Mergit is an AI-agent execution platform — harness plus sandbox, comparable to existing agent
runtimes — with a Web3 trust and settlement layer native to the runtime rather than bolted on.
Agents hold on-chain identity, every executed task yields a verifiable record, payment is
contingent on verified outcome, reputation is earned from verified history, and in autonomous
orchestration mode task routing is driven by that reputation.

The paper's purpose is to state this vision publicly with enough rigor that technical readers
take it seriously: academic structure and citation discipline, whitepaper framing and
accessibility.

**Audience:** hybrid. Researchers and engineers who will scrutinize the mechanism, plus
prospective contributors, adopters, and grant/program reviewers deciding whether Mergit is worth
backing.

**Success criteria for the paper:** a reader finishes it able to state (a) what specific problem
blocks outcome-contingent agent payment today, (b) why Mergit's mechanism removes that block,
and (c) what is genuinely new versus existing protocols — without feeling oversold.

---

## 2. Locked decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Verification model | Validator network, ERC-8004-aligned — refined to *receipt audit* with sampled re-execution rather than default re-execution |
| 2 | Payment model | Hybrid: faucet credits for onboarding, connected wallet for production scale |
| 3 | Chain | Ethereum L2 (Base / Arbitrum / Optimism class), EVM-compatible |
| 4 | Cost scope | LLM tokens and on-chain gas treated as one combined cost problem |
| 5 | Audience / tone | Hybrid: academic rigor, whitepaper framing |
| 6 | Reputation scoring | Bayesian, decay-weighted, per task category |
| 7 | Sybil resistance | Staking as baseline; verified external credentials reduce required stake |
| 8 | Implementation status | Pre-implementation. Prior prototype discarded; rebuilding fresh. No benchmarks may be claimed. |
| 9 | Related work | Researched and positioned against explicitly |
| 10 | Format | Markdown first, structured for later LaTeX/arXiv conversion |
| 11 | Agent domain | General-purpose protocol; software-engineering agents as flagship first use case |
| 12 | Length | Full paper first; concise whitepaper extracted from its subset |
| 13 | Headline contribution | Cost-adjusted reputation — "pay for what you got" |
| 14 | Formalization level | Fully formal, including cost analysis |
| 15 | Runtime trust anchor | TEE attestation (SGX/TDX, SEV, Nitro class) |

---

## 3. Thesis

> Outcome-contingent payment is a solved problem for machine work that can be re-executed:
> restaking-based verifiable inference posts stake, audits probabilistically, and slashes on
> detected cheating. It does not transfer to agent work, for a structural rather than economic
> reason — an agent task is multi-step, tool-using, and side-effecting, so once a repository has
> been mutated, an API called, or money spent, the task cannot be re-executed even in principle.
> Verification by re-execution is therefore not merely expensive here, it is frequently undefined.
> Because Mergit owns the execution environment, it can attest execution instead of reproducing
> it: the runtime emits hardware-attested, tamper-evident execution receipts, and verification
> becomes an audit of evidence. Attested metering then makes the principal contribution available —
> reputation as verified quality per unit cost — turning "pay for what you got" into a measurable
> quantity rather than a slogan.

**Revision note (2026-10-09).** An earlier version of this brief claimed "stake substitutes for
verification compute" as the paper's central result. Research found this is prior art in the
verifiable-inference setting (arXiv 2608.09055), and TEE-plus-optimistic-challenge is likewise
published (arXiv 2512.20176). The thesis was reframed: non-reproducibility of agent work is now
the structural pillar, cost-adjusted reputation the headline contribution, and the deterrence
analysis is presented as an adaptation of prior art. See `paper/research.md` §F2.

Falsifiable content of the reframed claim: that agent-task verification can be grounded in attested
execution evidence without re-execution; that cost of trust is bounded by evidence volume rather
than task cost; and that cost-adjusted reputation changes routing outcomes relative to
quality-only ranking.

---

## 4. Contributions

Ordered as the paper presents them. C2 leads the abstract; C1 is the enabling mechanism.

**C2 (headline) — Cost-adjusted reputation.**
Because the harness meters both LLM tokens and gas per task, reputation is defined as *verified
quality per unit cost*, not quality alone. An agent succeeding at ten times the token spend is not
equivalent to one succeeding cheaply. Existing systems score quality (Bittensor) or counterparty
satisfaction (Virtuals ACP); none treat cost-efficiency as a first-class trust dimension. This is
the formal statement of "pay for what you got."

**C1 (structural pillar) — The non-reproducibility argument, and Verifiable Execution Receipts.**
Agent work cannot be verified by re-execution because it cannot be re-executed: tool calls have
effects outside the computation (mutated repositories, called APIs, spent money), state cannot be
restored, and even restored state yields a different trajectory. The inference literature already
strains against a weaker form of this (non-determinism defeating bit-exact comparison, arXiv
2510.16028; determinism engineered specifically to enable verification, arXiv 2602.00182); agent
execution is strictly harder. Attested execution evidence is therefore the remaining substrate.
The harness emits a structured, signed record per task — tool calls, commands, test results, diff
hashes, artifacts touched, tokens and gas consumed — Merkle-rooted on-chain with the body
off-chain, matching ERC-8004's pointer-and-commitment pattern. Only a platform owning the runtime
can do this: ERC-8004 is a registry without a runtime, x402 a payment rail without a runtime, ACP
a marketplace without a runtime.
*Explicitly not claimed as novel:* attestation combined with optimistic challenge (published,
arXiv 2512.20176). The novelty is the object being verified, not the pairing of mechanisms.

**C3 — Budget-constrained bandit routing.**
Autonomous agent selection is framed as a contextual bandit under cost constraints: maximize
expected verified success per unit cost, using Thompson sampling over the Bayesian reputation
posteriors. This replaces static leaderboard ranking with a decision policy, and resolves the
ossification failure mode where a top-ranked agent absorbs all tasks and better newcomers are
never sampled.

**C4 — Revocable settlement.**
x402 and ACP settle and conclude. Mergit adds a dispute window in which a receipt may be
challenged after settlement, with clawback against the agent's stake. This is the mechanism that
actually implements "if we later learn the work failed, we do not pay," and it makes the staking
requirement load-bearing in the payment path rather than decorative.

---

## 5. Formal core

### 5.1 Notation

| Symbol | Meaning |
|---|---|
| `V` | payment for a task |
| `S` | agent's posted stake |
| `λ ∈ (0,1]` | slashing fraction applied to `S` on a proven false receipt |
| `p ∈ [0,1]` | probability a submitted receipt is audited |
| `c_exec` | cost of executing (or re-executing) the task; dominated by LLM tokens |
| `c_audit` | cost of auditing a receipt without re-execution; `c_audit ≪ c_exec` |
| `g` | agent's gain from submitting a false receipt (payment plus work cost avoided) |
| `α_{a,k}, β_{a,k}` | Beta posterior parameters for agent `a` on task category `k` |
| `γ ∈ (0,1]` | time-decay factor applied to accumulated evidence |

### 5.2 Deterrence condition

Submitting a false receipt is irrational when expected penalty exceeds expected gain:

```
p · λ · S  >  g,     where g ≈ V + c_exec
```

giving a minimum honest-equilibrium audit rate

```
p*  ≈  (V + c_exec) / (λ · S)
```

This is an inspection game; the structure follows standard deterrence analysis (Becker;
Avenhaus–von Stengel–Zamir) and the sampled-challenge design of Truebit's verification game.

### 5.3 Cost of trust, and the substitution result

Expected verification cost per task:

```
C_trust(p)  =  c_audit  +  p · c_exec
```

Substituting the minimum sustainable audit rate:

```
C_trust(p*)  =  c_audit  +  ((V + c_exec) / (λ·S)) · c_exec
```

**Adaptation, not result (stake trades against audit frequency).** `C_trust` is decreasing in `S`:
as stake rises, the audit rate required for deterrence falls, and the cost of trust approaches
`c_audit` rather than scaling with `c_exec`. **This substitution is prior art** in the
verifiable-inference setting (arXiv 2608.09055, which quantifies it — baseline audit rate falling
0.370 → 0.145 at discount factor 0.95 — and notes that higher audit rates raise verification cost
linearly across honest queries). The paper presents the above as adaptation and cites it as
foundation.

What genuinely changes in our setting, and what §7 must establish:
- the audited object is an *attestation of a non-reproducible trajectory*, not a *substituted
  computation*;
- challenge cannot reliably terminate in re-execution, so disputes resolve against receipt evidence
  and attestation integrity, leaving a residual adjudication burden to characterize;
- `c_audit` is bounded by evidence volume rather than by task cost, which is what keeps the
  substitution useful when `c_exec` is unavailable as a comparison baseline.

**Contrast with prior designs.** Verification-by-re-execution operates at `p ≈ 1`, so
`C_trust ≈ c_exec` — the cost of checking equals the cost of the work. That is the economic reason
outcome-contingent agent payment has not been deployed at task granularity, and it is the
constraint Mergit removes.

Two consequences worth stating explicitly in the paper:
- Stake requirements and audit rates are *jointly* tunable; a platform may trade collateral
  against verification compute along the `p·λ·S` isoquant.
- Because verified credentials reduce required stake (decision 7), credentialed agents sit at a
  lower point on the same curve without weakening deterrence — the credential substitutes for
  collateral, which in turn substitutes for verification.

### 5.4 Reputation: Bayesian, decayed, cost-adjusted

Per agent `a` and task category `k`, verified outcomes update a Beta–Bernoulli posterior with
geometric decay applied before each update:

```
α ← γ·α + 1   on validated success
β ← γ·β + 1   on validated failure
```

Decay (`γ < 1`) bounds the influence of old evidence, so reputation tracks current capability and
a long-dormant high score does not persist unchallenged.

Cost-adjusted score for routing is the posterior expectation of success per unit expected cost:

```
score(a,k)  =  E[θ_{a,k}] / Ê[cost_{a,k}]     where  E[θ_{a,k}] = α / (α + β)
```

with `Ê[cost]` estimated from metered token and gas spend on that agent's prior tasks in category
`k`. New agents carry wide posteriors rather than zero scores, which is what makes cold-start
exploration principled instead of a special case.

### 5.5 Routing policy

Autonomous selection draws `θ̃_{a,k} ~ Beta(α_{a,k}, β_{a,k})` per candidate and selects the agent
maximizing `θ̃_{a,k} / Ê[cost_{a,k}]` subject to the task's budget. This is Thompson sampling
adapted to a cost-constrained objective; regret behavior is cited from the Thompson sampling and
Bandits-with-Knapsacks literature rather than newly proven here. The paper states this as an
adaptation of known results, not as new theory.

### 5.6 The faucet tier is a deterrence special case

The deterrence condition has an immediate consequence for the onboarding tier. If faucet credits
are issued free, effective stake is zero, `p* = (V + c_exec)/(λ·S)` diverges, and no audit rate
deters a false receipt. Free credits therefore provide no Sybil resistance and no receipt
integrity, and the paper must not present the faucet tier as if the same guarantees apply.

Mergit resolves this by treating the faucet tier as explicitly unsecured and constraining it:

- faucet-tier tasks are audited at `p = 1` (verification cost is absorbed by the platform as an
  onboarding subsidy, which is affordable precisely because the tier is rate-limited);
- faucet-tier agents are excluded from autonomous routing and from accruing reputation weight that
  transfers to the staked tier;
- task value is capped, bounding platform-absorbed risk.

Stated plainly: the faucet tier buys onboarding, not trust. Trust begins at stake. This keeps the
hybrid payment model consistent with the deterrence result rather than quietly contradicting it.

### 5.7 Runtime trust anchor

Receipts are trustworthy only if the sandbox emitting them is. Mergit's answer is TEE attestation:
the sandbox executes inside a trusted execution environment and receipts carry hardware
attestation binding the receipt to a measured runtime image.

The paper must acknowledge, not elide, that TEEs have a substantial side-channel and
micro-architectural attack literature, and that attestation shifts trust to hardware vendors. The
mitigation story is layered: TEE attestation establishes baseline integrity; staking plus
challengeable receipts means a compromised or colluding operator still faces slashing; k-of-n
redundant execution and succinct proofs are the decentralization path in future work. zkML remains
impractical at LLM inference scale and is cited as such.

---

## 6. Architecture

Six components, each independently describable and testable:

1. **Harness / sandbox (attested runtime).** Executes agent tasks in a TEE, meters tokens and gas,
   emits signed Verifiable Execution Receipts with a Merkle commitment.
2. **Identity registry.** ERC-8004-compatible agent identity; stake posted at registration;
   verified credentials (DID, domain, prior on-chain reputation) reduce required stake.
3. **Validation layer.** Samples receipts at rate `p` derived from `V`, `λ`, `S`; audits cheaply;
   escalates to re-execution on challenge; writes attestations on-chain.
4. **Reputation engine.** Maintains decayed Beta posteriors per (agent, category) plus metered cost
   estimates; exposes cost-adjusted scores.
5. **Settlement.** Escrowed payment released on validated completion; dispute window permits
   post-settlement challenge and clawback against stake. Faucet credits for the onboarding tier
   (unsecured, fully audited, rate-limited, value-capped per §5.6), connected wallet for
   production; x402-compatible where it fits.
6. **Orchestrator.** Human-in-the-loop by default; in autonomous mode routes tasks by
   budget-constrained Thompson sampling over reputation posteriors.

Boundary discipline: the harness is the only component that can assert what happened; the chain is
the only component that holds commitments and value; the reputation engine derives, and asserts
nothing of its own.

---

## 7. Related work positioning

| System | What it provides | What it lacks that Mergit supplies |
|---|---|---|
| **ERC-8004 Trustless Agents** | Identity, Reputation, Validation registries for agents | No runtime; validation presumes re-execution; empirically populated largely by placeholder registrations |
| **x402** (Coinbase/Cloudflare) | HTTP 402 stablecoin payment rail for agents; large transaction volume | Pays for *access*, not verified outcome; no verification, no revocability |
| **Virtuals Protocol ACP** | Request→negotiation→escrow→evaluation→settlement; reputation affects terms | Counterparty evaluation rather than attested execution; no runtime; no cost-adjusted trust |
| **Bittensor** | Validator-scored quality via Yuma Consensus; stake-weighted aggregation | Inflation-funded commodity production within subnets, not requester-funded verified task settlement |
| **Olas / Autonolas** | Proof of Active Agent staking tied to verifiable outcomes | Activity and KPI rewards, not per-task outcome-contingent payment with clawback |
| **Fetch.ai** | Agent identity credentials; ANAME domain-linked trust signals | Identity and discovery, not verification economics or conditional settlement |
| **Restaking-based verifiable inference** (arXiv 2608.09055) | Stake, probabilistic audit, slashing; quantified substitution between audit budget and mechanism parameters | Verifies a *re-executable* model call; no reputation system; no cost-adjusted trust; inapplicable where re-execution is undefined |
| **Optimistic TEE-rollups** (arXiv 2512.20176) | TEE attestation combined with optimistic challenge | Deterministic computation with re-execution as dispute terminator; not agent trajectories with external side effects |
| **Proof of Sampling** (arXiv 2405.00295) | Nash-equilibrium sampled-audit verification | Same re-executability assumption |
| **Nondeterminism-aware optimistic verification / EigenAI** (arXiv 2510.16028, 2602.00182) | Confronts non-reproducibility; engineers determinism to enable verification | Addresses numerical non-determinism in pure inference, not side-effecting multi-step execution |

Honest framing, post-research: the trust primitives exist and are largely non-operational [2,17];
the verification economics exist but assume re-executability [34,35,36]; nothing verifies
multi-step, side-effecting agent work. **That intersection is the gap, and it is narrower and more
defensible than "nobody has combined these."** The related-work section must cite [34] and [36]
prominently — a reviewer familiar with that literature who finds them buried will reject on prior
art regardless of the rest.

---

## 8. Paper outline

Sections marked **[W]** also constitute the concise whitepaper subset.

1. **Abstract** **[W]** — lead with cost-adjusted reputation and the substitution result.
2. **Introduction** **[W]** — the agent economy premise; why "pay for what you got" has not shipped.
3. **Problem statement** — verification cost scaling; whitewashing; opaque pricing; routing ossification.
4. **Related work** **[W]** — the table in §7, with citations.
5. **Design overview** **[W]** — six components, data flow, trust boundaries.
6. **Verifiable Execution Receipts** — structure, attestation, commitment scheme.
7. **Verification economics** — §5.2–5.3; the deterrence condition and substitution result.
8. **Cost-adjusted reputation** — §5.4; decay, cold start, Sybil interaction.
9. **Routing under budget constraints** — §5.5.
10. **Settlement and revocability** — escrow, dispute window, clawback, faucet/wallet tiers.
11. **Cost reduction** — combined LLM-token and gas strategy: caching, routing, compression, batching; batched/off-chain commitment to minimize gas.
12. **Security analysis** — Sybil/whitewashing, collusion, TEE compromise, challenger liveness, oracle and pricing manipulation.
13. **Limitations and open problems** — §9.
14. **Future work** — decentralized execution, learning from verified failures, proof-based verification.
15. **Conclusion** **[W]**
16. **References**

---

## 9. Limitations to state honestly

Stating these strengthens the paper; omitting them invites rejection.

- **No implementation, no benchmarks.** All quantitative claims are analytical. The prior prototype
  was discarded and nothing may be presented as measured.
- **Verification is only as good as the checks.** Open-ended creative output resists objective
  verification; the receipt proves *what ran*, not that an essay was good. Scope claims to task
  classes with checkable outcomes, and say so.
- **TEE trust shift.** Hardware vendor trust plus a live side-channel literature.
- **Challenger liveness.** Optimistic challenge needs at least one motivated honest challenger;
  incentives for challengers must be designed, not assumed.
- **Market timing.** Reported agent micropayment demand is thinner than ecosystem messaging
  suggests; the paper should acknowledge this rather than assume demand.
- **Collusion.** Requester–agent or validator–agent collusion is not fully solved by staking alone.
- **The onboarding tier is a subsidy, not a trust tier.** Full auditing of faucet-tier tasks is a
  platform cost that scales with onboarding volume, and the tier carries none of the paper's
  deterrence guarantees (§5.6). Growth in that tier is a cost center, not evidence of the
  mechanism working.
- **Learning from failures** is scoped to future work and carries unresolved data-ownership
  questions.

---

## 10. Reference list status

Verified during research for this brief (web-confirmed this session):

- ERC-8004 Trustless Agents — Ethereum Magicians discussion; `awesome-erc8004` resource index.
- *Can Trustless Agents Be Trusted? An Empirical Study of the ERC-8004 Decentralized AI Agent
  Ecosystem* — arXiv 2606.26028. Source of the placeholder-registration finding.
- *Agent-to-Agent Finance: Blockchain Payments and Trust Infrastructure for Autonomous AI Agents* —
  arXiv 2607.00245.
- *TessIndex: Capability Verified Identity System for the Agent Economy* — arXiv 2608.21942.
- *Agent TCP/IP: An Agent-to-Agent Transaction System* — arXiv 2501.06243.
- *SoK: Security of Autonomous LLM Agents in Agentic Commerce* — arXiv 2604.15367.
- *From Multi-Agent Systems and the Semantic Web to Agentic AI: A Unified Narrative of the Web of
  Agents* — arXiv 2507.10644.
- *Bittensor Protocol: The Bitcoin in Decentralized Artificial Intelligence? A Critical and
  Empirical Analysis* — arXiv 2507.02951.
- *Fetch.ai: An Architecture for Modern Multi-Agent Systems* — arXiv 2510.18699.
- x402 — Coinbase developer platform launch documentation; x402 Foundation (Coinbase/Cloudflare);
  adoption metrics via Allium and Coinbase reporting; CoinDesk (2026-03-11) on weaker-than-expected
  micropayment demand.
- Virtuals Protocol / ACP — Tiger Research, Delphi Digital, and Messari reports; virtuals.io.
- Olas / Autonolas — Tokenomics core technical document; Olas staking documentation (Proof of
  Active Agent).
- LLM cost reduction magnitudes — practitioner sources compiled this session (prompt caching,
  model routing, prompt compression, batching, semantic caching).

Cited from model knowledge — **IDs and editions must be verified before submission**:

- Douceur, *The Sybil Attack* (2002).
- Friedman & Resnick, *The Social Cost of Cheap Pseudonyms* (2001) — whitewashing argument.
- Kamvar, Schlosser & Garcia-Molina, *EigenTrust* (2003).
- Becker, *Crime and Punishment: An Economic Approach* (1968) — deterrence.
- Avenhaus, von Stengel & Zamir, *Inspection Games* (Handbook of Game Theory).
- Teutsch & Reitwießner, Truebit verification game (2017).
- Kalodner et al., *Arbitrum: Scalable, Private Smart Contracts* (USENIX Security 2018) — fraud proofs.
- Thompson (1933); Agrawal & Goyal, Thompson sampling regret analysis (2012).
- Badanidiyuru, Kleinberg & Slivkins, *Bandits with Knapsacks* (2013).
- Costan & Devadas, *Intel SGX Explained*; SGX side-channel literature (Foreshadow, SGAxe,
  Plundervolt class).
- RouteLLM (model routing); LLMLingua (prompt compression) — titles correct, arXiv IDs to confirm.
- zkML practicality surveys — specific citation to be selected.

Rule for drafting: no citation enters the paper without a resolvable source. Anything in the second
list is verified or cut.

---

## 11. Next step

Draft the full paper against §8, using the content-research-writer workflow: section by section,
with review between sections. The concise whitepaper is extracted from the **[W]** sections once the
full draft is stable.

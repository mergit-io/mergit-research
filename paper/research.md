# Mergit Paper — Research & Citation Register

Working reference register for the paper. Citation numbers here are **stable**: the draft cites
`[n]` against this list, so renumbering happens only here.

**Verification status is tracked per entry.** `VERIFIED` = confirmed via web research during this
project. `TO VERIFY` = recalled from model knowledge, title/author believed correct, exact
venue/year/ID must be confirmed before submission. Nothing marked `TO VERIFY` may remain in the
final paper unchecked.

---

## A. Agent trust protocols & standards

**[1] ERC-8004: Trustless Agents.** `VERIFIED`
Ethereum ERC proposal. Extends the A2A protocol with a trust layer: three on-chain singleton
registries — Identity (ERC-721 handle, tokenId → tokenURI pointing to an off-chain agent
registration file), Reputation (authorized clients post feedback: score, tags, optional URI +
hash), Validation (records independent checks of an agent's work). Content-heavy artifacts stay
off-chain (IPFS/HTTPS); only pointers and commitments go on-chain. Registration schema supports
A2A, MCP, OASF, ENS, DID service endpoints.
Stated design goal: high-quality agents should not reset to zero on entering a new environment,
and low-quality/malicious agents should not be able to cheaply reintroduce themselves.
→ https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098
*Use in paper:* primary prior art; Mergit implements/extends these registries (decision 9).
*Note:* the standard's own rationale states the whitewashing problem but the registries do not
themselves price identity creation — this is the opening Mergit's staking design addresses.

**[2] Xiong et al. (2026). "Can Trustless Agents Be Trusted? An Empirical Study of the ERC-8004
Decentralized AI Agent Ecosystem."** arXiv 2606.26028. `VERIFIED`
Empirical finding: many ERC-8004 registrations are **placeholders rather than fully operational
agents**; the ecosystem is still maturing.
→ https://arxiv.org/html/2606.26028
*Use in paper:* **load-bearing citation.** This is the evidence that the trust layer exists but is
not operationally used — i.e. the gap is not the protocol, it's the absence of a runtime bound to
it. Cite in abstract-adjacent intro and in Related Work.

**[33] awesome-erc8004** — curated ERC-8004 resource/ecosystem index. `VERIFIED`
→ https://github.com/sudeepb02/awesome-erc8004
*Use in paper:* ecosystem breadth footnote only; not a load-bearing claim.

**[17] "TessIndex: Capability Verified Identity System for the Agent Economy."** arXiv 2608.21942.
`VERIFIED`
Characterizes ERC-8004 as lightweight and registry-specific — providing identity, feedback and
validation but *not* the broader components needed to support commerce and trust.
*Use in paper:* independent corroboration that the registry layer alone is insufficient. Strong
support for the "missing execution/commerce layer" argument.

**[16] "Agent-to-Agent Finance: Blockchain Payments and Trust Infrastructure for Autonomous AI
Agents."** arXiv 2607.00245. `VERIFIED`
*Use in paper:* framing for agent payment/trust infrastructure in Related Work.

**[13] "Agent TCP/IP: An Agent-to-Agent Transaction System."** arXiv 2501.06243. `VERIFIED`
*Use in paper:* prior art on agent-to-agent transaction substrates.

**[15] "From Multi-Agent Systems and the Semantic Web to Agentic AI: A Unified Narrative of the Web
of Agents."** arXiv 2507.10644. `VERIFIED`
*Use in paper:* intro context — situates the agent-economy premise in a longer research lineage,
which keeps the introduction from reading as crypto-cycle hype.

**[14] "SoK: Security of Autonomous LLM Agents in Agentic Commerce."** arXiv 2604.15367. `VERIFIED`
*Use in paper:* Security Analysis section — existing systematization of attack surface for agents
transacting autonomously. Check before drafting §12 to avoid re-deriving known attack classes.

---

## B. Payment rails

**[3] x402.** `VERIFIED`
Open HTTP-402-based payment protocol released by Coinbase, May 2025. Server returns HTTP 402 with
payment requirements (price, accepted tokens, destination); client signs a stablecoin transfer
authorization, resubmits, receives the resource after on-chain settlement. USDC on Base; supports
Base, Ethereum, Arbitrum, Polygon, Solana. x402 Foundation co-founded with Cloudflare, Sept 2025.
Zero protocol fees.
→ https://www.coinbase.com/developer-platform/discover/launches/x402
*Use in paper:* the payment rail Mergit is compatible with. **Critical distinction for the thesis:
x402 settles payment for _access_ to a resource, not for a _verified outcome_, and has no
revocability.** This is the gap C4 fills.

**[4] x402 adoption metrics.** `VERIFIED`
By April 2026: ~165M cumulative transactions, ~$50M volume, ~69,000 active AI agents. As of March
2026: 119M+ transactions on Base, 35M on Solana, ~$600M annualized volume.
→ https://www.allium.so/blog/x402-explained-the-internet-native-payments-standard-for-apis-data-and-agent-commerce/
*Use in paper:* evidence the agent-payment premise is real and at scale — strongest single data
point that this is not a speculative market.

**[5] CoinDesk (2026-03-11). "Coinbase-backed AI payments protocol wants to fix micropayment but
demand is just not there yet."** `VERIFIED`
Reports demand for agent micropayments is weaker than ecosystem messaging suggests.
→ https://www.coindesk.com/markets/2026/03/11/coinbase-backed-ai-payments-protocol-wants-to-fix-micropayment-but-demand-is-just-not-there-yet
*Use in paper:* **cite deliberately.** Including the counter-evidence is what separates this from
a pitch deck. Belongs in Limitations (market timing), and arguably in the intro as honest framing.

---

## C. Agent marketplaces, incentives, reputation

**[6] Virtuals Protocol / Agent Commerce Protocol (ACP).** `VERIFIED`
Decentralized platform on Base for creating/tokenizing/monetizing autonomous agents. ACP provides
smart-contract primitives for agents to transact across platforms: full on-chain flow of request →
negotiation → escrow → evaluation → settlement, with revenue splits and reputation. Trusted agents
receive more favorable terms/expedited negotiation; dispute-prone or unknown agents face stricter
terms or higher fees. Evaluation is recorded into an agent's reputation and used as a trust
indicator in later transactions.
→ Tiger Research, Delphi Digital, Messari reports; https://www.virtuals.io/
*Use in paper:* **closest prior art** — has escrow + evaluation + reputation-affects-terms.
Differentiation must be precise: ACP's evaluation is counterparty assessment of a delivered
product, not attested evidence of *how execution proceeded*; there is no runtime, no metered cost,
and no cost-adjusted trust dimension.

**[7] Bittensor subnets.** `VERIFIED`
Blockchain-coordinated market for digital commodities organized into subnets; each subnet sets its
own incentive mechanism with its own miners and validators. Miners perform the subnet's task;
validators score them. Emissions split 41% miners / 41% validators / 18% subnet owner.
→ https://bittensor.ai/learn/subnets
*Use in paper:* precedent for validator-scored agent quality at protocol scale.

**[8] "Bittensor Protocol: The Bitcoin in Decentralized Artificial Intelligence? A Critical and
Empirical Analysis."** arXiv 2507.02951. `VERIFIED`
Yuma Consensus detail: aggregates validator score vectors by computing a stake-weighted median
benchmark, clipping outlier weights, allocating miner emissions proportional to the clipped
aggregate; validator rewards accrue via exponentially smoothed bonds penalizing deviation from
consensus.
*Use in paper:* cite for stake-weighted aggregation and outlier-clipping as established mechanism
design. Also the honest counterpoint — a *critical* analysis, so cite it as such, not as
endorsement.
**Differentiation:** Bittensor rewards are inflation-funded for commodity production within a
subnet; Mergit's are requester-funded, per-task, and outcome-contingent.

**[9] Autonolas / Olas — Tokenomics Core Technical Document.** `VERIFIED`
→ https://olas.network/documents/whitepaper/Autonolas_Tokenomics_Core_Technical_Document.pdf
Bonding for protocol-owned liquidity; staking model for code contributions tracked on-chain;
veOLAS locking for governance; protocol fees burn OLAS.

**[10] Olas Staking — Proof of Active Agent (PoAA).** `VERIFIED`
Rewards *real agent activity* rather than passive token lockup; described as combining PoS and PoW
strengths but shifting rewards to agents delivering useful, verifiable outcomes — executing
on-chain actions or meeting KPIs. Mech Marketplace lets agents autonomously hire each other.
→ https://olas.network/staking
*Use in paper:* **nearest precedent for "stake tied to verified work."** Differentiation: PoAA
rewards activity/KPI satisfaction from protocol emissions; it is not per-task settlement of a
requester's payment conditional on an audited execution record, and has no clawback.

**[11] "Fetch.ai: An Architecture for Modern Multi-Agent Systems."** arXiv 2510.18699. `VERIFIED`
*Use in paper:* architecture comparison in Related Work.

**[12] Fetch.ai identity / ANAME.** `VERIFIED`
Identity layer requires agents to act on behalf of identifiable users/businesses rather than
anonymously; verified business agents carry a cryptographically signed credential proving brand
representation. Agent Name Service (ANAME) verifiably links agents to Web2 domain names as a
reputation signal. Scale reported 2026: 2.7M+ agents registered on Agentverse.
→ https://business.fetch.ai/
*Use in paper:* **direct precedent for decision 7** — external verifiable credentials as a trust
signal. Supports "credential reduces required stake" without having to invent the idea.

---

## D. Mechanism design foundations

**[18] Douceur (2002). "The Sybil Attack."** `VERIFIED 2026-10-24` (IPTPS 2002, LNCS 2429, pp. 251–260; doi:10.1007/3-540-45748-8_24)
*Note:* covers multiple identities, not identity replacement; the whitewashing claim rests on [19].
*Use:* canonical statement that cheap identity creation undermines reputation systems.

**[19] Friedman & Resnick (2001). "The Social Cost of Cheap Pseudonyms."** `VERIFIED 2026-10-24`
(J. Economics & Management Strategy 10(2):173–199; doi:10.1111/j.1430-9134.2001.00173.x)
*Use:* **best citation for the whitewashing argument** — formal treatment of why costless identity
replacement forces distrust of newcomers. Directly motivates staking at registration and the
cold-start posterior design.

**[20] Kamvar, Schlosser & Garcia-Molina (2003). "EigenTrust."** `VERIFIED 2026-10-24` (WWW 2003, pp. 640–651; doi:10.1145/775152.775242)
*Note:* bounds a rater's influence; it does not discount by counterparty diversity. Cite "in the spirit of".
*Use:* prior art on reputation aggregation in decentralized networks.

**[21] Becker (1968). "Crime and Punishment: An Economic Approach."** `VERIFIED 2026-10-24` (JPE 76(2):169–217; doi:10.1086/259394)
*Note:* deterrence, not proof-of-stake slashing.
*Use:* deterrence foundation — expected penalty (probability × severity) vs expected gain. Direct
support for §5.2's deterrence condition.

**[22] Avenhaus, von Stengel & Zamir (2002). "Inspection Games."** `VERIFIED 2026-10-24`
(Handbook of Game Theory with Economic Applications, Vol. 3, ch. 51, pp. 1947–1987; doi:10.1016/S1574-0005(02)03014-X)
*Use:* the formal game class Mergit's audit mechanism belongs to. Important for framing §5.2 as an
instance of a known game rather than an ad-hoc rule.

**[23] Teutsch & Reitwießner. "A Scalable Verification Solution for Blockchains" (Truebit).**
`VERIFIED 2026-10-24` (arXiv:1908.04756, 2019; whitepaper 2017; preprint, not peer-reviewed)
*Use:* **key precedent.** Verification game with forced errors (not sampled challenge) for
off-chain computation — the established design pattern Mergit's sampled-audit model extends from
deterministic computation to agent execution.

**[24] Kalodner et al. (2018). "Arbitrum: Scalable, Private Smart Contracts."** `VERIFIED 2026-10-24`
(USENIX Security 2018, pp. 1353–1370)
*Note:* a challenge/bisection protocol, not an optimistic-rollup paper; cite it for bisection to one on-chain step.
*Use:* fraud-proof / dispute-window precedent for optimistic acceptance with challenge.

**[25] Thompson (1933).** `VERIFIED 2026-10-24` (Biometrika 25(3/4):285–294; doi:10.1093/biomet/25.3-4.285)
**[26] Agrawal & Goyal (2012). "Analysis of Thompson Sampling for the Multi-armed Bandit Problem."**
`VERIFIED 2026-10-24` (COLT 2012, PMLR 23:39.1–39.26)
*Use:* routing policy foundation and regret results — **cited, not re-proven** (design brief §5.5).

**[27] Badanidiyuru, Kleinberg & Slivkins (2013). "Bandits with Knapsacks."** `VERIFIED 2026-10-24` (FOCS 2013, pp. 207–216, doi:10.1109/FOCS.2013.30; JACM 65(3), 2018, doi:10.1145/3164539)
*Use:* the budget-constrained bandit formalism C3 adapts. Regret behavior under budget constraints
is cited from here.

---

## E. Trusted execution

**[28] Costan & Devadas. "Intel SGX Explained."** `VERIFIED 2026-10-24` (IACR ePrint 2016/086)
*Note:* a 2016 explainer; it predates most real attacks, so the attack claims rest on [29a–d].
*Use:* TEE attestation mechanics for the runtime trust anchor (decision 15).

**[29a–d] Attacks on production TEEs.** `VERIFIED 2026-10-24`
- [29a] Van Bulck et al., *Foreshadow*, USENIX Security 2018, pp. 991–1008.
- [29b] Murdock et al., *Plundervolt*, IEEE S&P 2020, pp. 1466–1482, doi:10.1109/SP40000.2020.00057.
- [29c] De Meulemeester et al., *BadRAM*, IEEE S&P 2025, pp. 4117–4135, doi:10.1109/SP61157.2025.00104 (breaks SEV-SNP attestation).
- [29d] De Meulemeester et al., *Battering RAM*, IEEE S&P 2026, pp. 4391–4407, doi:10.1109/SP63933.2026.00052 (interposer under $50; breaks SEV-SNP attestation; physical-access threat model).
*Use:* **required honesty citation** for threat A5. Still open: AWS Nitro Enclaves documentation as a production-attestation example.

**[41] Sun, Li & Zhang (2024). "zkLLM."** `VERIFIED 2026-10-24` (ACM CCS 2024, pp. 4405–4419; doi:10.1145/3658644.3670334)
**[42] Peng et al. (2026). "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning."** `VERIFIED 2026-10-24` (Artificial Intelligence Review 59, art. 157; arXiv:2502.18535)
*Use:* proof-based verification is expensive rather than impossible (13B-parameter inference in under 15 minutes); the stronger obstacle is that inference proofs do not cover tool calls and side effects.

---

## F. Cost reduction (LLM tokens + gas)

**[32] Practitioner-reported magnitudes for LLM cost optimization.** `VERIFIED` (as practitioner
sources, not peer-reviewed)
- Prompt caching: ~90% reduction on cached input cost (Anthropic models); ~59–70% savings at an
  80% cache-hit rate. Described as the single highest-ROI production optimization.
- Model routing (frontier → budget mix): ~60–80% savings on per-query cost.
- Prompt compression: ~30–45% input-token savings.
- Batch processing: ~50% cheaper.
- Semantic caching: eliminates ~30–70% of redundant calls.
→ https://github.com/pleasedodisturb/awesome-llm-token-optimization and compiled practitioner
guides.
*Use in paper:* §11 cost reduction. **Attribute as practitioner-reported, not as peer-reviewed
measurement** — these are vendor/blog figures and overclaiming them would be the easiest thing in
the paper to attack.

**[30] Ong et al. "RouteLLM: Learning to Route LLMs from Preference Data."** `VERIFIED 2026-10-24` (ICLR 2025; arXiv:2406.18665; reports >2x cost reduction)
**[31] Jiang et al. "LLMLingua."** `VERIFIED 2026-10-24` (EMNLP 2023, pp. 13358–13376; arXiv:2310.05736; up to 20x compression)
*Use:* peer-reviewed anchors for the routing and compression claims, replacing reliance on [32]
wherever a primary source is available.

---

## F2. Verifiable inference, staking, and audit-game economics — **NOVELTY-CRITICAL**

Searched specifically to test whether design-brief §5.3's "stake substitutes for verification
compute" is already known. **It substantially is.** Recorded here in full because it forces a
reframing of the paper's novelty claims.

**[34] Shang, Z., Yu, Y., Chen, K. "Repeated-Game Security for Restaking-Based Verifiable
Inference."** arXiv 2608.09055, 2026-08-10. `READ IN FULL 2026-10-09`

**Full-read corrections to the summary-based notes below — all applied to the draft:**
- **Its one-shot test is not its contribution.** Definition 1 ("1-Round IC", `cαS ≥ Δ`) is
  structurally our `p·λS > g`, but [34] attributes it to existing slashing and inspection-game
  literature. Our earlier framing deferred to [34] for something it does not claim. Correct
  attribution: [21,22], with [34] stating it as a baseline.
- **Its actual thesis refutes our foundation.** Definition 4 defines *memoryless bounded-slashing*
  mechanisms (audits independent of history; slashing ≤ α_max·S; decisions depend on history only
  via current stake) and Theorem 4.2 shows these admit profitable repeated-game deviations when
  slashing is partial. **Our §7.2 rule satisfies all three conditions.** The gap is largest for
  patient providers with high stake relative to per-query rewards — and our Rule 1 mandates a high
  stake-to-value ratio, i.e. the adverse regime. Addressed in new §7.5 (history-dependent auditing
  coupled to §8 posteriors; `λ = 1` as conservative fallback). **Not yet proven adequate — listed in
  §13 and §14.**
- **The substitution is mislabeled in our earlier notes.** Appendix 0.D, Table 1: at δ_target = 0.95,
  raising signal gain from β = 0 to β = 0.5 cuts the required baseline audit rate from 0.370 to
  0.145 (≈2.6× saving). That is *signal responsiveness ↔ audit budget*, **not stake ↔ audit rate**.
  Their framing: "signal responsiveness substitutes for baseline audit budget, and history
  dependence is what makes the stake level feasible in the first place." Linear-cost claim
  confirmed.
- **It does build reputation.** §5.3 "Bayesian Reputation-Weighted Slashing": two-type model,
  posterior ρ_t over provider type, robust worst-case variant, penalty `(α₀ + α₁ρ̄_t)S_t`. So
  "deterrence only, no reputation" was false and is now removed from §3.5, §3.7, §8.1 and the
  whitepaper. What survives: reputation there weights *penalties*, not *selection*, and excludes
  cost.
- **It formally handles whitewashing.** Lemma 4: respawning is unprofitable iff
  `π₀ > c_reg(1 − δ(1 − c₀p̲)) / (α₁c₀S)`. Cited in §8.6 alongside [18,19]; a production
  registration-stake parameterization should be checked against it.
- **Scope confirms our differentiation, strongly.** §3.1 is a single query, verifier re-executes with
  probability c, binary action: contracted model vs cheaper substitute. No tool use, side effects,
  state mutation, or multi-step trajectories anywhere.
- **One point helps us:** Remark 3 notes re-execution audits are noisy — floating-point
  non-determinism and hardware heterogeneity can cause false disagreement between honest parties.
  Cited in §3.5: re-execution is already an imperfect oracle for pure inference.
- **Our `q > g/(λS)` threshold is not theirs.** Nearest analogue is their Arbitrum discussion ("one
  correct challenger deters false assertions because a caught cheater loses its bond in full"),
  which relies on full confiscation. Our threshold stands as original; lineage acknowledged.
- **Notation collision:** their `α` is our `λ` (slashing fraction); their `λ` is an
  exponential-weighting parameter. Warned in §7.2.

*Original summary-based notes retained below for provenance:*
→ https://arxiv.org/html/2608.09055
Setup is near-identical in structure to our §5: a provider posts stake and privately chooses
between running the contracted model or a cheaper substitute that saves computation cost; a
verifier re-executes queries with some probability; an on-chain mechanism schedules audits and
slashes fractions of the provider's stake on detected cheating. Explicitly analyzes substitution
effects on audit budget — reports that raising signal gain cuts the required baseline audit rate
from 0.370 to 0.145 at discount factor 0.95 (≈2.6× budget saving), and that history dependence is
what makes a given stake level feasible. Also notes the relevant counterpoint directly: raising
audit rates increases verification cost linearly for every honest query.
*Implication:* **our §5.2–5.3 result is an application of this class of analysis, not a new
result.** It must be cited as prior art and framed as adaptation. Claiming it as novel would be
the single most damaging error available to this paper.

**[35] "Proof of Sampling: A Nash Equilibrium-Based Verification Protocol for Decentralized
Systems."** arXiv 2405.00295. `VERIFIED`
Sampling-based verification protocol with Nash equilibrium analysis.
*Use:* prior art for sampled-audit verification as an equilibrium design.

**[36] Chan, Ding, Chen, Wu, Zhang, Tian. "Optimistic TEE-Rollups: A Hybrid Architecture for
Scalable and Verifiable Generative AI Inference on Blockchain."** arXiv 2512.20176, 2025-12-23.
`READ IN FULL 2026-10-09`

**Title correction:** our earlier citation said "...Verifiable Computation." The real title says
**Generative AI Inference on Blockchain**, which also helps us — the scope limitation is on the
title page. Fixed in §16.

**Full-read findings — all applied to the draft:**
- **Our novelty disclaimer is accurate.** Three tiers: Tier 1 provisional finality from a DCAP
  attestation quote over MRENCLAVE; Tier 2 fraud-proof "Fisherman Game"; Tier 3 **VRF-triggered
  stochastic ZK spot-checks at ρ ≈ 0.01**, which our earlier draft did not mention and §3.5 now
  does.
- **Our differentiation holds and was understated.** Dispute resolution is deterministic replay by
  construction: a Fisherman recomputes locally "using bit-wise deterministic settings", and
  divergence triggers interactive bisection over transformer layers, then over matrix
  multiplications, until a single disputed operation executes on-chain. Bit-wise determinism is a
  stated precondition. No treatment of side effects, irreversibility, or non-restorable state. Now
  quoted in §3.5.
- **Tiered disclosure is theirs, not ours.** §3.4.2 reveals only the divergent state during a
  dispute, explicitly to protect the user's prompt, and criticizes full-trace reproduction on
  privacy grounds — the same motivation as our §6.3. **§6.3 now credits them** and narrows our claim
  to extending selective disclosure from a tensor-level divergence point to an evidence subset of a
  trajectory where no divergence point exists.
- **Value-scaled assurance is theirs.** §4.3.1 varies ρ from 0 for a $0.01 query to 1 for a $1000
  trade. Cited in §7.2 as precedent for Rule 1 and for category-dependent dispute windows.
- **Their TEE-compromise fallback is strictly stronger than ours and does not transfer.** §4.2.2:
  even an adversary extracting the TEE signing key "cannot forge the execution trace"; a broken TEE
  "behaves like a standard OpML sequencer" and bad outputs are bisected and slashed. Their ZK
  spot-checks need no TEE honesty at all. Both remedies require determinism. **§12.5 now concedes
  this explicitly** rather than implying parity, and it raises the priority of k-of-n redundant
  execution for us.
- **PoEA is not our receipt.** It binds *model identity* (MRENCLAVE ∈ registry) to output — "was
  this the model you paid for" — via a flat tuple (y, σ_TEE, H(·)) on a DA layer, with "execution
  trace" meaning internal tensor computation. No hash-chaining, no sequence numbers, no evidence
  subsets. Our §6.2 structure stands as distinct.
- **They cite [34]'s Theorem 2** for their deterrence condition (eq. 7, `p_detect·S > G`),
  independently confirming that the one-shot form is shared prior art rather than anyone's
  contribution.
- **Cost-comparison risk.** They report ≈ **$0.07/query** end-to-end from H100 simulation (vs opML
  $0.05, ZKML $50+), and a gas table (≈40k gas signature check vs ≈350k for ZKML). Our §11.5
  tenths-of-a-cent audit figure reads as aggressive against that. **§11.5 now pre-empts the
  comparison**, distinguishing marginal evidence-audit cost from end-to-end per-query cost and
  conceding their simulated figure is the more credible anchor.
- They also assume ≥ 1 honest watchtower — the same liveness dependency as our `q`.

*Original summary-based note retained for provenance:* TEE attestation combined with optimistic
challenge, architecturally the closest published analogue to Mergit's trust anchor plus challenge
window; must be cited and differentiated in §6 and §12.

**[37] "Nondeterminism-Aware Optimistic Verification for Floating-Point Neural Networks."**
arXiv 2510.16028. `VERIFIED`
Handles the problem that re-execution does not reproduce bit-identical results.
*Use:* important — supports our argument that re-execution is fragile, and shows that even the
*inference* setting has had to confront non-reproducibility. Our setting is strictly harder.

**[38] "EigenAI: Deterministic Inference, Verifiable Results."** arXiv 2602.00182. `VERIFIED`
*Use:* related work on making inference verifiable by making it deterministic — a different
strategy (constrain execution to be reproducible) than ours (attest execution that is not).

**[39] Naysayer proofs.** Cryptology ePrint 2023/1472. `VERIFIED`
Optimistic verification mode for resource-constrained verifiers such as smart contracts.
*Use:* cheap-rejection verification precedent for §6.

### What survives as novel after this finding

Assessed honestly against [34]–[39]:

- **Does NOT survive:** stake-substitutes-for-audit-rate as a *result*. Published [34].
- **Does NOT survive:** TEE + optimistic challenge as an *architecture*. Published [36].
- **Survives:** the **domain shift**. [34]–[38] verify *inference* — a single, re-executable,
  functionally pure model call, where the verification question is "did you run model X." Mergit
  verifies *agent task execution*: multi-step, tool-using, side-effecting, and not re-executable
  even in principle once the agent has mutated a repository, called an external API, or spent
  money. Re-execution is not merely expensive in our setting, it is often undefined — and [37]
  shows the literature already strains against non-reproducibility in the far easier inference
  case. Receipts are a response to non-reproducibility, not merely to cost.
- **Survives:** **cost-adjusted reputation** (C2). None of [34]–[39] builds a reputation system at
  all; they build deterrence mechanisms. Scoring agents on verified quality per unit metered cost
  remains unclaimed.
- **Survives:** **budget-constrained bandit routing over on-chain reputation posteriors** (C3).
- **Weakened:** revocable settlement (C4) — now a transposition of challenge-period semantics
  [24,36] to task-granular agent payment, which is a contribution of engineering framing rather
  than of mechanism.

**Required paper changes:** demote the substitution result from "central result" to "adaptation of
[34] to a non-reproducible execution setting"; promote C2 and the non-reproducibility argument to
carry novelty; cite [34] and [36] prominently rather than burying them, since a reviewer who knows
this literature will otherwise reject on prior art alone.

---

## G. Research gaps still open

- [x] **CLOSED (2026-10-24).** zkML: [41] zkLLM (CCS 2024) and [42] survey.
- [x] **CLOSED (2026-10-24).** [29a–d]: Foreshadow, Plundervolt, BadRAM, Battering RAM.
- [x] **CLOSED (2026-10-24).** RouteLLM arXiv:2406.18665; LLMLingua arXiv:2310.05736.
- [x] **CLOSED (2026-10-24).** All `TO VERIFY` entries confirmed against DOI/publisher/arXiv records; 0 remain.
- [x] **CLOSED (2026-10-09, negative result).** Checked whether existing work formalizes *stake
      substituting for verification compute*. It does — see §F2 [34]. The result is prior art;
      novelty claims reframed accordingly.
- [x] **CLOSED (2026-10-09).** [34] and [36] both read in full; corrections applied to §§3.5, 3.7,
      6.3, 7.2, 8.1, 8.2, 8.6, 11.5, 12.5, 13, 14, 16 and to the whitepaper. Two material outcomes:
      a wrong title for [36], and the discovery that our §7.2 rule falls inside [34]'s
      memoryless-bounded-slashing impossibility class (new §7.5).
- [x] **CLOSED (2026-10-09).** Designed the audit-rate coupling. Outcome recorded in §H below; §§7.2,
      7.4, 7.5, 7.6 rewritten, plus §1.5, §10.4, §11.5, §13, §14 and the whitepaper.
- [ ] Re-derive §7.6's deviation argument inside [34]'s formalism, with recoverable collateral less
      than `λS` under restaking. Carried in §14.
- [~] **PARTLY CLOSED (2026-10-24).** `θ_LCB` quantile set to 0.01 by simulation (§7.7), against the earlier
      rate; to be rechecked against the corrected rate, and ideally set from the cost of a missed falsification.
- [ ] Re-check whether anything in [34]'s §5.3 (reputation-weighted slashing) or Lemma 4
      (whitewashing) should further constrain our registration-stake parameterization in §8.6.
- [ ] Read [14] (SoK on agentic commerce security) in full before the public version; positioned against its taxonomy rather than duplicated (open), to position
      against its taxonomy rather than duplicate it.

---

## H. The audit-rate coupling (worked 2026-10-09)

Design record for §§7.2–7.6. Three findings, in order of importance.

### H.1 The paper's deterrence condition was wrong

The pre-existing condition `p* = (V + c_exec)/(λS)` was mis-derived in two ways at once. It took the
defection gain as `V + c_exec`, which double-counts: the agent receives `V` in both branches when
undetected, so `V` cancels and the gain is the *saved work* plus the forgone expected value of
attempting honestly. And it omitted payment forfeiture from the penalty side, although escrow
returns to the requester on a failed audit (§10.1). Correct condition:

```
P_d · (V + λ·S)  ≥  c_exec + (1 − θ)·V
```

The old formula was ≈2.9× over-conservative (0.100 vs 0.034 at `V=2, c_exec=1, θ=0.95, λ=1, S=30`).
Being conservative was not harmless: it inflated every cost figure in §7.4 and §11.5, and it
obscured the `θ`-dependence that H.2 depends on. All numbers re-derived.

### H.2 `f` should not be invented — it is the condition evaluated at a pessimistic posterior

Because `p*` depends on the agent's `θ`, and §8.2 already maintains `Beta(α, β)` over `θ`, the audit
rate is just the deterrence condition at a lower-confidence bound:

```
p(a,k) = ( c_exec + (1 − θ_LCB(a,k))·V ) / (V + λ·S)
```

Every property demanded of `f` then follows from the derivation rather than being imposed: bounded
below by `c_exec/(V + λS) > 0` as `θ_LCB → 1`; rising on validated failure; rising under posterior
uncertainty, so newcomers are audited most; and history-dependent, which exits [34]'s Definition 4.

Sampled rates at `S=30`: `θ=0.95 → 0.034`, `θ=0.6 → 0.056`, `θ=0.2 → 0.081`. At `S=5`: 0.157, 0.257,
0.371. Spread widens as collateral thins, which is the right direction.

**Deliberately rejected:** lowering `p` in exchange for an agent's continuation value ("too much
future business to risk it"). The agent privately knows its exit intention and the platform does
not, so crediting continuation value sets `p` lowest for exactly the agent planning an exit scam.
Continuation value explains compliance; it may not set the floor.

### H.3 History-dependence alone does **not** answer Theorem 4.2 — the volume channel does

This corrects the earlier §7.5. The substance of bounded-slashing failure is not history-blindness
but *volume*: one stake secures many concurrent tasks while slashing is capped at `λS`, so an agent
defecting on `n` in-flight tasks simultaneously collects `n` times the gain against a single slash.
A posterior-derived audit rate does nothing here, because no posterior has updated yet when the
defections are simultaneous.

Forfeited payments scale with `n`; the slash does not. Hence

```
n · (c_exec + (1 − θ)V)  ≤  n · P_d · V  +  λS
  ⟹  n_max = λS / [ (c_exec + (1 − θ)V) − P_d·V ]
```

At `V=2, c_exec=1, θ=0.95, λ=1, P_d=0.05`: `n_max = 30`, linear in stake. Unbounded only when
`P_d·V` exceeds the per-task gain, i.e. `P_d ≥ 0.55` — not the operating regime. Enforced **per
operator**, not per identity, since one operator can defect across all identities at once. This also
replaces the informal "bounds this, imperfectly" remark in §10.4.

### H.4 Deviation argument and its standing

(i) gives pointwise one-shot IC at every reachable history; continuation effects of detection are
weakly negative (probation, lost routing share), so accounting for them strengthens the inequality.
By the one-shot deviation principle, no deviation built from single-task deviations pays. (ii) bounds
the only deviation that is not of that form — simultaneous multi-task defection. (iii) prevents a
second attempt under a softly-updated posterior.

**Standing:** a derivation under §5.2's assumptions, not a theorem in [34]'s formalism. Named
dependencies: recoverable collateral assumed `= λS`, which **restaking undercuts** — and [34] is
specifically about restaking, so this is the weakest joint; `P_d` depends on a challenger population
the protocol does not enforce; adjudication rests on evidence rather than recomputation, so both
`θ`-estimates and falsification findings carry noise absent from the deterministic setting.

---

## I. Publishing research and new sources (2026-10-10)

### I.1 [40] and the three papers it points to (read in full 2026-10-24)

**[40] "SoK: Blockchain Agent-to-Agent Payments"** (arXiv 2604.03733, q-fin.GN) — `READ IN FULL`.
A short SoK with no mechanism or evaluation. Names "financial finality does not establish
fulfillment", payment–service decoupling and limited accountability as open; proposes a "shared
append-only execution record" as a direction. Does not cover escrow, slashing, re-execution,
revocable settlement, cost as a trust signal, or routing.

Three papers it cites overlap the novelty claims; all `READ IN FULL`:
- **[43] A402** (arXiv 2603.01179v2): TEE-assisted adaptor signatures bind payment to attested
  execution of a *single* service call; TEE fully trusted; no stake or audit; payment final.
- **[44] Acharya / TIVA** (arXiv 2511.15712): authenticity and intent of an agent's *payment*
  (DIDs, intent proofs, ZK compliance, optional TEE code attestation); does not verify the work.
- **[45] Insured Agents** (arXiv 2512.08737, submitted to AAMAS 2026): insurer agents post slashable
  stake and get TEE audit access; one-shot equilibrium; verification an errorless oracle; credits
  future business in deterrence. Closest in spirit; hence "insured exploratory draws" was renamed
  "subsidized" and the "insurance fund" renamed "residual-loss reserve" in the paper.

Effect on claims: C1 (cost-adjusted reputation) and C4 (routing) untouched; C2 narrowed to
multi-step, side-effecting trajectories; C3 gains a contrast with [45]; C5 narrowed to clawback
bounded by encumbered stake. Nothing dropped.

**ERC-8004 [1]** (checked 2026-10-24; status Draft): names stake-secured re-execution, zkML verifiers
and TEE oracles as validator models, and leaves "incentives and slashing related to validation" to the
validation protocol. The paper's "registry without a runtime" framing stands but is stated precisely.

### I.2 Reference fix (resolved)

**[23] Truebit** — arXiv 1908.04756 (located by search). † status downgraded to "confirm against
record"; was previously venue-less.

### I.3 Policy change that reclassifies citation hygiene as risk

arXiv began issuing **one-year submission bans in May 2026** for *unchecked* AI-generated content —
hallucinated references and leftover chatbot prose specifically. AI assistance is permitted; the
author is accountable for every line and every citation. Consequence for this paper: the 14
† citations were not a polish item but a precondition for posting anything; all are now verified (0 remain). The paper's
own rule ("nothing unresolvable stays in") is now also arXiv's rule, with teeth. Venue policies on
AI disclosure remain under-specified; the norm is a brief disclosure of substantial assistance.

### I.4 Venues (as of 2026-10-10)

| Venue | Fit | Format | Status |
|---|---|---|---|
| **FC'27** (Financial Cryptography) | Best scope fit: incentive design, game theory for blockchain, smart contracts | LNCS; 15 pp regular, 8 pp short, 20 pp SoK; anonymized; **arXiv preprints explicitly permitted** | Deadline 24 Sep 2026 **passed**. Target **FC'28** (~Sep 2027) or an FC'27 workshop (CFPs typically Nov–Dec 2026) |
| **AFT 2027** | Closest culturally — mechanism design + verifiable computation; LIPIcs; proof-based papers accepted | ~May–June 2027 deadline historically | CFP not yet posted; watch aft.ifca.ai |
| **AAMAS 2027 Blue Sky Ideas** | The one track that explicitly wants vision / no-results work | **4 pp + refs, deadline 12 Nov 2026**; needs a "why Blue Sky" rationale and author track record | Open — nearest stake in the ground |
| **AGENT 2027 @ ICSE** | Verification, accountability, governance of agentic systems (not economics) | **5 pp incl. refs, deadline 13 Nov 2026**; single-anonymous; IEEE | Open |
| ACM EC 2027 | Theory-heavy; would expect formal results | ~Feb 2027 pattern | CFP not posted |
| S&P / NDSS / ASIACCS / CCS 2027 | Would demand real evaluation | arXiv preprints tolerated | Not yet appropriate |
| CESC, SBC | Good talk venues, non-archival (SBC accepts already-submitted work) | — | Visibility, not publication credit |

### I.5 arXiv process

- **Endorsement policy changed 21 Jan 2026**: institutional email alone no longer suffices;
  automatic endorsement needs institutional email *and* prior claimed authorship in the domain.
  Otherwise: personal endorsement from an active author in the category — an advisor or faculty
  member is the standard route. **Start this now; it is the gating step.**
- Category: **cs.CR primary** (attestation / slashing / verification is security framing; [34] and
  [36] live there), cross-list **cs.GT** and **cs.MA**. cs.DC is a poor fit.
- License: arXiv default non-exclusive is fine for later venue submission; CC BY 4.0 only if open
  reuse is wanted.
- Preprint-then-submit is the field norm; FC and S&P say so explicitly.

### I.6 What reviewers expect without an implementation

USENIX's guidance: design-only papers "face skepticism" unless the idea is obviously strong and
there is "initial experience in the closing sections." Top rejection reason is a system "isomorphic
to well-known predecessors" — exactly the risk [34]/[36] posed, and why the differentiation work
mattered. Analytical-only *is* publishable at FC/AFT when the contribution is a mechanism with
formal properties.

Precedents: Truebit was a whitepaper, never peer-reviewed; Arbitrum went to USENIX Security 2018
*with* a prototype; the ERC-8004 study [2] is empirical and arXiv-only.

**Minimal evaluation that moves Mergit from vision to research:**
(a) **agent-based simulation of §7.5–7.6** — deviation profitability vs stake, concurrency, and
`θ_LCB` quantile; show the volume attack succeeds without the concurrency cap and fails with it.
Cheap, and sufficient for FC/AFT. Converts "argued" to "shown."
(b) **a receipt-emitting harness prototype** on a few real repository tasks, measuring `c_audit`
against `c_exec`. What security venues would want.

### I.7 Craft guidance applied

Peyton Jones: one idea per paper; contributions as refutable bullets; intuition before formalism;
related work after the idea. USENIX: abstracts state assumptions and concrete results, not a table
of contents. Applied 2026-10-10: abstract cut from ~430 to ~290 words; running example added
(§2.2, threaded through §4.2, §6.2, §7.4); three figures specified (`paper/figures/`). Still open:
compression from ~20k words to ~15 pp LNCS for an FC-class venue.

### I.8 Recommended order

1. Verify every † citation; read [40] in full. (Gating — see I.3.)
2. Build the §7 simulation (I.6a). Cheapest step that changes the paper's category.
3. Secure an arXiv endorser (I.5). Post to arXiv cs.CR once 1–2 are done.
4. Submit a 4-page AAMAS Blue Sky (12 Nov 2026) or 5-page AGENT@ICSE short (13 Nov 2026) as a
   stake in the ground, derived from the whitepaper.
5. Compress to 15 pp LNCS for FC'28 or LIPIcs for AFT 2027, with the simulation as the evaluation
   section.


---

## J. Verification log, 2026-10-24

Method: each entry checked against Crossref, the publisher page or the arXiv record (DBLP was rate-limited).
Result: **all 14 previously unverified entries are real; none was hallucinated.** Corrections:
[22] gained year, chapter, pages and editors; [28] gained its report number; [30], [31] gained authors,
IDs, venues. Claims the sources do not fully support, now reworded in the paper: [24] is not an
optimistic-rollup paper; [21,22] cover deterrence, not proof-of-stake slashing; [20] does not discount by
counterparty diversity; [18] does not cover identity replacement; zkML is expensive, not impossible
([41] proves a 13B-parameter inference in under 15 minutes). Remaining gap: [1]–[17] and [32]–[39] were
confirmed during the research phase and not re-checked in this pass.


---

## K. Simulation findings, 2026-10-24

Code and data in `sim/` (agent-based model, five mechanisms M0–M4, six deviations, 400–2000 seeds per
cell; nine unit checks reproduce the §7.4 table and the break-even concurrency). Result: **two claims of
the previous revision failed** and are corrected in paper §7.2, §7.5, §7.6, with §7.7 reporting the run.

1. **§7.5(ii) concurrency bound.** The slash is incurred only if at least one receipt is detected, so the
   exact condition is `n(g − P_d·V) ≤ λS[1 − (1 − P_d)^n]`; at the paper's example the break-even is 18, not
   30, and at the one-shot rate any `n ≥ 2` is profitable. Fix: size the audit rate jointly with a
   per-operator allowance.
2. **§7.2 fake-on-failure.** After a failed honest attempt `c_exec` is sunk, so forging needs
   `P_d ≥ V/(V + λS)` whatever `θ` (0.0625 vs 0.034 at `S = $30`). Fix: `g(θ) = max(c_exec + (1 − θ)V, V)`.
3. Probation at `p = 1` lifted the cap (fix: the allowance is a parameter, kept during probation).
4. §8.2 needs: update the posterior from audited receipts only (else downward bias).

Both mathematical failures were also checked by hand outside the simulation. The corrected mechanism
(M4) shows no significantly profitable deviation in 108 cells; this is evidence about inequalities in the
model, not about unmodelled attackers. Not re-run under the corrected rate: audit concentration (E4), the
quantile table (E3). Residual risks: strategies are fixed, adjudication error-free, no restaking.

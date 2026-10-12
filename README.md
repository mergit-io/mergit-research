# Mergit — research

> **Pay for what you got.** A trust and settlement layer for autonomous agent work.

This repository holds the paper that defines Mergit. The project is **pre-implementation**: there
is no runtime, no deployed contract and no measurement. The argument is the artifact, so this repo
is currently the source of truth for the whole project — `mergit` (runtime and product
requirements) and `mergit-contracts` follow from the decisions locked here.

## The argument in brief

Delegate a task to an agent today and you are billed for the attempt. Tokens, tool calls and
sandbox minutes are metered precisely; whether the task was *done* is not metered at all. By April
2026 roughly 69,000 autonomous agents had settled some 165 million payments on a single protocol,
and none of those payments was contingent on verified completion.

This is not for want of infrastructure. Payment rails, identity registries and agent marketplaces
all exist. The obstacle is that **outcome-contingent payment has only ever been solved for work
that can be re-executed** — post stake, re-run the query, slash on mismatch. Agent work cannot be
re-run: it is multi-step, tool-using and side-effecting, so the repository has already changed, the
API call has already landed, and the money has already moved. The binding constraint is not the
price of verification but its definability.

Mergit owns the execution environment, which none of the existing systems do. So it attests
execution rather than reproducing it:

- **Verifiable Execution Receipts** — hash-chained, TEE-attested records of what actually ran, with
  a Merkle root on chain and tiered disclosure (totals at settlement, evidence subset at audit, full
  trajectory only under bonded challenge).
- **Verification economics** — stake, per-agent audit rates derived from a posterior over
  capability, permissionless bonded challenge, and a concurrency cap so one stake cannot secure
  unlimited simultaneous work.
- **Cost-adjusted reputation** — the headline contribution. Reputation is verified quality *per unit
  cost* (`D = E[verified success] / E[metered cost]`), not quality alone, which is possible only
  because metering is attested.
- **Routing as a decision policy** — Thompson sampling over value density under budget, with the
  platform bearing exploration's downside so requesters do not opt out of it.
- **Revocable settlement** — escrow released on a passing audit or dispute-window expiry; a
  successful challenge refunds, rewards and slashes.

## How to read this

| Start here if you want | Read |
| --- | --- |
| The argument in 15 minutes | [`paper/whitepaper.md`](paper/whitepaper.md) |
| The full treatment | [`paper/draft-v1.md`](paper/draft-v1.md) |
| Why each design choice was made | [`docs/superpowers/specs/2026-10-09-mergit-research-paper-design.md`](docs/superpowers/specs/2026-10-09-mergit-research-paper-design.md) — 17 locked decisions with rationale |
| Our honest account of what is weak | [`paper/draft-v1.md`](paper/draft-v1.md) §13 Limitations |
| Sources, and which are verified | [`paper/research.md`](paper/research.md) |

### The full paper, by section

| § | | § | |
|---|---|---|---|
| 1 | Introduction | 9 | Routing under budget constraints |
| 2 | Problem statement | 10 | Settlement and revocability |
| 3 | Related work | 11 | Cost reduction across tokens and gas |
| 4 | Design overview | 12 | Security analysis |
| 5 | Threat model and assumptions | 13 | **Limitations** |
| 6 | Verifiable Execution Receipts | 14 | Future work |
| 7 | Verification economics | 15 | Conclusion |
| 8 | **Cost-adjusted reputation** | 16 | References |

Figures live in [`paper/figures/`](paper/figures/) — `.mmd` sources are Mermaid, and
`fig_audit_rate.py` regenerates its own PDF and PNG.

## Conventions

- **Markdown first**, structured for later LaTeX/arXiv conversion.
- **Citation numbers are stable and owned by [`paper/research.md`](paper/research.md).** The draft
  cites `[n]` against that register, so renumbering happens there and nowhere else.
- **Every source carries a verification status.** `VERIFIED` means confirmed by reading the source;
  `TO VERIFY` means believed correct but unconfirmed. Nothing marked `TO VERIFY` may remain in a
  submitted version.
- **Nothing may be claimed as measured.** Every quantitative figure is arithmetic on the stated
  model. The prior prototype was discarded and the system is being rebuilt.

## What we are not claiming

Stated at length in §13, and summarised because it matters more than the pitch: verification scope
covers *checkable* outcomes only (tests pass, hashes match, chain state changed) — open-ended
judgment gets nothing, which is why software engineering is the flagship domain. TEE attestation
relocates trust to hardware vendors rather than removing it, and unlike deterministic systems we
cannot fall back on replay when a TEE is compromised. Repeated-game soundness is argued, not proven.
Routine verification is centralized at v1. The economics depend on challengers actually existing.
Weak predicates are the likeliest real-world failure, and the system cannot protect a requester from
under-specifying their own task.

## Contributing

Corrections are the most valuable contribution right now — especially prior art we mis-positioned,
a derivation that does not follow, a deviation that profits an attacker under our own conditions, or
a sentence that claims more than its evidence supports.

Use the **Paper correction** or **Mechanism challenge** issue form, and see
[CONTRIBUTING.md](https://github.com/mergit-io/.github/blob/main/CONTRIBUTING.md).

## Citing

```bibtex
@misc{mergit2026,
  title  = {Mergit: Pay for What You Got --- A Trust and Settlement Layer for Autonomous Agent Work},
  author = {Mergit},
  year   = {2026},
  note   = {Draft 1. https://github.com/mergit-io/mergit-research}
}
```

**Licence:** the paper text is intended to be CC BY 4.0, matching the documentation in
[`mergit/docs`](https://github.com/mergit-io/mergit/tree/main/docs). The `LICENSE` file still needs
to be added to this repo.

---

<sub>Project overview: <a href="https://github.com/mergit-io">github.com/mergit-io</a> · Archived v0 prototype: <a href="https://github.com/mergit-io/Mergit-proto">Mergit-proto</a></sub>

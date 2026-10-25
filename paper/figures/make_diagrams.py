#!/usr/bin/env python3
"""Draw Figures 1 and 2 of the paper as SVG, and rasterize them to PNG.

    python3 paper/figures/make_diagrams.py

Figure 1: task lifecycle and trust boundaries (section 4.2).
Figure 2: structure of a Verifiable Execution Receipt and its disclosure levels (sections 6.2, 6.3).

These replace the Mermaid sources fig_lifecycle.mmd and fig_receipt.mmd, whose automatic layout was
too wide to read at page width. The content is the same; only the layout is drawn by hand.

Needs only the standard library to write the SVG. The PNG step calls ImageMagick (`magick`) built
with librsvg; if it is missing the SVG is still written and the PNG step is skipped.
"""
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "Inter, Helvetica, Arial, sans-serif"
INK = "#1f2430"
MUTED = "#5b6270"
LINE = "#8a93a3"

# Palette: a role per colour, so the same thing looks the same in both figures.
TEE = ("#e4f3e9", "#3b8a5a")        # attested runtime: the only party that asserts what ran
CHAIN = ("#e6eefc", "#4a74c9")      # on-chain: commitments and value
NEUTRAL = ("#f6f7f9", "#b4bac6")
REP = ("#f0e9fb", "#7b5cc7")        # reputation: derives only
EVID = ("#fff2cf", "#c48a1d")       # outcome-bearing evidence
WHITE = ("#ffffff", "#8a93a3")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def spans(line: str, bold: bool = False) -> str:
    """**bold** and _{subscript} inside a line."""
    out = []
    for tok in re.split(r"(\*\*.+?\*\*|_\{.+?\})", line):
        if not tok:
            continue
        if tok.startswith("**"):
            out.append(f'<tspan font-weight="700">{esc(tok[2:-2])}</tspan>')
        elif tok.startswith("_{"):
            out.append(f'<tspan baseline-shift="sub" font-size="72%">{esc(tok[2:-1])}</tspan>')
        else:
            out.append(esc(tok))
    return "".join(out)


class Svg:
    def __init__(self, w: int, h: int):
        self.w, self.h, self.parts = w, h, []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def rect(self, x, y, w, h, fill, stroke, rx=8, sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, lines, size=11.5, anchor="middle", color=INK, weight=400, italic=False, lh=None):
        """Lines are centred vertically on y."""
        lh = lh or size * 1.3
        y0 = y - (len(lines) - 1) * lh / 2 + size * 0.35
        style = ' font-style="italic"' if italic else ""
        tspans = "".join(
            f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{spans(line)}</tspan>' for i, line in enumerate(lines)
        )
        self.add(
            f'<text x="{x}" y="{y0:.1f}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" '
            f'fill="{color}" font-weight="{weight}"{style}>{tspans}</text>'
        )

    def box(self, cx, cy, w, h, lines, colors=WHITE, size=11, **kw):
        self.rect(cx - w / 2, cy - h / 2, w, h, colors[0], colors[1], **kw)
        self.text(cx, cy, lines, size=size)

    def arrow(self, pts, dashed=False, color="#3a4150"):
        d = " ".join(f"{x},{y}" for x, y in pts)
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self.add(
            f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.4"{dash} '
            f'marker-end="url(#head)" stroke-linejoin="round"/>'
        )

    def render(self) -> str:
        defs = (
            '<defs><marker id="head" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" '
            'markerUnits="userSpaceOnUse"><path d="M0,0.5 L9,4.5 L0,8.5 z" fill="#3a4150"/></marker></defs>'
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}">{defs}'
            f'<rect width="{self.w}" height="{self.h}" fill="#ffffff"/>' + "".join(self.parts) + "</svg>\n"
        )


# --------------------------------------------------------------------------- Figure 1

def lifecycle() -> Svg:
    LANE, X0, TOP = 140, 10, 10
    lanes = [
        ("Requester", [], NEUTRAL),
        ("Orchestrator", ["policy over posteriors;", "asserts nothing"], NEUTRAL),
        ("Ethereum L2", ["holds commitments", "and value only"], CHAIN),
        ("Attested runtime", ["(TEE)", "**the only party that**", "**may assert what**", "**executed**"], TEE),
        ("Validation layer", ["permissioned at v1"], NEUTRAL),
        ("Any bonded party", ["permissionless", "challenge"], NEUTRAL),
        ("Reputation engine", ["derives only"], REP),
    ]
    cx = [X0 + LANE * i + LANE / 2 for i in range(len(lanes))]
    R, O, C, T, V, X, G = cx

    STEP, Y1 = 62, 150
    ys = [Y1 + STEP * k for k in range(14)]
    H = int(ys[-1] + 56)
    s = Svg(X0 * 2 + LANE * len(lanes), H)

    for i, (name, sub, col) in enumerate(lanes):
        x = X0 + LANE * i
        s.rect(x + 3, TOP, LANE - 6, H - 2 * TOP, col[0], col[1], rx=10, sw=1.6 if col is TEE else 1.0,
               dash=None if col is not NEUTRAL else "3 3")
        s.text(cx[i], TOP + 20, [f"**{name}**"], size=12.5)
        if sub:
            s.text(cx[i], TOP + 36 + 7 * len(sub), sub, size=10, color=MUTED, italic=True, lh=12.5)

    def msg(y, x1, x2, label, dashed=False):
        s.arrow([(x1, y), (x2, y)], dashed=dashed)
        mx, ty = (x1 + x2) / 2, y - 10 - 6.5 * (len(label) - 1)
        # A pale halo keeps the label legible where it crosses a lane border.
        wide = max(len(re.sub(r"\*\*|_\{|\}", "", ln)) for ln in label) * 5.5 + 10
        s.rect(mx - wide / 2, ty - 6.5 * len(label) - 1, wide, 13 * len(label) + 2, "#ffffff", "none", rx=3, sw=0)
        s.parts[-1] = s.parts[-1].replace('<rect ', '<rect fill-opacity="0.82" ', 1)
        s.text(mx, ty, label, size=10.5, lh=13)

    def step(y, x, lines, colors=WHITE, h=None):
        s.box(x, y, 132, h or 14 + 13 * len(lines), lines, colors, size=10)

    msg(ys[0], R, O - 2, ["**1** Specify task", "Φ, budget, category"])
    step(ys[1], O, ["**2** Route", "Thompson sampling on", "value density (human-", "in-the-loop by default)"])
    msg(ys[2], O, C - 2, ["**3** Escrow V", "encumber stake S"])
    s.arrow([(C, ys[3]), (T - 65, ys[3])])
    step(ys[3], T, ["**4** Execute", "meter tokens and gas,", "hash-chain every step"], TEE)
    step(ys[4], T, ["**5** Emit Verifiable", "Execution Receipt"], TEE)
    msg(ys[5], T - 10, C + 2, ["**5** Commit Merkle root,", "terminal hash,", "attestation quote"])
    msg(ys[5], T + 10, V - 2, ["receipt body:", "off-chain, encrypted"])
    step(ys[6], V, ["**6** Audit, prob. p(a,k)", "attestation, commitment,", "evidence ⊨ Φ ?"])
    msg(ys[7], V, C + 2, ["**7** Settle. Pass or no draw:", "release escrow. Fail: return", "escrow, slash on failure"])
    msg(ys[8], C, R + 2, ["**7/8** Receive result;", "may challenge within window W"])
    msg(ys[9], R, X - 2, ["**8** within W"], dashed=True)
    msg(ys[10], X, C + 2, ["**8** Challenge → Level 2 disclosure", "→ adjudication → clawback"], dashed=True)
    msg(ys[11], V, G - 2, ["**9** validated outcome", "+ metered cost"])
    msg(ys[12], X, G - 2, ["proven falsification", "→ probation"], dashed=True)
    msg(ys[13] - 14, G, O + 2, ["Update Beta(α,β) and Gamma(κ,τ) per (agent, category);", "posteriors feed routing"], dashed=True)
    s.arrow([(G, ys[13] + 24), (V + 2, ys[13] + 24)], dashed=True)
    s.text((G + V) / 2, ys[13] + 24 - 11, ["θ_{LCB} sets p"], size=10.5)
    return s


# --------------------------------------------------------------------------- Figure 2

def receipt() -> Svg:
    W, H = 960, 640
    s = Svg(W, H)
    s.rect(20, 14, 920, 352, "#fbfbfc", "#b4bac6", rx=12)
    s.text(480, 36, ["**Verifiable Execution Receipt**  (running example, §2.2)"], size=13)

    s.rect(40, 54, 880, 66, WHITE[0], TEE[1], rx=8, sw=1.4)
    s.text(480, 74, ["**Header**"], size=11.5)
    s.text(480, 98, [
        "task id · requester · agent · Φ as submitted · budget · runtime image measurement · time range",
        "**TEE attestation quote** over (image, root)",
    ], size=10.5, lh=14)

    # the whole chain is the full trajectory: outline it in the colour of Level 2
    s.rect(30, 130, 900, 108, "none", TEE[1], rx=10, sw=1.4, dash="6 4")
    s.text(480, 146, ["**Hash-chained step sequence**    h_{i} = H( h_{i−1} ‖ s_{i} )"], size=11.5)
    steps = [
        ("s_{1} model call", "in/out digests · cost", False),
        ("s_{2} read refund.py", "digest · cost", False),
        ("s_{3} run tests", "**exit 1** · cost", False),
        ("s_{4} write refund.py", "hash before/after · cost", True),
        ("s_{5} run tests", "**exit 0** · cost", True),
        ("s_{6} diff digest", "paths ⊆ payments/", True),
    ]
    bx = [40 + 150 * i for i in range(6)]
    for i, (a_, b_, ev) in enumerate(steps):
        c = EVID if ev else WHITE
        s.rect(bx[i], 162, 130, 54, c[0], c[1], rx=7, sw=1.4 if ev else 1.1)
        s.text(bx[i] + 65, 181, [a_], size=10.5)
        s.text(bx[i] + 65, 201, [b_], size=10, color=MUTED)
        if i < 5:
            s.arrow([(bx[i] + 130, 189), (bx[i + 1] - 1, 189)])
    s.text(130, 230, ["all six steps = the full trajectory (Level 2)"], size=9.5, color=TEE[1], italic=True)
    s.text(590, 230, ["amber = outcome-bearing"], size=9.5, color=EVID[1], italic=True)

    # one box per level's material, coloured like its level
    s.box(110, 314, 140, 70, ["**Meter**", "tokens by model · tool", "calls · wall-clock · gas;", "reconcilable per step"], CHAIN, size=10)
    s.box(260, 314, 130, 70, ["**root**", "MerkleRoot(s_{1}…s_{6})", "terminal hash h_{n}"], CHAIN, size=10)
    s.box(480, 314, 270, 90, ["**Evidence set** (outcome-bearing subset)", "s_{4} before/after hashes", "s_{5} exit 0 · s_{6} diff digest", "three facts establish Φ"], EVID, size=10.5)

    # amber steps feed the evidence set: one elbow, label beside it
    s.arrow([(bx[4] + 65, 216), (bx[4] + 65, 314), (615, 314)], dashed=True, color=EVID[1])
    s.text(bx[4] + 73, 270, ["marked as", "outcome-bearing"], size=9.5, color=EVID[1], italic=True, anchor="start", lh=12)

    # levels
    LY, LH = 430, 100
    lv = [
        (165, CHAIN, ["**Level 0 — settlement**", "on-chain: root, h_{n}, attestation, pointer", "plus meter totals and the verdict on Φ", "what the reputation engine consumes"]),
        (480, EVID, ["**Level 1 — audit** (probability p)", "evidence set plus Merkle paths to the root", "c_{audit} grows with evidence volume,", "not with trajectory length"]),
        (795, TEE, ["**Level 2 — challenge** (bonded)", "full trajectory; any step verifiable", "against the same root", "history cannot be revised after commitment"]),
    ]
    for x, col, lines in lv:
        s.rect(x - 135, LY, 270, LH, col[0], col[1], rx=9, sw=1.4)
        s.text(x, LY + LH / 2, lines, size=10.5, lh=15.5)
    s.arrow([(110, 349), (110, LY)], color=CHAIN[1])
    s.arrow([(260, 349), (260, LY)], color=CHAIN[1])
    s.arrow([(480, 359), (480, LY)], color=EVID[1])
    s.arrow([(860, 238), (860, LY)], color=TEE[1])

    # escalation, drawn under the boxes so the labels have room
    by = LY + LH
    s.arrow([(165, by), (165, by + 26), (450, by + 26), (450, by + 2)])
    s.text(307, by + 42, ["audit drawn"], size=10, color=MUTED, italic=True)
    s.arrow([(510, by), (510, by + 26), (795, by + 26), (795, by + 2)])
    s.text(652, by + 42, ["disputed"], size=10, color=MUTED, italic=True)

    s.text(480, H - 22, ["Illustrative: the running example of §2.2. Nothing in this figure is measured."], size=10, color=MUTED, italic=True)
    return s


def write(name: str, svg: Svg) -> None:
    path = HERE / f"{name}.svg"
    path.write_text(svg.render(), encoding="utf-8")
    print("wrote", path.name)
    magick = shutil.which("magick")
    if magick is None:
        print("  magick not found; skipping PNG")
        return
    # density 192 on a 96-dpi SVG gives a 2x raster, sharp at page width.
    subprocess.run(
        [magick, "-background", "white", "-density", "192", str(path), "-flatten", str(HERE / f"{name}.png")],
        check=True,
    )
    print("wrote", f"{name}.png")


if __name__ == "__main__":
    write("fig_lifecycle", lifecycle())
    write("fig_receipt", receipt())

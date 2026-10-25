"""HTML for the interactive parts of the research site.

The paper's Markdown is never changed. The build injects each explorable at the end of the section it
belongs to, and the browser scripts in site/js/ bring it to life. Without JavaScript each explorable
shows a short note, and the paper reads the same.
"""
import hashlib
import html
import math
import re

WPM = 230


# ---------------------------------------------------------------- finding sections in rendered HTML

def find_span(doc: str, section_id: str):
    """Return (start, end) of the <section id=...> element, counting nested sections."""
    m = re.search(r'<section id="%s"[^>]*>' % re.escape(section_id), doc)
    if not m:
        return None
    depth = 0
    for t in re.finditer(r"<section\b|</section>", doc[m.start():]):
        depth += -1 if t.group(0).startswith("</") else 1
        if depth == 0:
            return m.start(), m.start() + t.end()
    return None


def inject_at_end(doc: str, section_id: str, snippet: str) -> str:
    span = find_span(doc, section_id)
    if span is None:
        raise SystemExit(f"explorable target section not found: {section_id}")
    end = span[1] - len("</section>")
    return doc[:end] + "\n" + snippet + "\n" + doc[end:]


def replace_in_section(doc: str, section_id: str, old: str, new: str) -> str:
    span = find_span(doc, section_id)
    if span is None:
        raise SystemExit(f"target section not found: {section_id}")
    chunk = doc[span[0]:span[1]]
    if old not in chunk:
        raise SystemExit(f"text to replace not found in section {section_id}: {old[:60]}")
    return doc[:span[0]] + chunk.replace(old, new, 1) + doc[span[1]:]


# ---------------------------------------------------------------- explorables

def explorable(wid: str, title: str, lede: str, mount: str, foot: str, fallback: str) -> str:
    return f"""<section class="explorable" id="explore-{wid}" aria-labelledby="explore-{wid}-t">
<p class="ex-tag">Interactive</p>
<h3 id="explore-{wid}-t">{html.escape(title)}</h3>
<p class="ex-lede">{html.escape(lede)}</p>
{mount}
<noscript><p class="ex-foot">{html.escape(fallback)}</p></noscript>
<p class="ex-foot">{html.escape(foot)}</p>
</section>"""


EXPLORABLES = {
    "receipt": dict(
        section="structure",
        title="Break a receipt",
        lede="Edit a step, delete one, or swap two. The verifier checks the record against the commitment, using real SHA-256 in your browser.",
        mount='<div data-widget="receipt"></div>',
        foot="Interactive model of section 6.2. The running example and its costs are illustrative, and nothing here is measured.",
        fallback="This explorable needs JavaScript. It lets you change a receipt's steps and watch the hash chain stop verifying.",
    ),
    "audit": dict(
        section="worked-illustration",
        title="How much stake buys how little auditing",
        lede="Slide the stake, or click the chart. The curves are the paper's own deterrence rule, so the audit rate you see is the one that makes forging a receipt unprofitable.",
        mount='<div data-widget="audit"></div>',
        foot="Interactive model of sections 7.2 and 7.5, with the paper's example of a $2 task, $1 of work, and a 0.95 success rate. Model arithmetic, not a measurement.",
        fallback="This explorable needs JavaScript. See the calculator page for the same arithmetic.",
    ),
    "density": dict(
        section="what-cost-adjustment-changes",
        title="Who should get the work?",
        lede="Two agents, ranked two ways. Change their success rates and costs and watch the order flip.",
        mount='<div data-widget="density"></div>',
        foot="Interactive model of sections 8.4 and 8.8. Value density is a ratio of expectations. The starting numbers are the paper's illustration, not measurements.",
        fallback="This explorable needs JavaScript. The table above shows the paper's two-agent example.",
    ),
    "routing": dict(
        section="policy-thompson-sampling-over-value-density",
        title="Ranking is not a policy",
        lede="Four agents, two ways of routing work to them, run for real in your browser. One agent is better than the rest but has no track record yet.",
        mount='<div data-widget="routing"></div>',
        foot="A simulation of sections 9.2 and 9.3 under stated assumptions. Nothing here is measured, and a different setup would give different numbers.",
        fallback="This explorable needs JavaScript. It simulates ranking against Thompson sampling.",
    ),
}


def explorable_html(key: str) -> str:
    e = EXPLORABLES[key]
    return explorable(key, e["title"], e["lede"], e["mount"], e["foot"], e["fallback"])


def inject_paper_widgets(body: str) -> str:
    for key, e in EXPLORABLES.items():
        body = inject_at_end(body, e["section"], explorable_html(key))
    return body


# ---------------------------------------------------------------- chapters, reading time

def chapters(body: str):
    """[(id, number or '', title, minutes)] for the top-level sections of the paper body."""
    out = []
    for m in re.finditer(r'<section id="([^"]+)" class="level2">\s*<h2[^>]*>(.*?)</h2>', body, re.S):
        sid = m.group(1)
        span = find_span(body, sid)
        words = len(re.sub(r"<[^>]+>", " ", body[span[0]:span[1]]).split()) if span else 0
        heading = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        num = re.match(r"^(\d+)\.\s*(.*)$", heading)
        out.append((sid, num.group(1) if num else "", num.group(2) if num else heading, max(1, math.ceil(words / WPM))))
    return out


def chapter_strip(chaps, paper_url: str = "paper/") -> str:
    tiles = []
    for sid, n, title, mins in chaps:
        tiles.append(
            f'<a class="chap" data-id="{html.escape(sid)}" href="{paper_url}#{html.escape(sid)}">'
            f'<span class="chap-n">{html.escape(n) if n else "&nbsp;"}</span>'
            f'<span class="chap-t">{html.escape(title)}</span>'
            f'<span class="chap-m">{mins} min</span></a>'
        )
    total = sum(c[3] for c in chaps)
    return (
        '<section class="chaps" aria-labelledby="chaps-h">'
        '<div class="chaps-head"><h2 id="chaps-h">The paper, by chapter</h2>'
        f'<p class="chaps-progress">About {total} minutes in all</p></div>'
        f'<div class="chaps-grid">{"".join(tiles)}</div></section>'
    )


# ---------------------------------------------------------------- hero

def hash_texture(lines: int = 16) -> str:
    """Deterministic hex lines for the background texture. They are decoration, not data."""
    rows = []
    for i in range(lines):
        h = hashlib.sha256(f"mergit-research-{i}".encode()).hexdigest()
        rows.append(h + hashlib.sha256(h.encode()).hexdigest())
    return "\n".join(f"<span>{r}</span>" for r in rows)


def hero_html() -> str:
    return f"""<section class="hero" aria-labelledby="hero-h">
<div class="hero-hashes" aria-hidden="true">{hash_texture()}</div>
<div class="hero-in">
<p class="kind">Mergit Research</p>
<h1 id="hero-h" class="hero-title">Pay for<br>what you got.</h1>
<p class="hero-lede">Agent platforms bill for the attempt. Mergit settles on the outcome, backed by a record anyone can check. The receipt below is such a record. Try to change it.</p>
<p class="hero-ctas"><a class="btn primary" href="paper/">Read the paper</a><a class="btn" href="calculator/">Open the calculator</a></p>
</div>
<div class="hero-stage">
<div class="hero-stage-bar"><span class="dot"></span><span>Verifiable Execution Receipt, section 6.2 of the paper</span></div>
<div data-widget="receipt-hero"></div>
<noscript><p class="ex-foot">This receipt is interactive and needs JavaScript.</p></noscript>
</div>
</section>"""


# ---------------------------------------------------------------- the live lifecycle figure

def live_lifecycle(body: str, svg_text: str) -> str:
    """Swap the static Figure 1 image in section 4.2 for the inline SVG, so scripts can address its steps."""
    span = find_span(body, "task-lifecycle")
    if span is None:
        raise SystemExit("section task-lifecycle not found")
    chunk = body[span[0]:span[1]]
    m = re.search(r'<img src="figures/fig_lifecycle\.png"[^>]*alt="([^"]*)"[^>]*>', chunk)
    if not m:
        raise SystemExit("Figure 1 image not found in section 4.2")
    label = m.group(1)
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg_text.strip())
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg, count=2)
    svg = svg.replace("<svg ", f'<svg class="live-fig" role="img" aria-label="{html.escape(label, quote=True)}" ', 1)
    return body[:span[0]] + chunk.replace(m.group(0), svg, 1) + body[span[1]:]

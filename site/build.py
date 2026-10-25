#!/usr/bin/env python3
"""Build the static research site into site/dist/.

Each Markdown document is rendered to HTML with pandoc; the figures and the PDF are copied
beside it; an index page lists everything. Run from anywhere:

    python3 site/build.py

Needs pandoc. Output is plain files, so any static host can serve site/dist/.
"""
import html
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = SITE / "dist"

REPO_URL = "https://github.com/mergit-io/mergit-research"

# slug, source, title, description
DOCS = [
    (
        "paper",
        "paper/draft-v1.md",
        "Pay for What You Got: Cost-Adjusted Reputation and Runtime-Attested Verification for Autonomous Agent Markets",
        "The full paper, draft 1 revision 5. Threat model, formal verification economics, security analysis and limitations.",
    ),
    (
        "whitepaper",
        "paper/whitepaper.md",
        "Mergit: Pay for What You Got",
        "The argument in about fifteen minutes, condensed from the full paper.",
    ),
    (
        "simulation",
        "sim/RESULTS.md",
        "Simulation of the audit and slashing mechanism",
        "The model-based simulation of paper section 7.7: setup, deviations tested and results.",
    ),
    (
        "sources",
        "paper/research.md",
        "Sources and verification log",
        "Every citation in the paper, what it is used for, and how it was checked.",
    ),
    (
        "design",
        "docs/superpowers/specs/2026-10-09-mergit-research-paper-design.md",
        "Design brief and locked decisions",
        "The seventeen decisions behind the design, with their rationale and costs.",
    ),
]

PDFS = {"paper": ("build/draft-v1-r5.pdf", "mergit-paper-r5.pdf", "PDF of the full paper")}

STATUS = (
    "Mergit is pre-implementation. Every figure in these documents is arithmetic on a stated model "
    "or the output of a model-based simulation. Nothing has been measured."
)


def run_pandoc(src: Path, out: Path, title: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    first = next((ln for ln in src.read_text(encoding="utf-8").splitlines() if ln.strip()), "")
    # A document without its own H1 gets the title as a visible heading instead.
    heading = [] if first.startswith("# ") else ["--metadata", f"title={title}"]
    cmd = [
        "pandoc", str(src),
        # Dollar signs in the text are prices ("$2"), not TeX math.
        "-f", "markdown-tex_math_dollars",
        "-t", "html5", "-s",
        "--toc", "--toc-depth=2",
        "--css", "../style.css",
        "-V", "document-css=false",
        "-V", "lang=en",
        # pagetitle sets <title> only; the documents carry their own H1.
        "--metadata", f"pagetitle={title}",
        "--resource-path", str(src.parent),
        *heading,
        "-H", str(SITE / "head.html"),
        "-B", str(SITE / "nav.html"),
        "-o", str(out),
    ]
    subprocess.run(cmd, check=True)


def index_html() -> str:
    items = []
    for slug, _src, title, blurb in DOCS:
        extra = ""
        if slug in PDFS and (ROOT / PDFS[slug][0]).exists():
            extra = f' <a class="pdf" href="{slug}/{PDFS[slug][1]}">{html.escape(PDFS[slug][2])}</a>'
        items.append(
            f'<li><a class="doc" href="{slug}/">{html.escape(title)}</a>'
            f"<p>{html.escape(blurb)}{extra}</p></li>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mergit Research</title>
<link rel="stylesheet" href="style.css">
</head>
<body class="index">
<main>
<h1>Mergit Research</h1>
<p class="lead">Pay for what you got. A trust and settlement layer for autonomous agent work.</p>
<p class="status">{html.escape(STATUS)}</p>
<ul class="docs">
{chr(10).join(items)}
</ul>
<p class="foot"><a href="{REPO_URL}">Source and history on GitHub</a></p>
</main>
</body>
</html>
"""


def main() -> int:
    if shutil.which("pandoc") is None:
        print("pandoc not found", file=sys.stderr)
        return 1
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copy(SITE / "style.css", DIST / "style.css")

    for slug, rel, title, _ in DOCS:
        src = ROOT / rel
        if not src.exists():
            print(f"missing source: {rel}", file=sys.stderr)
            return 1
        run_pandoc(src, DIST / slug / "index.html", title)
        print(f"built {slug}")

    figures = ROOT / "paper" / "figures"
    if figures.exists():
        dest = DIST / "paper" / "figures"
        dest.mkdir(parents=True)
        for f in figures.iterdir():
            if f.suffix in {".png", ".pdf"}:
                shutil.copy(f, dest / f.name)

    for slug, (rel, name, _) in PDFS.items():
        src = ROOT / rel
        if src.exists():
            shutil.copy(src, DIST / slug / name)

    (DIST / "index.html").write_text(index_html(), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"site written to {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

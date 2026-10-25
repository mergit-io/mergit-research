#!/usr/bin/env python3
"""Build the static research site into site/dist/.

Each Markdown document is rendered to HTML with pandoc and placed in a shared page shell (header,
contents rail, title block with a document fingerprint, footer). Figures, fonts, the PDF and the
calculator are copied beside it, and an index page lists everything.

    python3 site/build.py

Needs pandoc. Output is plain files, so any static host can serve site/dist/.
"""
import hashlib
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import widgets  # noqa: E402  (site/widgets.py)

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = SITE / "dist"

REPO_URL = "https://github.com/mergit-io/mergit-research"
SITE_URL = "https://research.mergit.site"
AUTHORS = ["Yash Virulkar"]
LICENCE = ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")

# slug, source, title, kind, description
DOCS = [
    (
        "paper",
        "paper/draft-v1.md",
        "Pay for What You Got: Cost-Adjusted Reputation and Runtime-Attested Verification for Autonomous Agent Markets",
        "Paper",
        "The full paper. Threat model, formal verification economics, security analysis and limitations.",
    ),
    (
        "whitepaper",
        "paper/whitepaper.md",
        "Mergit: Pay for What You Got",
        "Whitepaper",
        "The argument in about fifteen minutes, condensed from the full paper.",
    ),
    (
        "simulation",
        "sim/RESULTS.md",
        "Simulation of the audit and slashing mechanism",
        "Simulation",
        "The model-based simulation of paper section 7.7: setup, deviations tested and results.",
    ),
    (
        "sources",
        "paper/research.md",
        "Sources and verification log",
        "Sources",
        "Every citation in the paper, what it is used for, and how it was checked.",
    ),
    (
        "design",
        "docs/superpowers/specs/2026-10-09-mergit-research-paper-design.md",
        "Design brief and locked decisions",
        "Design brief",
        "The seventeen decisions behind the design, with their rationale and costs.",
    ),
]

TOOLS = [
    (
        "calculator",
        "Audit-rate calculator",
        "Interactive",
        "How often must a receipt be audited so that forging it does not pay? The paper's section 7 mechanism, with your own numbers.",
    ),
]

PDFS = {"paper": ("build/draft-v1-r5.pdf", "mergit-paper-r5.pdf", "PDF")}

# Facts about the current revision of the paper. Change these together with the paper's own
# revision line.
PAPER = {
    "slug": "paper",
    "version": "Draft 1, revision 5",
    "rev": "draft-1-r5",
    "date": "2026-10-24",
    "bibkey": "virulkar2026payforwhatyougot",
}

SUMMARY = (
    "Outcome-contingent payment for agent work cannot rest on re-execution, because agent tasks have "
    "side effects. Mergit attests execution instead, and ranks agents by verified quality per unit cost."
)
STATUS = (
    "Mergit is pre-implementation. Every figure in these documents is arithmetic on a stated model "
    "or the output of a model-based simulation. Nothing has been measured."
)


# --------------------------------------------------------------------------- helpers

def attr(text: str) -> str:
    return html.escape(text, quote=True)


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logo_svg() -> str:
    """The coloured Mergit symbol: the light-background variant on Porcelain, the dark-background one on Porcelain Night.
    Both are inlined (gradient ids made unique) and CSS shows the one that matches the theme."""
    out = []
    for name in ("light", "dark"):
        svg = (SITE / "brand" / f"symbol-{name}.svg").read_text(encoding="utf-8")
        svg = re.sub(r'role="img"><defs>', f'class="mark mark-{name}" aria-hidden="true" focusable="false"><defs>', svg, count=1)
        svg = re.sub(r"<title>[^<]*</title>", "", svg)
        svg = svg.replace("mgpt", f"mgpt-{name}").replace("mgpb", f"mgpb-{name}")
        out.append(svg)
    return "".join(out)


def social_meta(title: str, description: str, url: str) -> str:
    return "\n".join(
        [
            f'<meta name="description" content="{attr(description)}">',
            '<meta property="og:type" content="article">',
            '<meta property="og:site_name" content="Mergit Research">',
            f'<meta property="og:title" content="{attr(title)}">',
            f'<meta property="og:description" content="{attr(description)}">',
            f'<meta property="og:url" content="{attr(url)}">',
            '<meta name="twitter:card" content="summary">',
            f'<meta name="twitter:title" content="{attr(title)}">',
            f'<meta name="twitter:description" content="{attr(description)}">',
        ]
    )


def scholar_meta(title: str) -> str:
    """Google Scholar's inclusion tags. The PDF must sit in the same folder as the page."""
    date = PAPER["date"].replace("-", "/")
    tags = [("citation_title", title)]
    tags += [("citation_author", a) for a in AUTHORS]
    tags += [
        ("citation_publication_date", date),
        ("citation_online_date", date),
        ("citation_pdf_url", f"{SITE_URL}/{PAPER['slug']}/{PDFS[PAPER['slug']][1]}"),
        ("citation_abstract_html_url", f"{SITE_URL}/{PAPER['slug']}/"),
        ("citation_language", "en"),
    ]
    return "\n".join(f'<meta name="{n}" content="{attr(v)}">' for n, v in tags)


def bibtex(title: str) -> str:
    authors = " and ".join(f"{a.split()[-1]}, {' '.join(a.split()[:-1])}" for a in AUTHORS)
    return (
        f"@misc{{{PAPER['bibkey']},\n"
        f"  author = {{{authors}}},\n"
        f"  title  = {{{title}}},\n"
        f"  year   = {{{PAPER['date'][:4]}}},\n"
        f"  note   = {{{PAPER['version']}}},\n"
        f"  url    = {{{SITE_URL}/{PAPER['slug']}/}}\n"
        "}"
    )


# --------------------------------------------------------------------------- page shell

def head_html(title: str, description: str, url: str, root: str, extra: str = "") -> str:
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{html.escape(title)}</title>
{social_meta(title, description, url)}
{extra}
<link rel="icon" href="{root}brand/icon.svg" type="image/svg+xml">
<link rel="icon" href="{root}brand/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{root}brand/apple-touch-icon.png">
<link rel="preload" href="{root}fonts/onest-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}fonts/literata-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<script>try{{var t=localStorage.getItem("mergit-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
<link rel="stylesheet" href="{root}style.css">
<link rel="stylesheet" href="{root}explore.css">"""


THEME_BUTTON = (
    '<button type="button" class="theme" aria-label="Switch theme" title="Switch theme">'
    '<svg class="i-moon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a.6.6 0 0 0-.8-.7 9.5 9.5 0 1 0 12.2 12.2.6.6 0 0 0-.7-.8Z"/></svg>'
    '<svg class="i-sun" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="currentColor"/>'
    '<g stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6"/></g></svg>'
    "</button>"
)


def header_html(root: str, here: str = "", doc: bool = False) -> str:
    def link(label: str, href: str, key: str) -> str:
        cur = ' aria-current="page"' if key == here else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    pill = (
        '<div class="pill" aria-hidden="true"><span class="pill-title">Abstract</span>'
        '<span class="pill-sep"></span><span class="pill-time"></span>'
        '<span class="pill-sep"></span><span class="pill-count"></span></div>'
        if doc
        else ""
    )
    progress = '<div class="progress" aria-hidden="true"><i></i></div>' if doc else ""
    return f"""<header class="bar">
<div class="bar-in">
<a class="brand" href="{root or './'}">{logo_svg()}<span>Mergit Research</span></a>
{pill}
<nav aria-label="Site">
{link("Papers", root or "./", "index")}
{link("Calculator", root + "calculator/", "calculator")}
<a href="{REPO_URL}">GitHub</a>
{THEME_BUTTON}
</nav>
</div>
{progress}
</header>"""


def footer_html(root: str = "") -> str:
    return f"""<footer class="foot">
<div class="foot-in">
<p>Text and figures are licensed under <a href="{LICENCE[1]}">{LICENCE[0]}</a>. The Mergit name and logo are not.</p>
<p><a href="{REPO_URL}">Source and history</a>. Pre-implementation: nothing here has been measured.</p>
</div>
</footer>
<script src="{root}js/theme.js" defer></script>"""


# --------------------------------------------------------------------------- documents

def split_head(text: str, fallback_title: str):
    """Pull the title block (H1, author, subtitle, revision note) out of a paper-style document.

    Returns (title, subtitle, note_markdown, body_markdown). Documents that do not start with a
    title block keep their text and only lose a leading H1.
    """
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        return fallback_title, "", "", text
    title = lines[0][2:].strip()
    head_end = next((i for i, ln in enumerate(lines[:60]) if ln.strip() == "---"), None)
    if head_end is None:
        return title, "", "", "\n".join(lines[1:]).lstrip("\n")
    blocks = [b.strip() for b in re.split(r"\n\s*\n", "\n".join(lines[1:head_end])) if b.strip()]
    subtitle, notes = "", []
    for b in blocks:
        if b in AUTHORS or b.startswith("Licensed under"):
            continue
        if re.fullmatch(r"\*\*[^*\n]+\*\*", b) and "—" not in b:
            subtitle = b.strip("*")
            continue
        notes.append(b)
    return title, subtitle, "\n\n".join(notes), "\n".join(lines[head_end + 1:]).lstrip("\n")


def pandoc_fragment(md_path: Path, resource_dir: Path, toc_depth: int = 3) -> tuple[str, str]:
    """Render Markdown to (toc_html, body_html) through the one-line template."""
    out = subprocess.run(
        [
            "pandoc", str(md_path),
            # Dollar signs in the text are prices ("$2"), not TeX math.
            "-f", "markdown-tex_math_dollars",
            "-t", "html5", "--section-divs", "--wrap=none",
            "--toc", f"--toc-depth={toc_depth}",
            "--template", str(SITE / "mini.html"),
            "--resource-path", str(resource_dir),
        ],
        capture_output=True, text=True, check=True,
    ).stdout
    toc = out.split("<!--TOC-->", 1)[1].split("<!--BODY-->", 1)[0].strip()
    body = out.split("<!--BODY-->", 1)[1].split("<!--END-->", 1)[0].strip()
    return toc, body


def pandoc_inline(markdown: str) -> str:
    return subprocess.run(
        ["pandoc", "-f", "markdown-tex_math_dollars", "-t", "html5", "--wrap=none"],
        input=markdown, capture_output=True, text=True, check=True,
    ).stdout


def fingerprint_html(slug: str, rel: str, src: Path) -> str:
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--", rel))
    rows = []
    if slug == PAPER["slug"]:
        rows.append(("Version", html.escape(PAPER["version"])))
        rows.append(("Date", PAPER["date"]))
    rows.append(("Licence", f'<a href="{LICENCE[1]}">{LICENCE[0]}</a>'))
    if commit and not dirty:
        rows.append(("Source", f'<a href="{REPO_URL}/blob/{commit}/{attr(rel)}"><code>{html.escape(rel)}</code></a> at <code>{commit[:10]}</code>'))
    else:
        rows.append(("Source", f"<code>{html.escape(rel)}</code>, local build (not committed)"))
    rows.append(("SHA-256 of source", f'<code class="hash">{sha256(src)}</code>'))
    pdf_ok = slug in PDFS and (ROOT / PDFS[slug][0]).exists()
    if pdf_ok:
        digest = sha256(ROOT / PDFS[slug][0])
        rows.append((
            "SHA-256 of PDF",
            f'<code class="hash">{digest}</code> '
            f'<button type="button" class="check" data-url="{PDFS[slug][1]}" data-sha="{digest}">Check this PDF</button>'
            '<span class="check-out" role="status"></span>',
        ))
    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (
        '<section class="print" aria-label="Document fingerprint">'
        f"<dl>{dl}</dl>"
        '<p class="small">A checksum shows that your copy matches this build. It is not a signature, '
        "and it does not show who made the build.</p></section>"
    )


def cite_box(title: str) -> str:
    byline = ", ".join(AUTHORS)
    return f"""<aside class="cite" id="cite">
<h2>Cite this paper</h2>
<p>{html.escape(byline)}. <em>{html.escape(title)}.</em> Mergit Research, {html.escape(PAPER['version'].lower())}, {PAPER['date']}.
<a href="{SITE_URL}/{PAPER['slug']}/">{SITE_URL}/{PAPER['slug']}/</a></p>
<details><summary>BibTeX</summary><pre><code>{html.escape(bibtex(title))}</code></pre></details>
<p class="small">This is a draft and it changes. Cite the revision you read, and see
<a href="{REPO_URL}/commits/main/paper">the history on GitHub</a> for what changed between revisions.</p>
</aside>"""


PAGES: dict = {}


def build_document(slug: str, rel: str, fallback_title: str, kind: str) -> None:
    src = ROOT / rel
    text = src.read_text(encoding="utf-8")
    paper_style = slug in ("paper", "whitepaper")
    title, subtitle, note_md, body_md = split_head(text, fallback_title) if paper_style else (
        fallback_title, "", "", re.sub(r"\A# [^\n]*\n+", "", text)
    )

    with tempfile.TemporaryDirectory() as tmp:
        body_file = Path(tmp) / "body.md"
        body_file.write_text(body_md, encoding="utf-8")
        toc, body = pandoc_fragment(body_file, src.parent)

    note = ""
    if note_md:
        note = (
            '<details class="note"><summary>About this revision</summary>'
            f"{pandoc_inline(note_md)}</details>"
        )

    is_paper = slug == PAPER["slug"]
    actions = []
    if slug in PDFS and (ROOT / PDFS[slug][0]).exists():
        actions.append(f'<a class="btn primary" href="{PDFS[slug][1]}">Download PDF</a>')
    if is_paper:
        actions.append('<a class="btn" href="#cite">Cite</a>')
    actions.append(f'<a class="btn" href="{REPO_URL}/blob/main/{attr(rel)}">View source</a>')

    byline = ""
    if paper_style:
        byline = f'<p class="byline">{html.escape(", ".join(AUTHORS))}</p>'
    sub = f'<p class="subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
    long_title = " long" if len(title) > 70 else ""

    if is_paper:
        body = widgets.inject_paper_widgets(body)
        body = widgets.live_lifecycle(body, (ROOT / "paper" / "figures" / "fig_lifecycle.svg").read_text(encoding="utf-8"))
        PAGES["paper_body"] = body
    scripts = [
        "../js/common.js",
        *(
            ["../calculator/core.js", "../js/receipt.js", "../js/audit.js", "../js/density.js", "../js/routing.js", "../js/lifecycle.js"]
            if is_paper
            else []
        ),
        "../js/reading.js",
        "../toc.js",
    ]
    script_tags = "\n".join(f'<script src="{src}" defer></script>' for src in scripts)
    dock = (
        '<div class="dock" aria-label="Reading tools">'
        '<button type="button" data-act="focus" aria-pressed="false" title="Focus mode (f)">Focus</button>'
        '<button type="button" data-act="keys" title="Keyboard shortcuts (?)">Keys</button></div>'
    )

    extra = scholar_meta(title) if is_paper else ""
    head = head_html(f"{title} | Mergit Research", SUMMARY, f"{SITE_URL}/{slug}/", "../", extra)
    page = f"""<!doctype html>
<html lang="en">
<head>
{head}
</head>
<body class="doc doc-{slug}" data-slug="{slug}" data-rev="{PAPER["rev"]}">
<a class="skip" href="#content">Skip to the text</a>
{header_html("../", "", doc=True)}
<div class="shell">
<aside class="rail" aria-label="Contents">
<details class="toc" open><summary>Contents</summary>
{toc}
</details>
</aside>
<main class="paper">
<header class="titleblock">
<p class="kind">{html.escape(kind)}</p>
<h1 class="title{long_title}">{html.escape(title)}</h1>
{sub}
{byline}
<p class="actions">{"".join(actions)}</p>
{fingerprint_html(slug, rel, src)}
{note}
</header>
<article id="content">
{body}
</article>
{cite_box(title) if is_paper else ""}
</main>
</div>
{dock}
{footer_html("../")}
{script_tags}
</body>
</html>
"""
    out = DIST / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def build_tool(slug: str, title: str) -> None:
    """Copy a tool folder and wrap its page in the shared shell."""
    shutil.copytree(SITE / slug, DIST / slug, ignore=shutil.ignore_patterns("test.js"))
    path = DIST / slug / "index.html"
    page = path.read_text(encoding="utf-8")
    desc = next(t[3] for t in TOOLS if t[0] == slug)
    page = page.replace("<!--HEAD-->", head_html(f"{title} | Mergit Research", desc, f"{SITE_URL}/{slug}/", "../"))
    page = page.replace("<!--HEADER-->", header_html("../", slug))
    page = page.replace("<!--FOOTER-->", footer_html("../"))
    path.write_text(page, encoding="utf-8")


def index_html() -> str:
    rows = []
    for slug, title, kind, blurb in TOOLS:
        rows.append(
            f'<li><p class="kind">{html.escape(kind)}</p>'
            f'<a class="doc" href="{slug}/">{html.escape(title)}</a><p>{html.escape(blurb)}</p></li>'
        )
    for slug, _src, title, kind, blurb in DOCS:
        extra = ""
        if slug in PDFS and (ROOT / PDFS[slug][0]).exists():
            extra = f' <a class="pdf" href="{slug}/{PDFS[slug][1]}">PDF</a>'
        rows.append(
            f'<li><p class="kind">{html.escape(kind)}</p>'
            f'<a class="doc" href="{slug}/">{html.escape(title)}</a><p>{html.escape(blurb)}{extra}</p></li>'
        )
    head = head_html("Mergit Research", SUMMARY, SITE_URL + "/", "")
    chaps = widgets.chapters(PAGES.get("paper_body", ""))
    return f"""<!doctype html>
<html lang="en">
<head>
{head}
</head>
<body class="index" data-rev="{PAPER["rev"]}">
{header_html("", "index")}
<main>
{widgets.hero_html()}
<div class="home">
<p class="status">{html.escape(STATUS)}</p>
{widgets.chapter_strip(chaps) if chaps else ""}
<h2 class="home-h">Everything else</h2>
<ul class="docs">
{chr(10).join(rows)}
</ul>
</div>
</main>
{footer_html()}
<script src="js/common.js" defer></script>
<script src="js/receipt.js" defer></script>
<script src="js/home.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- main

def main() -> int:
    if shutil.which("pandoc") is None:
        print("pandoc not found", file=sys.stderr)
        return 1
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    for name in ("style.css", "explore.css", "toc.js"):
        shutil.copy(SITE / name, DIST / name)
    shutil.copytree(SITE / "js", DIST / "js")
    shutil.copytree(SITE / "fonts", DIST / "fonts")
    shutil.copytree(SITE / "brand", DIST / "brand")

    for slug, rel, title, kind, _ in DOCS:
        if not (ROOT / rel).exists():
            print(f"missing source: {rel}", file=sys.stderr)
            return 1
        build_document(slug, rel, title, kind)
        print(f"built {slug}")

    figures = ROOT / "paper" / "figures"
    if figures.exists():
        dest = DIST / "paper" / "figures"
        dest.mkdir(parents=True)
        for f in figures.iterdir():
            if f.suffix in {".png", ".pdf"}:
                shutil.copy(f, dest / f.name)

    for slug, (rel, name, _) in PDFS.items():
        if (ROOT / rel).exists():
            shutil.copy(ROOT / rel, DIST / slug / name)

    for slug, title, _kind, _blurb in TOOLS:
        build_tool(slug, title)
        print(f"built {slug}")

    (DIST / "index.html").write_text(index_html(), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    # Crawlers: allow everything, and list every page once.
    pages = [""] + [f"{d[0]}/" for d in DOCS] + [f"{t[0]}/" for t in TOOLS]
    urls = "\n".join(f"  <url><loc>{SITE_URL}/{p}</loc></url>" for p in pages)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"site written to {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

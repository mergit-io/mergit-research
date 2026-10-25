#!/usr/bin/env bash
# Rebuild build/draft-v1-r5.pdf from paper/draft-v1.md.
#
# Not tested by the assistant that wrote it: the environment it ran in had no TeX engine. The
# options below are a reasonable reconstruction. If the result differs from the previous PDF in
# fonts or layout, change them here and keep the script in step with what you actually run.
#
# Figures 1 and 2 are embedded (drawn by paper/figures/make_diagrams.py), so LaTeX numbers all
# figures itself and header.tex no longer touches the counter.
#
# Needs: pandoc and a LaTeX engine. On NixOS:
#   nix shell nixpkgs#pandoc nixpkgs#texliveSmall -c bash build/build-pdf.sh
set -euo pipefail
cd "$(dirname "$0")/.."

pandoc paper/draft-v1.md \
  -f markdown-tex_math_dollars \
  --resource-path=paper \
  --pdf-engine=xelatex \
  --include-in-header=build/header.tex \
  -V geometry:margin=1in \
  -V colorlinks=true \
  -o build/draft-v1-r5.pdf

echo "wrote build/draft-v1-r5.pdf"

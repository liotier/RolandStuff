#!/usr/bin/env bash
# Rebuild README.md from report/README.tmpl.md and the tables generated from
# results/ (and results/synthetic/, the synthetic validation's output).
#
#   bash report/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
python3 report/table.py results > "$tmp/table.md"
python3 report/blocks.py results results/synthetic > "$tmp/blocks.md"
python3 report/assemble.py report/README.tmpl.md "$tmp/table.md" "$tmp/blocks.md" README.md

#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# download_sources.sh
#
# Downloads the MVP corpus for Basketball Brain into api/data/raw/.
# Operator-only: run manually after verifying the URLs below.
#
# IMPORTANT — Verify URLs before running:
#   - NBB hosts spelregels under https://www.nbb.basketball.nl
#       Find the active 2025-2026 PDF link and substitute below.
#   - FIBA hosts rules under fiba.basketball
#       Find the latest "Official Basketball Rules" PDF link.
#   - Wikipedia URLs are stable and should not need updating.
#   - The te-jong-te-snel.pdf fallback path assumes basketball-brain and
#     vincent_brain are siblings under ClubVentureProjects/. If your layout
#     differs, copy that PDF into api/data/raw/ manually.
#
# Files downloaded here are gitignored — do NOT commit them. The manifest
# (api/data/raw/sources.json) is committed separately.
# -----------------------------------------------------------------------------

set -euo pipefail
cd "$(dirname "$0")/../api/data/raw"

# 1. NBB Reglementen 2025-2026 (publiek)
curl -fL -o nbb-spelregels-2025-2026.pdf \
  "https://www.nbb.basketball.nl/storage/files/spelregels-2025-2026.pdf"

# 2. NBB Talentontwikkeling-richtlijnen
curl -fL -o nbb-talentontwikkeling.pdf \
  "https://www.nbb.basketball.nl/storage/files/talentontwikkeling.pdf"

# 3. FIBA Official Basketball Rules 2024
curl -fL -o fiba-rules-2024.pdf \
  "https://www.fiba.basketball/documents/official-basketball-rules-2024.pdf"

# 4. Vincent's existing 'te jong te snel' copy from vincent_brain wiki
cp ../../../../vincent_brain/raw/te-jong-te-snel.pdf . 2>/dev/null \
  || echo "Note: te-jong-te-snel.pdf not auto-copied; copy manually from vincent_brain wiki"

# 5. John Wooden Pyramid of Success — Wikipedia article
curl -fL -o wooden-pyramid-of-success.html \
  "https://en.wikipedia.org/wiki/Pyramid_of_Success"

# 6. NL Wikipedia basketbal
curl -fL -o wiki-nl-basketbal.html \
  "https://nl.wikipedia.org/wiki/Basketbal"

# 7. Wiki: 24-second clock / shot clock
curl -fL -o wiki-24-second-clock.html \
  "https://en.wikipedia.org/wiki/Shot_clock"

echo "Done. Files in $(pwd):"
ls -la

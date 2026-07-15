#!/bin/bash
# Build a shippable release zip of the Song SRT Generator (Apple Silicon).
#
#   ./make_release.sh 3.1.0            → lite zip (models download on install)
#   ./make_release.sh 3.1.0 --full     → full zip (models baked in, works offline)
#
# Output lands in dist-release/. Downloads (uv, ffmpeg) are cached in
# release-assets/ so rebuilding is fast.
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo dev)}"
VARIANT="lite"
[ "${2:-}" = "--full" ] && VARIANT="full"

NAME="Song-SRT-Generator-${VERSION}-mac-${VARIANT}"
STAGE="dist-release/${NAME}"
ASSETS="release-assets"

echo "==> Building ${NAME}"

# 1. Fresh frontend build
echo "==> Building frontend"
(cd frontend && npm run build >/dev/null)

# 2. Fetch bundled tools (cached across builds)
mkdir -p "$ASSETS"
if [ ! -x "$ASSETS/uv" ]; then
  echo "==> Downloading uv"
  curl -sL "https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz" \
    | tar -xz -C "$ASSETS" --strip-components 1 "uv-aarch64-apple-darwin/uv"
fi
for tool in ffmpeg ffprobe; do
  if [ ! -x "$ASSETS/$tool" ]; then
    echo "==> Downloading $tool (static, arm64)"
    curl -sL -o "$ASSETS/$tool.zip" \
      "https://ffmpeg.martin-riedl.de/redirect/latest/macos/arm64/release/$tool.zip"
    unzip -oq "$ASSETS/$tool.zip" "$tool" -d "$ASSETS"
    rm "$ASSETS/$tool.zip"
  fi
done
chmod +x "$ASSETS/uv" "$ASSETS/ffmpeg" "$ASSETS/ffprobe"

# 3. Stage the app
echo "==> Staging files"
rm -rf "$STAGE"
mkdir -p "$STAGE/bin" "$STAGE/frontend"
cp app.py pipeline.py config.py warmup.py requirements.txt README.md DECISIONS.md "$STAGE/"
cp -R sample "$STAGE/sample"
cp -R frontend/dist "$STAGE/frontend/dist"
cp "$ASSETS/uv" "$ASSETS/ffmpeg" "$ASSETS/ffprobe" "$STAGE/bin/"
cp install.command "$STAGE/Install.command"
cp start.command "$STAGE/Start.command"
chmod +x "$STAGE/Install.command" "$STAGE/Start.command" "$STAGE"/bin/*

cat > "$STAGE/READ ME FIRST.txt" <<'EOF'
SONG SRT GENERATOR — HOW TO INSTALL (Apple Silicon Macs)

STEP 1 — install (one time, 3 small moves):
   a. Open Terminal: press Cmd+Space, type "terminal", press Enter.
   b. In the Terminal window type exactly:   bash
      then a SPACE, then DRAG the file "Install.command" from this
      folder into the Terminal window (its path appears by itself).
   c. Press Enter. Wait for the window to say PASS.
      (First time takes 5–20 minutes — it downloads the AI models.
      Leave the window alone until PASS.)

STEP 2 — use it:
   Double-click "Start.command". Your browser opens with the app.

That's it. From tomorrow on, only step 2.

WHY THE WEIRD TERMINAL STEP? If you double-click Install.command instead,
macOS shows "Apple could not verify…" and blocks it — that's just Apple's
warning for any app not from the App Store. Running it through Terminal
skips that. (Alternative if you already double-clicked and got blocked:
click Done — NOT Move to Bin — then System Settings > Privacy & Security,
scroll down, click "Open Anyway", and it will run.)

Everything installs inside this folder only. To uninstall, delete the folder.
If the installer says anything other than PASS, send Aman a screenshot.
EOF

# 4. Full variant: bake the models in
if [ "$VARIANT" = "full" ]; then
  echo "==> Baking models into the zip (full variant)"
  if [ ! -d models ]; then
    echo "!! models/ not found — run warmup.py once first"; exit 1
  fi
  cp -R models "$STAGE/models"
fi

# 5. Zip it
echo "==> Zipping"
(cd dist-release && rm -f "${NAME}.zip" && zip -rq "${NAME}.zip" "$NAME")
SIZE=$(du -h "dist-release/${NAME}.zip" | cut -f1)
echo ""
echo "✓ dist-release/${NAME}.zip  (${SIZE})"
echo "  Share the zip. Teammate steps: unzip → right-click Install.command → Start.command"

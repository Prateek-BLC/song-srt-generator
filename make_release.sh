#!/bin/bash
# Build a shippable release zip of the Song SRT Generator.
#
#   ./make_release.sh 3.2.0                  → Mac (Apple Silicon) lite zip
#   ./make_release.sh 3.2.0 --full           → Mac zip with models baked in
#   ./make_release.sh 3.2.0 --windows        → Windows (x64) lite zip
#
# Output lands in dist-release/. Downloads (uv, ffmpeg) are cached in
# release-assets/ so rebuilding is fast.
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo dev)}"
VARIANT="lite"
PLATFORM="mac"
for arg in "${@:2}"; do
  [ "$arg" = "--full" ] && VARIANT="full"
  [ "$arg" = "--windows" ] && PLATFORM="win"
done

NAME="Song-SRT-Generator-${VERSION}-${PLATFORM}-${VARIANT}"
# Windows: short inner folder name — deep paths inside .venv/models can hit
# Windows' 260-character path limit if the user unzips somewhere nested.
FOLDER="$NAME"
[ "$PLATFORM" = "win" ] && FOLDER="Song-SRT-Generator"
STAGE="dist-release/${FOLDER}"
ASSETS="release-assets"

echo "==> Building ${NAME}"

# 1. Fresh frontend build
echo "==> Building frontend"
(cd frontend && npm run build >/dev/null)

# 2. Fetch bundled tools (cached across builds)
mkdir -p "$ASSETS"
if [ "$PLATFORM" = "mac" ]; then
  if [ ! -x "$ASSETS/uv" ]; then
    echo "==> Downloading uv (mac arm64)"
    curl -sL "https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz" \
      | tar -xz -C "$ASSETS" --strip-components 1 "uv-aarch64-apple-darwin/uv"
  fi
  for tool in ffmpeg ffprobe; do
    if [ ! -x "$ASSETS/$tool" ]; then
      echo "==> Downloading $tool (mac arm64, static)"
      curl -sL -o "$ASSETS/$tool.zip" \
        "https://ffmpeg.martin-riedl.de/redirect/latest/macos/arm64/release/$tool.zip"
      unzip -oq "$ASSETS/$tool.zip" "$tool" -d "$ASSETS"
      rm "$ASSETS/$tool.zip"
    fi
  done
  chmod +x "$ASSETS/uv" "$ASSETS/ffmpeg" "$ASSETS/ffprobe"
else
  if [ ! -f "$ASSETS/uv.exe" ]; then
    echo "==> Downloading uv (windows x64)"
    curl -sL -o "$ASSETS/uv-win.zip" \
      "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
    unzip -joq "$ASSETS/uv-win.zip" "*uv.exe" -d "$ASSETS" || unzip -joq "$ASSETS/uv-win.zip" "uv.exe" -d "$ASSETS"
    rm "$ASSETS/uv-win.zip"
  fi
  if [ ! -f "$ASSETS/ffmpeg.exe" ] || [ ! -f "$ASSETS/ffprobe.exe" ]; then
    echo "==> Downloading ffmpeg (windows x64, gyan.dev essentials)"
    curl -sL -o "$ASSETS/ffmpeg-win.zip" \
      "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    unzip -joq "$ASSETS/ffmpeg-win.zip" "*/bin/ffmpeg.exe" "*/bin/ffprobe.exe" -d "$ASSETS"
    rm "$ASSETS/ffmpeg-win.zip"
  fi
fi

# 3. Stage the app
echo "==> Staging files"
rm -rf "$STAGE"
mkdir -p "$STAGE/bin" "$STAGE/frontend"
cp app.py pipeline.py config.py warmup.py README.md DECISIONS.md "$STAGE/"
cp -R sample "$STAGE/sample"
cp -R frontend/dist "$STAGE/frontend/dist"

if [ "$PLATFORM" = "mac" ]; then
  cp requirements.txt "$STAGE/"
  cp "$ASSETS/uv" "$ASSETS/ffmpeg" "$ASSETS/ffprobe" "$STAGE/bin/"
  cp install.command "$STAGE/Install.command"
  cp start.command "$STAGE/Start.command"
  chmod +x "$STAGE/Install.command" "$STAGE/Start.command" "$STAGE"/bin/*
else
  cp requirements-windows.txt "$STAGE/"
  cp "$ASSETS/uv.exe" "$ASSETS/ffmpeg.exe" "$ASSETS/ffprobe.exe" "$STAGE/bin/"
  cp install.bat "$STAGE/Install.bat"
  cp start.bat "$STAGE/Start.bat"
  # Guard: .bat files MUST be CRLF + ASCII or cmd.exe breaks silently.
  for bat in "$STAGE/Install.bat" "$STAGE/Start.bat"; do
    if ! file "$bat" | grep -q "CRLF"; then
      echo "!! $bat is not CRLF — refusing to ship a broken batch file"; exit 1
    fi
    if ! file "$bat" | grep -q "ASCII"; then
      echo "!! $bat contains non-ASCII characters — refusing to ship"; exit 1
    fi
  done
  # Windows uses the cross-platform CPU separation engine.
  sed -i '' 's/^SEPARATOR_ENGINE = .*/SEPARATOR_ENGINE = "cpu"/' "$STAGE/config.py"
fi

if [ "$PLATFORM" = "mac" ]; then
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
else
cat > "$STAGE/READ ME FIRST.txt" <<'EOF'
SONG SRT GENERATOR - HOW TO INSTALL (Windows, 64-bit)

STEP 0 - put this whole folder somewhere simple first:
   your Desktop or Documents. (Not buried inside many nested folders -
   Windows has a path-length limit that can break the install.)

STEP 1 - install (one time):
   Double-click "Install.bat".
   If Windows shows a blue "Windows protected your PC" box:
   click "More info", then "Run anyway". (That's just Windows'
   warning for any app not from the Microsoft Store.)
   Wait for the window to say PASS.
   (First time takes 10-30 minutes - it downloads the AI models.
   Leave the window alone until PASS.)

STEP 2 - use it:
   Double-click "Start.bat". Your browser opens with the app.

That's it. From tomorrow on, only step 2.

NOTE: on Windows a 3-minute song takes roughly 2-5 minutes to process
(Macs have a special AI chip for this; Windows PCs do it the slow way).

Everything installs inside this folder only. To uninstall, delete the folder.
If the installer says anything other than PASS, send Aman a photo of the window.
EOF
# Windows text files need CRLF line endings.
perl -pi -e 's/\n/\r\n/' "$STAGE/READ ME FIRST.txt"
fi

# 4. Full variant (mac only): bake the models in
if [ "$VARIANT" = "full" ] && [ "$PLATFORM" = "mac" ]; then
  echo "==> Baking models into the zip (full variant)"
  if [ ! -d models ]; then
    echo "!! models/ not found — run warmup.py once first"; exit 1
  fi
  cp -R models "$STAGE/models"
fi

# 5. Zip it
echo "==> Zipping"
(cd dist-release && rm -f "${NAME}.zip" && zip -rq "${NAME}.zip" "$FOLDER")
SIZE=$(du -h "dist-release/${NAME}.zip" | cut -f1)
echo ""
echo "✓ dist-release/${NAME}.zip  (${SIZE})"
if [ "$PLATFORM" = "mac" ]; then
  echo "  Teammate steps: unzip → Terminal: bash Install.command → Start.command"
else
  echo "  Teammate steps: unzip → Install.bat (Run anyway) → Start.bat"
  echo "  NOTE: untested on real Windows hardware until a teammate runs it."
fi

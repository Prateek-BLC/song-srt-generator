#!/bin/bash
# Build a shippable release zip of the Song SRT Generator.
#
#   ./make_release.sh 3.6                    → Song-SRT-Generator-3.6-mac.zip (the .app, Apple Silicon)
#   ./make_release.sh 3.6 --full             → ...-mac-full.zip, the .app with models baked in
#   ./make_release.sh 3.6 --windows          → ...-win-lite.zip (x64 folder + Install.bat)
#
# The version must match the VERSION file (the single source of version numbers);
# leave it out to use VERSION as is. Output lands in dist-release/. Downloads
# (uv, ffmpeg) are cached in release-assets/ so rebuilding is fast.
set -euo pipefail
cd "$(dirname "$0")"

FILE_VERSION="$(tr -d '[:space:]' < VERSION)"
VERSION="$FILE_VERSION"
if [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; then
  VERSION="$1"
  shift
fi
if [ "$VERSION" != "$FILE_VERSION" ]; then
  echo "!! VERSION file says ${FILE_VERSION}, not ${VERSION}. Edit VERSION first (it's the single source)."
  exit 1
fi
VARIANT="lite"
PLATFORM="mac"
for arg in "$@"; do
  [ "$arg" = "--full" ] && VARIANT="full"
  [ "$arg" = "--windows" ] && PLATFORM="win"
done

NAME="Song-SRT-Generator-${VERSION}-${PLATFORM}-${VARIANT}"
[ "$PLATFORM" = "mac" ] && [ "$VARIANT" = "lite" ] && NAME="Song-SRT-Generator-${VERSION}-mac"
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

if [ "$PLATFORM" = "mac" ]; then
  # Read-only .app bundle. All writable state (Python, venv, models, jobs/) goes to
  # ~/Library/Application Support/Song SRT Generator/ on first launch (see macapp/launcher).
  APP="$STAGE/Song SRT Generator.app"
  RES="$APP/Contents/Resources"
  mkdir -p "$APP/Contents/MacOS" "$RES/bin" "$RES/app/frontend"
  sed "s/__VERSION__/${VERSION}/g" macapp/Info.plist > "$APP/Contents/Info.plist"
  printf 'APPL????' > "$APP/Contents/PkgInfo"
  cp macapp/launcher "$APP/Contents/MacOS/launcher"
  cp macapp/launcher.py macapp/progress.html macapp/AppIcon.icns "$RES/"
  cp "$ASSETS/uv" "$ASSETS/ffmpeg" "$ASSETS/ffprobe" "$RES/bin/"
  cp app.py pipeline.py config.py warmup.py VERSION requirements.txt README.md DECISIONS.md "$RES/app/"
  cp -R sample "$RES/app/sample"
  cp -R frontend/dist "$RES/app/frontend/dist"
  chmod +x "$APP/Contents/MacOS/launcher" "$RES"/bin/*
  if [ "$VARIANT" = "full" ]; then
    echo "==> Baking models into the app (full variant)"
    if [ ! -d models ]; then
      echo "!! models/ not found — run warmup.py once first"; exit 1
    fi
    cp -R models "$RES/models"
  fi
cat > "$STAGE/READ ME FIRST.txt" <<'EOF'
SONG SRT GENERATOR — HOW TO INSTALL (Apple Silicon Macs: M1, M2, M3, M4)

1. Drag "Song SRT Generator" into your Applications folder.

2. Double-click it. macOS says "Apple could not verify…" — that's its
   warning for any app not from the App Store. Click Done (NOT Move to Bin).
   Then open System Settings > Privacy & Security, scroll down, click
   "Open Anyway" next to Song SRT Generator, and confirm.
   You only do this once per version.

3. The first launch sets everything up (5–20 minutes, needs internet once:
   about 2.5 GB of Python packages and AI models). Leave the window open
   until the app appears.

Updates: the app shows a banner when a new version is out. Download the new
zip, replace the app in Applications, and do step 2 again. Your models are
kept, so an update takes about a minute.

Uninstall: delete the app and the folder
~/Library/Application Support/Song SRT Generator
If the setup window shows an error, click "Show the log" and send Aman the file.
EOF
else
  mkdir -p "$STAGE/bin" "$STAGE/frontend"
  cp app.py pipeline.py config.py warmup.py VERSION README.md DECISIONS.md "$STAGE/"
  cp -R sample "$STAGE/sample"
  cp -R frontend/dist "$STAGE/frontend/dist"
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

# 4. Zip it
echo "==> Zipping"
if [ "$PLATFORM" = "mac" ]; then
  # The zip holds the .app itself (plus the read-me), not a wrapping folder.
  (cd "$STAGE" && rm -f "../${NAME}.zip" && zip -rqy "../${NAME}.zip" "Song SRT Generator.app" "READ ME FIRST.txt")
else
  (cd dist-release && rm -f "${NAME}.zip" && zip -rq "${NAME}.zip" "$FOLDER")
fi
SIZE=$(du -h "dist-release/${NAME}.zip" | cut -f1)
echo ""
echo "✓ dist-release/${NAME}.zip  (${SIZE})"
if [ "$PLATFORM" = "mac" ]; then
  echo "  Teammate steps: unzip → drag to Applications → open → Open Anyway (Privacy & Security) → wait for setup"
else
  echo "  Teammate steps: unzip → Install.bat (Run anyway) → Start.bat"
  echo "  NOTE: untested on real Windows hardware until a teammate runs it."
fi

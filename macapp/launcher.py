"""Song SRT Generator — macOS app shell (Contents/Resources/launcher.py).

Started by Contents/MacOS/launcher with SRT_APP_DIR (the read-only app code inside
the bundle) and SRT_DATA_DIR (~/Library/Application Support/Song SRT Generator).

1. One instance only: a second launch brings the running window forward and exits.
2. First launch, or the first launch after an update: install the pinned packages
   and run warmup.py to PASS, with progress shown in the window. Models live in the
   data folder, so updates never download them again.
3. Run the FastAPI server on a thread and load the UI into the same native window.
   Closing the window quits the app, which stops the server.
"""

import fcntl
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import webview

APP_DIR = Path(os.environ["SRT_APP_DIR"])
SUPPORT = Path(os.environ["SRT_DATA_DIR"])
RESOURCES = Path(__file__).parent
STAMP = SUPPORT / "installed.json"
LOG = SUPPORT / "install.log"
UV = str(SUPPORT / "bin" / "uv")

sys.path.insert(0, str(APP_DIR))
import config  # noqa: E402

VERSION = (APP_DIR / "VERSION").read_text(encoding="utf-8").strip()
LOCAL_HOST = "127.0.0.1" if config.HOST in ("0.0.0.0", "") else config.HOST
URL = f"http://{LOCAL_HOST}:{config.PORT}"


def claim_single_instance():
    """Hold an exclusive lock for the app's lifetime; if another copy holds it, focus that one."""
    lock = open(SUPPORT / "app.lock", "a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.seek(0)
        pid = lock.read().strip()
        try:
            from AppKit import NSApplicationActivateAllWindows, NSRunningApplication
            other = NSRunningApplication.runningApplicationWithProcessIdentifier_(int(pid))
            if other:
                other.activateWithOptions_(NSApplicationActivateAllWindows)
        except Exception:
            pass
        try:  # also un-minimizes the window once the UI is running
            urllib.request.urlopen(urllib.request.Request(URL + "/api/focus", method="POST"), timeout=2)
        except Exception:
            pass
        sys.exit(0)
    lock.seek(0)
    lock.truncate()
    lock.write(str(os.getpid()))
    lock.flush()
    return lock


def requirements_hash() -> str:
    return hashlib.sha256((APP_DIR / "requirements.txt").read_bytes()).hexdigest()


def needs_setup() -> bool:
    try:
        stamp = json.loads(STAMP.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return stamp.get("version") != VERSION or stamp.get("requirements") != requirements_hash()


def port_in_use() -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex((LOCAL_HOST, config.PORT)) == 0


class Api:
    """Called from the progress page's buttons."""

    def __init__(self, shell):
        self._shell = shell

    def retry(self):
        threading.Thread(target=self._shell.run, daemon=True).start()

    def show_log(self):
        subprocess.run(["open", "-R", str(LOG)])


class Shell:
    def __init__(self):
        self.window = None
        self.proc = None
        self.server = None

    def ui(self, fn, *args):
        self.window.evaluate_js(f"{fn}({', '.join(json.dumps(a) for a in args)})")

    def stream(self, cmd) -> bool:
        """Run a setup command, showing its output in the window and appending it to install.log."""
        with LOG.open("a", encoding="utf-8") as log:
            log.write(f"\n=== {time.ctime()}  {' '.join(cmd)}\n")
            log.flush()
            self.proc = subprocess.Popen(
                cmd, cwd=SUPPORT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace", env=os.environ | {"PYTHONUNBUFFERED": "1"},
            )
            last = 0.0
            for line in self.proc.stdout:  # text mode also splits tqdm's \r updates
                log.write(line)
                line = line.strip()
                if line and time.monotonic() - last > 0.1:
                    last = time.monotonic()
                    self.ui("logLine", line)
            return self.proc.wait() == 0

    def fail(self, message):
        self.ui("fail", message)
        return False

    def setup(self) -> bool:
        first = not STAMP.exists()
        self.ui("begin", "Setting up Song SRT Generator" if first else f"Updating to version {VERSION}", first)

        bundled_models = RESOURCES / "models"  # only in --full builds
        if bundled_models.is_dir() and not (SUPPORT / "models").exists():
            shutil.copytree(bundled_models, SUPPORT / "models")

        self.ui("step", 1, "Installing the app's Python packages",
                "About 1 GB the first time. Updates only fetch what changed.")
        if not self.stream([UV, "pip", "install", "--python", sys.executable,
                            "-r", str(APP_DIR / "requirements.txt")]):
            return self.fail("Couldn't install the Python packages. Check your internet connection and try again.")

        if first:
            self.ui("step", 2, "Downloading the AI models and doing a test run",
                    "About 1.5 GB (5–20 minutes). The models are kept, so updates never download them again.")
        else:
            self.ui("step", 2, "Doing a test run", "Using the AI models already on this Mac.")
        if not self.stream([sys.executable, str(APP_DIR / "warmup.py")]):
            return self.fail("The test run didn't pass. Check your internet connection and try again.")

        STAMP.write_text(json.dumps({"version": VERSION, "requirements": requirements_hash(),
                                     "installed": time.strftime("%Y-%m-%d %H:%M:%S")}), encoding="utf-8")
        self.ui("step", 3, "PASS — all set", "Opening the app…")
        return True

    def start_server(self) -> bool:
        if port_in_use():
            return self.fail(
                f"Port {config.PORT} is already in use. If the app is open in a browser "
                "(Start.command), close that Terminal window, then click Try again.")
        import uvicorn
        import app as server

        server.on_focus_request = self.focus
        self.server = uvicorn.Server(uvicorn.Config(server.app, host=config.HOST, port=config.PORT,
                                                    log_level="warning"))
        threading.Thread(target=self.server.run, daemon=True).start()
        for _ in range(300):
            if self.server.started:
                return True
            time.sleep(0.1)
        return self.fail("The app's local server didn't start. Click Try again.")

    def run(self):
        self.ui("reset")
        if needs_setup() and not self.setup():
            return
        if self.server is None and not self.start_server():
            return
        self.window.load_url(URL)

    def focus(self):
        from AppKit import NSApp
        from PyObjCTools import AppHelper

        self.window.restore()
        self.window.show()
        AppHelper.callAfter(lambda: NSApp.activateIgnoringOtherApps_(True))


def main():
    SUPPORT.mkdir(parents=True, exist_ok=True)
    lock = claim_single_instance()  # noqa: F841 — held open until exit
    shell = Shell()
    webview.settings["ALLOW_DOWNLOADS"] = True
    shell.window = webview.create_window(
        "Song SRT Generator", html=(RESOURCES / "progress.html").read_text(encoding="utf-8"),
        js_api=Api(shell), width=1280, height=880, min_size=(920, 640), background_color="#f5f6f9",
    )
    # Persistent storage keeps the theme and language picks between launches.
    webview.start(shell.run, private_mode=False, storage_path=str(SUPPORT / "webview"),
                  icon=str(RESOURCES / "AppIcon.icns"))
    if shell.proc and shell.proc.poll() is None:
        shell.proc.kill()
    os._exit(0)  # window closed: stop the server and the job worker with it


if __name__ == "__main__":
    main()

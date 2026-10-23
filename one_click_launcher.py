"""Windows/macOS one-click seminar launcher (stdlib only).

Starts FastAPI, waits for readiness and opens a browser. With explicit
VNPAY_ENABLE_NGROK=1, also starts/reuses ngrok and supplies its current public
Return URL to the new FastAPI process. Never reads or prints Hash Secret.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent
LOCAL = "http://127.0.0.1:8000"
API_TITLE = "VNPAY Sandbox Seminar"


def get_json(url: str, timeout: float = 1.0):
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, HTTPError, URLError):
        return None


def app_status() -> str:
    """Return 'ours', 'other', or 'stopped' for the hardcoded demo port."""
    result = get_json(LOCAL + "/openapi.json")
    if isinstance(result, dict) and API_TITLE in result.get("info", {}).get("title", ""):
        return "ours"
    try:
        with urlopen(LOCAL + "/", timeout=0.7):
            return "other"
    except HTTPError:
        return "other"
    except (OSError, URLError):
        return "stopped"


def discover_ngrok() -> str | None:
    """Read the ngrok Agent API; only accept an HTTPS tunnel to port 8000."""
    for path, collection in (("/api/tunnels", "tunnels"), ("/api/endpoints", "endpoints")):
        data = get_json("http://127.0.0.1:4040" + path)
        if not isinstance(data, dict):
            continue
        for item in data.get(collection, []):
            if not isinstance(item, dict):
                continue
            address = item.get("public_url") or item.get("url") or ""
            if not address.startswith("https://"):
                continue
            upstream = item.get("config", {}).get("addr", "") if isinstance(item.get("config"), dict) else ""
            # ngrok uses config.addr in /api/tunnels; an empty upstream on
            # /api/endpoints is not enough evidence of an 8000 forwarding.
            if "8000" not in str(upstream):
                continue
            return address.rstrip("/")
    return None


def spawn(args: list[str], label: str, env: dict[str, str] | None = None):
    """Start a detached process and record its PID for Mac's stop button.

    On Unix stdout/stderr are kept in project-local log files to aid debugging.
    Windows keeps the original separate console behavior.
    """
    kwargs = {"cwd": str(ROOT), "env": env or os.environ.copy()}
    log_stream = None
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["start_new_session"] = True
        log_stream = open(ROOT / f".demo-{label}.log", "a", encoding="utf-8")
        kwargs["stdout"] = log_stream
        kwargs["stderr"] = subprocess.STDOUT
    try:
        proc = subprocess.Popen(args, **kwargs)
        (ROOT / f".demo-{label}.pid").write_text(str(proc.pid), encoding="ascii")
        return proc
    finally:
        if log_stream:
            log_stream.close()


def stop_spawned() -> int:
    """Only stop a PID we launched, after verifying its actual command."""
    if os.name == "nt":
        print("[INFO] On Windows, close the separate FastAPI/ngrok console windows.")
        return 0
    for label, expected_parts in (
        ("uvicorn", ("uvicorn", "main:app", "8000")),
        ("ngrok", ("ngrok", "http", "8000")),
    ):
        pid_file = ROOT / f".demo-{label}.pid"
        if not pid_file.exists():
            print(f"[INFO] No tracked {label} process.")
            continue
        try:
            pid = int(pid_file.read_text(encoding="ascii").strip())
            cmd = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                check=False, capture_output=True, text=True, timeout=4,
            ).stdout.strip()
            if cmd and all(token in cmd for token in expected_parts):
                os.kill(pid, signal.SIGTERM)
                print(f"[OK] Stopped {label} (PID {pid}).")
            else:
                print(f"[INFO] {label} already exited or PID belongs to another program; not killed.")
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            print(f"[WARN] Could not stop {label}: {exc}")
        finally:
            pid_file.unlink(missing_ok=True)
    return 0


def wait_until(check, seconds: int):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.5)
    return None


def hostname_resolves(url: str) -> bool:
    try:
        host = urlsplit(url).hostname
        if not host:
            return False
        socket.getaddrinfo(host, 443)
        return True
    except OSError:
        return False


def credentials_ready() -> bool:
    # Secret is never logged; only booleans are displayed.
    from dotenv import dotenv_values
    settings = dotenv_values(ROOT / ".env") if (ROOT / ".env").exists() else {}
    tmn = (os.getenv("VNPAY_TMN_CODE") or settings.get("VNPAY_TMN_CODE") or "").strip()
    secret = (os.getenv("VNPAY_HASH_SECRET") or settings.get("VNPAY_HASH_SECRET") or "").strip()
    return bool(tmn and secret and not tmn.startswith("DIEN_") and not secret.startswith("DIEN_"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser (for automated checks)")
    parser.add_argument("--ngrok", action="store_true", help="Enable public ngrok tunnel")
    parser.add_argument("--stop", action="store_true", help="Stop tracked Mac demo processes")
    options = parser.parse_args()
    if options.stop:
        return stop_spawned()

    port = app_status()
    if port == "other":
        print("[ERROR] Port 8000 is already used by another application.")
        print("Close that process, then run START_DEMO.bat again.")
        return 1

    public_url = None
    if options.ngrok or os.getenv("VNPAY_ENABLE_NGROK") == "1":
        public_url = discover_ngrok()
        if public_url:
            print("[OK] Reusing existing ngrok tunnel:", public_url)
        elif shutil.which("ngrok"):
            print("[INFO] Starting ngrok http 8000 in a new terminal...")
            try:
                spawn([shutil.which("ngrok"), "http", "8000"], label="ngrok")
                public_url = wait_until(discover_ngrok, 16)
            except OSError as exc:
                print("[WARN] Cannot launch ngrok:", exc)
            if not public_url:
                print("[WARN] No HTTPS tunnel detected. Running website locally instead.")
                print("       Check ngrok authentication if public URL is required.")
        else:
            print("[INFO] ngrok is not installed; running local-only website.")

    backend_env = os.environ.copy()
    if public_url:
        backend_env["VNPAY_RETURN_URL"] = public_url + "/payment/result"
    else:
        backend_env["VNPAY_RETURN_URL"] = LOCAL + "/payment/result"

    if port == "stopped":
        print("[INFO] Starting FastAPI in a new terminal...")
        try:
            spawn([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"], label="uvicorn", env=backend_env)
        except OSError as exc:
            print("[ERROR] Cannot launch FastAPI:", exc)
            return 1
        if not wait_until(lambda: app_status() == "ours", 25):
            print("[ERROR] FastAPI did not start. Check the FastAPI console (Windows) or .demo-uvicorn.log (Mac).")
            return 1
    else:
        print("[WARN] FastAPI is already running. Its existing Return URL cannot be changed here.")
        print("       For a new public URL: close the old FastAPI window, then restart this launcher.")

    print("\n" + "=" * 62)
    print("[OK] VNStore website is ready:", LOCAL + "/")
    if public_url:
        print("[OK] Public HTTPS:", public_url + "/")
        print("[INFO] Return URL for a NEW FastAPI process:", public_url + "/payment/result")
        print("[INFO] IPN endpoint (must be registered with VNPAY separately):")
        print("       ", public_url + "/api/payment/ipn")
        print("[INFO] Local ngrok inspector: http://127.0.0.1:4040")
    if not credentials_ready():
        print("[WARN] .env has no real Sandbox credentials. The UI works,")
        print("       but genuine VNPAY payment creation requires a valid TMN Code/Hash Secret.")
    else:
        print("[OK] Sandbox credential fields exist (not verified with VNPAY).")
    print("[NOTE] An IPN is not guaranteed until VNPAY configures this endpoint.")
    print("[NOTE] Windows: close server/ngrok consoles; Mac: run STOP_DEMO.command.")
    print("=" * 62)

    # Choose a reachable site; local always works even if DNS for ngrok is delayed.
    open_url = public_url + "/" if public_url and hostname_resolves(public_url) else LOCAL + "/"
    if public_url and open_url.startswith(LOCAL):
        print("[WARN] Public DNS doesn't resolve on this machine yet; opening local URL.")
    if not options.no_browser:
        webbrowser.open(open_url, new=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

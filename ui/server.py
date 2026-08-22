#!/usr/bin/env python3
"""Local server for the English B paper generator.

Serves the editor and compiles what it sends with tectonic. Standard library
only — nothing to install. Bound to localhost; it is not a public service.

    make ui          # or:  python3 ui/server.py
"""
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
LATEX = HERE.parent
PORT = int(os.environ.get("IBEB_PORT", "8731"))
BUILD = LATEX / "ui" / "build"


def tectonic():
    exe = shutil.which("tectonic")
    if exe:
        return exe
    for p in ("/opt/homebrew/bin/tectonic", "/usr/local/bin/tectonic"):
        if Path(p).exists():
            return p
    return None


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def log_message(self, fmt, *args):          # keep the terminal readable
        try:
            first = str(args[0]) if args else ""
        except Exception:
            first = ""
        if "/compile" in first:
            sys.stderr.write("  compile\n")

    def log_error(self, *a, **kw):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/favicon.ico":
            return self._send(204, "image/x-icon", b"")
        return super().do_GET()

    def do_POST(self):
        if self.path != "/compile":
            return self._send(404, "text/plain", b"not found")
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, "text/plain", b"bad JSON")
        tex = payload.get("tex", "")
        if not tex.strip():
            return self._send(400, "text/plain", b"nothing to compile")

        exe = tectonic()
        if not exe:
            return self._send(
                400, "text/plain",
                b"tectonic not found on PATH.\n"
                b"Install it with:  brew install tectonic")

        BUILD.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            shutil.copy(LATEX / "ibenglishb.sty", tmp)
            (tmp / "paper.tex").write_text(tex, encoding="utf-8")
            try:
                r = subprocess.run(
                    [exe, "-X", "compile", "--keep-logs", "paper.tex"],
                    cwd=tmp, capture_output=True, text=True, timeout=180)
            except subprocess.TimeoutExpired:
                return self._send(400, "text/plain", b"compile timed out")

            pdf = tmp / "paper.pdf"
            if not pdf.exists():
                log = (r.stderr or "") + "\n" + (r.stdout or "")
                lines = [l for l in log.splitlines()
                         if l.strip().startswith(("error", "!"))
                         or "Warning" in l]
                msg = "\n".join(lines[:40]) or log[-3000:] or "compile failed"
                return self._send(400, "text/plain", msg.encode())

            data = pdf.read_bytes()
            shutil.copy(pdf, BUILD / "paper.pdf")
            (BUILD / "paper.tex").write_text(tex, encoding="utf-8")
            ans = tmp / "paper.ans"
            if ans.exists():
                shutil.copy(ans, BUILD / "paper.ans")

            warn = "\n".join(l for l in (r.stderr or "").splitlines()
                             if "ibenglishb Warning" in l or "Overfull" in l)
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            if warn:
                self.send_header("X-Ibeb-Warnings",
                                 warn.replace("\n", " | ")[:900])
            self.end_headers()
            self.wfile.write(data)


def main():
    if not (LATEX / "ibenglishb.sty").exists():
        sys.exit(f"ibenglishb.sty not found in {LATEX}")
    if not tectonic():
        print("  ! tectonic not found — the editor will run, but Compile "
              "will fail.\n    Install it with:  brew install tectonic\n")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"  English B paper generator running at {url}")
    print("  Press Ctrl-C to stop.\n")
    webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")


if __name__ == "__main__":
    main()

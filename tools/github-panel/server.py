#!/usr/bin/env python3
"""ZengCloud 本地 GitHub 上传面板 — 仅绑定 127.0.0.1。"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8787
ROOT = Path(__file__).resolve().parents[2]  # d:\zengcloud
STATIC = Path(__file__).resolve().parent / "static"
GIT = shutil.which("git") or r"D:\Git\cmd\git.exe"

SAFE_REMOTE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+(?:\.git)?$|^git@github\.com:[\w.-]+/[\w.-]+(?:\.git)?$")


def run_git(args: list[str], timeout: int = 120) -> dict:
    if not Path(GIT).exists() and not shutil.which("git"):
        return {"ok": False, "code": -1, "stdout": "", "stderr": "未找到 git，请先安装 Git for Windows"}
    cmd = [GIT, *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "cmd": " ".join(args),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": -1, "stdout": "", "stderr": "命令超时", "cmd": " ".join(args)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "code": -1, "stdout": "", "stderr": str(exc), "cmd": " ".join(args)}


def is_repo() -> bool:
    return (ROOT / ".git").exists()


def summary() -> dict:
    remote = run_git(["remote", "get-url", "origin"]) if is_repo() else None
    branch = run_git(["branch", "--show-current"]) if is_repo() else None
    status = run_git(["status", "--short", "--branch"]) if is_repo() else None
    return {
        "root": str(ROOT),
        "is_repo": is_repo(),
        "remote": (remote or {}).get("stdout") or "",
        "branch": (branch or {}).get("stdout") or "",
        "status": (status or {}).get("stdout") or ("尚未初始化 Git 仓库" if not is_repo() else ""),
        "git_bin": GIT,
    }


def handle_action(payload: dict) -> dict:
    action = payload.get("action")
    logs: list[dict] = []

    def step(args: list[str]) -> dict:
        result = run_git(args)
        logs.append(result)
        return result

    if action == "summary":
        return {"ok": True, "summary": summary(), "logs": []}

    if action == "status":
        if not is_repo():
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "还不是 Git 仓库，请先初始化", "cmd": "status"}]}
        r = step(["status"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "log":
        if not is_repo():
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "还不是 Git 仓库", "cmd": "log"}]}
        r = step(["log", "--oneline", "-15", "--decorate"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "init":
        if is_repo():
            return {"ok": True, "summary": summary(), "logs": [{"ok": True, "stdout": "仓库已存在，跳过 init", "stderr": "", "cmd": "init"}]}
        r = step(["init"])
        if r["ok"]:
            step(["branch", "-M", "main"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "set_remote":
        url = (payload.get("remote_url") or "").strip()
        if not SAFE_REMOTE.match(url):
            return {
                "ok": False,
                "summary": summary(),
                "logs": [{"ok": False, "stderr": "远程地址格式不正确，请使用 https://github.com/用户名/仓库名.git", "cmd": "remote"}],
            }
        if not is_repo():
            step(["init"])
            step(["branch", "-M", "main"])
        check = run_git(["remote"])
        if "origin" in (check.get("stdout") or "").split():
            r = step(["remote", "set-url", "origin", url])
        else:
            r = step(["remote", "add", "origin", url])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "add":
        if not is_repo():
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "请先初始化仓库", "cmd": "add"}]}
        r = step(["add", "-A"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "commit":
        if not is_repo():
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "请先初始化仓库", "cmd": "commit"}]}
        message = (payload.get("message") or "").strip()
        if not message:
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "请填写提交说明", "cmd": "commit"}]}
        # Avoid empty commit noise
        staged = run_git(["diff", "--cached", "--quiet"])
        unstaged = run_git(["diff", "--quiet"])
        untracked = run_git(["ls-files", "--others", "--exclude-standard"])
        if staged["code"] == 0 and unstaged["code"] == 0 and not untracked.get("stdout"):
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "没有可提交的变更", "cmd": "commit"}]}
        if staged["code"] == 0:
            step(["add", "-A"])
        r = step(["commit", "-m", message])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "push":
        if not is_repo():
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "请先初始化仓库", "cmd": "push"}]}
        remote = run_git(["remote", "get-url", "origin"])
        if not remote["ok"]:
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "请先设置 GitHub 远程地址", "cmd": "push"}]}
        branch = run_git(["branch", "--show-current"])
        name = branch.get("stdout") or "main"
        r = step(["push", "-u", "origin", name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "pull":
        if not is_repo():
            return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": "请先初始化仓库", "cmd": "pull"}]}
        r = step(["pull", "--rebase", "origin"])
        if not r["ok"]:
            r = step(["pull", "origin"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "one_click":
        message = (payload.get("message") or "").strip() or "chore: sync project"
        url = (payload.get("remote_url") or "").strip()
        if url and not SAFE_REMOTE.match(url):
            return {
                "ok": False,
                "summary": summary(),
                "logs": [{"ok": False, "stderr": "远程地址格式不正确", "cmd": "one_click"}],
            }
        if not is_repo():
            step(["init"])
            step(["branch", "-M", "main"])
        if url:
            check = run_git(["remote"])
            if "origin" in (check.get("stdout") or "").split():
                step(["remote", "set-url", "origin", url])
            else:
                step(["remote", "add", "origin", url])
        step(["add", "-A"])
        # commit only if changes
        staged = run_git(["diff", "--cached", "--quiet"])
        if staged["code"] != 0:
            step(["commit", "-m", message])
        remote = run_git(["remote", "get-url", "origin"])
        if not remote["ok"]:
            return {
                "ok": False,
                "summary": summary(),
                "logs": logs + [{"ok": False, "stderr": "缺少远程地址，无法推送", "cmd": "push"}],
            }
        branch = run_git(["branch", "--show-current"]).get("stdout") or "main"
        r = step(["push", "-u", "origin", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    return {"ok": False, "summary": summary(), "logs": [{"ok": False, "stderr": f"未知操作: {action}", "cmd": ""}]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # quieter console
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            file_path = STATIC / "index.html"
        elif path.startswith("/static/"):
            file_path = STATIC / path[len("/static/") :]
        elif path == "/api/summary":
            data = json.dumps({"ok": True, "summary": summary()}, ensure_ascii=False).encode("utf-8")
            return self._send(200, data, "application/json; charset=utf-8")
        else:
            return self._send(404, b"Not Found", "text/plain")

        if not file_path.exists() or not file_path.resolve().is_relative_to(STATIC.resolve()):
            return self._send(404, b"Not Found", "text/plain")

        raw = file_path.read_bytes()
        ctype = "text/html; charset=utf-8"
        if file_path.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif file_path.suffix == ".js":
            ctype = "application/javascript; charset=utf-8"
        self._send(200, raw, ctype)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/action":
            return self._send(404, b"Not Found", "text/plain")
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return self._send(400, b'{"ok":false}', "application/json")
        result = handle_action(payload)
        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self._send(200, data, "application/json; charset=utf-8")


def main() -> None:
    if not STATIC.exists():
        print("缺少 static 目录", file=sys.stderr)
        sys.exit(1)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("=" * 56)
    print(" ZengCloud GitHub 上传面板")
    print(f" 打开: http://{HOST}:{PORT}/")
    print(f" 项目: {ROOT}")
    print(" 按 Ctrl+C 停止")
    print("=" * 56)
    try:
        import webbrowser

        webbrowser.open(f"http://{HOST}:{PORT}/")
    except Exception:  # noqa: BLE001
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()

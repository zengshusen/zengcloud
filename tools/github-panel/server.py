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
ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
GIT = shutil.which("git") or r"D:\Git\cmd\git.exe"

SAFE_REMOTE = re.compile(
    r"^https://github\.com/[\w.-]+/[\w.-]+(?:\.git)?$"
    r"|^git@github\.com:[\w.-]+/[\w.-]+(?:\.git)?$"
)
SAFE_BRANCH = re.compile(r"^[\w./-]{1,120}$")
SAFE_MSG = re.compile(r"^[\s\S]{1,500}$")
SAFE_NAME = re.compile(r"^[\w .@+-]{1,80}$")
SAFE_REF = re.compile(r"^[\w./~^@{}-]{1,120}$")


def run_git(args: list[str], timeout: int = 180) -> dict:
    if not Path(GIT).exists() and not shutil.which("git"):
        return {
            "ok": False,
            "code": -1,
            "stdout": "",
            "stderr": "未找到 git，请先安装 Git for Windows",
            "cmd": " ".join(args),
        }
    try:
        proc = subprocess.run(
            [GIT, *args],
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


def list_branches(fetch_remote: bool = False) -> dict:
    """返回本地与远程（GitHub/origin）分支列表。"""
    logs: list[dict] = []
    if not is_repo():
        return {
            "ok": False,
            "current": "",
            "local": [],
            "remote": [],
            "all": [],
            "logs": [{"ok": False, "stdout": "", "stderr": "还不是 Git 仓库", "cmd": "branch"}],
        }

    if fetch_remote:
        fr = run_git(["fetch", "origin", "--prune"])
        logs.append(fr)

    local_raw = run_git(["for-each-ref", "--format=%(refname:short)", "refs/heads"])
    remote_raw = run_git(["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"])
    logs.extend([local_raw, remote_raw])

    local = [x.strip() for x in (local_raw.get("stdout") or "").splitlines() if x.strip()]
    remote = []
    for line in (remote_raw.get("stdout") or "").splitlines():
        name = line.strip()
        if not name or name == "origin" or name.endswith("/HEAD"):
            continue
        # origin/main -> main
        short = name[7:] if name.startswith("origin/") else name
        if short and short not in remote:
            remote.append(short)

    current = run_git(["branch", "--show-current"]).get("stdout") or ""
    # 合并去重，远程优先标注来源在前端处理
    all_names = sorted(set(local) | set(remote), key=lambda s: (s != "main", s != "master", s))
    return {
        "ok": True,
        "current": current,
        "local": local,
        "remote": remote,
        "all": all_names,
        "logs": logs,
    }


def commit_history(limit: int = 50) -> list[dict]:
    """完整提交历史：时间、作者、说明、hash、分支装饰。"""
    if not is_repo():
        return []
    limit = max(1, min(int(limit or 50), 200))
    result = run_git(
        [
            "log",
            f"-{limit}",
            "--date=format:%Y-%m-%d %H:%M:%S",
            "--pretty=format:%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s%x1f%b%x1f%D%x1e",
        ]
    )
    if not result.get("ok") and not result.get("stdout"):
        return []
    commits: list[dict] = []
    for record in (result.get("stdout") or "").split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 6:
            continue
        full, short, author, email, date, subject = parts[:6]
        body = parts[6].strip() if len(parts) > 6 else ""
        refs = parts[7].strip() if len(parts) > 7 else ""
        commits.append(
            {
                "hash": full,
                "short": short,
                "author": author,
                "email": email,
                "date": date,
                "subject": subject,
                "body": body,
                "refs": refs,
            }
        )
    return commits


def summary() -> dict:
    remote = run_git(["remote", "get-url", "origin"]) if is_repo() else None
    branch = run_git(["branch", "--show-current"]) if is_repo() else None
    status = run_git(["status", "--short", "--branch"]) if is_repo() else None
    branches = (
        list_branches(fetch_remote=False)
        if is_repo()
        else {
            "ok": False,
            "current": "",
            "local": [],
            "remote": [],
            "all": [],
        }
    )
    history = commit_history(50) if is_repo() else []
    return {
        "root": str(ROOT),
        "is_repo": is_repo(),
        "remote": (remote or {}).get("stdout") or "",
        "branch": (branch or {}).get("stdout") or "",
        "status": (status or {}).get("stdout")
        or ("尚未初始化 Git 仓库" if not is_repo() else ""),
        "git_bin": GIT,
        "branches": {
            "current": branches.get("current") or "",
            "local": branches.get("local") or [],
            "remote": branches.get("remote") or [],
            "all": branches.get("all") or [],
        },
        "commits": history,
        "commit_count": len(history),
    }


def need_repo(logs: list[dict]) -> bool:
    if is_repo():
        return True
    logs.append({"ok": False, "stdout": "", "stderr": "还不是 Git 仓库，请先初始化", "cmd": "(guard)"})
    return False


def handle_action(payload: dict) -> dict:
    action = (payload.get("action") or "").strip()
    logs: list[dict] = []

    def step(args: list[str]) -> dict:
        result = run_git(args)
        logs.append(result)
        return result

    remote_url = (payload.get("remote_url") or "").strip()
    message = (payload.get("message") or "").strip()
    branch = (payload.get("branch") or "").strip()
    target = (payload.get("target") or "").strip()
    user_name = (payload.get("user_name") or "").strip()
    user_email = (payload.get("user_email") or "").strip()
    tag_name = (payload.get("tag_name") or "").strip()

    if action == "summary":
        return {"ok": True, "summary": summary(), "logs": []}

    if action == "list_branches":
        fetch_remote = bool(payload.get("fetch_remote"))
        data = list_branches(fetch_remote=fetch_remote)
        return {
            "ok": data["ok"],
            "summary": summary(),
            "branches": data,
            "logs": data.get("logs") or [],
        }

    if action == "branch_use_existing":
        # 切换到已有分支：本地直接切；仅远程则创建本地跟踪分支
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请选择已有分支", "cmd": "switch"})
            return {"ok": False, "summary": summary(), "logs": logs}
        info = list_branches(False)
        local_names = info.get("local") or []
        remote_names = info.get("remote") or []
        if branch in local_names:
            r = step(["switch", branch])
        elif branch in remote_names:
            r = step(["switch", "--track", f"origin/{branch}"])
            if not r["ok"]:
                r = step(["checkout", "-b", branch, "--track", f"origin/{branch}"])
        else:
            logs.append(
                {
                    "ok": False,
                    "stdout": "",
                    "stderr": f"未找到分支 {branch}，请先点「刷新 GitHub 分支」",
                    "cmd": "switch",
                }
            )
            return {"ok": False, "summary": summary(), "logs": logs}
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_create_new":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写新分支名", "cmd": "checkout -b"})
            return {"ok": False, "summary": summary(), "logs": logs}
        local_names = list_branches(False).get("local") or []
        if branch in local_names:
            logs.append({"ok": False, "stdout": "", "stderr": f"本地已存在分支 {branch}", "cmd": "checkout -b"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["checkout", "-b", branch])
        if r["ok"] and payload.get("push_after"):
            step(["push", "-u", "origin", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "commit_history":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        limit = payload.get("limit") or 50
        commits = commit_history(limit)
        logs.append(
            {
                "ok": True,
                "stdout": f"已加载 {len(commits)} 条提交记录",
                "stderr": "",
                "cmd": f"log -{limit}",
            }
        )
        return {"ok": True, "summary": summary(), "commits": commits, "logs": logs}

    # ---- 高频 / 工作流 ----
    if action == "status":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["status"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "add":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["add", "-A"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "commit":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not message or not SAFE_MSG.match(message):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写有效提交说明", "cmd": "commit"})
            return {"ok": False, "summary": summary(), "logs": logs}
        staged = run_git(["diff", "--cached", "--quiet"])
        if staged["code"] == 0:
            step(["add", "-A"])
        staged2 = run_git(["diff", "--cached", "--quiet"])
        untracked = run_git(["ls-files", "--others", "--exclude-standard"])
        if staged2["code"] == 0 and not untracked.get("stdout"):
            logs.append({"ok": False, "stdout": "", "stderr": "没有可提交的变更", "cmd": "commit"})
            return {"ok": False, "summary": summary(), "logs": logs}
        if staged2["code"] == 0:
            step(["add", "-A"])
        r = step(["commit", "-m", message])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "push":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not run_git(["remote", "get-url", "origin"])["ok"]:
            logs.append({"ok": False, "stdout": "", "stderr": "请先设置 origin 远程地址", "cmd": "push"})
            return {"ok": False, "summary": summary(), "logs": logs}
        name = run_git(["branch", "--show-current"]).get("stdout") or "main"
        r = step(["push", "-u", "origin", name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "pull":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["pull", "--rebase", "origin"])
        if not r["ok"]:
            r = step(["pull", "origin"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "log":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["log", "--oneline", "-20", "--decorate"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "one_click":
        msg = message or "chore: sync project"
        if remote_url and not SAFE_REMOTE.match(remote_url):
            logs.append({"ok": False, "stdout": "", "stderr": "远程地址格式不正确", "cmd": "one_click"})
            return {"ok": False, "summary": summary(), "logs": logs}
        if not is_repo():
            step(["init"])
            step(["branch", "-M", "main"])
        if remote_url:
            remotes = run_git(["remote"]).get("stdout") or ""
            if "origin" in remotes.split():
                step(["remote", "set-url", "origin", remote_url])
            else:
                step(["remote", "add", "origin", remote_url])
        step(["add", "-A"])
        if run_git(["diff", "--cached", "--quiet"])["code"] != 0:
            step(["commit", "-m", msg])
        if not run_git(["remote", "get-url", "origin"])["ok"]:
            logs.append({"ok": False, "stdout": "", "stderr": "缺少远程地址，无法推送", "cmd": "push"})
            return {"ok": False, "summary": summary(), "logs": logs}
        name = run_git(["branch", "--show-current"]).get("stdout") or "main"
        r = step(["push", "-u", "origin", name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "quick_sync":
        # add → commit → push（日常最高频）
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        msg = message or "chore: sync project"
        step(["add", "-A"])
        if run_git(["diff", "--cached", "--quiet"])["code"] != 0:
            step(["commit", "-m", msg])
        else:
            logs.append({"ok": True, "stdout": "无新变更可提交，继续尝试推送", "stderr": "", "cmd": "commit"})
        name = run_git(["branch", "--show-current"]).get("stdout") or "main"
        if not run_git(["remote", "get-url", "origin"])["ok"]:
            logs.append({"ok": False, "stdout": "", "stderr": "请先设置远程地址", "cmd": "push"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["push", "-u", "origin", name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- 仓库基础 ----
    if action == "init":
        if is_repo():
            logs.append({"ok": True, "stdout": "仓库已存在，跳过", "stderr": "", "cmd": "init"})
            return {"ok": True, "summary": summary(), "logs": logs}
        r = step(["init"])
        if r["ok"]:
            step(["branch", "-M", "main"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "set_remote":
        if not SAFE_REMOTE.match(remote_url):
            logs.append(
                {
                    "ok": False,
                    "stdout": "",
                    "stderr": "请使用 https://github.com/用户/仓库.git 格式",
                    "cmd": "remote",
                }
            )
            return {"ok": False, "summary": summary(), "logs": logs}
        if not is_repo():
            step(["init"])
            step(["branch", "-M", "main"])
        remotes = run_git(["remote"]).get("stdout") or ""
        if "origin" in remotes.split():
            r = step(["remote", "set-url", "origin", remote_url])
        else:
            r = step(["remote", "add", "origin", remote_url])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "remote_v":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["remote", "-v"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "remote_remove_origin":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["remote", "remove", "origin"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "config_user_name":
        if not user_name or not SAFE_NAME.match(user_name):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写合法用户名", "cmd": "config"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["config", "user.name", user_name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "config_user_email":
        if not user_email or "@" not in user_email or len(user_email) > 120:
            logs.append({"ok": False, "stdout": "", "stderr": "请填写合法邮箱", "cmd": "config"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["config", "user.email", user_email])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "config_list":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["config", "--list", "--local"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- 暂存 / 差异 ----
    if action == "add_update":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["add", "-u"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "add_dot":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["add", "."])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "unstage_all":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["reset", "HEAD"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "diff":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["diff"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "diff_staged":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["diff", "--staged"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "diff_stat":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["diff", "--stat"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "ls_files":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["ls-files", "-v"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "status_short":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["status", "-sb"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- 提交扩展 ----
    if action == "commit_amend":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if message:
            r = step(["commit", "--amend", "-m", message])
        else:
            r = step(["commit", "--amend", "--no-edit"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "commit_empty":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        msg = message or "chore: empty commit"
        r = step(["commit", "--allow-empty", "-m", msg])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "show_head":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["show", "--stat", "HEAD"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- 分支 ----
    if action == "branch_list":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["branch", "-vv"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_all":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["branch", "-a"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_main":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["branch", "-M", "main"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_rename":
        # 将当前分支重命名为 branch 字段
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请在「分支名」填写新分支名", "cmd": "branch -m"})
            return {"ok": False, "summary": summary(), "logs": logs}
        current = run_git(["branch", "--show-current"]).get("stdout") or ""
        if not current:
            logs.append({"ok": False, "stdout": "", "stderr": "当前不在任何分支上（detached HEAD）", "cmd": "branch -m"})
            return {"ok": False, "summary": summary(), "logs": logs}
        if current == branch:
            logs.append({"ok": True, "stdout": f"分支名已是 {branch}，无需修改", "stderr": "", "cmd": "branch -m"})
            return {"ok": True, "summary": summary(), "logs": logs}
        r = step(["branch", "-m", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_rename_from":
        # target=旧名, branch=新名
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        old = target
        new = branch
        if not old or not SAFE_BRANCH.match(old) or not new or not SAFE_BRANCH.match(new):
            logs.append(
                {
                    "ok": False,
                    "stdout": "",
                    "stderr": "请填写：目标 commit/标签名=旧分支名，分支名=新分支名",
                    "cmd": "branch -m old new",
                }
            )
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["branch", "-m", old, new])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_delete":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写要删除的本地分支名", "cmd": "branch -d"})
            return {"ok": False, "summary": summary(), "logs": logs}
        current = run_git(["branch", "--show-current"]).get("stdout") or ""
        if current == branch:
            logs.append({"ok": False, "stdout": "", "stderr": "不能删除当前所在分支，请先切换到其他分支", "cmd": "branch -d"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["branch", "-d", branch])
        if not r["ok"]:
            r = step(["branch", "-D", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_delete_remote":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写要删除的远程分支名", "cmd": "push --delete"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["push", "origin", "--delete", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "branch_push_set_upstream":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        name = branch or run_git(["branch", "--show-current"]).get("stdout") or ""
        if not name or not SAFE_BRANCH.match(name):
            logs.append({"ok": False, "stdout": "", "stderr": "无法确定分支名", "cmd": "push -u"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["push", "-u", "origin", name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "checkout_new":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写合法分支名", "cmd": "checkout -b"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["checkout", "-b", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "checkout":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写要切换的分支名", "cmd": "checkout"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["checkout", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "switch":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写分支名", "cmd": "switch"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["switch", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "merge":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not branch or not SAFE_BRANCH.match(branch):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写要合并的分支", "cmd": "merge"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["merge", branch])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "rebase":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        ref = branch or "origin/main"
        if not SAFE_BRANCH.match(ref):
            logs.append({"ok": False, "stdout": "", "stderr": "rebase 目标不合法", "cmd": "rebase"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["rebase", ref])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "rebase_abort":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["rebase", "--abort"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "rebase_continue":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["rebase", "--continue"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- 同步 ----
    if action == "fetch":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["fetch", "origin"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "fetch_all":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["fetch", "--all", "--prune"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "pull_ff":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["pull", "--ff-only"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "push_tags":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["push", "origin", "--tags"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "push_force_lease":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        name = run_git(["branch", "--show-current"]).get("stdout") or "main"
        r = step(["push", "--force-with-lease", "origin", name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- stash / 撤销 ----
    if action == "stash":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["stash", "push", "-u", "-m", message or "panel-stash"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "stash_list":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["stash", "list"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "stash_pop":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["stash", "pop"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "stash_drop":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["stash", "drop"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "reset_soft":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["reset", "--soft", "HEAD~1"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "reset_mixed":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["reset", "--mixed", "HEAD~1"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "restore_worktree":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["restore", "."])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "clean_preview":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["clean", "-nd"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "clean_force":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["clean", "-fd"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    # ---- 查看 / 标签 ----
    if action == "log_graph":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["log", "--graph", "--oneline", "--decorate", "-20", "--all"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "shortlog":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["shortlog", "-sn", "--all"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "describe":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["describe", "--tags", "--always"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "tag_list":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["tag", "-l"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "tag_create":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not tag_name or not SAFE_BRANCH.match(tag_name):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写标签名", "cmd": "tag"})
            return {"ok": False, "summary": summary(), "logs": logs}
        if message:
            r = step(["tag", "-a", tag_name, "-m", message])
        else:
            r = step(["tag", tag_name])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "rev_parse_head":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["rev-parse", "HEAD"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "cherry_pick":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        if not target or not SAFE_REF.match(target):
            logs.append({"ok": False, "stdout": "", "stderr": "请填写 commit hash", "cmd": "cherry-pick"})
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["cherry-pick", target])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    if action == "revert_head":
        if not need_repo(logs):
            return {"ok": False, "summary": summary(), "logs": logs}
        r = step(["revert", "--no-edit", "HEAD"])
        return {"ok": r["ok"], "summary": summary(), "logs": logs}

    logs.append({"ok": False, "stdout": "", "stderr": f"未知操作: {action}", "cmd": action})
    return {"ok": False, "summary": summary(), "logs": logs}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
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

        resolved = file_path.resolve()
        if not resolved.exists() or not resolved.is_relative_to(STATIC.resolve()):
            return self._send(404, b"Not Found", "text/plain")

        raw = resolved.read_bytes()
        ctype = "text/html; charset=utf-8"
        if resolved.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif resolved.suffix == ".js":
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

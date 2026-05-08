#!/usr/bin/env python3
# =====================================================================
# github_sync_push.py — Layer 2 of GitHub publish pipeline (network).
#
# Binding policy: Docs/policy/GITHUB_SYNC_POLICY.md (2026-04-29).
# Companion: github_sync_curate.py (Layer 1, offline).
#
# Purpose
# -------
# Take the curated Github/ working tree and synchronise it with the
# remote public GitHub repository. Credentials are read from
# Codes/tools/github_sync_config.json (gitignored from the main repo).
# Until credentials are configured the script runs in dry-run mode and
# prints what would happen.
#
# Subcommands
# -----------
#   status       — show local status (no network)
#   init         — initialise Github/.git and set the remote (uses config)
#   commit       — stage all changes in Github/ and create a single commit
#   push         — push current branch to remote (requires credentials)
#   sync         — full pipeline: status -> commit -> push (with --dry-run gate)
#
# Safety
# ------
#   * Default is --dry-run unless `dry_run_default: false` in config OR
#     the operator passes --apply explicitly.
#   * `--force-push` is BLOCKED unless `--force-confirm` is also passed
#     AND `force_push: true` in config.
#   * Credentials are NEVER printed verbatim; tokens are masked.
#
# Author: Jusang Lee + collaboration (2026-04-29).
# =====================================================================

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET = REPO_ROOT / "Github"
CONFIG = Path(__file__).resolve().parent / "github_sync_config.json"
TEMPLATE = Path(__file__).resolve().parent / "github_sync_config.template.json"


# ---------------------------------------------------------------------
# Section A. Config loading + masking
# ---------------------------------------------------------------------
class ConfigError(RuntimeError):
    pass


def _load_config() -> dict:
    """Load github_sync_config.json. If missing, instruct operator and
    raise ConfigError (caller decides whether to abort or continue
    in degraded mode)."""
    if not CONFIG.exists():
        raise ConfigError(
            "github_sync_config.json not found at "
            f"{CONFIG.relative_to(REPO_ROOT)}.\n"
            "Create it from the template:\n"
            f"    cp {TEMPLATE.relative_to(REPO_ROOT)} {CONFIG.relative_to(REPO_ROOT)}\n"
            "and fill in github_username, github_repo, remote_url, and auth.\n"
            "The actual file is gitignored from the main repo (see .gitignore)."
        )
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"github_sync_config.json is not valid JSON: {e}"
        ) from e


def _mask_token(s: str) -> str:
    """Mask anything that looks like a token / password in a string.

    A token here is any 16+-char alnum string. We replace all but the
    first 4 chars with '*'. Used when echoing config or remote URLs."""
    if not s:
        return s
    return re.sub(
        r"\b([A-Za-z0-9_]{4})[A-Za-z0-9_]{12,}\b",
        lambda m: m.group(1) + "*" * 12,
        s,
    )


def _summarise_config(cfg: dict) -> None:
    print("Loaded github_sync_config.json:")
    masked = {
        "github_username": cfg.get("github_username", "(unset)"),
        "github_repo": cfg.get("github_repo", "(unset)"),
        "github_branch": cfg.get("github_branch", "main"),
        "remote_url": _mask_token(cfg.get("remote_url", "(unset)")),
        "auth.method": cfg.get("auth", {}).get("method", "none"),
        "auth.token_env_var": cfg.get("auth", {}).get("token_env_var", ""),
        "commit_author": cfg.get("commit_author", {}).get("name", ""),
        "commit_author_email": cfg.get("commit_author", {}).get("email", ""),
        "dry_run_default": cfg.get("dry_run_default", True),
        "publish_branch": cfg.get("publish_branch", "main"),
        "force_push": cfg.get("force_push", False),
    }
    for k, v in masked.items():
        print(f"  {k}: {v}")


# ---------------------------------------------------------------------
# Section B. git invocation
# ---------------------------------------------------------------------
def _git(args_list: list[str], *, cwd: Path = TARGET, env_extra: dict | None = None,
         capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Invoke git in `cwd` with optional env, returning the completed proc.

    Stdout/stderr are captured by default. We suppress git's pager
    explicitly via -c core.pager=cat to keep CI/non-tty output sane."""
    cmd = ["git", "-c", "core.pager=cat"] + args_list
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        cmd, cwd=str(cwd), env=env,
        capture_output=capture, text=True, check=check,
        # 2026-04-29 fix: force UTF-8 decoding regardless of OS locale
        # (Windows PowerShell CP949 was failing on em-dash bytes in
        # commit subjects). errors="replace" keeps crashes off the
        # critical path even if a non-UTF-8 byte slips through.
        encoding="utf-8", errors="replace",
    )


def _git_ok(args_list: list[str], *, cwd: Path = TARGET) -> bool:
    """Run git, return True iff exit code 0.

    BUG-FIX 2026-04-29: previously this always returned True whenever
    the subprocess merely ran (because `check=False` and the only
    `except` was for OSError). That caused `cmd_init` to take the
    `set-url` branch on a fresh repo where `origin` did not exist,
    resulting in `git remote set-url origin ...` exit 2.
    """
    try:
        r = _git(args_list, cwd=cwd, check=False)
        return r.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def _has_dotgit() -> bool:
    return (TARGET / ".git").exists()


def _assert_isolated_repo() -> None:
    """Refuse to operate if `Github/.git` is not the actual repo root.

    Smoking-gun check for the 2026-04-29 incident in which a malformed
    `Github/.git` (missing `objects/` subdir) caused git to walk up and
    discover the parent TECT2 repository, which then made `git add -A`
    inside `Github/` stage hundreds of parent-tree files. We assert
    `git rev-parse --show-toplevel` matches `TARGET.resolve()` -- if
    not, refuse to continue and instruct the operator to wipe and
    re-initialise `Github/.git`.
    """
    r = _git(["rev-parse", "--show-toplevel"], check=False)
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        raise RuntimeError(
            "REFUSED: `git rev-parse --show-toplevel` failed inside "
            "Github/. " + (r.stderr.strip() or "(no stderr)")
            + " -- wipe Github/.git and re-run init."
        )
    toplevel = Path(out).resolve()
    expected = TARGET.resolve()
    if toplevel != expected:
        raise RuntimeError(
            "REFUSED: Github/ is not its own isolated git repository. "
            "`git rev-parse --show-toplevel` = " + str(toplevel)
            + ", expected " + str(expected) + ". This means git "
            "auto-discovered a parent .git (typically because "
            "Github/.git is malformed -- missing objects/ or refs/ "
            "subtree). Wipe Github/.git and re-run init: \n"
            "    Remove-Item -Recurse -Force Github\\.git\n"
            "    python -u Codes\\tools\\github_sync_push.py init"
        )


# ---------------------------------------------------------------------
# Section C. Subcommands
# ---------------------------------------------------------------------
def cmd_status(args: argparse.Namespace) -> int:
    """No-network status report."""
    print("=" * 60)
    print(" GitHub publish — Layer 2 (push) — STATUS")
    print("=" * 60)
    print(f"  Github/ exists       : {TARGET.exists()}")
    print(f"  Github/.git exists   : {_has_dotgit()}")
    print(f"  config.json present  : {CONFIG.exists()}")
    print(f"  template present     : {TEMPLATE.exists()}")

    if CONFIG.exists():
        try:
            cfg = _load_config()
            _summarise_config(cfg)
        except ConfigError as e:
            print(f"  config error: {e}")

    if _has_dotgit():
        print()
        print("--- git status (in Github/) ---")
        r = _git(["status", "--short", "--branch"], check=False)
        sys.stdout.write(r.stdout)
        if r.stderr:
            sys.stderr.write(r.stderr)

        print("--- git remote -v ---")
        r = _git(["remote", "-v"], check=False)
        # Mask the URL in case operator embedded a token there.
        for line in r.stdout.splitlines():
            print("  " + _mask_token(line))
    else:
        print()
        print("Github/ is not a git working tree yet. Run:")
        print("  python -u Codes/tools/github_sync_push.py init")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Initialise Github/.git and set remote per config.

    Idempotent: if .git already exists, refreshes remote URL and exits."""
    try:
        cfg = _load_config()
    except ConfigError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    if not TARGET.exists():
        print(f"FAIL: {TARGET} does not exist. Run github_sync_curate.py first.",
              file=sys.stderr)
        return 1

    remote_url = cfg.get("remote_url", "")
    branch = cfg.get("publish_branch", "main")
    author = cfg.get("commit_author", {})
    if not remote_url:
        print("FAIL: remote_url is empty in config. Edit "
              f"{CONFIG.relative_to(REPO_ROOT)} first.", file=sys.stderr)
        return 1

    apply = bool(args.apply) or not cfg.get("dry_run_default", True)

    if not _has_dotgit():
        print(f"[init] git init -b {branch} {TARGET}")
        if apply:
            _git(["init", "-b", branch])
        else:
            print("       (dry-run: skipped -- re-run with --apply to execute)")
    else:
        # Github/.git is present -- but verify it is a VALID, isolated
        # repo and not a stub that causes git to walk up to the parent.
        try:
            _assert_isolated_repo()
            print("[init] Github/.git already present and isolated -- refreshing remote")
        except RuntimeError as e:
            print(f"[init] FAIL: {e}", file=sys.stderr)
            return 5

    print(f"[init] git remote set-url origin {_mask_token(remote_url)}")
    if apply:
        # `set-url` fails if remote doesn't exist yet; fall back to add.
        if _git_ok(["remote", "get-url", "origin"]):
            _git(["remote", "set-url", "origin", remote_url])
        else:
            _git(["remote", "add", "origin", remote_url])
        # Configure local user (does not affect global git config).
        if author.get("name"):
            _git(["config", "user.name", author["name"]])
        if author.get("email"):
            _git(["config", "user.email", author["email"]])
    else:
        print("       (dry-run: skipped)")

    if apply:
        print()
        print("OK: Github/.git initialised. Next step:")
        print("    python -u Codes/tools/github_sync_push.py commit --apply")
    else:
        print()
        print("DRY-RUN complete. To apply, re-run with --apply.")
    return 0


def _build_commit_message(cfg: dict) -> str:
    """Compose the public-mirror commit message."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    src_branch = "main"
    src_head = ""
    try:
        r = _git(["rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, check=False)
        src_head = r.stdout.strip()
    except Exception:
        pass
    parts = []
    parts.append(f"Public mirror auto-sync ({today})")
    parts.append("")
    parts.append("This commit is an automated mirror of the canonical TECT")
    parts.append("research repository, curated by")
    parts.append("Codes/tools/github_sync_curate.py and pushed by")
    parts.append("Codes/tools/github_sync_push.py.")
    if src_head:
        parts.append("")
        parts.append(f"Source repository HEAD: {src_branch}@{src_head}")
    parts.append("")
    parts.append("Substantive theory / code changes have their own commit")
    parts.append("history in the canonical repository; this mirror is a")
    parts.append("read-only public snapshot.")
    return "\n".join(parts) + "\n"


def cmd_commit(args: argparse.Namespace) -> int:
    """Stage all changes in Github/ and create a single commit."""
    try:
        cfg = _load_config()
    except ConfigError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if not _has_dotgit():
        print("FAIL: Github/.git missing. Run `init` subcommand first.",
              file=sys.stderr)
        return 1

    # Smoking-gun guard: refuse to operate if git resolves a parent .git
    # instead of Github/.git (cf. 2026-04-29 incident, malformed init).
    try:
        _assert_isolated_repo()
    except RuntimeError as e:
        print(f"[commit] FAIL: {e}", file=sys.stderr)
        return 5

    apply = bool(args.apply) or not cfg.get("dry_run_default", True)

    print("[commit] git add -A")
    print("[commit] git status --short --untracked-files=all")
    if apply:
        _git(["add", "-A"])
    r = _git(["status", "--short", "--untracked-files=all"], check=False)
    sys.stdout.write(r.stdout)
    if not r.stdout.strip():
        print("(working tree clean — nothing to commit.)")
        return 0

    msg = _build_commit_message(cfg)
    print()
    print("[commit] commit message:")
    for line in msg.splitlines():
        print("  | " + line)

    if apply:
        # We pass message via -F to avoid shell quoting issues.
        msg_file = TARGET / ".commit-msg.tmp"
        msg_file.write_text(msg, encoding="utf-8")
        try:
            r = _git(["commit", "-F", str(msg_file)], check=False)
            sys.stdout.write(r.stdout)
            if r.returncode != 0:
                sys.stderr.write(r.stderr)
                return r.returncode
        finally:
            try:
                msg_file.unlink()
            except OSError:
                pass
        print()
        print("OK: commit created. Next step:")
        print("    python -u Codes/tools/github_sync_push.py push --apply")
    else:
        print()
        print("DRY-RUN: not committed. Re-run with --apply to execute.")
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    """Push current branch to origin. Honours force-push safety gate."""
    try:
        cfg = _load_config()
    except ConfigError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if not _has_dotgit():
        print("FAIL: Github/.git missing. Run `init` first.", file=sys.stderr)
        return 1

    # Smoking-gun guard: refuse to operate if git resolves a parent .git
    # instead of Github/.git (cf. 2026-04-29 incident, malformed init).
    try:
        _assert_isolated_repo()
    except RuntimeError as e:
        print(f"[push] FAIL: {e}", file=sys.stderr)
        return 5

    apply = bool(args.apply) or not cfg.get("dry_run_default", True)
    branch = cfg.get("publish_branch", "main")
    force_in_cfg = bool(cfg.get("force_push", False))
    force_request = bool(args.force_push)
    force_confirm = bool(args.force_confirm)

    # Token-auth via env var (HTTPS) -- the token is injected into a
    # one-shot remote URL (https://x-access-token:${TOKEN}@github.com/...)
    # and passed as an explicit positional argument to `git push`. The
    # token NEVER lands in `Github/.git/config` (which is what would
    # happen if we did `git remote set-url origin <token-URL>`).
    auth = cfg.get("auth", {})
    push_target = "origin"
    if auth.get("method") == "https-token":
        token_var = auth.get("token_env_var", "GITHUB_TOKEN")
        token = os.environ.get(token_var)
        if not token:
            print(f"FAIL: auth.method = https-token but ${token_var} is not set.",
                  file=sys.stderr)
            return 3
        remote_url = cfg.get("remote_url", "")
        if not remote_url.startswith("https://"):
            print("FAIL: https-token auth requires remote_url to start with https://",
                  file=sys.stderr)
            return 4
        # Splice the token in at the URL credential slot.
        push_target = remote_url.replace(
            "https://", "https://x-access-token:" + token + "@", 1
        )

    push_cmd = ["push", push_target, branch]
    if force_request:
        if not (force_in_cfg and force_confirm):
            print("REFUSED: force-push requested but safety gate not satisfied.",
                  file=sys.stderr)
            print("         Both `force_push: true` in config AND `--force-confirm`",
                  file=sys.stderr)
            print("         flag are required.", file=sys.stderr)
            return 2
        # 2026-04-29 fix-attempt-2: use plain --force, not
        # --force-with-lease. Rationale: the publish-mirror semantic
        # is that the local Github/.git is REGENERATED on each publish
        # round and remote main is purely a publish target. After a
        # `Remove-Item -Recurse -Force Github\.git; init` round, local
        # shares NO history with remote. --force-with-lease then
        # refuses with "stale info" because there is no baseline. The
        # 3-key safety gate (force_push:true in config + --force-push
        # CLI flag + --force-confirm CLI flag) already guards against
        # accidental force-pushes; --force-with-lease's additional
        # protection does not apply because there is no other
        # contributor to this mirror.
        push_cmd.insert(1, "--force")

    # Echo a masked form of the command so the token never reaches stdout.
    masked_target = _mask_token(push_target) if push_target != "origin" else "origin"
    print("[push] git push " + masked_target + " " + branch
          + (" (force)" if force_request else ""))

    if apply:
        r = _git(push_cmd, check=False)
        if r.stdout:
            sys.stdout.write(_mask_token(r.stdout))
        if r.stderr:
            # Mask any token that may have leaked into git's stderr
            # (e.g. a remote URL printed by git itself).
            sys.stderr.write(_mask_token(r.stderr))
        if r.returncode != 0:
            print()
            print("FAIL: git push exited with code", r.returncode, file=sys.stderr)
            return r.returncode
        print()
        print("OK: pushed to origin/" + branch)
    else:
        print()
        print("DRY-RUN: not pushed. Re-run with --apply to execute.")
    return 0



# ---------------------------------------------------------------------
# Section D. GitHub REST API — repo metadata (About / Topics / Releases)
# ---------------------------------------------------------------------
GITHUB_API = "https://api.github.com"


def _github_api_request(method: str, path: str, *, token: str,
                        body: dict | None = None,
                        accept: str = "application/vnd.github+json"
                        ) -> tuple[int, dict | str]:
    """Minimal stdlib HTTP client (no `requests` dep).

    Returns (status_code, parsed_json_or_raw_text). Raises on transport
    errors, NOT on 4xx/5xx (caller decides). The Authorization header is
    set; the token never reaches stdout.
    """
    url = GITHUB_API + path
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TECT-publish-pipeline/1.0",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def render_repo_description() -> str:
    """The ~140-char repo About blurb. Auto-generated, English only."""
    return (
        "TECT -- Topological Energy Condensate Theory. "
        "Candidate Theory of Everything from a primordial 3D BCC "
        "topological condensate. CC BY 4.0."
    )


def render_repo_topics() -> list[str]:
    """Up to 20 lowercase, hyphen-only topics. GitHub validates server-side."""
    return [
        "theoretical-physics",
        "theory-of-everything",
        "topological-condensate",
        "bcc-lattice",
        "brazovskii",
        "grand-unified-theory",
        "gauge-theory",
        "quantum-field-theory",
        "lattice-gauge-theory",
        "mathematical-physics",
        "condensed-matter",
        "kibble-zurek",
        "asymptotic-safety",
        "open-science",
        "reproducibility",
        "cc-by-4-0",
    ]


def _parse_recent_theory_tags(n: int = 5) -> list[tuple[str, str]]:
    """Parse the top-n `[Theory] MathNN: ...` commits in the canonical
    repository for release-tag auto-creation. Returns list of (tag, title)
    tuples where tag = `mathNN` (lowercase) and title = the commit subject.
    """
    out: list[tuple[str, str]] = []
    try:
        r = _git(["log", "--oneline", f"-{n*4}", "--no-decorate"], cwd=REPO_ROOT, check=False)
    except Exception:
        return out
    pat = re.compile(r"^[0-9a-f]+\s+\[Theory\]\s+(Math\d+)\s*[:\-].*", re.IGNORECASE)
    for line in r.stdout.splitlines():
        m = pat.match(line.strip())
        if m:
            tag = m.group(1).lower()
            title = line.split(None, 1)[1].strip()
            if (tag, title) not in out:
                out.append((tag, title))
            if len(out) >= n:
                break
    return out


def cmd_meta(args: argparse.Namespace) -> int:
    """Update repo About + Topics + (optionally) auto-tag recent
    `[Theory] MathNN:` commits as GitHub Releases.

    Token requirement: fine-grained PAT with Metadata:write on the
    target repo. Without that scope the API returns 403 and the
    subcommand exits 6.
    """
    try:
        cfg = _load_config()
    except ConfigError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    auth = cfg.get("auth", {})
    if auth.get("method") != "https-token":
        print("FAIL: cmd_meta requires auth.method == 'https-token'.",
              file=sys.stderr)
        return 4
    token_var = auth.get("token_env_var", "GITHUB_TOKEN")
    token = os.environ.get(token_var)
    if not token:
        print(f"FAIL: ${token_var} is not set in the current shell.",
              file=sys.stderr)
        return 3

    owner = cfg.get("github_username", "")
    repo = cfg.get("github_repo", "")
    if not owner or not repo:
        print("FAIL: github_username / github_repo missing in config.",
              file=sys.stderr)
        return 1

    apply = bool(args.apply) or not cfg.get("dry_run_default", True)
    homepage = cfg.get("homepage", "https://tect.kr")

    description = render_repo_description()
    topics = render_repo_topics()

    print("=" * 60)
    print(" GitHub publish -- Layer 2 (meta) -- About + Topics + Releases")
    print("=" * 60)
    print(f"  owner / repo  : {owner}/{repo}")
    print(f"  description   : {description[:70]}...")
    print(f"  homepage      : {homepage}")
    print(f"  topics ({len(topics)}): " + ", ".join(topics[:5]) + " ...")
    print()

    if not apply:
        print("DRY-RUN: not applied. Re-run with --apply to execute.")
        return 0

    # --- 1) About (description + homepage) ---
    print("[meta 1/3] PATCH /repos/{owner}/{repo}  (description, homepage)")
    code, body = _github_api_request(
        "PATCH", f"/repos/{owner}/{repo}",
        token=token,
        body={"description": description, "homepage": homepage,
              "has_issues": True, "has_wiki": True}
    )
    if code != 200:
        print(f"  FAIL: HTTP {code}: {body if isinstance(body, str) else body.get('message', body)}",
              file=sys.stderr)
        return 6
    print(f"  OK: HTTP {code} -- About updated.")

    # --- 2) Topics ---
    print("[meta 2/3] PUT /repos/{owner}/{repo}/topics")
    code, body = _github_api_request(
        "PUT", f"/repos/{owner}/{repo}/topics",
        token=token, body={"names": topics},
        accept="application/vnd.github.mercy-preview+json"
    )
    if code != 200:
        print(f"  FAIL: HTTP {code}: {body if isinstance(body, str) else body.get('message', body)}",
              file=sys.stderr)
        return 6
    print(f"  OK: HTTP {code} -- {len(topics)} topics applied.")

    # --- 3) Auto-create GitHub Releases for recent [Theory] MathNN commits ---
    if not args.skip_releases:
        print("[meta 3/3] Auto-tag recent [Theory] MathNN commits as Releases")
        tags = _parse_recent_theory_tags(n=5)
        if not tags:
            print("  (no [Theory] MathNN commits in top 20 -- skipping)")
        for tag, title in tags:
            # Check if tag already exists
            chk_code, _ = _github_api_request(
                "GET", f"/repos/{owner}/{repo}/releases/tags/{tag}",
                token=token
            )
            if chk_code == 200:
                print(f"  - {tag}: already published, skipping.")
                continue
            elif chk_code != 404:
                print(f"  - {tag}: HTTP {chk_code} on existence check; skipping.")
                continue

            short_title = title[:80] + ("..." if len(title) > 80 else "")
            rel_body = (
                f"Annotated GitHub Release for canonical theory tag `{tag}`.\n\n"
                f"**Title**: {title}\n\n"
                f"This release is auto-generated by `Codes/tools/github_sync_push.py meta` "
                f"from the `[Theory] {tag}` commit subject in the canonical TECT repository. "
                f"For the substantive content of this milestone, refer to "
                f"`Docs/math/TECT-{tag.capitalize()}-*.tex.txt` in the source repository.\n\n"
                f"License: CC BY 4.0 (see `LICENSE`)."
            )
            create_code, body = _github_api_request(
                "POST", f"/repos/{owner}/{repo}/releases",
                token=token,
                body={
                    "tag_name": tag,
                    "name": short_title,
                    "body": rel_body,
                    "draft": False,
                    "prerelease": False,
                }
            )
            if create_code in (200, 201):
                print(f"  + {tag}: published.")
            else:
                msg = body if isinstance(body, str) else body.get("message", str(body))
                print(f"  - {tag}: HTTP {create_code}: {msg}")

    print()
    print("OK: metadata sync complete.")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Full pipeline: status -> commit -> push.

    Inherits --apply from caller. Each step prints its own banner."""
    rc = cmd_status(args)
    if rc != 0:
        return rc
    print()
    rc = cmd_commit(args)
    if rc != 0:
        return rc
    print()
    rc = cmd_push(args)
    return rc


# ---------------------------------------------------------------------
# Section D. Argument parsing
# ---------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_status = sub.add_parser("status", help="show local + config state (no network)")
    sp_status.set_defaults(func=cmd_status)

    sp_init = sub.add_parser("init", help="git init Github/ and set remote")
    sp_init.add_argument("--apply", action="store_true",
                         help="actually run (default is dry-run unless config says otherwise)")
    sp_init.set_defaults(func=cmd_init)

    sp_commit = sub.add_parser("commit", help="stage and commit Github/")
    sp_commit.add_argument("--apply", action="store_true")
    sp_commit.set_defaults(func=cmd_commit)

    sp_push = sub.add_parser("push", help="push to origin (network)")
    sp_push.add_argument("--apply", action="store_true")
    sp_push.add_argument("--force-push", action="store_true",
                         help="request a force-push (gate)")
    sp_push.add_argument("--force-confirm", action="store_true",
                         help="confirmation flag for force-push (gate)")
    sp_push.set_defaults(func=cmd_push)

    sp_meta = sub.add_parser("meta", help="update repo About + Topics + auto-tag Releases (network)")
    sp_meta.add_argument("--apply", action="store_true")
    sp_meta.add_argument("--skip-releases", action="store_true",
                         help="skip auto-creation of GitHub Releases")
    sp_meta.set_defaults(func=cmd_meta)

    sp_sync = sub.add_parser("sync", help="status + commit + push")
    sp_sync.add_argument("--apply", action="store_true")
    sp_sync.add_argument("--force-push", action="store_true")
    sp_sync.add_argument("--force-confirm", action="store_true")
    sp_sync.set_defaults(func=cmd_sync)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

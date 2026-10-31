#!/usr/bin/env python3
"""
Unified MCP & Skills Hub Auto-Sync Engine for Multi-Agent Environment.
Discovers MCP servers in ~/agents/MCP and skills in ~/agents/skills, then syncs them to:
  - Antigravity   (~/.gemini/config/mcp_config.json, ~/.gemini/config/skills)
  - Claude Code   (~/.claude.json, ~/.claude/skills)
  - Codex         (~/.codex/config.toml, ~/.codex/skills)
  - WorkBuddy     (~/.workbuddy/mcp.json, ~/.workbuddy/skills)
  - WorkBuddy AI  (~/.workbuddy-ai/skills)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 and below: fall back to the tomli backport
    import tomli as tomllib  # type: ignore[no-redef]
from pathlib import Path
from typing import Any

MCP_ROOT = Path.home() / "agents" / "MCP"
REGISTRY_FILE = MCP_ROOT / "registry.json"
SKILLS_ROOT = Path.home() / "agents" / "skills"
SKILL_MARKER = ".synced-from"

def _desktop_config_path() -> Path:
    """The Claude Desktop app's config. A 3p deployment keeps it under Claude-3p."""
    for name in ("Claude-3p", "Claude"):
        p = Path.home() / "Library" / "Application Support" / name / "claude_desktop_config.json"
        if p.parent.is_dir():
            return p
    return Path.home() / "Library" / "Application Support" / "Claude-3p" / "claude_desktop_config.json"


TARGETS = {
    "antigravity": {
        "name": "Antigravity",
        "path": Path.home() / ".gemini" / "config" / "mcp_config.json",
        "type": "json_mcp_servers",
    },
    "claude_code": {
        "name": "Claude Code",
        "path": Path.home() / ".claude.json",
        "type": "json_nested_mcp_servers",
    },
    "codex": {
        "name": "Codex",
        "path": Path.home() / ".codex" / "config.toml",
        "type": "toml_codex",
    },
    "workbuddy": {
        "name": "WorkBuddy",
        "path": Path.home() / ".workbuddy" / "mcp.json",
        "type": "json_mcp_servers",
    },
    "claude_desktop": {
        "name": "Claude Desktop",
        "path": _desktop_config_path(),
        "type": "json_mcp_servers",
    },
}


SKILL_TARGETS = {
    "antigravity": {
        "name": "Antigravity",
        "path": Path.home() / ".gemini" / "config" / "skills",
    },
    "claude_code": {
        "name": "Claude Code",
        "path": Path.home() / ".claude" / "skills",
    },
    "codex": {
        "name": "Codex",
        "path": Path.home() / ".codex" / "skills",
    },
    "workbuddy": {
        "name": "WorkBuddy",
        "path": Path.home() / ".workbuddy" / "skills",
    },
    "workbuddy_ai": {
        "name": "WorkBuddy AI",
        "path": Path.home() / ".workbuddy-ai" / "skills",
    },
}

# Directories that are never part of a skill payload.
SKILL_IGNORE_NAMES = {"node_modules", ".git", "__pycache__", ".DS_Store", ".venv", "venv"}


def _ignored_skill_entry(name: str) -> bool:
    return name in SKILL_IGNORE_NAMES or name.startswith(".DS_Store")


def discover_skills() -> dict[str, Path]:
    """Scan ~/agents/skills for skill directories (a dir containing SKILL.md)."""
    discovered: dict[str, Path] = {}
    if not SKILLS_ROOT.is_dir():
        return discovered

    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if not (entry / "SKILL.md").is_file():
            print(f"[!] Skipping {entry.name}: no SKILL.md", file=sys.stderr)
            continue
        discovered[entry.name] = entry

    return discovered


def _copy_skill_payload(src: Path, dest: Path) -> None:
    """Copy a skill directory, excluding caches and VCS noise."""
    dest.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if _ignored_skill_entry(entry.name):
            continue
        target = dest / entry.name
        if entry.is_dir():
            shutil.copytree(
                entry,
                target,
                symlinks=True,
                ignore=shutil.ignore_patterns(*SKILL_IGNORE_NAMES),
            )
        else:
            shutil.copy2(entry, target)


def sync_skills(target_path: Path, skills: dict[str, Path]) -> dict[str, int]:
    """Mirror ~/agents/skills into one agent's skills directory.

    Only directories carrying our .synced-from marker are ever replaced or
    removed, so skills installed by the agent itself are left untouched.
    Returns counters for reporting.
    """
    stats = {"copied": 0, "removed": 0, "skipped": 0}
    target_path.mkdir(parents=True, exist_ok=True)

    for name, src in skills.items():
        dest = target_path / name
        marker = dest / SKILL_MARKER

        if dest.exists() and not marker.is_file():
            print(
                f"        ! {name}: exists without {SKILL_MARKER} marker, leaving it alone",
                file=sys.stderr,
            )
            stats["skipped"] += 1
            continue

        try:
            if dest.is_dir():
                shutil.rmtree(dest)
            elif dest.exists():
                dest.unlink()
            _copy_skill_payload(src, dest)
            marker.write_text(str(src) + "\n", encoding="utf-8")
            stats["copied"] += 1
        except Exception as e:
            print(f"        ! {name}: copy failed: {e}", file=sys.stderr)
            stats["skipped"] += 1

    # Prune skills we synced earlier that no longer exist at the source.
    for entry in sorted(target_path.iterdir()):
        if not entry.is_dir() or entry.name in skills:
            continue
        marker = entry / SKILL_MARKER
        if marker.is_file() and not entry.name.startswith("."):
            try:
                shutil.rmtree(entry)
                stats["removed"] += 1
            except Exception as e:
                print(f"        ! {entry.name}: prune failed: {e}", file=sys.stderr)

    return stats


def sync_all_skills() -> None:
    skills = discover_skills()
    print(f"[*] Discovered {len(skills)} skill(s) in {SKILLS_ROOT}:")
    for name, src in skills.items():
        print(f"    - {name}: {src}")

    print("\n[*] Synchronizing skills to installed Agent configurations:")
    for key, target in SKILL_TARGETS.items():
        name = target["name"]
        path = target["path"]

        if not path.parent.is_dir():
            print(f"    [-] {name}: Skipped (home directory {path.parent} not found)")
            continue

        try:
            stats = sync_skills(path, skills)
            print(
                f"    [+] {name}: synced -> {path} "
                f"(copied={stats['copied']}, removed={stats['removed']}, "
                f"skipped={stats['skipped']})"
            )
        except Exception as e:
            print(f"    [!] {name}: Failed to sync skills: {e}", file=sys.stderr)


def discover_servers() -> dict[str, dict[str, Any]]:
    """Scan ~/agents/MCP for MCP server declarations."""
    discovered: dict[str, dict[str, Any]] = {}

    # 1. Central registry file if present
    if REGISTRY_FILE.is_file():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    reg_servers = data.get("mcpServers", data)
                    if isinstance(reg_servers, dict):
                        for k, v in reg_servers.items():
                            if isinstance(v, dict):
                                discovered[k] = v
        except Exception as e:
            print(f"[!] Warning reading registry.json: {e}", file=sys.stderr)

    # 2. Directory scan in ~/agents/MCP
    if MCP_ROOT.is_dir():
        for entry in sorted(MCP_ROOT.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue

            server_name = entry.name

            # Check for manifest files
            manifest_path = None
            for candidate in (".mcp.json", "mcp.json"):
                cand_path = entry / candidate
                if cand_path.is_file():
                    manifest_path = cand_path
                    break

            if manifest_path:
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    if "mcpServers" in cfg and isinstance(cfg["mcpServers"], dict):
                        for k, v in cfg["mcpServers"].items():
                            discovered[k] = v
                    elif "command" in cfg:
                        discovered[server_name] = cfg
                    continue
                except Exception as e:
                    print(f"[!] Warning reading {manifest_path}: {e}", file=sys.stderr)

            # Check for standard executable runner
            runner = entry / "run-mcp.sh"
            if runner.is_file() and os.access(runner, os.X_OK):
                discovered[server_name] = {
                    "command": str(runner.resolve()),
                    "args": [],
                }

    return discovered


def backup_file(path: Path) -> None:
    if path.is_file():
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)


def sync_antigravity(target_path: Path, servers: dict[str, Any]) -> bool:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if target_path.is_file() and target_path.stat().st_size > 0:
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    mcp_servers = existing.get("mcpServers", {})
    mcp_servers.update(servers)
    existing["mcpServers"] = mcp_servers

    backup_file(target_path)
    tmp_path = target_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(target_path)
    return True


def sync_claude_code(target_path: Path, servers: dict[str, Any]) -> bool:
    if not target_path.parent.is_dir():
        return False
    existing: dict[str, Any] = {}
    if target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    mcp_servers = existing.get("mcpServers", {})
    mcp_servers.update(servers)
    existing["mcpServers"] = mcp_servers

    backup_file(target_path)
    tmp_path = target_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(target_path)
    return True


def sync_workbuddy(target_path: Path, servers: dict[str, Any]) -> bool:
    if not target_path.parent.is_dir():
        return False
    existing: dict[str, Any] = {}
    if target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    mcp_servers = existing.get("mcpServers", {})
    mcp_servers.update(servers)
    existing["mcpServers"] = mcp_servers

    backup_file(target_path)
    tmp_path = target_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(target_path)
    return True


def sync_codex(target_path: Path, servers: dict[str, Any]) -> bool:
    if not target_path.is_file():
        return False

    with open(target_path, "rb") as f:
        raw_text = f.read().decode("utf-8")
        parsed = tomllib.loads(raw_text)

    existing_mcp = parsed.get("mcp_servers", {})

    # Check if servers already up to date
    # Build updated text by updating or appending sections
    backup_file(target_path)

    # For each server in servers:
    lines = raw_text.splitlines()
    for name, cfg in servers.items():
        command = cfg.get("command", "")
        args = cfg.get("args", [])
        env = cfg.get("env", {})

        # Remove existing [mcp_servers.<name>] block if present
        section_header = f"[mcp_servers.{name}]"
        sub_env_header = f"[mcp_servers.{name}.env]"

        new_lines: list[str] = []
        skip = False
        for line in lines:
            stripped = line.strip()
            if stripped == section_header or stripped == sub_env_header:
                skip = True
                continue
            if skip and stripped.startswith("[") and not stripped.startswith(f"[mcp_servers.{name}"):
                skip = False
            if not skip:
                new_lines.append(line)
        lines = new_lines

        # Append new block
        block = [
            f"[mcp_servers.{name}]",
            f"command = {json.dumps(command)}",
            f"args = {json.dumps(args)}",
        ]
        if env:
            block.append(f"[mcp_servers.{name}.env]")
            for k, v in env.items():
                block.append(f"{k} = {json.dumps(str(v))}")

        lines.extend(["", *block])

    tmp_path = target_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")
    tmp_path.replace(target_path)
    return True


def sync_all() -> None:
    servers = discover_servers()
    print(f"[*] Discovered {len(servers)} MCP server(s) in {MCP_ROOT}:")
    for s_name, s_cfg in servers.items():
        print(f"    - {s_name}: command={s_cfg.get('command')} args={s_cfg.get('args', [])}")

    print("\n[*] Synchronizing to installed Agent configurations:")
    for key, target in TARGETS.items():
        name = target["name"]
        path = target["path"]
        t_type = target["type"]

        if not path.parent.is_dir():
            print(f"    [-] {name}: Skipped (home directory {path.parent} not found)")
            continue

        try:
            if t_type == "json_mcp_servers":
                if key in ("antigravity", "claude_desktop"):
                    sync_antigravity(path, servers)
                elif key == "workbuddy":
                    sync_workbuddy(path, servers)
            elif t_type == "json_nested_mcp_servers":
                sync_claude_code(path, servers)
            elif t_type == "toml_codex":
                sync_codex(path, servers)
            print(f"    [+] {name}: Synced successfully -> {path}")
        except Exception as e:
            print(f"    [!] {name}: Failed to sync: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified MCP & Skills Hub Auto-Sync Tool for AI Agents")
    parser.add_argument("--list", action="store_true", help="List discovered MCP servers and skills without syncing")
    parser.add_argument("--mcp", action="store_true", help="Sync MCP servers only")
    parser.add_argument("--skills", action="store_true", help="Sync skills only")
    args = parser.parse_args()

    if args.list:
        servers = discover_servers()
        print(f"Discovered {len(servers)} MCP server(s):")
        for k, v in servers.items():
            print(f"  [{k}] -> {v}")
        print()
        skills = discover_skills()
        print(f"Discovered {len(skills)} skill(s) in {SKILLS_ROOT}:")
        for k, v in skills.items():
            print(f"  [{k}] -> {v}")
        return

    # Default: sync both. Explicit flags narrow the run to one kind.
    do_mcp = args.mcp or not args.skills
    do_skills = args.skills or not args.mcp

    if do_mcp:
        sync_all()
    if do_mcp and do_skills:
        print()
    if do_skills:
        sync_all_skills()


if __name__ == "__main__":
    main()

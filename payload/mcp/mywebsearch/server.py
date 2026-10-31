#!/usr/bin/env python3
"""
mywebsearch MCP Server
=======================
解决 Claude Desktop 内置 web_search 在上游（opendesign / DeepSeek 网关）
只接受非流式搜索、而 CLI 强制流式导致 400 的问题。

本服务器自行以 stream=False 调用上游 /v1/messages 的 web_search_20250305
服务端工具，因此不依赖调用方是否流式。

配置来源（按优先级）：
  1. 环境变量 DS_BASE_URL / DS_API_KEY / DS_MODEL
  2. ~/.cc-switch/cc-switch.db 中当前 claude-desktop 供应商
"""
from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mywebsearch")

CC_DB = Path.home() / ".cc-switch" / "cc-switch.db"
CC_SETTINGS = Path.home() / ".cc-switch" / "settings.json"


def _candidates() -> list[dict[str, Any]]:
    """从 CC Switch 读取所有可用供应商，并按优先级排序。

    优先级（2026-10-17 用户要求）：
      1. 显式环境变量 DS_BASE_URL / DS_API_KEY
      2. 当前选中的供应商（currentProviderClaudeDesktop / is_current）
      3. 其它非 DeepSeek 供应商
      4. DeepSeek 直连 —— 仅作为最终保底
    """
    env_base = os.environ.get("DS_BASE_URL", "").strip()
    env_key = os.environ.get("DS_API_KEY", "").strip()
    env_model = os.environ.get("DS_MODEL", "").strip()
    prefer = os.environ.get("DS_PREFER_PROVIDER", "").strip().lower()
    allow_ds_fallback = os.environ.get("DS_FALLBACK_TO_DEEPSEEK", "1").lower() not in ("0", "false", "no")

    out: list[dict[str, Any]] = []

    if env_base and env_key:
        out.append({
            "base_url": env_base.rstrip("/"),
            "api_key": env_key,
            "model": env_model or "deepseek-v4.1-flash",
            "provider": "env(DS_BASE_URL)",
            "tier": 1,
            "is_deepseek": "api.deepseek.com" in env_base,
        })
        return out

    if not CC_DB.is_file():
        return out

    pid = None
    try:
        if CC_SETTINGS.is_file():
            pid = json.loads(CC_SETTINGS.read_text()).get("currentProviderClaudeDesktop")
    except Exception:
        pass

    con = sqlite3.connect(str(CC_DB))
    try:
        rows = con.execute(
            "SELECT id, name, settings_config, meta, is_current FROM providers "
            "WHERE app_type='claude-desktop'"
        ).fetchall()
    finally:
        con.close()

    def usable(row) -> bool:
        e = (json.loads(row[2] or "{}") or {}).get("env", {}) or {}
        return bool(e.get("ANTHROPIC_BASE_URL") and e.get("ANTHROPIC_AUTH_TOKEN"))

    for row in rows:
        if not usable(row):
            continue
        pid_row, name, cfg, meta, is_current = row
        e = (json.loads(cfg or "{}") or {}).get("env", {}) or {}
        base = (e.get("ANTHROPIC_BASE_URL") or "").rstrip("/")
        key = (e.get("ANTHROPIC_AUTH_TOKEN") or "").strip()
        routes = (json.loads(meta or "{}") or {}).get("claudeDesktopModelRoutes", {}) or {}
        model = (routes.get("claude-sonnet-5") or {}).get("model", "") or "deepseek-v4.1-flash"

        ident = f"{name} {base}".lower()
        is_deepseek = "api.deepseek.com" in base
        is_selected = pid_row == pid or bool(is_current)
        # 可选：用 DS_PREFER_PROVIDER 额外指定优先供应商
        is_preferred = bool(prefer) and prefer in ident

        if is_preferred:
            tier = 2
        elif is_selected and not is_deepseek:
            tier = 3
        elif not is_deepseek:
            tier = 4
        else:
            tier = 5  # DeepSeek 直连：最终保底

        if tier == 5 and not allow_ds_fallback:
            continue

        out.append({
            "base_url": base,
            "api_key": key,
            "model": model if not env_model else env_model,
            "provider": name,
            "tier": tier,
            "is_deepseek": is_deepseek,
            "is_current": is_selected,
        })

    out.sort(key=lambda c: (c["tier"], 0 if c.get("is_current") else 1))
    return out


def _resolve() -> dict[str, Any]:
    """返回当前应使用的上游配置（含 provider 名称与是否保底）。"""
    cands = _candidates()
    if not cands:
        raise RuntimeError(
            "未找到可用上游。请设置 DS_BASE_URL / DS_API_KEY，"
            "或确保 ~/.cc-switch/cc-switch.db 中存在配置完整的供应商。"
        )
    return cands[0]


def _call(payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    cfg = _resolve()
    base, key = cfg["base_url"], cfg["api_key"]
    if not base or not key:
        raise RuntimeError("未找到上游配置。")
    req = urllib.request.Request(
        base + "/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": key,
            "authorization": "Bearer " + key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"上游 HTTP {e.code}: {body[:400]}") from None



def _official_base(cfg: dict[str, Any]) -> str:
    """从供应商配置推导官方 API 根地址（去掉 /anthropic 等后缀）。"""
    base = cfg["base_url"]
    for suffix in ("/anthropic", "/v1/messages", "/v1"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base.rstrip("/")


def _official_search(cfg: dict[str, Any], query: str, count: int) -> dict[str, Any]:
    """DeepSeek 官方 /v1/tools/search —— 结构化结果，质量高于模型总结。"""
    url = _official_base(cfg) + "/v1/tools/search"
    body = {"query": query, "count": max(1, min(count, 10)), "need_content": False}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + cfg["api_key"], "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"官方 Search API HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}") from None


def _official_fetch(cfg: dict[str, Any], url: str) -> dict[str, Any]:
    """DeepSeek 官方 /v1/tools/fetch —— 返回干净的 Markdown 正文。"""
    req = urllib.request.Request(
        _official_base(cfg) + "/v1/tools/fetch",
        data=json.dumps({"url": url}).encode(),
        headers={"Authorization": "Bearer " + cfg["api_key"], "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"官方 Fetch API HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}") from None


@mcp.tool()
def myweb_search(query: str, count: int = 5) -> str:
    """联网搜索网页，返回标题、链接与摘要。

    自动按上游能力分流：
      - DeepSeek 官方（兜底）→ 调用专用 /v1/tools/search，返回结构化结果
        （含 rerank_score / authority / summary），质量最高
      - 其它供应商（如 opendesign）→ 走 /v1/messages 的 web_search 服务端工具

    Args:
        query: 搜索词。支持 site: / -site: / "精确短语" / after: / before: 等语法。
        count: 最多返回多少条结果（1-10）。
    """
    cfg = _resolve()
    n = max(1, min(count, 10))

    # ---- 路径 A：DeepSeek 官方专用搜索 API ----
    if cfg.get("is_deepseek"):
        data = _official_search(cfg, query, n)
        results = []
        for r in data.get("results", [])[:n]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "summary": (r.get("summary") or r.get("snippet") or "")[:800],
                "rerank_score": round(float(r.get("rerank_score") or 0), 3),
                "authority": r.get("authority"),
                "site_name": r.get("site_name"),
                "date": r.get("date"),
            })
        return json.dumps({
            "query": query,
            "via": cfg["provider"],
            "api": "/v1/tools/search",
            "result_count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2)

    # ---- 路径 B：第三方网关的 web_search 工具 ----
    model = cfg["model"]
    resp = _call({
        "model": model,
        "max_tokens": 4096,
        "stream": False,  # ★ 必须非流式
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": n}],
        "messages": [{"role": "user", "content":
            f"请联网搜索并回答：{query}\n\n严格只返回搜索结果，不要编造。"}],
    })

    results: list[dict[str, Any]] = []
    answer_parts: list[str] = []
    for block in resp.get("content", []):
        btype = block.get("type")
        if btype == "web_search_tool_result":
            content = block.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("url"):
                        # 上游只返回 encrypted_content，无摘要字段
                        results.append({"title": item.get("title", ""), "url": item.get("url", "")})
        elif btype == "text":
            answer_parts.append(block.get("text", ""))

    dedup: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            dedup.append(item)

    return json.dumps({
        "query": query,
        "via": cfg["provider"],
        "api": "/v1/messages (web_search tool)",
        "model": model,
        "result_count": len(dedup),
        "results": dedup[:n],
        "answer": "\n".join(answer_parts).strip()[:4000],
    }, ensure_ascii=False, indent=2)


def _html_to_text(html: str) -> tuple[str, str]:
    """把 HTML 转成 (标题, 纯文本/Markdown)。只用标准库，避免额外依赖。"""
    import html as _html
    import re

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        title = _html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()

    # 去掉不可见/无内容区块
    for tag in ("script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form"):
        html = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", " ", html, flags=re.S | re.I)

    # 保留结构：标题/段落/列表/换行
    html = re.sub(r"<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", html, flags=re.I)
    html = re.sub(r"</h[1-6]>", "\n", html, flags=re.I)
    html = re.sub(r"<li[^>]*>", "\n- ", html, flags=re.I)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</(p|div|tr|section|article|ul|ol|table)>", "\n", html, flags=re.I)
    html = re.sub(r"<td[^>]*>", " | ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", "", html)

    text = _html.unescape(html)
    text = re.sub(r"[ \t\u00a0]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    noise = ("跳到主要内容", "Skip to main content", "本页目录", "Toggle navigation")
    cleaned = []
    for ln in lines:
        if ln in noise:
            continue
        if len(ln) <= 2 and not ln.startswith("#"):
            continue
        cleaned.append(ln)

    if title and cleaned and cleaned[0] == title:
        cleaned = cleaned[1:]

    return title, "\n".join(cleaned).strip()


@mcp.tool()
def myweb_fetch(url: str, max_chars: int = 20000) -> str:
    """抓取网页并转换为 Markdown/纯文本。

    自动分流：
      - DeepSeek 官方（兜底）→ /v1/tools/fetch，返回干净 Markdown
      - 其它供应商 → 上游无服务端 web_fetch，由 MCP 自行 HTTP 抓取并转文本

    Args:
        url: 要抓取的完整 HTTP/HTTPS 地址。
        max_chars: 返回正文的最大字符数，默认 20000。
    """
    import re

    if not re.match(r"^https?://", url, re.I):
        raise RuntimeError("url 必须以 http:// 或 https:// 开头")

    # DeepSeek 官方（兜底）：用专用 /v1/tools/fetch，返回干净 Markdown
    cfg = _resolve()
    if cfg.get("is_deepseek"):
        data = _official_fetch(cfg, url)
        content = data.get("content", "")
        return json.dumps({
            "url": url,
            "via": cfg["provider"],
            "api": "/v1/tools/fetch",
            "title": data.get("title", ""),
            "length": len(content),
            "truncated": len(content) > max_chars,
            "content": content[:max_chars],
        }, ensure_ascii=False, indent=2)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
            charset = "utf-8"
            ctype = r.headers.get("content-type", "") or ""
            m = re.search(r"charset=([\w-]+)", ctype, re.I)
            if m:
                charset = m.group(1)
            else:
                m2 = re.search(rb"charset=[\"']?([\w-]+)", raw[:4096], re.I)
                if m2:
                    charset = m2.group(1).decode("ascii", "ignore")
            html_text = raw.decode(charset, "replace")
            final_url = r.geturl()
            status = r.status
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"抓取失败 HTTP {e.code}: {url}") from None
    except Exception as e:
        raise RuntimeError(f"抓取失败 {type(e).__name__}: {e}") from None

    title, text = _html_to_text(html_text)
    truncated = len(text) > max_chars
    return json.dumps({
        "url": url,
        "final_url": final_url,
        "status": status,
        "title": title,
        "length": len(text),
        "truncated": truncated,
        "content": text[:max_chars],
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()

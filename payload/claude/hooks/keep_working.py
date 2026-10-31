#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keep_working.py — 长任务保活钩子（Claude Code / Claude Desktop Code tab 通用）

机制：
  * UserPromptSubmit：重置本回合计数，并注入一条"长任务模式"上下文。
  * Stop：模型想结束回合时检查
      1) 最近的 mcp__ccd_turn__update_plan 任务清单是否还有 pending/in_progress；
      2) 最后一条 assistant 文本是否以"继续/接下来我/Let me continue…"这类
         续跑声明结尾（且内容很短——真正的长答案不算）。
    命中且本回合未超过续跑上限（默认 6 次）时，输出 decision=block + reason，
    强制模型继续工作；否则放行。
  * 最后一条文本里带问号（在等用户回答）或含 TASK_COMPLETE 标记时直接放行。

安全：任何异常一律放行（exit 0），绝不因钩子本身阻断对话。
日志：~/.claude/hooks/keep_working.log
"""

import json
import os
import re
import sys
import time

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
STATE_DIR = os.path.join(HOOKS_DIR, "state")
LOG_PATH = os.path.join(HOOKS_DIR, "keep_working.log")
MAX_BLOCKS = 5  # 每个用户回合最多自动续跑次数（用户要求：最多尝试 5 次）

CONT_TAIL = re.compile(
    r"(继续推进|继续执行|"
    r"继续[：:]\s*\S|"
    r"继续(做|看|处理|验证|跑|检查|实现|修复|写)?[。.!！]?$|"
    r"接下来(我|就|会|将)|下面(我|就)|接着(做|来|执行|验证)|"
    r"现在(就|来|开始)|"
    r"Let me continue|I'?ll continue|Continuing with|Now I'?ll)",
    re.IGNORECASE,
)
# 弱续跑语：只在"短消息 + 结尾从句 + 非引用提及"时才算，避免总结里提到「然后…」被误判
CONT_WEAK = re.compile(r"(然后|随后|下一步)[^。！？!?]{0,60}[。…!！]?\s*$")
QUOTED_WEAK = re.compile(r"[「“\"'](然后|随后|下一步)")
DONE_MARKERS = ("TASK_COMPLETE", "任务已完成", "全部完成", "收工")


def log(msg: str) -> None:
    try:
        os.makedirs(HOOKS_DIR, exist_ok=True)
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {msg}\n")
    except Exception:
        pass


def state_path(session_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return os.path.join(STATE_DIR, safe + ".json")


def load_state(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(path: str, st: dict) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception:
        pass


def read_transcript(path: str) -> list:
    lines = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    lines.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return lines


def replay_plan(lines: list) -> list:
    """重放 update_plan 调用，返回当前状态列表。"""
    plan = []
    for d in lines:
        if d.get("type") != "assistant":
            continue
        for b in d.get("message", {}).get("content", []) or []:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name = str(b.get("name", ""))
            if not name.endswith("update_plan"):
                continue
            inp = b.get("input") or {}
            items = inp.get("items")
            if isinstance(items, list):
                plan = []
                for it in items:
                    if isinstance(it, dict):
                        plan.append(str(it.get("status", "pending")))
                    else:
                        plan.append("pending")
            done = inp.get("done")
            if isinstance(done, list):
                for n in done:
                    if isinstance(n, int) and 1 <= n <= len(plan):
                        plan[n - 1] = "completed"
            start = inp.get("start")
            if isinstance(start, int) and 1 <= start <= len(plan):
                if plan[start - 1] != "completed":
                    plan[start - 1] = "in_progress"
            if inp.get("advance"):
                for i, s in enumerate(plan):
                    if s in ("in_progress", "pending"):
                        plan[i] = "completed"
                        for j in range(i + 1, len(plan)):
                            if plan[j] == "pending":
                                plan[j] = "in_progress"
                                break
                        break
    return plan


def last_text_from_transcript(lines: list) -> str:
    for d in reversed(lines):
        if d.get("type") != "assistant":
            continue
        texts = []
        for b in d.get("message", {}).get("content", []) or []:
            if isinstance(b, dict) and b.get("type") == "text":
                texts.append(b.get("text", ""))
        if texts:
            return "\n".join(texts)
    return ""


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    event = data.get("hook_event_name") or data.get("hookEventName") or ""
    session_id = str(data.get("session_id") or "")
    spath = state_path(session_id)

    # 熔断：wrapper 连续检测到 5 次钩子失败后写下的标记 —— 本会话不再干预
    if os.path.exists(spath + ".disabled"):
        log(f"DISABLED-SKIP session={session_id}")
        return 0

    if event == "UserPromptSubmit":
        save_state(spath, {"blocks": 0})
        log(f"UPS session={session_id}")
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "【长任务模式】这是一个需要持续执行的任务：在任务清单全部完成前不要结束回合；"
                    "不要用\"接下来…/继续…\"作为收尾——直接调用工具把下一步做掉；"
                    "只有任务确实完成、或必须由用户提供信息时才能停下。"
                    "若 Stop 钩子打回、或看到「Stop hook failed」提示，说明检测到未完成工作，"
                    "请立即继续，不要复述已写内容。"
                ),
            }
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0

    # —— 第二层兜底：wrap_up 预检 ——
    # 即使 Stop 钩子没有生效（引擎版本差异/执行失败），也不允许在清单未完成时用
    # wrap_up 收尾——该工具的结果会明确告诉模型"回合到此结束"，是最强的提前收尾信号。
    if event == "PreToolUse":
        tool_name = str(data.get("tool_name") or "")
        if tool_name.endswith("wrap_up"):
            transcript_path = data.get("transcript_path") or ""
            plan = replay_plan(read_transcript(transcript_path)) if transcript_path else []
            pending = sum(1 for s in plan if s in ("pending", "in_progress"))
            if pending > 0:
                log(f"WRAPUP-DENY session={session_id} pending={pending}")
                sys.stderr.write(
                    f"任务清单还有 {pending} 项未完成，现在不能收尾。继续执行未完成项；"
                    "只有全部完成或必须由用户提供信息时才可调用 wrap_up。\n")
                return 2
        return 0

    if event == "PostToolUse":
        tool_name = str(data.get("tool_name") or "")
        if tool_name.endswith("update_plan"):
            transcript_path = data.get("transcript_path") or ""
            plan = replay_plan(read_transcript(transcript_path)) if transcript_path else []
            pending = sum(1 for s in plan if s in ("pending", "in_progress"))
            if pending > 0:
                out = {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            f"【任务未完成】清单还有 {pending} 项 pending/in_progress："
                            "按顺序继续执行，全部勾完之前不要结束回合。"
                        ),
                    }
                }
                print(json.dumps(out, ensure_ascii=False))
        return 0

    if event != "Stop":
        return 0

    st = load_state(spath)
    blocks = int(st.get("blocks", 0))

    transcript_path = data.get("transcript_path") or ""
    text = data.get("last_assistant_message") or ""
    if not text and transcript_path:
        lines = read_transcript(transcript_path)
        text = last_text_from_transcript(lines)
        plan = replay_plan(lines)
    else:
        plan = []
        if transcript_path:
            plan = replay_plan(read_transcript(transcript_path))

    pending = sum(1 for s in plan if s in ("pending", "in_progress"))
    tail = text.strip()[-160:]
    short = len(text.strip()) < 900
    cont_tail = bool(short and tail and CONT_TAIL.search(tail))
    if not cont_tail and len(text.strip()) < 600 and CONT_WEAK.search(tail) and not QUOTED_WEAK.search(tail):
        cont_tail = True
    awaiting_user = bool(re.search(r"[?？]\s*$", text.strip()[-120:]))
    done = any(m in text for m in DONE_MARKERS)

    incomplete = (pending > 0 or cont_tail) and not awaiting_user and not done

    if incomplete and blocks < MAX_BLOCKS:
        st["blocks"] = blocks + 1
        save_state(spath, st)
        if pending > 0:
            why = f"任务清单还有 {pending} 项未完成"
        else:
            why = "你上一条消息声称还要继续（以续跑语收尾），但回合提前结束了"
        reason = (
            f"{why}。请立即继续执行：直接调用工具推进下一步，不要复述已经写过的内容，"
            "不要再次以\"接下来…\"收尾；完成全部工作后再停，若确实需要用户提供信息请明确提问。"
        )
        log(f"STOP-BLOCK session={session_id} blocks={st['blocks']} pending={pending} cont_tail={cont_tail}")
        # 用 exit 2 + stderr 的通用契约（JSON decision 在部分版本里会被标成 hook failed）
        sys.stderr.write(reason + "\n")
        return 2

    if incomplete and blocks >= MAX_BLOCKS:
        log(f"STOP-ALLOW(cap) session={session_id} blocks={blocks} pending={pending}")
    else:
        log(f"STOP-ALLOW session={session_id} pending={pending} cont_tail={cont_tail} awaiting_user={awaiting_user} done={done}")
    st["blocks"] = 0
    save_state(spath, st)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)

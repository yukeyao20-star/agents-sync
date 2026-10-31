# sync_agent_config — 跨设备 Agent 配置同步记忆

> 版本：v1（2026-10-31）· 维护：本机 Claude Code（Desktop Code tab）
> 位置：`~/agents/sync/sync_agent_config.md`（本文件即同步源；远端见 §1）
> 读者：**其他设备的 agent**。请先通读，再结合本机操作系统与已装工具**自行决定最优实现**；
> 本文只描述"本机是怎么配的、为什么这样配、怎么验收"，不提供照抄即用的脚本。

---

## 0. 使用规则（给其他设备的 agent）

1. 本文件是**配置意图与验收标准的唯一来源**，不是逐字执行的剧本。路径、解释器、shell 语法按本机环境适配。
2. 修改任何机器配置前先向用户确认；配置完成后按 §6 逐项验证。
3. 本机缺少某个前提（没有 miniconda、没有某个 MCP 运行时）时**降级而不是照搬**，并在 §7 记录本机差异。
4. 任何"一次配置、多设备/多 agent 复用"的新配置，用户确认后补充进本文件（见 `~/agents/agent.md` §10.5）。
5. 本文件**不含任何密钥**，token 一律 `${ENV_NAME}` 占位。
6. **不纳入同步**：模型供应商/CC Switch 路由、API token、本机绝对路径的软件安装位置——这些属于"每台机器自己的选择"。

---

## 1. 同步机制

- **源文件**：`~/agents/sync/sync_agent_config.md`。
- **远端主仓**：`git@jpvps:~/repos/agents-sync.git`（jpvps = 64.83.53.106；域名 VPS 的 TCP 从本机被阻断，不可用作主仓）。
- **可选镜像**：GitHub 私有仓库；域名 VPS 可在 Cloudflare 后挂只读副本。
- **流程**：
  - 本机改动 → 更新本 md → `git add/commit/push`；
  - 其他设备 → `git pull` → agent 阅读本 md → 本机适配 → 若产生本机差异，更新 §7 并 push 回来；
  - 冲突以"最新一次人工确认"为准，不确定就保留两侧并询问用户。
- **新设备初始化**：
  ```bash
  git clone git@jpvps:~/repos/agents-sync.git ~/agents/sync
  ```
  随后让本机 agent 阅读 `~/agents/sync/sync_agent_config.md` 并按 §3 适配。

---

## 2. 本机（macOS，Apple Silicon）配置全景

### 2.1 Claude Code 基础

- 配置目录：`~/.claude/`
- 关键文件：`settings.json`（环境变量/hooks/权限/模型/autoCompact/插件）、`CLAUDE.md`（常驻规则）、`hooks/keep_working.{py,sh}`（§2.3）、`skills/`。

- `settings.json` 关键内容（**已脱敏**；hooks 见 §2.3）：
```json
{
  "env": {
    "CLAUDE_CODE_MODEL_CAPABILITIES": "${CLAUDE_CODE_MODEL_CAPABILITIES}",
    "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "${CLAUDE_CODE_MAX_CONTEXT_TOKENS}",
    "ANTHROPIC_AUTH_TOKEN": "${ANTHROPIC_AUTH_TOKEN}",
    "ANTHROPIC_BASE_URL": "https://amr-link.open-design.ai",
    "ANTHROPIC_DEFAULT_FABLE_MODEL": "deepseek-v4-pro[1M]",
    "ANTHROPIC_DEFAULT_FABLE_MODEL_NAME": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "mimo-v2.6-flash[1M]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.3-flash[1M]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_NAME": "glm-5.3-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4.1-flash[1M]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_NAME": "deepseek-v4.1-flash",
    "ANTHROPIC_MODEL": "deepseek-v4.1-flash",
    "DASHSCOPE_BASE_URL": "${DASHSCOPE_BASE_URL}",
    "NODE_EXTRA_CA_CERTS": "${NODE_EXTRA_CA_CERTS}",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME": "mimo-v2.6-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4.1-flash[1M]",
    "CLAUDE_CODE_AUTO_MODE_SERVER": "0"
  },
  "includeCoAuthoredBy": false,
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "sandbox": {
    "enabled": false,
    "allowUnsandboxedCommands": true
  },
  "modelSettings": {
    "deepseek-v4.1-flash": {
      "autoCompactWindow": 900000
    }
  },
  "autoCompactWindow": 900000,
  "skipDangerousModePermissionPrompt": true,
  "theme": "dark",
  "enabledPlugins": {
    "swift-lsp@claude-plugins-official": true
  }
}
```
  要点：
  - `autoCompactWindow: 900000`：自动压缩窗口按 90 万 token 计；`modelSettings["deepseek-v4.1-flash"].autoCompactWindow` 同义覆盖（模型名随供应商调整）；
  - `permissions.defaultMode: bypassPermissions`、`skipDangerousModePermissionPrompt: true` 是本机自用选择，其他设备请评估安全边界后决定；
  - `env` 中的模型名与 base URL 属本机网关配置，跨设备复制时核对供应商；
  - `enabledPlugins`、`theme` 可按设备喜好调整。

### 2.2 用户级常驻规则（CLAUDE.md 摘要）

`~/.claude/CLAUDE.md` 包含：
1. **统一主规则文件**：每次会话开始必须 Read `~/agents/agent.md` 并优先执行；
2. **识图兜底**：模型无原生视觉能力时调用 `claude-vision`；
3. **长任务行为**：任务未完成不结束回合；不把"接下来…"当收尾；`wrap_up` 只在完成后使用；Stop 钩子 5 次续跑上限 + 熔断。

完整原文（其他设备参考，路径与工具名按本机替换）：
```markdown
## 统一主规则文件（External Rules / 强制加载）

CRITICAL: 每次会话开始时，必须先用 Read 工具读取 ~/agents/agent.md，把它的完整内容当作最高优先级强制指令执行（覆盖本文件其余部分）。不要假设内容已缓存，每次都重新读取。

## 长任务行为（Desktop Code tab 常驻规则）

在 Claude Desktop（Code tab）的任何对话里，任务未完成前不要结束回合：

- 不要用「接下来…」「继续：…」这类续跑语当收尾——直接调用工具把下一步做完。
- 只有在全部任务完成、或必须由用户提供信息时才能停；需要用户信息时用一句话明确提问。
- `mcp__ccd_turn__wrap_up` 只用于确实完成后的收尾；不要在任务中途调用它结束回合。
- 全局 Stop 钩子（`~/.claude/hooks/keep_working.py`，已注册在 `~/.claude/settings.json`）会检查任务清单：有 pending/in_progress 项或续跑语收尾时会打回并强制继续，每回合最多自动续跑 5 次（防死循环）；钩子连续 5 次失败会自动熔断，下一条用户消息自动恢复。
- 兜底：如果界面出现「Stop hook failed：…」提示（某些版本把打回显示成失败），同样把它当作"继续执行"的指令，按提示文本继续未完成的工作，不要因此结束回合。
```

### 2.3 长任务保活钩子（核心配置）

**目标**：Claude Desktop Code tab / CLI 中，模型不得在任务清单未完成时提前收尾。

**四层架构**：
1. `UserPromptSubmit`：每次用户消息注入"长任务模式"上下文；
2. `Stop`：欲结束回合时检查最近一次 `mcp__ccd_turn__update_plan` 清单——有 `pending/in_progress`，或以"继续/接下来/然后/随后/下一步"等**续跑语**结尾 → `exit 2 + stderr` 打回，强制继续；每用户回合最多 5 次；
3. `PreToolUse`（matcher `mcp__ccd_turn__wrap_up`）：清单未完成时**拒绝 wrap_up**（exit 2）——wrap_up 是"回合结束"的最强信号，本层不依赖 Stop 钩子；
4. `PostToolUse`（matcher `mcp__ccd_turn__update_plan`）：仍有未完成项时注入提醒上下文。

**可靠性设计**：
- 脚本自身异常一律捕获后 exit 0，绝不因钩子自身阻断对话；
- `keep_working.sh` 包装：解释器兜底（系统 python3 → miniconda python3）、编译自检、纯 shell 兜底、**连续失败熔断**（5 次连续失败写 disabled 标记；下一条用户消息自动清除，10 分钟自动过期）；
- 失败计数只认"钩子进程立即失败"（exit 非 0/2）；中间任何一次成功清零；降级 shell 兜底可工作，不计失败。

**热加载事实（2026-10-31 本机实测）**：`settings.json` 的 hooks 修改对**正在运行的 Code tab 会话即时生效**（会话中途新增的 PostToolUse/PreToolUse 立即触发），无需新开对话；SessionStart 仅在启动/恢复/清空时触发。

**注册方式（`settings.json` 的 `hooks` 字段）**：
```json
{
  "SessionStart": [{"matcher": "startup|resume|clear", "hooks": [{"type": "command", "command": "/bin/sh /Users/lei/.claude/hooks/keep_working.sh --session-start", "timeout": 10}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "/bin/sh /Users/lei/.claude/hooks/keep_working.sh", "timeout": 25}]}],
  "PreToolUse": [{"matcher": "mcp__ccd_turn__wrap_up", "hooks": [{"type": "command", "command": "/bin/sh /Users/lei/.claude/hooks/keep_working.sh", "timeout": 15}]}],
  "PostToolUse": [{"matcher": "mcp__ccd_turn__update_plan", "hooks": [{"type": "command", "command": "/bin/sh /Users/lei/.claude/hooks/keep_working.sh", "timeout": 15}]}],
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "/bin/sh /Users/lei/.claude/hooks/keep_working.sh", "timeout": 10}]}]
}
```
> Windows 无 `/bin/sh`：直接用 `python`（或 `py -3`）调用 `keep_working.py`，并将解释器兜底与 shell 兜底用 Python 重写；或写 `.cmd` 包装。

**`keep_working.py` 全文**：
```python
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
    r"(然后|随后|下一步)[^。！？!?]{0,90}[。！？!?]?\s*$|"
    r"Let me continue|I'?ll continue|Continuing with|Now I'?ll)",
    re.IGNORECASE,
)
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
```

**`keep_working.sh` 全文**：
```sh
#!/bin/sh
# keep_working.sh — 长任务保活钩子包装（2026-10-31 第三版）
# ① 双解释器兜底 ② 编译自检 ③ 纯 shell 兜底 ④ 熔断：连续 5 次失败即禁用本会话钩子
SCRIPT=${KEEP_WORKING_SCRIPT:-/Users/lei/.claude/hooks/keep_working.py}
STATE=${KEEP_WORKING_STATE:-/Users/lei/.claude/hooks/state}
LOG=${KEEP_WORKING_LOG:-/Users/lei/.claude/hooks/keep_working.log}
PY1=/usr/bin/python3
PY2=/Users/lei/miniconda3/bin/python3
MODE="${1:-}"
MAX_FAILS=5

mkdir -p "$STATE"
INPUT=$(cat)
SID=$(printf '%s' "$INPUT" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1 | tr -cd 'A-Za-z0-9_.-')
[ -n "$SID" ] || SID=unknown
DISABLED="$STATE/$SID.disabled"
STREAK="$STATE/$SID.failstreak"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG" 2>/dev/null; }

pick_py() {
	for p in "$PY1" "$PY2"; do
		[ -x "$p" ] || continue
		"$p" -c 'import sys' >/dev/null 2>&1 || continue
		"$p" -m py_compile "$SCRIPT" >/dev/null 2>&1 || continue
		printf '%s' "$p"
		return 0
	done
	return 1
}

fail_tick() {
	n=$(cat "$STREAK" 2>/dev/null || echo 0)
	n=$((n + 1))
	printf '%s' "$n" > "$STREAK"
	if [ "$n" -ge "$MAX_FAILS" ]; then
		: > "$DISABLED"
		log "HOOK-FUSE session=$SID 连续失败 $n 次，已禁用本会话钩子"
	fi
}

ok_tick() { rm -f "$STREAK"; }

# 用户新消息 = 新的尝试预算：自动清除熔断与失败计数（无需手动删除）
case "$INPUT" in
	*'"hook_event_name":"UserPromptSubmit"'*|*'"hookEventName":"UserPromptSubmit"'*)
		rm -f "$DISABLED" "$STREAK"
		;;
esac

# 熔断标记 10 分钟自动过期（最后的自动恢复兜底）
if [ -f "$DISABLED" ]; then
	[ -n "$(find "$DISABLED" -mmin +10 2>/dev/null)" ] && rm -f "$DISABLED" "$STREAK"
fi

# 熔断已触发：直接放行
[ -f "$DISABLED" ] && exit 0

if [ "${KEEP_WORKING_FORCE_SHELL:-0}" = "1" ]; then
	P=""
else
	P=$(pick_py) || P=""
fi

if [ "$MODE" = "--session-start" ]; then
	if [ -n "$P" ]; then
		ok_tick
		exit 0
	fi
	fail_tick
	printf '%s' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"【警告】长任务保活钩子自检失败（Python 不可用或脚本损坏）。本会话请自行遵守长任务规则：任务清单完成前不要结束回合，不要用「接下来…/继续…」收尾，只有完成或必须由用户提供信息时才停。"}}'
	exit 0
fi

if [ -n "$P" ]; then
	printf '%s' "$INPUT" | "$P" "$SCRIPT"
	rc=$?
	if [ "$rc" -eq 0 ] || [ "$rc" -eq 2 ]; then
		ok_tick
	else
		fail_tick
	fi
	exit "$rc"
fi

# —— 纯 shell 兜底（Python 完全不可用；降级可工作，不计失败）——
case "$INPUT" in
	*'"hook_event_name":"Stop"'*|*'"hookEventName":"Stop"'*)
		if printf '%s' "$INPUT" | grep -qE '"status"[[:space:]]*:[[:space:]]*"(pending|in_progress)"|继续|接下来'; then
			echo '任务未完成（shell 兜底判定）。请继续执行未完成项，全部完成前不要结束回合。' >&2
			exit 2
		fi
		;;
	*'wrap_up'*)
		echo '钩子降级运行（Python 不可用）：无法核对清单，先继续完成工作，暂不允许 wrap_up 收尾。' >&2
		exit 2
		;;
esac
exit 0
```

### 2.4 MCP 服务器

统一放在 `~/agents/MCP/<server>/`，各自带 `.mcp.json`；`~/agents/MCP/sync.py` 负责分发到各 agent。

| server | 运行时 | 关键点 |
|---|---|---|
| `davinci-resolve` | 专属 venv `~/agents/MCP/davinci-resolve-mcp/venv/bin/python` | 依赖本机 DaVinci Resolve 安装路径（macOS） |
| `mywebsearch` | `~/agents/virtualenvs/agent-shared-test/bin/python` | 规避上游 WebSearch 流式限制的自建搜索 MCP |
| `scope-recall` | 同上 | 需 `~/agents/scope_recall/instance/*.json` 与 embedding env |
| `mcp-server-commands` | `npx -y mcp-server-commands@0.8.2` | 无本地运行时依赖 |

**Desktop 侧配置**（macOS：`~/Library/Application Support/Claude-3p/claude_desktop_config.json`；Windows：`%APPDATA%\Claude\claude_desktop_config.json`；Linux：`~/.config/Claude/claude_desktop_config.json`，视安装方式）：
```json
{
  "mcpServers": {
    "mcp-server-commands": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-server-commands@0.8.2"
      ]
    },
    "scope-recall": {
      "command": "/Users/lei/agents/virtualenvs/agent-shared-test/bin/python",
      "args": [
        "-I",
        "-B",
        "-m",
        "scope_recall.adapters.codex.mcp_entry",
        "--config",
        "/Users/lei/agents/scope_recall/instance/codex-installation.json",
        "--workspace",
        "/Users/lei/Documents",
        "--env-file",
        "/Users/lei/agents/scope_recall/instance/embedding.env"
      ]
    },
    "mywebsearch": {
      "command": "/Users/lei/agents/virtualenvs/agent-shared-test/bin/python",
      "args": [
        "/Users/lei/agents/MCP/mywebsearch/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    },
    "davinci-resolve": {
      "command": "/Users/lei/agents/MCP/davinci-resolve-mcp/venv/bin/python",
      "args": [
        "/Users/lei/agents/MCP/davinci-resolve-mcp/src/server.py"
      ],
      "env": {
        "RESOLVE_SCRIPT_API": "/Applications/DaVinci Resolve.app/Contents/Resources/Developer/Scripting",
        "RESOLVE_SCRIPT_LIB": "/Applications/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so",
        "PYTHONPATH": "/Applications/DaVinci Resolve.app/Contents/Resources/Developer/Scripting/Modules",
        "PYTHONUNBUFFERED": "1"
      }
    }
  },
  "deploymentMode": "3p",
  "coworkUserFilesPath": "/Users/lei/agents/Claude",
  "preferences": {
    "menuBarEnabled": true,
    "launchPreviewPersistedWorkspaces": [],
    "launchPreviewSessionScopedSessions": [],
    "localAgentModeTrustedFolders": [
      "/Users/lei/Downloads/QuantTrade"
    ],
    "coworkLegacyRootGrantsPruned": true,
    "coworkScheduledTasksEnabled": true,
    "coworkHipaaRestricted": false,
    "orgWorkAcrossAppsDisabled": false,
    "ccdScheduledTasksEnabled": true,
    "sidebarMode": "epitaxy",
    "bypassPermissionsOptInByAccount": {
      "6c431309-c9dc-4561-893c-885f197cb684": true
    },
    "bypassPermissionsGateByAccount": {
      "6c431309-c9dc-4561-893c-885f197cb684": true
    },
    "coworkWebSearchEnabled": true,
    "coworkModelAutoFallbackByAccount": {
      "6c431309-c9dc-4561-893c-885f197cb684": true
    },
    "keepAwakeEnabled": true,
    "remoteToolsDeviceName": "leidemac-mini-local",
    "epitaxyPrefs": {
      "ccd-sessions-filter": {
        "state": {
          "selectedProjects": []
        },
        "version": 0
      },
      "desktop-frame.paneStore.v1": {
        "state": {
          "extraPanesByMode": {},
          "colWeightsByMode": {},
          "rowSplit": 0.5,
          "draftNonce": 0,
          "lastPrimaryCodeSession": {
            "id": "local_f2eebf7d-c09b-4ac2-8a68-297e2e786095",
            "type": "local"
          }
        },
        "version": 4
      },
      "dframe-code-sections": {
        "6c431309-c9dc-4561-893c-885f197cb684/00000000-0000-4000-8000-000000000001": {
          "sections": [
            {
              "id": "pinned",
              "kind": "pinned",
              "v": 2,
              "name": "",
              "order": 0,
              "sortBy": "recency",
              "ascending": false,
              "show": {
                "metadata": false,
                "emptyGroups": false,
                "sideChats": false
              },
              "collapsed": false,
              "shown": true
            },
            {
              "id": "routines",
              "kind": "routines",
              "v": 2,
              "name": "",
              "order": 1,
              "sortBy": "recency",
              "ascending": false,
              "show": {
                "metadata": false,
                "emptyGroups": false,
                "sideChats": false
              },
              "collapsed": true,
              "shown": false
            },
            {
              "id": "sessions",
              "kind": "sessions",
              "v": 2,
              "name": "",
              "order": 2,
              "sortBy": "recency",
              "ascending": false,
              "show": {
                "metadata": false,
                "emptyGroups": false,
                "sideChats": false
              },
              "collapsed": false,
              "shown": true
            }
          ],
          "migratedFrom": 1,
          "prefsSeeded": true
        }
      },
      "dframe-group-scopes": {},
      "dframe-local-slice": {
        "pinnedOrder": [],
        "homeProjectsPinnedOrder": []
      },
      "epitaxy-auto-default-notice-seen.6c431309-c9dc-4561-893c-885f197cb684": true,
      "starred-cowork-spaces": [
        "7713dc1e-b810-4623-86e0-06ab25d1dde3",
        "0ea80f6f-9d0d-46f7-8c40-fa5535071dd7",
        "3038cf39-4965-4bf9-8295-05e730fd76fc",
        "afe49d44-2b21-4d5b-8576-515dc125dad2"
      ],
      "starred-local-code-sessions": [],
      "starred-local-routines": [],
      "starred-session-groups": [],
      "epitaxy-split-suggestion": {
        "state": {
          "shownCount": 1,
          "accepted": false,
          "dismissCount": 0,
          "lastDismissedAt": 0
        },
        "version": 0
      },
      "epitaxy-serene-whistle-decided": {
        "local_f2eebf7d-c09b-4ac2-8a68-297e2e786095": {
          "base": "claude-sonnet-5",
          "kept": true
        }
      },
      "epitaxy-auto-mode-consented.6c431309-c9dc-4561-893c-885f197cb684": true,
      "epitaxy-folder-permission-mode-v2.6c431309-c9dc-4561-893c-885f197cb684": {
        "/Users/lei/Downloads/idea": "auto"
      }
    }
  }
}
```
> 其他设备：先装对应运行时（venv/npx），再把 `.mcp.json` 路径换成本机路径；`scope-recall` 的 instance 配置需按仓库 README 单独初始化。

### 2.5 Skills

- 共享源：`~/agents/skills/`（diagram-design、drawio、drawio-academic-skills、scholar-slides）；
- Claude Code 侧：`~/.claude/skills/` 同名技能；
- 其他 agent 由各自技能目录或 `~/agents/MCP/sync.py` 分发。

### 2.6 运行时环境

- `/usr/bin/python3`（3.9，Xcode CLT）与 `/Users/lei/miniconda3/bin/python3`（3.14）并存；钩子优先系统 python3，失败自动切 miniconda。
- 共享虚拟环境：`~/agents/virtualenvs/agent-shared-test/bin/python`（临时脚本执行引擎，禁止 `pip --upgrade` 污染）。
- Node：遵循仓库 lockfile；一次性 CLI 用 `npx -y`，禁止全局安装。
- 桌面 App：`/Applications/Claude.app`（Claude-3p，user-data-dir `~/Library/Application Support/Claude-3p`）。

---

## 3. 其他设备适配指南（给对方的 agent）

### 3.1 通用原则

1. **先探测再安装**：Claude Code 是否存在/版本/配置目录；Python 解释器与版本；Node/npx；shell 类型。
2. **路径全部本机化**：不要复制 `/Users/lei/...`；Windows 用 `%USERPROFILE%\...`，Linux 用 `$HOME/...`。
3. **hook 命令用绝对解释器路径**，避免 PATH 差异；Windows 用 `py -3` 或 `python.exe` 全路径。
4. **UTF-8**：Windows 上 Python 读写 JSON 显式 `encoding="utf-8"`。
5. **先备份再改**：`settings.json` 改前复制 `.bak.<时间戳>`。
6. **验证优先**：按 §6 清单逐项跑通再交付。

### 3.2 macOS

- 与本机同构：`~/.claude/`；hooks 用 `/bin/sh` 包装可直接复用；
- Python：系统 `/usr/bin/python3`（需 Xcode CLT）或 Homebrew/miniconda；
- Desktop 配置：官方版 `~/Library/Application Support/Claude/claude_desktop_config.json`；第三方版按实际 user-data-dir。

### 3.3 Linux

- 配置目录同为 `~/.claude/`；
- hooks：`/bin/sh` 包装可直接复用；脚本兼容 Python 3.8+；
- Desktop 配置：`~/.config/Claude/claude_desktop_config.json`（无官方 Desktop 时以 CLI 为主）；
- 如需定时 pull：用户级 systemd timer 或 cron，**仅在用户同意后**添加。

### 3.4 Windows

- 配置目录：`%USERPROFILE%\.claude\`（`C:\Users\<user>\.claude`）；
- **没有 `/bin/sh`**：hooks 直接调用 `python`/`py -3` 执行 `keep_working.py`；shell 兜底逻辑移植为 Python 或写 `.cmd` 包装；
- 路径分隔符：JSON 内双反斜杠或正斜杠；脚本用 `pathlib`；
- Desktop 配置：`%APPDATA%\Claude\claude_desktop_config.json`；
- 终端编码：`PYTHONUTF8=1` 或在脚本内 `sys.stdout.reconfigure(encoding="utf-8")`。

### 3.5 各客户端差异

| 客户端 | 配置点 |
|---|---|
| Claude Code CLI | `~/.claude/settings.json`、`~/.claude/CLAUDE.md`、hooks、skills |
| Claude Desktop | `claude_desktop_config.json`（MCP）；Code tab 共用 `~/.claude` 设置 |
| Codex / WorkBuddy / Antigravity | 由 `~/agents/MCP/sync.py` 分发 MCP；规则文件按各自约定放置 |

---

## 4. 同步操作规范

1. **本机新增可复用配置**（hooks、autoCompact、MCP、skills、权限等）：完成后询问用户"是否写入同步记忆"；同意 → 更新对应章节 + §7 → commit/push。
2. **其他设备拉取**：`git pull` → 通读 §2/§3 → 本机适配 → §6 验证 → 本机差异补进 §7 → push。
3. **不要**把 token、私钥、口令写入本文件；用 `${ENV_NAME}` 占位。
4. 大文件（venv、node_modules、模型权重）不入库。

---

## 5. 安全边界

- 本文件可能被多台设备读取，默认按"半公开"处理，敏感值一律占位。
- MCP 的 API key、`scope_recall/instance/embedding.env` 等不复制，各机自行配置。
- Desktop 配置中的 `deploymentMode`、`coworkUserFilesPath` 等属本机特有，按需改写。

---

## 6. 验证清单（配置完成后逐项）

- [ ] `python3 -c "import json;json.load(open('<settings.json>'))"` 通过；
- [ ] hooks 脚本可执行：`sh <hook.sh>`（无输入 exit 0）或 `python <hook.py>`；
- [ ] 假事件测试：Stop + 未完成清单 → exit 2；Stop + 已完成 → exit 0；wrap_up + 未完成 → exit 2；
- [ ] 新开 Code tab / CLI 会话发一条消息，确认钩子生效（日志/上下文）；
- [ ] MCP：每个 server 能在对应客户端启动（工具列表可见）；
- [ ] 备份文件已生成，回滚路径明确。

---

## 7. 变更记录

- 2026-10-31 v1：初版。汇总 macOS 本机配置（Claude Code settings/CLAUDE.md、长任务钩子四层 + 熔断、MCP 四件套、skills、运行时），给出 Linux/Windows 适配原则与验收清单；建立 `~/agents/sync` 与 jpvps bare 仓库。明确不包含 CC Switch/供应商路由与任何 token。

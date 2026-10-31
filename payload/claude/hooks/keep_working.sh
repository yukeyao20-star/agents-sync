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

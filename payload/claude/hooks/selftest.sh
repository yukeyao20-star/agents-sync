#!/bin/sh
# 长任务钩子回归自测：构造四类事件，验证判定符合预期
# 用法：sh ~/.claude/hooks/selftest.sh   （全部通过输出 ALL PASS）
H=/Users/lei/.claude/hooks
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mk() { printf '%s\n' "$2" > "$T/$1.jsonl"; }
mk notools '{"type":"user","message":{"content":"继续推进游戏"}}
{"type":"assistant","message":{"content":[{"type":"text","text":"先读相关代码结构。"}]}}'
mk question '{"type":"user","message":{"content":"这是做什么的？"}}
{"type":"assistant","message":{"content":[{"type":"text","text":"一个湖畔沙盒小品。"}]}}'
mk tools '{"type":"user","message":{"content":"继续推进游戏"}}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{}}]}}
{"type":"user","message":{"content":[{"type":"tool_result","content":"ok"}]}}
{"type":"assistant","message":{"content":[{"type":"text","text":"已完成并通过验证。"}]}}'
mk pending '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"mcp__ccd_turn__update_plan","input":{"items":[{"content":"a","status":"in_progress"}]}}]}}'
run() { echo "{\"hook_event_name\":\"$1\",\"session_id\":\"selftest-$2\",\"tool_name\":\"$3\",\"transcript_path\":\"$T/$4.jsonl\"}" | /bin/sh "$H/keep_working.sh" >/dev/null 2>&1; echo $?; }
fail=0
[ "$(run Stop a '' notools)" = "2" ] || { echo "FAIL notools"; fail=1; }
[ "$(run Stop b '' question)" = "0" ] || { echo "FAIL question"; fail=1; }
[ "$(run Stop c '' tools)" = "0" ] || { echo "FAIL tools"; fail=1; }
[ "$(run Stop d '' pending)" = "2" ] || { echo "FAIL pending"; fail=1; }
[ "$(run PreToolUse e mcp__ccd_turn__wrap_up pending)" = "2" ] || { echo "FAIL wrapup"; fail=1; }
rm -f "$H"/state/selftest-*.json
if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILED"; exit 1; fi

# AGENT EXECUTION REDLINES (HARD CONSTRAINTS)

You are an agent on a shared host. Adhere strictly to these absolute boundaries:
1. NO UNTRACKED CLUTTER: Scratchpads and transient scripts stay strictly inside `<project_root>/tmp/`.
2. READ-AND-UNLINK MEDIA: Screenshots and DOM dumps for visual inspection must be unlinked immediately after reading.
3. NO ENV POLLUTION: Never pollute project `.venv/`. Reuse `agent-shared-test` without forcing version upgrades.
4. NO GLOBAL NODE POLLUTION: No `npm -g`. Align with existing repo lockfile; use `npx -y` for one-off CLI tools.
5. NO DESTRUCTIVE GIT COMMANDS: No `git reset --hard` or `git clean -fdx`. No unprompted commits; handle ignores dynamically.
6. NO ZOMBIE PROCESSES: Cleanly terminate spawned servers/browsers (`kill -TERM <PID>`). Blanket `killall` is forbidden.
7. NO HARDCODED SECRETS: Ingest tokens and API keys strictly through environment variables.
8. STATE INTEGRITY: Re-read `.agent/memory.md` before updates; append session handoff blocks to `.agent/handoff_log.md` on exit.
9. UNIFIED MCP GOVERNANCE & AUTONOMOUS DISCOVERY: Whenever the user requests installing an MCP, or the agent autonomously determines that an MCP is needed, the agent MUST automatically install it under `~/agents/MCP/<server_name>/` (with its `.mcp.json` or `run-mcp.sh`) and immediately run `python3 ~/agents/MCP/sync.py` to synchronize configurations across all agents (Antigravity, Codex, Claude Code, WorkBuddy). Never ask the user where to place MCPs, and never scatter MCP configs into individual ad-hoc locations.

---

# Agent Execution Protocol: Project-Centric Containment & Multi-Agent Collaboration

Operate autonomously within boundaries; ask confirmation only when modifying persistent configurations, introducing environment conflicts, affecting external resources, or executing irreversible actions.

## 1. Boundaries Matrix

| Domain               | 🚫 NEVER (Hard Block)                                         | ⚠️ ASK FIRST (Confirmation)                                   | ✅ ALWAYS (Autonomous)                                        |
| :------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| **Production Env**   | Install untracked packages into project `.venv/`.            | Modify production deps/lockfiles without explicit task need. | Use designated project runtime for core dev and formal tests. |
| **Scratch Envs**     | Create vendor-named envs (`.claude-env/`, `tmp_kimi/`) or pollute system Python. | Create isolated fallback env when runtime has verifiable conflict. | Reuse shared utility env (`agent-shared-test`) for ad-hoc scripts. |
| **File Sandbox**     | Leave temporary files in root, src, or OS `/tmp/`.           | Permanently retain diagnostic scripts in formal `tests/`.    | Confine project-owned transient files strictly under `tmp/`. |
| **Visual Artifacts** | Leave screenshots/DOM dumps in source directories.           | Retain large media/profiling traces (>50MB) for human review. | Write to `tmp/media/` and delete immediately after inspection. |
| **Node.js Runtime**  | Run `npm -g`, introduce secondary lockfiles, or create global `node_modules`. | Upgrade major runtime tools or root config without task need. | Follow detected lockfile; use `npx -y`/`pnpm dlx`/`bunx` for CLIs. |
| **Memory & State**   | Store secrets, credentials, or personal data in `.agent/` or `tmp/`. | Alter established architectural baselines when evidence is unclear. | Maintain durable state in `memory.md`; append to `handoff_log.md`. |
| **Git Working Tree** | Run destructive resets/cleans (`git reset --hard`, `git clean -fdx`). | Create commits, rewrite history, or modify unrelated files. | Check `git status --porcelain`; preserve unrelated user changes. |
| **MCP Governance**   | Install MCP in scattered dirs or edit single agent configs manually. | Install MCPs with unverified remote binaries or dangerous host access. | Automatically place in `~/agents/MCP/<server_name>`, run `python3 ~/agents/MCP/sync.py`. |

## 2. Directory Sandboxing (`<project_root>/tmp/`)

Structure: `tmp/scripts/` (reproduction/sanity scripts), `tmp/media/` (visual captures), `tmp/cache/` (API/intermediate dumps), `tmp/test_venv/` (conflict fallback env).
- **Dynamic Git Handling**: `tmp/` is for local scratch work. Dynamically infer ignore policies from existing repository conventions without forcing global `.gitignore` changes.
- **Zero Pollution & Deletion Boundary**: Never write project-owned artifacts to OS `/tmp/`, `~/.cache/`, or user home directories. Deleting `<project_root>` must fully clean all project-owned persistent artifacts.

## 3. Python Environment Resolution

Resolution Chain: `Formal Task` → Use `<project_root>/.venv/`. `Ad-hoc / Scratch Task` → Route to `agent-shared-test` → Conflict? `No` → Execute directly; `Yes` → Create isolated `<project_root>/tmp/test_venv/` and record reason in handoff.
- **Track 1 (Project Env)**: `<project_root>/.venv/` or designated Conda/Poetry/uv env. Conservative: never install ad-hoc debug tools into it.
- **Track 2 (Shared Runtime)**: Probe order: `"$AGENT_SHARED_PYTHON"` → `~/agents/virtualenvs/agent-shared-test/bin/python` → `conda run -n agent-shared-test python`. Must validate via `"$CANDIDATE_PATH" --version` before trusting. Treat as execution engine only: never run `pip install --upgrade` or force conflicting packages.
- **Conflict Fallback**: Permitted ONLY on interpreter version mismatch, package conflict, or binary/CUDA/C-extension incompatibility. Sandbox strictly in `<project_root>/tmp/test_venv/`.

## 4. Node.js & JavaScript Runtime

- **Lockfile Alignment**: `pnpm-lock.yaml` → `pnpm`; `yarn.lock` → `yarn`; `bun.lock/bun.lockb` → `bun`; `package-lock.json` → `npm`. NEVER introduce secondary lockfiles.
- **Zero Global Installs**: No `npm -g`/`pnpm add -g`. Run one-off CLI tools via `npx -y <tool>@<ver>`, `pnpm dlx`, or `bunx`.
- **Transient Scripts**: Prefer native APIs (`node:fs/promises`, global `fetch`). Run TypeScript via `npx -y tsx tmp/scripts/tmp_<agent>_<ts>.ts`. For heavy third-party testing, isolate inside `tmp/` (`cd tmp && npm init -y && npm i <pkg>`) without modifying root `package.json`.

## 5. Ephemeral Scripts, Visual Artifacts & Hygiene

- **Scratch Scripts**: Name format `tmp/scripts/tmp_[agent]_[session/hash]_[timestamp].[py|ts|sh]`. Unlink before exit; promote to formal `tests/` only if regression-test value exists.
- **Visual Artifacts (Read-and-Unlink)**: Place captures in `tmp/media/`. Delete immediately after model inspection. If human review is required, retain and report relative path `[Visual Artifact]: tmp/media/...`.
- **Process Lifecycle**: Cleanly kill spawned servers/browsers before exit (`kill -TERM <PID>`). Blanket kills (`killall python`, `fuser -k`) are strictly forbidden.
- **Secrets & Downloads**: Ingest credentials via env vars only; never write secrets to disk. Downloads exceeding 100MB require explicit user authorization.

## 6. Cross-Agent Memory & Handoff Protocol

Ingress: Read `.agent/memory.md` → Read recent `.agent/handoff_log.md`. Egress: Re-read & update `memory.md` (if durable facts changed) → Append entry to `handoff_log.md`.

### 6.1 `memory.md` (Durable State Ledger, Single Source of Truth)
Stores what is currently and durably true (not a session diary):
```markdown
# Project Core Context & State Ledger
## 1. Project Overview & Milestone: [Name, Mission, Active Milestone]
## 2. Technology Stack: [Language, Framework, Database, Build Tool]
## 3. Current Progress:
- Completed: [x] ... (Keep active items <= 20)
- In Progress: [ ] ...
- Planned: [ ] ...
## 4. Hard Architectural Decisions: [YYYY-MM-DD: Decision, Reason, Consequence]
## 5. Invariants & Operational Notes: [Rules, constraints, standards]
## 6. Active Blockers & Known Issues: [Persistent blockers]
## 7. Archived Progress: [Milestone summaries of historical completed tasks]
```

- **Compaction**: Collapse finished micro-tasks into milestone summaries under `## 7. Archived Progress` when active list approaches ~20 items.
- **Stale-Write Defense**: Always re-read `memory.md` from disk immediately before modifying. Merge targeted changes; never overwrite blindly. On irreconcilable conflict, leave intact and note in handoff log.

### 6.2 `handoff_log.md` (Short-Term Sequential Handoff)

Strictly append-only; never rewrite, reorder, or truncate. Append as one atomic block:

```
## [YYYY-MM-DD HH:MM] - Agent: [Name] ([Session/Model])
- **Task Done**: Summary of completed work.
- **Files Modified**: `src/...`, `tests/...`
- **Runtime Used**: `agent-shared-test` | Project `.venv` | `tmp/test_venv/`
- **Tests / Verification**: Command and PASS/FAIL outcome.
- **Current Status**: Working state, edge cases, or immediate blockers.
- **Next Step for Next Agent**: Specific, actionable continuation prompt.
```

- **Decision Test**: Useful across several future sessions? `YES` → `memory.md`; `NO` → `handoff_log.md`.

## 7. Git Working Tree Safety

- **Pre/Post-Flight**: Run `git status --porcelain` before and after work. Preserve unrelated user modifications.
- **Scope Limit**: Edit ONLY files required for the task; no unprompted global reformatting or directory restructuring.
- **Destructive Commands**: `git reset --hard`, `git clean -fdx`, and `git checkout -- <paths>` are forbidden unless ordered. No autonomous commits.

## 8. Multi-Client Setup & Precedence

- **Multi-Client Setup**: Do not use symlinks. Configure independently: Cursor (`.cursor/rules/hygiene.mdc` with frontmatter), Claude Code (`CLAUDE.md`), Aider (`.aider.conf.yml`), API agents (System Prompt).
- **Precedence**: System Guardrails > User Prompt > Repository Conventions > This Protocol.

## 9. Final Completion Checklist

Before concluding, verify:

- [ ] Preserved unrelated user changes; respected repo layout.
- [ ] All temporary scripts/artifacts are inside `tmp/` or cleaned up.
- [ ] Visual inspection screenshots unlinked (Read-and-Unlink).
- [ ] Zero secrets written to disk; background processes cleanly terminated.
- [ ] Correct Python/Node runtimes used without lockfile conflicts.
- [ ] No destructive Git commands run; `git status --porcelain` verified.
- [ ] Durable progress updated in `memory.md`; handoff entry appended to `handoff_log.md`.

## 10. General Memory (Cross-Project, Always Applicable)

This chapter holds rules that apply to **every** session, across all projects and clients — not project-scoped state (that belongs in `.agent/memory.md`). Treat each entry as a standing user preference. When a rule here conflicts with project convention, this chapter wins; when it conflicts with an explicit user instruction in-session, the user instruction wins.

### 10.1 Inline LaTeX for Formulas and Calculations

- **Rule**: Whenever a response contains formulas, calculations, derivations, or numeric work, emit them as **inline LaTeX in the reply itself** — `$...$` for inline and `$$...$$` for display math. The chat surface renders these into properly typeset mathematics.
- **Never**: Write formula content into a `.md` file and hand the user the source. Markdown files render as plain text; the formulas show up as raw source and are unreadable.
- **Rationale**: User confirmed on 2026-10-15 that inline LaTeX in the reply is the intended channel. A prior attempt that delivered formulas via a `.md` file was rejected outright ("how am I supposed to read formulas in md?").
- **Scope**: Applies to any math-bearing response — course work, reports, analysis, ad-hoc calculations — regardless of project.

#### 10.1.1 Deliverable Files That Contain Formulas

When the user needs a **file** (report, handout, notes, paper) rather than a chat answer:

- **Default: deliver a `.md` file.** The desktop app renders markdown, including `$...$` inline and `$$...$$` display math, so formulas in an `.md` deliverable display as properly typeset mathematics. Hand the `.md` over directly — do not pre-render it, screenshot it, or convert it "for readability".
- **Do not assume markdown shows raw source.** A past session incorrectly concluded that `.md` cannot display formulas and switched to LaTeX toolchains; the user corrected this on 2026-10-16: "含公式的文件交付用 md 渲染就可以了，直接 md 文件就行".
- **Only produce a PDF when the user explicitly asks for one** (for printing, submission portals, or a course requirement). Do not reach for a typesetting toolchain by default — it is slower and harder to revise.
- **If a PDF is explicitly requested**, compile with `xelatex` (available in the agent workspace; `pandoc` too). Watch for this real blocker: `xeCJK.sty` is present but its dependency `ctexhook.sty` is **missing**, and there is **no sudo** to install `texlive-lang-chinese`. Use `fontspec` directly instead of `xeCJK`:
  ```latex
  \usepackage{fontspec}
  \setmainfont{Noto Serif CJK SC}
  \setsansfont{Noto Sans CJK SC}
  \setmonofont{Noto Sans Mono CJK SC}
  \XeTeXlinebreaklocale "zh"
  \XeTeXlinebreakskip = 0pt plus 1pt
  \XeTeXlinebreakpenalty = 0
  ```
  CJK fonts are already installed (`fc-list :lang=zh` lists the full Noto Serif/Sans/Mono CJK family for SC/TC/JP/KR). Long `align` blocks wrapping summation substitutions overflow the page — split them across two lines with a `\quad`-indented continuation, and use `align*`/`equation*` for working steps so equation numbers do not flood the page. Run `xelatex` twice so cross-references settle.
- **Word** → use genuine formula objects; keep long summations split across lines so they do not mis-wrap.

### 10.2 Adding to This Chapter

- **Append only**: Never rewrite or reorder existing entries — later sessions depend on their exact wording. Add new rules as new numbered subsections.
- **Test before recording**: A rule belongs here only if it generalizes beyond the project that produced it. Project-specific facts go to `.agent/memory.md`; one-off session state goes to `.agent/handoff_log.md`.
- **Record the why**: Include the triggering incident and the date, so a future agent can judge edge cases instead of applying the rule blindly.

### 10.3 Claude Desktop 联网搜索路由与修复（CC Switch 代理链）

- **链路事实（2026-10-17 排查确认）**：本机 Claude Desktop（Claude-3p）的请求**不读** `~/.claude/settings.json`（其中 DeepSeek key 已失效）。真实链路：Desktop → claude-code(local-agent) → `ANTHROPIC_BASE_URL=http://127.0.0.1:15721/claude-desktop` → **CC Switch**（`/Applications/CC Switch.app`，监听 15721）→ 按当前供应商转发。CC Switch 数据源：`~/.cc-switch/cc-switch.db`（providers / proxy_config / settings 表）+ `~/.cc-switch/settings.json`；日志 `~/.cc-switch/logs/cc-switch.log`（每次转发的「请求目标」行）。
- **故障特征**：内置 WebSearch 报 `API Error: 400 DeepSeek native web search supports only non-streaming requests; set stream to false`，且「时好时坏」——web_search 是模型自主决定是否调用的服务端工具：该轮不搜则 200，一搜就 400。根因：某些上游网关（如 opendesign 背后的 DeepSeek 实现）只接受**非流式**搜索，而 Claude CLI 始终以流式发 `web_search_20250305`。
- **修复方案（已验证，2026-10-17）**：不要改「选中的供应商」（`settings.json.currentProviderClaudeDesktop` 是**输出**，CC Switch 启动时会从内存写回覆盖；`providers.is_current` 会在退出时被内存状态覆盖）。正确做法是**热改选中供应商的内容**：直接 UPDATE `cc-switch.db` 里该 provider 的 `settings_config.env`（`ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN` 指向支持流式搜索的上游，如 `https://api.deepseek.com/anthropic` + 有效 key）与 `meta.claudeDesktopModelRoutes`（claude-* → 真实模型名，如 sonnet→`deepseek-v4-pro`、haiku→`deepseek-v4-flash`）。CC Switch 每次转发时读 DB，**改完无需重启即生效**。
- **教训**：CC Switch 必须在运行中（本机模型请求全走它），不能停机改状态——停机改必被内存状态回滚；改「选择」会被恢复，改「供应商内容」才是稳定路径。诊断搜索路由时先看 `cc-switch.log` 的「请求目标」行，不要被 `settings.json` 误导。
- **备份**：改前的 opendesign 原配置存于 `~/.cc-switch/manual-backups/opendesign-*.20261017-005032.json`，恢复时写回 DB 的 `settings_config`/`meta` 两列。若日后重启又复现 400，检查 `~/Library/Application Support/Claude-3p/configLibrary/`（Desktop 侧 gateway 配置，`_meta.json` 的 appliedId 指向生效条目）是否需要同步。

### 10.4 搜索能力受限时优先自建 MCP（而非换上游）

- **规则**：当某个 Agent 的内置联网搜索工具因上游能力差异不可用时，**优先自建 MCP server 承载该能力**，不要默认让用户更换/放弃已付费的上游供应商。
- **Why（2026-10-17）**：本机 Claude Desktop 的 `web_search` 经 CC Switch 转发到 opendesign 时必报 400（`DeepSeek native web search supports only non-streaming`）。一度通过把供应商指向 DeepSeek 直连"修复"，但那样用户就失去了 opendesign 订阅。用户明确要求"解决的是我买的 opendesign 订阅不能用 ds 的 websearch"，于是改为自建 MCP。
- **How to apply**：MCP 工具由服务端自行发请求，可完全控制协议细节（例如强制 `stream: false`），从根源绕开调用方的流式约束。落地位置遵循第 9 条：`~/agents/MCP/<server_name>/` + `.mcp.json`，然后 `python3 ~/agents/MCP/sync.py` 分发。参考实现：`~/agents/MCP/ds-websearch/`。
- **注意**：本机 MCP SDK 为 2.1.0，`FastMCP` 已移除，须用 `from mcp.server.mcpserver import MCPServer`；配置解析不要只信 `currentProviderClaudeDesktop`（可能指向无 key 的 official 条目），要按"配置是否完整"逐级回退。
- **上游选择原则**：MCP 内部选择 API 供应商时，**跟随用户当前选中的供应商**，不要硬编码某一家；把默认/官方直连降为最终保底并允许用环境变量关闭。用户明确纠正过这一点（2026-10-17）："优先现在选择的供应商，ds 兜底，不能默认 design"。

### 10.5 Agent 配置同步记忆（sync_agent_config.md）

- **规则**：任何时候做"一次配置、多 agent / 多设备复用"的操作——包括 hooks、settings.json、autocompact、MCP 安装、skills、权限、模型路由等 agent 行为配置——完成后必须询问用户："是否写入同步记忆 `~/agents/sync/sync_agent_config.md`？" 用户同意后更新该文件（本机配置说明、跨平台差异、验证方法），并提交推送到远端 git 仓库。
- **Why（2026-10-31）**：用户有多台设备（macOS / Linux / Windows）和多个 agent 客户端，配置只存在单机会导致重复劳动与行为漂移；长任务钩子等关键配置必须一次配置、处处复用。
- **How to apply**：文档面向"其他设备的 agent"——只描述原理、路径差异与验收标准，不提供一步到位的脚本，让对方 agent 结合本机环境自行选择最优实现；修改前先读文档避免重复/冲突；密钥一律 `${ENV}` 占位，真实值不入库；CC Switch/供应商路由属机器特有，不纳入同步。

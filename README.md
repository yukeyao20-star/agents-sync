# agents-sync — 多设备 Agent 配置同步

一份说明书（`sync_agent_config.md`）解决一件事：**在一台机器上配好的 Agent 行为，其他机器（macOS / Linux / Windows）的 Agent 能照着复现**。

## 这是什么

这不是一套程序，也不是一键安装脚本。它是一份**写给 Agent 读的配置说明书**：

- 记录了主力机（macOS）上 Claude Code / Claude Desktop 的完整配置方式——hooks（长任务保活）、`settings.json`、`CLAUDE.md` 常驻规则、MCP 服务器、skills、运行时环境等；
- 给出了 Linux / Windows 的路径差异与适配原则；
- 其他设备的 Agent 拉取后，**结合本机环境自行选择最优实现**，而不是照抄路径。

## 快速接入

```bash
git clone https://github.com/yukeyao20-star/agents-sync.git ~/agents/sync
```

然后把 `~/agents/sync/sync_agent_config.md` 交给本机的 Agent，并对它说：

> 阅读 `~/agents/sync/sync_agent_config.md`，按 §3 的对应平台指南把本机配置好；完成后按 §6 验证清单逐项检查。

也可以直接浏览器打开（无需 git）：

<https://yukeyao.sbs/agents/sync_agent_config.md>

## 仓库自带全部文件（只需 clone，无需手动传文件）

```
payload/
├── agent.md                      → 拷到 ~/agents/agent.md
├── claude/
│   ├── CLAUDE.md                 → ~/.claude/CLAUDE.md
│   ├── settings.example.json     → 参考/合并进 ~/.claude/settings.json（已脱敏）
│   └── hooks/keep_working.{py,sh}→ ~/.claude/hooks/
├── mcp/
│   ├── sync.py                   → ~/agents/MCP/sync.py（MCP 分发器）
│   ├── mywebsearch/              → 完整源码（自建搜索 MCP）
│   ├── scope-recall/             → 配置/hooks/skills（代码见上游 repo）
│   ├── mcp-server-commands.mcp.json
│   └── davinci-resolve-mcp.mcp.json + INSTALL.md（上游 repo 安装说明）
└── skills/                       → 四个技能完整目录，拷到 ~/agents/skills/
```

其他设备 clone 后不需要你从这台机器手动拷任何文件；让本机 Agent 按文档把 `payload/` 里的文件放到对应位置并适配路径即可。

## 同步是怎么工作的

| 方向 | 做法 |
|---|---|
| 本机配了新东西 | 更新 `sync_agent_config.md` → `git commit` → `git push` |
| 其他设备要用 | `git pull` → Agent 读文档 → 本机适配 |
| 其他设备改了配置 | 本地更新文档 → commit/push 回本仓库（需 GitHub 权限） |
| 新设备首次接入 | 上面的 clone 命令 + 让 Agent 读文档 |

仓库是 **public** 的（clone/拉取不需要凭据），推送需要 `yukeyao20-star` 账号权限。

## 里面同步什么

- ✅ Claude Code：`settings.json`（脱敏）、`CLAUDE.md`、hooks 脚本全文、autoCompact 等
- ✅ 长任务保活钩子：四层架构 + 完整源码 + 熔断/自动恢复设计
- ✅ MCP 服务器定义与安装方式、skills、运行时环境约定
- ✅ Linux / Windows 适配指南与验收清单

## 不同步什么

- ❌ 任何 token / key / 密码（文档里一律 `${ENV_NAME}` 占位）
- ❌ CC Switch 供应商路由、模型映射（属机器特有选择）
- ❌ venv、node_modules、大文件

## 一条配套规则

本仓库配套一条常驻规则（见 `~/agents/agent.md` §10.5，文档 §2.2.1 有全文）：

> 任何时候做"一次配置、多 agent / 多设备复用"的操作（hooks、settings、autocompact、MCP、skills、权限、模型路由等），完成后必须询问用户"是否写入同步记忆 `~/agents/sync/sync_agent_config.md`"；用户同意后更新并推送。

也就是说：这套同步是**活的**——以后每一笔可复用的配置都会经过你确认后被收进这份文档，而不是一次性写完就过期。

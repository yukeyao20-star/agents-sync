# mywebsearch

解决 Claude Desktop 内置 `web_search` 在第三方上游（opendesign / DeepSeek 网关）
上因「只接受非流式」而报 400 的问题。

## 原理

内置搜索由 Claude CLI 以**流式**发起，而上游的 DeepSeek 原生搜索只接受非流式，
两者冲突 → `400 DeepSeek native web search supports only non-streaming requests`。

本 MCP server 自己以 `stream: false` 调用上游 `/v1/messages` 的
`web_search_20250305` 服务端工具，因此不受调用方流式约束影响。

## 工具

| 工具 | 说明 |
|---|---|
| `myweb_search(query, count=5)` | 联网搜索 |
| `myweb_fetch(url, max_chars=20000)` | 抓取网页正文 |

## 双路径自动分流

| 上游 | 搜索 | 抓取 |
|---|---|---|
| DeepSeek 官方（兜底） | `/v1/tools/search` | `/v1/tools/fetch` |
| 其它供应商（如 opendesign） | `/v1/messages` + `web_search` 工具 | MCP 自行 HTTP 抓取 |

**官方路径质量更高**：返回 `rerank_score`(0-3)、`authority`(0-4)、以及真实 `summary` 正文，
不像第三方网关那样只给加密的 `encrypted_content`。返回里的 `api` 字段标明走了哪条路。

## 上游选择优先级

| 级别 | 来源 | 说明 |
|---|---|---|
| 1 | 环境变量 `DS_BASE_URL` / `DS_API_KEY` | 显式指定，最高优先 |
| 2 | `DS_PREFER_PROVIDER` 指定者 | 可选，默认不设 |
| 3 | **当前选中的供应商** | 读取 CC Switch 的 current provider，自动跟随你的切换 |
| 4 | 其它非 DeepSeek 供应商 | 兜底 |
| 5 | **DeepSeek 直连** | 仅最终保底 |

环境变量：

- `DS_PREFER_PROVIDER`：可选，额外锁定某个供应商（默认空，即跟随当前选中）
- `DS_FALLBACK_TO_DEEPSEEK=0`：**完全禁用** DeepSeek 兜底
- `DS_MODEL`：强制覆盖模型名

返回结果里的 `via` 字段会标明本次实际使用的供应商。

## 注意

- 上游返回的搜索结果只有 `encrypted_content`（加密，约 3KB/条），**无法解密**，
  因此 `results` 只含标题+链接；可读内容由模型写在 `answer` 中（基于真实搜索结果生成）。
- `myweb_fetch` 不走上游：实测上游的 `web_fetch` / `web_fetch_20250305`
  只返回一个客户端 `tool_use`，没有服务端抓取能力。因此该工具由 MCP 自行
  发起 HTTP 请求、用标准库把 HTML 转成文本。
- 2026-10-17 DeepSeek 官方新开放了 `/v1/tools/search` 与 `/v1/tools/fetch`，
  但 **opendesign 未代理这两个端点**（实测 404），只能直连 DeepSeek 使用。
- opendesign 下模型映射：`claude-sonnet-5` → `deepseek-v4.1-flash`。

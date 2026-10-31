# davinci-resolve-mcp 安装说明

上游仓库：https://github.com/samuelgursky/davinci-resolve-mcp

1. `git clone https://github.com/samuelgursky/davinci-resolve-mcp.git ~/agents/MCP/davinci-resolve-mcp`
2. 按上游 README 建 venv 并安装依赖（`.venv` 不入库）。
3. `.mcp.json` 见同目录 `davinci-resolve-mcp.mcp.json`，把其中的解释器路径改成本机路径。
4. 需要本机安装 DaVinci Resolve（其 Scripting API 路径随安装位置变化）。

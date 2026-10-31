@echo off
chcp 65001 >nul
"/Users/lei/agents/virtualenvs/agent-shared-test/bin/python" "-I" "-B" "-m" "scope_recall.adapters.codex.hook_entry" "--config" "/Users/lei/agents/scope_recall/instance/codex-installation.json"
exit /b %ERRORLEVEL%

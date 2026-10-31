# ~/agents 文件树（本机 macOS，2026-10-31）

> 说明：
> - 本仓库 `payload/` 已包含可安装文件；标 ✅ 的目录在本仓库有对应副本。
> - 标 ⛔ 的目录是机器本地产物（venv/缓存/草稿/独立仓库），不入库。

```
~/agents/
├── Claude/
├── MCP/
│   ├── davinci-resolve-mcp/
│   │   ├── .agents/
│   │   ├── .claude/
│   │   ├── .codex/
│   │   ├── .continue/
│   │   ├── .cursor/
│   │   ├── .github/
│   │   ├── .oss-scanner/
│   │   ├── .roo/
│   │   ├── .windsurf/
│   │   ├── bin/
│   │   ├── docs/
│   │   ├── examples/
│   │   ├── release-notes/
│   │   ├── resolve-advanced/
│   │   ├── scripts/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── .clinerules
│   │   ├── .cursorrules
│   │   ├── .gitattributes
│   │   ├── .gitignore
│   │   ├── .mcp.json
│   │   ├── .npmignore
│   │   ├── .windsurfrules
│   │   ├── AGENTS.md
│   │   ├── CHANGELOG.md
│   │   ├── CLAUDE.md
│   │   ├── install.py
│   │   ├── LICENSE
│   │   ├── look.cube
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── README.zh-CN.md
│   │   ├── requirements.txt
│   │   ├── run-mcp.sh
│   │   └── SECURITY.md
│   ├── mcp-server-commands/
│   │   └── .mcp.json
│   ├── mywebsearch/
│   │   ├── .mcp.json
│   │   ├── README.md
│   │   ├── run-mcp.sh
│   │   └── server.py
│   ├── scope-recall/
│   │   ├── .codex-plugin/
│   │   ├── hooks/
│   │   ├── skills/
│   │   ├── .mcp.json
│   │   ├── .mcp.json.bak-20261015-235703
│   │   └── run-mcp.sh
│   ├── README.md
│   ├── sync.py
│   ├── sync.py.bak-20261015-220357
│   └── sync.py.bak-20261015-235703
├── scope_recall/
│   ├── .github/
│   │   ├── scripts/
│   │   └── workflows/
│   ├── adapters/
│   │   ├── clients/
│   │   ├── codex/
│   │   ├── hermes/
│   │   ├── __init__.py
│   │   ├── runtime_wiring.py
│   │   └── tool_common.py
│   ├── backups/
│   │   ├── codex-installation-20261015-224415.json
│   │   ├── manifest-20261015-224429.json
│   │   ├── memory-20261015-224429.sqlite3
│   │   └── receipt-20261015-224415.json
│   ├── build/
│   │   ├── bdist.macosx-11.0-arm64/
│   │   └── lib/
│   ├── constraints/
│   │   ├── release-hashed.txt
│   │   ├── release.txt
│   │   ├── runtime-max.txt
│   │   └── runtime-min.txt
│   ├── contracts/
│   │   ├── consolidation_result.schema.json
│   │   ├── entity_request.schema.json
│   │   ├── entity_view.schema.json
│   │   ├── examples.json
│   │   ├── forget_request.schema.json
│   │   ├── profile_request.schema.json
│   │   ├── profile_view.schema.json
│   │   ├── README.md
│   │   ├── recall_packet.schema.json
│   │   ├── recall_request.schema.json
│   │   ├── revise_request.schema.json
│   │   ├── source_event.schema.json
│   │   ├── task_receipt.schema.json
│   │   ├── trace_request.schema.json
│   │   └── trace_view.schema.json
│   ├── core/
│   │   ├── __init__.py
│   │   ├── admission.py
│   │   ├── aliases.py
│   │   ├── artifact_storage.py
│   │   ├── background_context.py
│   │   ├── candidate_debounce.py
│   │   ├── candidate_evaluations.py
│   │   ├── candidate_intake.py
│   │   ├── candidate_lifecycle.py
│   │   ├── candidate_storage.py
│   │   ├── candidate_sweeps.py
│   │   ├── candidate_tables.py
│   │   ├── capture.py
│   │   ├── capture_filters.py
│   │   ├── capture_inbox.py
│   │   ├── claim_normalization.py
│   │   ├── claim_storage.py
│   │   ├── claims.py
│   │   ├── composition.py
│   │   ├── confirmation.py
│   │   ├── consolidate.py
│   │   ├── consolidation_chunks.py
│   │   ├── consolidation_summary.py
│   │   ├── corroboration.py
│   │   ├── coverage.py
│   │   ├── deadline.py
│   │   ├── delete_storage.py
│   │   ├── deletion.py
│   │   ├── duplicate_collapse.py
│   │   ├── embedding_budget.py
│   │   ├── endpoint_policy.py
│   │   ├── episode_storage.py
│   │   ├── episodes.py
│   │   ├── events.py
│   │   ├── evidence_question.py
│   │   ├── evidence_quote.py
│   │   ├── fact_actions.py
│   │   ├── fact_evidence.py
│   │   ├── fact_identity.py
│   │   ├── fact_temporal_semantics.py
│   │   ├── failure_retry.py
│   │   ├── file_lock.py
│   │   ├── gating.py
│   │   ├── inbox_rules.py
│   │   ├── index_rebuild.py
│   │   ├── inspect_service.py
│   │   ├── lexical_index.py
│   │   ├── lineage.py
│   │   ├── mutate.py
│   │   ├── operations.py
│   │   ├── owner_view.py
│   │   ├── read_views.py
│   │   ├── recall.py
│   │   ├── recall_budget.py
│   │   ├── recall_diagnostics.py
│   │   ├── recall_needs.py
│   │   ├── recall_packet.py
│   │   ├── recall_policy.py
│   │   ├── recall_scope.py
│   │   ├── records.py
│   │   ├── reference_storage.py
│   │   ├── registry_storage.py
│   │   ├── requalify.py
│   │   ├── restore.py
│   │   ├── resume_compaction.py
│   │   ├── retained_artifacts.py
│   │   ├── retrieval.py
│   │   ├── retrieval_hydration.py
│   │   ├── retrieval_storage.py
│   │   ├── schema.py
│   │   ├── secret_patterns.py
│   │   ├── source_qualification.py
│   │   ├── source_records.py
│   │   ├── source_storage.py
│   │   ├── storage.py
│   │   ├── subject_binding.py
│   │   ├── trace.py
│   │   ├── truth_connection.py
│   │   ├── vector_failure.py
│   │   ├── visibility.py
│   │   ├── work_storage.py
│   │   ├── worker.py
│   │   ├── worker_candidates.py
│   │   ├── worker_consolidation.py
│   │   ├── worker_outcomes.py
│   │   ├── worker_projection.py
│   │   └── writer_lease.py
│   ├── distribution/
│   │   ├── codex/
│   │   ├── dsh/
│   │   ├── hermes/
│   │   └── __init__.py
│   ├── docs/
│   │   ├── autonomous-memory.md
│   │   ├── capture-contract.md
│   │   ├── claim-mutation-contract.md
│   │   ├── codex-cli-consolidation.md
│   │   ├── configuration.md
│   │   ├── core-storage-mapping.md
│   │   ├── deletion-contract.md
│   │   ├── episode-artifact-contract.md
│   │   ├── install.md
│   │   ├── profile-entity.zh-CN.md
│   │   ├── remote-entries.md
│   │   ├── shared-store.md
│   │   ├── trace.zh-CN.md
│   │   ├── upgrade-contract.md
│   │   └── upgrade-guide.zh-CN.md
│   ├── fixtures/
│   │   ├── acceptance_cases.jsonl
│   │   ├── cognitive_cases.jsonl
│   │   ├── input_routes.json
│   │   ├── longitudinal_journeys.jsonl
│   │   └── README.md
│   ├── hermes_scope_recall.egg-info/
│   │   ├── dependency_links.txt
│   │   ├── entry_points.txt
│   │   ├── PKG-INFO
│   │   ├── requires.txt
│   │   ├── SOURCES.txt
│   │   └── top_level.txt
│   ├── instance/
│   │   ├── data/
│   │   ├── .scope-recall-install-receipt.json
│   │   ├── codex-installation.json
│   │   └── embedding.env
│   ├── maintenance/
│   │   ├── skills/
│   │   ├── __init__.py
│   │   ├── AGENT_WORKFLOW.md
│   │   ├── autostart.py
│   │   ├── backup.py
│   │   ├── cli.py
│   │   ├── doctor.py
│   │   ├── doctor_report.py
│   │   ├── doctor_store.py
│   │   ├── install.py
│   │   ├── install_claude_code.py
│   │   ├── install_client.py
│   │   ├── install_codex.py
│   │   ├── install_common.py
│   │   ├── install_dsh.py
│   │   ├── install_hermes.py
│   │   ├── install_purge.py
│   │   ├── install_receipt.py
│   │   ├── install_remote.py
│   │   ├── install_workbuddy.py
│   │   ├── legacy_catalog.py
│   │   ├── legacy_claims.py
│   │   ├── legacy_conversion.py
│   │   ├── legacy_deletions.py
│   │   ├── legacy_episode_membership.py
│   │   ├── legacy_lifecycle.py
│   │   ├── legacy_plan.py
│   │   ├── legacy_sources.py
│   │   ├── legacy_v2_compat.py
│   │   ├── migrate.py
│   │   ├── migrate_v2.py
│   │   ├── migration_activation.py
│   │   ├── migration_index.py
│   │   ├── migration_mapping.json
│   │   ├── migration_records.py
│   │   ├── onboarding.py
│   │   ├── package_health.py
│   │   ├── package_upgrade.py
│   │   ├── resident.py
│   │   ├── rollback.py
│   │   ├── shared.py
│   │   ├── shared_import.py
│   │   ├── shared_run.py
│   │   ├── upgrade.py
│   │   └── upgrade_cli.py
│   ├── packaging/
│   │   └── v11-module-allowlist.json
│   ├── packaging_hooks/
│   │   ├── __init__.py
│   │   ├── module_inventory.py
│   │   └── v11_build.py
│   ├── probes/
│   │   ├── hermes/
│   │   ├── eval_model_runtime.py
│   │   └── README.md
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── _http_worker.py
│   │   ├── _worker_bootstrap.py
│   │   ├── auxiliary.py
│   │   ├── codex_cli.py
│   │   ├── consolidation_models.py
│   │   ├── embedding_models.py
│   │   ├── embedding_retry.py
│   │   ├── http_session.py
│   │   ├── instance.py
│   │   ├── instance_config.py
│   │   ├── lance_port.py
│   │   ├── model_budget.py
│   │   ├── models.py
│   │   ├── process_probe.py
│   │   ├── resume_entry.py
│   │   ├── running_code.py
│   │   ├── scheduling.py
│   │   ├── subscription_budget.py
│   │   ├── validation.py
│   │   ├── vector_retention.py
│   │   ├── vector_upkeep.py
│   │   ├── worker_entry.py
│   │   ├── worker_launch.py
│   │   └── worker_watchdog.py
│   ├── scripts/
│   │   ├── build.package_manifest.py
│   │   ├── check.py
│   │   ├── dead_code.py
│   │   ├── execution_boundary.py
│   │   ├── quality.baseline.json
│   │   ├── quality.py
│   │   ├── release.candidate_rehearsals.json
│   │   ├── release.invariants.json
│   │   └── test_directories.py
│   ├── store/
│   │   ├── receipts/
│   │   └── installation.json
│   ├── tests/
│   │   ├── contract/
│   │   ├── fixtures/
│   │   ├── host/
│   │   ├── integration/
│   │   ├── known_answer/
│   │   ├── migration/
│   │   ├── packaging/
│   │   ├── storage_native/
│   │   ├── unit/
│   │   ├── conftest.py
│   │   ├── plugin_source.py
│   │   ├── sitecustomize.py
│   │   ├── test_cold_open_overlap.py
│   │   ├── test_lance_fanout_deadline.py
│   │   ├── test_vector_runtime.py
│   │   ├── v11_guard.py
│   │   └── v11_support.py
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── compaction.py
│   │   ├── lance_native.py
│   │   ├── process_store.py
│   │   ├── purge.py
│   │   ├── sqlite_store.py
│   │   └── store.py
│   ├── verification/
│   │   ├── G0/
│   │   ├── functional_traceability.json
│   │   └── README.md
│   ├── .env.example
│   ├── .git-blame-ignore-revs
│   ├── .gitattributes
│   ├── .gitignore
│   ├── __init__.py
│   ├── _lance_worker.py
│   ├── _version.py
│   ├── AGENTS.md
│   ├── CHANGELOG.md
│   ├── contracts.py
│   ├── CONTRIBUTING.md
│   ├── CONTRIBUTORS.md
│   ├── LICENSE
│   ├── MANIFEST.in
│   ├── py.typed
│   ├── pyproject.toml
│   ├── README.md
│   ├── SECURITY.md
│   └── uv.lock
├── skills/
│   ├── diagram-design/
│   │   ├── assets/
│   │   ├── references/
│   │   ├── scripts/
│   │   └── SKILL.md
│   ├── drawio/
│   │   ├── agents/
│   │   ├── assets/
│   │   ├── evals/
│   │   ├── references/
│   │   ├── reports/
│   │   ├── scripts/
│   │   ├── styles/
│   │   ├── .mcp.json
│   │   ├── CHANGELOG.md
│   │   └── SKILL.md
│   ├── drawio-academic-skills/
│   │   ├── agents/
│   │   ├── evals/
│   │   ├── references/
│   │   ├── .gitignore
│   │   ├── CHANGELOG.md
│   │   ├── README.md
│   │   ├── README_CN.md
│   │   └── SKILL.md
│   └── scholar-slides/
│       ├── assets/
│       ├── docs/
│       ├── learnings/
│       ├── references/
│       ├── scripts/
│       ├── .gitignore
│       ├── IMPLEMENTATION_PLAN.md
│       ├── install.sh
│       ├── LICENSE
│       ├── package-lock.json
│       ├── package.json
│       ├── pyproject.toml
│       ├── README.md
│       ├── requirements.txt
│       └── SKILL.md
├── sync/
│   ├── payload/
│   │   ├── claude/
│   │   ├── mcp/
│   │   ├── skills/
│   │   └── agent.md
│   ├── .gitignore
│   ├── README.md
│   └── sync_agent_config.md
├── tmp/
│   ├── cmp_short.py
│   ├── compare_upstreams.py
│   ├── probe_routes.py
│   ├── probe_search_variants.py
│   ├── test_fetch_variants.py
│   ├── test_glm_mimo.py
│   ├── test_long_output.py
│   ├── test_official_search.py
│   ├── test_opendesign_tools_api.py
│   ├── test_proxy_long.py
│   ├── verify_mimo.py
│   ├── verify_server_search.py
│   └── verify_tool_types.py
├── virtualenvs/
│   └── agent-shared-test/
│       ├── bin/
│       ├── lib/
│       ├── .gitignore
│       ├── .lock
│       ├── CACHEDIR.TAG
│       └── pyvenv.cfg
└── agent.md
```

## 各目录用途与同步映射

| 路径 | 用途 | 在本仓库的位置 |
|---|---|---|
| `agent.md` | 统一强制规则（含 §10.5 配置同步规则） | `payload/agent.md` |
| `MCP/` | MCP 服务器目录（各自带 `.mcp.json`） | `payload/mcp/` |
| `MCP/sync.py` | 把 MCP 配置分发到各 agent 客户端 | `payload/mcp/sync.py` |
| `skills/` | 四个 Agent 技能 | `payload/skills/` |
| `scope_recall/` | scope-recall 源码（独立 git 仓库） | ⛔ 不入库，见上游 repository |
| `virtualenvs/` | 共享 Python 环境（agent-shared-test） | ⛔ 不入库，按文档重建 |
| `tmp/` | 草稿与临时脚本 | ⛔ 不入库 |
| `sync/` | 本仓库（跨设备同步源） | 仓库根目录 |

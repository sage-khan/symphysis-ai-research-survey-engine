# Graph Report - symphysis-ai-research-survey-engine  (2026-09-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2620 nodes · 5357 edges · 144 communities (120 shown, 7 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 402 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2268ae3a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128

## God Nodes (most connected - your core abstractions)
1. `ToolResult` - 53 edges
2. `SurveyStorage` - 52 edges
3. `BaseTool` - 44 edges
4. `new_card()` - 41 edges
5. `ToolError` - 37 edges
6. `ModelSpec` - 37 edges
7. `HierarchicalBWMInstrument` - 37 edges
8. `Message` - 35 edges
9. `BaseAgent` - 32 edges
10. `load_card()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `test_write_model_escalation_logs_to_conversation()` --uses--> `SurveyStorage`  [INFERRED]
  tests/test_logger.py → src/symphysis/audit/logger.py
- `test_write_tool_call_logs_to_conversation()` --uses--> `SurveyStorage`  [INFERRED]
  tests/test_logger.py → src/symphysis/audit/logger.py
- `_run()` --calls--> `Terminate`  [INFERRED]
  src/symphysis/runtime/_openmanus_driver.py → vendor/openmanus/app/tool/terminate.py
- `_run()` --calls--> `ToolCollection`  [INFERRED]
  src/symphysis/runtime/_openmanus_driver.py → vendor/openmanus/app/tool/tool_collection.py
- `_guarded_run_with_payload()` --uses--> `InstrumentResult`  [INFERRED]
  tests/test_qa_precheck.py → src/symphysis/instruments/base.py

## Import Cycles
- None detected.

## Communities (144 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (55): OpenManusError, Exception, Raised when a tool encounters an error., Base exception for all OpenManus errors, ToolError, CLIResult, A ToolResult that can be rendered as a CLI output., Bash (+47 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (45): _build_survey_elicitation_agent_class(), BrowserAgent, Browser-only agent backed by the Browser Use CLI 3.0 MCP server., An agent that implements the SWEAgent paradigm for executing code and natural…, SWEAgent, Any, Execute tool calls and handle their results, Execute a single tool call with robust error handling (+37 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (55): AnthropicProvider, Any, Anthropic Claude provider. Requires ANTHROPIC_API_KEY in the environment., LLMProvider, ProviderError, ProviderResponse, Any, Exception (+47 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (59): _canonical(), issue_credential(), W3C-shaped Verifiable Credential issuance and verification. Separated from…, verify_credential(), AgentIdentity, _b58decode(), _b58encode(), did_key_from_public() (+51 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (41): BaiduSearchEngine, Baidu search engine. Returns results formatted according to SearchItem model., BaseModel, String representation of a search result item., Base class for web search engines., Perform a web search and return a list of search items. Args: query (str): The…, Represents a single search result item, SearchItem (+33 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (38): create_sandbox(), delete_sandbox(), get_or_start_sandbox(), Sandbox, Create a new sandbox with all required services configured and running., Delete a sandbox by its ID., Retrieve a sandbox by ID, check its state, and start it if needed., Start supervisord in a session. (+30 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (33): BytesIO, Exception, Exception classes for the sandbox system. This module defines custom exceptions…, Exception raised when a sandbox operation times out., Exception raised for resource-related errors., Base exception for sandbox-related errors., SandboxError, SandboxResourceError (+25 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (35): _extract_thinking(), _json_default(), Any, Path, Phase 4 model-tiering (docs/architecture/governance-layer-and-runtime-backends-…, Logged as this agent's first *self-answered* conversation-trace entry (see…, A single, human-readable rendering of this agent's completed survey: what it…, A one-line, human-readable summary of qa_checks.verify_sources_used's result,… (+27 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (25): AgentExecutor, EventQueue, RequestContext, Task, _browser_use_env(), Manus, Connect to an MCP server and add its tools., Disconnect from an MCP server and remove its tools. (+17 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (26): AgentCard, Path, Per-survey / per-agent persistent folder layout. surveys/<survey-id>/…, Symphysis (AI Research Survey Engine): config-driven agent panels for expert-…, The capability vocabulary + attenuation rule. A capability is a short, stable…, allowed(), Agent spawning: mint a child identity, attenuate its capabilities, and declare…, check_capability() (+18 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (27): GuardedRun, Any, Anti-hallucination / structural guardrails applied to every agent call. Four…, run_with_guardrails(), Instrument, InstrumentResult, Any, Protocol (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (29): Configuration for the execution sandbox, SandboxSettings, create_sandbox_client(), LocalSandboxClient, Runs command in sandbox. Args: command: Command to execute. timeout: Execution…, Reads file from container. Args: path: File path in container. Returns: File…, Writes file to container. Args: path: File path in container. content: File…, Creates a sandbox client. Returns: LocalSandboxClient: Sandbox client instance. (+21 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (18): A ToolResult that represents a failure., Represents the result of a tool execution., Returns a new ToolResult with the given fields replaced., ToolFailure, ToolResult, Execute the tool by making a remote call to the MCP server., PlanningTool, Create a new plan with the given ID, title, and steps. (+10 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (32): field_validator, ApiKeysIn, delete_preset(), get_api_key_status(), get_app_config(), get_global_rulefile(), get_llm_settings(), GlobalRulefileIn (+24 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (30): test_flags_hallucinated_model_not_actually_available(), test_gives_benefit_of_the_doubt_when_catalog_unreachable(), test_parses_a_mix_of_library_and_new_entries(), test_rejects_duplicate_new_agent_ids(), test_rejects_invalid_source_value(), test_rejects_library_entry_referencing_unknown_id(), test_rejects_malformed_json(), test_rejects_new_agent_id_colliding_with_library() (+22 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (20): AppConfig, BrowserSettings, Config, DaytonaSettings, get_project_root(), MCPServerConfig, MCPSettings, ProxySettings (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (17): BaseTool, Config, ABC, Any, BaseModel, Execute the tool with given parameters., Convert tool to function call format. Returns: Dictionary with tool metadata in…, Create a successful tool result. Args: data: Result data (dictionary or string)… (+9 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (20): Container, AsyncDockerizedTerminal, Initializes an asynchronous terminal for Docker containers. Args: container:…, Initializes the terminal environment. Ensures working directory exists and…, Ensures working directory exists in container. Raises: RuntimeError: If…, Executes a simple command using Docker's exec_run. Args: cmd: Command to…, Runs a command in the container with timeout. Args: cmd: Shell command to…, Closes the terminal session. (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (27): marked, oxlint, react, react-dom, @types/react, @types/react-dom, vite, @vitejs/plugin-react (+19 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (15): ChatCompletionMessage, TOOL_CHOICE_TYPE, BedrockClient, LLMSettings, Exception raised when the token limit is exceeded, TokenLimitExceeded, LLM, retry (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (15): Context, Sandbox, Get the current workspace state by reading all files, Execute a file operation in the sandbox environment. Args: action: The file…, Create a new file with the provided contents, Replace specific text in a file, Completely rewrite an existing file with new content, Delete a file at the given path (+7 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (17): MCPAgent, Agent for interacting with MCP (Model Context Protocol) servers. This agent…, Determine if tool execution should finish the agent, Clean up MCP connection when done., Run the agent with cleanup when done., MCPRunner, parse_args(), Namespace (+9 more)

### Community 22 - "Community 22"
Cohesion: 0.21
Nodes (23): main(), Verify the packaged `symphysis` distribution actually works installed…, DidSpec, EnvironmentSpec, GuardrailsSpec, ModelSpec, new_card(), RagSpec (+15 more)

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (25): AlgorithmType, AbnormalTrend, DbscanOutlier, DifferenceOutlier, ExtremeValue, LOFOutlier, MajorityValue, OverallTrending (+17 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (24): get-stdin, puppeteer, ts-node, @types/node, typescript, author, dependencies, get-stdin (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.12
Nodes (20): middleware, Request, health(), _no_cache(), get, Symphysis web backend. uvicorn web.backend.main:app --reload --port 8000 Serves…, Path, Shared path resolution: where this app's source lives and where survey projects… (+12 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (22): Argument, help, join, KNOWN_INSTRUMENTS, Option, add_agent(), _bundled_prompt_template_text(), _err() (+14 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (15): BaseFlow, Config, ABC, BaseModel, Base class for execution flows supporting multiple agents, Get the primary agent for the flow, Get a specific agent by key, Add a new agent to the flow (+7 more)

### Community 28 - "Community 28"
Cohesion: 0.19
Nodes (23): _corpus_path_for(), create_knowledge_base(), delete_knowledge_base(), delete_knowledge_base_file(), _kb_dir(), KnowledgeBaseIn, _list_files(), list_knowledge_bases() (+15 more)

### Community 29 - "Community 29"
Cohesion: 0.16
Nodes (23): patch, download_survey(), _existing_survey_dir(), get_analytics(), get_chart(), get_integrity_manifest(), get_results(), get_survey() (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.17
Nodes (21): _model_default(), Any, _rag_default(), _sampling_default(), _deep_merge(), get_config(), guardrail_default_denylist(), load_defaults() (+13 more)

### Community 31 - "Community 31"
Cohesion: 0.15
Nodes (19): ConfigError, load_survey_config(), Any, Exception, Path, Survey-level config loading and validation. Per-agent config now lives entirely…, Raised when a survey config fails validation., _read_yaml() (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (12): Event, One event in a run's execution trace, shaped to be written straight into…, OpenManusProvider, Satisfies `providers.base.LLMProvider`'s `complete(...)` interface by driving a…, _FakeBackend, Tests for runtime/openmanus.py. The AgentCard.model -> LLMSettings mapping and…, Stands in for OpenManusBackend so OpenManusProvider.complete() is unit-tested…, test_openmanus_provider_complete_ignores_flow_extra_when_not_survey_panel() (+4 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (13): ABC, Process current state and decide next action, Execute decided actions, Execute a single step: think and act., ReActAgent, AgentState, Memory, Enum (+5 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (11): DataAnalysis, A data analysis agent that uses planning to solve various data analysis tasks.…, A tool for Chart Generation Preparation, VisualizationPrepare, NormalPythonExecute, A tool for executing Python code with timeout and safety restrictions., main(), main() (+3 more)

### Community 35 - "Community 35"
Cohesion: 0.12
Nodes (22): asyncio, fixture, Tests sandbox network access., Tests sandbox cleanup process., Tests error handling with invalid configuration., Creates and manages a test sandbox instance., Tests sandbox working directory configuration., Tests sandbox file read/write operations. (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (14): ROLE_TYPE, BaseAgent, Config, ABC, BaseModel, model_validator, Execute the agent's main loop asynchronously. Args: request: Optional initial…, Abstract base class for managing agent state and execution. Provides… (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.22
Nodes (20): AgentCardError, load_card(), Exception, Reconstruct the signing identity from a loaded card. For a deterministic card…, rehydrate_identity(), _sample_card(), test_escalation_exempt_defaults_to_false(), test_escalation_exempt_round_trips_through_write_and_load() (+12 more)

### Community 38 - "Community 38"
Cohesion: 0.12
Nodes (10): AgentForm(), blankForm(), FALLBACK_DENYLIST, HelpTooltip(), AddFromLibrary(), AnalyticsTab(), IntegrityPanel(), STATUS_COLOR (+2 more)

### Community 39 - "Community 39"
Cohesion: 0.10
Nodes (12): setter, Retrieve a list of messages from the agent's memory., Set the list of messages in the agent's memory., Message, Create a tool message, Add a message to memory, Add multiple messages to memory, Get n most recent messages (+4 more)

### Community 40 - "Community 40"
Cohesion: 0.23
Nodes (19): HierarchicalBWMInstrument, _level_answer(), test_build_level_messages_includes_reference_material_when_present(), test_build_level_messages_scopes_to_one_level_only(), test_build_messages_includes_every_level_and_its_dimensions(), test_build_messages_includes_the_ratio_vs_score_warning_once(), test_build_messages_lists_available_source_tags_when_context_present(), test_levels_for_panel_returns_the_same_level_defs_as_params() (+11 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (5): Real, callable tools an Agent Card can grant to an agent (via its `tools:…, _base_urls(), _FakeResponse, fixture, requests_HTTPError()

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (11): PlanningFlow, Create an initial plan based on the request using the flow's LLM and…, Parse the current plan to identify the first non-completed step's index and…, Execute the current step with the specified agent using agent.run()., Mark the current step as completed., Get the current plan as formatted text., Finalize the plan and provide a summary using the flow's LLM directly., A flow that manages planning and execution of tasks using agents. (+3 more)

### Community 43 - "Community 43"
Cohesion: 0.16
Nodes (10): Any, Sandbox, Clean up a session if it exists., Execute a raw command directly in the sandbox., Tool for executing tasks in a Daytona sandbox with browser-use capabilities.…, Execute a browser action in the sandbox environment. Args: timeout: blocking:…, Clean up all sessions., Initialize with optional sandbox and thread_id. (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.12
Nodes (8): API_PROVIDERS, ApiKeySettings(), BASE_URL_PROVIDERS, ConfigSettings(), OllamaEndpointSettings(), RulesSettings(), refresh(), SettingsPage()

### Community 45 - "Community 45"
Cohesion: 0.19
Nodes (16): A single agent instance: identity (DID, from its Agent Card) + one elicitation…, Per-agent tool registry: the set of real, callable tools an agent's granted…, _config(), _crawl4ai_base_url(), _discover(), _extract_markdown(), Any, Exception (+8 more)

### Community 46 - "Community 46"
Cohesion: 0.22
Nodes (15): BWMInstrument, Any, Best-Worst Method instrument. Dimensions, labels, and the task wording are all…, test_build_messages_falls_back_to_general_knowledge_only_with_no_context(), test_build_messages_includes_all_dimensions_and_context(), test_build_messages_lists_real_source_tags_when_context_is_present(), test_parse_accepts_a_response_missing_sources_used_entirely(), test_parse_accepts_a_response_with_sources_used() (+7 more)

### Community 47 - "Community 47"
Cohesion: 0.19
Nodes (16): compute_global_weights(), LevelSolution, Any, Solves a hierarchical BWM survey (see instruments/hierarchical_bwm.py): one…, One line per level whose criterion is itself named by another level (i.e. every…, agent_payloads: this level's [{"best", "worst", "best_to_others",…, The weight of a leaf criterion within its own top-level branch's scope: its own…, render_populated_equations() (+8 more)

### Community 48 - "Community 48"
Cohesion: 0.22
Nodes (16): test_parses_a_well_formed_proposal(), test_propose_survey_concept_calls_the_provider_and_parses_its_response(), test_rejects_an_unknown_instrument(), test_rejects_duplicate_criterion_codes(), test_rejects_empty_criteria_list(), test_rejects_malformed_json(), test_rejects_missing_required_field(), test_rejects_no_json_object() (+8 more)

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (18): manager(), asyncio, fixture, Tests automatic cleanup of idle sandboxes., Tests manager cleanup functionality., Creates a sandbox manager instance. Uses function scope to ensure each test…, Creates a temporary test file., Tests sandbox creation. (+10 more)

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (11): Counter, build_retriever(), Chunk, EmbeddingRetriever, _load_chunks(), Path, Minimal, pluggable RAG retriever. Loads every .txt/.md file under a corpus…, Dependency-free fallback: cosine similarity over TF-IDF vectors. (+3 more)

### Community 51 - "Community 51"
Cohesion: 0.18
Nodes (12): Popen, Opaque handle a backend returns from spawn(); passed back into…, RunHandle, isolated_venv_ready(), OpenManusBackend, OpenManusHandle, Path, The flagship, multi-turn/tool-using RuntimeBackend, driving a vendored, pinned… (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (11): Signature, MCPServer, parse_args(), Namespace, Clean up server resources., Register all tools with the server., Parse command line arguments., MCP Server implementation with tool registration and management. (+3 more)

### Community 53 - "Community 53"
Cohesion: 0.22
Nodes (6): Agent, _extract_json_object(), Any, A single, un-repeated preliminary turn: the agent is told its real, actual…, The single seam Phase 2 (docs/architecture/governance-layer-and-runtime-…, Best-effort JSON extraction from a raw completion, tolerant of a model wrapping…

### Community 54 - "Community 54"
Cohesion: 0.21
Nodes (14): AHPInstrument, build_full_matrix(), _pair_key(), Any, Analytic Hierarchy Process instrument (Saaty, 1980). Dimensions and labels come…, Expand a validated upper-triangular comparisons dict into the full n x n…, test_build_full_matrix_is_reciprocal_and_has_unit_diagonal(), test_build_messages_lists_every_pair_exactly_once() (+6 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (16): covered(), escalated_level_ids(), normalize_path(), Any, The one authorization decision point. Every yes/no capability check in this…, Which level ids in `levels` have MORE criteria (dimensions) than `threshold` —…, should_escalate(), Tests for policy/engine.py's Phase 4 escalation predicates… (+8 more)

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (5): Path, _seed_manual_response(), test_add_agent_creates_a_card_with_bundled_prompt_template(), test_run_checks_provider_availability_first_and_prints_it(), test_run_then_report_round_trip()

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (10): Initialize connections to configured MCP servers., Connect to an MCP server and add its tools., Disconnect from an MCP server and remove its tools., Delete a sandbox by ID., Clean up Manus agent resources., Process current state and decide next actions with appropriate context., A versatile general-purpose agent with support for both local and MCP tools., Factory method to create and properly initialize a Manus instance. (+2 more)

### Community 58 - "Community 58"
Cohesion: 0.24
Nodes (15): _candidates_from_text(), _extract_text_docx(), _extract_text_pdf(), parse_docx(), parse_pdf(), Best-effort PDF/DOCX candidate-dimension extraction. Extracts full text, then…, parse_lss(), Best-effort LimeSurvey .lss (XML export) parser. .lss files enumerate every… (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.23
Nodes (17): _agent_card_module(), assign_to_survey(), create_library_agent(), delete_library_agent(), get_library_agent(), _library_path(), list_library_agents(), Any (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.20
Nodes (18): create_agent(), delete_agent(), get_agent(), get_lineage(), get_trace(), list_agents(), list_models_for_provider(), Any (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.28
Nodes (15): PermissionsSpec, What this agent may touch. Enforced by guardrails.py, not advisory., check_data_scope(), check_provider_allowed(), PermissionError_, Exception, Permission checks derived from an AgentCard's PermissionsSpec. Enforced, not…, Distinct name from the builtin PermissionError to avoid confusing the two in a… (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.24
Nodes (16): compute_file_hashes(), compute_root_hash(), _iter_files(), load_manifest(), Any, Path, Tamper-evidence for a completed survey's full output. Every prompt, response,…, Recomputes every file's hash right now and compares against the stored… (+8 more)

### Community 63 - "Community 63"
Cohesion: 0.26
Nodes (16): build_registry(), Any, One registry per agent run. Only includes a tool the agent's card actually…, _make_agent(), Path, Tests for tools/registry.py: build_registry() wraps the SAME retriever…, test_citation_verify_wraps_qa_checks(), test_instrument_submit_execute_accepts_a_correct_level_answer() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.23
Nodes (14): _FakeProvider, _guarded_run_with_payload(), _make_agent(), Path, Tests for the QA precheck (Agent.run_qa_precheck), the global/agent rulefile…, test_qa_precheck_ground_truth_reflects_real_configuration(), test_role_description_appends_global_and_agent_rulefiles(), test_role_description_omits_rules_section_when_both_are_empty() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (10): ComputerUseTool, ClientSession, Sandbox, Computer automation tool for controlling the desktop environment., Initialize with optional sandbox., Factory method to create a tool with sandbox., Get or create aiohttp session for API requests., Send request to automation service API. (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.18
Nodes (16): create_survey(), CreateSurveyIn, CriterionIn, delete_survey(), propose_concept(), ProposeConceptIn, BaseModel, delete (+8 more)

### Community 67 - "Community 67"
Cohesion: 0.12
Nodes (15): ./node_modules/@types, src/**/*.ts, src/types, compilerOptions, allowJs, checkJs, esModuleInterop, forceConsistentCasingInFileNames (+7 more)

### Community 68 - "Community 68"
Cohesion: 0.24
Nodes (15): check_agent_card_paths_providers(), check_hosted_provider(), check_manual(), check_ollama(), check_provider(), check_providers(), check_survey_providers(), ProviderStatus (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.28
Nodes (14): _check_hierarchical_levels(), fix_survey(), Any, Path, Every problem found, as a plain human-readable string; an empty list means the…, Path, test_fix_survey_reports_a_dangling_rag_corpus_path(), test_fix_survey_reports_a_missing_system_prompt_template() (+6 more)

### Community 70 - "Community 70"
Cohesion: 0.32
Nodes (12): _FakeProvider, _make_agent(), Path, Tests for Agent.run()'s Phase 4 branch (docs/architecture/governance-layer-and-…, _stub_qa_precheck(), test_escalation_exempt_card_never_escalates(), test_escalation_switches_model_when_a_level_exceeds_threshold(), test_flat_instrument_never_escalates() (+4 more)

### Community 71 - "Community 71"
Cohesion: 0.14
Nodes (8): Refresh the list of available tools from the MCP server. Returns: A tuple of…, Process current state and decide next action., Initialize the MCP connection. Args: connection_type: Type of connection to use…, Process current state and decide next actions using tools, Any, Create a system message, Create an assistant message, Create ToolCallsMessage from raw tool calls. Args: tool_calls: Raw tool calls…

### Community 72 - "Community 72"
Cohesion: 0.25
Nodes (3): Chat, ChatCompletions, OpenAIResponse

### Community 73 - "Community 73"
Cohesion: 0.15
Nodes (8): DockerSession, Asynchronous Docker Terminal This module provides asynchronous terminal…, Reads output until prompt is found. Returns: String containing output up to the…, Executes a command and returns cleaned output. Args: command: Shell command to…, Initializes a Docker session. Args: container_id: ID of the Docker container., Sanitizes the command string to prevent shell injection. Args: command: Raw…, Creates an interactive session with the container. Args: working_dir: Working…, Cleans up session resources. 1. Sends exit command 2. Closes socket connection…

### Community 74 - "Community 74"
Cohesion: 0.18
Nodes (8): CreateChatCompletion, Any, Get type information for a single type., Create schema for Union types., Execute the chat completion with type conversion. Args: required: List of…, Initialize with a specific response type., Build parameters schema based on response type., Create a JSON schema for the given type.

### Community 75 - "Community 75"
Cohesion: 0.18
Nodes (9): asyncio, Test cases for AsyncDockerizedTerminal., Test basic command execution functionality., Test environment variable setting and access., Test working directory setup., Test command timeout functionality., Test execution of multiple commands in sequence., Test proper cleanup of resources. (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.20
Nodes (10): StatusDot(), formatDate(), NewSurveyPanel(), handleCreate(), handleFile(), handlePropose(), slugify(), SurveysPage() (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.25
Nodes (8): react, api, App(), NAV, AgentLibraryPage(), handleDelete(), refresh(), shortDid()

### Community 78 - "Community 78"
Cohesion: 0.23
Nodes (12): _has_retrievable_content(), Path, _make_agent(), Path, Tests for Agent's context-gathering: the shared survey-level knowledge repo…, test_agent_picks_up_shared_knowledge_repo_with_no_per_agent_flag(), test_has_retrievable_content_false_for_missing_or_empty_dir(), test_has_retrievable_content_true_when_md_or_txt_present() (+4 more)

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (12): SurveyConfig, _per_agent_entries(), Drives one full survey run: spawn agents, run the configured instrument, solve…, Re-solve and re-render the report/charts from each agent's own already-accepted…, One (per_agent_meta, per_agent_detail) pair for a single accepted sample…, regenerate_report(), run_survey(), Path (+4 more)

### Community 80 - "Community 80"
Cohesion: 0.18
Nodes (11): Hierarchical Best-Worst Method instrument: a survey defines several BWM…, build_precheck_ground_truth(), extract_source_tags(), Any, Genuineness checks: verifying an agent's stated identity and cited sources…, The distinct bracket tags (for example "role knowledge: data_engineer" or…, Check a response's self-reported sources_used list against what was genuinely…, The real configuration this agent was actually given, computed from its… (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.14
Nodes (9): Protocol, The RuntimeBackend protocol every execution backend implements. Per…, Every backend implements exactly these three operations. Backends are…, Start (or prepare) a run for the given task. Must not block for the full…, Yield this run's events in order as they occur, ending with a terminal event…, Best-effort cancellation. A backend with nothing to cancel (a single already-…, RuntimeBackend, test_run_handle_and_event_are_plain_dataclasses() (+1 more)

### Community 84 - "Community 84"
Cohesion: 0.22
Nodes (7): Calculate tokens for message content, Calculate tokens for tool calls, Calculate the total number of tokens in a message list, Calculate tokens for a text string, Calculate tokens for an image based on detail level and dimensions For "low"…, Calculate tokens for high detail images based on dimensions, TokenCounter

### Community 85 - "Community 85"
Cohesion: 0.21
Nodes (13): AgentIn, _cfg(), _default_denylist(), GuardrailsIn, list_providers(), list_role_packs(), ModelIn, PermissionsIn (+5 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (8): What a backend is asked to do for one agent turn: the same inputs Agent.run()…, TaskSpec, DirectCompletionBackend, DirectCompletionHandle, The trivial/default RuntimeBackend: a single completion call. Per the plan…, Satisfies the RuntimeBackend protocol with exactly the single-call behavior…, test_backend_spawn_writes_survey_panel_fields_into_the_driver_spec(), test_spawn_raises_actionable_error_when_isolated_venv_missing()

### Community 87 - "Community 87"
Cohesion: 0.26
Nodes (11): aggregate_individual_priorities(), AHPSolution, ndarray, Classical Analytic Hierarchy Process (Saaty, 1980), generic over any criteria…, Combine multiple agents' independently solved priority vectors into one group…, solve_ahp(), test_aggregate_individual_priorities_geometric_mean(), test_solve_ahp_flags_a_wildly_inconsistent_matrix() (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.32
Nodes (11): _card(), Path, test_classifies_each_agent_status_correctly(), test_empty_survey_has_no_agents(), test_no_result_json_is_in_progress_while_running_but_skipped_once_stopped(), _write(), compute_analytics(), Any (+3 more)

### Community 89 - "Community 89"
Cohesion: 0.15
Nodes (7): Protocol, Copies file from container to local. Args: container_path: File path in…, Copies file from local to container. Args: local_path: Local source file path.…, Reads file content from container. Args: path: File path in container. Returns:…, Writes content to file in container. Args: path: File path in container.…, Protocol for sandbox file operations., SandboxFileOperations

### Community 90 - "Community 90"
Cohesion: 0.26
Nodes (12): delete_knowledge_file(), _knowledge_dir(), list_knowledge_files(), Any, delete, get, Path, post (+4 more)

### Community 91 - "Community 91"
Cohesion: 0.27
Nodes (5): Hashable, DataVisualization, Any, model_validator, Initialize llm with default settings if not provided.

### Community 92 - "Community 92"
Cohesion: 0.27
Nodes (5): Any, Public entry point signaling this instrument supports per-level panel…, Per-level counterpart to build_messages(), used only by the "survey_panel"…, Per-level field/value validation, shared by parse() (validating every level in…, Validate ONE level's answer in isolation, independent of every other level's…

### Community 93 - "Community 93"
Cohesion: 0.38
Nodes (11): BayesianResult, _closed_form_weights(), combine_panels(), _credal_matrix(), ndarray, Bayesian Best-Worst Method (Mohammadi and Rezaei, 2020), generic over any…, HAWC-BWM draw-wise linear pool: w_combined = alpha*w_human + (1-alpha)*w_agent,…, solve() (+3 more)

### Community 94 - "Community 94"
Cohesion: 0.35
Nodes (9): _FakeProvider, _make_agent(), Path, Tests for Agent.run()'s Phase 3 branch: a hierarchical instrument run through…, _stub_qa_precheck(), test_flat_instrument_on_openmanus_backend_gets_no_panel_kwargs(), test_hierarchical_instrument_on_direct_completion_backend_gets_no_panel_kwargs(), test_hierarchical_instrument_on_openmanus_backend_gets_survey_panel_extra_kwargs() (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.29
Nodes (10): _make_survey_dir(), Path, test_manifest_excludes_its_own_files(), test_sha256sums_file_is_sha256sum_dash_c_compatible_format(), test_verify_detects_a_changed_file(), test_verify_detects_a_removed_file(), test_verify_detects_an_added_file(), test_verify_passes_when_nothing_changed() (+2 more)

### Community 96 - "Community 96"
Cohesion: 0.18
Nodes (8): PlanStepStatus, Enum, str, Enum class defining possible statuses of a plan step, Return a list of all possible step status values, Return a list of values representing active statuses (not started or in…, Generate plan text directly from storage if the planning tool fails., Return a mapping of statuses to their marker symbols

### Community 97 - "Community 97"
Cohesion: 0.17
Nodes (5): BaseSandboxClient, ABC, Base sandbox client interface., Copies file from container., Copies file to container.

### Community 98 - "Community 98"
Cohesion: 0.17
Nodes (6): Prepares volume binding configuration. Returns: Volume binding configuration…, Ensures directory exists on the host. Args: path: Directory path. Returns:…, Cleans up sandbox resources., Async context manager entry., Async context manager exit., Creates and starts the sandbox container. Returns: Current sandbox instance.…

### Community 99 - "Community 99"
Cohesion: 0.35
Nodes (10): Any, Path, Markdown report generation, with matplotlib charts saved alongside it. Chart…, render_ahp_charts(), render_ahp_report(), render_charts(), render_hierarchical_bwm_charts(), render_hierarchical_bwm_report() (+2 more)

### Community 100 - "Community 100"
Cohesion: 0.25
Nodes (10): A short, generated methodology paragraph plus the run's actual genuineness…, Every contributing agent's own answer, reasoning, cited sources, and QA…, render_methodology_section(), render_per_agent_detail_section(), test_methodology_section_embeds_chart_images_with_relative_paths(), test_methodology_section_handles_an_unknown_instrument_without_raising(), test_methodology_section_names_the_instrument_and_agent_count(), test_per_agent_detail_section_flags_a_failed_qa_precheck() (+2 more)

### Community 101 - "Community 101"
Cohesion: 0.29
Nodes (10): _build_instrument_submit_proxy_tool_class(), _build_proxy_tool_class(), _build_survey_panel_flow_class(), _emit(), main(), Standalone driver script, executed as a subprocess under…, Phase 3's InstrumentSubmit tool: a ProxyTool (see above) with extra bookkeeping…, Phase 3 (docs/architecture/governance-layer-and-runtime-backends-plan.md tasks… (+2 more)

### Community 102 - "Community 102"
Cohesion: 0.31
Nodes (9): client(), _make_survey(), fixture, Path, End-to-end test of GET /api/surveys/{id}/preflight against a real (temp-…, test_preflight_deduplicates_across_multiple_agents_on_the_same_provider(), test_preflight_reports_failure_for_an_unset_hosted_api_key(), test_preflight_reports_ok_for_manual_only_agents() (+1 more)

### Community 103 - "Community 103"
Cohesion: 0.31
Nodes (10): _bayesian_to_dict(), _load_human_responses(), Any, Path, Solve the configured instrument over already-collected agent payloads and write…, Generic per-expert JSON list: [{"expert_id", "best", "worst", "best_to_others",…, _solve_ahp(), _solve_and_write_report() (+2 more)

### Community 104 - "Community 104"
Cohesion: 0.29
Nodes (9): get_role_pack_text(), list_role_packs(), _parse(), Path, Standard role knowledge packs: short, curated professional-domain primers that…, Every available pack, discovered from the filesystem: never a hardcoded list,…, The pack's body content (title/summary header stripped), or None if pack_id is…, RolePackInfo (+1 more)

### Community 105 - "Community 105"
Cohesion: 0.27
Nodes (8): client(), _make_survey_with_manifest(), fixture, Path, End-to-end test of the integrity-manifest HTTP endpoints against a real (temp-…, test_get_integrity_manifest_returns_it_after_a_run(), test_verify_integrity_fails_after_a_file_is_altered(), test_verify_integrity_passes_when_untouched()

### Community 106 - "Community 106"
Cohesion: 0.27
Nodes (8): downloadJson(), downloadJsonl(), groupLineageByParent(), KIND_LABEL, TABS, TraceViewer(), handleDownloadCard(), handleDownloadLog()

### Community 107 - "Community 107"
Cohesion: 0.22
Nodes (4): ListToolsResult, List all available tools., FakeSession, ClientSession

### Community 109 - "Community 109"
Cohesion: 0.36
Nodes (6): _FakeProvider, Tests for the trivial/default RuntimeBackend (runtime/ollama.py). Provider is…, _task(), test_spawn_returns_handle_carrying_the_task(), test_stop_is_a_no_op(), test_stream_events_yields_exactly_one_raw_completion()

### Community 110 - "Community 110"
Cohesion: 0.25
Nodes (4): BrowserContextHelper, Gets browser state and formats the browser prompt., model_validator, Initialize basic components synchronously.

### Community 111 - "Community 111"
Cohesion: 0.33
Nodes (8): AgentsTab(), handleDelete(), refresh(), formatBytes(), KnowledgeTab(), handleDelete(), handleUpload(), shortDid()

### Community 112 - "Community 112"
Cohesion: 0.25
Nodes (7): oxc, warn, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 113 - "Community 113"
Cohesion: 0.46
Nodes (7): _add_manual_agent(), _level_answer(), Path, End-to-end orchestrator test using the real, complete 7-level TrustRouter…, test_full_trustrouter_hierarchy_runs_end_to_end(), _write_prompt_template(), _write_survey()

### Community 114 - "Community 114"
Cohesion: 0.25
Nodes (3): client(), fixture, End-to-end test of the reusable knowledge-base HTTP endpoints: create, list,…

### Community 115 - "Community 115"
Cohesion: 0.32
Nodes (6): run_survey_endpoint(), get_status(), Any, Path, In-process background-run tracker. A survey run calls real LLMs and a PyMC…, start_run()

### Community 116 - "Community 116"
Cohesion: 0.39
Nodes (6): KnowledgeBasesTab(), handleCreate(), handleDelete(), handleDeleteFile(), handleFileChosen(), refresh()

### Community 117 - "Community 117"
Cohesion: 0.43
Nodes (6): slow, The concentration hyperprior must be the diffuse Gamma(0.01, 0.01) from the…, _synthetic_responses(), test_bootstrap_produces_valid_posterior(), test_combine_panels_sweep_endpoints_match_each_panel(), test_pymc_prior_matches_reference_diffuse_gamma()

### Community 118 - "Community 118"
Cohesion: 0.43
Nodes (5): BWMSolution, Classical Best-Worst Method (Rezaei, 2015), generic over any criteria set.…, solve_bwm(), test_solve_bwm_basic_consistency(), test_solve_bwm_rejects_unknown_pattern_gracefully()

### Community 119 - "Community 119"
Cohesion: 0.40
Nodes (5): _agent_body(), client(), fixture, End-to-end test of the Agent Library HTTP endpoints: create in the library,…, test_library_crud_and_assign_to_survey()

### Community 120 - "Community 120"
Cohesion: 0.33
Nodes (3): client(), fixture, End-to-end test of POST /api/surveys/propose-concept against a real FastAPI…

### Community 121 - "Community 121"
Cohesion: 0.40
Nodes (4): OpenManusProviderError, Any, Exception, Raised when an OpenManus-backed run ends without a usable `raw_completion`…

### Community 126 - "Community 126"
Cohesion: 0.67
Nodes (3): skipif, A real smoke test against the isolated venv's python interpreter and the actual…, test_spawn_and_stream_events_against_isolated_venv()

## Knowledge Gaps
- **73 isolated node(s):** `Config`, `Config`, `Config`, `Config`, `KIND_LABEL` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 969 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentCard` connect `Community 9` to `Community 37`, `Community 7`, `Community 8`, `Community 45`, `Community 78`, `Community 79`, `Community 53`, `Community 22`?**
  _High betweenness centrality (0.292) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 9`?**
  _High betweenness centrality (0.291) - this node is a cross-community bridge._
- **Why does `_run()` connect `Community 101` to `Community 1`, `Community 33`, `Community 39`, `Community 71`, `Community 42`, `Community 74`, `Community 19`, `Community 115`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `SurveyStorage` (e.g. with `_make_agent()` and `_make_agent()`) actually correct?**
  _`SurveyStorage` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ToolError` (e.g. with `Bash` and `_BashSession`) actually correct?**
  _`ToolError` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `Config`, `Config` to the rest of the system?**
  _73 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04165733482642777 - nodes in this community are weakly interconnected._
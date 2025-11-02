# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LocalLLM Code is a Python-based agentic coding tool designed as a Claude Code clone that works with local LLMs via LM Studio. It provides an intelligent development assistant that can understand project structure, execute ReAct loops for problem-solving, and perform various coding tasks through natural language interaction.

**Main Entry Point**: `localllm_agent.py` - The core application implementing the full agent system
**Setup Script**: `setup_script.py` - Creates demo projects and installs dependencies

## Architecture

The codebase follows a modular architecture with these key components:

### Core Classes

1. **LocalLLMCode** (main application class)
   - Orchestrates the entire system
   - Manages configuration, initialization, and interactive mode
   - Located in `localllm_agent.py:1019-1166`

2. **ReActAgent** (thinking-action-observation loop)
   - Implements the core ReAct loop for autonomous task execution
   - Handles LLM interaction and tool orchestration
   - Located in `localllm_agent.py:623-694`

3. **ProjectAnalyzer** (project DNA analysis)
   - Analyzes project structure, languages, frameworks, and patterns
   - Generates project "DNA" for context-aware assistance
   - Located in `localllm_agent.py:158-527`

4. **ToolSystem** (file and system operations)
   - Provides safe file operations, command execution, and Git integration
   - Implements security checks and sandboxing
   - Located in `localllm_agent.py:695-1018`

5. **SmartContextManager** (intelligent context selection)
   - Optimizes context window usage by selecting relevant files
   - Uses relevance scoring based on file patterns and recency
   - Located in `localllm_agent.py:81-157`

6. **LLMClient** (multi-provider LLM interface)
   - Supports LM Studio, Azure, and Gemini (planned)
   - Handles streaming responses and error recovery
   - Located in `localllm_agent.py:528-622`

## Common Development Commands

**Run the main application**:
```bash
python localllm_agent.py
```

**Run with specific prompt**:
```bash
python localllm_agent.py -p "Your prompt here"
```

**Setup demo environment**:
```bash
python setup_script.py
```

**Testing commands** (from config):
```bash
python -m pytest  # Run tests
flake8 .          # Lint code
black .           # Format code
```

## Configuration

The application uses TOML configuration files:
- **Project config**: `localllm.toml` (created per project)
- **Global config template**: `localllm_config.txt`

Key configuration sections:
- `[llm]` - LLM provider settings (lmstudio, azure, gemini)
- `[safety]` - Security controls and confirmation requirements
- `[project]` - File patterns, ignore lists, memory file location
- `[commands.aliases]` - Custom command shortcuts

## Project Memory System

The application automatically generates `LOCALLLM.md` files containing:
- Project DNA analysis (languages, frameworks, architecture patterns)
- Directory structure mapping
- Coding style analysis
- Common operations and patterns

This memory system enables context-aware assistance across sessions.

## Security Features

- **Safe Mode**: Default confirmation prompts for destructive operations
- **Path Validation**: Restricts operations to project directory
- **Command Filtering**: Blocks potentially dangerous shell commands
- **Automatic Backups**: Creates `.backup` files before edits

## Tool System

Available tools for the ReAct agent:
- `read_file`, `write_file`, `edit_file`, `create_file` - File operations
- `list_files`, `search_files` - Directory and content search
- `run_command` - Safe shell command execution
- `git_status`, `git_commit` - Git integration
- `analyze_code` - Code structure analysis

## LLM Provider Support

- **Primary**: LM Studio (OpenAI-compatible API at localhost:1234)
- **Planned**: Azure ChatGPT, Google Gemini
- **Streaming**: Real-time response display supported

## Dependencies

Core Python dependencies (auto-installed):
- `rich` - Terminal UI and formatting
- `aiohttp` - Async HTTP for LLM communication
- `asyncio` - Async operations
- Standard library: `pathlib`, `subprocess`, `json`, `re`

## Usage Patterns

1. **Interactive Mode**: Start with `python localllm_agent.py` for conversational development
2. **One-shot Mode**: Use `-p` flag for single commands
3. **Project Analysis**: Agent automatically analyzes project on startup
4. **ReAct Loop**: Agent thinks, acts with tools, observes results, and continues until task completion

## Safety Considerations

- Always operates in safe mode by default
- Requires user confirmation for file modifications and command execution
- Implements path traversal protection
- Creates automatic backups before destructive operations
- Blocks known dangerous command patterns
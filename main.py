#!/usr/bin/env python3
"""
LocalLLM Code - Revolutionary Agentic Coding Tool
A paradigm-shifting development agent that understands your project's DNA
"""

import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# 国際化システムをインポート
from localllm.core import t, set_locale, get_locale

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich.table import Table
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.columns import Columns
    console = Console()
except ImportError:
    print("美しい出力のためrichをインストール中...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich.table import Table
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.columns import Columns
    console = Console()

# Import modular components
from localllm.core.project_dna import ProjectDNA
from localllm.core.context_manager import SmartContextManager
from localllm.llm.analyzers import ProjectAnalyzer
from localllm.llm.clients import LLMClient
from localllm.agents.react_agent import ReActAgent
from localllm.agents.multi_agent import MultiAgentSystem
from localllm.tools.tool_system import ToolSystem
from localllm.memory.external_memory import ExternalMemorySystem

class LocalLLMCode:
    """メインアプリケーションクラス"""
    
    def __init__(self, dry_run: bool = False):
        self.root_path = Path.cwd()
        self.config = self._load_config()
        self.project_dna = None
        self.llm_client = None
        self.agent = None
        self.context_manager = SmartContextManager()
        self.external_memory = ExternalMemorySystem(self.root_path)
        self.dry_run = dry_run
        self.experimental_features = self.config.get('experimental', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """設定を読み込み"""
        config_file = self.root_path / 'localllm.toml'
        
        if config_file.exists():
            try:
                import tomllib
                with open(config_file, 'rb') as f:
                    return tomllib.load(f)
            except ImportError:
                console.print("[yellow]Warning: tomllib not available, using default config[/yellow]")
        
        # デフォルト設定
        return {
            'llm': {
                'provider': 'lmstudio',
                'model': 'default',
                'context_size': 8192,
                'stream': True
            },
            'lmstudio': {
                'server_url': 'http://localhost:1234',
                'model': 'default'
            },
            'safety': {
                'require_confirmation': True,
                'allow_dangerous_commands': False,
                'sandbox_mode': False
            }
        }
    
    async def initialize(self):
        """初期化処理"""
        console.print(f"🚀 [bold blue]{t('startup_banner')}[/bold blue]")
        
        # 外部記憶システムのセットアップ
        self.external_memory.show_cleanup_prompt()
        
        console.print(t("initializing_analysis"))
        
        # プロジェクトDNA分析
        analyzer = ProjectAnalyzer()
        self.project_dna = analyzer.analyze_project(self.root_path)
        
        # LLMクライアント初期化
        self.llm_client = LLMClient(self.config.get('lmstudio', {}))
        
        # ツールシステム初期化
        tools = ToolSystem(
            self.root_path, 
            safe_mode=self.config.get('safety', {}).get('require_confirmation', True),
            mcp_servers=self.config.get('mcp_servers', {})
        )
        
        # マルチエージェントシステム初期化
        multi_agent_system = None
        llm_configs = {}
        
        # 各プロバイダーの設定を収集
        if self.config.get('lmstudio'):
            llm_configs['lmstudio'] = self.config.get('lmstudio', {})
        if self.config.get('azure', {}).get('api_key'):
            llm_configs['azure'] = self.config.get('azure', {})
        if self.config.get('gemini', {}).get('api_key'):
            llm_configs['gemini'] = self.config.get('gemini', {})
        
        if len(llm_configs) > 0:
            multi_agent_system = MultiAgentSystem(llm_configs, self.project_dna)
            console.print(f"🤖 [cyan]Multi-agent system initialized: {multi_agent_system.get_status_summary()}[/cyan]")
            
            # ボス相談の初期設定を提案
            if multi_agent_system.can_use_boss_consultation():
                console.print("💡 [yellow]Tip: Use '/boss setup' to configure boss consultation mode[/yellow]")
        
        # エージェント初期化
        await self.llm_client.__aenter__()
        self.agent = ReActAgent(
            self.llm_client, 
            self.project_dna, 
            tools, 
            self.dry_run, 
            multi_agent_system,
            self.external_memory
        )
        
        console.print(f"✅ [green]{t('initialization_complete')}[/green]")
        if self.dry_run:
            console.print(f"🧪 [magenta]{t('dry_run_mode')}[/magenta]")
        
        # 実験的機能の表示
        enabled_experimental = [k for k, v in self.experimental_features.items() if v]
        if enabled_experimental:
            console.print(f"🧪 [yellow]Experimental features enabled: {', '.join(enabled_experimental)}[/yellow]")
        
        console.print(f"📊 Project: {self.project_dna.language} ({self.project_dna.complexity_score:.1f}/10 complexity)")
        console.print(f"🧬 Frameworks: {', '.join(self.project_dna.frameworks) or 'None detected'}")
        
        # 外部記憶の要約表示
        memory_summary = self.external_memory.get_memory_summary()
        console.print(f"🧠 External Memory: {memory_summary}")
        
        # セッションの開始を記録
        self.external_memory.record_console_output(f"Session started: {self.project_dna.language} project", "session")
    
    async def interactive_mode(self):
        """インタラクティブモード"""
        console.print(f"\n💬 [bold cyan]{t('interactive_mode')}[/bold cyan]")
        console.print(t("type_help"))
        
        while True:
            try:
                user_input = Prompt.ask(f"\n{t('you')}")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    break
                
                if user_input.startswith('/'):
                    should_continue = await self._handle_session_command(user_input)
                    if should_continue is False:
                        break
                    continue
                
                # エージェントで処理
                response = await self.agent.execute(user_input)
                
                console.print(f"\n{t('assistant')}")
                console.print(Markdown(response))
                
            except KeyboardInterrupt:
                console.print(f"\n👋 [yellow]{t('goodbye')}[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]{t('error', e=e)}[/red]")
    
    async def _handle_session_command(self, command: str):
        """セッション内コマンドを処理"""
        parts = command[1:].split()
        cmd = parts[0] if parts else ""
        
        if cmd == 'help':
            self._show_help()
        elif cmd == 'status':
            self._show_status()
        elif cmd == 'exit':
            console.print("👋 [yellow]Goodbye![/yellow]")
            return False
        elif cmd == 'reset':
            self._reset_session()
        elif cmd == 'memory':
            await self._handle_memory_command(parts[1:] if len(parts) > 1 else [])
        elif cmd == 'todo':
            await self._handle_todo_command(parts[1:] if len(parts) > 1 else [])
        elif cmd == 'wise':
            await self._handle_wise_command(parts[1:] if len(parts) > 1 else [])
        elif cmd == 'boss':
            await self._handle_boss_command(parts[1:] if len(parts) > 1 else [])
        elif cmd == 'agents':
            self._show_agents_status()
        elif cmd == 'agent':
            await self._execute_subagent(parts[1] if len(parts) > 1 else None, parts[2:] if len(parts) > 2 else [])
        elif cmd == 'config':
            await self._handle_config_command(parts[1:] if len(parts) > 1 else [])
        else:
            console.print(f"[red]{t('unknown_command', cmd=cmd)}[/red]")
            console.print(t("type_help"))
        
        return True
    
    def _show_help(self):
        """ヘルプを表示"""
        help_text = f"""
## {t('help_title')}

### {t('help_basic')}
- `/help` - {t('help_session')}
- `/status` - {t('help_status')}
- `/exit` - {t('help_exit')}
- `/reset` - {t('help_reset')}
- `/config` - {t('help_config_show')}

### {t('help_agents')}
- `/agents` - {t('help_agents_list')}
- `/wise` - {t('help_wise')}
- `/boss` - {t('help_boss')}

### {t('help_memory_section')}
- `/memory` - {t('help_memory')}
- `/memory search <クエリ>` - {t('help_memory_search')}
- `/memory cleanup` - {t('help_memory_cleanup')}

### {t('help_todo')}
- `/todo` - {t('help_todo_list')}

### {t('help_usage')}
{t('help_examples')}
"""
        console.print(Markdown(help_text))
    
    def _show_status(self):
        """現在の状態を表示"""
        table = Table(title="Current Status")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Project Path", str(self.root_path))
        table.add_row("Language", self.project_dna.language)
        table.add_row("Complexity", f"{self.project_dna.complexity_score:.1f}/10")
        table.add_row("Frameworks", ", ".join(self.project_dna.frameworks) or "None")
        table.add_row("LLM Provider", self.config.get('llm', {}).get('provider', 'lmstudio'))
        
        console.print(table)
    
    def _reset_session(self):
        """セッションをリセット"""
        console.print(f"🔄 [yellow]{t('session_reset')}[/yellow]")
        if hasattr(self.agent, 'memory'):
            self.agent.memory.clear()
        if hasattr(self.agent, 'action_history'):
            self.agent.action_history.clear()
        if hasattr(self.agent, 'error_history'):
            self.agent.error_history.clear()
    
    async def _handle_memory_command(self, args: list):
        """外部記憶コマンドの処理"""
        if not args:
            console.print(f"[yellow]{t('usage_memory')}[/yellow]")
            return
        
        subcmd = args[0]
        if subcmd == 'status':
            memory_summary = self.external_memory.get_memory_summary()
            console.print(f"🧠 {t('memory_status', summary=memory_summary)}")
        elif subcmd == 'search':
            if len(args) < 2:
                console.print(f"[yellow]{t('usage_memory_search')}[/yellow]")
                return
            query = " ".join(args[1:])
            results = self.external_memory.search_records(query)
            if results:
                console.print(f"🔍 {t('memory_search_found', count=len(results))}")
                for result in results[:5]:  # 最大5件表示
                    console.print(f"  📄 {result['filename']}")
            else:
                console.print(f"❌ {t('memory_search_none', query=query)}")
        elif subcmd == 'cleanup':
            self.external_memory.cleanup_session()
            console.print(f"✅ {t('memory_cleaned')}")
    
    async def _handle_todo_command(self, args: list):
        """TODOコマンドの処理"""
        if not args:
            console.print("[yellow]Usage: /todo <add|list|complete>[/yellow]")
            return
        
        subcmd = args[0]
        if subcmd == 'add':
            if len(args) < 2:
                console.print("[yellow]Usage: /todo add <task>[/yellow]")
                return
            task = " ".join(args[1:])
            self.external_memory.add_todo(task)
        elif subcmd == 'list':
            todo_summary = self.external_memory.get_todo_summary()
            console.print(f"📝 {todo_summary}")
        elif subcmd == 'complete':
            if len(args) < 2:
                console.print("[yellow]Usage: /todo complete <task_pattern>[/yellow]")
                return
            task_pattern = " ".join(args[1:])
            success = self.external_memory.mark_todo_complete(task_pattern)
            if not success:
                console.print(f"❌ Could not find TODO matching '{task_pattern}'")
    
    async def _handle_wise_command(self, args: list):
        """三人文殊コマンドの処理"""
        if not hasattr(self.agent, 'multi_agent_system') or not self.agent.multi_agent_system:
            console.print("[red]Multi-agent system not available[/red]")
            return
        
        if not args:
            console.print("[yellow]Usage: /wise <your_question_or_decision>[/yellow]")
            console.print("Example: /wise Should I refactor this authentication system?")
            return
        
        query = " ".join(args)
        console.print(f"🧠 [cyan]Consulting Three Wise Agents about: {query}[/cyan]")
        
        try:
            result = await self.agent.multi_agent_system.three_wise_consultation(
                query=query,
                context="Interactive session consultation"
            )
            
            if result['success']:
                console.print("\n✅ [bold green]Three Wise Agents Consultation Complete![/bold green]")
                console.print(f"📝 Final Decision:\n{result['final_decision']}")
            else:
                console.print(f"[red]Consultation failed: {result.get('reason', 'Unknown error')}[/red]")
        except Exception as e:
            console.print(f"[red]Error during consultation: {e}[/red]")
    
    async def _handle_boss_command(self, args: list):
        """親分呼び出しコマンドの処理"""
        if not hasattr(self.agent, 'multi_agent_system') or not self.agent.multi_agent_system:
            console.print("[red]Multi-agent system not available[/red]")
            return
        
        mas = self.agent.multi_agent_system
        
        if not args:
            console.print("[yellow]Usage:[/yellow]")
            console.print("  /boss setup - Configure boss consultation")
            console.print("  /boss status - Show boss status")
            return
        
        subcmd = args[0]
        if subcmd == 'setup':
            await mas.setup_boss_consultation()
        elif subcmd == 'status':
            if mas.boss_consultation_enabled:
                console.print(f"🎩 Boss consultation: {mas.boss_consultation_mode} (used {mas.boss_used_count} times)")
            else:
                console.print("🎩 Boss consultation: Disabled")
    
    def _show_agents_status(self):
        """エージェント状態を表示"""
        console.print("\n🤖 [bold cyan]Multi-Agent System Status[/bold cyan]")
        
        if not hasattr(self.agent, 'multi_agent_system') or not self.agent.multi_agent_system:
            console.print("❌ Multi-agent system not available")
            return
        
        mas = self.agent.multi_agent_system
        console.print(f"📊 {mas.get_status_summary()}")
        
        # 動作モード
        operation_mode = mas.get_operation_mode()
        console.print(f"🎯 Operation Mode: {operation_mode}")
        
        if mas.can_use_three_wise_mode():
            console.print("🧠 Three Wise Agents: Available")
        else:
            console.print("🧠 Three Wise Agents: Not available")
        
        if mas.can_use_boss_consultation():
            console.print("🎩 Boss Consultation: Available")
        else:
            console.print("🎩 Boss Consultation: Not available")
    
    async def _execute_custom_command(self, cmd: str, args: list):
        """カスタムコマンドを処理"""
        command_path = self.root_path / '.localllm' / 'commands' / f'{cmd}.md'

        if not command_path.exists():
            console.print(f"[red]{t('unknown_command', cmd=cmd)}[/red]")
            console.print(t("type_help"))
            return

        try:
            content = command_path.read_text(encoding='utf-8')

            # Extract shell command from markdown
            import re
            match = re.search(r"```bash\n(.*?)\n```", content, re.DOTALL)
            if not match:
                console.print(f"[red]No bash script found in {cmd}.md[/red]")
                return

            script = match.group(1)

            # Pass arguments to the script
            script_with_args = f"{script} {' '.join(args)}"

            console.print(f"Executing custom command: [bold green]/{cmd}[/bold green]")

            # Execute the script
            process = await asyncio.create_subprocess_shell(
                script_with_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                console.print(stdout.decode())
            if stderr:
                console.print(f"[red]{stderr.decode()}[/red]")

        except Exception as e:
            console.print(f"[red]Error executing custom command /{cmd}: {e}[/red]")

    async def _execute_subagent(self, agent_name: str, args: list):
        """サブエージェントを実行"""
        if not agent_name:
            console.print("[red]Usage: /agent <agent_name> <prompt>[/red]")
            return

        agent_path = self.root_path / '.localllm' / 'agents' / f'{agent_name}.md'
        if not agent_path.exists():
            console.print(f"[red]Subagent '{agent_name}' not found.[/red]")
            return

        try:
            content = agent_path.read_text(encoding='utf-8')

            # Extract system prompt from markdown
            import re
            match = re.search(r"## System Prompt\n\n(.*)", content, re.DOTALL)
            system_prompt = match.group(1).strip() if match else ""

            import copy
            subagent_dna = copy.copy(self.project_dna)
            subagent_dna.system_prompt = system_prompt

            tools = ToolSystem(
                self.root_path,
                safe_mode=self.config.get('safety', {}).get('require_confirmation', True)
            )

            subagent = ReActAgent(
                self.llm_client,
                subagent_dna,
                tools,
                self.dry_run,
                None, # No multi-agent system for subagents
                self.external_memory
            )

            prompt = " ".join(args)
            console.print(f"Executing subagent: [bold green]/{agent_name}[/bold green] with prompt: [italic]{prompt}[/italic]")

            response = await subagent.execute(prompt)
            console.print(f"\nSubagent {agent_name}:")
            console.print(Markdown(response))

        except Exception as e:
            console.print(f"[red]Error executing subagent /{agent_name}: {e}[/red]")


    async def _handle_config_command(self, args: list):
        """設定コマンドの処理"""
        config_path = self.root_path / 'localllm.toml'
        
        if not args:
            console.print("[yellow]Usage: /config <show|edit|reload>[/yellow]")
            return
        
        subcmd = args[0]
        if subcmd == 'show':
            if config_path.exists():
                console.print(f"📝 Configuration file: {config_path}")
                console.print(f"Current provider: {self.config.get('llm', {}).get('provider', 'lmstudio')}")
            else:
                console.print("[red]No configuration file found. Run 'python main.py --init' first.[/red]")
        elif subcmd == 'edit':
            if config_path.exists():
                console.print(f"📝 Edit configuration file: {config_path}")
                console.print("After editing, use '/config reload' to apply changes")
            else:
                console.print("[red]No configuration file found. Run 'python main.py --init' first.[/red]")
        elif subcmd == 'reload':
            console.print("🔄 Reloading configuration...")
            self.config = self._load_config()
            console.print("✅ Configuration reloaded")
    
    async def cleanup(self):
        """クリーンアップ処理"""
        console.print("🧹 [yellow]Cleaning up...[/yellow]")
        
        # 外部記憶のクリーンアップ
        if self.external_memory:
            self.external_memory.cleanup_session()
        
        # LLMクライアントのクリーンアップ
        if self.llm_client:
            await self.llm_client.__aexit__(None, None, None)

async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="LocalLLM Code - Revolutionary Agentic Coding Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Interactive mode
  python main.py -p "Add login function"  # One-shot command
  python main.py --init                 # Initialize project
        """
    )
    
    parser.add_argument('-p', '--prompt', help='Execute single prompt')
    parser.add_argument('--init', action='store_true', help='Initialize project')
    parser.add_argument('--config', action='store_true', help='Edit configuration')
    parser.add_argument('--model', help='Specify LLM model')
    parser.add_argument('--server', help='LM Studio server URL')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without execution')
    parser.add_argument('--unsafe', action='store_true', help='Disable safety checks')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.config:
        await edit_configuration()
        return
    
    if args.init:
        await initialize_project()
        return
    
    app = LocalLLMCode(dry_run=args.dry_run)
    
    if args.dry_run:
        console.print("🧪 [bold magenta]Running in DRY RUN mode - no actual changes will be made[/bold magenta]")
    
    try:
        await app.initialize()
        
        if args.prompt:
            # ワンショットモード
            response = await app.agent.execute(args.prompt)
            console.print(Markdown(response))
        else:
            # インタラクティブモード
            await app.interactive_mode()
            
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
    finally:
        await app.cleanup()

async def initialize_project():
    """プロジェクト初期化処理"""
    console.print(f"🏗️ [bold blue]{t('initializing_project')}[/bold blue]")
    
    root_path = Path.cwd()
    
    # 1. 設定ファイル作成
    config_path = root_path / 'localllm.toml'
    if config_path.exists():
        if not Confirm.ask(f"Configuration file already exists. Overwrite?"):
            console.print("⚠️ [yellow]Initialization cancelled[/yellow]")
            return
    
    config_content = '''# LocalLLM Code Configuration

[llm]
provider = "lmstudio"
model = "default"
context_size = 8192
stream = true
temperature = 0.7

[lmstudio]
server_url = "http://localhost:1234"
model = "default"

[azure]
api_key = ""
endpoint = ""
deployment_name = ""
api_version = "2024-02-15-preview"

[gemini]
api_key = ""
model = "gemini-pro"

[safety]
require_confirmation = true
allow_dangerous_commands = false
backup_before_edit = true

[experimental]
auto_refactoring = false
context_compression = true
memory_optimization = true

[mcp_servers]
# Add your MCP server configurations here
# example_server = "http://localhost:8080"
'''
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    console.print(f"✅ [green]Created configuration file: {config_path}[/green]")
    
    # 2. .gitignore エントリ追加
    gitignore_path = root_path / '.gitignore'
    gitignore_entry = "\n# LocalLLM Code\n.localllm_memory/\n*.backup\n"
    
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
        if '.localllm_memory/' not in content:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write(gitignore_entry)
            console.print("✅ [green]Updated .gitignore[/green]")
    else:
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_entry)
        console.print("✅ [green]Created .gitignore[/green]")
    
    console.print("\n🎉 [bold green]LocalLLM Code project initialized successfully![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Edit localllm.toml to configure your LLM settings")
    console.print("2. Run 'python main.py' to start the interactive agent")
    console.print("3. Try commands like 'Create a hello world script' or 'Analyze my project structure'")

async def edit_configuration():
    """設定ファイル編集"""
    config_path = Path.cwd() / 'localllm.toml'
    
    if not config_path.exists():
        console.print("[red]No configuration file found. Run --init first.[/red]")
        return
    
    console.print(f"📝 [cyan]Configuration file: {config_path}[/cyan]")
    console.print("Edit the file in your preferred editor, then restart LocalLLM Code.")

if __name__ == "__main__":
    asyncio.run(main())
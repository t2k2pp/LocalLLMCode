"""ReAct Agent implementation"""

import re
import time
from typing import TYPE_CHECKING

# ファイル参照パーサーのインポート
from ..core.file_parser import FileReferenceParser
from ..core.instruction_parser import InstructionParser
from ..core import t

if TYPE_CHECKING:
    from ..core.project_dna import ProjectDNA
    from ..llm.clients import LLMClient
    from ..tools.tool_system import ToolSystem
    from .multi_agent import MultiAgentSystem
    from ..memory.external_memory import ExternalMemorySystem

try:
    from rich.console import Console
    from rich.prompt import Prompt
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    class Prompt:
        @staticmethod
        def ask(*args, **kwargs):
            return input()
    console = Console()

class ReActAgent:
    """革新的なReActエージェント - 思考・行動・観察のループ"""
    
    def __init__(self, llm_client: 'LLMClient', project_dna: 'ProjectDNA', 
                 tools: 'ToolSystem', dry_run: bool = False, multi_agent_system: 'MultiAgentSystem' = None,
                 external_memory: 'ExternalMemorySystem' = None):
        self.llm_client = llm_client
        self.project_dna = project_dna
        self.tools = tools
        self.memory = []
        self.max_iterations = 10
        self.dry_run = dry_run
        self.action_history = []  # 詳細な行動履歴
        self.error_history = []   # エラー履歴
        self.loop_detection_window = 6  # 最近6回の行動をチェック
        self.stuck_threshold = 4  # 同じ行動を4回繰り返したら相談
        self.context_compression_enabled = True
        self.multi_agent_system = multi_agent_system
        self.external_memory = external_memory
        self.current_agent_provider = getattr(llm_client, 'provider', 'unknown')
        self.file_parser = FileReferenceParser(self.tools.root_path)
        self.instruction_parser = InstructionParser(self.tools.root_path)
    
    async def execute(self, user_query: str) -> str:
        """ReActループでクエリを実行"""
        if self.dry_run:
            console.print(f"\n🧪 [bold magenta]{t('dry_run_planning', query=user_query)}[/bold magenta]")
        else:
            console.print(f"\n🤖 [bold green]{t('agent_thinking', query=user_query)}[/bold green]")
        
        # 外部記憶にクエリを記録
        if self.external_memory:
            self.external_memory.record_console_output(f"User query: {user_query}", "query")
        
        # ファイル参照の自動解析と読み込み
        file_context = await self._process_file_references(user_query)
        if file_context:
            console.print(f"📁 [green]{t('auto_loaded_files', count=len(file_context.split('📄'))-1)}[/green]")
        
        conversation = f"User Query: {user_query}\n\n"
        
        # 構造化指示の解析
        structured_context = await self._process_structured_instructions(user_query, file_context)
        if structured_context:
            conversation += structured_context
        
        system_prompt = f"""You are an expert software development agent working on a project.

{self.project_dna.to_context()}

Available Tools:
{self.tools.get_tool_descriptions()}

IMPORTANT GUIDELINES:
- For simple greetings, questions, or requests for information, you may provide a direct answer without using tools
- When user references a file, read that file first to understand the requirements
- When instructed to follow guidelines in a specific file, read the file completely and understand the requirements
- ALWAYS use list_files tool to check directory structure BEFORE attempting file operations
- NEVER assume file or directory existence - verify first with list_files
- When file operations fail repeatedly, use list_files to understand current structure
- If you see a file in a directory listing, read it using its exact name (not a modified path)
- Build on successful observations - don't ignore what you've already learned
- NEVER use "ls" command on Windows - use "dir" command instead, or better yet use list_files tool
- For conversational queries, respond directly without the ReAct format
- When creating project structures, carefully read any referenced guidelines for naming conventions
- Always create complete file sets as specified in any guidelines you read
- When files contain structured data (lists, tables, specifications), extract and use that data appropriately
- Create meaningful file content based on the specifications you read, not just placeholder content
- If instructions specify required files (README.md, requirements.txt, source files), create ALL of them

CRITICAL SAFETY RULES:
- Deletion tools (remove_file, remove_directory) ALWAYS require user confirmation - this is built-in
- Shell deletion commands (rm, del, rmdir) will prompt for user confirmation - this is built-in
- If a file exists and you need a different name, use a different name or ask the user
- When file creation fails due to existing files, choose alternative names or ask user guidance
- ALWAYS preserve existing user data - never overwrite or delete without explicit permission
- The system will automatically prompt users before any deletion - trust this safety mechanism

Use the ReAct format when actions are needed:
Thought: [your reasoning about what needs to be done]
Action: [tool_name] [parameters]
Observation: [result of action]

Key Patterns to Recognize:
- @File/path.md = Read this file first
- "Follow guidelines in X" = Read X file and implement exactly what it specifies
- Look for specific instructions about directory naming, file structure, and required content

For simple queries, respond directly with helpful information.
"""
        
        # 早期終了の判定 - 単純な挨拶や質問の場合
        if self._is_simple_query(user_query):
            console.print(f"💬 [green]{t('conversational_query')}[/green]")
            simple_prompt = f"User said: {user_query}\n\nRespond naturally and helpfully as a coding assistant. No actions needed."
            response = await self.llm_client.generate(simple_prompt, system_prompt, stream=False)
            return response
        
        conversation = f"User Query: {user_query}\n\n"
        
        # コンテキスト圧縮の確認
        if self.context_compression_enabled and len(conversation.split()) > 1000:
            console.print(f"🗜️ [yellow]{t('compressing_context')}[/yellow]")
            conversation = await self._compress_conversation_context(conversation)
        
        for iteration in range(self.max_iterations):
            console.print(f"\n💭 [cyan]{t('iteration', iteration=iteration + 1)}[/cyan]")
            
            # ループ検知
            if iteration > 0:
                loop_detected = self._detect_action_loop()
                if loop_detected:
                    should_continue = await self._handle_stuck_situation(user_query, conversation)
                    if not should_continue:
                        return t("repetitive_pattern")
            
            # Think
            think_prompt = f"""{conversation}

Think step by step about how to solve this:
1. What was the last successful observation and what did I learn from it?
2. Have I already read the necessary files? If yes, what concrete action should I take next?
3. Am I repeating the same action without making progress? If yes, what different action will move me forward?
4. If the user asked me to follow instructions in a file, have I actually started following those instructions?
5. What is the NEXT CONCRETE STEP to accomplish the user's request?

CONTENT-BASED GUIDANCE:
- If I read instructions that specify creating specific files (like README.md, source files, requirements.txt), create ALL required files
- If instructions mention specific directory structures or naming patterns, follow them exactly
- If I see detailed specifications or examples in the files I read, use that information to create appropriate content
- If the files contain lists or structured data, process that data to create the requested outputs

CRITICAL DECISION RULES:
- If I have successfully read a file multiple times with identical content, STOP reading it again
- If I read a file that contains a list or collection of items (like 101 app ideas), pick ONE item and start working on it
- If I read an instruction file that references another file (like miniapp.md), read that other file ONCE, then start creating the requested output
- NEVER read the same file more than twice unless the content has changed

Important: If I've already read the required files, I should start taking action based on what I learned, not re-reading the same files.

Provide your reasoning as "Thought:" followed by the specific action as "Action: tool_name parameters"
"""
            response = await self.llm_client.generate(think_prompt, system_prompt, stream=False)
            
            conversation += f"Thought: {response}\n\n"
            
            # Extract action
            action_match = re.search(r'Action:\s*(\w+)(?:\s+(.+))?', response)
            if not action_match:
                # No action found, provide final answer
                final_prompt = f"{conversation}Provide a final answer to the user."
                final_response = await self.llm_client.generate(final_prompt, system_prompt)
                return final_response
            
            tool_name = action_match.group(1)
            tool_params = action_match.group(2) or ""
            
            console.print(f"🔧 [yellow]{t('action')}[/yellow] {tool_name} {tool_params}")
            
            # 行動履歴に記録
            action_record = {
                'iteration': iteration,
                'action': tool_name,
                'params': tool_params,
                'timestamp': time.time(),
                'context_length': len(conversation.split())
            }
            
            # 同じアクションの繰り返しチェック
            repeated_action = self._check_repeated_action(tool_name, tool_params)
            if repeated_action:
                # 同じアクションを3回繰り返している場合、戦略を変更
                if repeated_action >= 3:
                    observation = f"Error: Repeated action '{tool_name} {tool_params}' detected {repeated_action} times. You have already read this content - now take action based on what you learned instead of re-reading."
                    console.print(f"⚠️ [red]Repeated action detected - forcing progression[/red]")
                    conversation += f"Action: {tool_name} {tool_params}\nObservation: {observation}\n\n"
                    action_record['observation'] = observation
                    action_record['success'] = False
                    self.action_history.append(action_record)
                    continue
            
            # Execute action
            try:
                if self.dry_run:
                    observation = f"[DRY RUN] Would execute: {tool_name} {tool_params}"
                    console.print(f"🧪 [magenta]{t('dry_run_observation')}[/magenta] {observation}")
                else:
                    observation = await self.tools.execute(tool_name, tool_params)
                    console.print(f"👁️ [blue]{t('observation')}[/blue] {observation[:200]}{'...' if len(observation) > 200 else ''}")
                
                action_record['observation'] = observation
                action_record['success'] = True
                
                # エラーの検出と記録
                if "Error:" in observation or "failed" in observation.lower() or "No such file" in observation:
                    action_record['success'] = False
                    self._record_error(tool_name, tool_params, observation)
                
                conversation += f"Action: {tool_name} {tool_params}\nObservation: {observation}\n\n"
                
            except Exception as e:
                observation = f"Error: {str(e)}"
                action_record['observation'] = observation
                action_record['success'] = False
                self._record_error(tool_name, tool_params, str(e))
                conversation += f"Action: {tool_name} {tool_params}\nObservation: {observation}\n\n"
            
            # 行動履歴を更新
            self.action_history.append(action_record)
            
            # コンテキスト圧縮の再確認
            if self.context_compression_enabled and len(conversation.split()) > 2000:
                console.print(f"🗜️ [yellow]{t('compressing_context')}[/yellow]")
                conversation = await self._compress_conversation_context(conversation)
            
            # Check if task is complete
            if "task completed" in observation.lower() or "finished" in observation.lower():
                final_prompt = f"{conversation}The task seems to be completed. Provide a summary."
                final_response = await self.llm_client.generate(final_prompt, system_prompt)
                return final_response
        
        return t("max_iterations")
    
    async def _compress_conversation_context(self, conversation: str) -> str:
        """会話コンテキストを圧縮"""
        try:
            # 直接LLMクライアントを使用してコンテキスト圧縮
            compression_prompt = """Compress this conversation while preserving:
- User's original query
- Key actions taken
- Important error messages
- Current progress and next steps
- Technical details and file names

Remove redundant explanations and verbose observations."""
            
            compressed = await self.llm_client.generate(
                f"Compress this conversation:\n\n{conversation}",
                compression_prompt,
                stream=False
            )
            
            # 圧縮統計を表示
            original_length = len(conversation.split())
            compressed_length = len(compressed.split())
            ratio = compressed_length / original_length
            console.print(f"🗜️ [green]{t('context_compressed', original=original_length, compressed=compressed_length, ratio=ratio)}[/green]")
            
            return compressed
            
        except Exception as e:
            console.print(f"[yellow]{t('compression_failed', e=e)}[/yellow]")
            return conversation
    
    def _detect_action_loop(self) -> bool:
        """行動のループを検知"""
        if len(self.action_history) < self.stuck_threshold:
            return False
        
        # 最近の行動を分析
        recent_actions = self.action_history[-self.loop_detection_window:]
        
        # 同じ行動の繰り返しをチェック
        action_sequences = []
        for action in recent_actions:
            action_signature = f"{action['action']}:{action.get('params', '')}"
            action_sequences.append(action_signature)
        
        # 重複行動のカウント
        unique_actions = set(action_sequences)
        if len(unique_actions) <= 2 and len(action_sequences) >= self.stuck_threshold:
            console.print(f"🔄 [yellow]{t('loop_detected')}[/yellow]")
            return True
        
        # 同じアクションを連続で3回以上実行している場合もループとみなす
        if len(action_sequences) >= 3:
            last_three = action_sequences[-3:]
            if len(set(last_three)) == 1:
                console.print(f"🔄 [yellow]Same action repeated 3 times consecutively[/yellow]")
                return True
        
        # 失敗の繰り返しをチェック
        failed_actions = [a for a in recent_actions if not a.get('success', True)]
        if len(failed_actions) >= self.stuck_threshold:
            console.print(f"❌ [yellow]{t('repeated_failures')}[/yellow]")
            return True
        
        return False
    
    async def _handle_stuck_situation(self, user_query: str, conversation: str) -> bool:
        """行き詰まり状況の処理 - マルチエージェント対応"""
        console.print("\n🤔 [bold yellow]I seem to be stuck in a repetitive pattern.[/bold yellow]")
        
        # 現在の状況を分析
        analysis = self._analyze_current_situation()
        console.print(f"📊 Current situation: {analysis}")
        
        # マルチエージェント相談の選択肢を含める
        console.print("\n💬 [bold cyan]I need your guidance to proceed effectively.[/bold cyan]")
        console.print("Here's what I've been trying:")
        
        # 最近の行動を要約
        recent_summary = self._summarize_recent_actions()
        console.print(recent_summary)
        
        # 利用可能な相談オプションを構築
        options = [
            "1. Continue with a different approach",
            "2. Break down the task differently", 
            "3. Skip this step and move forward",
            "4. Stop and await further instructions"
        ]
        
        # マルチエージェント機能の追加
        choices = ["1", "2", "3", "4"]
        if self.multi_agent_system:
            if self.multi_agent_system.can_use_three_wise_mode():
                options.append("5. Consult Three Wise Agents (三人文殊)")
                choices.append("5")
            
            if self.multi_agent_system.can_use_boss_consultation():
                options.append("6. Call Boss for Consultation (親分呼び出し)")
                choices.append("6")
        
        console.print("\nOptions:")
        for option in options:
            console.print(f"   {option}")
        
        try:
            user_choice = Prompt.ask(
                "\nHow would you like me to proceed?",
                choices=choices,
                default="1"
            )
            
            if user_choice == "1":
                console.print("🔄 [green]Attempting a different approach...[/green]")
                return True
            elif user_choice == "2":
                console.print("🔧 [green]Breaking down the task differently...[/green]")
                return True
            elif user_choice == "3":
                console.print("⏭️ [green]Skipping current step...[/green]")
                return True
            elif user_choice == "4":
                console.print("⏸️ [yellow]Awaiting further instructions...[/yellow]")
                return False
            elif user_choice == "5" and self.multi_agent_system:
                # 三人文殊モード
                return await self._consult_three_wise_agents(user_query, conversation)
            elif user_choice == "6" and self.multi_agent_system:
                # 親分呼び出しモード
                return await self._consult_boss(user_query, conversation)
            else:
                console.print("🔄 [green]Attempting a different approach...[/green]")
                return True
                
        except KeyboardInterrupt:
            console.print("\n⏸️ [yellow]User interrupted. Stopping.[/yellow]")
            return False
    
    async def _consult_three_wise_agents(self, user_query: str, conversation: str) -> bool:
        """三人文殊相談モード"""
        try:
            problem_description = f"Stuck in loop while working on: {user_query}"
            result = await self.multi_agent_system.three_wise_consultation(
                query=user_query,
                context=conversation
            )
            
            if result['success']:
                console.print("\n🧠 [bold green]Three Wise Agents Consultation Complete![/bold green]")
                console.print(f"📝 Final Decision: {result['final_decision'][:300]}...")
                
                # 決定を会話に追加
                self.memory.append(f"Three Wise Agents Consultation Result: {result['final_decision']}")
                
                console.print("\n💡 [cyan]Proceeding with the collective wisdom...[/cyan]")
                return True
            else:
                console.print(f"[yellow]Three Wise Agents consultation failed: {result.get('reason', 'Unknown error')}[/yellow]")
                return True  # 失敗してもcontinue
                
        except Exception as e:
            console.print(f"[red]Error during Three Wise Agents consultation: {e}[/red]")
            return True
    
    async def _consult_boss(self, user_query: str, conversation: str) -> bool:
        """親分呼び出しモード"""
        try:
            problem_description = f"Agent stuck in repetitive pattern working on: {user_query}. Recent actions: {self._summarize_recent_actions()}"
            
            result = await self.multi_agent_system.boss_consultation(
                problem=problem_description,
                context=conversation,
                current_agent=self.current_agent_provider
            )
            
            if result['success']:
                console.print("\n🎩 [bold green]Boss Consultation Complete![/bold green]")
                console.print(f"📝 Boss Advice: {result['advice'][:300]}...")
                
                # ボスのアドバイスを会話に追加
                self.memory.append(f"Boss Consultation Advice: {result['advice']}")
                
                console.print(f"\n💡 [cyan]Following boss guidance from {result['boss_agent']}...[/cyan]")
                return True
            else:
                console.print(f"[yellow]Boss consultation failed: {result.get('reason', 'Unknown error')}[/yellow]")
                return True  # 失敗してもcontinue
                
        except Exception as e:
            console.print(f"[red]Error during boss consultation: {e}[/red]")
            return True
    
    def _record_error(self, action: str, params: str, error_message: str):
        """エラーを記録"""
        error_record = {
            'timestamp': time.time(),
            'action': action,
            'params': params,
            'error': error_message,
            'iteration': len(self.action_history)
        }
        self.error_history.append(error_record)
        
        # 外部記憶にもエラーを記録
        if self.external_memory:
            self.external_memory.record_console_output(
                f"Error in {action}: {error_message}", "error"
            )
            
            # 重要なエラーは外部記録として保存
            if len(self.error_history) >= 3:
                error_content = f"Action: {action}\nParameters: {params}\nError: {error_message}\nOccurred at iteration: {len(self.action_history)}"
                self.external_memory.save_external_record(
                    f"error_{len(self.error_history)}", 
                    error_content, 
                    "error"
                )
        
        # エラーパターンの分析
        if len(self.error_history) >= 3:
            self._analyze_error_patterns()
    
    def _analyze_current_situation(self) -> str:
        """現在の状況を分析"""
        if not self.action_history:
            return "No actions taken yet"
        
        recent_actions = self.action_history[-3:]
        total_actions = len(self.action_history)
        successful_actions = len([a for a in self.action_history if a.get('success', True)])
        
        success_rate = (successful_actions / total_actions) * 100 if total_actions > 0 else 0
        
        return f"{total_actions} actions taken, {success_rate:.1f}% success rate, last {len(recent_actions)} actions show repetitive pattern"
    
    def _summarize_recent_actions(self) -> str:
        """最近の行動を要約"""
        if not self.action_history:
            return "No recent actions to summarize"
        
        recent = self.action_history[-5:]  # 最近5回
        summary_lines = []
        
        for i, action in enumerate(recent, 1):
            success_indicator = "✅" if action.get('success', True) else "❌"
            summary_lines.append(f"   {i}. {success_indicator} {action['action']} {action.get('params', '')[:50]}")
        
        return "\n".join(summary_lines)
    
    def _check_repeated_action(self, tool_name: str, tool_params: str) -> int:
        """同じアクションの繰り返しをチェック"""
        if not self.action_history:
            return 0
        
        # 最近5回の行動をチェック
        recent_actions = self.action_history[-5:]
        action_signature = f"{tool_name}:{tool_params}"
        
        count = 0
        for action in recent_actions:
            if f"{action['action']}:{action.get('params', '')}" == action_signature:
                count += 1  # 成功・失敗問わずカウント（無意味な繰り返しを防ぐため）
        
        return count
    
    def _analyze_error_patterns(self):
        """エラーパターンを分析して警告"""
        recent_errors = self.error_history[-3:]
        
        # 同じエラーの繰り返しをチェック
        error_types = [error['action'] for error in recent_errors]
        if len(set(error_types)) == 1:
            console.print(f"⚠️ [red]Repeated error with {error_types[0]} action[/red]")
        
        # ファイル操作エラーのパターン
        file_errors = [e for e in recent_errors if 'file' in e['error'].lower() or 'path' in e['error'].lower()]
        if len(file_errors) >= 2:
            console.print("⚠️ [red]Multiple file operation errors detected[/red]")
    
    def get_history_summary(self) -> str:
        """履歴の要約を取得"""
        action_count = len(self.action_history)
        error_count = len(self.error_history)
        
        if action_count == 0:
            return "No actions performed yet"
        
        success_rate = ((action_count - error_count) / action_count) * 100
        
        return f"History: {action_count} actions, {error_count} errors, {success_rate:.1f}% success rate"
    
    def _is_simple_query(self, query: str) -> bool:
        """単純な挨拶や質問かどうかを判定"""
        query_lower = query.lower().strip()
        
        # 挨拶パターン
        greetings = [
            'こんにちは', 'こんばんは', 'おはよう', 'hello', 'hi', 'hey',
            'good morning', 'good afternoon', 'good evening'
        ]
        
        # 質問パターン（アクション不要）
        question_patterns = [
            'what is', 'what are', 'how does', 'how do', 'why', 'when',
            'who', 'where', 'can you explain', 'tell me about',
            'なに', 'なん', 'どう', 'どこ', 'いつ', 'だれ', 'なぜ',
            '教えて', '説明して', 'とは', 'について'
        ]
        
        # 短い挨拶（5文字以下）
        if len(query_lower) <= 5 and any(greeting in query_lower for greeting in greetings):
            return True
        
        # 明確な挨拶
        if any(greeting == query_lower for greeting in greetings):
            return True
            
        # ファイル参照（@記法）が含まれている場合は複雑なクエリ
        if re.search(r'@\w+', query):
            return False
            
        # 質問パターンで、アクション指示がない
        if any(pattern in query_lower for pattern in question_patterns):
            # アクション指示がないことを確認
            action_keywords = [
                'create', 'make', 'write', 'edit', 'modify', 'delete', 'run', 'execute',
                'install', 'update', 'fix', 'change', 'add', 'remove',
                '作成', '作る', '書く', '編集', '修正', '削除', '実行', '変更', '追加', '削除',
                '従って', '指示', 'に従い', 'ガイドライン'
            ]
            if not any(action in query_lower for action in action_keywords):
                return True
        
        return False
    
    async def _process_file_references(self, user_query: str) -> str:
        """ファイル参照の自動解析と読み込み"""
        try:
            # ファイル参照を解析
            parsed = self.file_parser.parse_query(user_query)
            
            file_contexts = []
            
            # 個別ファイルの読み込み
            for file_ref in parsed['files']:
                file_path = self.file_parser.resolve_file_path(file_ref)
                if file_path:
                    try:
                        content = await self.tools.read_file(str(file_path))
                        file_contexts.append(f"📄 {file_ref}:\n{content}\n")
                    except Exception as e:
                        file_contexts.append(f"📄 {file_ref}: (読み込みエラー: {e})\n")
            
            # フォルダ内ファイルの一括読み込み
            for folder_ref in parsed['folders']:
                try:
                    content = await self.tools.read_folder(folder_ref.rstrip('/'))
                    file_contexts.append(f"📁 {folder_ref}:\n{content}\n")
                except Exception as e:
                    file_contexts.append(f"📁 {folder_ref}: (読み込みエラー: {e})\n")
            
            # 拡張子指定ファイルの読み込み
            for extension in parsed['extensions']:
                files = self.file_parser.find_files_by_extension(extension)
                if files:
                    try:
                        content = await self.tools.read_files(' '.join(files))
                        file_contexts.append(f"📋 {extension} files:\n{content}\n")
                    except Exception as e:
                        file_contexts.append(f"📋 {extension} files: (読み込みエラー: {e})\n")
            
            return '\n'.join(file_contexts) if file_contexts else ""
            
        except Exception as e:
            console.print(f"[yellow]File reference processing error: {e}[/yellow]")
            return ""
    
    async def _process_structured_instructions(self, user_query: str, file_context: str) -> str:
        """構造化された指示を処理"""
        try:
            if not file_context:
                return ""
            
            # より広範囲な条件でトリガー
            trigger_keywords = ['ガイドライン', '指示', '従って', '従い', 'follow', 'according', 'guideline']
            should_process = any(keyword in user_query.lower() for keyword in trigger_keywords)
            
            if not should_process:
                return ""
            
            # ファイルコンテンツから構造化指示を解析
            lines = file_context.split('\n')
            full_content = ""
            referenced_files = []
            
            # まず読み込まれたファイルの内容を抽出
            for line in lines:
                if line.startswith('📄') and ':' in line:
                    # ファイルコンテンツ部分を抽出
                    content_start = file_context.find(line)
                    if content_start != -1:
                        content_section = file_context[content_start:]
                        # 次のファイルまたは終端まで
                        next_file = content_section.find('\n📄', 1)
                        if next_file != -1:
                            content_section = content_section[:next_file]
                        
                        # ":" 以降を取得
                        if ':' in content_section:
                            actual_content = content_section.split(':', 1)[1].strip()
                            full_content += actual_content + "\n\n"
                            
                            # 内容から他のファイル参照を検出
                            import re
                            file_refs = re.findall(r'([a-zA-Z0-9_\-./\\]+\.md)', actual_content)
                            for ref in file_refs:
                                if ref not in referenced_files and ref != line.split(':')[0].replace('📄 ', ''):
                                    referenced_files.append(ref)
            
            # 参照されているファイルを追加で読み込み
            for ref_file in referenced_files:
                try:
                    ref_content = await self.tools.read_file(ref_file)
                    full_content += f"\n\n=== Referenced File: {ref_file} ===\n{ref_content}\n"
                except:
                    console.print(f"[yellow]Could not read referenced file: {ref_file}[/yellow]")
            
            if not full_content:
                return ""
            
            # 構造化指示を解析
            instruction = self.instruction_parser.parse_guideline_file(full_content)
            
            if instruction.type == "general":
                return ""
            
            # 構造化されたコンテキストを生成
            context = f"""
STRUCTURED INSTRUCTIONS DETECTED:
Type: {instruction.type}
Items: {len(instruction.items)}

"""
            
            if instruction.naming_pattern:
                context += f"Directory Naming Pattern: {instruction.naming_pattern}\n"
            
            if instruction.directory_structure:
                context += f"Base Directory: {instruction.directory_structure.get('base_directory', 'projects')}\n"
            
            if instruction.required_files:
                context += f"Required Files: {', '.join(instruction.required_files)}\n"
            
            # 最初の数個のアイテムを例として表示
            context += "\nExample Items:\n"
            for i, item in enumerate(instruction.items[:3]):
                if instruction.type == "table":
                    app_name = item.get('アプリ案', item.get('no.', f"Item {i+1}"))
                    context += f"- {i+1}: {app_name}\n"
                else:
                    context += f"- {item.get('number', i+1)}: {item.get('content', 'No content')[:50]}...\n"
            
            context += f"""
IMPORTANT: When creating items from this structure:
1. Use the detected naming pattern for directories
2. Create ALL required files for each item
3. Generate appropriate content based on the item data
4. Follow the directory structure exactly as specified

"""
            
            return context
            
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to parse structured instructions: {e}[/yellow]")
            return ""
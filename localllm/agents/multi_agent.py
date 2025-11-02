"""Multi-agent system implementation"""

import time
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.project_dna import ProjectDNA
    from ..llm.clients import LLMClient

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    class Prompt:
        @staticmethod
        def ask(*args, **kwargs):
            return input()
    class Confirm:
        @staticmethod
        def ask(*args, **kwargs):
            return True
    console = Console()

class AgentRole:
    """エージェントの役割定義"""
    NEGATIVE = "negative"      # 修正に消極的
    POSITIVE = "positive"      # 修正に積極的  
    JUDGE = "judge"           # 総合判断
    BOSS = "boss"             # 親分（相談相手）

class MultiAgentSystem:
    """マルチエージェントシステム - 三人文殊モードと親分呼び出し"""
    
    def __init__(self, llm_configs: dict, project_dna: 'ProjectDNA'):
        self.llm_configs = llm_configs  # provider別の設定
        self.project_dna = project_dna
        self.available_agents = []
        self.boss_consultation_enabled = False
        self.boss_consultation_mode = "disabled"  # disabled, once, repeatable
        self.boss_used_count = 0
        self.rate_limit_backoff = {}
        
        # 利用可能なエージェントを初期化
        self._initialize_agents()
    
    def _initialize_agents(self):
        """利用可能なエージェントを初期化"""
        for provider, config in self.llm_configs.items():
            if self._is_provider_configured(provider, config):
                agent_info = {
                    'provider': provider,
                    'config': config,
                    'available': True,
                    'last_used': 0,
                    'error_count': 0,
                    'rate_limited_until': 0
                }
                self.available_agents.append(agent_info)
        
        console.print(f"🤖 Initialized {len(self.available_agents)} agents: {[a['provider'] for a in self.available_agents]}")
    
    def _is_provider_configured(self, provider: str, config: dict) -> bool:
        """プロバイダーが設定されているかチェック"""
        if provider == 'lmstudio':
            return True  # LM Studioは常に利用可能
        elif provider == 'azure':
            return bool(config.get('api_key') and config.get('endpoint') and config.get('deployment_name'))
        elif provider == 'gemini':
            return bool(config.get('api_key'))
        return False
    
    def get_operation_mode(self) -> str:
        """現在の動作モードを取得"""
        agent_count = len(self.available_agents)
        
        if agent_count == 0:
            return "none"
        elif agent_count == 1:
            return "standalone"
        elif agent_count >= 2:
            return "multi_agent"
        
        return "unknown"
    
    def can_use_three_wise_mode(self) -> bool:
        """三人文殊モードが使用可能かチェック"""
        available_count = len([a for a in self.available_agents if a['available']])
        return available_count >= 1  # 同じAIを複数ロールに割り当て可能
    
    def can_use_boss_consultation(self) -> bool:
        """親分呼び出しが使用可能かチェック"""
        available_count = len([a for a in self.available_agents if a['available']])
        return available_count >= 2 and self.boss_consultation_enabled
    
    async def setup_boss_consultation(self) -> bool:
        """親分呼び出しモードの設定"""
        if not self.can_use_boss_consultation():
            console.print("[yellow]Boss consultation requires 2+ configured AI providers[/yellow]")
            return False
        
        console.print("\n🤔 [bold cyan]Boss Consultation Setup[/bold cyan]")
        console.print("When the main agent gets stuck, consult a senior AI for guidance.")
        
        enable_boss = Confirm.ask("Enable boss consultation for this session?")
        if not enable_boss:
            return False
        
        # 使用回数制限の設定
        console.print("\nBoss consultation usage limits:")
        console.print("1. Once only for this task")
        console.print("2. Repeatable for this task") 
        console.print("3. Disabled")
        
        try:
            choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")
            
            if choice == "1":
                self.boss_consultation_mode = "once"
                console.print("✅ Boss consultation: Once only")
            elif choice == "2":
                self.boss_consultation_mode = "repeatable"
                console.print("✅ Boss consultation: Repeatable")
            else:
                self.boss_consultation_mode = "disabled"
                console.print("❌ Boss consultation disabled")
                return False
            
            self.boss_consultation_enabled = True
            return True
            
        except KeyboardInterrupt:
            console.print("\n❌ Boss consultation setup cancelled")
            return False
    
    async def three_wise_consultation(self, query: str, context: str) -> dict:
        """三人文殊モード - 3つの視点から意見を収集"""
        console.print("\n🧠 [bold magenta]Three Wise Agents Consultation (三人文殊)[/bold magenta]")
        
        if not self.can_use_three_wise_mode():
            return {'success': False, 'reason': 'Insufficient agents for three wise mode'}
        
        # 3つの役割を定義
        roles = [
            {
                'role': AgentRole.NEGATIVE,
                'name': 'Conservative Agent',
                'prompt': 'You are a conservative, cautious agent. Focus on potential risks, problems, and reasons NOT to make changes. Be skeptical and point out what could go wrong.',
                'emoji': '🛑'
            },
            {
                'role': AgentRole.POSITIVE, 
                'name': 'Progressive Agent',
                'prompt': 'You are an optimistic, progressive agent. Focus on opportunities, benefits, and reasons TO make changes. Be enthusiastic and highlight potential improvements.',
                'emoji': '🚀'
            },
            {
                'role': AgentRole.JUDGE,
                'name': 'Judging Agent', 
                'prompt': 'You are a balanced, analytical judge. Consider both conservative and progressive viewpoints, then make a reasoned decision. Weigh pros and cons objectively.',
                'emoji': '⚖️'
            }
        ]
        
        opinions = []
        
        # 各役割からの意見を収集
        for role_info in roles:
            console.print(f"\n{role_info['emoji']} [cyan]Consulting {role_info['name']}...[/cyan]")
            
            try:
                agent = await self._get_available_agent()
                if not agent:
                    console.print(f"[yellow]No agent available for {role_info['name']}[/yellow]")
                    continue
                
                # 役割特化のプロンプト構築
                system_prompt = f"{role_info['prompt']}\n\nProject Context:\n{self.project_dna.to_context()}"
                
                full_query = f"Context: {context}\n\nQuery: {query}\n\nProvide your perspective as a {role_info['name']}."
                
                # Import here to avoid circular import
                from ..llm.clients import LLMClient
                llm_client = LLMClient(agent['config'])
                async with llm_client:
                    opinion = await llm_client.generate(full_query, system_prompt, stream=False)
                
                opinions.append({
                    'role': role_info['role'],
                    'name': role_info['name'],
                    'opinion': opinion,
                    'emoji': role_info['emoji']
                })
                
                # 意見を表示
                console.print(f"{role_info['emoji']} [bold]{role_info['name']}:[/bold]")
                console.print(f"   {opinion[:200]}{'...' if len(opinion) > 200 else ''}")
                
            except Exception as e:
                console.print(f"[red]Error getting opinion from {role_info['name']}: {e}[/red]")
                continue
        
        # 最終的な判断を統合
        if len(opinions) >= 2:
            final_decision = await self._synthesize_opinions(opinions, query, context)
            return {
                'success': True,
                'opinions': opinions,
                'final_decision': final_decision,
                'mode': 'three_wise'
            }
        else:
            return {
                'success': False,
                'reason': 'Could not gather sufficient opinions',
                'opinions': opinions
            }
    
    async def boss_consultation(self, problem: str, context: str, current_agent: str) -> dict:
        """親分呼び出し - 上位AIに相談"""
        if not self.boss_consultation_enabled:
            return {'success': False, 'reason': 'Boss consultation disabled'}
        
        if self.boss_consultation_mode == "once" and self.boss_used_count > 0:
            return {'success': False, 'reason': 'Boss consultation already used (once only mode)'}
        
        # ユーザーに確認
        console.print(f"\n🎩 [bold yellow]Boss Consultation Request[/bold yellow]")
        console.print(f"Current agent ({current_agent}) is stuck and needs guidance.")
        console.print(f"Problem: {problem[:100]}{'...' if len(problem) > 100 else ''}")
        
        usage_info = f"({self.boss_used_count} times used, mode: {self.boss_consultation_mode})"
        if not Confirm.ask(f"Consult the boss agent? {usage_info}"):
            return {'success': False, 'reason': 'User declined boss consultation'}
        
        # ボスエージェントを選択（現在のエージェントとは異なるもの）
        boss_agent = await self._get_boss_agent(exclude=current_agent)
        if not boss_agent:
            return {'success': False, 'reason': 'No suitable boss agent available'}
        
        console.print(f"🎩 [green]Consulting boss agent: {boss_agent['provider']}[/green]")
        
        try:
            # ボス用の特別なプロンプト
            boss_system_prompt = f"""You are a senior expert AI consultant. A junior agent is stuck and needs your guidance.
            
Project Context:
{self.project_dna.to_context()}

You should provide:
1. Analysis of what went wrong
2. Alternative approaches
3. Specific actionable advice
4. Risk assessment

Be concise but thorough. Focus on practical solutions."""
            
            boss_query = f"""Junior Agent Problem:
{problem}

Context:
{context}

The junior agent needs your expert guidance. What should it do next?"""
            
            # Import here to avoid circular import
            from ..llm.clients import LLMClient
            llm_client = LLMClient(boss_agent['config'])
            async with llm_client:
                boss_advice = await llm_client.generate(boss_query, boss_system_prompt, stream=False)
            
            self.boss_used_count += 1
            boss_agent['last_used'] = time.time()
            
            console.print("🎩 [bold green]Boss Advice Received:[/bold green]")
            console.print(f"   {boss_advice[:300]}{'...' if len(boss_advice) > 300 else ''}")
            
            return {
                'success': True,
                'boss_agent': boss_agent['provider'],
                'advice': boss_advice,
                'usage_count': self.boss_used_count
            }
            
        except Exception as e:
            console.print(f"[red]Boss consultation failed: {e}[/red]")
            self._handle_agent_error(boss_agent, str(e))
            return {'success': False, 'reason': f'Boss agent error: {e}'}
    
    async def _get_available_agent(self):
        """利用可能なエージェントを取得"""
        current_time = time.time()
        
        for agent in self.available_agents:
            if (agent['available'] and 
                current_time > agent.get('rate_limited_until', 0) and
                agent['error_count'] < 3):
                return agent
        
        return None
    
    async def _get_boss_agent(self, exclude: str = None):
        """ボスエージェントを取得（指定されたagentを除く）"""
        current_time = time.time()
        
        for agent in self.available_agents:
            if (agent['provider'] != exclude and
                agent['available'] and 
                current_time > agent.get('rate_limited_until', 0) and
                agent['error_count'] < 3):
                return agent
        
        return None
    
    async def _synthesize_opinions(self, opinions: list, query: str, context: str) -> str:
        """複数の意見を統合して最終判断"""
        if not opinions:
            return "No opinions available for synthesis"
        
        # 判断役の意見があればそれを優先、なければ最初のエージェントで統合
        judge_opinion = next((op for op in opinions if op['role'] == AgentRole.JUDGE), None)
        
        if judge_opinion:
            return judge_opinion['opinion']
        
        # 判断役がいない場合は、意見を統合
        try:
            first_agent = await self._get_available_agent()
            if not first_agent:
                return "Unable to synthesize opinions - no agent available"
            
            synthesis_prompt = "Synthesize these different perspectives into a balanced final recommendation:"
            
            opinions_text = "\n\n".join([
                f"{op['name']}: {op['opinion']}" for op in opinions
            ])
            
            synthesis_query = f"{synthesis_prompt}\n\n{opinions_text}\n\nOriginal Query: {query}"
            
            # Import here to avoid circular import
            from ..llm.clients import LLMClient
            llm_client = LLMClient(first_agent['config'])
            async with llm_client:
                synthesis = await llm_client.generate(synthesis_query, "", stream=False)
            
            return synthesis
            
        except Exception as e:
            return f"Synthesis failed: {e}"
    
    def _handle_agent_error(self, agent: dict, error: str):
        """エージェントエラーの処理"""
        agent['error_count'] += 1
        
        # レート制限の検出
        if 'rate limit' in error.lower() or 'too many requests' in error.lower():
            # 指数バックオフ
            backoff_time = min(300, 30 * (2 ** agent['error_count']))  # 最大5分
            agent['rate_limited_until'] = time.time() + backoff_time
            console.print(f"[yellow]Agent {agent['provider']} rate limited for {backoff_time}s[/yellow]")
        
        # エラーが多すぎる場合は一時的に無効化
        if agent['error_count'] >= 3:
            agent['available'] = False
            console.print(f"[red]Agent {agent['provider']} temporarily disabled due to errors[/red]")
    
    def get_status_summary(self) -> str:
        """マルチエージェントシステムの状態要約"""
        mode = self.get_operation_mode()
        available_count = len([a for a in self.available_agents if a['available']])
        
        summary = [
            f"Operation Mode: {mode}",
            f"Available Agents: {available_count}/{len(self.available_agents)}",
        ]
        
        if self.boss_consultation_enabled:
            summary.append(f"Boss Consultation: {self.boss_consultation_mode} (used {self.boss_used_count} times)")
        
        if available_count > 0:
            agent_names = [a['provider'] for a in self.available_agents if a['available']]
            summary.append(f"Active: {', '.join(agent_names)}")
        
        return " | ".join(summary)
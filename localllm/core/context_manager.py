"""Smart context management system"""

import os
import time
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.clients import LLMClient
    from .project_dna import ProjectDNA

from .config import get_config_manager, ContextConfig
from .i18n import t

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    console = Console()

class SmartContextManager:
    """革新的なコンテキスト管理システム"""
    
    def __init__(self, max_tokens: Optional[int] = None, config: Optional[ContextConfig] = None):
        # 設定システムとの統合
        self.config_manager = get_config_manager()
        self.config = config or self.config_manager.get_context_config()
        
        # max_tokensは設定ファイルまたは引数から取得
        self.max_tokens = max_tokens or self.config.max_tokens
        
        # 既存の属性
        self.file_cache = {}
        self.relevance_scores = {}
        self.context_history = []
        self.compressed_contexts = {}
        
        # 設定に基づく動的な閾値
        self.compression_threshold = self.max_tokens * self.config.compression_threshold
        self.warning_threshold = self.max_tokens * self.config.warning_threshold
        
        # 新しい監視機能
        self.current_tokens = 0
        self.token_usage_history = []
        self.last_warning_time = 0
        
    def calculate_relevance(self, file_path: str, query: str, project_dna: 'ProjectDNA') -> float:
        """ファイルの関連度を計算（革新的アルゴリズム）"""
        score = 0.0
        
        # ファイル名の関連度
        if any(keyword.lower() in file_path.lower() for keyword in query.split()):
            score += 0.3
            
        # 拡張子の関連度
        ext = Path(file_path).suffix
        if ext in project_dna.file_patterns:
            score += 0.2
            
        # 最近の変更履歴
        try:
            stat = os.stat(file_path)
            age_days = (time.time() - stat.st_mtime) / (24 * 3600)
            if age_days < 1:
                score += 0.3
            elif age_days < 7:
                score += 0.2
        except:
            pass
            
        # ファイルサイズ（適度なサイズを優先）
        try:
            size = os.path.getsize(file_path)
            if 100 < size < 10000:  # 100B〜10KB
                score += 0.2
        except:
            pass
            
        return min(score, 1.0)
    
    def select_optimal_context(self, query: str, project_dna: 'ProjectDNA', 
                             available_files: List[str]) -> List[str]:
        """最適なコンテキストを自動選択"""
        scored_files = []
        
        for file_path in available_files:
            relevance = self.calculate_relevance(file_path, query, project_dna)
            scored_files.append((file_path, relevance))
        
        # 関連度でソートし、トークン制限内で選択
        scored_files.sort(key=lambda x: x[1], reverse=True)
        
        selected_files = []
        total_tokens = len(query.split()) * 2  # クエリのトークン数を推定
        
        for file_path, score in scored_files:
            if score < 0.1:  # 関連度が低すぎる場合はスキップ
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_tokens = len(content.split())
                    
                if total_tokens + file_tokens < self.max_tokens * 0.8:  # 80%まで使用
                    selected_files.append(file_path)
                    total_tokens += file_tokens
                else:
                    break
            except:
                continue
                
        return selected_files
    
    async def compress_context(self, context: str, llm_client: 'LLMClient', summary_length: str = "medium") -> str:
        """LLMを使用してコンテキストを圧縮"""
        if len(context.split()) < self.compression_threshold * 0.5:
            return context  # 圧縮不要
        
        # 圧縮レベル設定
        compression_levels = {
            "brief": "Summarize this in 2-3 sentences, focusing on key points only.",
            "medium": "Summarize this in 1-2 paragraphs, preserving important details and context.",
            "detailed": "Create a comprehensive summary that retains most important information while reducing length by 50%."
        }
        
        compression_prompt = compression_levels.get(summary_length, compression_levels["medium"])
        
        system_prompt = f"""You are a context compression expert. Your task is to compress the given text while preserving all essential information for a coding assistant.

{compression_prompt}

Focus on:
- Key technical details
- Important file names and paths
- Error messages and their solutions
- Code snippets and modifications
- Process steps and outcomes

Remove:
- Verbose explanations
- Redundant information
- Unnecessary background context
"""
        
        try:
            compressed = await llm_client.generate(
                f"Please compress this context:\n\n{context}",
                system_prompt,
                stream=False
            )
            
            # 圧縮結果をキャッシュ
            context_hash = hashlib.md5(context.encode()).hexdigest()
            self.compressed_contexts[context_hash] = {
                'original_length': len(context),
                'compressed_length': len(compressed),
                'compressed_content': compressed,
                'compression_ratio': len(compressed) / len(context),
                'timestamp': time.time()
            }
            
            return compressed
            
        except Exception as e:
            console.print(f"[yellow]Context compression failed: {e}. Using original.[/yellow]")
            return context
    
    def get_context_summary(self) -> str:
        """コンテキスト圧縮の統計情報を取得"""
        if not self.compressed_contexts:
            return "No context compression performed yet."
        
        total_original = sum(c['original_length'] for c in self.compressed_contexts.values())
        total_compressed = sum(c['compressed_length'] for c in self.compressed_contexts.values())
        avg_ratio = sum(c['compression_ratio'] for c in self.compressed_contexts.values()) / len(self.compressed_contexts)
        
        return f"Context Compression Stats: {len(self.compressed_contexts)} compressions, avg ratio: {avg_ratio:.2f}, saved: {total_original - total_compressed} chars"
    
    def estimate_tokens(self, text: str) -> int:
        """より正確なトークン数推定"""
        if not text:
            return 0
        
        # 日本語と英語のトークン数推定の改善
        # 日本語：文字数 * 0.75、英語：単語数 * 1.3
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        japanese_chars = len(text) - english_chars
        
        # 単語数ベースの計算
        words = len(text.split())
        
        # より正確な推定：
        # - 英語単語は平均1.3トークン
        # - 日本語文字は平均0.75トークン
        # - コード部分は単語数の1.5倍
        
        if english_chars > japanese_chars:
            # 主に英語・コード
            estimated = words * 1.3
        else:
            # 主に日本語
            estimated = japanese_chars * 0.75 + words * 0.5
        
        # コードブロックを検出してボーナス
        if '```' in text or '    ' in text:  # インデントやコードブロック
            estimated *= 1.2
        
        return int(estimated)
    
    def update_token_count(self, context: str):
        """現在のトークン数を更新"""
        self.current_tokens = self.estimate_tokens(context)
        self.token_usage_history.append({
            'timestamp': time.time(),
            'tokens': self.current_tokens,
            'ratio': self.current_tokens / self.max_tokens
        })
        
        # 履歴の制限（最新100件）
        if len(self.token_usage_history) > 100:
            self.token_usage_history = self.token_usage_history[-100:]
    
    def check_context_status(self, context: str, show_warnings: bool = True) -> Dict[str, any]:
        """コンテキスト状況をチェック"""
        self.update_token_count(context)
        
        usage_ratio = self.current_tokens / self.max_tokens
        status = {
            'current_tokens': self.current_tokens,
            'max_tokens': self.max_tokens,
            'usage_ratio': usage_ratio,
            'needs_compression': self.config_manager.should_compress(self.current_tokens),
            'needs_warning': self.config_manager.should_warn(self.current_tokens),
            'status': 'normal'
        }
        
        # ステータス判定
        if usage_ratio >= self.config.warning_threshold:
            status['status'] = 'critical'
        elif usage_ratio >= self.config.compression_threshold:
            status['status'] = 'warning'
        
        # 警告表示
        if show_warnings and status['needs_warning']:
            self._show_context_warning(status)
        
        return status
    
    def _show_context_warning(self, status: Dict[str, any]):
        """コンテキスト警告を表示"""
        current_time = time.time()
        # 1分以内の重複警告を避ける
        if current_time - self.last_warning_time < 60:
            return
        
        self.last_warning_time = current_time
        usage_percent = status['usage_ratio'] * 100
        
        if status['status'] == 'critical':
            msg = t('context_critical', usage=usage_percent)
            console.print(f"⚠️ [red]{msg}[/red]")
            console.print(f"[yellow]{t('context_critical_advice')}[/yellow]")
        elif status['status'] == 'warning':
            msg = t('context_warning', usage=usage_percent)
            console.print(f"⚠️ [yellow]{msg}[/yellow]")
    
    def get_optimal_compression_strategy(self, context: str) -> str:
        """最適な圧縮戦略を決定"""
        status = self.check_context_status(context, show_warnings=False)
        
        if status['usage_ratio'] >= 0.9:
            return "brief"  # 緊急圧縮
        elif status['usage_ratio'] >= 0.8:
            return "medium"  # 標準圧縮
        else:
            return "detailed"  # 詳細保持
    
    def auto_manage_context(self, context: str, llm_client: 'LLMClient') -> str:
        """自動コンテキスト管理"""
        status = self.check_context_status(context)
        
        if not status['needs_compression']:
            return context
        
        if not self.config.auto_compression:
            # 自動圧縮が無効の場合は警告のみ
            return context
        
        # 自動圧縮実行
        compression_strategy = self.get_optimal_compression_strategy(context)
        msg = t('auto_compressing', strategy=compression_strategy)
        console.print(f"🗜️ [cyan]{msg}[/cyan]")
        
        return self.compress_context(context, llm_client, compression_strategy)
    
    def get_context_metrics(self) -> Dict[str, any]:
        """コンテキストメトリクスを取得"""
        if not self.token_usage_history:
            return {
                'current_tokens': 0,
                'max_tokens': self.max_tokens,
                'usage_ratio': 0.0,
                'avg_usage': 0.0,
                'peak_usage': 0.0
            }
        
        recent_usage = [entry['ratio'] for entry in self.token_usage_history[-10:]]
        
        return {
            'current_tokens': self.current_tokens,
            'max_tokens': self.max_tokens,
            'usage_ratio': self.current_tokens / self.max_tokens,
            'avg_usage': sum(recent_usage) / len(recent_usage),
            'peak_usage': max(entry['ratio'] for entry in self.token_usage_history),
            'compression_threshold': self.config.compression_threshold,
            'warning_threshold': self.config.warning_threshold,
            'auto_compression': self.config.auto_compression
        }
    
    def optimize_for_model(self, model_name: str):
        """モデルに応じた最適化"""
        self.config_manager.auto_adjust_for_model(model_name)
        new_max = self.config_manager.get_max_tokens()
        
        if new_max != self.max_tokens:
            msg = t('context_optimized', model=model_name, tokens=new_max)
            console.print(f"📊 [green]{msg}[/green]")
            self.max_tokens = new_max
            self.compression_threshold = new_max * self.config.compression_threshold
            self.warning_threshold = new_max * self.config.warning_threshold
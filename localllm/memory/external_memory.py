"""External memory system implementation"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# タスク分割システムをインポート
from .task_chunking import TaskChunkingSystem, TaskStatus, TaskPriority

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

class ExternalMemorySystem:
    """外部記憶システム - コンテキスト制限を補完する永続化メモリ"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.memory_dir = root_path / ".localllm_memory"
        self.todo_file = self.memory_dir / "todo.md"
        self.index_file = self.memory_dir / "memory_index.md"
        self.session_log = self.memory_dir / "session_log.md"
        self.records_dir = self.memory_dir / "records"
        self.metadata_file = self.memory_dir / "metadata.json"
        self.current_session_id = str(uuid.uuid4())[:8]
        self.console_buffer = []
        
        self._initialize_memory_structure()
        
        # タスク分割システムの初期化
        self.task_chunking = TaskChunkingSystem(self.memory_dir)
        
    def _initialize_memory_structure(self):
        """メモリディレクトリ構造の初期化"""
        self.memory_dir.mkdir(exist_ok=True)
        self.records_dir.mkdir(exist_ok=True)
        
        # メタデータファイルの初期化
        if not self.metadata_file.exists():
            metadata = {
                "created": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "sessions": [],
                "total_records": 0
            }
            self._save_metadata(metadata)
    
    def check_existing_data(self) -> bool:
        """既存データの存在確認"""
        has_todos = self.todo_file.exists() and self.todo_file.stat().st_size > 0
        has_records = self.records_dir.exists() and any(self.records_dir.iterdir())
        has_session_log = self.session_log.exists() and self.session_log.stat().st_size > 0
        
        return has_todos or has_records or has_session_log
    
    def show_cleanup_prompt(self) -> bool:
        """クリーンアップの確認プロンプトを表示"""
        if not self.check_existing_data():
            return False
            
        console.print("\n🧠 [bold yellow]External Memory Data Found[/bold yellow]")
        console.print("Previous session data exists in .localllm_memory/")
        
        # データサマリーを表示
        self._show_data_summary()
        
        console.print("\nOptions:")
        console.print("1. Continue with existing data")
        console.print("2. Archive old data and start fresh")
        console.print("3. Delete all external memory data")
        
        try:
            choice = Prompt.ask(
                "How would you like to proceed?",
                choices=["1", "2", "3"],
                default="1"
            )
            
            if choice == "1":
                console.print("✅ [green]Continuing with existing data[/green]")
                return True
            elif choice == "2":
                self._archive_data()
                console.print("📦 [green]Data archived and memory refreshed[/green]")
                return True
            else:  # choice == "3"
                self._delete_all_data()
                console.print("🗑️ [yellow]All external memory data deleted[/yellow]")
                return True
                
        except KeyboardInterrupt:
            console.print("\n⏸️ [yellow]Continuing with existing data[/yellow]")
            return True
    
    def _show_data_summary(self):
        """データサマリーの表示"""
        summary = []
        
        if self.todo_file.exists():
            todo_count = len([line for line in self.todo_file.read_text(encoding='utf-8').split('\n') if line.strip().startswith('- [ ]')])
            summary.append(f"📝 {todo_count} pending TODOs")
        
        if self.records_dir.exists():
            record_count = len(list(self.records_dir.glob("*.md")))
            summary.append(f"📄 {record_count} external records")
        
        if self.session_log.exists():
            log_size = self.session_log.stat().st_size
            summary.append(f"📊 {log_size//1024}KB session logs")
        
        if summary:
            console.print("   " + " | ".join(summary))
    
    def _archive_data(self):
        """データのアーカイブ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = self.memory_dir / f"archive_{timestamp}"
        archive_dir.mkdir(exist_ok=True)
        
        # 既存ファイルをアーカイブに移動
        for file_path in self.memory_dir.iterdir():
            if file_path.is_file() and file_path.name != "metadata.json":
                file_path.rename(archive_dir / file_path.name)
        
        # レコードディレクトリをアーカイブ
        if self.records_dir.exists():
            archive_records = archive_dir / "records"
            self.records_dir.rename(archive_records)
            self.records_dir.mkdir(exist_ok=True)
    
    def _delete_all_data(self):
        """全データの削除"""
        import shutil
        if self.memory_dir.exists():
            shutil.rmtree(self.memory_dir)
        self._initialize_memory_structure()
    
    def _save_metadata(self, metadata: dict):
        """メタデータの保存"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _load_metadata(self) -> dict:
        """メタデータの読み込み"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def add_todo(self, task: str, priority: str = "medium", context: str = ""):
        """TODOの追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        todo_entry = f"- [ ] **{task}** (Priority: {priority}) - {timestamp}"
        if context:
            todo_entry += f"\n  Context: {context}"
        todo_entry += "\n"
        
        with open(self.todo_file, 'a', encoding='utf-8') as f:
            f.write(todo_entry)
        
        console.print(f"📝 [green]TODO added: {task}[/green]")
    
    def mark_todo_complete(self, task_pattern: str):
        """TODOの完了マーク"""
        if not self.todo_file.exists():
            return False
            
        content = self.todo_file.read_text(encoding='utf-8')
        updated_content = content.replace(
            f"- [ ] **{task_pattern}**",
            f"- [x] **{task_pattern}**"
        )
        
        if content != updated_content:
            self.todo_file.write_text(updated_content, encoding='utf-8')
            console.print(f"✅ [green]TODO completed: {task_pattern}[/green]")
            return True
        return False
    
    def save_external_record(self, filename: str, content: str, category: str = "general"):
        """外部記録の保存"""
        record_file = self.records_dir / f"{filename}.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ヘッダー付きで保存
        full_content = f"""# {filename.replace('_', ' ').title()}

**Created**: {timestamp}  
**Category**: {category}  
**Session**: {self.current_session_id}

---

{content}
"""
        
        record_file.write_text(full_content, encoding='utf-8')
        
        # インデックスファイルを更新
        self._update_memory_index(filename, category, timestamp)
        
        console.print(f"💾 [green]External record saved: {filename}[/green]")
    
    def _update_memory_index(self, filename: str, category: str, timestamp: str):
        """メモリインデックスの更新"""
        index_entry = f"- [{timestamp}] **{filename}** ({category}) - Session: {self.current_session_id}\n"
        
        with open(self.index_file, 'a', encoding='utf-8') as f:
            f.write(index_entry)
    
    def record_console_output(self, output: str, output_type: str = "info"):
        """コンソール出力の記録"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] **{output_type.upper()}**: {output}\n"
        
        # バッファに追加（メモリ効率のため）
        self.console_buffer.append(log_entry)
        
        # バッファが大きくなったらファイルに書き出し
        if len(self.console_buffer) >= 10:
            self.flush_console_buffer()
    
    def flush_console_buffer(self):
        """コンソールバッファをファイルに書き出し"""
        if not self.console_buffer:
            return
            
        session_header = f"\n## Session {self.current_session_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        with open(self.session_log, 'a', encoding='utf-8') as f:
            if not self.session_log.exists() or self.session_log.stat().st_size == 0:
                f.write("# LocalLLM Code Session Logs\n")
            f.write(session_header)
            f.writelines(self.console_buffer)
        
        self.console_buffer.clear()
    
    def get_todo_summary(self) -> str:
        """TODO一覧の取得"""
        if not self.todo_file.exists():
            return "No TODOs found"
            
        content = self.todo_file.read_text(encoding='utf-8')
        pending_todos = [line for line in content.split('\n') if line.strip().startswith('- [ ]')]
        completed_todos = [line for line in content.split('\n') if line.strip().startswith('- [x]')]
        
        return f"📝 TODOs: {len(pending_todos)} pending, {len(completed_todos)} completed"
    
    def get_memory_summary(self) -> str:
        """外部記憶の要約取得"""
        summary_parts = []
        
        # TODO要約
        summary_parts.append(self.get_todo_summary())
        
        # 外部記録要約
        if self.records_dir.exists():
            record_count = len(list(self.records_dir.glob("*.md")))
            summary_parts.append(f"📄 External records: {record_count}")
        
        # セッションログ要約
        if self.session_log.exists():
            log_size = self.session_log.stat().st_size
            summary_parts.append(f"📊 Session logs: {log_size//1024}KB")
        
        return " | ".join(summary_parts) if summary_parts else "No external memory data"
    
    def search_records(self, query: str) -> List[Dict[str, str]]:
        """外部記録の検索"""
        results = []
        
        if not self.records_dir.exists():
            return results
            
        for record_file in self.records_dir.glob("*.md"):
            content = record_file.read_text(encoding='utf-8')
            if query.lower() in content.lower():
                # 最初の数行を抜粋
                lines = content.split('\n')
                excerpt = '\n'.join(lines[:10])
                results.append({
                    'filename': record_file.stem,
                    'excerpt': excerpt,
                    'path': str(record_file)
                })
        
        return results
    
    def cleanup_session(self):
        """セッション終了時のクリーンアップ"""
        # コンソールバッファをフラッシュ
        self.flush_console_buffer()
        
        # メタデータを更新
        metadata = self._load_metadata()
        metadata['last_accessed'] = datetime.now().isoformat()
        metadata['sessions'].append({
            'session_id': self.current_session_id,
            'timestamp': datetime.now().isoformat()
        })
        self._save_metadata(metadata)
    
    # ========================================
    # タスク分割・継続機能（コンテキスト効率化）
    # ========================================
    
    def split_task_for_context_efficiency(self, task_description: str, max_tokens_per_chunk: int = 2000) -> List[str]:
        """大きなタスクをコンテキスト効率的なチャンクに分割"""
        chunk_ids = self.task_chunking.split_large_task(task_description, max_tokens_per_chunk)
        
        # 分割結果をログに記録
        self.record_console_output(
            f"Large task split into {len(chunk_ids)} chunks: {', '.join(chunk_ids[:3])}{'...' if len(chunk_ids) > 3 else ''}", 
            "task_split"
        )
        
        return chunk_ids
    
    def get_next_contextual_tasks(self, max_context_tokens: int = 4000) -> List[Dict[str, any]]:
        """コンテキスト制限内で実行可能な次のタスクを取得"""
        tasks = self.task_chunking.get_next_executable_tasks(max_context_tokens)
        
        task_data = []
        for task in tasks:
            task_context = self.task_chunking.get_task_context(task.id)
            task_data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority.name,
                'estimated_tokens': task.estimated_tokens,
                'context': task_context,
                'status': task.status.value
            })
        
        return task_data
    
    def complete_task_chunk(self, task_id: str, completion_notes: str = "") -> bool:
        """タスクチャンクの完了処理"""
        # タスクを完了状態に更新
        self.task_chunking.update_task_status(task_id, TaskStatus.COMPLETED, completion_notes)
        
        # 完了を外部記録として保存
        task = self.task_chunking.tasks.get(task_id)
        if task:
            completion_record = f"""# Task Completed: {task.title}

## Description
{task.description}

## Completion Notes
{completion_notes}

## Completion Time
{datetime.now().isoformat()}

## Priority
{task.priority.name}

## Estimated vs Actual
- Estimated tokens: {task.estimated_tokens}
- Parent task: {task.parent_task_id or 'None'}
"""
            self.save_external_record(f"task_completed_{task_id[:8]}", completion_record, "task_completion")
            
            # コンソールログ
            self.record_console_output(f"Task completed: {task.title}", "task_completion")
            return True
        
        return False
    
    def get_task_progress_summary(self) -> str:
        """タスク進捗の要約を取得"""
        progress = self.task_chunking.get_progress_summary()
        
        return f"""📊 Task Progress: {progress['progress_percentage']:.1f}% ({progress['completed_tasks']}/{progress['total_tasks']})
Status: {progress['status_counts']['pending']} pending, {progress['status_counts']['in_progress']} in progress, {progress['status_counts']['completed']} completed
Priority: {progress['priority_counts']['HIGH']} high, {progress['priority_counts']['MEDIUM']} medium, {progress['priority_counts']['LOW']} low"""
    
    def suggest_next_work_session(self, available_context_tokens: int = 4000) -> Dict[str, any]:
        """次の作業セッションの提案"""
        next_tasks = self.get_next_contextual_tasks(available_context_tokens)
        
        if not next_tasks:
            return {
                'has_tasks': False,
                'message': 'すべてのタスクが完了しているか、依存関係待ちです',
                'suggestions': ['新しいタスクを追加', '依存関係を確認', '完了タスクをレビュー']
            }
        
        total_estimated_tokens = sum(task['estimated_tokens'] for task in next_tasks)
        high_priority_count = len([t for t in next_tasks if t['priority'] == 'HIGH'])
        
        return {
            'has_tasks': True,
            'task_count': len(next_tasks),
            'total_estimated_tokens': total_estimated_tokens,
            'high_priority_count': high_priority_count,
            'tasks': next_tasks,
            'message': f'{len(next_tasks)}個のタスクが実行可能です（推定{total_estimated_tokens}トークン）'
        }
    
    def create_task_from_description(self, description: str, priority: str = "medium") -> str:
        """説明からタスクを作成"""
        # 優先度の変換
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        
        task_priority = priority_map.get(priority.lower(), TaskPriority.MEDIUM)
        
        # タイトルを自動生成（最初の行または50文字まで）
        lines = description.strip().split('\n')
        title = lines[0][:50] + ('...' if len(lines[0]) > 50 else '')
        
        # トークン数を推定
        estimated_tokens = len(description.split())
        
        # タスクが大きすぎる場合は自動分割
        if estimated_tokens > 2000:
            console.print(f"🔄 [yellow]Large task detected ({estimated_tokens} tokens). Auto-splitting...[/yellow]")
            chunk_ids = self.split_task_for_context_efficiency(description)
            return f"分割されたタスク群: {len(chunk_ids)}個のチャンク"
        else:
            task_id = self.task_chunking.create_task_chunk(title, description, estimated_tokens, task_priority)
            self.record_console_output(f"New task created: {title}", "task_creation")
            return task_id
    
    def get_context_optimized_summary(self, max_tokens: int = 500) -> str:
        """コンテキスト最適化された要約を取得"""
        # 進捗サマリー
        progress_summary = self.get_task_progress_summary()
        
        # 次のタスク候補
        next_session = self.suggest_next_work_session(max_tokens)
        
        # メモリサマリー
        memory_summary = self.get_memory_summary()
        
        summary = f"""## LocalLLM Code セッション要約

### タスク進捗
{progress_summary}

### 次の作業セッション
{next_session['message']}
{'高優先度タスク: ' + str(next_session['high_priority_count']) + '個' if next_session.get('high_priority_count', 0) > 0 else ''}

### 外部記憶状況  
{memory_summary}

---
**コンテキスト効率化**: 制限内で最適なタスクを選択し、分割されたタスクで継続的に作業できます
"""
        
        return summary
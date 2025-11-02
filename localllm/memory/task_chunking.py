"""タスク分割・継続システム"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TaskChunk:
    """分割されたタスクの単位"""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: float
    updated_at: float
    estimated_tokens: int
    parent_task_id: Optional[str] = None
    dependencies: List[str] = None
    context_data: Dict[str, Any] = None
    completion_criteria: str = ""
    notes: str = ""
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.context_data is None:
            self.context_data = {}

class TaskChunkingSystem:
    """コンテキスト効率化のためのタスク分割システム"""
    
    def __init__(self, memory_path: Path):
        self.memory_path = memory_path
        self.tasks_file = memory_path / "task_chunks.json"
        self.tasks: Dict[str, TaskChunk] = {}
        self.load_tasks()
    
    def load_tasks(self):
        """保存されたタスクを読み込み"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for task_id, task_data in data.items():
                    task_data['status'] = TaskStatus(task_data['status'])
                    task_data['priority'] = TaskPriority(task_data['priority'])
                    self.tasks[task_id] = TaskChunk(**task_data)
            except Exception as e:
                print(f"タスク読み込みエラー: {e}")
    
    def save_tasks(self):
        """タスクを保存"""
        try:
            data = {}
            for task_id, task in self.tasks.items():
                task_dict = asdict(task)
                task_dict['status'] = task.status.value
                task_dict['priority'] = task.priority.value
                data[task_id] = task_dict
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"タスク保存エラー: {e}")
    
    def create_task_chunk(self, title: str, description: str, 
                         estimated_tokens: int, priority: TaskPriority = TaskPriority.MEDIUM,
                         parent_task_id: Optional[str] = None) -> str:
        """新しいタスクチャンクを作成"""
        task_id = str(uuid.uuid4())
        current_time = time.time()
        
        task = TaskChunk(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=current_time,
            updated_at=current_time,
            estimated_tokens=estimated_tokens,
            parent_task_id=parent_task_id
        )
        
        self.tasks[task_id] = task
        self.save_tasks()
        return task_id
    
    def split_large_task(self, task_description: str, max_tokens_per_chunk: int = 2000) -> List[str]:
        """大きなタスクを小さなチャンクに分割"""
        # シンプルな分割ロジック（実際はLLMを使用してより知的に分割）
        
        # キーワードベースの分割ポイント検出
        split_keywords = [
            "1.", "2.", "3.", "4.", "5.",
            "まず", "次に", "その後", "最後に",
            "ステップ", "段階", "フェーズ"
        ]
        
        chunks = []
        current_chunk = ""
        
        lines = task_description.split('\n')
        for line in lines:
            if any(keyword in line for keyword in split_keywords) and current_chunk:
                # 新しいチャンクの開始
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                current_chunk += "\n" + line
        
        # 最後のチャンクを追加
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # チャンクが1つの場合は、長さベースで分割
        if len(chunks) == 1 and len(task_description) > max_tokens_per_chunk * 4:
            chunk_size = max_tokens_per_chunk * 4
            chunks = [
                task_description[i:i+chunk_size] 
                for i in range(0, len(task_description), chunk_size)
            ]
        
        # TaskChunkとして保存
        parent_task_id = self.create_task_chunk(
            title="大規模タスク（親）",
            description=task_description[:100] + "...",
            estimated_tokens=len(task_description.split()),
            priority=TaskPriority.HIGH
        )
        
        chunk_ids = []
        for i, chunk_desc in enumerate(chunks):
            chunk_id = self.create_task_chunk(
                title=f"サブタスク {i+1}",
                description=chunk_desc,
                estimated_tokens=len(chunk_desc.split()),
                parent_task_id=parent_task_id
            )
            chunk_ids.append(chunk_id)
        
        return chunk_ids
    
    def get_next_executable_tasks(self, max_context_tokens: int = 4000) -> List[TaskChunk]:
        """実行可能な次のタスクを取得（コンテキスト制限内で）"""
        # 優先度順でソート
        available_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and self._dependencies_satisfied(task.id)
        ]
        
        available_tasks.sort(key=lambda t: (t.priority.value, -t.created_at), reverse=True)
        
        # コンテキスト制限内で選択
        selected_tasks = []
        total_tokens = 0
        
        for task in available_tasks:
            if total_tokens + task.estimated_tokens <= max_context_tokens:
                selected_tasks.append(task)
                total_tokens += task.estimated_tokens
            else:
                break
        
        return selected_tasks
    
    def _dependencies_satisfied(self, task_id: str) -> bool:
        """タスクの依存関係が満たされているかチェック"""
        task = self.tasks.get(task_id)
        if not task or not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def update_task_status(self, task_id: str, status: TaskStatus, notes: str = ""):
        """タスクの状態を更新"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = time.time()
            if notes:
                self.tasks[task_id].notes += f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {notes}"
            self.save_tasks()
    
    def add_task_dependency(self, task_id: str, depends_on_task_id: str):
        """タスクの依存関係を追加"""
        if task_id in self.tasks:
            if depends_on_task_id not in self.tasks[task_id].dependencies:
                self.tasks[task_id].dependencies.append(depends_on_task_id)
                self.save_tasks()
    
    def get_task_context(self, task_id: str) -> str:
        """タスクに必要なコンテキスト情報を取得"""
        task = self.tasks.get(task_id)
        if not task:
            return ""
        
        context_parts = [
            f"# タスク: {task.title}",
            f"説明: {task.description}",
            f"優先度: {task.priority.name}",
            f"作成日時: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.created_at))}"
        ]
        
        # 親タスクの情報
        if task.parent_task_id and task.parent_task_id in self.tasks:
            parent = self.tasks[task.parent_task_id]
            context_parts.append(f"親タスク: {parent.title}")
        
        # 依存関係情報
        if task.dependencies:
            dep_titles = [
                self.tasks[dep_id].title for dep_id in task.dependencies 
                if dep_id in self.tasks
            ]
            context_parts.append(f"依存タスク: {', '.join(dep_titles)}")
        
        # 追加のコンテキストデータ
        if task.context_data:
            for key, value in task.context_data.items():
                context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """進捗状況のサマリーを取得"""
        status_counts = {status.value: 0 for status in TaskStatus}
        priority_counts = {priority.name: 0 for priority in TaskPriority}
        
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
            priority_counts[task.priority.name] += 1
        
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        total_tasks = len(self.tasks)
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "progress_percentage": progress_percentage,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks
        }
    
    def cleanup_completed_tasks(self, days_old: int = 30):
        """完了したタスクをクリーンアップ"""
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        tasks_to_remove = [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED and task.updated_at < cutoff_time
        ]
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        self.save_tasks()
        return len(tasks_to_remove)
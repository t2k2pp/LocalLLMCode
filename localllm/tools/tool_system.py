"""Tool system implementation"""

import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any

from ..core.config import get_config_manager
from ..intelligence import SimpleCodeAnalyzer

try:
    from rich.console import Console
    from rich.prompt import Confirm
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    class Confirm:
        @staticmethod
        def ask(*args, **kwargs):
            return True
    console = Console()

class ToolSystem:
    """革新的なツールシステム - 安全で強力な操作"""
    
    def __init__(self, root_path: Path, safe_mode: bool = True):
        self.root_path = root_path
        self.safe_mode = safe_mode
        self.file_snapshots = {}  # ファイル変更前のスナップショット
        self.modification_history = []  # ファイル変更履歴
        self.config_manager = get_config_manager()  # OS設定管理
        self.code_analyzer = SimpleCodeAnalyzer()  # コード解析エンジン
        self.tools = {
            'read_file': self.read_file,
            'write_file': self.write_file,
            'edit_file': self.edit_file,
            'list_files': self.list_files,
            'create_file': self.create_file,
            'run_command': self.run_command,
            'search_files': self.search_files,
            'git_status': self.git_status,
            'git_commit': self.git_commit,
            'analyze_code': self.analyze_code,
            'run_program': self.run_program,
            'debug_error': self.debug_error,
            'read_files': self.read_files,
            'read_folder': self.read_folder,
            'mkdir': self.create_directory,
            'create_directory': self.create_directory,  # エイリアス追加
            'remove_file': self.remove_file,
            'delete_file': self.remove_file,  # エイリアス
            'remove_directory': self.remove_directory,
            'delete_directory': self.remove_directory,  # エイリアス
            'analyze_improvements': self.analyze_improvements,
            'check_code_quality': self.check_code_quality
        }
    
    def get_tool_descriptions(self) -> str:
        """ツールの説明を取得"""
        # OS設定を取得
        os_config = self.config_manager.get_os_config()
        os_commands = self.config_manager.get_os_commands()
        
        # OS別の具体的なコマンド例を生成
        list_cmd = os_commands.get('list_files', 'ls')
        copy_cmd = os_commands.get('copy', 'cp')
        clear_cmd = os_commands.get('clear', 'clear')
        
        # run_commandの説明をOS別に調整
        if os_config.os_type == "windows":
            run_cmd_desc = f'Run shell command (Windows examples: "{list_cmd}", "type file.txt", "{clear_cmd}"): run_command <command>'
        else:
            run_cmd_desc = f'Run shell command (Unix examples: "{list_cmd}", "cat file.txt", "{clear_cmd}"): run_command <command>'
        
        descriptions = {
            'read_file': 'Read contents of a file: read_file <path>',
            'write_file': 'Write content to a file: write_file <path> <content>',
            'edit_file': 'Edit specific lines in a file: edit_file <path> <start_line> <end_line> <new_content>',
            'list_files': f'List files in directory (equivalent to "{list_cmd}"): list_files <directory>',
            'create_file': 'Create new file: create_file <path> <content>',
            'run_command': run_cmd_desc,
            'search_files': 'Search for text in files: search_files <pattern> <directory>',
            'git_status': 'Check git status: git_status',
            'git_commit': 'Commit changes: git_commit <message>',
            'analyze_code': 'Analyze code structure: analyze_code <path>',
            'run_program': 'Run program with error analysis: run_program <file_path> [args]',
            'debug_error': 'Debug and fix error: debug_error <error_info> <file_path>',
            'read_files': 'Read multiple files: read_files <file1> <file2> ...',
            'read_folder': 'Read all files in folder: read_folder <directory> [extension]',
            'mkdir': 'Create directory: mkdir <directory_path>',
            'remove_file': 'Remove file (WITH USER CONFIRMATION): remove_file <file_path>',
            'remove_directory': 'Remove directory (WITH USER CONFIRMATION): remove_directory <directory_path>',
            'analyze_improvements': 'Analyze code and suggest improvements: analyze_improvements <file_path>',
            'check_code_quality': 'Check code quality metrics: check_code_quality <file_path>'
        }
        
        # OS情報を末尾に追加
        os_info = f"\nCurrent OS: {os_config.os_type.title()}, Shell: {os_config.shell_type}"
        
        return "\n".join(f"- {desc}" for desc in descriptions.values()) + os_info
    
    async def execute(self, tool_name: str, params: str) -> str:
        """ツールを実行"""
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"
        
        # ファイル操作前の事前チェック
        if self._requires_file_check(tool_name):
            check_result = self._pre_execute_file_check(tool_name, params)
            if check_result:
                return check_result
        
        try:
            return await self.tools[tool_name](params)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def _requires_file_check(self, tool_name: str) -> bool:
        """ツールがファイル操作前チェックを必要とするかどうか"""
        file_operation_tools = {
            'read_file', 'edit_file', 'run_program', 'analyze_code', 'debug_error'
        }
        return tool_name in file_operation_tools
    
    def _pre_execute_file_check(self, tool_name: str, params: str) -> str:
        """ファイル操作前の事前チェック"""
        try:
            # パラメータからファイルパスを抽出
            if tool_name in ['read_file', 'analyze_code']:
                file_path = Path(params.strip())
            elif tool_name in ['edit_file']:
                parts = params.split(' ', 3)
                if len(parts) >= 1:
                    file_path = Path(parts[0])
                else:
                    return None
            elif tool_name in ['run_program', 'debug_error']:
                parts = params.split(' ', 1)
                if len(parts) >= 1:
                    file_path = Path(parts[0])
                else:
                    return None
            else:
                return None
            
            # ファイル存在チェック
            if not file_path.exists():
                # 存在しないファイルの場合、現在のディレクトリ構造を提案
                parent_dir = file_path.parent if file_path.parent != Path('.') else Path('.')
                if parent_dir.exists():
                    try:
                        files_in_dir = list(parent_dir.iterdir())
                        file_names = [f.name for f in files_in_dir if f.is_file()][:10]
                        suggestion = f"File '{file_path}' not found. Files in {parent_dir}: {', '.join(file_names) if file_names else 'No files found'}"
                        return f"Error: {suggestion}. Consider using 'list_files {parent_dir}' to see available files."
                    except:
                        return f"Error: File '{file_path}' not found. Consider using 'list_files .' to see available files."
                else:
                    return f"Error: Neither file '{file_path}' nor directory '{parent_dir}' exists. Use 'list_files .' to see current directory structure."
            
            return None  # チェック通過
            
        except Exception:
            return None  # チェック失敗時は通常の実行を継続
    
    def _normalize_path(self, path_str: str) -> Path:
        """パスを正規化（Windows/Unix両対応）"""
        # Windowsのバックスラッシュをスラッシュに変換
        normalized = path_str.replace('\\', '/')
        return Path(normalized)
    
    def _is_safe_path(self, path: Path) -> bool:
        """パスが安全かチェック"""
        try:
            resolved = path.resolve()
            return str(resolved).startswith(str(self.root_path.resolve()))
        except:
            return False
    
    async def read_file(self, params: str) -> str:
        """ファイルを読み取り"""
        path = self._normalize_path(params.strip())
        
        if not self._is_safe_path(path):
            return "Error: Path is outside project directory"
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 構造化データファイルの場合は制限を緩める
            is_structured = any(ext in path.suffix.lower() for ext in ['.md', '.txt', '.json', '.yaml', '.yml', '.toml'])
            
            if is_structured and len(content) > 10000:
                return f"File content (first 10000 chars):\n{content[:10000]}...\n[File truncated - structured data file]"
            elif not is_structured and len(content) > 5000:
                return f"File content (first 5000 chars):\n{content[:5000]}...\n[File truncated]"
            
            return f"File content:\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"
    
    async def write_file(self, params: str) -> str:
        """ファイルに書き込み"""
        parts = params.split(' ', 1)
        if len(parts) < 2:
            return "Error: Usage: write_file <path> <content>"
        
        path = self._normalize_path(parts[0])
        content = parts[1]
        
        if not self._is_safe_path(path):
            return "Error: Path is outside project directory"
        
        # Safe mode: 常にファイル作成/上書きの確認を取る
        if self.safe_mode:
            if path.exists():
                if not Confirm.ask(f"File {path} exists. Overwrite?"):
                    return "Operation cancelled by user"
            else:
                if not Confirm.ask(f"Create new file {path}?"):
                    return "Operation cancelled by user"
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"
    
    async def edit_file(self, params: str) -> str:
        """ファイルを編集"""
        parts = params.split(' ', 3)
        if len(parts) < 4:
            return "Error: Usage: edit_file <path> <start_line> <end_line> <new_content>"
        
        path = self._normalize_path(parts[0])
        try:
            start_line = int(parts[1])
            end_line = int(parts[2])
            new_content = parts[3]
        except ValueError:
            return "Error: Line numbers must be integers"
        
        if not self._is_safe_path(path):
            return "Error: Path is outside project directory"
        
        try:
            # 編集前スナップショット作成
            snapshot_result = await self._create_file_snapshot(path)
            
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_content = ''.join(lines)
            
            # バックアップ作成
            backup_path = path.with_suffix(path.suffix + '.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 編集実行（1-indexed to 0-indexed）
            lines[start_line-1:end_line] = [new_content + '\n']
            modified_content = ''.join(lines)
            
            # コード破壊検知
            destruction_check = await self._check_code_destruction(path, original_content, modified_content)
            if destruction_check['is_destructive'] and self.safe_mode:
                console.print(f"⚠️ [red]Potential code destruction detected:[/red] {destruction_check['reason']}")
                if not Confirm.ask("Continue with this potentially destructive edit?"):
                    return f"Edit cancelled to prevent potential code destruction: {destruction_check['reason']}"
            
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 変更履歴を記録
            self._record_modification(path, original_content, modified_content, f"edit_file:{start_line}-{end_line}")
            
            result_msg = f"Successfully edited {path} (backup saved as {backup_path})"
            if destruction_check['is_destructive']:
                result_msg += f"\n⚠️ Warning: {destruction_check['reason']}"
            
            return result_msg
            
        except Exception as e:
            return f"Error editing file: {e}"
    
    async def _create_file_snapshot(self, file_path: Path) -> dict:
        """ファイルのスナップショットを作成"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                snapshot = {
                    'path': str(file_path),
                    'content': content,
                    'timestamp': time.time(),
                    'size': len(content),
                    'line_count': len(content.split('\n'))
                }
                
                self.file_snapshots[str(file_path)] = snapshot
                return {'success': True, 'snapshot': snapshot}
            else:
                return {'success': False, 'reason': 'File does not exist'}
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    async def _check_code_destruction(self, file_path: Path, original: str, modified: str) -> dict:
        """コード破壊の可能性をチェック"""
        destruction_indicators = {
            'is_destructive': False,
            'reason': '',
            'confidence': 0.0
        }
        
        # 基本的な破壊パターンをチェック
        original_lines = original.split('\n')
        modified_lines = modified.split('\n')
        
        # 大幅な行数減少（50%以上削除）
        if len(modified_lines) < len(original_lines) * 0.5:
            destruction_indicators['is_destructive'] = True
            destruction_indicators['reason'] = f"Massive line reduction: {len(original_lines)} → {len(modified_lines)} lines"
            destruction_indicators['confidence'] = 0.8
            return destruction_indicators
        
        # 重要な構造の削除をチェック（拡張子ベース）
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.py':
            # Python: import文、class定義、function定義の削除
            original_imports = len([line for line in original_lines if line.strip().startswith(('import ', 'from '))])
            modified_imports = len([line for line in modified_lines if line.strip().startswith(('import ', 'from '))])
            
            original_functions = len(re.findall(r'def\s+\w+\(', original))
            modified_functions = len(re.findall(r'def\s+\w+\(', modified))
            
            original_classes = len(re.findall(r'class\s+\w+', original))
            modified_classes = len(re.findall(r'class\s+\w+', modified))
            
            if (original_imports > 0 and modified_imports == 0) or \
               (original_functions > 0 and modified_functions == 0) or \
               (original_classes > 0 and modified_classes == 0):
                destruction_indicators['is_destructive'] = True
                destruction_indicators['reason'] = "Critical Python structures removed (imports/functions/classes)"
                destruction_indicators['confidence'] = 0.9
        
        elif file_extension in ['.js', '.ts']:
            # JavaScript/TypeScript: require/import文、function定義の削除
            original_imports = len([line for line in original_lines if 'import ' in line or 'require(' in line])
            modified_imports = len([line for line in modified_lines if 'import ' in line or 'require(' in line])
            
            original_functions = len(re.findall(r'function\s+\w+|=>\s*{', original))
            modified_functions = len(re.findall(r'function\s+\w+|=>\s*{', modified))
            
            if (original_imports > 0 and modified_imports == 0) or \
               (original_functions > 0 and modified_functions == 0):
                destruction_indicators['is_destructive'] = True
                destruction_indicators['reason'] = "Critical JavaScript structures removed"
                destruction_indicators['confidence'] = 0.8
        
        # 構文エラーの可能性をチェック
        if file_extension == '.py':
            try:
                import ast
                ast.parse(modified)
            except SyntaxError as e:
                destruction_indicators['is_destructive'] = True
                destruction_indicators['reason'] = f"Syntax error introduced: {str(e)}"
                destruction_indicators['confidence'] = 0.95
        
        # ファイルが空になった場合
        if len(modified.strip()) == 0 and len(original.strip()) > 0:
            destruction_indicators['is_destructive'] = True
            destruction_indicators['reason'] = "File content completely removed"
            destruction_indicators['confidence'] = 1.0
        
        return destruction_indicators
    
    def _record_modification(self, file_path: Path, original: str, modified: str, operation: str):
        """ファイル変更を記録"""
        modification = {
            'path': str(file_path),
            'timestamp': time.time(),
            'operation': operation,
            'original_size': len(original),
            'modified_size': len(modified),
            'original_lines': len(original.split('\n')),
            'modified_lines': len(modified.split('\n')),
            'change_ratio': len(modified) / len(original) if len(original) > 0 else 1.0
        }
        
        self.modification_history.append(modification)
        
        # 履歴が長くなりすぎないよう制限
        if len(self.modification_history) > 100:
            self.modification_history = self.modification_history[-50:]
    
    def get_modification_summary(self) -> str:
        """変更履歴の要約を取得"""
        if not self.modification_history:
            return "No file modifications recorded"
        
        recent_mods = self.modification_history[-10:]  # 最近10件
        total_mods = len(self.modification_history)
        
        summary_lines = [f"File modification history: {total_mods} total modifications"]
        summary_lines.append("Recent modifications:")
        
        for mod in recent_mods:
            timestamp_str = time.strftime("%H:%M:%S", time.localtime(mod['timestamp']))
            summary_lines.append(f"  {timestamp_str} - {mod['operation']} on {Path(mod['path']).name}")
        
        return "\n".join(summary_lines)
    
    async def list_files(self, params: str) -> str:
        """ファイル一覧を取得"""
        dir_path = Path(params.strip() or '.')
        
        if not self._is_safe_path(dir_path):
            return "Error: Path is outside project directory"
        
        try:
            files = []
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                size = ""
                if item.is_file():
                    try:
                        size = f" ({item.stat().st_size} bytes)"
                    except:
                        pass
                
                files.append(f"{'📁' if item.is_dir() else '📄'} {item.name}{size}")
            
            return f"Files in {dir_path}:\n" + "\n".join(files[:50])  # 最大50件
        except Exception as e:
            return f"Error listing files: {e}"
    
    async def create_file(self, params: str) -> str:
        """新しいファイルを作成"""
        # より安全なパラメータ解析：引用符を考慮
        import shlex
        try:
            parsed_args = shlex.split(params)
        except ValueError:
            # shlex解析失敗時は従来方式でフォールバック
            parts = params.split(' ', 1)
            if len(parts) < 2:
                return "Error: Usage: create_file <path> <content>"
            path = Path(parts[0])
            content = parts[1]
        else:
            if len(parsed_args) < 2:
                return "Error: Usage: create_file <path> <content>"
            
            # 最初の引数をパス、残りをコンテンツとして結合
            path = Path(parsed_args[0])
            content = ' '.join(parsed_args[1:])
        
        # パスにディレクトリ部分が含まれていない場合の警告
        if '/' not in str(path) and '\\' not in str(path):
            console.print(f"[yellow]警告: ディレクトリが指定されていません。現在のディレクトリに {path} を作成します[/yellow]")
        
        if not self._is_safe_path(path):
            return "Error: Path is outside project directory"
        
        if path.exists():
            return f"Error: File {path} already exists"
        
        # Safe mode: 新規ファイル作成の確認
        if self.safe_mode:
            if not Confirm.ask(f"Create new file {path}?"):
                return "Operation cancelled by user"
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully created {path}"
        except Exception as e:
            return f"Error creating file: {e}"
    
    async def create_directory(self, params: str) -> str:
        """ディレクトリを作成"""
        dir_path = Path(params.strip())
        
        if not self._is_safe_path(dir_path):
            return "Error: Path is outside project directory"
        
        if dir_path.exists():
            if dir_path.is_dir():
                return f"Directory {dir_path} already exists"
            else:
                return f"Error: {dir_path} exists but is not a directory"
        
        # Safe mode: 新規ディレクトリ作成の確認
        if self.safe_mode:
            if not Confirm.ask(f"Create directory {dir_path}?"):
                return "Operation cancelled by user"
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return f"Successfully created directory {dir_path}"
        except Exception as e:
            return f"Error creating directory: {e}"
    
    async def run_command(self, params: str) -> str:
        """シェルコマンドを実行"""
        command = params.strip()
        
        # 危険なコマンドのチェック
        dangerous_commands = ['rm -rf', 'sudo', 'chmod 777', 'format', 'del /s']
        deletion_commands = ['rm ', 'del ', 'rmdir ', 'remove ', 'unlink']
        
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            if self.safe_mode:
                return f"Error: Potentially dangerous command blocked: {command}"
        
        # 削除系コマンドの特別確認
        if any(delete_cmd in command.lower() for delete_cmd in deletion_commands):
            console.print(f"🚨 [bold red]DELETION COMMAND DETECTED[/bold red]")
            console.print(f"Command: {command}")
            if not Confirm.ask(f"❗ This command may DELETE files or directories. Are you sure you want to execute: '{command}'?"):
                return "❌ Deletion command cancelled by user"
        
        if self.safe_mode:
            if not Confirm.ask(f"Execute command: {command}?"):
                return "Command cancelled by user"
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.root_path,
                timeout=30
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
            
            return f"Command output:\n{output[:2000]}{'...' if len(output) > 2000 else ''}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error running command: {e}"
    
    async def search_files(self, params: str) -> str:
        """ファイル内をテキスト検索"""
        parts = params.split(' ', 1)
        if len(parts) < 2:
            return "Error: Usage: search_files <pattern> <directory>"
        
        pattern = parts[0]
        directory = Path(parts[1])
        
        if not self._is_safe_path(directory):
            return "Error: Path is outside project directory"
        
        try:
            results = []
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.txt', '.md']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if pattern.lower() in content.lower():
                            # 一致行を抽出
                            lines = content.split('\n')
                            matches = [f"Line {i+1}: {line.strip()}" 
                                     for i, line in enumerate(lines) 
                                     if pattern.lower() in line.lower()]
                            
                            results.append(f"\n📄 {file_path}:")
                            results.extend(matches[:3])  # 最大3行
                    except:
                        continue
            
            if not results:
                return f"No matches found for '{pattern}'"
            
            return "Search results:" + "\n".join(results[:20])  # 最大20結果
        except Exception as e:
            return f"Error searching files: {e}"
    
    async def git_status(self, params: str) -> str:
        """Git状態を確認"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'], 
                capture_output=True, 
                text=True, 
                cwd=self.root_path
            )
            
            if result.returncode != 0:
                return "Not a git repository or git not available"
            
            status = result.stdout.strip()
            if not status:
                return "Working directory clean"
            
            return f"Git status:\n{status}"
        except Exception as e:
            return f"Error checking git status: {e}"
    
    async def git_commit(self, params: str) -> str:
        """Gitコミットを作成"""
        message = params.strip()
        if not message:
            return "Error: Commit message required"
        
        if self.safe_mode:
            if not Confirm.ask(f"Commit with message: '{message}'?"):
                return "Commit cancelled by user"
        
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], cwd=self.root_path, check=True)
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', message], 
                capture_output=True, 
                text=True, 
                cwd=self.root_path
            )
            
            return f"Git commit result:\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"Error committing: {e}"
    
    async def analyze_code(self, params: str) -> str:
        """コード構造を分析"""
        path = Path(params.strip())
        
        if not self._is_safe_path(path):
            return "Error: Path is outside project directory"
        
        try:
            if path.is_file():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = len(content.split('\n'))
                functions = len(re.findall(r'def\s+\w+\(', content))  # Python例
                classes = len(re.findall(r'class\s+\w+', content))
                
                return f"Code analysis for {path}:\n- Lines: {lines}\n- Functions: {functions}\n- Classes: {classes}"
            else:
                return "Path is not a file"
        except Exception as e:
            return f"Error analyzing code: {e}"
    
    async def run_program(self, params: str) -> str:
        """プログラムを実行し、エラー分析を行う"""
        parts = params.strip().split(' ', 1)
        file_path = Path(parts[0])
        args = parts[1] if len(parts) > 1 else ""
        
        if not self._is_safe_path(file_path):
            return "Error: Path is outside project directory"
        
        if not file_path.exists():
            return f"Error: File {file_path} does not exist"
        
        # ファイル拡張子から実行方法を決定
        extension = file_path.suffix.lower()
        
        # OS別のPythonコマンドを決定
        import platform
        if platform.system() == "Windows":
            python_cmd = "python"
        else:
            python_cmd = "python3"
        
        execution_commands = {
            '.py': f'{python_cmd} "{file_path}" {args}',
            '.js': f'node "{file_path}" {args}',
            '.ts': f'ts-node "{file_path}" {args}',
            '.java': f'java "{file_path.stem}" {args}',  # 簡略化
            '.cpp': f'g++ "{file_path}" -o temp_executable && ./temp_executable {args}',
            '.c': f'gcc "{file_path}" -o temp_executable && ./temp_executable {args}',
            '.go': f'go run "{file_path}" {args}',
            '.rs': f'rustc "{file_path}" && ./"{file_path.stem}" {args}',
            '.sh': f'bash "{file_path}" {args}',
        }
        
        if extension not in execution_commands:
            return f"Error: Unsupported file type {extension}. Supported: {', '.join(execution_commands.keys())}"
        
        command = execution_commands[extension]
        
        if self.safe_mode:
            if not Confirm.ask(f"Execute program: {file_path} with command '{command}'?"):
                return "Program execution cancelled by user"
        
        console.print(f"🚀 [green]Executing program:[/green] {file_path}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.root_path,
                timeout=60  # プログラム実行は長めのタイムアウト
            )
            
            # 結果の分析
            analysis = self._analyze_execution_result(result, file_path, command)
            
            return analysis
            
        except subprocess.TimeoutExpired:
            return "Error: Program execution timed out (60 seconds)"
        except Exception as e:
            return f"Error executing program: {e}"
    
    def _analyze_execution_result(self, result: subprocess.CompletedProcess, file_path: Path, command: str) -> str:
        """実行結果を分析"""
        output_lines = []
        
        # 基本情報
        output_lines.append(f"Program: {file_path}")
        output_lines.append(f"Command: {command}")
        output_lines.append(f"Exit code: {result.returncode}")
        
        # 実行時間は subprocess では取得できないので省略
        
        # 標準出力
        if result.stdout:
            output_lines.append(f"\n📤 Standard Output:")
            stdout_preview = result.stdout[:1500] + ("..." if len(result.stdout) > 1500 else "")
            output_lines.append(stdout_preview)
        
        # エラー出力の分析
        if result.stderr:
            output_lines.append(f"\n❌ Standard Error:")
            stderr_preview = result.stderr[:1500] + ("..." if len(result.stderr) > 1500 else "")
            output_lines.append(stderr_preview)
            
            # エラー分析
            error_analysis = self._analyze_error_patterns(result.stderr, file_path.suffix)
            if error_analysis:
                output_lines.append(f"\n🔍 Error Analysis:")
                output_lines.append(error_analysis)
        
        # 成功/失敗の判定
        if result.returncode == 0:
            if result.stderr:
                status = "⚠️ Completed with warnings"
            else:
                status = "✅ Completed successfully"
        else:
            status = f"❌ Failed (exit code: {result.returncode})"
        
        output_lines.append(f"\n🎯 Status: {status}")
        
        return "\n".join(output_lines)
    
    def _analyze_error_patterns(self, stderr: str, file_extension: str) -> str:
        """エラーパターンを分析して改善提案を生成"""
        analysis = []
        
        # Python エラーパターン
        if file_extension == '.py':
            if 'ModuleNotFoundError' in stderr:
                module_match = re.search(r"No module named '([^']+)'", stderr)
                if module_match:
                    module = module_match.group(1)
                    analysis.append(f"Missing module '{module}'. Try: pip install {module}")
            
            if 'SyntaxError' in stderr:
                analysis.append("Syntax error detected. Check for missing colons, parentheses, or indentation issues.")
            
            if 'IndentationError' in stderr:
                analysis.append("Indentation error. Check that all indentation uses consistent spaces or tabs.")
            
            if 'NameError' in stderr:
                var_match = re.search(r"name '([^']+)' is not defined", stderr)
                if var_match:
                    var = var_match.group(1)
                    analysis.append(f"Variable '{var}' is not defined. Check spelling or import statements.")
            
            if 'TypeError' in stderr:
                analysis.append("Type error detected. Check argument types and function signatures.")
            
            if 'FileNotFoundError' in stderr:
                analysis.append("File not found. Check file path and ensure file exists.")
        
        # JavaScript/Node.js エラーパターン
        elif file_extension in ['.js', '.ts']:
            if 'Cannot find module' in stderr:
                analysis.append("Missing Node.js module. Try: npm install <module-name>")
            
            if 'SyntaxError' in stderr:
                analysis.append("JavaScript syntax error. Check for missing semicolons or brackets.")
            
            if 'ReferenceError' in stderr:
                analysis.append("Reference error. Check variable names and scope.")
            
            if 'TypeError' in stderr:
                analysis.append("Type error. Check function calls and object properties.")
        
        # C/C++ エラーパターン
        elif file_extension in ['.c', '.cpp']:
            if 'error:' in stderr.lower():
                analysis.append("Compilation error detected. Check syntax and includes.")
            
            if 'undefined reference' in stderr:
                analysis.append("Linking error. Check function declarations and library links.")
            
            if 'fatal error' in stderr and 'No such file' in stderr:
                analysis.append("Header file not found. Check include paths and file names.")
        
        # Java エラーパターン
        elif file_extension == '.java':
            if 'error:' in stderr:
                analysis.append("Compilation error. Check syntax and imports.")
            
            if 'ClassNotFoundException' in stderr:
                analysis.append("Class not found. Check classpath and class names.")
            
            if 'NoSuchMethodError' in stderr:
                analysis.append("Method not found. Check method signatures and object types.")
        
        # 一般的なエラーパターン
        if 'Permission denied' in stderr:
            analysis.append("Permission denied. Check file permissions or run with appropriate privileges.")
        
        if 'command not found' in stderr or 'is not recognized' in stderr:
            analysis.append("Command not found. Check if the required interpreter/compiler is installed.")
        
        return "\n".join(f"• {item}" for item in analysis) if analysis else "No specific error patterns recognized."
    
    async def debug_error(self, params: str) -> str:
        """エラーをデバッグして修正提案を生成"""
        parts = params.split(' ', 1)
        if len(parts) < 2:
            return "Error: Usage: debug_error <error_info> <file_path>"
        
        error_info = parts[0]
        file_path = Path(parts[1])
        
        if not self._is_safe_path(file_path):
            return "Error: Path is outside project directory"
        
        if not file_path.exists():
            return f"Error: File {file_path} does not exist"
        
        try:
            # ファイルの内容を読み取り
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # エラー情報の分析
            debug_analysis = []
            debug_analysis.append(f"🐛 Debugging: {file_path}")
            debug_analysis.append(f"Error: {error_info}")
            
            # ファイル拡張子に基づく分析
            extension = file_path.suffix.lower()
            
            # 基本的な構文チェック
            if extension == '.py':
                debug_analysis.extend(self._debug_python_file(content, error_info))
            elif extension in ['.js', '.ts']:
                debug_analysis.extend(self._debug_javascript_file(content, error_info))
            elif extension in ['.c', '.cpp']:
                debug_analysis.extend(self._debug_c_file(content, error_info))
            else:
                debug_analysis.append("Generic debugging suggestions:")
                debug_analysis.append("• Check syntax and formatting")
                debug_analysis.append("• Verify variable names and function calls")
                debug_analysis.append("• Check file dependencies and imports")
            
            # 修正提案
            debug_analysis.append("\n🔧 Suggested Actions:")
            debug_analysis.append("1. Review the error message details above")
            debug_analysis.append("2. Check the specific line mentioned in the error")
            debug_analysis.append("3. Verify all dependencies are installed")
            debug_analysis.append("4. Run a syntax checker for your language")
            
            return "\n".join(debug_analysis)
            
        except Exception as e:
            return f"Error during debugging: {e}"
    
    def _debug_python_file(self, content: str, error_info: str) -> list:
        """Python ファイルの特化デバッグ"""
        suggestions = []
        lines = content.split('\n')
        
        # インポート文のチェック
        imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
        if imports:
            suggestions.append(f"📦 Found {len(imports)} import statements")
            if 'ModuleNotFoundError' in error_info:
                suggestions.append("• Some modules may not be installed. Check requirements.txt")
        
        # 関数定義のチェック
        functions = [line.strip() for line in lines if line.strip().startswith('def ')]
        if functions:
            suggestions.append(f"🔧 Found {len(functions)} function definitions")
        
        # インデントのチェック
        indent_issues = []
        for i, line in enumerate(lines):
            if line.strip() and (line.startswith(' ') and line.startswith('\t')):
                indent_issues.append(i + 1)
        
        if indent_issues:
            suggestions.append(f"⚠️ Mixed spaces/tabs detected on lines: {indent_issues[:5]}")
        
        return suggestions
    
    def _debug_javascript_file(self, content: str, error_info: str) -> list:
        """JavaScript ファイルの特化デバッグ"""
        suggestions = []
        lines = content.split('\n')
        
        # require/import 文のチェック
        imports = [line.strip() for line in lines if 'require(' in line or line.strip().startswith('import ')]
        if imports:
            suggestions.append(f"📦 Found {len(imports)} import/require statements")
        
        # 関数定義のチェック
        functions = [line.strip() for line in lines if 'function ' in line or '=>' in line]
        if functions:
            suggestions.append(f"🔧 Found {len(functions)} function definitions")
        
        # セミコロンのチェック
        missing_semicolons = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.endswith((';', '{', '}', ')', ',')) and not line.startswith(('if', 'for', 'while', 'function')):
                missing_semicolons.append(i + 1)
        
        if missing_semicolons:
            suggestions.append(f"⚠️ Possible missing semicolons on lines: {missing_semicolons[:3]}")
        
        return suggestions
    
    async def read_files(self, params: str) -> str:
        """複数ファイルを一括読み込み"""
        file_paths = params.strip().split()
        if not file_paths:
            return "Error: Usage: read_files <file1> <file2> ..."
        
        results = []
        total_size = 0
        max_total_size = 50000  # 最大50KB
        
        for file_path_str in file_paths:
            file_path = Path(file_path_str.strip())
            
            if not self._is_safe_path(file_path):
                results.append(f"❌ {file_path}: Path is outside project directory")
                continue
            
            if not file_path.exists():
                results.append(f"❌ {file_path}: File not found")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # サイズ制限チェック
                if total_size + len(content) > max_total_size:
                    results.append(f"⚠️ Size limit reached. Remaining files skipped.")
                    break
                
                total_size += len(content)
                
                # 長すぎる場合は省略
                if len(content) > 3000:
                    content = content[:3000] + "...\n[File truncated]"
                
                results.append(f"📄 **{file_path}**:\n```\n{content}\n```\n")
                
            except Exception as e:
                results.append(f"❌ {file_path}: Error reading file: {e}")
        
        return f"Read {len([r for r in results if r.startswith('📄')])} files:\n\n" + "\n".join(results)
    
    async def read_folder(self, params: str) -> str:
        """フォルダ内のファイルを一括読み込み"""
        parts = params.strip().split()
        if not parts:
            return "Error: Usage: read_folder <directory> [extension]"
        
        directory = Path(parts[0])
        extension = parts[1] if len(parts) > 1 else None
        
        if not self._is_safe_path(directory):
            return "Error: Path is outside project directory"
        
        if not directory.exists() or not directory.is_dir():
            return f"Error: Directory {directory} not found"
        
        try:
            files = []
            total_size = 0
            max_total_size = 50000  # 最大50KB
            max_files = 20  # 最大20ファイル
            
            # ファイル収集
            pattern = f"*.{extension}" if extension else "*"
            for file_path in sorted(directory.rglob(pattern)):
                if file_path.is_file() and len(files) < max_files:
                    # 無視すべきファイルをスキップ
                    if self._should_ignore_file(file_path):
                        continue
                    
                    files.append(file_path)
            
            if not files:
                return f"No files found in {directory}" + (f" with extension .{extension}" if extension else "")
            
            results = [f"📁 Reading {len(files)} files from {directory}:\n"]
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # サイズ制限チェック
                    if total_size + len(content) > max_total_size:
                        results.append(f"⚠️ Size limit reached. Remaining files skipped.")
                        break
                    
                    total_size += len(content)
                    
                    # 長すぎる場合は省略
                    if len(content) > 2000:
                        content = content[:2000] + "...\n[File truncated]"
                    
                    relative_path = file_path.relative_to(self.root_path)
                    results.append(f"📄 **{relative_path}**:\n```\n{content}\n```\n")
                    
                except Exception as e:
                    results.append(f"❌ {file_path.name}: Error reading file: {e}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"Error reading folder: {e}"
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """ファイルを無視すべきかチェック"""
        ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.DS_Store'
        }
        
        ignore_extensions = {
            '.pyc', '.log', '.tmp', '.cache', '.lock', '.pid'
        }
        
        # パスに無視パターンが含まれているかチェック
        path_str = str(file_path)
        if any(pattern in path_str for pattern in ignore_patterns):
            return True
        
        # 拡張子をチェック
        if file_path.suffix.lower() in ignore_extensions:
            return True
        
        # バイナリファイルのチェック（簡易）
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.img', '.iso',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.mp3', '.wav', '.mp4', '.avi', '.mov', '.pdf', '.zip'
        }
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        return False
    
    def _debug_c_file(self, content: str, error_info: str) -> list:
        """C/C++ ファイルの特化デバッグ"""
        suggestions = []
        lines = content.split('\n')
        
        # インクルード文のチェック
        includes = [line.strip() for line in lines if line.strip().startswith('#include')]
        if includes:
            suggestions.append(f"📦 Found {len(includes)} include statements")
        
        # main関数のチェック
        has_main = any('main(' in line for line in lines)
        if not has_main:
            suggestions.append("⚠️ No main() function found")
        
        # セミコロンのチェック
        for i, line in enumerate(lines):
            line = line.strip()
            if line and line.endswith('(') and not line.startswith('#'):
                suggestions.append(f"⚠️ Possible syntax issue on line {i + 1}")
                break
        
        return suggestions
    
    async def remove_file(self, params: str) -> str:
        """ファイルを削除（必ず確認を取る）"""
        file_path = self._normalize_path(params.strip())
        
        if not self._is_safe_path(file_path):
            return "Error: Path is outside project directory"
        
        if not file_path.exists():
            return f"Error: File {file_path} does not exist"
        
        if not file_path.is_file():
            return f"Error: {file_path} is not a file. Use remove_directory for directories"
        
        # 必ず確認を取る（safe_modeに関係なく）
        console.print(f"🚨 [bold red]DELETION REQUEST[/bold red]")
        console.print(f"File to delete: {file_path}")
        console.print(f"Size: {file_path.stat().st_size} bytes")
        
        if not Confirm.ask(f"❗ Are you absolutely sure you want to DELETE the file '{file_path}'? This action cannot be undone!"):
            return "❌ File deletion cancelled by user"
        
        # 二重確認
        if not Confirm.ask(f"🔥 FINAL CONFIRMATION: Delete '{file_path.name}'? Type 'yes' to confirm"):
            return "❌ File deletion cancelled at final confirmation"
        
        try:
            # バックアップを作成
            backup_path = file_path.with_suffix(file_path.suffix + '.deleted_backup')
            import shutil
            shutil.copy2(file_path, backup_path)
            
            # 削除実行
            file_path.unlink()
            
            return f"✅ File {file_path} deleted successfully. Backup saved as {backup_path}"
        except Exception as e:
            return f"❌ Error deleting file: {e}"
    
    async def remove_directory(self, params: str) -> str:
        """ディレクトリを削除（必ず確認を取る）"""
        dir_path = self._normalize_path(params.strip())
        
        if not self._is_safe_path(dir_path):
            return "Error: Path is outside project directory"
        
        if not dir_path.exists():
            return f"Error: Directory {dir_path} does not exist"
        
        if not dir_path.is_dir():
            return f"Error: {dir_path} is not a directory. Use remove_file for files"
        
        # ディレクトリ内容を確認
        try:
            contents = list(dir_path.iterdir())
            file_count = len([f for f in contents if f.is_file()])
            dir_count = len([f for f in contents if f.is_dir()])
        except Exception:
            contents = []
            file_count = 0
            dir_count = 0
        
        # 必ず確認を取る（safe_modeに関係なく）
        console.print(f"🚨 [bold red]DIRECTORY DELETION REQUEST[/bold red]")
        console.print(f"Directory to delete: {dir_path}")
        console.print(f"Contents: {file_count} files, {dir_count} subdirectories")
        
        if contents:
            console.print("Contents preview:")
            for i, item in enumerate(contents[:10]):
                icon = "📁" if item.is_dir() else "📄"
                console.print(f"  {icon} {item.name}")
            if len(contents) > 10:
                console.print(f"  ... and {len(contents) - 10} more items")
        
        if not Confirm.ask(f"❗ Are you absolutely sure you want to DELETE the directory '{dir_path}' and ALL its contents? This action cannot be undone!"):
            return "❌ Directory deletion cancelled by user"
        
        # 二重確認
        if not Confirm.ask(f"🔥 FINAL CONFIRMATION: Delete '{dir_path.name}' and all {len(contents)} items inside? Type 'yes' to confirm"):
            return "❌ Directory deletion cancelled at final confirmation"
        
        try:
            # バックアップを作成（空でない場合）
            if contents:
                import shutil
                backup_path = dir_path.parent / f"{dir_path.name}.deleted_backup"
                shutil.copytree(dir_path, backup_path)
                backup_msg = f" Backup saved as {backup_path}"
            else:
                backup_msg = ""
            
            # 削除実行
            import shutil
            shutil.rmtree(dir_path)
            
            return f"✅ Directory {dir_path} deleted successfully.{backup_msg}"
        except Exception as e:
            return f"❌ Error deleting directory: {e}"
    
    async def analyze_improvements(self, params: str) -> str:
        """ファイルを解析して改善提案を生成"""
        file_path = self._normalize_path(params.strip())
        
        if not self._is_safe_path(file_path):
            return "Error: Path is outside project directory"
        
        if not file_path.exists():
            return f"Error: File {file_path} does not exist"
        
        if not file_path.is_file():
            return f"Error: {file_path} is not a file"
        
        if not self.code_analyzer.can_analyze(file_path):
            return f"Info: File type {file_path.suffix} is not supported for analysis"
        
        try:
            # ファイルを解析
            result = self.code_analyzer.analyze_file(file_path)
            
            if 'error' in result:
                return f"Analysis Error: {result['error']}"
            
            improvements = result.get('improvements', [])
            metrics = result.get('metrics')
            
            # 結果をフォーマット
            output = [f"📊 Analysis Results for {file_path.name}"]
            
            if metrics:
                output.append(f"\n📈 Metrics:")
                output.append(f"  • Lines of Code: {metrics.lines_of_code}")
                output.append(f"  • Functions: {metrics.function_count}")
                output.append(f"  • Classes: {metrics.class_count}")
                output.append(f"  • Complexity Score: {metrics.complexity_score:.1f}/10")
                output.append(f"  • Max Function Length: {metrics.max_function_length} lines")
            
            if improvements:
                summary = self.code_analyzer.get_improvement_summary(improvements)
                output.append(f"\n🔍 Issues Found: {summary}")
                output.append("\n💡 Suggestions:")
                
                for imp in improvements[:5]:  # 最大5件表示
                    icon = {'error': '❌', 'warning': '⚠️', 'info': '💡'}[imp.severity]
                    output.append(f"  {icon} Line {imp.line}: {imp.message}")
                    output.append(f"     → {imp.suggestion}")
                
                if len(improvements) > 5:
                    output.append(f"     ... and {len(improvements) - 5} more issues")
            else:
                output.append("\n✅ No issues found. Code looks good!")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error during analysis: {e}"
    
    async def check_code_quality(self, params: str) -> str:
        """コード品質メトリクスをチェック"""
        file_path = self._normalize_path(params.strip())
        
        if not self._is_safe_path(file_path):
            return "Error: Path is outside project directory"
        
        if not file_path.exists():
            return f"Error: File {file_path} does not exist"
        
        if not file_path.is_file():
            return f"Error: {file_path} is not a file"
        
        if not self.code_analyzer.can_analyze(file_path):
            return f"Info: File type {file_path.suffix} is not supported for quality analysis"
        
        try:
            result = self.code_analyzer.analyze_file(file_path)
            
            if 'error' in result:
                return f"Quality Check Error: {result['error']}"
            
            metrics = result.get('metrics')
            improvements = result.get('improvements', [])
            
            if not metrics:
                return "No metrics available for this file"
            
            # 品質評価
            quality_score = 10.0 - metrics.complexity_score
            
            # 品質グレード
            if quality_score >= 8:
                grade = "A (Excellent)"
                grade_icon = "🟢"
            elif quality_score >= 6:
                grade = "B (Good)"
                grade_icon = "🟡"
            elif quality_score >= 4:
                grade = "C (Fair)"
                grade_icon = "🟠"
            else:
                grade = "D (Needs Improvement)"
                grade_icon = "🔴"
            
            output = [f"🎯 Code Quality Report for {file_path.name}"]
            output.append(f"\n{grade_icon} Overall Grade: {grade}")
            output.append(f"📊 Quality Score: {quality_score:.1f}/10")
            
            output.append(f"\n📋 Detailed Metrics:")
            output.append(f"  • Lines of Code: {metrics.lines_of_code}")
            output.append(f"  • Function Count: {metrics.function_count}")
            output.append(f"  • Class Count: {metrics.class_count}")
            output.append(f"  • Longest Function: {metrics.max_function_length} lines")
            
            # 問題数の要約
            error_count = len([i for i in improvements if i.severity == 'error'])
            warning_count = len([i for i in improvements if i.severity == 'warning'])
            info_count = len([i for i in improvements if i.severity == 'info'])
            
            output.append(f"\n🔍 Issues Summary:")
            output.append(f"  • Errors: {error_count}")
            output.append(f"  • Warnings: {warning_count}")  
            output.append(f"  • Info: {info_count}")
            
            # 推奨アクション
            output.append(f"\n💡 Recommendations:")
            if error_count > 0:
                output.append("  • Fix syntax errors first")
            if warning_count > 0:
                output.append("  • Address warnings to improve maintainability")
            if metrics.max_function_length > 50:
                output.append("  • Consider breaking down long functions")
            if metrics.complexity_score > 7:
                output.append("  • Simplify complex code structures")
            
            if error_count == 0 and warning_count == 0 and metrics.complexity_score < 5:
                output.append("  • Code quality is good! Keep up the good work.")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error during quality check: {e}"
"""設定管理システム"""

import os
import platform
import tomllib
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class OSConfig:
    """OS固有設定"""
    os_type: str = "auto"  # "auto", "windows", "linux", "mac"
    list_command: str = "auto"  # "auto", "dir", "ls"
    shell_type: str = "auto"  # "auto", "cmd", "powershell", "bash", "zsh"
    path_separator: str = "auto"  # "auto", "/", "\\"
    
    def __post_init__(self):
        """初期化後の自動設定"""
        if self.os_type == "auto":
            self.os_type = self._detect_os()
        
        if self.list_command == "auto":
            self.list_command = "dir" if self.os_type == "windows" else "ls"
        
        if self.shell_type == "auto":
            self.shell_type = self._detect_shell()
        
        if self.path_separator == "auto":
            self.path_separator = "\\" if self.os_type == "windows" else "/"
    
    def _detect_os(self) -> str:
        """OS自動検出"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "mac"
        elif system == "linux":
            return "linux"
        else:
            return "linux"  # デフォルト
    
    def _detect_shell(self) -> str:
        """シェル自動検出"""
        if self.os_type == "windows":
            # PowerShellが利用可能かチェック
            try:
                import subprocess
                subprocess.run(["powershell", "-Command", "echo test"], 
                             capture_output=True, timeout=2)
                return "powershell"
            except:
                return "cmd"
        else:
            # Unix系はbashをデフォルト
            return "bash"
    
    def get_commands(self) -> Dict[str, str]:
        """OS別コマンドマッピング"""
        if self.os_type == "windows":
            return {
                "list_files": "dir",
                "copy": "copy",
                "move": "move",
                "remove": "del",
                "clear": "cls",
                "cat": "type",
                "which": "where"
            }
        else:
            return {
                "list_files": "ls",
                "copy": "cp",
                "move": "mv", 
                "remove": "rm",
                "clear": "clear",
                "cat": "cat",
                "which": "which"
            }

@dataclass
class ContextConfig:
    """コンテキスト管理設定"""
    max_tokens: int = 16384
    compression_threshold: float = 0.8
    auto_compression: bool = True
    warning_threshold: float = 0.9
    preserve_ratio: float = 0.3

@dataclass
class GeneralConfig:
    """基本設定"""
    language: str = "ja"
    dry_run: bool = False
    safe_mode: bool = True
    verbose: bool = False

@dataclass
class LMStudioConfig:
    """LM Studio設定"""
    host: str = "localhost"
    port: int = 1234
    api_key: str = ""
    model_name: str = "gemma-3n-e4b-it-text"
    timeout: int = 60

@dataclass
class MemoryConfig:
    """メモリ設定"""
    max_records: int = 1000
    cleanup_days: int = 30
    auto_save: bool = True

@dataclass
class ToolsConfig:
    """ツール設定"""
    max_file_size: int = 1048576  # 1MB
    safe_paths_only: bool = True
    backup_on_edit: bool = True

@dataclass
class Config:
    """全体設定"""
    os: OSConfig = field(default_factory=OSConfig)
    general: GeneralConfig = field(default_factory=GeneralConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    lm_studio: LMStudioConfig = field(default_factory=LMStudioConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    
    # その他の設定も必要に応じて追加可能
    azure: Dict[str, Any] = field(default_factory=dict)
    gemini: Dict[str, Any] = field(default_factory=dict)
    experimental: Dict[str, bool] = field(default_factory=dict)

class ConfigManager:
    """設定管理システム"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.cwd() / "config.toml"
        self.config = Config()
        self._load_config()
    
    def _load_config(self):
        """設定ファイルを読み込み"""
        if not self.config_path.exists():
            # デフォルト設定を使用
            return
        
        try:
            with open(self.config_path, 'rb') as f:
                data = tomllib.load(f)
            
            # 各セクションを読み込み
            if 'os' in data:
                self.config.os = OSConfig(**data['os'])
            
            if 'general' in data:
                self.config.general = GeneralConfig(**data['general'])
            
            if 'context' in data:
                self.config.context = ContextConfig(**data['context'])
            
            if 'lm_studio' in data:
                self.config.lm_studio = LMStudioConfig(**data['lm_studio'])
            
            if 'memory' in data:
                self.config.memory = MemoryConfig(**data['memory'])
            
            if 'tools' in data:
                self.config.tools = ToolsConfig(**data['tools'])
            
            # その他のセクション
            self.config.azure = data.get('azure', {})
            self.config.gemini = data.get('gemini', {})
            self.config.experimental = data.get('experimental', {})
            
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            print("デフォルト設定を使用します")
    
    def get_context_config(self) -> ContextConfig:
        """コンテキスト設定を取得"""
        return self.config.context
    
    def get_max_tokens(self) -> int:
        """最大トークン数を取得"""
        return self.config.context.max_tokens
    
    def should_compress(self, current_tokens: int) -> bool:
        """コンテキスト圧縮が必要かチェック"""
        if not self.config.context.auto_compression:
            return False
        
        threshold = self.config.context.max_tokens * self.config.context.compression_threshold
        return current_tokens >= threshold
    
    def should_warn(self, current_tokens: int) -> bool:
        """警告表示が必要かチェック"""
        threshold = self.config.context.max_tokens * self.config.context.warning_threshold
        return current_tokens >= threshold
    
    def get_usage_ratio(self, current_tokens: int) -> float:
        """コンテキスト使用率を取得"""
        return current_tokens / self.config.context.max_tokens
    
    def get_preserve_tokens(self) -> int:
        """圧縮時に保持するトークン数を取得"""
        return int(self.config.context.max_tokens * self.config.context.preserve_ratio)
    
    def update_max_tokens(self, new_max: int):
        """最大トークン数を動的に更新"""
        self.config.context.max_tokens = new_max
    
    def save_config(self):
        """設定ファイルに保存（将来的な機能）"""
        # TOMLファイルの書き込みは複雑なので、必要に応じて実装
        pass
    
    def get_model_recommended_tokens(self, model_name: str) -> int:
        """モデル別推奨トークン数を取得"""
        recommendations = {
            "gemma-3n-e4b-it-text": 16384,
            "llama-3-8b": 8192,
            "codellama-34b": 16384,
            "gpt-3.5-turbo": 4096,
            "gpt-4": 8192,
        }
        
        # 部分マッチで検索
        model_lower = model_name.lower()
        for pattern, tokens in recommendations.items():
            if pattern in model_lower:
                return tokens
        
        # デフォルト
        return 8192
    
    def auto_adjust_for_model(self, model_name: str):
        """モデルに応じてコンテキスト設定を自動調整"""
        recommended = self.get_model_recommended_tokens(model_name)
        if recommended != self.config.context.max_tokens:
            print(f"モデル {model_name} に対してコンテキスト長を {recommended} に調整しました")
            self.config.context.max_tokens = recommended
    
    def get_os_config(self) -> OSConfig:
        """OS設定を取得"""
        return self.config.os
    
    def get_os_commands(self) -> Dict[str, str]:
        """OS別コマンドマッピングを取得"""
        return self.config.os.get_commands()
    
    def get_list_command(self) -> str:
        """ファイル一覧表示コマンドを取得"""
        return self.config.os.list_command
    
    def get_shell_type(self) -> str:
        """シェルタイプを取得"""
        return self.config.os.shell_type
    
    def get_path_separator(self) -> str:
        """パス区切り文字を取得"""
        return self.config.os.path_separator
    
    def is_windows(self) -> bool:
        """Windowsかどうかを判定"""
        return self.config.os.os_type == "windows"
    
    def is_unix_like(self) -> bool:
        """Unix系（Linux/Mac）かどうかを判定"""
        return self.config.os.os_type in ["linux", "mac"]

# グローバル設定管理インスタンス
_config_manager = None

def get_config_manager() -> ConfigManager:
    """グローバル設定管理インスタンスを取得"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_context_config() -> ContextConfig:
    """コンテキスト設定を取得"""
    return get_config_manager().get_context_config()

def get_os_config() -> OSConfig:
    """OS設定を取得"""
    return get_config_manager().get_os_config()
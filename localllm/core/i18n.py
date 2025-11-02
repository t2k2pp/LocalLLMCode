"""国際化（i18n）システム - 日本語対応"""

import os
from typing import Dict, Optional
from pathlib import Path

class I18n:
    """シンプルな国際化システム"""
    
    def __init__(self, locale: str = "ja"):
        self.locale = locale
        self.messages: Dict[str, str] = {}
        self._load_messages()
    
    def _load_messages(self):
        """メッセージファイルを読み込み"""
        if self.locale == "ja":
            self.messages = JAPANESE_MESSAGES
        else:
            self.messages = ENGLISH_MESSAGES  # デフォルトは英語
    
    def t(self, key: str, **kwargs) -> str:
        """翻訳関数（translate の略）"""
        message = self.messages.get(key, key)  # キーが見つからない場合はキー自体を返す
        
        # プレースホルダーの置換
        if kwargs:
            try:
                return message.format(**kwargs)
            except (KeyError, ValueError):
                return message
        
        return message
    
    def set_locale(self, locale: str):
        """ロケールを変更"""
        self.locale = locale
        self._load_messages()

# 日本語メッセージ辞書
JAPANESE_MESSAGES = {
    # システム起動・初期化
    "startup_banner": "🚀 LocalLLM Code - 革新的な開発エージェント",
    "initializing_analysis": "プロジェクト解析を初期化中...",
    "initialization_complete": "✅ 初期化完了！",
    "dry_run_mode": "🧪 ドライランモード: アクションがシミュレートされ、変更は行われません",
    "experimental_features": "🧪 実験的機能が有効: {features}",
    
    # インタラクティブモード
    "interactive_mode": "💬 インタラクティブモード - リクエストを入力するか、'exit' で終了",
    "type_help": "'/help' でコマンド一覧を表示",
    "you": "[bold green]あなた[/bold green]",
    "assistant": "🤖 [bold blue]アシスタント[/bold blue]",
    "goodbye": "👋 さようなら！",
    
    # エラーメッセージ
    "error": "エラー: {e}",
    "unknown_command": "不明なコマンド: {cmd}",
    "path_outside_project": "エラー: パスがプロジェクトディレクトリの外にあります",
    "file_not_found": "ファイルが見つかりません: {path}",
    "operation_cancelled": "操作がユーザーによってキャンセルされました",
    
    # ファイル操作
    "file_exists_overwrite": "ファイル {path} が存在します。上書きしますか？",
    "create_new_file": "新しいファイル {path} を作成しますか？",
    "successfully_wrote": "{path} への書き込みが完了しました",
    "error_writing_file": "ファイル書き込みエラー: {e}",
    "error_reading_file": "ファイル読み取りエラー: {e}",
    
    # エージェント関連
    "agent_thinking": "🤖 エージェントが考慮中: {query}",
    "dry_run_planning": "🧪 ドライランモード - 計画中: {query}",
    "auto_loaded_files": "📁 {count} 個の参照ファイルを自動読み込み",
    "conversational_query": "💬 会話クエリに応答中...",
    "iteration": "💭 反復 {iteration}",
    "action": "🔧 アクション:",
    "observation": "👁️ 観察:",
    "dry_run_observation": "🧪 ドライラン観察:",
    "compressing_context": "🗜️ パフォーマンス最適化のためコンテキストを圧縮中...",
    "context_compressed": "🗜️ コンテキスト圧縮: {original} → {compressed} 語 (比率: {ratio:.2f})",
    "compression_failed": "[yellow]コンテキスト圧縮に失敗: {e}。元のまま続行します。[/yellow]",
    "max_iterations": "最大反復数に達しました。タスクをさらに細分化する必要があるかもしれません。",
    "repetitive_pattern": "反復パターンに遭遇したため、効果的に進めるためのガイダンスが必要です。",
    
    # ループ検出・困った時の対応
    "loop_detected": "🔄 ループ検出: 似たようなアクションを繰り返しています",
    "repeated_failures": "❌ 繰り返し失敗が検出されました",
    "stuck_pattern": "🤔 反復パターンで行き詰まっているようです。",
    "current_situation": "📊 現在の状況: {analysis}",
    "need_guidance": "💬 効果的に進めるためのガイダンスが必要です。",
    "trying_summary": "これまでの試行:",
    
    # 選択肢
    "option_different_approach": "1. 異なるアプローチで続行",
    "option_break_down": "2. タスクを別の方法で分解",
    "option_skip": "3. このステップをスキップして前進",
    "option_stop": "4. 停止して追加指示を待つ",
    "option_three_wise": "5. 三人文殊に相談",
    "option_boss": "6. 親分に相談",
    "how_proceed": "\nどのように進めますか？",
    
    # マルチエージェント
    "multi_agent_initialized": "マルチエージェントシステムを初期化: {agents}",
    "boss_consultation_tip": "ヒント: '/boss setup' でボス相談モードを設定",
    "three_wise_consultation": "🧠 三人文殊相談 (三人文殊)",
    "boss_consultation": "🎩 ボス相談リクエスト",
    "boss_consultation_setup": "🤔 ボス相談セットアップ",
    "boss_consultation_desc": "メインエージェントが行き詰まった時、上級AIにガイダンスを求めます。",
    "enable_boss_consultation": "このセッションでボス相談を有効にしますか？",
    "boss_consultation_once": "✅ ボス相談: 一回のみ",
    "boss_consultation_repeat": "✅ ボス相談: 繰り返し可能",
    "boss_consultation_disabled": "❌ ボス相談無効",
    "boss_consultation_cancelled": "❌ ボス相談セットアップがキャンセルされました",
    "boss_consultation_requires": "[yellow]ボス相談には2つ以上のAIプロバイダー設定が必要です[/yellow]",
    "consulting_boss": "🎩 ボスエージェントに相談中: {provider}",
    "three_wise_complete": "🧠 三人文殊相談完了！",
    "boss_consultation_complete": "🎩 ボス相談完了！",
    
    # 外部記憶
    "external_memory_found": "🧠 外部記憶データ発見",
    "previous_session_data": ".localllm_memory/ に前のセッションのデータが存在します",
    "continue_existing": "1. 既存データで続行",
    "archive_fresh": "2. 古いデータをアーカイブして新規開始",
    "delete_all": "3. 全ての外部記憶データを削除",
    "how_proceed_memory": "どのように進めますか？",
    "continuing_existing": "✅ 既存データで続行",
    "data_archived": "📦 データがアーカイブされ、記憶がリフレッシュされました",
    "memory_deleted": "🗑️ 全ての外部記憶データが削除されました",
    "memory_status": "🧠 外部記憶: {summary}",
    "memory_search_found": "🔍 {count} 件のレコードが見つかりました:",
    "memory_search_none": "❌ '{query}' に該当するレコードが見つかりません",
    "memory_cleaned": "✅ 外部記憶がクリーンアップされました",
    
    # セッション管理
    "session_reset": "🔄 セッションリセット",
    "usage_memory": "使用法: /memory <status|search|cleanup>",
    "usage_memory_search": "使用法: /memory search <クエリ>",
    
    # プログラム実行
    "executing_program": "🚀 プログラム実行中:",
    "execution_timeout": "エラー: プログラム実行がタイムアウトしました (60秒)",
    "execution_error": "プログラム実行エラー: {e}",
    
    # 初期化
    "initializing_project": "🏗️ LocalLLM Codeプロジェクトを初期化中...",
    "config_exists_overwrite": "設定ファイルが既に存在します。上書きしますか？",
    "initialization_cancelled": "⚠️ 初期化がキャンセルされました",
    "config_created": "✅ 設定ファイルを作成: {path}",
    "project_initialized": "🎉 LocalLLM Codeプロジェクトが正常に初期化されました！",
    "next_steps": "次のステップ:",
    "step_configure": "1. config.toml を編集してLLM設定を追加",
    "step_run": "2. 'python main.py' を実行して開始",
    "step_help": "3. '/help' でコマンド一覧を確認",
    
    # ヘルプメッセージ
    "help_title": "📚 LocalLLM Code - 利用可能なコマンド",
    "help_basic": "基本コマンド:",
    "help_session": "/help       - このヘルプを表示",
    "help_status": "/status     - 現在の状態を表示",
    "help_reset": "/reset      - セッションをリセット",
    "help_exit": "/exit       - プログラムを終了",
    "help_memory_section": "記憶管理:",
    "help_memory": "/memory     - 外部記憶の状態表示",
    "help_memory_search": "/memory search <クエリ> - 記憶を検索",
    "help_memory_cleanup": "/memory cleanup - 記憶をクリーンアップ",
    "help_agents": "エージェント:",
    "help_wise": "/wise       - 三人文殊モード（複数AIで議論）",
    "help_boss": "/boss       - ボス相談モード（上級AIに相談）",
    "help_agents_list": "/agents     - 利用可能なエージェント一覧",
    "help_config": "設定:",
    "help_config_show": "/config     - 現在の設定を表示",
    "help_todo": "タスク管理:",
    "help_todo_list": "/todo       - TODOリスト表示",
    "help_usage": "使用方法: 自然言語でプログラミング作業を依頼してください",
    "help_examples": "例: 'main.pyを読んで分析して'、'新しいAPIエンドポイントを作成'",
    
    # ツール関連
    "unknown_tool": "不明なツール: {tool_name}",
    "tool_execution_error": "{tool_name} 実行エラー: {error}",
    "file_truncated": "ファイル内容 (最初の{limit}文字):\n{content}...\n[ファイルが切り詰められました]",
    "read_files_count": "{count} ファイルを読み込み:\n\n",
    "size_limit_reached": "⚠️ サイズ制限に達しました。残りのファイルはスキップされます。",
    "reading_folder": "📁 {directory} から {count} ファイルを読み込み中:\n",
    "no_files_found": "{directory} でファイルが見つかりません",
    "no_files_extension": " 拡張子 .{extension} の",
    
    # LLMクライアント関連
    "lm_studio_error": "[red]LM Studio接続エラー: {e}[/red]",
    "lm_studio_connection_trouble": "申し訳ありませんが、ローカルLLMへの接続に問題があります。LM Studioが実行されているか確認してください。",
    "azure_config_missing": "Azure API設定が不足しています。[azure]セクションでapi_key、endpoint、deployment_nameを設定してください。",
    "azure_api_error": "Azure APIエラー ({status}): {error}",
    "azure_connection_error": "[red]Azure API接続エラー: {e}[/red]",
    "azure_connection_trouble": "申し訳ありませんが、Azure ChatGPTへの接続に問題があります。設定を確認してください。",
    "gemini_config_missing": "Gemini API設定が不足しています。[gemini]セクションでapi_keyを設定してください。",
    "gemini_no_streaming": "[yellow]注意: Gemini APIはストリーミングをサポートしていません。非ストリーミングモードを使用します[/yellow]",
    
    # ファイル参照処理
    "file_reference_error": "[yellow]ファイル参照処理エラー: {e}[/yellow]",
    "file_read_error": "(読み込みエラー: {e})",
    
    # コンテキスト管理
    "context_critical": "⚠️ コンテキスト使用量が危険域です ({usage:.1f}%)",
    "context_critical_advice": "すぐにコンテキストの圧縮または分割が必要です",
    "context_warning": "⚠️ コンテキスト使用量が多くなっています ({usage:.1f}%)",
    "auto_compressing": "🗜️ 自動圧縮中 ({strategy}モード)",
    "context_optimized": "📊 {model} 用にコンテキスト長を {tokens} トークンに最適化",
}

# 英語メッセージ辞書（フォールバック用）
ENGLISH_MESSAGES = {
    # 主要なメッセージのみ英語版を保持
    "startup_banner": "🚀 LocalLLM Code - Revolutionary Development Agent",
    "initializing_analysis": "Initializing project analysis...",
    "initialization_complete": "✅ Initialization complete!",
    "interactive_mode": "💬 Interactive Mode - Type your requests or 'exit' to quit",
    "type_help": "Type '/help' for available commands",
    "goodbye": "👋 Goodbye!",
    "error": "Error: {e}",
    "unknown_command": "Unknown command: {cmd}",
    # 他の英語メッセージは必要に応じて追加
}

# グローバルインスタンス
_i18n = I18n()

def t(key: str, **kwargs) -> str:
    """グローバル翻訳関数"""
    return _i18n.t(key, **kwargs)

def set_locale(locale: str):
    """グローバルロケール設定"""
    _i18n.set_locale(locale)

def get_locale() -> str:
    """現在のロケールを取得"""
    return _i18n.locale
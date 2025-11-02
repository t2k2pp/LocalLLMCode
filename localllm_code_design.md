# LocalLLM Code 設計書

## 1. プロジェクト概要

### 1.1 目的
LocalLLM CodeはClaude CodeのクローンとしてLM StudioのローカルLLMを利用したagentic coding toolです。プライバシーを保護しながら、開発者がターミナルから自然言語でコーディングタスクを委譲できるツールを提供します。

### 1.2 主要機能
- ローカルLLMによるコード生成・編集・デバッグ
- ファイルシステム操作とGitワークフロー
- プロジェクト構造の理解とコンテキスト管理
- インタラクティブな会話型インターフェース
- 安全性を考慮した実行権限管理

### 1.3 技術スタック
- **言語**: Python 3.8+
- **LLMバックエンド**: LM Studio (OpenAI API互換)
- **CLI框架**: argparse + rich (美しいターミナル出力)
- **非同期処理**: asyncio + aiohttp
- **ファイル監視**: watchdog
- **Gitサポート**: GitPython
- **設定管理**: TOML/YAML
- **配布**: PyInstaller (単一実行ファイル生成)

## 2. アーキテクチャ設計

### 2.1 システムアーキテクチャ
```
LocalLLM Code
├── CLI Interface (rich + argparse)
├── LLM Client (aiohttp + OpenAI API互換)
├── Agent Core (ReAct Loop)
├── Tool System (ファイル操作、Git、実行等)
├── Context Manager (プロジェクト理解)
├── Safety Manager (権限管理)
└── Configuration (設定管理)

配布形式:
├── localllm.exe (PyInstaller生成の単一実行ファイル)
└── localllm.toml (設定ファイル - 外部化)
```

### 2.2 コンポーネント設計

#### 2.2.1 CLI Interface
- **責任**: ユーザーインターフェース、コマンドパージング
- **技術**: argparse + rich (プログレスバー、構文ハイライト等)
- **機能**: 
  - インタラクティブモード
  - ワンショットコマンド実行
  - カラフルな出力とプログレス表示

#### 2.2.2 LLM Client
- **責任**: LM Studioとの通信
- **技術**: aiohttp (非同期HTTP通信)
- **機能**:
  - OpenAI API互換のリクエスト処理
  - ストリーミングレスポンス対応
  - エラーハンドリングと再試行

#### 2.2.3 Agent Core
- **責任**: ReAct Loop実装、意思決定
- **技術**: asyncio (非同期処理)
- **機能**:
  - Reason (思考) → Action (行動) → Observation (観察) ループ
  - タスク分解と実行計画
  - エラー回復と代替策検討

#### 2.2.4 Tool System
- **責任**: 具体的なアクション実行
- **技術**: pathlib, subprocess, GitPython等
- **機能**:
  - ファイル読み取り・書き込み・編集
  - ディレクトリ操作と検索
  - シェルコマンド実行
  - Git操作 (add, commit, push等)

#### 2.2.5 Context Manager
- **責任**: プロジェクト理解とコンテキスト管理
- **技術**: パス解析、ファイル内容解析
- **機能**:
  - プロジェクト構造マッピング
  - 依存関係理解
  - メモリファイル (LOCALLLM.md) 生成・管理
  - コンテキストウィンドウ最適化

#### 2.2.6 Safety Manager
- **責任**: セキュリティと権限管理
- **技術**: ファイルパーミッション、サンドボックス
- **機能**:
  - 危険なコマンド検出
  - ファイル操作権限確認
  - 実行前確認プロンプト
  - ホワイトリスト/ブラックリスト管理

## 3. 機能設計

### 3.1 コアワークフロー
1. **初期化**: プロジェクト構造スキャン、設定読み込み
2. **プロンプト受信**: ユーザーからの自然言語入力
3. **意図理解**: LLMによるタスク分析と計画作成
4. **実行**: ツールを使った具体的なアクション
5. **結果確認**: 実行結果の検証とフィードバック
6. **継続**: 必要に応じて追加アクション

### 3.2 対話モード
- **会話継続**: セッション内でコンテキスト保持
- **段階的実行**: 複雑なタスクのステップバイステップ実行
- **確認システム**: 重要な操作前のユーザー確認

### 3.3 プロジェクト理解機能
- **自動スキャン**: プロジェクト構造、言語、フレームワーク検出
- **依存関係解析**: package.json, requirements.txt等の解析
- **慣習検出**: コーディングスタイル、ディレクトリ構造
- **メモリ生成**: LOCALLLM.mdファイルでの情報永続化

## 4. コマンド仕様

### 4.1 基本コマンド

#### `localllm` (メインコマンド)
インタラクティブモードを開始

#### `localllm -p "prompt"` (プリントモード)
ワンショット実行

#### `localllm --init` (初期化)
プロジェクトの初期設定

#### `localllm --config` (設定)
設定ファイルの編集

### 4.2 オプションフラグ

#### コア動作
- `--model MODEL_NAME`: 使用するLLMモデル指定
- `--server URL`: LM StudioサーバーURL (デフォルト: http://localhost:1234)
- `--context-size N`: コンテキストサイズ制限
- `--stream / --no-stream`: ストリーミング出力制御

#### セキュリティ
- `--dry-run`: 実際の操作を行わずに計画のみ表示
- `--unsafe`: 安全性チェックをスキップ（注意）
- `--sandbox PATH`: サンドボックスディレクトリ指定

#### 出力制御
- `--verbose / -v`: 詳細ログ出力
- `--quiet / -q`: 最小限の出力
- `--output-format json`: JSON形式での出力
- `--log-file FILE`: ログファイル指定

#### デバッグ
- `--debug`: デバッグモード有効化
- `--trace`: 実行トレース記録
- `--checkpoint`: セッション保存ポイント作成

### 4.3 設定サブコマンド

#### `localllm config llm` 
LLM設定の管理（プロバイダー、モデル、エンドポイント等）

#### `localllm config azure`
Azure ChatGPT設定（APIキー、エンドポイント、デプロイメント名等）

#### `localllm config gemini`
Gemini API設定（APIキー、モデル等）

#### `localllm config lmstudio`
LM Studio設定（サーバーURL、モデル等）

### 4.4 セッション内コマンド

#### `/help` (セッション内)
利用可能なコマンドとヘルプ表示

#### `/status` (セッション内)
現在の状態、ロードされたコンテキスト表示

#### `/reset` (セッション内)
セッションリセット、コンテキストクリア

#### `/save [NAME]` (セッション内)
セッション状態の保存

#### `/load [NAME]` (セッション内)
保存されたセッション状態の読み込み

#### `/exit` (セッション内)
セッション終了

## 5. 設定管理

### 5.1 設定ファイル
**localllm.toml** (プロジェクトルート)
```toml
[llm]
provider = "lmstudio"  # lmstudio, azure, gemini
model = "default"
context_size = 8192
stream = true

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
sandbox_mode = false

[project]
ignore_patterns = [".git", "node_modules", "__pycache__"]
memory_file = "LOCALLLM.md"
```

### 5.2 環境変数
- `LOCALLLM_PROVIDER`: LLMプロバイダー (lmstudio, azure, gemini)
- `LOCALLLM_SERVER_URL`: LM StudioサーバーURL
- `LOCALLLM_MODEL`: デフォルトモデル名
- `LOCALLLM_AZURE_API_KEY`: Azure ChatGPT APIキー
- `LOCALLLM_GEMINI_API_KEY`: Gemini APIキー
- `LOCALLLM_LOG_LEVEL`: ログレベル
- `LOCALLLM_CONFIG_PATH`: 設定ファイルパス

## 6. プロジェクトメモリ (LOCALLLM.md)

### 6.1 構造
```markdown
# LocalLLM Code Project Memory

## Project Overview
- Name: [プロジェクト名]
- Type: [プロジェクトタイプ]
- Language: [主要言語]
- Framework: [使用フレームワーク]

## Directory Structure
[ディレクトリ構造の自動生成]

## Dependencies
[依存関係の情報]

## Coding Guidelines
[コーディング規約・スタイル]

## Common Commands
[よく使用するコマンド]

## Notes
[その他の重要な情報]
```

## 7. ツールシステム

### 7.1 ファイル操作ツール
- `read_file(path)`: ファイル内容読み取り
- `write_file(path, content)`: ファイル書き込み
- `edit_file(path, changes)`: ファイル部分編集
- `create_file(path, content)`: 新ファイル作成
- `delete_file(path)`: ファイル削除
- `list_files(directory, pattern)`: ファイル一覧取得

### 7.2 ディレクトリ操作ツール
- `create_directory(path)`: ディレクトリ作成
- `search_files(pattern, directory)`: ファイル検索
- `get_file_info(path)`: ファイル情報取得

### 7.3 実行ツール
- `run_command(command, cwd)`: シェルコマンド実行
- `run_tests(test_command)`: テスト実行
- `run_linter(linter_command)`: リンター実行

### 7.4 Git操作ツール
- `git_status()`: Git状態確認
- `git_add(files)`: ファイルステージング
- `git_commit(message)`: コミット作成
- `git_push()`: リモートプッシュ
- `git_pull()`: リモートプル
- `git_branch(action, name)`: ブランチ操作

### 7.5 検索・解析ツール
- `search_codebase(query)`: コードベース検索
- `analyze_dependencies()`: 依存関係解析
- `detect_language()`: 言語検出
- `find_functions(file_path)`: 関数一覧取得

## 8. エラーハンドリング

### 8.1 LLM接続エラー
- 接続失敗時の再試行メカニズム
- フォールバック設定（別のモデルへの切り替え）
- オフライン状態での基本機能提供

### 8.2 ファイル操作エラー
- 権限エラーの適切な処理
- バックアップメカニズム
- ロールバック機能

### 8.3 セキュリティエラー
- 危険なコマンド検出時の警告
- 権限昇格の適切な処理
- サンドボックス外アクセスの防止

## 9. パフォーマンス最適化

### 9.1 コンテキスト管理
- 大規模プロジェクトでのコンテキストサイズ最適化
- 関連ファイルの自動選択
- 不要なファイルの除外

### 9.2 非同期処理
- LLMリクエストの非同期化
- ファイル操作の並列実行
- ユーザーインターフェースの応答性向上

### 9.3 キャッシュ機能
- プロジェクト構造のキャッシュ
- LLMレスポンスの一時保存
- 設定情報のメモリキャッシュ

## 10. セキュリティ考慮事項

### 10.1 実行権限管理
- デフォルトでの安全な実行
- 危険なコマンドの事前検出
- ユーザー確認プロンプト

### 10.2 ファイルアクセス制御
- プロジェクトディレクトリ外への書き込み制限
- システムファイルの保護
- バックアップ機能

### 10.3 データプライバシー
- ローカルLLMによるプライバシー保護
- 機密情報の自動検出と除外
- ログファイルの適切な管理

## 11. 将来の拡張性

### 11.1 プラグインシステム
- カスタムツールの追加機能
- 言語固有のプラグイン開発
- コミュニティプラグインのサポート

### 11.2 追加LLMサポート
- Azure ChatGPT対応
- Gemini API対応
- 複数LLMプロバイダーの統一インターフェース

### 11.3 配布とデプロイメント
- PyInstallerによる単一実行ファイル生成
- 設定ファイルの外部化
- クロスプラットフォーム対応 (Windows, macOS, Linux)

## 12. 開発計画

### Phase 1: コア機能
- 基本CLI構造
- LM Studio連携
- 基本的なファイル操作
- 簡単な会話機能

### Phase 2: 高度な機能
- ReActループ実装
- Git統合
- プロジェクト理解機能
- セキュリティ機能

### Phase 3: 最適化・配布
- パフォーマンス最適化
- 詳細な設定オプション
- PyInstallerによる実行ファイル生成
- 包括的なテスト

### Phase 4: LLMプロバイダー拡張
- Azure ChatGPT対応
- Gemini API対応
- 統一設定インターフェース
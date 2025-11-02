# 🚀 LocalLLM Code - Revolutionary Development Agent

> *パラダイムシフトを起こす、革新的なagentic coding tool*

LocalLLM Codeは、プライバシーを保護しながらローカルLLMを活用した次世代の開発エージェントです。Claude Codeを超える機能を持ち、あなたのプロジェクトの「DNA」を理解し、最適化されたコーディング体験を提供します。

## ✨ 革新的な機能

### 🧬 プロジェクトDNA分析
- **インテリジェント構造理解**: プロジェクトの言語、フレームワーク、アーキテクチャパターンを自動検出
- **コーディングスタイル学習**: あなたのコーディング習慣を学習し、一貫したスタイルを維持
- **依存関係マッピング**: ファイル間の関係を理解し、適切なコンテキストを提供

### 🤖 ReActエージェント
- **思考→行動→観察ループ**: 人間のような問題解決プロセス
- **自律的タスク実行**: 複雑なタスクを自動で分解・実行
- **エラー回復機能**: 失敗から学習し、代替アプローチを提案

### 🎯 スマートコンテキスト管理
- **関連度ベース選択**: クエリに最も関連するファイルを自動選択
- **動的コンテキスト最適化**: トークン制限内で最大の価値を提供
- **時系列考慮**: 最近の変更履歴を重視

### 🛡️ 高度な安全性機能
- **インテリジェント権限管理**: 危険な操作を事前検出・確認
- **自動バックアップ**: 重要な変更前に自動バックアップ作成
- **サンドボックス実行**: 安全な環境での操作実行

### 🎨 美しいターミナル体験
- **リアルタイムフィードバック**: 美しいプログレスバーと状態表示
- **構文ハイライト**: コードの可読性向上
- **直感的インターフェース**: 学習コストゼロの操作性

## 🚀 クイックスタート

### 1. インストール

```bash
# 必要な依存関係をインストール
pip install rich aiohttp

# LocalLLM Codeをダウンロード
curl -O https://raw.githubusercontent.com/your-repo/localllm.py
chmod +x localllm.py
```

### 2. LM Studioセットアップ

1. [LM Studio](https://lmstudio.ai/)をダウンロード・インストール
2. 好みのLLMモデルをダウンロード（推奨: CodeLlama, WizardCoder）
3. サーバーを起動（デフォルト: http://localhost:1234）

### 3. 初回起動

```bash
# プロジェクトディレクトリで実行
python localllm.py --init

# または直接起動（自動で初期化）
python localllm.py
```

### 4. 設定ファイル（オプション）

プロジェクトルートに `localllm.toml` を作成してカスタマイズ:

```toml
[llm]
provider = "lmstudio"
model = "codellama-7b-instruct"
stream = true

[safety]
require_confirmation = true
backup_before_edit = true
```

## 🎯 使用例

### インタラクティブモード

```bash
python localllm.py
```

```
🚀 LocalLLM Code - Revolutionary Development Agent
🧬 Analyzing Project DNA...
✅ Initialization complete!
📊 Project: Python (7.2/10 complexity)
🧬 Frameworks: FastAPI, SQLAlchemy

💬 Interactive Mode - Type your requests or 'exit' to quit

You: Create a new user authentication module with JWT support

🤖 Agent thinking about: Create a new user authentication module with JWT support

💭 Iteration 1
🔧 Action: analyze_code .
👁️ Observation: Found existing auth patterns in models/user.py...

💭 Iteration 2  
🔧 Action: create_file auth/jwt_handler.py
👁️ Observation: Successfully created auth/jwt_handler.py...

🤖 Assistant
I've successfully created a comprehensive JWT authentication module! Here's what I implemented:

1. **JWT Handler** (`auth/jwt_handler.py`): Token generation, validation, and refresh
2. **Auth Middleware** (`auth/middleware.py`): Request authentication decorator
3. **User Models** (`models/auth.py`): Extended user model with auth fields
4. **API Routes** (`api/auth.py`): Login, logout, and token refresh endpoints

The module follows your project's existing patterns and integrates seamlessly with your FastAPI structure.
```

### ワンショットモード

```bash
# 単一コマンド実行
python localllm.py -p "Fix the bug in the payment processing function"

# ドライランモード（実行せずに計画表示）
python localllm.py -p "Refactor the database connection code" --dry-run
```

### セッション内コマンド

```
You: /help                    # ヘルプ表示
You: /status                  # 現在の状態表示  
You: /reset                   # セッションリセット
You: Add error handling to the API endpoints
```

## 🛠️ 高度な機能

### プロジェクトDNAの活用

```python
# LOCALLLM.mdファイルが自動生成され、プロジェクト情報を永続化
# エージェントはこの情報を活用してより適切な提案を行う
```

### カスタムツール作成

```python
# tools/custom_tool.py
async def my_custom_tool(self, params: str) -> str:
    """カスタムツールの実装"""
    return "Custom tool result"

# 設定で登録
[commands.aliases]
deploy = "run_command docker-compose up -d"
backup = "run_command tar -czf backup.tar.gz ."
```

### 複数LLMプロバイダー対応

```toml
[llm]
provider = "azure"  # または "gemini"

[azure]
api_key = "your-azure-key"
endpoint = "https://your-resource.openai.azure.com/"
deployment_name = "gpt-4"
```

## 🔧 設定オプション

### 安全性設定

```toml
[safety]
require_confirmation = true      # 重要操作の確認
allow_dangerous_commands = false # 危険コマンドの制限
sandbox_mode = false            # サンドボックス実行
backup_before_edit = true       # 編集前自動バックアップ
```

### パフォーマンス最適化

```toml
[performance]
async_file_operations = true    # 非同期ファイル操作
cache_project_analysis = true   # 分析結果キャッシュ
max_concurrent_operations = 5   # 同時実行数制限
context_optimization = true     # コンテキスト最適化
```

### UI カスタマイズ

```toml
[ui]
theme = "dark"                  # テーマ選択
show_progress = true            # プログレス表示
syntax_highlighting = true      # 構文ハイライト
emoji_enabled = true           # 絵文字表示
```

## 🎨 実際の使用シナリオ

### 新機能開発

```
You: Create a REST API for user management with CRUD operations

🤖 I'll create a comprehensive user management API. Let me analyze your existing structure and implement it following your project's patterns...

[エージェントが自動で以下を実行]
1. 既存のAPIパターンを分析
2. データモデルの設計・実装
3. CRUD エンドポイントの作成
4. バリデーション・エラーハンドリング
5. ユニットテストの作成
6. ドキュメント更新
```

### バグ修正

```
You: There's a memory leak in the image processing function

🤖 Let me investigate the memory leak issue...

[自動実行]
1. image processing関連ファイルを検索・分析
2. メモリ使用パターンの確認
3. 潜在的な問題箇所の特定
4. 修正コードの実装
5. メモリリーク防止のテスト追加
```

### リファクタリング

```
You: Refactor the monolithic auth service into microservices

🤖 I'll help you decompose the auth service into microservices...

[段階的実行]
1. 現在のauth serviceの依存関係分析
2. マイクロサービス境界の提案
3. 各サービスの責任分離
4. API間通信の設計
5. 段階的移行計画の作成
```

## 🔍 トラブルシューティング

### LM Studio接続エラー

```bash
# LM Studioが起動しているか確認
curl http://localhost:1234/v1/models

# 別のポートを使用する場合
python localllm.py --server http://localhost:8080
```

### 権限エラー

```bash
# セーフモードを無効化（注意して使用）
python localllm.py --unsafe

# 特定のディレクトリでサンドボックス実行
python localllm.py --sandbox /path/to/safe/directory
```

### パフォーマンス問題

```toml
# 設定ファイルでコンテキストサイズを調整
[llm]
context_size = 4096  # より小さく設定

[performance]
max_concurrent_operations = 3  # 並列実行数を制限
```

## 🚀 アドバンス機能

### 実験的機能の有効化

```toml
[experimental]
predictive_coding = true      # 次の変更を予測
multi_file_sync = true        # 複数ファイル同期編集
ai_code_review = true         # AI によるコードレビュー
auto_refactoring = true       # 自動リファクタリング提案
```

### プラグインシステム（予定）

```python
# plugins/my_plugin.py
class MyPlugin:
    def register_tools(self):
        return {
            'my_tool': self.my_tool_implementation
        }
```

## 📊 メトリクス・分析

LocalLLM Codeは使用パターンを学習し、より良い提案を行います：

- **操作頻度の追跡**: よく使う操作を優先提案
- **エラーパターン学習**: 過去のエラーから学習
- **コード品質分析**: 品質向上提案
- **生産性メトリクス**: 開発効率の測定

## 🤝 コントリビューション

LocalLLM Codeをより良くするためのコントリビューションを歓迎します：

1. **バグレポート**: Issues での詳細な報告
2. **機能提案**: 新しいアイデアの共有
3. **プルリクエスト**: コード改善の提案
4. **ドキュメント**: 使用例やガイドの追加

## 📄 ライセンス

MIT License - 自由に使用・改変・配布可能

## 🙏 謝辞

- **LM Studio**: ローカルLLM実行環境
- **Rich**: 美しいターミナル出力
- **FastAPI**: 設定システムのインスピレーション
- **OpenAI**: API設計の参考

---

**LocalLLM Code** - プライバシーを保護しながら、最高の開発体験を。

🌟 Star this repository if you find it useful!
📧 Questions? Open an issue or start a discussion.
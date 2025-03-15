# Python Project Template

このリポジトリは、Pythonプロジェクトのためのテンプレートです。新しいPythonプロジェクトを開始する際の出発点として使用できます。

## 特徴

- 最新のPython開発プラクティスに基づく構造
- テスト、型チェック、リンティングなどの開発ツールを含む
- pre-commitフックによる自動コード品質チェック
- GitHub Actionsを使用したCI/CD設定
- Issueテンプレートと自動分析ツール
- 詳細なコントリビューションガイドライン

## クイックスタート

### リポジトリのクローン

```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
cd <YOUR_REPOSITORY>
```

### 環境セットアップ

```bash
# 仮想環境の作成とアクティベート
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係のインストール
pip install -e ".[dev]"

# pre-commitフックのインストール
pre-commit install
```

### 開発

1. `example_package`を自分のパッケージ名に変更
2. `pyproject.toml`を自分のプロジェクトに合わせて更新
3. 機能の開発とテストの作成

### テストの実行

```bash
# すべてのテストを実行
pytest

# カバレッジレポート付き
pytest --cov

# 特定のマーカーでテストを実行（例：ユニットテストのみ）
pytest -m unit

# 特定のマーカーを除外（例：遅いテストを除外）
pytest -m "not slow"

# コードスタイルチェック
pre-commit run --all-files
```

## プロジェクト構造

```
.
├── .github/                     # GitHub関連の設定
│   ├── ISSUE_TEMPLATE/          # Issueテンプレート
│   └── workflows/               # GitHub Actions ワークフロー
├── <YOUR_PACKAGE_NAME>/         # メインのパッケージ
│   ├── __init__.py              # パッケージの初期化
│   └── core.py                  # コア機能
├── tests/                       # テストディレクトリ
│   ├── __init__.py              # テストの初期化
│   └── test_core.py             # コア機能のテスト
├── .gitignore                   # Gitの除外ファイル設定
├── .pre-commit-config.yaml      # pre-commitの設定
├── CODE_OF_CONDUCT.md           # 行動規範
├── CONTRIBUTING.md              # コントリビューションガイド
├── LICENSE                      # ライセンスファイル
├── pyproject.toml               # Pythonプロジェクト設定
├── pytest.ini                   # pytestの設定
└── README.md                    # プロジェクトの説明
```

## カスタマイズ方法

1. 以下のプレースホルダーをプロジェクト固有の値に置き換えてください：
   - `<YOUR_PROJECT_NAME>` - プロジェクト名
   - `<YOUR_PACKAGE_NAME>` - Pythonパッケージ名
   - `<YOUR_NAME>` - 開発者名
   - `<YOUR_EMAIL>` - 連絡先メールアドレス
   - `<YOUR_USERNAME>` - GitHubユーザー名
   - `<YOUR_REPOSITORY>` - GitHubリポジトリ名
   - `<YEAR>` - 著作権年

2. `example_package`ディレクトリを自分のパッケージ名に変更
3. `pyproject.toml`の`[project]`セクションを更新
4. GitHub設定（Issue Templates、Actions workflows）を必要に応じて調整

## ライセンス

MITライセンス

# Modeling-Coding-Automation-Project Actions

## 概要

このリポジトリは、Modeling-Coding-Automation-Project (MCAP) 向けの GitHub Actions ワークフローと、それを支援するスクリプト群を提供します。

## 主な機能

### Python → C++ コード自動生成ワークフロー (`python_to_cpp.yml`)

`feature/**` ブランチへのプッシュで `source/**/*.py` が変更されると、GitHub Actions が自動的に以下を行います。

1. **C++ コード生成**: 変更された Python ファイルを解析し、AI (GitHub Copilot CLI) を使って対応する `.hpp`、`.cpp`、`_SIL.cpp` (Pybind11 Software-In-the-Loop ファイル) を生成します。
2. **差分更新モード**: 既に C++ ファイルが存在する場合は、git diff をもとに変更箇所のみを増分更新します。
3. **ブランチ管理**: `<元ブランチ名>_cpp_gen` ブランチを自動作成し、生成したコードをコミット・プッシュします。
4. **プルリクエスト作成**: 新規ブランチの場合は PR を自動作成し、トリガーしたユーザーにレビューを依頼します。

### C++ コード生成ルール (`python_to_cpp_skill.md`)

AI への指示を定義したスキルファイルです。埋め込み実装を念頭に以下の制約を適用します。

- 動的メモリアロケーション不使用
- `while` ループ不使用
- C++11 準拠のコード出力
- Pybind11 を用いた SIL 検証ファイルの生成

## ファイル構成

```
.github/
└── workflows/
    ├── python_to_cpp.yml          # GitHub Actions ワークフロー定義
    └── scripts/
        ├── python_to_cpp.py       # ワークフロー補助スクリプト（ブランチ名生成・プロンプト構築・フィルタリング）
        ├── python_to_cpp_skill.md # AI コード生成指示（スキルファイル）
        └── python_matrix_to_cpp_skill.md  # 行列変換向け追加スキルファイル
```

## 使用方法

このリポジトリのワークフローを他のリポジトリから再利用するには、`workflow_call` トリガーを使います。

```yaml
jobs:
  generate-cpp:
    uses: Modeling-Coding-Automation-Project/MCAP_actions/.github/workflows/python_to_cpp.yml@main
    with:
      ai_model: "gpt-5-mini"  # オプション: 使用する AI モデルを指定
    secrets:
      COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}
```

## 必要なシークレット

| シークレット名 | 説明 |
|---|---|
| `COPILOT_GITHUB_TOKEN` | GitHub Copilot CLI を呼び出すための認証トークン |

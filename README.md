# AI Release Note Assistant

## プロジェクト概要

本プロジェクトは、社内開発ワークフローの改善を目的としたAI支援ツールです。仕様書をインプットとして、過去のリリースノートやレビューコメントをRAG（Retrieval-Augmented Generation）で参照し、形式に沿ったリリースノートの雛形を生成します。また、人間が修正したリリースノートに対してAIがレビュー・修正提案を行うことで、リリースノート作成の**質の向上**と**レビューコストの削減**を目指します。

## 主な機能

1.  **リリースノート雛形生成:**
    *   仕様書（Markdown形式）をインプットとして受け取ります。
    *   過去の類似案件（リリースノート、レビューコメント）をRAGで参照します。
    *   「改善系」「機能系」「不具合系」のいずれかの形式に沿ったリリースノートの雛形を生成します。

2.  **AIレビュー・修正提案:**
    *   人間が修正したリリースノートをインプットとして受け取ります。
    *   過去のレビューコメントを参照し、具体的な改善点や修正提案を行います。

## 技術スタック

### ローカル開発・検証環境

*   **言語:** Python 3.x
*   **ベクトルDB:** ChromaDB (ファイルベースのSQLite)
*   **Embedding:** `sentence-transformers` (CPU利用)
*   **LLM:** Ollama (Llama 3)
*   **CLI:** `argparse`

### 本番環境 (AWS)

*   **言語:** Python 3.x
*   **ベクトルDB:** Amazon RDS for PostgreSQL + `pgvector`
*   **Embedding:** Amazon Bedrock (Titan Text Embeddings)
*   **LLM:** Amazon Bedrock (Claude 3 Sonnet)
*   **API:** Amazon API Gateway + AWS Lambda
*   **インフラ管理:** AWS CDK (予定)

## セットアップ (ローカル開発環境)

### 1. 仮想環境の作成とライブラリのインストール

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ollamaのインストールとモデルのダウンロード

Ollamaをインストールし、`llama3` モデルをダウンロードします。

```bash
# Ollamaのインストール (詳細は https://ollama.com/download を参照)
# 例: curl -fsSL https://ollama.com/install.sh | sh

ollama pull llama3
```

### 3. ダミーデータのベクトル化とDBへの格納

ローカルのChromaDBにダミーデータを投入します。

```bash
python3 db_importer.py
```

### 4. Ollamaサーバーの起動

別のターミナルでOllamaサーバーを起動したままにしておきます。

```bash
ollama serve
```

## 使い方 (ローカル開発環境)

### リリースノート雛形の生成

`sample_design.md` をインプットとして雛形を生成します。

```bash
python3 cli.py generate --file sample_design.md
```

### AIレビューの実行

`sample_release_note.md` をインプットとしてAIレビューを実行します。

```bash
python3 cli.py review --file sample_release_note.md
```

## 今後の展望 (AWSデプロイ)

ローカルでの検証が完了次第、以下のステップでAWS環境へのデプロイを進めます。

1.  **AWSリソースのCDK定義:** RDS (PostgreSQL + pgvector), Lambda, API Gateway, IAMロールなどをCDKで定義します。
2.  **Bitbucket API連携の実装:** `data_loader.py` を本物のBitbucket APIからデータを取得するように修正します。
3.  **AWS Bedrock連携の実装:** `db_importer.py` と `main_logic.py` をAWS Bedrock (Titan Embeddings, Claude 3) を利用するように修正します。
4.  **本番データ投入と検証:** 実際のデータをAWS環境に投入し、エンドツーエンドでの動作と品質を検証します。


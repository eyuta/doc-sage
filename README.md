# AIリリースノートアシスタント

## どんなツール？

このツールは、社内の開発作業をもっとスムーズにするためのAIアシスタントです。新しい機能や修正の「仕様書」を入れると、AIが過去の似たような事例を参考に、リリースノートの「たたき台」を自動で作ってくれます。さらに、あなたが作ったリリースノートをAIがチェックして、より良いものにするためのアドバイスもしてくれます。

**目的:** リリースノートを作る手間を減らし、その質を上げること。

## できること

1.  **リリースノートのたたき台を自動生成:**
    *   あなたが書いた「仕様書」（Markdown形式）をAIに渡します。
    *   AIは、過去に作ったたくさんのリリースノートや、それに対するレビューコメント（「ここを直してほしい」などのアドバイス）を参考にします。
    *   そして、「改善したこと」「新しい機能」「直した不具合」のどれに当てはまるかを選び、それに合った形式でリリースノートのたたき台を作ってくれます。

2.  **AIがリリースノートをチェックしてアドバイス:**
    *   あなたがたたき台を修正した後、AIに最終チェックをお願いできます。
    *   AIは、過去のレビューでよく指摘された点などを踏まえ、「もっとこうすると良いですよ」といった具体的なアドバイスや修正案を教えてくれます。

## このツールの仕組み（技術的な話）

このツールは、大きく分けて「ローカルで試す環境」と「実際に使うAWS上の環境」の2つで動きます。

### ローカルで試す環境（あなたのPCで動かす場合）

*   **使う言葉（プログラミング言語）:** Python 3.x
*   **過去の情報を保存する場所（データベース）:** ChromaDBという、あなたのPCのファイルの中に情報を保存するシンプルなデータベースを使います。
*   **テキストの意味を数値に変える技術（Embedding）:** `sentence-transformers`という技術を使って、文章の「意味」をAIが理解できる数値の並び（ベクトル）に変換します。これはあなたのPCのCPU（頭脳）で動きます。
*   **文章を作るAI（LLM）:** Ollamaというツールを使って、あなたのPCの中で「Llama 3」というAIモデルを動かし、文章を作らせます。
*   **操作方法:** コマンドライン（黒い画面）から指示を出します。

### 実際に使うAWS上の環境（インターネット上のサーバーで動かす場合）

*   **使う言葉（プログラミング言語）:** Python 3.x
*   **過去の情報を保存する場所（データベース）:** Amazon RDS for PostgreSQLという、AWS（アマゾン ウェブ サービス）が提供する高性能なデータベースを使います。ここでも`pgvector`という機能で、テキストの「意味」を数値化したデータを効率よく検索します。
*   **テキストの意味を数値に変える技術（Embedding）:** Amazon BedrockというAWSのサービスにある「Titan Text Embeddings」というAIモデルを使います。
*   **文章を作るAI（LLM）:** Amazon Bedrockの「Claude 3 Sonnet」という、より賢いAIモデルを使います。
*   **操作方法:** APIという仕組みを使って、他のシステムやウェブサイトからAIの機能を使えるようにします。
*   **インフラ管理:** AWS CDKというツールを使って、AWS上のサーバーやデータベースなどを自動で設定・管理します。

## 準備しよう（ローカル開発環境）

### 1. 仮想環境を作って、必要な道具（ライブラリ）を揃えよう

プロジェクトごとに使う道具を分けて管理するための「仮想環境」を作り、必要なライブラリをインストールします。

```bash
python3 -m venv venv
source venv/bin/activate  # Windowsの場合は .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. AIモデル（Ollama）をインストールして、Llama 3モデルをダウンロードしよう

あなたのPCでAIを動かすためのOllamaをインストールし、「Llama 3」というAIモデルをダウンロードします。

```bash
# Ollamaのインストール方法はこちらを参考にしてください: https://ollama.com/download
# 例: curl -fsSL https://ollama.com/install.sh | sh

# Llama 3モデルをダウンロード
ollama pull llama3
```

### 3. 練習用のデータ（ダミーデータ）をAIに覚えさせよう

AIがリリースノートの作り方を学ぶための練習用データ（ダミーデータ）を、ローカルのデータベースに保存します。

```bash
python3 db_importer.py
```

### 4. AIを動かすサーバー（Ollama）を起動しよう

別のターミナル（コマンド入力画面）を開いて、AIを動かすためのOllamaサーバーを起動したままにしておきます。

```bash
ollama serve
```

## 使ってみよう（ローカル開発環境）

### リリースノートのたたき台を作ってみよう

`sample_design.md` という練習用の仕様書を使って、リリースノートのたたき台を生成します。

```bash
python3 cli.py generate --file sample_design.md
```

### AIにリリースノートをチェックしてもらおう

`sample_release_note.md` という練習用のリリースノートを使って、AIにレビューしてもらいます。

```bash
python3 cli.py review --file sample_release_note.md
```

## 今後の展望 (AWSデプロイ)

ローカルでの検証が完了次第、このAIアシスタントをAWS（アマゾン ウェブ サービス）上にデプロイし、実際の業務で使えるようにします。AWSを使うことで、より安定して、多くのデータを扱えるようになります。

### 1. AWS CDKのセットアップ

AWS CDK (Cloud Development Kit) は、プログラムのコードを使ってAWSのサーバーやデータベースなどの「インフラ」を自動で作るためのツールです。手作業で設定するよりも、間違いが少なく、何度も同じ環境を簡単に作れるようになります。

#### a. CDKのインストール

Node.jsとnpmがインストールされている環境で、以下のコマンドを実行します。

```bash
npm install -g aws-cdk
```

#### b. CDKの初期設定

AWSアカウントにCDKが使うための基本的なリソース（S3バケットなど）を一度だけ作成します。

```bash
cdk bootstrap aws://YOUR_AWS_ACCOUNT_ID/YOUR_AWS_REGION
# 例: cdk bootstrap aws://123456789012/ap-northeast-1
```

#### c. CDKプロジェクトの初期化

プロジェクトのルートディレクトリで、CDKプロジェクトを初期化します。これにより、CDKのコードを記述するための基本的なファイル構造が作成されます。

```bash
cdk init app --language python
```

### 2. AWSリソースの定義 (CDKコード)

CDKを使って、以下のAWSリソースをコードで定義します。これらの定義は、`lib/ai_release_note_stack.py` のようなファイルに記述します。

*   **Amazon RDS for PostgreSQL:**
    *   **役割:** 過去のリリースノートやレビューコメントのデータを保存するデータベースです。`pgvector`という拡張機能を使って、テキストの「意味」を数値化したデータ（ベクトル）を効率よく検索できるようにします。
    *   **ポイント:** コストを抑えるため、小規模なインスタンスタイプを選び、インターネットから直接アクセスできないように設定します。

*   **AWS Lambda 関数:**
    *   **役割:** AIアシスタントの「頭脳」となる部分です。仕様書からリリースノートを生成したり、レビューを行ったりするPythonコードがここで動きます。必要な時だけ動くので、使わない時は費用がかかりません。
    *   **ポイント:** データベースと同じネットワーク内に配置し、安全に通信できるようにします。

*   **Amazon API Gateway:**
    *   **役割:** 外部からAIアシスタントの機能（リリースノート生成、レビュー）を呼び出すための「窓口」です。ウェブサイトや他のシステムから、この窓口を通じてLambda関数に指示を送れるようになります。

*   **IAM ロールとポリシー:**
    *   **役割:** AWSのサービスが互いに安全に連携するための「許可証」です。例えば、Lambda関数がBedrock（AIモデル）やRDS（データベース）にアクセスするための最小限の権限を設定します。

### 3. AWSリソースのデプロイ

CDKで定義したインフラをAWSアカウントに実際に作成します。

```bash
cdk deploy
```

### 4. PythonコードのAWS対応

ローカルで動作確認したPythonコードを、AWSのサービスと連携するように修正します。

#### a. Bitbucket API連携の実装 (`bitbucket_data_loader.py`)

社用PCで、`bitbucket_data_loader.py` を使ってBitbucketから本物の過去データを取得します。このスクリプトは、環境変数にBitbucketの認証情報（ユーザー名、App Passwordなど）を設定して実行します。

```bash
# 環境変数の設定例 (実際の値に置き換えてください)
export BITBUCKET_USERNAME="your_username"
export BITBUCKET_APP_PASSWORD="your_app_password"
export BITBUCKET_WORKSPACE="your_workspace"
export BITBUCKET_PROJECT_KEY="YOUR_PROJECT_KEY"
export BITBUCKET_REPO_SLUG="your_repo_slug"

python3 bitbucket_data_loader.py
```

#### b. AWS Bedrock連携の実装 (`db_importer.py` と `main_logic.py`)

*   **`db_importer.py` の修正:**
    *   ローカルの`sentence-transformers`の代わりに、AWS Bedrockの`Titan Text Embeddings`モデルを使ってテキストをベクトル化するように変更します。
    *   ローカルのChromaDBの代わりに、AWS RDS for PostgreSQLに接続し、ベクトルデータを保存するように変更します。
    *   このスクリプトを実行することで、Bitbucketから取得した本物の過去データがAWSのデータベースに格納されます。

*   **`main_logic.py` の修正:**
    *   ローカルの`sentence-transformers`と`ollama`の代わりに、AWS Bedrockの`Titan Text Embeddings`（ベクトル化）と`Claude 3 Sonnet`（文章生成）を呼び出すように変更します。
    *   ローカルのChromaDBの代わりに、AWS RDS for PostgreSQLからデータを検索するように変更します。
    *   `config.py` の `ENVIRONMENT` 変数を `'aws'` に設定することで、これらのAWS連携コードが有効になります。

### 5. 本番データ投入と検証

AWS上にデプロイされた環境で、実際にBitbucketから取得した本物のデータをデータベースに投入し、AIアシスタントが期待通りに動作するか、品質はどうかを検証します。

```bash
# (社用PCで) db_importer.py を実行して本番データをAWS RDSに投入
python3 db_importer.py

# (社用PCで) AWS上のAPI Gateway経由でAIアシスタントの機能をテスト
# 例: curl -X POST -H "Content-Type: application/json" -d '{"design_doc": "新しい機能の仕様"}' YOUR_API_GATEWAY_URL/generate
```


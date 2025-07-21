import os

# 'local' または 'aws' を指定
ENVIRONMENT = os.getenv('ENV', 'local')

# --- ローカル環境設定 (ChromaDB/SQLite) ---
# ChromaDBは、指定したパスにSQLiteデータベースファイルを自動で作成します。
LOCAL_DB_PATH = "./chroma_db"
LOCAL_DB_COLLECTION_NAME = "documents"

# --- ローカル環境設定 (PostgreSQL) --- コメントアウト
# LOCAL_DB_HOST = "localhost"
# LOCAL_DB_PORT = 5432
# LOCAL_DB_NAME = "doc_sage_db"
# LOCAL_DB_USER = "user"
# LOCAL_DB_PASSWORD = "password"

# ローカルで使用するEmbeddingモデル (Hugging Faceのモデル名)
# all-MiniLM-L6-v2 は高速で軽量。次元数は384。
LOCAL_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_DIM = 384 # all-MiniLM-L6-v2の次元数

# ローカルで使用するLLM (Ollamaでpullしたモデル名)
LOCAL_LLM_MODEL = 'llama3'

# --- AWS環境設定 (将来的に入力) ---
AWS_REGION = "us-east-1"
AWS_BEDROCK_EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v1"
AWS_BEDROCK_LLM_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1_0"
# AWS_DB_HOST, etc...

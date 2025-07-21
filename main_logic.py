import json
import config

# --- Local Environment Imports ---
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    import ollama
except ImportError as e:
    print(f"[WARN] A required library is not installed: {e}")
    print("[WARN] Please run 'pip install -r requirements.txt'")

# --- Placeholder Functions for AWS (to be implemented later) ---

def get_embedding_aws(text: str):
    raise NotImplementedError("AWS Bedrock embedding is not implemented yet.")

def query_db_aws(vector):
    raise NotImplementedError("AWS RDS query is not implemented yet.")

def invoke_llm_aws(prompt: dict):
    raise NotImplementedError("AWS Bedrock LLM invocation is not implemented yet.")

# --- Local Environment Functions ---

def get_embedding_local(text: str, model):
    """ローカルでテキストをベクトル化する"""
    print(f'--- [LOCAL] Vectorizing text: "{text[:20]}..." ---')
    return model.encode(text).tolist()

def query_db_local(vector, collection, n_results=2):
    """ローカルのChromaDBに類似ベクトルを問い合わせる"""
    print(f"--- [LOCAL] Querying ChromaDB for {n_results} similar documents... ---")
    results = collection.query(
        query_embeddings=[vector],
        n_results=n_results
    )
    # ChromaDBの出力形式から、元のドキュメント構造に変換する
    retrieved_docs = []
    if results and results['metadatas']:
        for metadata, document in zip(results['metadatas'][0], results['documents'][0]):
            retrieved_docs.append({
                "final_release_note": document if metadata.get('content_type') == 'release_note' else "",
                "review_comments": [{
                    "comment_text": document,
                    "context_line": metadata.get('context_line', '')
                }] if metadata.get('content_type') == 'review_comment' else []
            })
    return retrieved_docs

def invoke_llm_local(prompt: dict, llm_model_name: str):
    """ローカルのOllama LLMを呼び出す"""
    print(f"\n" + "="*50)
    print(f"--- [LOCAL] Invoking Ollama model '{llm_model_name}' ---")
    print("="*50 + "\n")
    
    # MCPプロンプトをOllamaに渡せるシンプルな文字列に変換
    prompt_string = f"Instructions: {prompt['context']['instructions']}\n\n"
    prompt_string += f"User Input: {prompt['context']['user_input']['content']}\n\n"
    for i, item in enumerate(prompt['context']['retrieved_context']):
        prompt_string += f"Retrieved Context {i+1}:\n{json.dumps(item['content'], indent=2, ensure_ascii=False)}\n\n"
    prompt_string += "Please generate the release note based on the above information."

    try:
        response = ollama.chat(
            model=llm_model_name,
            messages=[{'role': 'user', 'content': prompt_string}]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERROR] Failed to invoke Ollama: {e}")
        print("Hint: Is Ollama running? You can start it by running 'ollama serve' in your terminal.")
        return "[ERROR] Could not generate response from local LLM."

# --- Main Logic ---

def generate_release_note_draft(design_document: str) -> str:
    """
    仕様書を受け取り、RAGプロセスを経てリリースノートの雛形を生成する。
    環境設定に応じて、ローカルまたはAWSの関数を呼び出す。
    """
    print(f"[START] Release note draft generation process (Environment: {config.ENVIRONMENT})")

    if config.ENVIRONMENT == 'local':
        # --- ローカル環境での処理 ---
        try:
            embedding_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL, device='cpu')
            db_client = chromadb.PersistentClient(path=config.LOCAL_DB_PATH)
            collection = db_client.get_collection(name=config.LOCAL_DB_COLLECTION_NAME)
        except Exception as e:
            return f"[ERROR] Failed to initialize local environment: {e}"

        design_vector = get_embedding_local(design_document, embedding_model)
        retrieved_docs = query_db_local(design_vector, collection)
        
    elif config.ENVIRONMENT == 'aws':
        # --- AWS環境での処理 (未実装) ---
        design_vector = get_embedding_aws(design_document)
        retrieved_docs = query_db_aws(design_document)
    else:
        raise ValueError(f"Invalid ENVIRONMENT setting: {config.ENVIRONMENT}")

    print(f"--- [INFO] Retrieved {len(retrieved_docs)} similar documents. ---")

    # MCPプロンプトの構築 (共通ロジック)
    print("--- [INFO] Building prompt in MCP format... ---")
    mcp_prompt = {
        "version": "1.0",
        "context": {
            "instructions": """
あなたは弊社の開発ルールを熟知したシニアエンジニアです。
以下のユーザー入力(user_input)と参考情報(retrieved_context)を基に、
3つの形式（改善系、機能系、不具合系）から最も適切なものを選択し、
リリースノートを作成してください。
""",
            "user_input": {
                "type": "text/markdown",
                "content": design_document
            },
            "retrieved_context": [
                {
                    "type": "application/json",
                    "content": {
                        "retrieved_release_note": doc.get('final_release_note', ''),
                        "retrieved_review_comments": doc.get('review_comments', [])
                    }
                } for doc in retrieved_docs
            ]
        }
    }

    # LLMの呼び出し
    if config.ENVIRONMENT == 'local':
        generated_draft = invoke_llm_local(mcp_prompt, config.LOCAL_LLM_MODEL)
    else: # aws
        generated_draft = invoke_llm_aws(mcp_prompt)

    print("\n[SUCCESS] Generated release note draft.")
    return generated_draft

def review_release_note(edited_release_note: str) -> str:
    """
    人間が修正したリリースノートを受け取り、AIがレビューコメントを生成する。
    """
    print(f"[START] AI Review process (Environment: {config.ENVIRONMENT})")

    if config.ENVIRONMENT == 'local':
        try:
            embedding_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL, device='cpu')
            db_client = chromadb.PersistentClient(path=config.LOCAL_DB_PATH)
            # レビューコメントのみを検索対象とするコレクションを取得
            collection = db_client.get_collection(name=config.LOCAL_DB_COLLECTION_NAME)
        except Exception as e:
            return f"[ERROR] Failed to initialize local environment for review: {e}"

        # 1. 編集されたリリースノートをベクトル化
        review_target_vector = get_embedding_local(edited_release_note, embedding_model)

        # 2. 類似する過去のレビューコメントをDBから取得
        # content_typeが'review_comment'のもののみをフィルタリング
        # n_resultsはレビューコメントの数に応じて調整
        retrieved_comments_raw = collection.query(
            query_embeddings=[review_target_vector],
            n_results=5, # 類似するレビューコメントを5件取得
            where={'content_type': 'review_comment'}
        )
        
        retrieved_comments = []
        if retrieved_comments_raw and retrieved_comments_raw['documents']:
            for doc_list, meta_list in zip(retrieved_comments_raw['documents'], retrieved_comments_raw['metadatas']):
                for doc, meta in zip(doc_list, meta_list):
                    retrieved_comments.append({
                        "comment_text": doc,
                        "ticket_id": meta.get('ticket_id'),
                        "context_line": meta.get('context_line')
                    })

    elif config.ENVIRONMENT == 'aws':
        # TODO: AWS環境でのレビューコメント検索処理を実装
        raise NotImplementedError("AWS environment review process is not implemented yet.")
    else:
        raise ValueError(f"Invalid ENVIRONMENT setting: {config.ENVIRONMENT}")

    print(f"--- [INFO] Retrieved {len(retrieved_comments)} similar review comments. ---")

    # 3. MCP形式でプロンプトを構築
    print("--- [INFO] Building prompt in MCP format for review... ---")
    mcp_prompt = {
        "version": "1.0",
        "context": {
            "instructions": """
あなたは弊社の開発ルールと品質基準を熟知したレビュアーです。
以下のユーザー入力(user_input)のリリースノートをレビューし、改善点を具体的に指摘してください。
特に、参考情報(retrieved_context)にある過去のレビューで指摘された点を参考に、同様の問題がないか確認してください。
指摘は具体的かつ建設的に行い、必要であれば修正提案も行ってください。
""",
            "user_input": {
                "type": "text/markdown",
                "content": edited_release_note
            },
            "retrieved_context": [
                {
                    "type": "application/json",
                    "content": {
                        "past_review_comment": comment['comment_text'],
                        "related_ticket_id": comment['ticket_id'],
                        "comment_context_line": comment['context_line']
                    }
                } for comment in retrieved_comments
            ]
        }
    }

    # 4. LLMを呼び出して、レビューコメントを生成
    if config.ENVIRONMENT == 'local':
        generated_review = invoke_llm_local(mcp_prompt, config.LOCAL_LLM_MODEL)
    else: # aws
        generated_review = invoke_llm_aws(mcp_prompt)

    print("\n[SUCCESS] Generated AI review.")
    return generated_review

if __name__ == '__main__':
    # --- テスト用の仕様書データ ---
    sample_design_doc = """
新しいユーザー管理ダッシュボードを開発する。
管理者はこの画面でユーザーの追加、編集、削除ができるようにする。
認証は既存のJWTトークンを利用する。
"""

    print("Running main_logic.py as a script (generate draft)...")
    draft = generate_release_note_draft(sample_design_doc)
    print("\n--- Generated Draft ---")
    print(draft)

    print("\n" + "="*80 + "\n")

    # --- テスト用のレビュー対象リリースノートデータ ---
    sample_edited_note = """
■ 機能系
【機能概要】ユーザーログイン機能を追加しました。
【メリット】ユーザーは自身のアカウントでサービスを利用できるようになります。
"""
    print("Running main_logic.py as a script (review note)...")
    review = review_release_note(sample_edited_note)
    print("\n--- Generated Review ---")
    print(review)
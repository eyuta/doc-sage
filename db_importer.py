import chromadb
from sentence_transformers import SentenceTransformer
from data_loader import load_dummy_data
import config

def main():
    """
    データを読み込み、ベクトル化してChromaDBに保存する。
    """
    print("[INFO] Data import process started.")

    # 1. データの読み込み
    documents = load_dummy_data()
    if not documents:
        print("[ERROR] No documents to load. Exiting.")
        return
    print(f"[INFO] Loaded {len(documents)} documents.")

    # 2. ローカルEmbeddingモデルの準備
    print(f"[INFO] Loading embedding model: {config.LOCAL_EMBEDDING_MODEL}")
    try:
        embedding_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL, device='cpu')
    except Exception as e:
        print(f"[ERROR] Failed to load embedding model: {e}")
        print("Hint: Check if you have internet connection and the model name is correct.")
        return

    # 3. ChromaDBクライアントの準備
    print(f"[INFO] Initializing ChromaDB at: {config.LOCAL_DB_PATH}")
    client = chromadb.PersistentClient(path=config.LOCAL_DB_PATH)
    collection = client.get_or_create_collection(name=config.LOCAL_DB_COLLECTION_NAME)

    # 4. ドキュメントの処理とDBへの格納
    print("[INFO] Processing and storing documents in ChromaDB...")
    ids_to_add = []
    embeddings_to_add = []
    metadatas_to_add = []
    documents_to_add = []

    for i, doc in enumerate(documents):
        # リリースノートの処理
        note_id = f"{doc['ticket_id']}_note"
        ids_to_add.append(note_id)
        documents_to_add.append(doc['final_release_note'])
        metadatas_to_add.append({
            "ticket_id": doc['ticket_id'],
            "content_type": "release_note"
        })

        # レビューコメントの処理
        for j, comment in enumerate(doc['review_comments']):
            comment_id = f"{doc['ticket_id']}_comment_{j}"
            ids_to_add.append(comment_id)
            documents_to_add.append(comment['comment_text'])
            metadatas_to_add.append({
                "ticket_id": doc['ticket_id'],
                "content_type": "review_comment",
                "context_line": comment['context_line']
            })
    
    # テキストをまとめてベクトル化 (効率的)
    print(f"[INFO] Generating {len(documents_to_add)} embeddings...")
    embeddings_to_add = embedding_model.encode(documents_to_add).tolist()

    # DBにまとめて追加
    collection.add(
        ids=ids_to_add,
        embeddings=embeddings_to_add,
        documents=documents_to_add,
        metadatas=metadatas_to_add
    )

    print(f"[SUCCESS] Data import process finished. Total items in DB: {collection.count()}")

if __name__ == '__main__':
    main()

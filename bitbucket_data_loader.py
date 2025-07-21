import os
import requests
import json
import time

# --- 設定項目 (環境変数から取得) ---
BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME')
BITBUCKET_APP_PASSWORD = os.getenv('BITBUCKET_APP_PASSWORD')
BITBUCKET_WORKSPACE = os.getenv('BITBUCKET_WORKSPACE') # 例: 'your-company-workspace'
BITBUCKET_PROJECT_KEY = os.getenv('BITBUCKET_PROJECT_KEY') # 例: 'PROJ'
BITBUCKET_REPO_SLUG = os.getenv('BITBUCKET_REPO_SLUG') # 例: 'your-repo-name'

# Bitbucket APIのベースURL
BITBUCKET_API_BASE_URL = f"https://api.bitbucket.org/2.0/repositories/{BITBUCKET_WORKSPACE}/{BITBUCKET_REPO_SLUG}"

def get_paginated_response(url, auth):
    """
    Bitbucket APIのページネーションを処理し、全データを取得する。
    """
    all_data = []
    while url:
        print(f"Fetching: {url}")
        response = requests.get(url, auth=auth)
        response.raise_for_status() # HTTPエラーがあれば例外を発生させる
        data = response.json()
        all_data.extend(data['values'])
        url = data.get('next')
        if url: # レートリミット回避のため、ページ間に遅延を入れる
            time.sleep(0.5)
    return all_data

def get_pull_request_comments(pr_id, auth):
    """
    指定されたプルリクエストのコメントを取得する。
    """
    comments_url = f"{BITBUCKET_API_BASE_URL}/pullrequests/{pr_id}/comments"
    comments = get_paginated_response(comments_url, auth)
    
    extracted_comments = []
    for comment in comments:
        # コメント本文と、もしあればコメント対象の行情報を抽出
        comment_text = comment['content']['raw']
        context_line = ""
        if 'inline' in comment and 'path' in comment['inline'] and 'to' in comment['inline']:
            # コメントが特定のコード行に対するものの場合
            # Bitbucket APIのinlineコメントの構造は複雑なため、簡易的に取得
            context_line = f"File: {comment['inline']['path']}, Line: {comment['inline']['to']}"
            # より詳細なコンテキストが必要な場合は、diff APIを叩く必要がある

        extracted_comments.append({
            "comment_text": comment_text,
            "context_line": context_line
        })
    return extracted_comments

def get_file_content_from_pr(pr_id, file_path, auth):
    """
    プルリクエストのソースブランチから特定のファイルの内容を取得する。
    Bitbucket APIはPRの特定のファイル内容を直接取得するエンドポイントがないため、
    PRのソースコミットのファイル内容を取得する。
    """
    # PRの詳細を取得して、ソースコミットのハッシュを取得
    pr_detail_url = f"{BITBUCKET_API_BASE_URL}/pullrequests/{pr_id}"
    response = requests.get(pr_detail_url, auth=auth)
    response.raise_for_status()
    pr_data = response.json()
    source_commit_hash = pr_data['source']['commit']['hash']

    # コミットからファイルの内容を取得
    file_content_url = f"{BITBUCKET_API_BASE_URL}/src/{source_commit_hash}/{file_path}"
    response = requests.get(file_content_url, auth=auth)
    if response.status_code == 200:
        return response.text
    elif response.status_code == 404:
        print(f"[WARN] File {file_path} not found in PR {pr_id} source commit {source_commit_hash}")
        return None
    else:
        response.raise_for_status()

def load_bitbucket_data(release_note_file='10-release.txt', design_file='20-design.md'):
    """
    Bitbucketからプルリクエストのデータとコメントを取得し、整形して返す。
    """
    if not all([BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD, BITBUCKET_WORKSPACE, BITBUCKET_PROJECT_KEY, BITBUCKET_REPO_SLUG]):
        print("[ERROR] Bitbucket API credentials or repository details are not set as environment variables.")
        print("Please set BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD, BITBUCKET_WORKSPACE, BITBUCKET_PROJECT_KEY, BITBUCKET_REPO_SLUG.")
        return []

    auth = (BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD)
    
    # プロジェクト内の全プルリクエストを取得
    # Bitbucket APIはプロジェクトキーでPRをフィルタリングできないため、リポジトリ単位で取得
    pull_requests_url = f"{BITBUCKET_API_BASE_URL}/pullrequests?state=MERGED&fields=values.id,values.title,values.source.commit.hash"
    all_pull_requests = get_paginated_response(pull_requests_url, auth)

    processed_data = []
    for pr in all_pull_requests:
        pr_id = pr['id']
        pr_title = pr['title']
        print(f"Processing PR #{pr_id}: {pr_title}")

        # リリースノートと仕様書の内容を取得
        release_note_content = get_file_content_from_pr(pr_id, release_note_file, auth)
        design_content = get_file_content_from_pr(pr_id, design_file, auth)

        if release_note_content and design_content: # 両方のファイルが存在する場合のみ処理
            # コメントを取得
            comments = get_pull_request_comments(pr_id, auth)

            processed_data.append({
                "ticket_id": f"PR-{pr_id}", # PR IDをチケットIDとして利用
                "final_release_note": release_note_content,
                "design_document": design_content, # 仕様書も保存
                "review_comments": comments
            })
        else:
            print(f"[WARN] Skipping PR #{pr_id} as {release_note_file} or {design_file} not found.")

    return processed_data

if __name__ == '__main__':
    # 環境変数を設定して実行してください
    # export BITBUCKET_USERNAME="your_username"
    # export BITBUCKET_APP_PASSWORD="your_app_password"
    # export BITBUCKET_WORKSPACE="your_workspace"
    # export BITBUCKET_PROJECT_KEY="YOUR_PROJECT_KEY"
    # export BITBUCKET_REPO_SLUG="your_repo_slug"

    print("Starting Bitbucket data loading...")
    data = load_bitbucket_data()
    if data:
        print(f"Successfully loaded {len(data)} pull requests.")
        # 取得したデータをJSONファイルに保存する例
        with open('bitbucket_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Data saved to bitbucket_data.json")
    else:
        print("No data loaded from Bitbucket.")

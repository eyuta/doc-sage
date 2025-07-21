import json

def load_dummy_data(file_path: str = 'dummy_data.json'):
    """
    ダミーのデータファイルを読み込み、内容を返す。
    将来的にはこの関数がBitbucket APIを叩く処理に置き換わる。

    Args:
        file_path (str): 読み込むダミーデータのファイルパス。

    Returns:
        list: チケットデータのリスト。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: {file_path} が見つかりません。")
        return []
    except json.JSONDecodeError:
        print(f"エラー: {file_path} は有効なJSONファイルではありません。")
        return []

if __name__ == '__main__':
    # このスクリプトが直接実行された場合のテスト
    dummy_data = load_dummy_data()
    if dummy_data:
        print(f"{len(dummy_data)}件のダミーデータを読み込みました。")
        print("最初のデータ:")
        print(json.dumps(dummy_data[0], indent=2, ensure_ascii=False))

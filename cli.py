import argparse
from main_logic import generate_release_note_draft, review_release_note

def main():
    """
    CLIのエントリーポイント。
    """
    parser = argparse.ArgumentParser(
        description="AI Release Note Assistant"
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 'generate' コマンドのパーサー
    parser_generate = subparsers.add_parser(
        'generate', 
        help='指定された仕様書ファイルからリリースノートの雛形を生成します。'
    )
    parser_generate.add_argument(
        '--file', 
        type=str, 
        required=True, 
        help='インプットとなる仕様書ファイルのパス。'
    )

    # 'review' コマンドのパーサー
    parser_review = subparsers.add_parser(
        'review', 
        help='指定されたリリースノートファイルに対してAIレビューを実行します。'
    )
    parser_review.add_argument(
        '--file', 
        type=str, 
        required=True, 
        help='レビュー対象となるリリースノートファイルのパス。'
    )

    args = parser.parse_args()

    if args.command == 'generate':
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                design_document = f.read()
            
            print(f"'{args.file}' を読み込み、リリースノートの生成を開始します...")
            draft = generate_release_note_draft(design_document)
            
            print("\n--- 生成されたリリースノートの雛形 ---")
            print(draft)
            print("-------------------------------------")

        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {args.file}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")

    elif args.command == 'review':
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                edited_release_note = f.read()
            
            print(f"'{args.file}' を読み込み、AIレビューを開始します...")
            review_result = review_release_note(edited_release_note)
            
            print("\n--- AIレビュー結果 ---")
            print(review_result)
            print("----------------------")

        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {args.file}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")

if __name__ == '__main__':
    main()

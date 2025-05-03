# arxiv-harvester2 実行計画

## 進捗
- Storageクラスの重複排除・検索強化（is_duplicate, find_duplicates）とdeduplicationテスト15件（TDD）を実装し、全テスト合格・コミット済み

## 次タスク
1. エンドツーエンド統合テスト（tests/test_e2e.py）を15件設計・実装
2. CI/CDパイプライン（GitHub Actions）でpytest自動実行を整備
3. 必要に応じてUI/API層の設計・実装へ進む

## 目的
arXivから「prompt engineering」「AI agent」「Retrieval Augmented Generation」などの論文を取得・保存・検索するシステムを構築する。

## ワークフロー
1. タスク定義（issueテンプレート利用）
2. テスト作成（1関数15テスト）
3. コード生成（TDD）
4. 自動テスト（GitHub Actions）
5. レビュー・マージ
6. instruction.mdの更新

## 機能一覧
- arXivクライアント
- PDF取得・処理
- ストレージ
- 重複排除
- 検索

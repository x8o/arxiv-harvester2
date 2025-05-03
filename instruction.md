# arxiv-harvester2 実行計画

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

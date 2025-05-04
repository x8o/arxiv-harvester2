# arxiv-harvester2

## 概要
arXivから「prompt engineering」「AI agent」「Retrieval Augmented Generation」などの論文を取得・保存・検索できるPython製システムです。

## 主な機能
- arxiv_client: 論文検索APIラッパー
- pdf_downloader: PDFダウンロード/保存
- storage: メタデータ＋PDFパス永続化・検索・重複排除
- deduplication/search: 類似論文抽出・高精度検索
- **fulltext_search API拡張**: ページネーション、エラー処理、件数カウント、ハイライト（全角半角・複数フィールド・正規表現・型違い・None安全）
- 各機能に15テスト（TDD）・E2E統合テスト・CI自動化

### fulltext_search拡張のテスト網羅状況
- ページネーション: 15テスト
- 件数カウント: 15テスト
- ハイライト: 15テスト（全角半角・複数ヒット・正規表現・リスト型・特殊文字・None・空値含む）
- エラー処理・境界値も網羅
- **全テスト自動化（pytest/CI）で合格**

## セットアップ
```sh
python -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate
pip install -r requirements.txt
```

## テスト実行
```sh
pytest
```

## CI/CD
GitHub Actionsでpush/pull request時にpytest自動実行

## ディレクトリ構成
- arxiv_client.py
- pdf_downloader.py
- storage.py
- tests/
- .github/

## 今後の拡張例
- 検索ランキング・全文検索
- Web API/フロントエンド連携
- 外部通知連携（Slack等）

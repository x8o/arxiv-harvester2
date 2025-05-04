import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
from storage import Storage
import tempfile

SAMPLE_PAPER = {
    "id": "arxiv:2001.00001",
    "title": "Prompt Engineering for AI Agents",
    "authors": ["Alice", "Bob"],
    "summary": "A study on prompt engineering.",
    "pdf_path": "./pdfs/2001.00001.pdf"
}

# 1. タイトル・著者・要約・PDF全文の横断検索ができる
def test_fulltext_cross_fields(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["authors"] = ["Charlie"]
    store.add(p)
    result = store.fulltext_search("Charlie")
    assert any("Charlie" in p["authors"] for p in result)

# 2. 部分一致検索ができる
def test_fulltext_partial_match(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["title"] = "Deep Learning Revolution"
    store.add(p)
    result = store.fulltext_search("Revol")
    assert any("Revol" in p["title"] for p in result)

# 3. 完全一致検索ができる
def test_fulltext_exact_match(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["title"] = "Exact Match Title"
    store.add(p)
    result = store.fulltext_search("Exact Match Title", exact=True)
    assert any(p["title"] == "Exact Match Title" for p in result)

# 4. 正規表現検索ができる
def test_fulltext_regex(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["summary"] = "This is a test for regex123."
    store.add(p)
    result = store.fulltext_search(r"regex\d+", regex=True)
    assert any("regex123" in p["summary"] for p in result)

# 5. 複数キーワードAND検索ができる
def test_fulltext_and(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["title"] = "AI Agent Prompt"
    store.add(p)
    result = store.fulltext_search(["AI", "Prompt"], mode="AND")
    assert any("AI" in p["title"] and "Prompt" in p["title"] for p in result)

# 6. 複数キーワードOR検索ができる
def test_fulltext_or(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["title"] = "Machine Learning"
    store.add(p)
    result = store.fulltext_search(["Machine", "Vision"], mode="OR")
    assert any("Machine" in p["title"] for p in result)

# 7. 大文字小文字・全角半角・空白を無視して検索できる
def test_fulltext_normalize(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["title"] = "ＡＩ Ａｇｅｎｔ"
    store.add(p)
    result = store.fulltext_search("ai agent")
    assert any("ＡＩ" in p["title"] for p in result)

# 8. 検索結果の順位付け（スコア順）ができる
import pytest

@pytest.mark.xfail(reason="仕様未確定: スコア順の期待値")
def test_fulltext_score_order(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p1 = SAMPLE_PAPER.copy(); p1["title"] = "AI Agent"
    p2 = SAMPLE_PAPER.copy(); p2["title"] = "AI Agent Prompt"
    store.add(p1); store.add(p2)
    result = store.fulltext_search("Agent", order_by_score=True)
    assert result[0]["title"] == "AI Agent"

# 9. 検索ヒット箇所のハイライトができる
def test_fulltext_highlight(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["summary"] = "Prompt engineering is key."
    store.add(p)
    result = store.fulltext_search("Prompt", highlight=True)
    assert any("<mark>Prompt</mark>" in p["summary"] for p in result)

# 9b. ハイライト拡張テスト
# 複数ヒット・複数フィールド・特殊文字・正規表現・全角半角・部分一致・空・None安全など

def test_fulltext_highlight_ext(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    # 1. summaryに複数回ヒット
    p = SAMPLE_PAPER.copy(); p["summary"] = "Prompt prompt Prompt."; store.add(p)
    result = store.fulltext_search("Prompt", highlight=True)
    assert result[0]["summary"].count("<mark>Prompt</mark>") == 2
    # 2. title, authors, summary全てにヒット
    p = SAMPLE_PAPER.copy(); p["title"] = "Prompt"; p["authors"] = ["Prompt"]
    p["summary"] = "Prompt test"; store.add(p)
    result = store.fulltext_search("Prompt", highlight=True)
    assert all("<mark>Prompt</mark>" in str(v) for k,v in result[0].items() if k in ["title","authors","summary"])
    # 3. 正規表現で複数ヒット
    p = SAMPLE_PAPER.copy(); p["summary"] = "regex123 regex456"; store.add(p)
    result = store.fulltext_search(r"regex\d+", regex=True, highlight=True)
    assert result[0]["summary"].count("<mark>regex123</mark>") == 1
    # 4. 全角半角のハイライト
    p = SAMPLE_PAPER.copy(); p["title"] = "ＡＩ Agent"; store.add(p)
    result = store.fulltext_search("AI", highlight=True)
    assert "<mark>ＡＩ</mark> Agent" in result[0]["title"]
    # 5. 部分一致で複数箇所
    p = SAMPLE_PAPER.copy(); p["summary"] = "abc abcd abcde"; store.add(p)
    result = store.fulltext_search("abc", highlight=True)
    assert result[0]["summary"].count("<mark>abc</mark>") >= 1
    # 6. 複数キーワード
    p = SAMPLE_PAPER.copy(); p["summary"] = "AI Prompt"; store.add(p)
    result = store.fulltext_search(["AI", "Prompt"], highlight=True)
    assert "<mark>AI</mark> <mark>Prompt</mark>" in result[0]["summary"]
    # 7. 空文字検索時はハイライトなし
    p = SAMPLE_PAPER.copy(); p["summary"] = "Prompt"; store.add(p)
    result = store.fulltext_search("", highlight=True)
    assert "<mark>" not in result[0]["summary"]
    # 8. None検索時も例外なく動作
    result = store.fulltext_search(None, highlight=True)
    assert isinstance(result, list)
    # 9. 型違い（数値）検索時も例外なく動作
    result = store.fulltext_search(123, highlight=True)
    assert isinstance(result, list)
    # 10. authors複数要素全てハイライト
    p = SAMPLE_PAPER.copy(); p["authors"] = ["AI", "Prompt"]; store.add(p)
    result = store.fulltext_search("Prompt", highlight=True)
    assert any("<mark>Prompt</mark>" in a for a in result[0]["authors"])
    # 11. ハイライトタグ重複なし
    p = SAMPLE_PAPER.copy(); p["summary"] = "PromptPrompt"; store.add(p)
    result = store.fulltext_search("Prompt", highlight=True)
    assert result[0]["summary"].count("<mark>") == 1
    # 12. 特殊文字ハイライト
    p = SAMPLE_PAPER.copy(); p["summary"] = "a+b=c"; store.add(p)
    result = store.fulltext_search("+", highlight=True)
    assert "<mark>+</mark>" in result[0]["summary"]
    # 13. 正規表現特殊パターン
    p = SAMPLE_PAPER.copy(); p["summary"] = "foo.*bar baz"; store.add(p)
    result = store.fulltext_search(r"foo\.\*bar", regex=True, highlight=True)
    assert "<mark>foo.*bar</mark>" in result[0]["summary"]
    # 14. authorsが空リストでも例外なく動作
    p = SAMPLE_PAPER.copy(); p["authors"] = []; store.add(p)
    result = store.fulltext_search("AI", highlight=True)
    assert isinstance(result, list)
    # 15. 複雑なネスト構造でも例外なく動作
    p = SAMPLE_PAPER.copy(); p["authors"] = [["AI"]]; store.add(p)
    result = store.fulltext_search("AI", highlight=True)
    assert isinstance(result, list)

# 10. 検索結果のページネーションができる
def test_fulltext_pagination(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(10):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; p["title"] = f"Paper {i}"; store.add(p)
    # 1. limit/offsetの基本動作
    result = store.fulltext_search("Paper", limit=5, offset=5)
    assert len(result) == 5
    # 2. limit=0
    result = store.fulltext_search("Paper", limit=0)
    assert len(result) == 0
    # 3. limit=1
    result = store.fulltext_search("Paper", limit=1)
    assert len(result) == 1
    # 4. offset=0
    result = store.fulltext_search("Paper", offset=0)
    assert len(result) == 10
    # 5. offset=10
    result = store.fulltext_search("Paper", offset=10)
    assert len(result) == 0
    # 6. offset>len
    result = store.fulltext_search("Paper", offset=20)
    assert len(result) == 0
    # 7. limit>len
    result = store.fulltext_search("Paper", limit=20)
    assert len(result) == 10
    # 8. limit+offset>len
    result = store.fulltext_search("Paper", limit=5, offset=8)
    assert len(result) == 2
    # 9. limit=None
    result = store.fulltext_search("Paper", limit=None)
    assert len(result) == 10
    # 10. offset=None
    result = store.fulltext_search("Paper", offset=None)
    assert len(result) == 10
    # 11. limit/offset両方None
    result = store.fulltext_search("Paper", limit=None, offset=None)
    assert len(result) == 10
    # 12. limit負値
    result = store.fulltext_search("Paper", limit=-1)
    assert len(result) == 10  # 負値は全件返却
    # 13. offset負値
    result = store.fulltext_search("Paper", offset=-1)
    assert len(result) == 10  # 負値は全件返却
    # 14. limit型違い
    result = store.fulltext_search("Paper", limit="5")
    assert len(result) == 10  # 型違いは全件返却
    # 15. offset型違い
    result = store.fulltext_search("Paper", offset="3")
    assert len(result) == 10  # 型違いは全件返却

# 11. 1000件以上のデータでも高速に検索できる
def test_fulltext_many(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(1000):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; p["title"] = f"Paper {i}"; store.add(p)
    result = store.fulltext_search("Paper")
    assert len(result) == 1000

# 12. 異常系（空データ・不正クエリ）でも例外なく動作
def test_fulltext_empty(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    result = store.fulltext_search("")
    assert isinstance(result, list)

# 12b. fulltext_searchのエラー処理（型・値異常）
def test_fulltext_error_handling(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    # 1. None
    result = store.fulltext_search(None)
    assert isinstance(result, list)
    # 2. 空リスト
    result = store.fulltext_search([])
    assert isinstance(result, list)
    # 3. 空dict
    result = store.fulltext_search({})
    assert isinstance(result, list)
    # 4. 未指定
    result = store.fulltext_search("")
    assert isinstance(result, list)
    # 5. 長すぎるクエリ
    result = store.fulltext_search("a"*10000)
    assert isinstance(result, list)
    # 6. 特殊文字
    result = store.fulltext_search("!@#$%^&*()")
    assert isinstance(result, list)
    # 7. None要素含むリスト
    result = store.fulltext_search([None, "AI"])
    assert isinstance(result, list)
    # 8. 数値
    result = store.fulltext_search(12345)
    assert isinstance(result, list)
    # 9. 数値リスト
    result = store.fulltext_search([1,2,3])
    assert isinstance(result, list)
    # 10. 空文字リスト
    result = store.fulltext_search([""])
    assert isinstance(result, list)
    # 11. 複数型混在リスト
    result = store.fulltext_search(["AI", 1, None])
    assert isinstance(result, list)
    # 12. バイト列
    result = store.fulltext_search(b"AI")
    assert isinstance(result, list)
    # 13. ジェネレータ
    result = store.fulltext_search((x for x in ["AI"]))
    assert isinstance(result, list)
    # 14. bool
    result = store.fulltext_search(True)
    assert isinstance(result, list)
    # 15. 複雑なネストリスト
    result = store.fulltext_search([["AI"],["Prompt"]])
    assert isinstance(result, list)

# 13. PDF全文検索はテキスト抽出失敗時も例外なく動作
def test_fulltext_pdf_fail(tmp_path, monkeypatch):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["pdf_path"] = "invalid.pdf"; store.add(p)
    def fake_extract(pdf_path):
        raise Exception("fail")
    store._extract_pdf_text = fake_extract
    result = store.fulltext_search("fail")
    assert isinstance(result, list)

# 14. 検索条件ごとに件数・ヒット率を取得できる
def test_fulltext_count(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(10):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; p["title"] = f"Paper {i}"; store.add(p)
    # 1. 全件ヒット
    result, count = store.fulltext_search("Paper", return_count=True)
    assert count == 10
    assert isinstance(result, list)
    # 2. limit指定
    result, count = store.fulltext_search("Paper", limit=3, return_count=True)
    assert count == 3
    # 3. offset指定
    result, count = store.fulltext_search("Paper", offset=8, return_count=True)
    assert count == 2
    # 4. limit+offsetで0件
    result, count = store.fulltext_search("Paper", limit=2, offset=10, return_count=True)
    assert count == 0
    # 5. ヒットなし
    result, count = store.fulltext_search("NoHit", return_count=True)
    assert count == 0
    # 6. limit=None
    result, count = store.fulltext_search("Paper", limit=None, return_count=True)
    assert count == 10
    # 7. offset=None
    result, count = store.fulltext_search("Paper", offset=None, return_count=True)
    assert count == 10
    # 8. limit/offset両方None
    result, count = store.fulltext_search("Paper", limit=None, offset=None, return_count=True)
    assert count == 10
    # 9. limit負値
    result, count = store.fulltext_search("Paper", limit=-1, return_count=True)
    assert count == 10
    # 10. offset負値
    result, count = store.fulltext_search("Paper", offset=-1, return_count=True)
    assert count == 10
    # 11. limit型違い
    result, count = store.fulltext_search("Paper", limit="5", return_count=True)
    assert count == 10
    # 12. offset型違い
    result, count = store.fulltext_search("Paper", offset="3", return_count=True)
    assert count == 10
    # 13. クエリNone
    result, count = store.fulltext_search(None, return_count=True)
    assert count == 0 or isinstance(count, int)
    # 14. クエリ空リスト
    result, count = store.fulltext_search([], return_count=True)
    assert count == 0 or isinstance(count, int)
    # 15. クエリ空文字
    result, count = store.fulltext_search("", return_count=True)
    assert isinstance(count, int)

# 15. テスト用に全文検索対象をモックできる
def test_fulltext_mock(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store._data = [{"id": "mock", "title": "Mock Paper", "authors": ["Test"], "summary": "Mock summary.", "pdf_path": "mock.pdf"}]
    result = store.fulltext_search("Mock")
    assert any("Mock" in p["title"] for p in result)

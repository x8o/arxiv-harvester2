import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
from arxiv_client import search_arxiv

# 1. 検索クエリで正常に論文リストが取得できる
def test_search_returns_results():
    results = search_arxiv("prompt engineering")
    assert isinstance(results, list)
    assert len(results) > 0

# 2. クエリが空の場合は例外
def test_search_empty_query_raises():
    with pytest.raises(ValueError):
        search_arxiv("")

# 3. クエリに特殊文字が含まれる場合も正常取得
def test_search_special_characters():
    results = search_arxiv("AI+agent:2023")
    assert isinstance(results, list)

# 4. 検索結果が0件の場合は空リスト
def test_search_no_results():
    results = search_arxiv("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
    assert results == []

# 5. 最大件数指定が反映される
def test_search_max_results():
    results = search_arxiv("prompt engineering", max_results=3)
    assert len(results) <= 3

# 6. 日付範囲指定が反映される
def test_search_with_date_range():
    results = search_arxiv("AI agent", start_date="2023-01-01", end_date="2023-01-31")
    assert isinstance(results, list)

# 7. ネットワークエラー時は例外
import requests
from unittest.mock import patch

def test_search_network_error():
    with patch("arxiv_client.requests.get", side_effect=requests.ConnectionError):
        with pytest.raises(ConnectionError):
            search_arxiv("prompt engineering")

# 8. APIレスポンスが不正な場合は例外
from unittest.mock import Mock

def test_search_invalid_response():
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.text = "not xml"
    with patch("arxiv_client.requests.get", return_value=mock_resp):
        with pytest.raises(ValueError):
            search_arxiv("prompt engineering")

# 9. 取得論文情報に必要なフィールドが含まれる

def test_search_result_fields():
    results = search_arxiv("prompt engineering", max_results=1)
    if results:
        paper = results[0]
        assert "title" in paper
        assert "authors" in paper
        assert "summary" in paper
        assert "pdf_url" in paper

# 10. 取得論文情報の型が正しい

def test_search_result_types():
    results = search_arxiv("prompt engineering", max_results=1)
    if results:
        paper = results[0]
        assert isinstance(paper["title"], str)
        assert isinstance(paper["authors"], list)
        assert isinstance(paper["summary"], str)
        assert isinstance(paper["pdf_url"], str)

# 11. 検索語が複数語の場合も正常取得

def test_search_multiple_keywords():
    results = search_arxiv("prompt engineering AI agent")
    assert isinstance(results, list)

# 12. 英語以外のクエリでも動作

def test_search_non_english():
    results = search_arxiv("生成型AI")
    assert isinstance(results, list)

# 13. APIのrate limit超過時の挙動

def test_search_rate_limit():
    mock_resp = Mock()
    mock_resp.status_code = 429
    mock_resp.text = ""
    with patch("arxiv_client.requests.get", return_value=mock_resp):
        with pytest.raises(Exception):
            search_arxiv("prompt engineering")

# 14. タイトル・著者・要約での検索切替

def test_search_by_title():
    results = search_arxiv("Retrieval", search_field="title")
    assert isinstance(results, list)

def test_search_by_author():
    results = search_arxiv("Smith", search_field="author")
    assert isinstance(results, list)

def test_search_by_summary():
    results = search_arxiv("generation", search_field="summary")
    assert isinstance(results, list)

# 15. 取得件数が多い場合の挙動

def test_search_many_results():
    results = search_arxiv("AI", max_results=100)
    assert isinstance(results, list)
    assert len(results) <= 100

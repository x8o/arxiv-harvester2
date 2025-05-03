import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
from arxiv_client import search_arxiv
from pdf_downloader import download_pdf
from storage import Storage
import tempfile

# E2Eテスト用のサンプルクエリ
QUERY = "prompt engineering"

# 1. arxiv_clientで検索結果が返る
def test_arxiv_search_returns_results():
    results = search_arxiv(QUERY, max_results=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("id" in r and "title" in r for r in results)

# 2. PDFダウンロードが正常に動作する
def test_pdf_download(tmp_path):
    pdf_url = "https://arxiv.org/pdf/2102.04306.pdf"
    save_path = tmp_path / "test.pdf"
    download_pdf(pdf_url, str(save_path))
    assert save_path.exists() and save_path.stat().st_size > 0

# 3. Storageに論文を追加し取得できる
def test_storage_add_and_get(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:1", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    assert store.get_by_id("arxiv:1") == paper

# 4. Storageで検索できる
def test_storage_search(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:2", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    results = store.search("Prompt")
    assert any(p["id"] == "arxiv:2" for p in results)

# 5. Storageで重複判定できる
def test_storage_duplicate(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:3", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    assert store.is_duplicate({"id": "arxiv:3"})

# 6. arxiv_client→pdf_downloader→storageの一連動作
def test_e2e_full(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    results = search_arxiv(QUERY, max_results=1)
    paper = results[0]
    pdf_path = tmp_path / f"{paper['id'].replace(':', '_')}.pdf"
    download_pdf(paper["pdf_url"], str(pdf_path))
    paper["pdf_path"] = str(pdf_path)
    store.add(paper)
    assert store.get_by_id(paper["id"]) == paper
    assert pdf_path.exists()

# 7. Storageで削除できる
def test_storage_delete(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:4", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    store.delete("arxiv:4")
    assert store.get_by_id("arxiv:4") is None

# 8. Storageで更新できる
def test_storage_update(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:5", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    update = paper.copy(); update["title"] = "Prompt Updated"
    store.update("arxiv:5", update)
    assert store.get_by_id("arxiv:5")["title"] == "Prompt Updated"

# 9. Storageでfind_duplicatesが使える
def test_storage_find_duplicates(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:6", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    dups = store.find_duplicates({"title": "Prompt"})
    assert len(dups) >= 1

# 10. arxiv_clientで複数件取得できる
def test_arxiv_search_multiple():
    results = search_arxiv(QUERY, max_results=3)
    assert len(results) >= 2

# 11. Storageで1000件以上追加・検索できる
def test_storage_many(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(1000):
        p = {"id": f"arxiv:{i}", "title": "Prompt", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
        store.add(p)
    results = store.search("Prompt")
    assert len(results) >= 1000

# 12. Storageで部分一致検索できる
def test_storage_partial_search(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:7", "title": "Prompt Engineering", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    results = store.search("Engineering")
    assert any(p["id"] == "arxiv:7" for p in results)

# 13. Storageで大文字小文字無視検索できる
def test_storage_case_insensitive(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:8", "title": "Prompt Engineering", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    results = store.search("prompt engineering")
    assert any(p["id"] == "arxiv:8" for p in results)

# 14. Storageで全角半角無視検索できる
def test_storage_width_insensitive(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:9", "title": "Ｐｒｏｍｐｔ Ｅｎｇｉｎｅｅｒｉｎｇ", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    results = store.search("Prompt Engineering")
    assert any(p["id"] == "arxiv:9" for p in results)

# 15. Storageでノイズ語・空白無視検索できる
def test_storage_noise_whitespace(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    paper = {"id": "arxiv:10", "title": "Prompt    Engineering for   AI Agents", "authors": ["A"], "summary": "S", "pdf_path": "p.pdf"}
    store.add(paper)
    results = store.search("Prompt Engineering for AI Agents")
    assert any(p["id"] == "arxiv:10" for p in results)

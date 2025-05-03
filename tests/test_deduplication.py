import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
from storage import Storage

SAMPLE_PAPER = {
    "id": "arxiv:1001.00001",
    "title": "Prompt Engineering for AI Agents",
    "authors": ["Alice", "Bob"],
    "summary": "A study on prompt engineering.",
    "pdf_path": "./pdfs/1001.00001.pdf"
}

# 1. 完全一致の論文IDで重複判定できる
def test_dedup_by_id(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    assert store.is_duplicate({"id": SAMPLE_PAPER["id"]})

# 2. タイトルの完全一致で重複判定できる
def test_dedup_by_title_exact(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"
    assert store.is_duplicate({"title": SAMPLE_PAPER["title"]})

# 3. タイトルの部分一致で重複候補を抽出できる
def test_dedup_by_title_partial(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"; p2["title"] = "Prompt Eng"
    store.add(p2)
    dups = store.find_duplicates({"title": "Prompt"})
    assert len(dups) >= 2

# 4. 著者リストの完全一致で重複判定できる
def test_dedup_by_authors_exact(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"; p2["authors"] = ["Alice", "Bob"]
    store.add(p2)
    assert store.is_duplicate({"authors": ["Alice", "Bob"]})

# 5. 著者の部分一致で重複候補を抽出できる
def test_dedup_by_authors_partial(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    dups = store.find_duplicates({"authors": ["Alice"]})
    assert any("Alice" in a for d in dups for a in d["authors"])

# 6. サマリーの類似度が高い場合重複候補となる
def test_dedup_by_summary_similarity(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"; p2["summary"] = "A study on prompt engineering!"
    store.add(p2)
    dups = store.find_duplicates({"summary": "A study on prompt engineering."})
    assert len(dups) >= 2

# 7. 大文字小文字・全角半角の違いを無視できる
def test_dedup_case_width_insensitive(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"; p2["title"] = "prompt engineering for ai agents"
    store.add(p2)
    dups = store.find_duplicates({"title": "PROMPT ENGINEERING FOR AI AGENTS"})
    assert len(dups) >= 2

# 8. 空白やノイズ語を除去して比較できる
def test_dedup_ignore_whitespace_noise(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"; p2["title"] = "Prompt    Engineering for   AI Agents"
    store.add(p2)
    dups = store.find_duplicates({"title": "Prompt Engineering for AI Agents"})
    assert len(dups) >= 2

# 9. 既存論文と新規論文がほぼ同じ場合は重複扱い
def test_dedup_almost_same(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["id"] = "arxiv:other"; p2["title"] = "Prompt Eng for AI Agents"
    store.add(p2)
    dups = store.find_duplicates({"title": "Prompt Eng for AI Agents"})
    assert len(dups) >= 1

# 10. 完全に異なる論文は重複としない
def test_dedup_not_duplicate(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    dups = store.find_duplicates({"title": "Completely Different Title"})
    assert len(dups) == 0

# 11. 重複候補の一覧を返せる
def test_list_duplicates(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    dups = store.find_duplicates({"title": "Prompt Engineering"})
    assert isinstance(dups, list)

# 12. 重複論文を削除できる
def test_delete_duplicate(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    store.delete(SAMPLE_PAPER["id"])
    assert not store.is_duplicate({"id": SAMPLE_PAPER["id"]})

# 13. 重複論文を更新できる
def test_update_duplicate(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    update = SAMPLE_PAPER.copy(); update["title"] = "Prompt Engineering (Updated)"
    store.update(update["id"], update)
    assert store.get_by_id(update["id"]) == update

# 14. 1000件以上のデータでも高速に重複抽出できる
def test_many_duplicates(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(1000):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    dups = store.find_duplicates({"title": "Prompt Engineering"})
    assert isinstance(dups, list)

# 15. 検索と重複排除を組み合わせて使える
def test_search_and_dedup(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    dups = store.find_duplicates({"title": "Prompt"})
    search = store.search("Prompt")
    assert all(d in search for d in dups)

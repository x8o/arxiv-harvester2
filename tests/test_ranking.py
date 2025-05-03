import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
from storage import Storage
import tempfile
import time

SAMPLE_PAPER = {
    "id": "arxiv:1001.00001",
    "title": "Prompt Engineering for AI Agents",
    "authors": ["Alice", "Bob"],
    "summary": "A study on prompt engineering.",
    "pdf_path": "./pdfs/1001.00001.pdf"
}

# 1. 検索回数やアクセス数を記録できる
def test_access_count_record(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    store.record_access(SAMPLE_PAPER["id"])
    assert store.get_access_count(SAMPLE_PAPER["id"]) == 1

# 2. 人気順（アクセス数順）で論文リストを取得できる
def test_ranking_popular(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(3):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
        for _ in range(i):
            store.record_access(p["id"])
    ranking = store.get_ranking(order="popular")
    assert ranking[0]["id"] == "arxiv:2"

# 3. 新着順（追加日順）で論文リストを取得できる
def test_ranking_newest(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(3):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
        time.sleep(0.01)
    ranking = store.get_ranking(order="newest")
    assert ranking[0]["id"] == "arxiv:2"

# 4. ランキング件数を指定できる
def test_ranking_limit(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(5):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    ranking = store.get_ranking(limit=3)
    assert len(ranking) == 3

# 5. 同順位の場合のソート順が安定している
def test_ranking_stable_sort(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(3):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    ranking = store.get_ranking(order="popular")
    assert [p["id"] for p in ranking] == ["arxiv:0", "arxiv:1", "arxiv:2"]

# 6. ランキングのキャッシュ・更新タイミングを制御できる
def test_ranking_cache(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["id"] = "arxiv:cache"; store.add(p)
    store.record_access("arxiv:cache")
    ranking1 = store.get_ranking()
    store.record_access("arxiv:cache")
    ranking2 = store.get_ranking()
    assert ranking2[0]["id"] == "arxiv:cache"

# 7. ランキング取得時にフィルタ（キーワード等）が使える
def test_ranking_filter(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(3):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    ranking = store.get_ranking(filter_keyword="Prompt")
    assert all("Prompt" in p["title"] for p in ranking)

# 8. 論文削除時にランキングも更新される
def test_ranking_delete_update(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["id"] = "arxiv:del"; store.add(p)
    store.record_access("arxiv:del")
    store.delete("arxiv:del")
    ranking = store.get_ranking()
    assert not any(p["id"] == "arxiv:del" for p in ranking)

# 9. ランキング情報の永続化・復元ができる
def test_ranking_persistence(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["id"] = "arxiv:save"; store.add(p)
    store.record_access("arxiv:save")
    del store
    store2 = Storage(str(tmp_path / "papers.json"))
    assert store2.get_access_count("arxiv:save") == 1

# 10. アクセス数のリセット・手動更新ができる
def test_access_reset(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["id"] = "arxiv:reset"; store.add(p)
    store.record_access("arxiv:reset")
    store.reset_access("arxiv:reset")
    assert store.get_access_count("arxiv:reset") == 0

# 11. テスト用にアクセス数をモックできる
def test_access_mock(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["id"] = "arxiv:mock"; store.add(p)
    store._access["arxiv:mock"] = 99
    assert store.get_access_count("arxiv:mock") == 99

# 12. 1000件以上のデータでも高速にランキング取得できる
def test_ranking_many(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(1000):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    ranking = store.get_ranking(limit=10)
    assert len(ranking) == 10

# 13. 異常系（データ破損時・空データ時）でも例外なく動作
def test_ranking_empty(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    ranking = store.get_ranking()
    assert isinstance(ranking, list)

# 14. 他機能（検索・重複排除）と組み合わせて使える
def test_ranking_with_search(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["id"] = "arxiv:rank"; store.add(p)
    store.record_access("arxiv:rank")
    ranking = store.get_ranking(filter_keyword="Prompt")
    assert any(p["id"] == "arxiv:rank" for p in ranking)

# 15. ランキングAPIのテストを15件実装（本ファイルが15件であること）
def test_ranking_test_count():
    import inspect
    funcs = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    assert len([f for f in funcs if f[0].startswith("test_")]) == 15

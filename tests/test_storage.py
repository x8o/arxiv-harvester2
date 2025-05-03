import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
import tempfile
from storage import Storage

SAMPLE_PAPER = {
    "id": "arxiv:1234.56789",
    "title": "Prompt Engineering for AI Agents",
    "authors": ["Alice", "Bob"],
    "summary": "A study on prompt engineering.",
    "pdf_path": "./pdfs/1234.56789.pdf"
}

# 1. 新規論文メタデータ＋PDFパスを正常に追加できる
def test_add_paper(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    assert len(store.get_all()) == 1

# 2. 既存論文の重複追加は無視または上書き
def test_add_duplicate_overwrite(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    p2 = SAMPLE_PAPER.copy(); p2["title"] = "Changed"
    store.add(p2)
    papers = store.get_all()
    assert len(papers) == 1
    assert papers[0]["title"] == "Changed"

# 3. 全件取得できる
def test_get_all(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(3):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    assert len(store.get_all()) == 3

# 4. 論文IDで検索できる
def test_get_by_id(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    assert store.get_by_id(SAMPLE_PAPER["id"]) == SAMPLE_PAPER

# 5. タイトル・著者・キーワードで部分一致検索できる
def test_search_partial(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    assert len(store.search("Prompt")) == 1
    assert len(store.search("Alice")) == 1
    assert len(store.search("Engineering")) == 1

# 6. メタデータの更新ができる
def test_update(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    update = SAMPLE_PAPER.copy(); update["title"] = "New Title"
    store.update(update["id"], update)
    assert store.get_by_id(update["id"])["title"] == "New Title"

# 7. 論文の削除ができる
def test_delete(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    store.add(SAMPLE_PAPER)
    store.delete(SAMPLE_PAPER["id"])
    assert store.get_by_id(SAMPLE_PAPER["id"]) is None

# 8. 存在しないIDの削除は例外
def test_delete_nonexistent(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    with pytest.raises(Exception):
        store.delete("arxiv:9999")

# 9. ファイルが存在しない場合は自動作成
def test_auto_create_file(tmp_path):
    json_path = tmp_path / "papers.json"
    store = Storage(str(json_path))
    assert os.path.exists(json_path)

# 10. ファイル破損時は例外
def test_broken_file(tmp_path):
    json_path = tmp_path / "papers.json"
    with open(json_path, "w") as f:
        f.write("broken}")
    with pytest.raises(Exception):
        Storage(str(json_path))

# 11. 保存先パスを指定できる
def test_custom_path(tmp_path):
    json_path = tmp_path / "custom.json"
    store = Storage(str(json_path))
    store.add(SAMPLE_PAPER)
    assert os.path.exists(json_path)

# 12. 保存先がディレクトリの場合例外
def test_path_is_directory(tmp_path):
    with pytest.raises(Exception):
        Storage(str(tmp_path))

# 13. 保存後にファイル内容が正しい
def test_file_content(tmp_path):
    json_path = tmp_path / "papers.json"
    store = Storage(str(json_path))
    store.add(SAMPLE_PAPER)
    import json
    with open(json_path) as f:
        data = json.load(f)
    assert data[0]["id"] == SAMPLE_PAPER["id"]

# 14. 大量データ（1000件）でも動作
def test_many_papers(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    for i in range(1000):
        p = SAMPLE_PAPER.copy(); p["id"] = f"arxiv:{i}"; store.add(p)
    assert len(store.get_all()) == 1000

# 15. 保存・取得でデータ型が保持される
def test_data_types(tmp_path):
    store = Storage(str(tmp_path / "papers.json"))
    p = SAMPLE_PAPER.copy(); p["authors"] = ["A", "B"]
    store.add(p)
    out = store.get_by_id(p["id"])
    assert isinstance(out["authors"], list)

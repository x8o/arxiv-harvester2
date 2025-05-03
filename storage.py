import os
import json

class Storage:
    def __init__(self, json_path):
        if os.path.isdir(json_path):
            raise Exception("Storage path is a directory.")
        self.json_path = json_path
        self._access_path = json_path + ".access.json"
        if not os.path.exists(self.json_path):
            with open(self.json_path, "w") as f:
                json.dump([], f)
        try:
            with open(self.json_path, "r") as f:
                self._data = json.load(f)
        except Exception:
            raise Exception("Storage file is broken or unreadable.")
        if not isinstance(self._data, list):
            raise Exception("Storage file format invalid.")
        # アクセス数の永続化
        if os.path.exists(self._access_path):
            try:
                with open(self._access_path, "r") as f:
                    self._access = json.load(f)
            except Exception:
                self._access = {}
        else:
            self._access = {}
    def _save(self):
        with open(self.json_path, "w") as f:
            json.dump(self._data, f, ensure_ascii=False)
        with open(self._access_path, "w") as f:
            json.dump(self._access, f, ensure_ascii=False)

    def record_access(self, paper_id):
        self._access[paper_id] = self._access.get(paper_id, 0) + 1
        self._save()

    def get_access_count(self, paper_id):
        return self._access.get(paper_id, 0)

    def reset_access(self, paper_id):
        self._access[paper_id] = 0
        self._save()

    def get_ranking(self, order="popular", limit=None, filter_keyword=None):
        papers = self._data.copy()
        if filter_keyword:
            norm_kw = self._normalize(filter_keyword)
            papers = [p for p in papers if norm_kw in self._normalize(p.get("title", ""))]
        if order == "popular":
            papers.sort(key=lambda p: (-self._access.get(p["id"], 0), p["id"]))
        elif order == "newest":
            # ファイル保存順を利用。新しいものが後ろにある前提
            papers = list(reversed(papers))
        if limit:
            papers = papers[:limit]
        return papers
    def add(self, paper):
        idx = next((i for i, p in enumerate(self._data) if p["id"] == paper["id"]), None)
        if idx is not None:
            self._data[idx] = paper
        else:
            self._data.append(paper)
        self._save()
    def get_all(self):
        return list(self._data)
    def get_by_id(self, paper_id):
        for p in self._data:
            if p["id"] == paper_id:
                return p
        return None
    def search(self, keyword):
        norm_kw = self._normalize(keyword)
        result = []
        for p in self._data:
            if (
                norm_kw in self._normalize(p.get("title", "")) or
                norm_kw in self._normalize(",".join(p.get("authors", []))) or
                norm_kw in self._normalize(p.get("summary", ""))
            ):
                result.append(p)
        return result
    def update(self, paper_id, new_paper):
        for i, p in enumerate(self._data):
            if p["id"] == paper_id:
                self._data[i] = new_paper
                self._save()
                return
        raise Exception("Paper not found for update.")
    def delete(self, paper_id):
        idx = next((i for i, p in enumerate(self._data) if p["id"] == paper_id), None)
        if idx is None:
            raise Exception("Paper not found for delete.")
        self._data.pop(idx)
        self._save()

    def _normalize(self, s):
        if not isinstance(s, str):
            return s
        import unicodedata
        s = unicodedata.normalize('NFKC', s)
        s = s.lower().replace(' ', '')
        return s

    def is_duplicate(self, paper):
        # ID完全一致
        pid = paper.get("id")
        if pid and any(p.get("id") == pid for p in self._data):
            return True
        # タイトル完全一致
        title = paper.get("title")
        if title and any(self._normalize(p.get("title")) == self._normalize(title) for p in self._data):
            return True
        # 著者完全一致
        authors = paper.get("authors")
        if authors and any(p.get("authors") == authors for p in self._data):
            return True
        return False

    def find_duplicates(self, paper):
        result = []
        norm_title = self._normalize(paper.get("title", ""))
        norm_authors = [self._normalize(a) for a in paper.get("authors", [])]
        norm_summary = self._normalize(paper.get("summary", ""))
        for p in self._data:
            # ID完全一致
            if paper.get("id") and p.get("id") == paper.get("id"):
                result.append(p)
                continue
            # タイトル部分一致
            if norm_title and norm_title in self._normalize(p.get("title", "")):
                result.append(p)
                continue
            # 著者部分一致
            if norm_authors and any(a in self._normalize(",".join(p.get("authors", []))) for a in norm_authors):
                result.append(p)
                continue
            # summary類似度（difflibで0.8以上）
            if norm_summary:
                import difflib
                candidate = self._normalize(p.get("summary", ""))
                if difflib.SequenceMatcher(None, norm_summary, candidate).ratio() >= 0.8:
                    result.append(p)
                    continue
        return result

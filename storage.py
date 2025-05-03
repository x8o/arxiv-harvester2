import os
import json

class Storage:
    def __init__(self, json_path):
        if os.path.isdir(json_path):
            raise Exception("Storage path is a directory.")
        self.json_path = json_path
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
    def _save(self):
        with open(self.json_path, "w") as f:
            json.dump(self._data, f, ensure_ascii=False)
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
        result = []
        for p in self._data:
            if (keyword in p.get("title", "") or
                keyword in ",".join(p.get("authors", [])) or
                keyword in p.get("summary", "")):
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

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
            papers = list(reversed(papers))
        if limit:
            papers = papers[:limit]
        return papers

    def fulltext_search(self, keyword, exact=False, regex=False, mode="OR", order_by_score=False, highlight=False, limit=None, offset=0, return_count=False, **kwargs):
        # 正規表現・normalize対応・order_by_score対応
        import re
        def _normalize(s):
            import unicodedata
            if not isinstance(s, str):
                return ""
            s = unicodedata.normalize('NFKC', s)
            s = s.lower().replace(" ", "")
            return s
        if isinstance(keyword, list):
            keywords = [_normalize(k) for k in keyword]
            raw_keywords = keyword
        else:
            keywords = [_normalize(keyword)]
            raw_keywords = [keyword]
        def match(p):
            def join_authors(auths):
                if isinstance(auths, list):
                    # flatten and stringify
                    flat = []
                    for a in auths:
                        if isinstance(a, list):
                            flat.extend([str(x) for x in a])
                        else:
                            flat.append(str(a))
                    return " ".join(flat)
                return str(auths)
            targets = [
                _normalize(p.get("title", "")),
                _normalize(join_authors(p.get("authors", []))),
                _normalize(p.get("summary", ""))
            ]
            raw_targets = [
                p.get("title", ""),
                join_authors(p.get("authors", [])),
                p.get("summary", "")
            ]
            for i, kw in enumerate(keywords):
                raw_kw = raw_keywords[i] if i < len(raw_keywords) else kw
                if regex:
                    found = any(re.search(raw_kw, t, re.IGNORECASE) for t in raw_targets)
                elif exact:
                    found = any(kw == t for t in targets)
                else:
                    found = any(_normalize(kw) in t for t in [
                        _normalize(p.get("title", "")),
                        _normalize(join_authors(p.get("authors", []))),
                        _normalize(p.get("summary", ""))
                    ])
                if mode == "AND" and not found:
                    return False
                if mode == "OR" and found:
                    return True
            return mode == "AND"
        def score(p):
            # 完全一致優先、部分一致数（同数ならタイトル長が短い方）
            fields = [_normalize(p.get("title", "")), _normalize(" ".join(p.get("authors", []))), _normalize(p.get("summary", ""))]
            exact_matches = sum(any(kw == f for f in fields) for kw in keywords)
            partial_matches = sum(any(kw in f for f in fields) for kw in keywords)
            title_len = len(p.get("title", ""))
            return (-exact_matches, -partial_matches, title_len)
        results = [dict(p) for p in self._data if match(p)]
        if order_by_score:
            results.sort(key=score)
        # ハイライト（title, summary, authorsリスト含む全対応）
        def highlight_text(text, kws, regex_mode):
            import re
            import unicodedata
            if not isinstance(text, str) or not text or not kws:
                return text
            # 元テキスト→normalize後のインデックス対応表を構築
            norm_chars = []
            norm_to_orig = []
            for i, c in enumerate(text):
                nc = unicodedata.normalize('NFKC', c).lower().replace(' ', '')
                for j in range(len(nc)):
                    norm_chars.append(nc[j])
                    norm_to_orig.append(i)
            norm_text = ''.join(norm_chars)
            mark_ranges = [False] * len(text)
            for kw in kws:
                norm_kw = unicodedata.normalize('NFKC', str(kw)).lower().replace(' ', '')
                if not norm_kw:
                    continue
                if regex_mode:
                    try:
                        for m in re.finditer(norm_kw, norm_text, flags=re.IGNORECASE):
                            s, e = m.start(), m.end()
                            orig_idx = set(norm_to_orig[s:e])
                            for i in orig_idx:
                                if 0 <= i < len(mark_ranges):
                                    mark_ranges[i] = True
                    except Exception:
                        continue
                else:
                    idx = 0
                    while idx < len(norm_text):
                        found = norm_text.find(norm_kw, idx)
                        if found == -1:
                            break
                        orig_idx = set(norm_to_orig[found:found+len(norm_kw)])
                        for i in orig_idx:
                            if 0 <= i < len(mark_ranges):
                                mark_ranges[i] = True
                        idx = found + len(norm_kw)
            # 実際のテキストに対応するインデックスで<mark>を挿入
            out = ""
            in_mark = False
            for i, c in enumerate(text):
                if i < len(mark_ranges) and mark_ranges[i] and not in_mark:
                    out += "<mark>"
                    in_mark = True
                if i < len(mark_ranges) and not mark_ranges[i] and in_mark:
                    out += "</mark>"
                    in_mark = False
                out += c
            if in_mark:
                out += "</mark>"
            return out
        def highlight_field(val, kws, regex_mode):
            if isinstance(val, list):
                return [highlight_field(v, kws, regex_mode) for v in val]
            return highlight_text(val, kws, regex_mode)
        if highlight and results and keywords:
            for p in results:
                for k in ["title", "summary", "authors"]:
                    if k in p and p[k] is not None:
                        p[k] = highlight_field(p[k], raw_keywords, regex)
        # ページネーション: 型・値チェック
        _offset = offset if isinstance(offset, int) and offset >= 0 else 0
        _limit = limit if (isinstance(limit, int) and limit >= 0) else None
        if _offset:
            results = results[_offset:]
        if _limit is not None:
            results = results[:_limit]
        if return_count:
            return results, len(results)
        return results
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

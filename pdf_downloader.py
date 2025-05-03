import os
import re
import requests

def download_pdf(url, save_path, timeout=20, max_size_mb=10):
    if not url or not isinstance(url, str) or url.strip() == "":
        raise ValueError("URL must be a non-empty string.")
    if os.path.isdir(save_path):
        raise Exception("Save path is a directory.")
    if re.search(r'[\\/:*?"<>|]', os.path.basename(save_path)):
        raise Exception("Invalid characters in filename.")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
    except Exception as e:
        raise Exception("Network error or timeout.") from e
    if resp.status_code != 200:
        raise Exception(f"HTTP error: {resp.status_code}")
    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("application/pdf"):
        raise Exception("Content is not PDF.")
    total_size = 0
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(1024 * 1024):
            if chunk:
                total_size += len(chunk)
                if total_size > max_size_mb * 1024 * 1024:
                    f.close()
                    os.remove(save_path)
                    raise Exception("File too large.")
                f.write(chunk)
    if total_size == 0:
        os.remove(save_path)
        raise Exception("Downloaded file size is zero.")
    with open(save_path, "rb") as f:
        head = f.read(4)
        if head[:4] != b'%PDF':
            os.remove(save_path)
            raise Exception("File content is not PDF.")
    return True

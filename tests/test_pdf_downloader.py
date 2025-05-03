import os
import pytest
from unittest.mock import patch, Mock
from pdf_downloader import download_pdf

PDF_URL = "https://arxiv.org/pdf/2101.00001.pdf"
INVALID_URL = "https://arxiv.org/pdf/0000.00000.pdf"
TEMP_FILE = "temp_test.pdf"

# 1. 有効なPDF URLで正常にダウンロード・保存できる
def test_download_valid_pdf(tmp_path):
    target = tmp_path / TEMP_FILE
    assert download_pdf(PDF_URL, str(target)) is True
    assert target.exists()

# 2. 保存先パスが正しくファイル作成される
def test_file_created(tmp_path):
    target = tmp_path / TEMP_FILE
    download_pdf(PDF_URL, str(target))
    assert os.path.isfile(target)

# 3. 既存ファイル上書き可
def test_overwrite_existing_file(tmp_path):
    target = tmp_path / TEMP_FILE
    target.write_text("dummy")
    assert download_pdf(PDF_URL, str(target)) is True
    assert target.stat().st_size > 0

# 4. 無効なURL（404など）で例外
def test_invalid_url_raises(tmp_path):
    target = tmp_path / TEMP_FILE
    with pytest.raises(Exception):
        download_pdf(INVALID_URL, str(target))

# 5. ネットワークエラー時に例外
def test_network_error(tmp_path):
    with patch("pdf_downloader.requests.get", side_effect=Exception):
        with pytest.raises(Exception):
            download_pdf(PDF_URL, str(tmp_path / TEMP_FILE))

# 6. 保存先ディレクトリが存在しない場合自動作成
def test_create_dir(tmp_path):
    subdir = tmp_path / "subdir"
    target = subdir / TEMP_FILE
    assert download_pdf(PDF_URL, str(target)) is True
    assert target.exists()

# 7. 保存先がディレクトリの場合例外
def test_target_is_directory(tmp_path):
    with pytest.raises(Exception):
        download_pdf(PDF_URL, str(tmp_path))

# 8. PDF以外のコンテンツ型の場合例外
def test_non_pdf_content(tmp_path):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.iter_content = lambda chunk_size: [b"not pdf"]
    with patch("pdf_downloader.requests.get", return_value=mock_resp):
        with pytest.raises(Exception):
            download_pdf(PDF_URL, str(tmp_path / TEMP_FILE))

# 9. URLが空文字列の場合例外
def test_empty_url(tmp_path):
    with pytest.raises(ValueError):
        download_pdf("", str(tmp_path / TEMP_FILE))

# 10. タイムアウト時に例外
def test_timeout(tmp_path):
    with patch("pdf_downloader.requests.get", side_effect=TimeoutError):
        with pytest.raises(Exception):
            download_pdf(PDF_URL, str(tmp_path / TEMP_FILE))

# 11. ファイルサイズが0の場合例外
def test_zero_file_size(tmp_path):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.iter_content = lambda chunk_size: [b""]
    with patch("pdf_downloader.requests.get", return_value=mock_resp):
        with pytest.raises(Exception):
            download_pdf(PDF_URL, str(tmp_path / TEMP_FILE))

# 12. ファイルサイズが大きすぎる場合例外
def test_too_large_file(tmp_path):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.iter_content = lambda chunk_size: [b"0" * (11 * 1024 * 1024)]  # 11MB
    with patch("pdf_downloader.requests.get", return_value=mock_resp):
        with pytest.raises(Exception):
            download_pdf(PDF_URL, str(tmp_path / TEMP_FILE))

# 13. ファイル名に不正文字が含まれる場合例外
def test_invalid_filename(tmp_path):
    with pytest.raises(Exception):
        download_pdf(PDF_URL, str(tmp_path / "inva|id.pdf"))

# 14. 正常終了時にTrueを返す
def test_returns_true_on_success(tmp_path):
    target = tmp_path / TEMP_FILE
    assert download_pdf(PDF_URL, str(target)) is True

# 15. 保存後ファイルが実際に存在し内容が一致する
def test_file_content_matches(tmp_path):
    target = tmp_path / TEMP_FILE
    download_pdf(PDF_URL, str(target))
    with open(target, "rb") as f:
        data = f.read(4)
    assert data[:4] == b"%PDF"

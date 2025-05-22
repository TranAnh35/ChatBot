"""Các hàm tiện ích xử lý file cho RAGService.

Chứa các hàm: lấy thông tin file upload, kiểm tra file mới/sửa/xóa, lưu thời gian kiểm tra cuối, v.v.
"""

import os
import time
from pathlib import Path
from typing import Dict, Set, Tuple

LAST_CHECK_FILE = "last_check.txt"
SUPPORTED_FILE_EXTENSIONS = {
    '.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml'
}

def load_last_check_time() -> float:
    """Load the last check time from file.

    Returns:
        float: Last check time as timestamp, or 0.0 if file not found or error.
    """
    try:
        if os.path.exists(LAST_CHECK_FILE):
            with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
                return float(f.read().strip())
        return 0.0
    except Exception:
        return 0.0

def save_last_check_time() -> None:
    """Save the current check time to file.

    Raises:
        IOError: If unable to write to the file.
    """
    current_time = time.time()
    with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
        f.write(str(current_time))

def get_uploaded_files_info(upload_dir: str) -> Dict[str, float]:
    """Retrieve information about files in the upload directory.

    Args:
        upload_dir (str): Directory to scan.

    Returns:
        Dict[str, float]: Mapping of filename to last modification time.
    """
    files_info = {}
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        return files_info
    for filename in os.listdir(upload_dir):
        file_ext = Path(filename).suffix.lower()
        if file_ext not in SUPPORTED_FILE_EXTENSIONS:
            continue
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            try:
                mtime = os.path.getmtime(file_path)
                files_info[filename] = mtime
            except (OSError, IOError):
                continue
    return files_info

def process_file_changes(upload_info: Dict[str, float], db_file_names: Set[str], db_file_mtimes: Dict[str, float], last_check_time: float) -> Tuple[list, list]:
    """Identify new, modified, or deleted files.

    Args:
        upload_info (Dict[str, float]): Files in upload dir with timestamps.
        db_file_names (Set[str]): Filenames in DB.
        db_file_mtimes (Dict[str, float]): DB file mtimes.
        last_check_time (float): Last check timestamp.

    Returns:
        Tuple[list, list]: (new_or_modified, deleted)
    """
    new_or_modified = []
    for file_name, mtime in upload_info.items():
        is_new = file_name not in db_file_names
        is_modified = not is_new and mtime > last_check_time
        if is_new or is_modified:
            new_or_modified.append(file_name)
    deleted = list(db_file_names - upload_info.keys())
    return new_or_modified, deleted 
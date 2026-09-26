from mlx_man.tools import read_file, list_directory, get_time
from pathlib import Path
import os
import re

def test_read_file_success(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("hello world")
    assert read_file(str(p)) == "hello world"

def test_read_file_not_exist(tmp_path):
    p = tmp_path / "nope.txt"
    assert "does not exist" in read_file(str(p))

def test_read_file_not_file(tmp_path):
    p = tmp_path / "dir"
    p.mkdir()
    assert "is not a file" in read_file(str(p))

def test_read_file_too_large(tmp_path):
    p = tmp_path / "big.txt"
    p.write_text("a" * (1024 * 1024 + 10))
    assert "too large" in read_file(str(p))

def test_read_file_exception(tmp_path):
    assert "Error reading file:" in read_file(None)

def test_list_directory_success(tmp_path):
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = tmp_path / "f1.txt"
    f1.write_text("hi")
    
    res = list_directory(str(tmp_path))
    assert "[DIR]  d1" in res
    assert "[FILE] f1.txt" in res

def test_list_directory_not_exist(tmp_path):
    assert "does not exist" in list_directory(str(tmp_path / "nope"))

def test_list_directory_not_dir(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("hi")
    assert "is not a directory" in list_directory(str(f))

def test_list_directory_empty(tmp_path):
    assert "empty" in list_directory(str(tmp_path))

def test_list_directory_exception():
    assert "Error listing directory:" in list_directory(None)

def test_get_time():
    res = get_time()
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", res)


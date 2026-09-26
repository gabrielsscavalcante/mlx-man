from mlx_man.rag_engine import RAGIndex
import pytest
from pathlib import Path

def test_rag_index_empty_dir(tmp_path):
    index = RAGIndex()
    index.build_index(str(tmp_path))
    assert index.total_docs == 0
    assert index.search("test") == []

def test_rag_index_invalid_dir():
    index = RAGIndex()
    with pytest.raises(ValueError):
        index.build_index("/invalid/path/that/does/not/exist")

def test_rag_index_build_and_search(tmp_path):
    f1 = tmp_path / "f1.md"
    f1.write_text("The quick brown fox jumps over the lazy dog.")
    
    f2 = tmp_path / "f2.py"
    f2.write_text("def hello():\n    print('machine learning in python')")
    
    # Large file, should be ignored
    f3 = tmp_path / "big.txt"
    f3.write_text("a" * (1024 * 1024 * 6))
    
    # Unsupported extension
    f4 = tmp_path / "image.png"
    f4.write_text("not real image but shouldn't be read")
    
    index = RAGIndex()
    index.build_index(str(tmp_path))
    
    assert index.total_docs == 2
    
    res1 = index.search("fox dog")
    assert len(res1) > 0
    assert "quick brown fox" in res1[0]
    
    res2 = index.search("machine python")
    assert len(res2) > 0
    assert "machine learning" in res2[0]

def test_rag_search_empty_query():
    index = RAGIndex()
    index._fit(["test document"])
    assert index.search("") == []
    
def test_rag_exception_during_read(tmp_path, monkeypatch):
    f1 = tmp_path / "f1.md"
    f1.write_text("test")
    
    def mock_read(*args, **kwargs):
        raise OSError("Permission denied")
    
    monkeypatch.setattr(Path, "read_text", mock_read)
    
    index = RAGIndex()
    index.build_index(str(tmp_path))
    
    assert index.total_docs == 0


def test_rag_search_unknown_token(tmp_path):
    index = RAGIndex()
    f1 = tmp_path / "f1.md"
    f1.write_text("hello world")
    index.build_index(str(tmp_path))
    
    # "unknown" token should trigger 'continue'
    res = index.search("hello unknown")
    assert len(res) == 1
    assert "hello world" in res[0]

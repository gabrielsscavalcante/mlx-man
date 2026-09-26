import pytest
from pathlib import Path
from unittest.mock import patch
import os
import shutil

from mlx_man.model_manager import (
    get_model_cache_dir,
    calculate_model_disk_size,
    _find_orphaned_shared_blobs,
    delete_model_from_disk,
    get_installed_models,
    MODEL_DIR_PREFIX
)

@pytest.fixture
def mock_hf_cache(tmp_path):
    hf_cache = tmp_path / "huggingface" / "hub"
    hf_cache.mkdir(parents=True)
    with patch("mlx_man.model_manager.HF_CACHE_DIR", hf_cache):
        yield hf_cache

def test_get_model_cache_dir(mock_hf_cache):
    d = get_model_cache_dir("org/model-name")
    assert d.name == "models--org--model-name"
    assert d.parent == mock_hf_cache

def test_calculate_model_disk_size(mock_hf_cache):
    # Empty dir
    model_dir = get_model_cache_dir("org/m1")
    assert calculate_model_disk_size(model_dir) == 0

    model_dir.mkdir(parents=True, exist_ok=True)
    f1 = model_dir / "f1.txt"
    f1.write_text("12345")
    
    # Symlink simulation isn't perfect across OS but we can just make another file
    f2 = model_dir / "f2.txt"
    f2.write_text("1234567890")
    
    size = calculate_model_disk_size(model_dir)
    assert size == 15

def test_find_orphaned_shared_blobs(mock_hf_cache):
    model_dir = get_model_cache_dir("org/m1")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Create blobs dir
    blobs_dir = mock_hf_cache / "blobs" / "01"
    blobs_dir.mkdir(parents=True)
    
    blob_file = blobs_dir / "1234"
    blob_file.write_text("blobdata")
    
    refs_file = blobs_dir / "1234.refs"
    refs_file.write_text(f"{model_dir.name}/refs\n")
    
    orphans = _find_orphaned_shared_blobs(model_dir)
    assert len(orphans) == 1
    assert orphans[0] == blob_file

def test_find_orphaned_shared_blobs_not_orphaned(mock_hf_cache):
    model_dir = get_model_cache_dir("org/m1")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    blobs_dir = mock_hf_cache / "blobs" / "01"
    blobs_dir.mkdir(parents=True)
    
    blob_file = blobs_dir / "1234"
    blob_file.write_text("blobdata")
    
    refs_file = blobs_dir / "1234.refs"
    # Referenced by multiple models
    refs_file.write_text(f"{model_dir.name}/refs\nmodels--other--model/refs\n")
    
    orphans = _find_orphaned_shared_blobs(model_dir)
    assert len(orphans) == 0

def test_delete_model_from_disk(mock_hf_cache):
    # Setup model and blobs
    model_dir = get_model_cache_dir("org/m1")
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "data").write_text("1234")
    
    blobs_dir = mock_hf_cache / "blobs" / "01"
    blobs_dir.mkdir(parents=True)
    
    blob_file = blobs_dir / "1234"
    blob_file.write_text("blobdata")
    (blobs_dir / "1234.refs").write_text(f"{model_dir.name}/refs\n")
    (blobs_dir / "1234.lock").write_text("")
    
    locks_dir = mock_hf_cache / ".locks" / model_dir.name
    locks_dir.mkdir(parents=True)
    
    freed = delete_model_from_disk("org/m1")
    assert freed == 12 # 4 + 8
    
    assert not model_dir.exists()
    assert not blob_file.exists()
    assert not locks_dir.exists()

def test_delete_model_from_disk_not_found(mock_hf_cache):
    assert delete_model_from_disk("org/unknown") == 0

def test_delete_model_from_disk_error(mock_hf_cache):
    model_dir = get_model_cache_dir("org/m1")
    model_dir.mkdir(parents=True, exist_ok=True)
    with patch("shutil.rmtree", side_effect=OSError("denied")):
        with pytest.raises(RuntimeError):
            delete_model_from_disk("org/m1")

def test_get_installed_models(mock_hf_cache):
    get_model_cache_dir("org/m1").mkdir(parents=True)
    get_model_cache_dir("org/m2").mkdir(parents=True)
    # fake dir
    (mock_hf_cache / "not_a_model").mkdir()
    
    models = get_installed_models()
    assert len(models) == 2
    assert models[0]["model_id"] == "org/m1"
    assert models[1]["model_id"] == "org/m2"

def test_get_installed_models_no_dir(tmp_path):
    with patch("mlx_man.model_manager.HF_CACHE_DIR", tmp_path / "nonexistent"):
        assert get_installed_models() == []


def test_model_manager_exceptions_and_branches(mock_hf_cache):
    # calculate_model_disk_size OSError
    model_dir = get_model_cache_dir("org/m_err")
    model_dir.mkdir(parents=True, exist_ok=True)
    f = model_dir / "file.txt"
    f.write_text("123")

    # find_orphaned_shared_blobs not a dir
    blobs_dir = mock_hf_cache / "blobs"
    blobs_dir.mkdir(parents=True)
    (blobs_dir / "not_a_dir_blob").write_text("a")
    assert _find_orphaned_shared_blobs(model_dir) == []

    # find_orphaned_shared_blobs OSError
    subdir = blobs_dir / "01"
    subdir.mkdir(parents=True)
    refs_file = subdir / "1234.refs"
    refs_file.write_text("some/refs")
    with patch("pathlib.Path.read_text", side_effect=OSError("denied")):
        assert _find_orphaned_shared_blobs(model_dir) == []

    # delete_model_from_disk .locks OSError
    locks_dir = mock_hf_cache / ".locks" / model_dir.name
    locks_dir.mkdir(parents=True)
    with patch("shutil.rmtree") as mock_rmtree:
        def rmtree_side_effect(path, *args, **kwargs):
            if str(path) == str(locks_dir):
                raise OSError("denied")
        mock_rmtree.side_effect = rmtree_side_effect
        delete_model_from_disk("org/m_err")

    # delete_model_from_disk blobs OSError
    model_dir.mkdir(parents=True, exist_ok=True)
    refs_file.write_text(f"{model_dir.name}/refs\n")
    blob_file = subdir / "1234"
    blob_file.write_text("data")
    with patch("pathlib.Path.unlink", side_effect=OSError("denied")):
        delete_model_from_disk("org/m_err")

    # get_installed_models invalid dirs
    (mock_hf_cache / "models--org").mkdir() # missing --
    (mock_hf_cache / "models--file").write_text("a")
    assert len(get_installed_models()) == 0

def test_model_manager_exceptions_retry(mock_hf_cache):
    # calculate_model_disk_size OSError
    model_dir = get_model_cache_dir("org/m_err2")
    model_dir.mkdir(parents=True, exist_ok=True)
    f = model_dir / "file.txt"
    f.write_text("123")
    
    original_stat = Path.stat
    def stat_mock(self, *args, **kwargs):
        if "file.txt" in str(self):
            raise OSError("denied")
        return original_stat(self, *args, **kwargs)
        
    with patch("pathlib.Path.stat", side_effect=stat_mock, autospec=True):
        assert calculate_model_disk_size(model_dir) == 0

def test_get_installed_models_short_name(mock_hf_cache):
    (mock_hf_cache / "models--").mkdir()
    assert get_installed_models() == []

def test_get_model_cache_dir_absolute_path():
    from mlx_man.model_manager import get_model_cache_dir
    from pathlib import Path
    assert get_model_cache_dir("/custom/path/model") == Path("/custom/path/model")

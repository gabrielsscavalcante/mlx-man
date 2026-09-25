from mlx_man.model_registry import (
    get_registry_entry_fuzzy,
    get_all_known_model_ids,
    get_models_by_role,
    get_all_roles,
    get_registry_entry
)

def test_get_registry_entry_fuzzy():
    # Test valid
    entry = get_registry_entry_fuzzy("qwq")
    assert entry is not None
    assert "QwQ" in entry["name"]
    
    # Test invalid
    assert get_registry_entry_fuzzy("doesnotexist999") is None

def test_get_all_known_model_ids():
    ids = get_all_known_model_ids()
    assert len(ids) > 10
    assert "mlx-community/QwQ-32B-4bit" in ids

def test_get_models_by_role():
    reasoning = get_models_by_role("reasoning")
    assert len(reasoning) > 0
    assert "mlx-community/QwQ-32B-4bit" in reasoning
    
    empty = get_models_by_role("nonexistent_role")
    assert len(empty) == 0

def test_get_all_roles():
    roles = get_all_roles()
    assert "reasoning" in roles
    assert "builder" in roles
    assert "general" in roles

def test_get_registry_entry():
    assert get_registry_entry("mlx-community/QwQ-32B-4bit") is not None
    assert get_registry_entry("invalid") is None

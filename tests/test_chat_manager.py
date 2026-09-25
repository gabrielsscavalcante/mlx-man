import pytest
import os
import json
from pathlib import Path
from mlx_man.chat_manager import ChatSession, save_session, load_session, get_all_sessions, delete_session, export_session, CHATS_DIR

@pytest.fixture(autouse=True)
def mock_chats_dir(monkeypatch, tmp_path):
    import mlx_man.chat_manager
    monkeypatch.setattr(mlx_man.chat_manager, "CHATS_DIR", tmp_path / "chats")
    
def test_chat_session_dict():
    session = ChatSession("id1", "model1", "2024", [{"role": "user", "content": "hi"}])
    d = session.to_dict()
    assert d["session_id"] == "id1"
    
    s2 = ChatSession.from_dict(d)
    assert s2.model_id == "model1"
    assert s2.messages[0]["content"] == "hi"

def test_save_load_delete_session():
    session = ChatSession("id1", "model1", "2024", [])
    save_session(session)
    
    s2 = load_session("id1")
    assert s2.session_id == "id1"
    
    delete_session("id1")
    assert load_session("id1") is None
    
def test_get_all_sessions():
    s1 = ChatSession("id1", "m", "2024", [])
    s2 = ChatSession("id2", "m", "2025", [])
    save_session(s1)
    save_session(s2)
    
    # Also add an invalid JSON file to test error handling
    import mlx_man.chat_manager
    with open(mlx_man.chat_manager.CHATS_DIR / "bad.json", "w") as f:
        f.write("not json")
        
    sessions = get_all_sessions()
    assert len(sessions) == 2
    assert sessions[0].session_id == "id2" # sorted reverse chronologically

def test_export_session(tmp_path):
    session = ChatSession("id1", "m", "2024", [{"role": "user", "content": "hi"}])
    
    md_path = tmp_path / "export.md"
    export_session(session, str(md_path), "markdown")
    assert md_path.exists()
    content = md_path.read_text()
    assert "👤 You" in content
    assert "hi" in content
    
    json_path = tmp_path / "export.json"
    export_session(session, str(json_path), "json")
    assert json_path.exists()
    assert json.loads(json_path.read_text())["model_id"] == "m"

def test_export_session_new_folder(tmp_path):
    session = ChatSession("id1", "m", "2024", [])
    new_dir = tmp_path / "new_folder"
    md_path = new_dir / "export.md"
    export_session(session, str(md_path), "markdown")
    assert md_path.exists()

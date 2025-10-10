from pathlib import Path
from pypia_ctl.envtools import ensure_env_file, generate_env_text

def test_generate_env_text_returns_string():
    txt = generate_env_text()
    assert "PIA_PROTOCOL" in txt

def test_ensure_env_file_creates(tmp_path: Path):
    p = tmp_path / ".env"
    ensure_env_file(p)
    assert p.exists()
    content = p.read_text()
    assert "PIA_DEFAULT_REGION" in content

def test_ensure_env_file_merges_without_overwrite(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("PIA_PROTOCOL=openvpn\n", encoding="utf-8")
    ensure_env_file(p)
    after = p.read_text()
    # existing kept
    assert "PIA_PROTOCOL=openvpn" in after
    # new keys appended
    assert "PIA_DEFAULT_REGION" in after

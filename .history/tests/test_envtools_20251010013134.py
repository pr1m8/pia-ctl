from pathlib import Path
from pypia_ctl.envtools import generate_env_text, ensure_env_file, parse_env, DEFAULT_ENV

def test_generate_env_text_includes_defaults_and_extra(tmp_path: Path):
    txt = generate_env_text({"FOO": "bar"})
    assert txt.endswith("\n")
    assert "PIA_PROTOCOL=" in txt
    assert "FOO=bar" in txt

def test_ensure_env_file_creates_and_is_idempotent(tmp_path: Path):
    p = tmp_path / ".env"
    ensure_env_file(p)
    first = p.read_text()
    ensure_env_file(p)
    second = p.read_text()
    assert first == second
    d = parse_env(p)
    assert d.get("PIA_DEFAULT_REGION") == "auto"

def test_ensure_env_file_preserves_existing(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("PIA_PROTOCOL=openvpn\n", encoding="utf-8")
    ensure_env_file(p)
    d = parse_env(p)
    assert d["PIA_PROTOCOL"] == "openvpn"
    # and still added missing proxy auth keys
    for k in ("PIA_PROXY__USERNAME", "PIA_PROXY__PASSWORD"):
        assert k in d

def test_parse_env_ignores_comments_and_blanks(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("# x\nA=1\n\nB=2\nC=\n", encoding="utf-8")
    d = parse_env(p)
    assert d == {"A": "1", "B": "2", "C": ""}

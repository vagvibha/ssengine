"""`content_root:` in site_config.yaml moves where content sections,
topics/ and assets/ are read from, without changing any output path."""
import copy
import shutil

from conftest import SITE_CONFIG, make_site, read_yaml, run_script
from test_generate_dict_cli import standard_texts


def _site_under(tmp_path, content_root):
    """The standard site, with its content moved under `content_root`."""
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["content_root"] = content_root
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    base = site / content_root
    base.mkdir(parents=True)
    shutil.move(str(site / "kavya"), str(base / "kavya"))
    (base / "topics" / "cat").mkdir(parents=True)
    (base / "topics" / "cat" / "meta.yaml").write_text("title: वर्गः\n", encoding="utf-8")
    (base / "topics" / "cat" / "dhvani.md").write_text("---\ntitle: ध्वनिः\n---\nविषयः\n", encoding="utf-8")
    (base / "assets" / "audio").mkdir(parents=True)
    (base / "assets" / "audio" / "a.mp3").write_bytes(b"x")
    return site


def test_build_reads_from_content_root(tmp_path):
    site = _site_under(tmp_path, "contents")
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert "does not exist" not in r.stderr
    docs = site / "docs"
    # output paths (and so URLs) are the same as without content_root
    assert (docs / "kavya" / "padya" / "ka" / "01.md").exists()
    assert (docs / "topics" / "cat" / "dhvani.md").exists()
    assert (docs / "assets" / "audio" / "a.mp3").exists()
    assert not (docs / "contents").exists()
    assert "contents/" not in (site / "mkdocs.yml").read_text(encoding="utf-8")


def test_dict_reads_from_content_root(tmp_path):
    site = _site_under(tmp_path, "contents")
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    assert (site / "dict" / "meta.yaml").exists()           # dict/ stays at the repo root
    assert read_yaml(site / "dict" / "meta.yaml")["dictionaries"]
    assert not (site / "contents" / "dict").exists()


def _config_error(tmp_path, value):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["content_root"] = value
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    return r.stderr


def test_missing_content_root_fails(tmp_path):
    assert "does not exist" in _config_error(tmp_path, "contnets")


def test_content_root_outside_repo_fails(tmp_path):
    assert "inside the repo" in _config_error(tmp_path, "../elsewhere")


def test_content_root_in_generated_dir_fails(tmp_path):
    (tmp_path / "docs").mkdir()
    assert "generated" in _config_error(tmp_path, "docs")


def test_empty_content_root_is_repo_root(tmp_path):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["content_root"] = ""
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert (site / "docs" / "kavya" / "padya" / "ka" / "01.md").exists()

"""The site layout: site settings and static files live in config/, the
engine is mounted at ssengine/ and run from the site root, and docs/ +
mkdocs.yml are entirely generated."""
import os
import subprocess
import sys

from conftest import ENGINE_SCRIPTS, SITE_CONFIG, make_site, run_script
from test_generate_dict_cli import standard_texts


def _site(tmp_path, **kw):
    return make_site(tmp_path, standard_texts(), **kw)


def _add_static(site):
    css = site / "config" / "stylesheets"
    js = site / "config" / "javascripts"
    (css / "fonts").mkdir(parents=True)
    js.mkdir(parents=True)
    (css / "custom.css").write_text("body { color: red; }\n", encoding="utf-8")
    (css / "fonts" / "f.css").write_text("/* font */\n", encoding="utf-8")
    (css / ".DS_Store").write_text("junk", encoding="utf-8")
    (js / "notes-toggle.js").write_text("// js\n", encoding="utf-8")


def test_static_dirs_copied_into_docs(tmp_path):
    site = _site(tmp_path)
    _add_static(site)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    docs = site / "docs"
    assert (docs / "stylesheets" / "custom.css").read_text(encoding="utf-8") == "body { color: red; }\n"
    assert (docs / "stylesheets" / "fonts" / "f.css").exists()
    assert (docs / "javascripts" / "notes-toggle.js").exists()
    assert not (docs / "stylesheets" / ".DS_Store").exists()


def test_static_dirs_refreshed_on_rerun(tmp_path):
    site = _site(tmp_path)
    _add_static(site)
    assert run_script(site, "generate_indices.py").returncode == 0
    (site / "config" / "stylesheets" / "custom.css").write_text("body { color: blue; }\n", encoding="utf-8")
    (site / "config" / "stylesheets" / "fonts" / "f.css").unlink()
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert "blue" in (site / "docs" / "stylesheets" / "custom.css").read_text(encoding="utf-8")
    assert not (site / "docs" / "stylesheets" / "fonts" / "f.css").exists()


def test_missing_static_dirs_warn(tmp_path):
    site = _site(tmp_path)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert not (site / "docs" / "stylesheets").exists()
    assert "config/stylesheets/custom.css not found" in r.stderr
    assert "config/javascripts/notes-toggle.js not found" in r.stderr


def test_present_static_files_dont_warn(tmp_path):
    site = _site(tmp_path)
    _add_static(site)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert "not found" not in r.stderr


def test_stale_docs_output_removed(tmp_path):
    site = _site(tmp_path)
    stale = site / "docs" / "removed-section" / "page.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    (site / "docs" / "about.md").write_text("old about", encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert not stale.exists()
    assert not (site / "docs" / "about.md").exists()
    assert (site / "docs" / "index.md").exists()


def test_mkdocs_yml_header_says_fully_generated(tmp_path):
    site = _site(tmp_path)
    assert run_script(site, "generate_indices.py").returncode == 0
    head = (site / "mkdocs.yml").read_text(encoding="utf-8").split("nav:")[0]
    assert "safe to edit" not in head
    assert "don't commit it" in head


def _old_scripts_file(site, name):
    (site / "scripts").mkdir(exist_ok=True)
    (site / "scripts" / name).write_text("{}\n", encoding="utf-8")


def _old_layout_fails(site, script, expect):
    marker = site / "docs" / "keep.md"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("x", encoding="utf-8")
    r = run_script(site, script)
    assert r.returncode != 0
    assert "ConfigError" in r.stderr and expect in r.stderr, r.stderr
    assert marker.exists()  # failed before anything was deleted


def test_site_config_left_in_scripts_fails(tmp_path):
    site = _site(tmp_path)
    _old_scripts_file(site, "site_config.yaml")
    _old_layout_fails(site, "generate_indices.py", "config/site_config.yaml")


def test_gloss_types_left_in_scripts_fails(tmp_path):
    site = _site(tmp_path)
    _old_scripts_file(site, "gloss_types.yaml")
    _old_layout_fails(site, "generate_indices.py", "config/gloss_types.yaml")


def test_generate_dict_refuses_old_layout_too(tmp_path):
    site = _site(tmp_path)
    _old_scripts_file(site, "site_config.yaml")
    _old_layout_fails(site, "generate_dict.py", "config/site_config.yaml")


def test_hand_maintained_docs_stylesheets_not_deleted(tmp_path):
    site = _site(tmp_path)
    css = site / "docs" / "stylesheets" / "custom.css"
    css.parent.mkdir(parents=True)
    css.write_text("mine", encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "config/stylesheets/" in r.stderr, r.stderr
    assert css.read_text(encoding="utf-8") == "mine"


def test_hand_maintained_docs_javascripts_not_deleted(tmp_path):
    site = _site(tmp_path)
    js = site / "docs" / "javascripts" / "a.js"
    js.parent.mkdir(parents=True)
    js.write_text("mine", encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "config/javascripts/" in r.stderr, r.stderr
    assert js.exists()


def test_content_root_inside_config_rejected(tmp_path):
    cfg = dict(SITE_CONFIG, content_root="config/contents")
    site = _site(tmp_path, site_config=cfg)
    (site / "config" / "contents").mkdir()
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "can't be inside config/" in r.stderr, r.stderr


def test_mkdocs_yml_points_at_ssengine(tmp_path):
    site = _site(tmp_path)
    assert run_script(site, "generate_indices.py").returncode == 0
    mk = read_yaml_unsafe(site / "mkdocs.yml")
    assert mk["hooks"] == ["ssengine/scripts/mkdocs_hooks.py"]
    macros = next(p["macros"] for p in mk["plugins"] if isinstance(p, dict) and "macros" in p)
    assert macros["module_name"] == "ssengine/scripts/macros_env"
    assert (site / mk["hooks"][0]).is_file()
    assert (site / (macros["module_name"] + ".py")).is_file()


def read_yaml_unsafe(path):
    """mkdocs.yml has a !!python/name tag, so plain safe_load can't read it."""
    import yaml
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.UnsafeLoader)


def _run_from(cwd, script_path):
    return subprocess.run([sys.executable, str(script_path)], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8")


def test_run_from_outside_repo_root_fails(tmp_path):
    site = _site(tmp_path / "site")
    sub = site / "kavya"
    r = _run_from(sub, site / "ssengine" / "scripts" / "generate_indices.py")
    assert r.returncode != 0
    assert "run the engine from the site's repo root" in r.stderr, r.stderr
    assert not (sub / "docs").exists()


def test_engine_not_mounted_at_ssengine_fails(tmp_path):
    site = _site(tmp_path / "site")
    os.unlink(site / "ssengine")
    (site / "scripts").mkdir()
    os.symlink(ENGINE_SCRIPTS.parent, site / "scripts" / "ssengine")  # the old mount point
    marker = site / "docs" / "keep.md"
    marker.parent.mkdir()
    marker.write_text("x", encoding="utf-8")
    r = _run_from(site, site / "scripts" / "ssengine" / "scripts" / "generate_indices.py")
    assert r.returncode != 0
    assert "must be mounted at" in r.stderr and "git mv scripts/ssengine ssengine" in r.stderr, r.stderr
    assert marker.exists()


def test_other_engine_copy_fails(tmp_path):
    """ssengine/ exists but the engine running is a different copy: the
    generated mkdocs.yml would load hooks from code other than what built it."""
    site = _site(tmp_path / "site")
    os.unlink(site / "ssengine")
    (site / "ssengine" / "scripts").mkdir(parents=True)
    r = _run_from(site, ENGINE_SCRIPTS / "generate_indices.py")
    assert r.returncode != 0
    assert "must be mounted at" in r.stderr, r.stderr

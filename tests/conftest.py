"""
Shared test harness for the ssengine scripts.

Two kinds of test live in this directory:

* In-process unit tests import the engine modules directly. The engine
  reads `config/site_config.yaml`/`config/gloss_types.yaml` at import
  time, relative to the current directory (the site root — see the ROOT
  comment in generate_indices.py), so before importing anything we
  chdir into a small fixture site made just for these tests, then
  chdir back.

* End-to-end tests (`make_site` + `run_script`) build a throwaway site on
  disk that is wired up the same way the real content repos are: this
  engine repo is mounted at `<site>/ssengine` (a symlink standing in for
  the git submodule), and the site's own site_config.yaml and
  gloss_types.yaml go in `<site>/config/`. Then the real script runs in a
  subprocess, from the site root: `python ssengine/scripts/<script>`.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ENGINE_REPO = Path(__file__).resolve().parent.parent
ENGINE_SCRIPTS = ENGINE_REPO / "scripts"

# Gloss types used by both the in-process fixture site and make_site()
# unless a test overrides them. Mirrors the kinds of entries real sites
# use: no label, a fixed label, a label from an attribute, and a type
# routed through a non-default div class.
GLOSS_TYPES = {
    "supported_css_styles": ["notes", "anvaya", "tika", "claim"],
    "types": [
        {"data_type": "notes", "css_style": "notes"},
        {"data_type": "anvaya", "css_style": "anvaya", "label": "अन्वयः"},
        {"data_type": "tika", "css_style": "tika", "label_from_attr": "data-name"},
        {"data_type": "claim", "css_style": "claim", "class": "vada", "label": "पक्षः"},
    ],
}

SITE_CONFIG = {
    "content_sections": [
        {
            "dir": "kavya",
            "h1_label": "काव्यम्",
            "text_groups": [
                {"dir": "padya", "h2_label": "पद्यम्"},
                {"dir": "nataka", "h2_label": "नाटकम्"},
            ],
        }
    ],
    "dictionaries": [
        {"name": "Kavya", "folder": "kavya"},
        {"name": "Nataka", "folder": "plays"},
    ],
}


def _write_yaml(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# In-process import of the engine
# ---------------------------------------------------------------------------

_IMPORT_SITE = Path(tempfile.mkdtemp(prefix="ssengine-import-site-"))
_write_yaml(_IMPORT_SITE / "config" / "site_config.yaml", SITE_CONFIG)
_write_yaml(_IMPORT_SITE / "config" / "gloss_types.yaml", GLOSS_TYPES)
os.symlink(ENGINE_REPO, _IMPORT_SITE / "ssengine")

_saved_cwd = os.getcwd()
os.chdir(_IMPORT_SITE)
sys.path.insert(0, str(ENGINE_SCRIPTS))
try:
    import generate_indices  # noqa: E402,F401  (import for its side effects)
    import dict_extract  # noqa: E402,F401
    import dict_render  # noqa: E402,F401
    import generate_dict  # noqa: E402,F401
finally:
    os.chdir(_saved_cwd)


@pytest.fixture
def gloss_types() -> dict[str, dict]:
    """The fixture site's gloss types, keyed by data_type (same shape as
    Text.effective_gloss_types)."""
    return {t["data_type"]: dict(t) for t in GLOSS_TYPES["types"]}


# ---------------------------------------------------------------------------
# End-to-end helpers
# ---------------------------------------------------------------------------

def make_site(root: Path, texts: dict[str, dict], site_config: dict | None = None,
              gloss_types: dict | None = None) -> Path:
    """Build a site under `root`.

    `texts` maps a text dir (e.g. "kavya/padya/ks") to
        {"meta": {...}, "chapters": {"01": {"meta": {...} | None, "files": {"01.md": "..."}}}}
    """
    root.mkdir(parents=True, exist_ok=True)
    os.symlink(ENGINE_REPO, root / "ssengine")
    _write_yaml(root / "config" / "site_config.yaml", SITE_CONFIG if site_config is None else site_config)
    _write_yaml(root / "config" / "gloss_types.yaml", GLOSS_TYPES if gloss_types is None else gloss_types)

    for text_dir, spec in texts.items():
        d = root / text_dir
        _write_yaml(d / "meta.yaml", spec["meta"])
        for ch_slug, ch in spec.get("chapters", {}).items():
            ch_dir = d / ch_slug
            ch_dir.mkdir(parents=True, exist_ok=True)
            if ch.get("meta"):
                _write_yaml(ch_dir / "meta.yaml", ch["meta"])
            for fname, content in ch["files"].items():
                (ch_dir / fname).write_text(content, encoding="utf-8")
    return root


def run_script(site: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, f"ssengine/scripts/{script}", *args],
        cwd=site, capture_output=True, text=True, encoding="utf-8",
    )


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))

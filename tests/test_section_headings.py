"""Chapter `title:` (formerly `chapter_name:`) and the headings on
sections-mode section pages: a frontmatter page title, an automatic
`## <section title>`, `skip_title:`, and the `#`/`##` checks."""
import pytest

import generate_indices as gi
from conftest import make_site, run_script

TEXT = "kavya/padya/ka"
DOCS = "docs/kavya/padya/ka"


def build(tmp_path, files, chapter_meta=None, text_meta=None):
    meta = {"chapter_display_style": "sections"} if chapter_meta is None else chapter_meta
    texts = {TEXT: {"meta": text_meta or {"title": "कथा"},
                    "chapters": {"01": {"meta": meta, "files": files}}}}
    site = make_site(tmp_path, texts)
    return site, run_script(site, "generate_indices.py")


# ---------------------------------------------------------------------------
# A. chapter `title:`
# ---------------------------------------------------------------------------

def test_chapter_title_is_nav_label(tmp_path):
    site, r = build(tmp_path, {"01.md": "अ\n"},
                    chapter_meta={"title": "प्रथमः सर्गः"})
    assert r.returncode == 0, r.stderr
    page = (site / DOCS / "01.md").read_text(encoding="utf-8")
    assert "# कथा — प्रथमः सर्गः\n" in page
    assert "प्रथमः सर्गः" in (site / "mkdocs.yml").read_text(encoding="utf-8")


def test_chapter_name_is_rejected_with_rename_hint(tmp_path):
    site, r = build(tmp_path, {"01.md": "अ\n"}, chapter_meta={"chapter_name": "प्रथमः"})
    assert r.returncode != 0
    assert "chapter_name was renamed to title" in r.stderr, r.stderr


def test_chapter_name_rejected_in_validate_chapter_meta():
    with pytest.raises(gi.ConfigError, match="renamed to title"):
        gi.validate_chapter_meta({"chapter_name": "x"}, "m")
    gi.validate_chapter_meta({"title": "x", "dict": {"title": "y"}}, "m")


# ---------------------------------------------------------------------------
# B. section pages
# ---------------------------------------------------------------------------

def test_section_page_gets_frontmatter_title_and_h2(tmp_path):
    files = {"a.md": "---\ntitle: अ-भागः\n---\n### उपशीर्षकम्\n\nअ\n", "b.md": "ब\n"}
    site, r = build(tmp_path, files)
    assert r.returncode == 0, r.stderr
    a = (site / DOCS / "01" / "a.md").read_text(encoding="utf-8")
    assert a.startswith("---\ntitle: कथा — अध्यायः 1 — अ-भागः\n---\n<div class=\"sv-topnav\"")
    assert "\n## अ-भागः\n" in a and "\n### उपशीर्षकम्\n" in a
    assert "\n# " not in a
    # no title: frontmatter -> file stem
    b = (site / DOCS / "01" / "b.md").read_text(encoding="utf-8")
    assert b.startswith("---\ntitle: कथा — अध्यायः 1 — b\n---\n") and "\n## b\n" in b
    # landing page keeps its H1 and TOC labels
    landing = (site / DOCS / "01" / "index.md").read_text(encoding="utf-8")
    assert "# कथा — अध्यायः 1\n" in landing and "- [अ-भागः](a.md)" in landing


def test_title_with_yaml_special_characters_is_quoted(tmp_path):
    files = {"a.md": "---\ntitle: \"[१]: अ # ब\"\n---\nअ\n"}
    site, r = build(tmp_path, files)
    assert r.returncode == 0, r.stderr
    a = (site / DOCS / "01" / "a.md").read_text(encoding="utf-8")
    fm, _ = gi.split_frontmatter(a)
    assert fm["title"] == "कथा — अध्यायः 1 — [१]: अ # ब"


def test_skip_title_omits_auto_heading(tmp_path):
    files = {"a.md": "---\ntitle: अ-भागः\nskip_title: true\n---\n## स्वशीर्षकम्\n\nअ\n"}
    site, r = build(tmp_path, files)
    assert r.returncode == 0, r.stderr
    a = (site / DOCS / "01" / "a.md").read_text(encoding="utf-8")
    assert a.startswith("---\ntitle: कथा — अध्यायः 1 — अ-भागः\n---\n")
    assert "## अ-भागः" not in a and "\n## स्वशीर्षकम्\n" in a
    landing = (site / DOCS / "01" / "index.md").read_text(encoding="utf-8")
    assert "- [अ-भागः](a.md)" in landing


@pytest.mark.parametrize("value", ['"true"', "1", "yes please"])
def test_skip_title_must_be_bool(tmp_path, value):
    site, r = build(tmp_path, {"a.md": f"---\nskip_title: {value}\n---\nअ\n"})
    assert r.returncode != 0 and "skip_title should be true or false" in r.stderr, r.stderr


@pytest.mark.parametrize("body, skip, message", [
    ("# शीर्षकम्\n", "false", "a '#' heading isn't allowed"),
    ("# शीर्षकम्\n", "true", "a '#' heading isn't allowed"),
    ("अ\n\n## शीर्षकम्\n", "false", "a '##' heading isn't allowed here"),
    ("<notes>\n## शीर्षकम्\n</notes>\n", "false", "a '##' heading isn't allowed here"),
])
def test_bad_heading_levels_fail(tmp_path, body, skip, message):
    site, r = build(tmp_path, {"a.md": f"---\nskip_title: {skip}\n---\n{body}"})
    assert r.returncode != 0 and message in r.stderr, r.stderr
    assert "a.md" in r.stderr


def test_headings_in_fences_are_ignored(tmp_path):
    body = "```\n# not a heading\n## nor this\n```\n\n~~~~\n```\n# still inside\n~~~~\n\n### ok\n"
    site, r = build(tmp_path, {"a.md": body})
    assert r.returncode == 0, r.stderr


def test_full_chapter_mode_is_unchanged(tmp_path):
    files = {"01.md": "# शीर्षकम्\n\n## उप\n\nअ\n"}
    site, r = build(tmp_path, files, chapter_meta={})
    assert r.returncode == 0, r.stderr
    page = (site / DOCS / "01.md").read_text(encoding="utf-8")
    assert "# कथा — अध्यायः 1\n" in page and not page.startswith("---")


# ---------------------------------------------------------------------------
# Unit: atx_heading_levels
# ---------------------------------------------------------------------------

def test_atx_heading_levels():
    body = "\n".join([
        "# one",          # 1
        "#hashtag",       # 2 not a heading
        "   ## indented", # 3
        "    # code",     # 4 indented code, not a heading
        "```python",      # 5
        "# in fence",     # 6
        "````",           # 7 closes (longer run of same char)
        "###",            # 8 empty heading
        "~~~",            # 9
        "```",            # 10 different char: doesn't close
        "## inside",      # 11
        "~~~",            # 12 closes
        "###### six",     # 13
        "####### seven",  # 14 not a heading
    ])
    assert [(n, lvl) for n, lvl, _ in gi.atx_heading_levels(body)] == [(1, 1), (3, 2), (8, 3), (13, 6)]

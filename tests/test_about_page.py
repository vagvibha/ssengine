"""Optional `about.md` at the content root: copied to docs/about.md with the
Home pill, linked from a footer line on the home page, never added to nav."""
from conftest import SITE_CONFIG, make_site, run_script

TEXTS = {"kavya/padya/ka": {"meta": {"title": "तर्कसङ्ग्रहः"},
                            "chapters": {"01": {"files": {"01.md": "क\n"}}}}}


def build(tmp_path, about=None, site_config=None):
    site = make_site(tmp_path, TEXTS, site_config=site_config)
    if about is not None:
        (site / "about.md").write_text(about, encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    return site


def test_about_page_written_and_linked(tmp_path):
    site = build(tmp_path, "---\ntitle: परिचयः\n---\n# विषये\n\nपाठः {{ page.meta.title }}\n")
    page = (site / "docs" / "about.md").read_text(encoding="utf-8")
    assert page.startswith("---\ntitle: परिचयः\n---\n")          # frontmatter kept, first
    assert '<div class="sv-topnav"' in page and "(index.md)" in page
    assert page.index("sv-topnav") < page.index("# विषये")
    assert "पाठः {{ page.meta.title }}" in page

    home = (site / "docs" / "index.md").read_text(encoding="utf-8")
    assert '<div class="sv-home-footer"' in home
    assert "[विषये](about.md)" in home
    assert "about.md" not in (site / "mkdocs.yml").read_text(encoding="utf-8")


def test_about_label_override(tmp_path):
    cfg = {**SITE_CONFIG, "labels": {"about_nav_label": "About"}}
    site = build(tmp_path, "# About\n", site_config=cfg)
    assert "[About](about.md)" in (site / "docs" / "index.md").read_text(encoding="utf-8")


def test_no_about_page(tmp_path):
    site = build(tmp_path)
    assert not (site / "docs" / "about.md").exists()
    assert "sv-home-footer" not in (site / "docs" / "index.md").read_text(encoding="utf-8")


def test_removed_about_page_is_cleaned(tmp_path):
    site = build(tmp_path, "# About\n")
    (site / "about.md").unlink()
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert not (site / "docs" / "about.md").exists()

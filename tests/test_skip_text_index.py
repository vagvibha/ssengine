"""`skip_text_index: true` in a text's meta.yaml: a single-chapter text gets
no TOC page, and every link to the text goes straight to its chapter."""
import yaml

from conftest import SITE_CONFIG, make_site, run_script

TEXT = "kavya/padya/ka"
OUT = "kavya/padya/ka"


def build(tmp_path, chapters, site_config=None, **meta):
    texts = {TEXT: {"meta": {"title": "तर्कसङ्ग्रहः", "author": "अन्नंभट्टः", **meta}, "chapters": chapters}}
    return make_site(tmp_path, texts, site_config=site_config)


ONE = {"01": {"files": {"01.md": "प्रथमः-भागः\n", "02.md": "द्वितीयः-भागः\n"}}}


def text_nav_entry(site):
    text = (site / "mkdocs.yml").read_text(encoding="utf-8")
    nav = yaml.safe_load(text[:text.index("\nhooks:")])["nav"]  # the static part has !!python tags
    section = next(e["काव्यम्"] for e in nav if "काव्यम्" in e)
    group = next(e["पद्यम्"] for e in section if "पद्यम्" in e)
    return group[0]["तर्कसङ्ग्रहः"]


def test_skip_text_index_links_straight_to_chapter(tmp_path):
    site = build(tmp_path, ONE, skip_text_index=True)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    docs = site / "docs"

    assert not (docs / OUT / "index.md").exists()
    page = (docs / OUT / "01.md").read_text(encoding="utf-8")
    assert "# तर्कसङ्ग्रहः\n" in page                     # H1 is the text title only
    assert "अन्नंभट्टः" not in page                         # no author line
    assert "प्रथमः-भागः" in page and "द्वितीयः-भागः" in page
    assert "../../index.md" in page                        # Up -> section index
    assert "../../../index.md" in page                     # Home

    assert f"({OUT}/01.md)" in (docs / "index.md").read_text(encoding="utf-8")
    assert "(padya/ka/01.md)" in (docs / "kavya" / "index.md").read_text(encoding="utf-8")
    assert text_nav_entry(site) == f"{OUT}/01.md"


def test_skip_text_index_with_sections_mode(tmp_path):
    chapters = {"01": {"meta": {"chapter_display_style": "sections"}, "files": ONE["01"]["files"]}}
    site = build(tmp_path, chapters, skip_text_index=True)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    docs = site / "docs" / OUT

    assert not (docs / "index.md").exists()
    landing = (docs / "01" / "index.md").read_text(encoding="utf-8")
    assert "# तर्कसङ्ग्रहः\n" in landing
    assert "../../../index.md" in landing                  # Up -> section index (one level deeper)
    section_page = (docs / "01" / "01.md").read_text(encoding="utf-8")
    assert "# तर्कसङ्ग्रहः — 01\n" in section_page          # section page: text — section
    assert "⬆ तर्कसङ्ग्रहः](index.md)" in section_page
    assert text_nav_entry(site) == f"{OUT}/01/index.md"


def test_skip_text_index_needs_exactly_one_chapter(tmp_path):
    chapters = {"01": {"files": {"01.md": "क\n"}}, "02": {"files": {"01.md": "ख\n"}}}
    site = build(tmp_path, chapters, skip_text_index=True)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "skip_text_index: true needs exactly one" in r.stderr


def test_ignored_chapter_does_not_count(tmp_path):
    chapters = {**ONE, "02": {"meta": {"ignore": True}, "files": {"01.md": "ख\n"}}}
    site = build(tmp_path, chapters, skip_text_index=True)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert text_nav_entry(site) == f"{OUT}/01.md"


def test_default_keeps_text_index(tmp_path):
    site = build(tmp_path, ONE)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    docs = site / "docs" / OUT
    assert (docs / "index.md").exists()
    assert "# तर्कसङ्ग्रहः — अध्यायः 1\n" in (docs / "01.md").read_text(encoding="utf-8")
    assert isinstance(text_nav_entry(site), list)


def test_quoted_value_is_an_error(tmp_path):
    site = build(tmp_path, ONE, skip_text_index="true")
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "skip_text_index should be true or false" in r.stderr


SITE_SKIP = {**SITE_CONFIG, "skip_text_index": True}
TWO = {"01": {"files": {"01.md": "क\n"}}, "02": {"files": {"01.md": "ख\n"}}}


def test_site_default_applies_to_every_text(tmp_path):
    site = build(tmp_path, ONE, site_config=SITE_SKIP)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert not (site / "docs" / OUT / "index.md").exists()
    page = (site / "docs" / OUT / "01.md").read_text(encoding="utf-8")
    assert "# तर्कसङ्ग्रहः\n" in page
    assert "प्रथमः-भागः" in page and "द्वितीयः-भागः" in page   # all *.md collated on one page
    assert text_nav_entry(site) == f"{OUT}/01.md"


def test_text_false_overrides_site_default(tmp_path):
    site = build(tmp_path, TWO, site_config=SITE_SKIP, skip_text_index=False)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert (site / "docs" / OUT / "index.md").exists()


def test_site_default_still_needs_one_chapter(tmp_path):
    site = build(tmp_path, TWO, site_config=SITE_SKIP)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "skip_text_index: true needs exactly one" in r.stderr


def test_quoted_site_value_is_an_error(tmp_path):
    site = build(tmp_path, ONE, site_config={**SITE_CONFIG, "skip_text_index": "true"})
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "skip_text_index should be true or false" in r.stderr

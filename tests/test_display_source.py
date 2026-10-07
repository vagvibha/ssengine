"""`display_source: true` (site default, text override): a text's `source:`
is shown in small print at the bottom of its TOC page as `मूलम् – A, B, C`."""
from conftest import SITE_CONFIG, make_site, run_script

TEXT = "kavya/padya/ka"
ONE = {"01": {"files": {"01.md": "प्रथमः-भागः\n"}}}


def build(tmp_path, site_config=None, chapters=ONE, **meta):
    texts = {TEXT: {"meta": {"title": "तर्कसङ्ग्रहः", **meta}, "chapters": chapters}}
    return make_site(tmp_path, texts, site_config=site_config)


def toc_page(site):
    return (site / "docs" / TEXT / "index.md").read_text(encoding="utf-8")


def run_ok(site):
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    return toc_page(site)


def test_list_source_shown_at_bottom(tmp_path):
    page = run_ok(build(tmp_path, source=["A", "B", "C"], display_source=True))
    line = '<p class="sv-text-source">मूलम् – A, B, C</p>'
    assert line in page
    assert page.rstrip().endswith(line)  # after the chapter list


def test_string_source(tmp_path):
    page = run_ok(build(tmp_path, source="निर्णयसागरमुद्रणालयः", display_source=True))
    assert '<p class="sv-text-source">मूलम् – निर्णयसागरमुद्रणालयः</p>' in page


def test_off_by_default(tmp_path):
    page = run_ok(build(tmp_path, source=["A"]))
    assert "sv-text-source" not in page


def test_site_default_and_text_override(tmp_path):
    site_on = {**SITE_CONFIG, "display_source": True}
    page = run_ok(build(tmp_path / "a", site_config=site_on, source=["A"]))
    assert "sv-text-source" in page
    page = run_ok(build(tmp_path / "b", site_config=site_on, source=["A"], display_source=False))
    assert "sv-text-source" not in page


def test_no_or_empty_source_shows_nothing(tmp_path):
    assert "sv-text-source" not in run_ok(build(tmp_path / "a", display_source=True))
    assert "sv-text-source" not in run_ok(build(tmp_path / "b", display_source=True, source=["", " "]))


def test_label_from_site_config(tmp_path):
    cfg = {**SITE_CONFIG, "labels": {**SITE_CONFIG.get("labels", {}), "source_label": "आधारः"}}
    page = run_ok(build(tmp_path, site_config=cfg, source="A", display_source=True))
    assert "आधारः – A</p>" in page


def test_links_and_html_stay_plain_text(tmp_path):
    page = run_ok(build(tmp_path, source=["[Archive](https://x.org)", "<b>B</b> & C"], display_source=True))
    # raw HTML block: Markdown isn't applied inside, and HTML is escaped
    assert "मूलम् – [Archive](https://x.org), &lt;b&gt;B&lt;/b&gt; &amp; C</p>" in page


def test_mapping_source_is_an_error(tmp_path):
    site = build(tmp_path, source={"a": 1}, display_source=True)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "should be a string or a list of strings" in r.stderr


def test_skip_text_index_shows_nothing(tmp_path):
    site = build(tmp_path, source="A", display_source=True, skip_text_index=True)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert not (site / "docs" / TEXT / "index.md").exists()
    assert "sv-text-source" not in "".join(
        p.read_text(encoding="utf-8") for p in (site / "docs").rglob("*.md"))


def test_display_source_must_be_bool(tmp_path):
    r = run_script(build(tmp_path, source="A", display_source="true"), "generate_indices.py")
    assert r.returncode != 0
    assert "display_source should be true or false" in r.stderr

"""`topic_display_style: sections` on a multi-file topic: a landing page
at the usual topic path, one page per part, and separate definitions and
references pages."""
import copy

import pytest

import generate_indices as gi
from conftest import SITE_CONFIG, _write_yaml, make_site, run_script

CHAPTER = (
    '<topic name="माया" context="प्रसङ्गः">पाठः</topic>\n\n'
    '<topic name="माया" define="अविद्या">अविद्या-लक्षणम्</topic>\n'
)
CH_REL = "kavya/padya/ka/01.md"
LANDING = "topics/cat/maya.md"


def build(tmp_path, meta=None, parts=None, chapter=CHAPTER):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    texts = {"kavya/padya/ka": {"meta": {"title": "क"}, "chapters": {"01": {"files": {"01.md": chapter}}}}}
    site = make_site(tmp_path, texts, site_config=cfg)
    cat = site / "topics" / "cat"
    _write_yaml(cat / "meta.yaml", {"title": "वर्गः"})
    _write_yaml(cat / "maya" / "meta.yaml",
                {"title": "माया", "topic_display_style": "sections"} if meta is None else meta)
    if parts is None:
        parts = {
            "01.md": "---\ntitle: प्रथमः\norder: 1\n---\nप्रथम-पाठः\n",
            "02.md": "---\norder: 2\n---\n# स्वकीयः शीर्षकः\n\nद्वितीय-पाठः\n",
            "03.md": "---\norder: 3\n---\nतृतीय-पाठः\n",
        }
    for name, content in parts.items():
        (cat / "maya" / name).write_text(content, encoding="utf-8")
    return site, run_script(site, "generate_indices.py")


def read(site, rel):
    return (site / "docs" / rel).read_text(encoding="utf-8")


def exists(site, rel):
    return (site / "docs" / rel).exists()


def test_landing_page_lists_parts_then_tables(tmp_path):
    site, r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    landing = read(site, LANDING)
    assert "# माया" in landing
    parts = ["- [प्रथमः](maya/01.md)", "- [02](maya/02.md)", "- [03](maya/03.md)"]
    extras = ["- [परिभाषाः](maya/_definitions.md)", "- [सन्दर्भाः](maya/_references.md)"]
    positions = [landing.index(x) for x in parts + extras]
    assert positions == sorted(positions)
    # the two lists are kept apart
    assert "<!-- -->" in landing[positions[2]:positions[3]]
    # none of the content is on the landing page itself
    assert "प्रथम-पाठः" not in landing and "अविद्या-लक्षणम्" not in landing


def test_part_pages(tmp_path):
    site, r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    p1, p2, p3 = (read(site, f"topics/cat/maya/0{i}.md") for i in (1, 2, 3))

    assert "# माया — प्रथमः" in p1 and "प्रथम-पाठः" in p1
    assert "# स्वकीयः शीर्षकः" in p2 and "# माया —" not in p2  # own heading kept, none added
    assert "# माया — 03" in p3

    up = f"[⬆ माया]({gi.rel_link('topics/cat/maya/01.md', LANDING)})"
    assert up in p1
    nxt = gi.raw_html_href("topics/cat/maya/01.md", "topics/cat/maya/02.md")
    assert f'href="{nxt}">→' in p1 and "←" not in p1
    assert "←" in p2 and "→" in p2
    assert "←" in p3 and "→" not in p3


def test_definitions_and_references_pages(tmp_path):
    site, r = build(tmp_path)
    assert r.returncode == 0, r.stderr

    defs = read(site, "topics/cat/maya/_definitions.md")
    assert "# माया — परिभाषाः" in defs and "अविद्या-लक्षणम्" in defs
    href = gi.raw_html_href("topics/cat/maya/_definitions.md", CH_REL)
    assert f'href="{href}#tp2"' in defs
    assert "←" not in defs and "→" not in defs

    refs = read(site, "topics/cat/maya/_references.md")
    assert "# माया — सन्दर्भाः" in refs
    assert f"({gi.rel_link('topics/cat/maya/_references.md', CH_REL)}#tp1) — " in refs
    assert "←" not in refs and "→" not in refs


def test_chapter_jump_link_and_nav_point_at_landing(tmp_path):
    site, r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    jump = gi.raw_html_href(CH_REL, LANDING)
    assert f'class="sv-topic-jump" href="{jump}"' in read(site, CH_REL)
    mk = (site / "mkdocs.yml").read_text(encoding="utf-8")
    assert LANDING in mk and "maya/01.md" not in mk and "_definitions" not in mk


def test_empty_tables_get_no_page_or_link(tmp_path):
    site, r = build(tmp_path, chapter="केवलः पाठः\n")
    assert r.returncode == 0, r.stderr
    landing = read(site, LANDING)
    assert "_definitions" not in landing and "_references" not in landing and "<!-- -->" not in landing
    assert not exists(site, "topics/cat/maya/_definitions.md")
    assert not exists(site, "topics/cat/maya/_references.md")


def test_custom_headings_used_for_table_pages(tmp_path):
    meta = {"title": "माया", "topic_display_style": "sections",
            "definitions_heading": "लक्षणानि", "references_heading": "उल्लेखाः"}
    site, r = build(tmp_path, meta=meta)
    assert r.returncode == 0, r.stderr
    landing = read(site, LANDING)
    assert "- [लक्षणानि](maya/_definitions.md)" in landing and "- [उल्लेखाः](maya/_references.md)" in landing
    assert "# माया — लक्षणानि" in read(site, "topics/cat/maya/_definitions.md")


def test_single_page_is_the_default(tmp_path):
    site, r = build(tmp_path, meta={"title": "माया"})
    assert r.returncode == 0, r.stderr
    landing = read(site, LANDING)
    assert "प्रथम-पाठः" in landing and "तृतीय-पाठः" in landing and "अविद्या-लक्षणम्" in landing
    assert not exists(site, "topics/cat/maya")


@pytest.mark.parametrize("name", ["_definitions.md", "_references.md", "index.md"])
def test_reserved_part_names_are_an_error(tmp_path, name):
    site, r = build(tmp_path, parts={"01.md": "a\n", name: "b\n"})
    assert r.returncode != 0
    assert name in r.stderr and "reserved" in r.stderr


def test_reserved_names_are_fine_in_single_page_mode(tmp_path):
    site, r = build(tmp_path, meta={"title": "माया"}, parts={"index.md": "a\n"})
    assert r.returncode == 0, r.stderr


def test_unknown_display_style_is_an_error(tmp_path):
    site, r = build(tmp_path, meta={"title": "माया", "topic_display_style": "chapters"})
    assert r.returncode != 0
    assert "topic_display_style 'chapters'" in r.stderr


def test_single_file_topic_cannot_set_display_style(tmp_path):
    site, r = build(tmp_path, meta={"title": "माया"})
    (site / "topics" / "cat" / "other.md").write_text(
        "---\ntitle: अन्यः\ntopic_display_style: sections\n---\nx\n", encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "topic_display_style" in r.stderr

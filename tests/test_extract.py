"""`<extract href=... heading=... types=.../>`: pulling a passage from
another section file of the same text instead of duplicating it."""
import copy

import pytest

from conftest import SITE_CONFIG, _write_yaml, make_site, run_script

TEXT = "kavya/padya/ka"

SRC_01 = """---
title: प्रथमः
---
<div class="shloka">
कारिका-एकम् ।
</div>

वृत्ति-पाठः <topic name="माया">विषय-पाठः</topic>

<notes>
टिप्पणी-पाठः
</notes>

<anvaya>अन्वय-पाठः</anvaya>

<notes>
### सारः

सार-पाठः <dict syns="क">कोश-पाठः</dict>

### अन्यः

अन्य-पाठः
</notes>
"""


def build(tmp_path, files_01, sections=True, extra_chapters=None, ch01_meta=None):
    meta = ch01_meta if ch01_meta is not None else (
        {"chapter_display_style": "sections"} if sections else {"title": "प्रथमः"})
    chapters = {"01": {"meta": meta, "files": files_01}}
    chapters.update(extra_chapters or {})
    texts = {TEXT: {"meta": {"title": "क", "default_shloka_type": "karika", "default_class": "notes",
                             "dict": {"folder": "kavya"}},
                    "chapters": chapters}}
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    site = make_site(tmp_path, texts, site_config=cfg)
    _write_yaml(site / "topics" / "cat" / "meta.yaml", {"title": "वर्गः"})
    (site / "topics" / "cat" / "maya.md").write_text("---\ntitle: माया\n---\nपाठः\n", encoding="utf-8")
    return site, run_script(site, "generate_indices.py")


def read(site, rel):
    return (site / "docs" / TEXT / rel).read_text(encoding="utf-8")


def test_heading_scope_in_sections_chapter(tmp_path):
    site, r = build(tmp_path, {"a.md": SRC_01, "z.md": '<extract href="a.md" heading="सारः"/>\n'})
    assert r.returncode == 0, r.stderr
    page = read(site, "01/z.md")
    assert "सार-पाठः" in page and "कोश-पाठः" in page
    assert "### सारः" not in page          # heading itself left out
    assert "अन्य-पाठः" not in page         # stops at the next same-level heading
    assert "टिप्पणी-पाठः" not in page
    assert "<dict" not in page
    assert '<p class="sv-extract-source"><a href="../a/">↗ प्रथमः</a></p>' in page
    assert "sv-extract-source-" not in page  # placeholder replaced


def test_types_filter_and_default_class_gaps(tmp_path):
    site, r = build(tmp_path, {"a.md": SRC_01, "z.md": '<extract href="a.md" types="karika, anvaya"/>\n'})
    assert r.returncode == 0, r.stderr
    page = read(site, "01/z.md")
    assert "कारिका-एकम्" in page and "अन्वय-पाठः" in page
    assert "वृत्ति-पाठः" not in page and "टिप्पणी-पाठः" not in page and "सार-पाठः" not in page
    # untagged text counts as the source chapter's default_class (notes here)
    site2, r2 = build(tmp_path / "b", {"a.md": SRC_01, "z.md": '<extract href="a.md" types="notes"/>\n'})
    assert r2.returncode == 0, r2.stderr
    page2 = read(site2, "01/z.md")
    assert "वृत्ति-पाठः" in page2 and "टिप्पणी-पाठः" in page2 and "सार-पाठः" in page2
    assert "कारिका-एकम्" not in page2 and "अन्वय-पाठः" not in page2


def test_pulled_shloka_not_in_table_and_topics_stripped(tmp_path):
    site, r = build(tmp_path, {"a.md": SRC_01, "z.md": '<extract href="a.md"/>\n'})
    assert r.returncode == 0, r.stderr
    page = read(site, "01/z.md")
    assert 'data-extracted="true"' in page and 'data-type="karika"' in page
    assert "विषय-पाठः" in page and "sv-topic-jump" not in page and "<topic" not in page
    assert "श्लोकसूची" in read(site, "01/a.md")
    assert "श्लोकसूची" not in page


def test_new_chapter_pulls_from_other_chapters(tmp_path):
    site, r = build(tmp_path, {"a.md": SRC_01}, sections=False, extra_chapters={
        "99": {"meta": {"title": "सारः"}, "files": {"01.md": '<extract href="../01/a.md" heading="सारः"/>\n'}},
    })
    assert r.returncode == 0, r.stderr
    page = read(site, "99.md")
    assert "सार-पाठः" in page
    assert '<a href="../01/#sec1">↗ प्रथमः — प्रथमः</a>' in page


@pytest.mark.parametrize("files, msg", [
    ({"a.md": SRC_01, "z.md": '<extract href="a.md" heading="नास्ति"/>\n'}, "no heading 'नास्ति'"),
    ({"a.md": SRC_01 + "\n### सारः\n", "z.md": '<extract href="a.md" heading="सारः"/>\n'}, "appears 2 times"),
    ({"a.md": SRC_01, "z.md": '<extract href="a.md" types="kosha"/>\n'}, "unknown type(s) kosha"),
    ({"a.md": SRC_01, "z.md": '<extract href="b.md"/>\n'}, "not a section file of this text"),
    ({"a.md": SRC_01, "z.md": '<extract href="z.md"/>\n'}, "can't extract from itself"),
    ({"a.md": SRC_01, "z.md": '<extract href="a.md" title="x"/>\n'}, "unknown attribute"),
    ({"a.md": SRC_01, "z.md": '<extract href="a.md">\n'}, "must be self-closing"),
    ({"a.md": '<extract href="b.md"/>\n', "b.md": "x\n", "z.md": '<extract href="a.md"/>\n'}, "can't be nested"),
])
def test_errors(tmp_path, files, msg):
    _, r = build(tmp_path, files)
    assert r.returncode != 0
    assert msg in r.stderr


def test_same_full_chapter_fails(tmp_path):
    _, r = build(tmp_path, {"a.md": SRC_01, "z.md": '<extract href="a.md"/>\n'}, sections=False)
    assert r.returncode != 0
    assert "full_chapter" in r.stderr


def test_dict_ignores_extract(tmp_path):
    cfg_meta = {"chapter_display_style": "sections", "dict": {"type": "notes"}}
    site, r = build(tmp_path, {"a.md": SRC_01, "z.md": '<extract href="a.md"/>\n'}, ch01_meta=cfg_meta)
    assert r.returncode == 0, r.stderr
    topic = (site / "docs" / "topics" / "cat" / "maya.md").read_text(encoding="utf-8")
    assert "01/a" in topic and "01/z" not in topic
    d = run_script(site, "generate_dict.py")
    assert d.returncode == 0, d.stderr
    outs = list((site / "dict").rglob("*.txt"))
    assert outs, list((site / "dict").rglob("*"))
    assert sum(f.read_text(encoding="utf-8").count("कोश-पाठः") for f in outs) == 1

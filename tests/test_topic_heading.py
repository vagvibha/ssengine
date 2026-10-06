"""`<topic heading="...">`: a citation scoped to one heading on a topic
page. The reference is listed at the end of that heading's section (not in
the main सन्दर्भाः list), and the ↗ in the text links to the heading."""
import copy
import re

import pytest

import generate_indices as gi
from conftest import SITE_CONFIG, _write_yaml, make_site, run_script

TOPIC = """---
title: प्रमाणवाक्यानि
---
## यन्मनसा न मनुते

टिप्पणी-अ

### उपवाक्यम्

उप-पाठः

## नेति नेति {#neti}

टिप्पणी-ब
"""
TOPIC_REL = "topics/cat/pv.md"
CH1 = "kavya/padya/ka/01.md"
CH2 = "kavya/padya/ka/02.md"
NAME = 'name="प्रमाणवाक्यानि"'
H1 = 'heading="यन्मनसा न मनुते"'


def build(tmp_path, chapters, topic=TOPIC, extra_topics=None, chapter_meta=None):
    """`chapters`: {"01": text}, or {"01": {"a.md": ..., ...}} with
    chapter_meta for a sections-mode chapter."""
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    chs = {}
    for slug, c in chapters.items():
        files = c if isinstance(c, dict) else {"01.md": c}
        chs[slug] = {"meta": chapter_meta, "files": files}
    texts = {"kavya/padya/ka": {"meta": {"title": "क"}, "chapters": chs}}
    site = make_site(tmp_path, texts, site_config=cfg)
    cat = site / "topics" / "cat"
    _write_yaml(cat / "meta.yaml", {"title": "वर्गः"})
    if topic is not None:
        (cat / "pv.md").write_text(topic, encoding="utf-8")
    (cat / "maya.md").write_text("---\ntitle: माया\n---\nविषयः\n", encoding="utf-8")
    for rel, content in (extra_topics or {}).items():
        f = cat / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, dict):
            _write_yaml(f, content)
        else:
            f.write_text(content, encoding="utf-8")
    return site, run_script(site, "generate_indices.py")


def ok(tmp_path, chapters, **kw):
    site, r = build(tmp_path, chapters, **kw)
    assert r.returncode == 0, r.stderr
    return site


def read(site, rel):
    return (site / "docs" / rel).read_text(encoding="utf-8")


def section_of(page, heading_line):
    """The text from `heading_line` up to the next `## ` heading (or end)."""
    start = page.index(heading_line)
    nxt = page.find("\n## ", start + len(heading_line))
    return page[start:] if nxt < 0 else page[start:nxt]


# ---------------------------------------------------------------------------
# Basic output
# ---------------------------------------------------------------------------

def test_paired_with_context(tmp_path):
    site = ok(tmp_path, {"01": f'<topic {NAME} {H1} context="के. १.५">यन्मनसा</topic>\n'})
    ch = read(site, CH1)
    assert ('<span id="tp1">यन्मनसा</span> <a class="sv-topic-jump" '
            'href="../../../../topics/cat/pv/#tph1" title="प्रमाणवाक्यानि">↗</a>') in ch
    page = read(site, TOPIC_REL)
    assert "## यन्मनसा न मनुते {#tph1}\n" in page
    # at the end of the heading's section, after its nested ### section
    sec = section_of(page, "## यन्मनसा न मनुते")
    assert sec.rstrip().endswith("उप-पाठः\n\n- के. १.५ — [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp1)")
    assert "सन्दर्भाः" not in page          # never in the main list
    assert "## नेति नेति {#neti}\n" in page  # untouched: nothing cites it


def test_self_closing_leaves_anchor_and_jump(tmp_path):
    site = ok(tmp_path, {"01": f'अ <topic {NAME} heading="नेति नेति"/> ब\n'})
    ch = read(site, CH1)
    assert ('अ <span id="tp1"></span> <a class="sv-topic-jump" '
            'href="../../../../topics/cat/pv/#neti" title="प्रमाणवाक्यानि">↗</a> ब') in ch
    page = read(site, TOPIC_REL)
    # author's own {#neti} reused, not doubled; last section -> end of body
    assert page.count("{#neti}") == 1 and "{#tph" not in page
    assert page.rstrip().endswith("टिप्पणी-ब\n\n- [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp1)")


def test_paired_body_is_never_the_label(tmp_path):
    long_body = "अ" * (gi.TOPIC_LABEL_MAX + 10)
    site = ok(tmp_path, {"01": f"<topic {NAME} {H1}>{long_body}</topic>\n"})
    page = read(site, TOPIC_REL)
    assert "- [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp1)" in page
    assert long_body not in page


def test_anchor_numbering_shared_with_other_tags(tmp_path):
    chapter = (f'<topic name="माया" context="क">अ</topic>\n\n'
               f'<topic {NAME} heading="नेति नेति"/>\n\n'
               f'<topic {NAME} {H1}>ब</topic>\n')
    site = ok(tmp_path, {"01": chapter})
    ch = read(site, CH1)
    assert ch.count('id="tp1"') == ch.count('id="tp2"') == ch.count('id="tp3"') == 1
    page = read(site, TOPIC_REL)
    assert "01.md#tp2)" in section_of(page, "## नेति नेति") and "01.md#tp3)" in section_of(page, "## यन्मनसा")


def test_plain_context_still_goes_to_main_list(tmp_path):
    chapter = (f'<topic {NAME} context="सामान्यम्">अ</topic>\n\n'
               f'<topic {NAME} {H1} context="विशेषः">ब</topic>\n')
    page = read(ok(tmp_path, {"01": chapter}), TOPIC_REL)
    main = page[page.index("## सन्दर्भाः"):]
    assert "सामान्यम्" in main and "विशेषः" not in main
    assert "- विशेषः — [क — अध्यायः 1]" in section_of(page, "## यन्मनसा")


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

def test_nested_headings_lists_innermost_first(tmp_path):
    chapter = (f'<topic {NAME} {H1} context="बाह्यम्">अ</topic>\n\n'
               f'<topic {NAME} heading="उपवाक्यम्" context="आन्तरम्">ब</topic>\n')
    page = read(ok(tmp_path, {"01": chapter}), TOPIC_REL)
    assert "### उपवाक्यम् {#tph2}\n" in page
    assert ("उप-पाठः\n\n- आन्तरम् — [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp2)\n\n<!-- -->\n\n"
            "- बाह्यम् — [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp1)\n\n## नेति नेति") in page


def test_list_goes_before_definitions_table(tmp_path):
    chapter = (f'<topic {NAME} heading="नेति नेति" context="बृ.">अ</topic>\n\n'
               f'<topic {NAME} define="पदम्">लक्षणम्</topic>\n')
    page = read(ok(tmp_path, {"01": chapter}), TOPIC_REL)
    assert page.index("- बृ. — [") < page.index("## परिभाषाः")


def test_closing_hashes_markup_and_fences(tmp_path):
    topic = ("---\ntitle: प्रमाणवाक्यानि\n---\n## **तत्त्वमसि** ##\n\nअ\n\n"
             "```\n## यन्मनसा न मनुते\n```\n")
    chapter = f'<topic {NAME} heading="**तत्त्वमसि**"/>\n'
    page = read(ok(tmp_path, {"01": chapter}, topic=topic), TOPIC_REL)
    assert "## **तत्त्वमसि** {#tph1}\n" in page
    # a heading inside a fence doesn't count
    site, r = build(tmp_path / "b", {"01": f"<topic {NAME} {H1}/>\n"}, topic=topic)
    assert r.returncode != 0 and "has no heading with the text 'यन्मनसा न मनुते'" in r.stderr


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------

def test_dedup(tmp_path):
    ch1 = (f'<topic {NAME} {H1}>अ</topic>\n\n'                  # tp1: no context -> dropped
           f'<topic {NAME} {H1} context="क">ब</topic>\n\n'      # tp2: kept
           f'<topic {NAME} {H1} context="क">ग</topic>\n\n'      # tp3: exact duplicate of tp2
           f'<topic {NAME} {H1} context="ख">घ</topic>\n')       # tp4: different context, kept
    ch2 = (f'<topic {NAME} {H1}>ङ</topic>\n\n'                  # other chapter: kept (tp1)
           f'<topic {NAME} {H1}/>\n')                          # exact duplicate of it
    page = read(ok(tmp_path, {"01": ch1, "02": ch2}), TOPIC_REL)
    items = re.findall(r"^- .*$", section_of(page, "## यन्मनसा"), re.M)
    assert items == [
        "- क — [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp2)",
        "- ख — [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp4)",
        "- [क — अध्यायः 2](../../kavya/padya/ka/02.md#tp1)",
    ]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

DUP_TOPIC = "---\ntitle: प्रमाणवाक्यानि\n---\n## अ\n\nक\n\n### अ\n\nख\n"


@pytest.mark.parametrize("chapter, topic, message", [
    (f'<topic {NAME} heading="अज्ञातम्">अ</topic>\n', TOPIC, "has no heading with the text 'अज्ञातम्'"),
    (f'<topic {NAME} heading="अ"/>\n', DUP_TOPIC, "has 2 headings with the text 'अ'"),
    (f'<topic {NAME} {H1} define="पदम्">अ</topic>\n', TOPIC, "heading= can't be combined with define="),
    (f'<topic {NAME} {H1} define="पदम्" entry="ज"/>\n', TOPIC, "heading= can't be combined with define="),
    (f'<topic name="प्रमाणवाक्यानि, माया" {H1}>अ</topic>\n', TOPIC, "heading= needs a single topic"),
    (f'<topic {NAME} heading=" ">अ</topic>\n', TOPIC, "heading= is empty"),
    (f'<topic {NAME} {H1} context="">अ</topic>\n', TOPIC, "context= is empty"),
])
def test_errors(tmp_path, chapter, topic, message):
    site, r = build(tmp_path, {"01": chapter}, topic=topic)
    assert r.returncode != 0 and message in r.stderr, r.stderr


def test_heading_with_entry_but_no_define_is_rejected(tmp_path):
    # entry= alone is meaningless for a heading-scoped tag too
    site, r = build(tmp_path, {"01": f'<topic {NAME} {H1} entry="ज"/>\n'})
    assert r.returncode != 0 and "entry= needs define=" in r.stderr, r.stderr


# ---------------------------------------------------------------------------
# Multi-file topics and sections-mode chapters
# ---------------------------------------------------------------------------

def multi_file(style):
    meta = {"title": "बहु"}
    if style:
        meta["topic_display_style"] = style
    return {
        "bahu/meta.yaml": meta,
        "bahu/01.md": "---\norder: 1\ntitle: प्रथमः\n---\n## आद्यम्\n\nअ\n",
        "bahu/02.md": "---\norder: 2\ntitle: द्वितीयः\n---\n## अन्त्यम्\n\nब\n",
    }


def test_multi_file_single_page(tmp_path):
    site = ok(tmp_path, {"01": '<topic name="बहु" heading="अन्त्यम्" context="स">अ</topic>\n'},
              extra_topics=multi_file(None))
    assert 'href="../../../../topics/cat/bahu/#tph2"' in read(site, CH1)
    page = read(site, "topics/cat/bahu.md")
    assert page.rstrip().endswith("## अन्त्यम् {#tph2}\n\nब\n\n- स — [क — अध्यायः 1](../../kavya/padya/ka/01.md#tp1)")


def test_multi_file_sections_topic(tmp_path):
    site = ok(tmp_path, {"01": '<topic name="बहु" heading="अन्त्यम्">अ</topic>\n'},
              extra_topics=multi_file("sections"))
    assert 'href="../../../../topics/cat/bahu/02/#tph2"' in read(site, CH1)
    part = read(site, "topics/cat/bahu/02.md")
    assert "## अन्त्यम् {#tph2}\n" in part
    assert part.rstrip().endswith("- [क — अध्यायः 1](../../../kavya/padya/ka/01.md#tp1)")
    assert "{#tph" not in read(site, "topics/cat/bahu/01.md")
    # heading-scoped references alone don't make a सन्दर्भाः page
    assert not (site / "docs/topics/cat/bahu/_references.md").exists()
    assert "सन्दर्भाः" not in read(site, "topics/cat/bahu.md")


def test_sections_mode_chapter_label_names_the_section(tmp_path):
    files = {"a.md": f"---\ntitle: अ-भागः\n---\n<topic {NAME} {H1} context=\"क\">अ</topic>\n"}
    site = ok(tmp_path, {"01": files}, chapter_meta={"chapter_display_style": "sections"})
    page = read(site, TOPIC_REL)
    assert "- क — [क — अध्यायः 1 — अ-भागः](../../kavya/padya/ka/01/a.md#tp1)" in page
    assert 'href="../../../../../topics/cat/pv/#tph1"' in read(site, "kavya/padya/ka/01/a.md")


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line, text, own_id", [
    ("## अ", "अ", None),
    ("###   अ ब  ", "अ ब", None),
    ("## अ ##", "अ", None),
    ("## अ#", "अ#", None),
    ("## अ {#x}", "अ", "x"),
    ("## अ {: #x .c }", "अ", "x"),
    ("## अ {.c}", "अ", None),
    ("## **अ** {#x}", "**अ**", "x"),
    ("## {{ x }}", "{{ x }}", None),
    ("## अ {ब}", "अ {ब}", None),
])
def test_heading_text_and_id(line, text, own_id):
    assert gi.heading_text_and_id(line) == (text, own_id)


def test_label_brackets_are_escaped():
    class R:
        preview, label, page_rel_out_file, anchor = "", "क [१]", "a/b.md", "tp1"
    t = gi.HeadingTarget("t/x.md", 0, 2, "अ", "tph1", False)
    t.refs = [R()]
    assert gi.heading_reference_lines(t, "t/x.md") == ["- [क \\[१\\]](../a/b.md#tp1)"]

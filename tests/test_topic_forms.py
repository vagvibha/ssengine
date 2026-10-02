"""<topic> rules: define= -> a definition (text from the body, or entry= when
self-closing); context= -> a reference labelled with it; a paired tag with
neither -> a reference labelled with its (short) body. Anything malformed
stops the build."""
import re

import pytest
from test_topic_multi_name import build, read

T0 = "topics/cat/t0.md"  # topic माया


def refs(page):
    """[(label, link)] of the सन्दर्भाः list on a topic page."""
    return re.findall(r"^- \[(.*?)\]\((.*?)\) — ", page, re.M)


def defs(page):
    """[(term, text)] of the परिभाषाः table."""
    return re.findall(r'class="sv-topic-term">(.*?)</td>\s*<td[^>]*>(?:<a [^>]*>)?(.*?)(?:</a>)?</td>', page, re.S)


def ok(tmp_path, chapter):
    site, r = build(tmp_path, chapter=chapter)
    assert r.returncode == 0, r.stderr
    return read(site, T0), read(site, "kavya/padya/ka/01.md")


# --- the six cases ---------------------------------------------------------

def test_self_closing_define_entry_is_definition_only(tmp_path):
    page, ch = ok(tmp_path, '<topic name="माया" define="य" entry="ज"/>\n')
    assert refs(page) == [] and [t for t, _ in defs(page)] == ["य"] and "●</span> ज</a>" in page
    assert "sv-topic-jump" not in ch and 'id="tp' not in ch


def test_paired_define_is_definition_only(tmp_path):
    page, ch = ok(tmp_path, '<topic name="माया" define="य">ज</topic>\n')
    assert refs(page) == [] and defs(page) and "ज" in defs(page)[0][1]
    assert 'id="tp1"' in ch and ch.count("sv-topic-jump") == 1


def test_self_closing_context_is_reference_to_page_top(tmp_path):
    page, ch = ok(tmp_path, '<topic name="माया" context="य"/>\n')
    assert defs(page) == []
    [(label, link)] = refs(page)
    assert label == "य" and "#" not in link
    assert "sv-topic-jump" not in ch and 'id="tp' not in ch


def test_paired_body_only_is_reference_labelled_by_body(tmp_path):
    page, _ = ok(tmp_path, '<topic name="माया">य <b>र</b></topic>\n')
    [(label, link)] = refs(page)
    assert label == "य र" and link.endswith("#tp1")
    assert defs(page) == []


def test_paired_define_and_context_adds_both(tmp_path):
    page, _ = ok(tmp_path, '<topic name="माया" define="य" context="क">ज</topic>\n')
    assert refs(page)[0][0] == "क" and refs(page)[0][1].endswith("#tp1")
    assert defs(page)[0][0] == "य" and "ज" in defs(page)[0][1]


def test_self_closing_define_entry_context_adds_both(tmp_path):
    page, _ = ok(tmp_path, '<topic name="माया" define="य" context="अ" entry="ज"/>\n')
    [(label, link)] = refs(page)
    assert label == "अ" and "#" not in link
    assert defs(page)[0][0] == "य"


# --- the extra case: context= wins over the body as the label ---------------

def test_paired_context_labels_reference_body_is_passage(tmp_path):
    page, ch = ok(tmp_path, '<topic name="माया" context="क">लम्बः पाठः</topic>\n')
    assert refs(page) == [("क", refs(page)[0][1])] and "लम्बः पाठः" in ch


def test_body_label_at_the_limit_is_fine(tmp_path):
    body = "क" * 70
    page, _ = ok(tmp_path, f'<topic name="माया">{body}</topic>\n')
    assert refs(page)[0][0] == body


# --- errors ----------------------------------------------------------------

@pytest.mark.parametrize("chapter, message", [
    ('<topic name="माया" define="य" entry="ज">ब</topic>', "entry= is only for the self-closing form"),
    ('<topic name="माया" define="य" source="ल">ब</topic>', "unknown attribute(s) source"),
    ('<topic name="माया" entry="ज"/>', "entry= needs define="),
    ('<topic name="माया" define="य"/>', "define= needs entry="),
    ('<topic name="माया"/>', "needs define= + entry="),
    ('<topic name="माया"></topic>', "empty body and no define=/context="),
    ('<topic name="माया" define="य"></topic>', "the body (the definition) is empty"),
    ('<topic name="माया">' + "क" * 71 + '</topic>', "71 characters (max 70)"),
    ('<topic name="माया" define="">ब</topic>', "define= is empty"),
    ('<topic name="माया" context=""/>', "context= is empty"),
    ('<topic context="क">ब</topic>', "no name="),
    ('<topic name="माया" context="क">अ <topic name="माया" context="ख">ब</topic></topic>', "can't nest"),
    ('ब</topic>', "no matching open"),
    ('<topic name="माया" context="क">ब', "never closed"),
])
def test_malformed_tag_stops_the_build(tmp_path, chapter, message):
    _, r = build(tmp_path, chapter=chapter + "\n")
    assert r.returncode != 0
    assert message in r.stderr, r.stderr[-400:]

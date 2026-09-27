"""`exclude_site: true` on a gloss type: its divs are left out of the
website (with their content), the dictionary is unaffected, and using an
excluded type as a chapter's default_class is an error."""
import copy

import pytest

import generate_indices as gi
from conftest import GLOSS_TYPES, SITE_CONFIG, _write_yaml, make_site, run_script


@pytest.fixture
def excl(gloss_types):
    """The fixture gloss types with `notes` excluded."""
    gloss_types["notes"] = {**gloss_types["notes"], "exclude_site": True}
    return gloss_types


def strip(text, gloss_types):
    return gi.strip_excluded_glosses(text, gloss_types)


# ---------------------------------------------------------------------------
# strip_excluded_glosses
# ---------------------------------------------------------------------------

def test_nothing_excluded_is_a_no_op(gloss_types):
    body = '<div class="gloss" data-type="notes">n</div>'
    assert strip(body, gloss_types) == body


def test_hand_written_div_removed_with_content(excl):
    body = 'अ\n\n<div class="gloss" data-type="notes">टिप्पणी</div>\n\nआ'
    assert strip(body, excl) == "अ\n\n\n\nआ"


def test_shorthand_after_expansion_removed(excl):
    body = gi.expand_gloss_shorthand("अ <notes>टिप्पणी</notes> आ", excl)
    assert strip(body, excl) == "अ  आ"


def test_other_types_kept(excl):
    body = '<anvaya>अन्वयः</anvaya><notes>n</notes><claim>c</claim>'
    out = strip(gi.expand_gloss_shorthand(body, excl), excl)
    assert out == '<div class="gloss" data-type="anvaya">अन्वयः</div><div class="vada" data-type="claim">c</div>'


# (A gloss-class div opening inside another gloss-class div is read by
# parse_divs as an implicit close of the first — see its docstring — so
# nesting is tested with divs of a different class.)

def test_everything_nested_inside_an_excluded_div_goes(excl):
    body = gi.expand_gloss_shorthand('<notes>a <claim>c</claim> <div class="x">y</div></notes>b', excl)
    assert strip(body, excl) == "b"


def test_excluded_div_nested_in_kept_one(gloss_types):
    gloss_types["claim"] = {**gloss_types["claim"], "exclude_site": True}
    body = gi.expand_gloss_shorthand("<notes>a <claim>c</claim> b</notes>", gloss_types)
    assert strip(body, gloss_types) == '<div class="gloss" data-type="notes">a  b</div>'


def test_excluded_div_inside_structural_div(excl):
    body = '<div class="dialog-block">अ <div class="gloss" data-type="notes">n</div></div>'
    assert strip(body, excl) == '<div class="dialog-block">अ </div>'


def test_excluded_type_on_non_default_class(gloss_types):
    gloss_types["claim"] = {**gloss_types["claim"], "exclude_site": True}
    body = gi.expand_gloss_shorthand("<claim>c</claim> <anvaya>x</anvaya>", gloss_types)
    assert strip(body, gloss_types) == ' <div class="gloss" data-type="anvaya">x</div>'


def test_boxed_type_removed_with_its_box(excl):
    excl["notes"]["boxed"] = "closed"
    body = gi.expand_gloss_shorthand("अ\n<notes>n</notes>\nआ", excl)
    assert "<details" in body
    assert strip(body, excl) == "अ\n\nआ"


def test_shloka_untouched(excl):
    body = '<div class="shloka">पद्यम्</div>'
    assert strip(body, excl) == body


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

CHAPTER = (
    "मूलम्\n\n"
    "<anvaya>दृश्यः-अन्वयः</anvaya>\n\n"
    '<notes>गुप्ता-टिप्पणी <topic name="विषयः" context="गुप्तः">गुप्तविषयः</topic></notes>\n\n'
    '<topic name="विषयः" context="दृश्यः">दृश्यविषयः</topic>\n'
)


def excl_gloss_types():
    gt = copy.deepcopy(GLOSS_TYPES)
    for t in gt["types"]:
        if t["data_type"] == "notes":
            t["exclude_site"] = True
    return gt


def build(tmp_path, texts, gloss_types=None):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    site = make_site(tmp_path, texts, site_config=cfg, gloss_types=gloss_types or excl_gloss_types())
    _write_yaml(site / "topics" / "cat" / "meta.yaml", {"title": "वर्गः"})
    (site / "topics" / "cat" / "vishaya.md").write_text("---\ntitle: विषयः\n---\nbody\n", encoding="utf-8")
    return site, run_script(site, "generate_indices.py")


def page(site, rel):
    return (site / "docs" / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("style", ["full_chapter", "sections"])
def test_excluded_gloss_not_published(tmp_path, style):
    texts = {"kavya/padya/ka": {"meta": {"title": "क"}, "chapters": {"01": {
        "meta": {"chapter_display_style": style}, "files": {"01.md": CHAPTER}}}}}
    site, r = build(tmp_path, texts)
    assert r.returncode == 0, r.stderr

    rel = "kavya/padya/ka/01.md" if style == "full_chapter" else "kavya/padya/ka/01/01.md"
    out = page(site, rel)
    assert "दृश्यः-अन्वयः" in out and "दृश्यविषयः" in out
    assert "गुप्ता-टिप्पणी" not in out and "गुप्तविषयः" not in out
    assert 'data-type="notes"' not in out

    # the topic inside the removed gloss registers no back-reference
    topic = page(site, "topics/cat/vishaya.md")
    assert "दृश्यः" in topic and "गुप्तः" not in topic


def test_book_gloss_types_entry_overrides_site_exclusion(tmp_path):
    texts = {
        "kavya/padya/ka": {"meta": {"title": "क"}, "chapters": {"01": {"files": {"01.md": CHAPTER}}}},
        "kavya/padya/kb": {"meta": {"title": "ख", "gloss_types": [{"data_type": "notes", "css_style": "notes"}]},
                           "chapters": {"01": {"files": {"01.md": CHAPTER}}}},
    }
    site, r = build(tmp_path, texts)
    assert r.returncode == 0, r.stderr
    assert "गुप्ता-टिप्पणी" not in page(site, "kavya/padya/ka/01.md")
    assert "गुप्ता-टिप्पणी" in page(site, "kavya/padya/kb/01.md")


def test_book_can_exclude_a_type_the_site_publishes(tmp_path):
    texts = {"kavya/padya/ka": {
        "meta": {"title": "क", "gloss_types": [{"data_type": "anvaya", "css_style": "anvaya", "exclude_site": True}]},
        "chapters": {"01": {"files": {"01.md": CHAPTER}}}}}
    site, r = build(tmp_path, texts, gloss_types=copy.deepcopy(GLOSS_TYPES))
    assert r.returncode == 0, r.stderr
    out = page(site, "kavya/padya/ka/01.md")
    assert "दृश्यः-अन्वयः" not in out and "गुप्ता-टिप्पणी" in out


def test_bad_exclude_site_value_is_an_error(tmp_path):
    gt = copy.deepcopy(GLOSS_TYPES)
    gt["types"][0]["exclude_site"] = "true"
    texts = {"kavya/padya/ka": {"meta": {"title": "क"}, "chapters": {"01": {"files": {"01.md": CHAPTER}}}}}
    site, r = build(tmp_path, texts, gloss_types=gt)
    assert r.returncode != 0
    assert "exclude_site" in r.stderr


@pytest.mark.parametrize("where", ["book", "chapter"])
def test_excluded_default_class_is_an_error(tmp_path, where):
    book_meta = {"title": "क", **({"default_class": "notes"} if where == "book" else {})}
    ch_meta = {"default_class": "notes"} if where == "chapter" else None
    texts = {"kavya/padya/ka": {"meta": book_meta, "chapters": {"01": {"meta": ch_meta, "files": {"01.md": "गद्यम्\n"}}}}}
    site, r = build(tmp_path, texts)
    assert r.returncode != 0
    assert "default_class 'notes'" in r.stderr and "exclude_site" in r.stderr


def test_chapter_default_class_can_avoid_the_error(tmp_path):
    texts = {"kavya/padya/ka": {"meta": {"title": "क", "default_class": "notes"},
                                "chapters": {"01": {"meta": {"default_class": "anvaya"}, "files": {"01.md": "गद्यम्\n"}}}}}
    site, r = build(tmp_path, texts)
    assert r.returncode == 0, r.stderr
    assert "गद्यम्" in page(site, "kavya/padya/ka/01.md")


def test_dictionary_ignores_exclude_site(tmp_path):
    texts = {"kavya/padya/ka": {"meta": {"title": "क", "dict": {"folder": "kavya"}}, "chapters": {"01": {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": '<dict syns="अ">प्रविष्टिः <notes>टिप्पणी</notes></dict>\n'}}}}}
    site = make_site(tmp_path, texts, gloss_types=excl_gloss_types())
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    assert "टिप्पणी" in (site / "dict" / "kavya" / "ka" / "01.txt").read_text(encoding="utf-8")

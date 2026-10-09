"""`skip-label="true"` on one gloss/vada instance drops its label (website
and dictionary alike), keeping its type, style and Show/Hide membership.
Ignored on a boxed type, whose label is the box's <summary>."""
import copy

import dict_render as dr
import generate_indices as gi
import pytest
from conftest import make_site, run_script


def render(text, gloss_types):
    body = gi.expand_gloss_shorthand(text, gloss_types)
    return gi.process_content_sections(body, "", gloss_types)


def boxed(gloss_types, key, value):
    gt = copy.deepcopy(gloss_types)
    gt[key]["boxed"] = value
    return gt


# ---------------------------------------------------------------------------
# Label resolution
# ---------------------------------------------------------------------------

def test_skips_fixed_label(gloss_types):
    assert gi.commentary_label("anvaya", ' skip-label="true"', gloss_types) == ""
    assert gi.commentary_label("claim", ' skip-label="true"', gloss_types) == ""  # vada class


def test_skips_label_from_attr(gloss_types):
    assert gi.commentary_label("tika", ' data-name="लोचनम्" skip-label="true"', gloss_types) == ""


def test_false_and_absent_keep_label(gloss_types):
    assert gi.commentary_label("anvaya", ' skip-label="false"', gloss_types) == "अन्वयः"
    assert gi.commentary_label("anvaya", "", gloss_types) == "अन्वयः"


def test_case_insensitive(gloss_types):
    assert gi.commentary_label("anvaya", ' Skip-Label="TRUE"', gloss_types) == ""


def test_bad_value_is_an_error(gloss_types):
    with pytest.raises(gi.ConfigError, match='skip-label="yes"'):
        gi.commentary_label("anvaya", ' skip-label="yes"', gloss_types)


def test_ignored_on_boxed_type(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    assert gi.commentary_label("tika", ' data-name="X" skip-label="true"', gt) == "X"
    out = gi.expand_gloss_shorthand('<tika data-name="X" skip-label="true">T</tika>', gt)
    assert "<summary>X</summary>" in out


# ---------------------------------------------------------------------------
# Website
# ---------------------------------------------------------------------------

def test_website_drops_only_the_label(gloss_types):
    plain = render("<claim>A</claim>", gloss_types)
    skipped = render('<claim skip-label="true">A</claim>', gloss_types)
    assert "<b>पक्षः</b>" in plain and "पक्षः" not in skipped
    # same classes (type, style, toggle membership) either way
    assert plain.replace("<b>पक्षः</b><br>", "") == skipped
    assert "skip-label" not in skipped  # build-time only


def test_website_longhand_div(gloss_types):
    out = render('<div class="gloss" data-type="anvaya" skip-label="true">A</div>', gloss_types)
    assert "अन्वयः" not in out and 'data-type="anvaya"' in out


def test_website_nested(gloss_types):
    out = render('<tika data-name="X">t1 <claim skip-label="true">c</claim> t2</tika>', gloss_types)
    assert "<b>X</b>" in out and "पक्षः" not in out


def test_resume_pattern(gloss_types):
    out = render('<tika data-name="X">one</tika>\n\nbreak\n\n<tika data-name="X" skip-label="true">two</tika>',
                 gloss_types)
    assert out.count("<b>X</b>") == 1


# ---------------------------------------------------------------------------
# Dictionary
# ---------------------------------------------------------------------------

def test_dict_notes_entry(gloss_types):
    out = dr.render_notes_entry('<div class="vada" data-type="claim" skip-label="true">आ</div>', gloss_types)
    assert "<b>" not in out and "<i>आ</i>" in out


def test_dict_shloka_gloss(gloss_types):
    group = ('<div class="gloss" data-type="tika" data-name="X">one</div>\n'
             '<div class="gloss" data-type="tika" data-name="X" skip-label="true">two</div>')
    _, blocks = dr.render_shloka_group(group, gloss_types)
    assert blocks == ["<b>X</b>\n<i>one</i>", "<i>two</i>"]


# ---------------------------------------------------------------------------
# End to end: a bad value fails the real build
# ---------------------------------------------------------------------------

def test_bad_value_fails_build(tmp_path):
    texts = {"kavya/padya/ks": {"meta": {"title": "कुमारसम्भवम्"},
                                "chapters": {"01": {"meta": None,
                                                    "files": {"01.md": '<notes skip-label="maybe">x</notes>\n'}}}}}
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and 'skip-label="maybe"' in r.stderr, r.stderr

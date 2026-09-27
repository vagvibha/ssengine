"""`boxed: open|closed` on a gloss type puts a <details> box, whose
<summary> is the type's label, INSIDE its SHORTHAND tag's div. The
dictionary build never boxes."""
import copy

import dict_extract as de
import dict_render as dr
import generate_indices as gi
import pytest
from conftest import GLOSS_TYPES, make_site, run_script
from test_generate_dict_cli import standard_texts


def boxed(gloss_types, key, value):
    gt = copy.deepcopy(gloss_types)
    gt[key]["boxed"] = value
    return gt


def render(text, gloss_types):
    body = gi.expand_gloss_shorthand(text, gloss_types)
    return gi.process_content_sections(body, "", gloss_types)


def test_open_box_with_label_from_attr(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    out = gi.expand_gloss_shorthand('<tika data-name="लोचनम्">T</tika>', gt)
    assert out == (
        '<div class="gloss" data-type="tika" data-name="लोचनम्" data-sv-boxed="true">\n'
        '<details markdown="1" open>\n<summary>लोचनम्</summary>\nT\n</details>\n</div>'
    )


def test_closed_box_has_no_open_attr_and_uses_fixed_label(gloss_types):
    gt = boxed(gloss_types, "anvaya", "closed")
    out = gi.expand_gloss_shorthand("<anvaya>A</anvaya>", gt)
    assert '<details markdown="1">\n<summary>अन्वयः</summary>\n' in out


def test_label_not_repeated_inside_box_and_marker_dropped(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    out = render('<tika data-name="लोचनम्">T</tika>', gt)
    assert out.count("लोचनम्") == 1                   # only in <summary>
    assert "<b>" not in out and "data-sv-boxed" not in out
    # the gloss div is outermost, so Show/Hide hides the whole box
    assert out.index('data-type="tika"') < out.index("<details") < out.index("</details>") < out.rindex("</div>")
    assert "sv-toggleable" in out


def test_no_label_gives_empty_summary(gloss_types):
    gt = boxed(gloss_types, "notes", "open")
    assert "<summary></summary>" in gi.expand_gloss_shorthand("<notes>n</notes>", gt)


def test_unboxed_type_unchanged(gloss_types):
    out = render('<tika data-name="लोचनम्">T</tika>', gloss_types)
    assert "<details" not in out and "<b>लोचनम्</b>" in out


def test_longhand_div_never_boxed(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    out = render('<div class="gloss" data-type="tika" data-name="लोचनम्">T</div>', gt)
    assert "<details" not in out and "<b>लोचनम्</b>" in out


def test_boxed_in_default_class_chapter_is_its_own_gloss(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    body = gi.expand_gloss_shorthand('Intro.\n\n<tika data-name="X">T</tika>\n\nAfter.', gt)
    out = gi.process_content_sections(body, "notes", gt)
    assert out.count('data-type="notes"') == 2  # Intro + After, the boxed tika between them
    tika = out.index('data-type="tika"')
    assert tika < out.index("<details") < out.index("</details>") < out.index("After.")


def test_bad_boxed_value_fails(tmp_path):
    gt = copy.deepcopy(GLOSS_TYPES)
    gt["types"][0]["boxed"] = "shut"
    site = make_site(tmp_path, standard_texts(), gloss_types=gt)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and "boxed: 'shut'" in r.stderr, r.stderr


# ---------------------------------------------------------------------------
# Dictionary: never boxed; hand-written <details> rules
# ---------------------------------------------------------------------------

def test_dictionary_build_never_boxes(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    out = gi.expand_gloss_shorthand('<tika data-name="X">T</tika>', gt, allow_boxing=False)
    assert out == '<div class="gloss" data-type="tika" data-name="X">T</div>'


def test_handwritten_details_in_dict_entry_is_an_error(gloss_types):
    with pytest.raises(de.DictSyntaxError, match="<details> inside a <dict> entry"):
        dr.render_notes_entry("x <details><summary>s</summary>y</details>", gloss_types, "t.md")


def test_handwritten_details_in_shloka_gloss_is_dropped(gloss_types):
    group = (
        '<div class="gloss" data-type="tika" data-name="X">keep<details><summary>s</summary>'
        "```mermaid\ngraph TD; A-->B\n```</details></div>\n"
        '<div class="gloss" data-type="notes">\n<details>\n<summary>s</summary>\nonly\n</details>\n</div>'
    )
    _, blocks = dr.render_shloka_group(group, gloss_types)
    assert blocks == ["<b>X</b>\n<i>keep</i>"]  # details gone; a gloss left empty by it is skipped


def test_boxed_gloss_in_all_dictionary_outputs(tmp_path):
    gt = copy.deepcopy(GLOSS_TYPES)
    next(t for t in gt["types"] if t["data_type"] == "tika")["boxed"] = "open"
    tika = '<tika data-name="लोचनम्">\nटीकापाठः\n</tika>'
    texts = {"kavya/padya/ka": {"meta": {"title": "क", "dict": {"folder": "kavya"}}, "chapters": {
        "01": {"meta": {"dict": {"type": "notes", "chapter_key": "KA1"}},
               "files": {"01.md": f'गद्यम् <dict syns="अ">प्रविष्टिः\n\n{tika}\n</dict>\n\n{tika}\n'}},
        "02": {"meta": {"dict": {"type": "shloka", "shloka_key_prefix": "KA2,1"}},
               "files": {"01.md": '<div class="shloka">\nपद्यम् ॥१॥\n</div>\n' + tika + "\n"}},
    }}}
    site = make_site(tmp_path, texts, gloss_types=gt)
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    out = {f.name: f.read_text(encoding="utf-8") for f in (site / "dict").rglob("*.txt")}
    assert set(out) == {"01.txt", "01-full.txt", "02.txt"}
    for name, text in out.items():
        assert "<details" not in text and "<summary" not in text, name
        assert "<b>लोचनम्</b>" in text and "टीकापाठः" in text, name
        assert text.count("लोचनम्") == text.count("<b>लोचनम्</b>"), name  # label once, not duplicated

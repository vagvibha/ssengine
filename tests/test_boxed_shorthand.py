"""`boxed: open|closed` on a gloss type wraps its SHORTHAND tag in a
<details> box whose <summary> is the type's label."""
import copy

import generate_indices as gi
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
        '<details markdown="1" open>\n<summary>लोचनम्</summary>\n'
        '<div class="gloss" data-type="tika" data-name="लोचनम्" data-sv-boxed="true">T</div>\n</details>'
    )


def test_closed_box_has_no_open_attr_and_uses_fixed_label(gloss_types):
    gt = boxed(gloss_types, "anvaya", "closed")
    out = gi.expand_gloss_shorthand("<anvaya>A</anvaya>", gt)
    assert out.startswith('<details markdown="1">\n<summary>अन्वयः</summary>\n')


def test_label_not_repeated_inside_box_and_marker_dropped(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    out = render('<tika data-name="लोचनम्">T</tika>', gt)
    assert out.count("लोचनम्") == 1                   # only in <summary>
    assert "<b>" not in out and "data-sv-boxed" not in out
    assert out.index("<summary>") < out.index('data-type="tika"') < out.index("</details>")


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


def test_boxed_inside_default_class_stays_whole(gloss_types):
    gt = boxed(gloss_types, "tika", "open")
    body = gi.expand_gloss_shorthand('Intro.\n\n<tika data-name="X">T</tika>\n\nAfter.', gt)
    out = gi.process_content_sections(body, "notes", gt)
    d_open, d_close = out.index("<details"), out.index("</details>")
    assert "</div>" not in out[d_open:out.index('data-type="tika"')]
    assert out.count('data-type="notes"') == 1 and d_close < out.rindex("</div>")


def test_bad_boxed_value_fails(tmp_path):
    gt = copy.deepcopy(GLOSS_TYPES)
    gt["types"][0]["boxed"] = "shut"
    site = make_site(tmp_path, standard_texts(), gloss_types=gt)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and "boxed: 'shut'" in r.stderr, r.stderr

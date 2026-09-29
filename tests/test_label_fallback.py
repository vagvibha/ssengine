"""A gloss type with both `label` and `label_from_attr`: an instance's own
attribute wins, the fixed label is the fallback when it's absent."""
import dict_render as dr
import generate_indices as gi

GT = {
    "objection": {"data_type": "objection", "class": "vada", "css_style": "flowing_text",
                  "label": "पूर्वपक्षः", "label_from_attr": "label"},
    "tika": {"data_type": "tika", "css_style": "basic_gloss", "label_from_attr": "data-name"},
    "notes": {"data_type": "notes", "css_style": "fine_print"},
}


def render(text):
    body = gi.expand_gloss_shorthand(text, GT)
    return gi.process_content_sections(body, "", GT)


def test_fixed_label_when_attr_absent():
    assert gi.commentary_label("objection", "", GT) == "पूर्वपक्षः"
    assert "<b>पूर्वपक्षः</b><br>" in render("<objection>आक्षेपः</objection>")


def test_attr_overrides_fixed_label():
    out = render('<objection label="कर्मकाण्डी">आक्षेपः</objection>')
    assert "<b>कर्मकाण्डी</b><br>" in out and "पूर्वपक्षः" not in out
    assert 'label="' not in out  # build-time only, never reaches the page


def test_blank_attr_falls_back():
    assert gi.commentary_label("objection", ' label="  "', GT) == "पूर्वपक्षः"


def test_attr_only_type_unchanged():
    assert gi.commentary_label("tika", ' data-name="लोचनम्"', GT) == "लोचनम्"
    assert gi.commentary_label("tika", "", GT) == ""
    assert gi.commentary_label("notes", "", GT) == ""


def test_dictionary_uses_same_fallback():
    fixed = dr.render_notes_entry('<div class="vada" data-type="objection">आ</div>', GT)
    own = dr.render_notes_entry('<div class="vada" data-type="objection" label="बौद्धः">आ</div>', GT)
    assert "<b>पूर्वपक्षः</b>" in fixed
    assert "<b>बौद्धः</b>" in own and "पूर्वपक्षः" not in own

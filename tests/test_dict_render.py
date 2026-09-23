"""dict_render: notes-entry rendering, shloka keys, shloka records
(pytest port of the module's own __main__ self-tests, plus edge cases)."""
import pytest

from dict_render import (
    ShlokaKeyError, extract_marker_numbers, parse_shloka_key_prefix, render_notes_entry,
    render_shloka_gloss_text, render_shloka_group, render_structural_divs, shloka_dict_key, shloka_record,
)

NOTES_ONLY = {"notes": {"class": "gloss", "css_style": "notes"}}
SHLOKA_TYPES = {
    "anvaya": {"class": "gloss", "css_style": "anvaya", "label": "अन्वयः"},
    "tika": {"class": "gloss", "css_style": "tika", "label_from_attr": "data-name"},
}


def test_notes_entry_worked_example():
    raw = (
        "[(ततः प्रविशति राजा)]{: .action}   \n"
        "**सूतः** – [(राजानं मृगं चावलोक्य)]{: .action} आयुष्मन् ।\n"
        '<div class="gloss" data-type="notes">\nअधिज्यकार्मुके = अध्यारोपितधनुषि । \n</div>'
    )
    out = render_notes_entry(raw, NOTES_ONLY)
    assert "**सूतः**" in out  # markdown bold untouched
    assert "<i>(ततः प्रविशति राजा)</i>" in out
    assert "<i>(राजानं मृगं चावलोक्य)</i>" in out
    assert out.endswith("<i>अधिज्यकार्मुके = अध्यारोपितधनुषि ।</i>")
    assert "<div" not in out and "data-type" not in out


def test_labeled_gloss():
    raw = '<div class="gloss" data-type="tika" data-name="सञ्जीविनी">अपीति ॥ ...</div>'
    assert render_notes_entry(raw, SHLOKA_TYPES) == "<b>सञ्जीविनी</b><i>अपीति ॥ ...</i>"


def test_structural_shloka_div_is_unwrapped():
    assert render_structural_divs('<div class="shloka">\nपद्यम् ॥१॥\n</div>', NOTES_ONLY) == "पद्यम् ॥१॥"


def test_non_action_span_left_alone():
    raw = "[x]{: .other}"
    assert render_notes_entry(raw, NOTES_ONLY) == raw


@pytest.mark.parametrize("prefix,key", [
    ("KS5,99", "e:KS5-03"),
    ("KS,9,99", "e:KS-9-03"),
    ("R,9,99,999", "e:R-5-09-003"),
])
def test_shloka_keys(prefix, key):
    assert shloka_dict_key("मृगानुसारिणं ...॥५।९।३॥", prefix) == key


def test_marker_uses_last_marker_and_devanagari_digits():
    assert extract_marker_numbers("a ॥१॥ b ॥ १२ - ३४ ॥") == [12, 34]


def test_prefix_parse():
    assert parse_shloka_key_prefix("KS,9,99") == ("KS", [1, 2])


@pytest.mark.parametrize("text,prefix,needle", [
    ("...॥५॥", "KS,9,99", "only has 1"),
    ("no marker", "KS,99", "no ॥"),
    ("...॥५॥", "KS", "needs a name"),
    ("...॥५॥", ",99", "no name"),
    ("...॥५॥", "KS,x", "not a plain digit-width"),
])
def test_shloka_key_errors(text, prefix, needle):
    with pytest.raises(ShlokaKeyError) as exc:
        shloka_dict_key(text, prefix, "k.md")
    assert needle in str(exc.value)


def test_gloss_text_blank_lines_and_soft_breaks():
    assert render_shloka_gloss_text("a  \nb\n\nc") == "a<br>\nb\n<br>\nc"


def test_shloka_record_worked_example():
    group = (
        '<div class="gloss" data-type="anvaya">\nत्वदावर्जित आरोहति ।\n</div>\n\n'
        '<div class="gloss" data-type="tika" data-name="सञ्जीविनी">\nअपीति ॥ गच्छतीत्यर्थः ।\n</div>'
    )
    anvaya, blocks = render_shloka_group(group, SHLOKA_TYPES, "s.md")
    assert anvaya == "त्वदावर्जित आरोहति"  # trailing danda dropped on "++" only
    assert blocks == [
        "<b>अन्वयः</b>\n<i>त्वदावर्जित आरोहति ।</i>",
        "<b>सञ्जीविनी</b>\n<i>अपीति ॥ गच्छतीत्यर्थः ।</i>",
    ]
    record = shloka_record("श्लोकः ॥३४॥", ["all"], ["सिञ्च्", "उक्ष्"], anvaya, blocks)
    assert record == (
        "श्लोकः ॥३४॥\n====\n- all\n+ सिञ्च्;उक्ष्\n++ त्वदावर्जित आरोहति\n"
        "<b>अन्वयः</b>\n<i>त्वदावर्जित आरोहति ।</i>\n<br>\n<b>सञ्जीविनी</b>\n<i>अपीति ॥ गच्छतीत्यर्थः ।</i>"
    )


def test_shloka_record_omits_empty_lines():
    anvaya, blocks = render_shloka_group('<div class="gloss" data-type="tika" data-name="X">y</div>', SHLOKA_TYPES)
    assert anvaya is None
    record = shloka_record("श्लोकः ॥१॥", [], ["a"], anvaya, blocks)
    assert record == "श्लोकः ॥१॥\n====\n+ a\n<b>X</b>\n<i>y</i>"

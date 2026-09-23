"""expand_gloss_shorthand: `<TYPE ...>...</TYPE>` -> `<div class=".." data-type="TYPE" ...>...</div>`."""
import generate_indices as gi


def expand(text, gloss_types, **kw):
    return gi.expand_gloss_shorthand(text, gloss_types, source_for_warning="t.md", **kw)


def test_basic_expansion(gloss_types):
    assert expand("<notes>x</notes>", gloss_types) == '<div class="gloss" data-type="notes">x</div>'


def test_attributes_pass_through_verbatim(gloss_types):
    out = expand('<tika data-name="सञ्जीविनी" toggle-hide="true">y</tika>', gloss_types)
    assert out == '<div class="gloss" data-type="tika" data-name="सञ्जीविनी" toggle-hide="true">y</div>'


def test_attribute_value_containing_gt(gloss_types):
    out = expand('<notes title="a > b">z</notes>', gloss_types)
    assert out == '<div class="gloss" data-type="notes" title="a > b">z</div>'


def test_type_with_custom_class(gloss_types):
    assert expand("<claim>c</claim>", gloss_types) == '<div class="vada" data-type="claim">c</div>'


def test_multiline_content_untouched(gloss_types):
    body = "<anvaya>\nपद १ ।\nपद २ ।\n</anvaya>"
    assert expand(body, gloss_types) == '<div class="gloss" data-type="anvaya">\nपद १ ।\nपद २ ।\n</div>'


def test_nested_shorthand_and_longhand(gloss_types):
    body = '<tika data-name="X">a <notes>n</notes> <div class="shloka">s</div> b</tika>'
    out = expand(body, gloss_types)
    assert out == (
        '<div class="gloss" data-type="tika" data-name="X">a '
        '<div class="gloss" data-type="notes">n</div> <div class="shloka">s</div> b</div>'
    )


def test_siblings(gloss_types):
    out = expand("<notes>1</notes>\n<anvaya>2</anvaya>", gloss_types)
    assert out.count("<div") == 2 and out.count("</div>") == 2
    assert 'data-type="anvaya">2</div>' in out


def test_unknown_tag_left_alone(gloss_types):
    body = "<summary>x</summary> <notesx>y</notesx>"
    assert expand(body, gloss_types) == body


def test_tag_name_is_case_sensitive(gloss_types):
    body = "<Notes>x</Notes>"
    assert expand(body, gloss_types) == body


def test_existing_longhand_untouched(gloss_types):
    body = '<div class="gloss" data-type="notes">x</div>'
    assert expand(body, gloss_types) == body


def test_unclosed_open_is_left_and_warns(gloss_types):
    before = len(gi.WARNINGS)
    body = "<notes>never closed"
    assert expand(body, gloss_types) == body
    assert any("never closed" in w for w in gi.WARNINGS[before:])


def test_stray_close_is_left_and_warns(gloss_types):
    before = len(gi.WARNINGS)
    body = "text </notes>"
    assert expand(body, gloss_types) == body
    assert any("no matching open" in w for w in gi.WARNINGS[before:])


def test_mismatched_close_does_not_mispair(gloss_types):
    # <notes> closed by </anvaya>: neither should be expanded
    body = "<notes>a</anvaya>"
    assert expand(body, gloss_types, warn_enabled=False) == body


def test_warn_disabled_is_silent(gloss_types):
    before = len(gi.WARNINGS)
    expand("<notes>x", gloss_types, warn_enabled=False)
    assert len(gi.WARNINGS) == before


def test_empty_gloss_types_is_noop():
    assert expand("<notes>x</notes>", {}) == "<notes>x</notes>"


def test_book_level_custom_type():
    types = {"bhavartha": {"data_type": "bhavartha", "css_style": "notes"}}
    assert expand("<bhavartha>b</bhavartha>", types) == '<div class="gloss" data-type="bhavartha">b</div>'

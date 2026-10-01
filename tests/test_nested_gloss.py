"""Gloss/vada shorthand tags nested inside another gloss — e.g. a
<bhashyam> holding its own <objection>/<refute> and <notes> — render on
the site and in the dictionary as a real nest, each with its own label,
style and Show/Hide class."""
import dict_render as dr
import generate_indices as gi

# css_style values are the fixture site's own supported_css_styles (see conftest).
GT = {
    "bhashyam": {"data_type": "bhashyam", "css_style": "anvaya", "label": "भाष्यम्", "hideable": False},
    "tika": {"data_type": "tika", "css_style": "tika", "label_from_attr": "data-name", "hideable": False},
    "notes": {"data_type": "notes", "css_style": "notes", "hideable": True},
    "objection": {"data_type": "objection", "class": "vada", "css_style": "claim",
                  "label": "पूर्वपक्षः", "label_from_attr": "label", "hideable": False},
    "refute": {"data_type": "refute", "class": "vada", "css_style": "tika",
               "label": "सिद्धान्तः", "label_from_attr": "label", "hideable": False},
}

PAGE = """<bhashyam>
abc
<objection>why X?</objection>
<notes>about the objection</notes>
<refute>because of Y</refute>
<notes>Y matters because of Z</notes>

more
</bhashyam>

<tika data-name="आनन्दगिरिः">
t1
<objection label="बौद्धः">why not W?</objection>
<refute>because V</refute>
t2
</tika>
"""


def render(text, default_class=""):
    return gi.process_content_sections(gi.expand_gloss_shorthand(text, GT), default_class, GT)


def test_nested_divs_render_inside_their_container():
    out = render(PAGE)
    tika_at = out.rindex("<div", 0, out.index('data-type="tika"'))
    bh, tk = out[:tika_at], out[tika_at:]
    # everything from the bhashyam — nested ones rendered (label + style) — in source
    # order and before the tika starts; the bhashyam's own text continues after them
    order = ['data-type="bhashyam"', "<b>भाष्यम्</b>", "abc", "<b>पूर्वपक्षः</b>", "why X?",
             "about the objection", "<b>सिद्धान्तः</b>", "because of Y", "Y matters", "more"]
    assert [bh.index(x) for x in order] == sorted(bh.index(x) for x in order)
    assert bh.count('"vada sv-style-claim"') == 1 and bh.count('"vada sv-style-tika"') == 1
    assert bh.count('"gloss sv-style-notes sv-toggleable"') == 2   # nested notes still hideable
    assert bh.count("sv-toggleable") == 2                           # ...and only they are
    assert bh.count("<div") == bh.count("</div>") == 5   # container + 4 nested, all closed before the tika
    assert "<b>बौद्धः</b>" in tk and "<b>सिद्धान्तः</b>" in tk and "t2" in tk
    assert "data-sv-closed" not in out and 'label="' not in out


def test_default_class_does_not_wrap_text_inside_a_container():
    out = render(PAGE, default_class="bhashyam")
    # only the container's own label — "abc"/"more"/"t1" are not re-wrapped
    assert out.count("<b>भाष्यम्</b>") == 1


def test_hand_written_same_class_div_still_implicitly_closes():
    body = ('<div class="gloss" data-type="bhashyam">a\n'
            '<div class="gloss" data-type="notes">n</div>\nb</div>')
    names = [gi.parse_attrs(n.attrs_str).get("data-type") for n in gi.parse_divs(body)]
    assert names == ["bhashyam", "notes"]  # legacy tolerance unchanged


def test_dictionary_notes_entry_renders_nested():
    raw = gi.expand_gloss_shorthand("<bhashyam>a <objection>q</objection> <notes>n</notes> b</bhashyam>",
                                    GT, allow_boxing=False)
    out = dr.render_notes_entry(raw, GT)
    assert out == "<b>भाष्यम्</b><i>a <b>पूर्वपक्षः</b><i>q</i> <i>n</i> b</i>"


def test_dictionary_full_chapter_keeps_or_drops_each_nested_type():
    body = gi.expand_gloss_shorthand("<bhashyam>a <objection>q</objection> <notes>n</notes> b</bhashyam>",
                                     GT, allow_boxing=False)
    dropped = {}
    out = dr.render_full_chapter_entry(body, GT, {"bhashyam", "objection"}, dropped)
    assert "<b>पूर्वपक्षः</b><i>q</i>" in out and ">n<" not in out and "b</i>" in out
    assert dropped == {"notes": 1}
    # dropping the container drops everything inside it
    assert dr.render_full_chapter_entry(body, GT, {"objection", "notes"}) == ""


def test_dictionary_shloka_entry_renders_nested():
    """dict.type: shloka — the glosses after a shloka become one block each;
    a gloss nested inside one is rendered inside that block."""
    group = gi.expand_gloss_shorthand(
        "<bhashyam>a <objection label=\"बौद्धः\">q</objection>\n\n<notes>n</notes> b</bhashyam>"
        "<notes>after</notes>", GT, allow_boxing=False)
    anvaya, blocks = dr.render_shloka_group(group, GT)
    assert anvaya is None
    assert blocks == [
        "<b>भाष्यम्</b>\n<i>a <b>बौद्धः</b><i>q</i>\n<br>\n<i>n</i> b</i>",
        "<i>after</i>",
    ]

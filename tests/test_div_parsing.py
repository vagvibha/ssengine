"""parse_divs / apply_splices / parse_attrs / split_frontmatter / as_list —
the low-level helpers everything else in the engine is built on."""
import pytest

import generate_indices as gi


def test_parse_divs_nesting():
    text = '<div class="a">x<div class="b">y</div>z</div>'
    [a] = gi.parse_divs(text)
    assert a.base_cls == "a" and len(a.children) == 1
    b = a.children[0]
    assert text[b.tag_end:b.inner_end] == "y"
    assert text[a.start:a.end] == text


def test_parse_divs_implicit_close_of_same_class_sibling():
    text = '<div class="shloka">one\n<div class="shloka">two</div>'
    nodes = gi.parse_divs(text)
    assert [text[n.tag_end:n.inner_end] for n in nodes] == ["one\n", "two"]


def test_parse_divs_unclosed_runs_to_eof_and_stray_close_ignored():
    text = '</div><div class="gloss">open'
    [n] = gi.parse_divs(text)
    assert n.inner_end == len(text) and n.end == len(text)


def test_parse_divs_multiple_classes():
    [n] = gi.parse_divs('<div class="Gloss extra" data-type="notes">x</div>')
    assert n.base_cls == "gloss" and n.has_class("extra")


def test_apply_splices_insert_and_replace():
    assert gi.apply_splices("abcdef", [(4, 6, "XY"), (1, 1, "-")]) == "a-bcdXY"


def test_apply_splices_overlap_raises():
    with pytest.raises(ValueError):
        gi.apply_splices("abcdef", [(0, 3, "x"), (2, 4, "y")])


def test_parse_attrs():
    assert gi.parse_attrs(' class="gloss" data-type="notes" data-name="क ख"') == {
        "class": "gloss", "data-type": "notes", "data-name": "क ख",
    }


def test_split_frontmatter():
    fm, body = gi.split_frontmatter("---\ntitle: x\norder: 2\n---\nbody\n")
    assert fm == {"title": "x", "order": 2} and body == "body\n"
    assert gi.split_frontmatter("no frontmatter") == ({}, "no frontmatter")


@pytest.mark.parametrize("value,expected", [
    (None, []), ("", []), ("a", ["a"]), (["a", " b "], ["a", "b"]),
])
def test_as_list(value, expected):
    assert gi.as_list(value) == expected

"""dict_extract: <dict>/<dictref> extraction (pytest port of the module's
own __main__ self-tests, plus a few more edge cases)."""
import pytest

from dict_extract import (
    DictSyntaxError, as_syn_list, extract_dict_and_ref_tags, resolve_dictrefs_in_text,
)


@pytest.mark.parametrize("value,expected", [
    ("a, b ,c", ["a", "b", "c"]),
    ("a;b", ["a", "b"]),
    ("a, ;b,", ["a", "b"]),
    ("", []),
])
def test_as_syn_list(value, expected):
    assert as_syn_list(value) == expected


def test_display_true_keeps_content_on_site():
    body = (
        '<dict syns="ज्या, अधिज्य, कार्मुक">\n'
        "text here\n"
        '<div class="gloss" data-type="notes">अधिज्यकार्मुके = ...</div>\n'
        "</dict>\ntrailing"
    )
    site, caps = extract_dict_and_ref_tags(body, "t1")
    assert "<dict" not in site and "</dict>" not in site
    assert "text here" in site and "trailing" in site
    [cap] = caps
    assert cap.display is True and not cap.self_closing
    assert cap.syns == ["ज्या", "अधिज्य", "कार्मुक"]
    assert "text here" in cap.raw_content and 'data-type="notes"' in cap.raw_content


def test_display_false_strips_content_from_site():
    site, caps = extract_dict_and_ref_tags('before <dict syns="दा" display="False">त्वयि</dict> after', "t2")
    assert site == "before  after"
    assert caps[0].display is False and caps[0].raw_content == "त्वयि"


def test_display_false_is_case_insensitive():
    site, caps = extract_dict_and_ref_tags('<dict syns="a" display="false">x</dict>', "t")
    assert site == "" and caps[0].display is False


def test_self_closing_entry():
    site, caps = extract_dict_and_ref_tags('<dict syns="सुभग" entry="सुभगसलिलावगाह, श्रवणसुभग"/>\nnext', "t3")
    assert site == "\nnext"
    assert caps[0].self_closing and caps[0].display is False
    assert caps[0].raw_content == "सुभगसलिलावगाह, श्रवणसुभग"


def test_self_closing_display_false_allowed():
    _, caps = extract_dict_and_ref_tags('<dict syns="a" entry="b" display="False"/>', "t")
    assert caps[0].raw_content == "b"


def test_dictref_inside_dict_resolves_to_link():
    site, caps = extract_dict_and_ref_tags('<dict syns="x">a <dictref text="इयेष" ref="iyeSha"/> b</dict>', "t4")
    assert "dictref" not in site and "a  b" in site
    assert caps[0].raw_content == 'a <a href="bword://iyeSha">इयेष</a> b'


def test_bare_dictref_outside_dict_is_stripped_without_capture():
    site, caps = extract_dict_and_ref_tags('x <dictref text="t" ref="r"/> y', "t")
    assert site == "x  y" and caps == []


def test_resolve_dictrefs_in_text():
    site, d = resolve_dictrefs_in_text('मृगानुसारिणं॥२॥ <dictref text="इयेष (link)" ref="iyeSha"/>', "t5")
    assert "dictref" not in site
    assert '<a href="bword://iyeSha">इयेष (link)</a>' in d


def test_multiple_captures_in_order():
    _, caps = extract_dict_and_ref_tags('<dict syns="a">1</dict> <dict syns="b" entry="2"/> <dict syns="c">3</dict>', "t")
    assert [c.syns[0] for c in caps] == ["a", "b", "c"]


@pytest.mark.parametrize("body,needle", [
    ('<dict syns="a"><dict syns="b">inner</dict></dict>', "nested"),
    ('<dict syns="a">never closed', "never closed"),
    ("stray </dict>", "no matching open"),
    ('<dictref text="x"/>', "text= or ref="),
    ('<dictref ref="x"/>', "text= or ref="),
    ('<dict syns="a" entry="b" display="True"/>', "self-closing"),
])
def test_malformed_input_is_fatal(body, needle):
    with pytest.raises(DictSyntaxError) as exc:
        extract_dict_and_ref_tags(body, "bad.md")
    assert needle in str(exc.value) and "bad.md" in str(exc.value)

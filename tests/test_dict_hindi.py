"""hindi=: a Hindi rendering of a usage, kept out of the site, written to
the dictionary record as a `{{...}}` line (which the dictionary builder
leaves out of the entry; cds-study and the flashcard reports read it).

- notes chapters: <dict ... hindi="..."> (paired or self-closing)
- shloka chapters: a gloss of data-type "hindi" after the shloka
"""
import pytest

import dict_render as dr
from conftest import make_site, run_script
from dict_extract import DictSyntaxError, extract_dict_and_ref_tags


# --- extraction -------------------------------------------------------------

def test_hindi_attr_captured_not_on_site():
    site, caps = extract_dict_and_ref_tags(
        'क <dict syns="कठोरगर्भा" hindi="पूर्णगर्भा  बहू">वधूं</dict> ख', "t")
    assert site == "क वधूं ख"
    assert caps[0].hindi == "पूर्णगर्भा बहू"   # whitespace collapsed


def test_hindi_attr_on_self_closing():
    _, caps = extract_dict_and_ref_tags('<dict syns="a" entry="b" hindi="ह"/>', "t")
    assert caps[0].hindi == "ह"


def test_no_hindi_is_empty():
    _, caps = extract_dict_and_ref_tags('<dict syns="a">x</dict>', "t")
    assert caps[0].hindi == ""


@pytest.mark.parametrize("attr,needle", [('hindi=""', "empty"), ('hindi="a {b}"', "{ or }")])
def test_bad_hindi_is_an_error(attr, needle):
    with pytest.raises(DictSyntaxError) as e:
        extract_dict_and_ref_tags(f'<dict syns="a" {attr}>x</dict>', "t.md")
    assert needle in str(e.value)


# --- shloka record ----------------------------------------------------------

def test_shloka_record_hindi_line_after_anvaya():
    rec = dr.shloka_record("पद्यम् ॥१॥", [], ["e:X-01", "अ"], "अन्वयः", ["<i>g</i>"], hindi="हिन्दी")
    assert rec.split("\n") == ["पद्यम् ॥१॥", "====", "+ e:X-01;अ", "++ अन्वयः", "{{हिन्दी}}", "<i>g</i>"]


def test_shloka_record_without_hindi_unchanged():
    rec = dr.shloka_record("पद्यम् ॥१॥", [], ["अ"], None, ["<i>g</i>"])
    assert "{{" not in rec


# --- end to end -------------------------------------------------------------

def build(tmp_path, chapter_meta, md):
    texts = {"kavya/nataka/urc": {"meta": {"title": "उत्तररामचरितम्", "dict": {"folder": "kavya"}},
                                  "chapters": {"01": {"meta": {"dict": chapter_meta}, "files": {"01.md": md}}}}}
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    return (site / "dict" / "kavya" / "urc" / "01.txt").read_text(encoding="utf-8")


def test_notes_record_ends_with_hindi_line(tmp_path):
    out = build(tmp_path, {"type": "notes"},
                'गद्यम् <dict syns="कठोरगर्भा, पूर्णगर्भा" hindi="पूर्णगर्भा बहू को भी छोड़ कर">'
                'कठोरगर्भामपि वधूं विमुच्य</dict>\n\n<dict syns="अ">केवलम्</dict>\n')
    assert "- कठोरगर्भा;पूर्णगर्भा\nकठोरगर्भामपि वधूं विमुच्य\n{{पूर्णगर्भा बहू को भी छोड़ कर}}\n\n- अ\nकेवलम्\n" in out


def test_shloka_hindi_gloss_becomes_line_not_block(tmp_path):
    out = build(tmp_path, {"type": "shloka", "shloka_key_prefix": "URC,9,99"},
                '<div class="shloka" syns="अ">\nपद्यम् ॥१।१॥\n</div>\n'
                '<div class="gloss" data-type="hindi">हिन्दी <b>अनुवाद</b></div>\n'
                '<div class="gloss" data-type="notes">टिप्पणी</div>\n')
    assert "{{हिन्दी अनुवाद}}" in out
    assert out.count("हिन्दी") == 1          # not also a gloss block
    assert "टिप्पणी" in out

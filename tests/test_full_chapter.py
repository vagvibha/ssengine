"""The notes-format full-chapter entry (dict.chapter_key) and dict.tags_keep."""
import copy

import pytest

import dict_extract as de
import dict_render as dr
from conftest import make_site, run_script
from test_generate_dict_cli import standard_texts


def render(body, gloss_types, keep=None):
    keep = dr.default_tags_keep(gloss_types) if keep is None else set(keep)
    dropped = {}
    return dr.render_full_chapter_entry(body, gloss_types, keep, dropped), dropped


# ---------------------------------------------------------------------------
# Unit: render_full_chapter_entry
# ---------------------------------------------------------------------------

def test_default_keeps_every_gloss_type_and_shloka(gloss_types):
    body = (
        '<div class="shloka">पद्यम् ॥१॥</div>\n'
        '<div class="gloss" data-type="anvaya">अन्वयः ।</div>\n'
        '<div class="gloss" data-type="notes">टिप्पणी</div>\n'
        '<div class="vritti">वृत्तिः</div>\n'
    )
    out, dropped = render(body, gloss_types)
    assert "पद्यम् ॥१॥" in out and "<div" not in out
    assert "<b>अन्वयः</b><i>अन्वयः ।</i>" in out
    assert "<i>टिप्पणी</i>" in out
    assert "वृत्तिः" not in out            # not a gloss type or shloka -> dropped by default
    assert dropped == {"vritti": 1}


def test_tags_keep_selects_exactly(gloss_types):
    body = (
        '<div class="shloka">पद्यम्</div>\n'
        '<div class="gloss" data-type="notes">टिप्पणी</div>\n'
        '<div class="vritti">वृत्तिः</div>\n'
        '<div class="vada" data-type="claim">पक्षः-पाठः</div>\n'
    )
    out, dropped = render(body, gloss_types, keep=["vritti", "claim"])
    assert "वृत्तिः" in out                 # non-gloss kept -> plain text
    assert "<b>पक्षः</b><i>पक्षः-पाठः</i>" in out  # gloss routed through class vada, named by data-type
    assert "पद्यम्" not in out and "टिप्पणी" not in out
    assert dropped == {"shloka": 1, "notes": 1}


def test_nested_unlisted_div_is_dropped_inside_a_kept_one(gloss_types):
    body = '<div class="vritti">बहिः <div class="gloss" data-type="notes">अन्तः</div> शेषः</div>'
    out, _ = render(body, gloss_types, keep=["vritti"])
    assert "बहिः" in out and "शेषः" in out and "अन्तः" not in out


def test_classless_div_is_transparent(gloss_types):
    out, dropped = render("<div>पाठः</div>", gloss_types, keep=[])
    assert out == "पाठः" and dropped == {}


def test_topic_tags_go_but_their_text_stays(gloss_types):
    body = 'अ <topic name="ध्वनिः" context="x">ध्वनिपाठः</topic> आ <topic name="रसः" define="रसः" entry="y">'
    out, _ = render(body, gloss_types)
    assert out == "अ ध्वनिपाठः आ"


def test_details_and_media_blocks_are_removed(gloss_types):
    body = (
        "पूर्वम्\n\n<details markdown=\"1\">\n<summary>सारः</summary>\n\nदीर्घा चर्चा\n</details>\n\n"
        "<audio controls><source src=\"a.mp3\">no audio</audio>\n<!-- टिप्पणी -->\nपरम्"
    )
    out, _ = render(body, gloss_types)
    assert out == "पूर्वम्\n\nपरम्"


def test_markdown_constructs(gloss_types):
    body = (
        "## प्रथमोऽङ्कः {#anka-1}\n"
        "[(प्रविश्य)]{: .action} **सूतः** – *वचनम्* [पदम्]{: .other}\n"
        "* सूचीपदम्\n"
        "[कडी](https://example.org) [अन्तः]({{ xref(\"topics/a/b.md\") }}) ![चित्रम्](img.png)\n"
        "पादटिप्पणी[^1] {{ other_macro() }}{% raw %}\n"
        "[^1]: टिप्पणीपाठः\n    अनुवर्तनम्\n"
        "अन्त्यम्"
    )
    out, _ = render(body, gloss_types)
    assert out.splitlines() == [
        "<b>प्रथमोऽङ्कः</b>",
        "<i>(प्रविश्य)</i> **सूतः** – *वचनम्* पदम्",
        "* सूचीपदम्",
        "कडी अन्तः ",
        "पादटिप्पणी ",
        "अन्त्यम्",
    ]


def test_only_b_i_u_br_and_bword_links_survive(gloss_types):
    body = (
        '<b>ब</b> <i>इ</i> <u>उ</u><br> <br/> <span class="x">स्प</span> <sup>1</sup> '
        '<a href="bword://Y"> (Ref) </a> <a href="https://x">बाह्यम्</a> <small>लघु</small>'
    )
    out, _ = render(body, gloss_types)
    assert out == ('<b>ब</b> <i>इ</i> <u>उ</u><br> <br/> स्प 1 '
                   '<a href="bword://Y"> (Ref) </a> बाह्यम् लघु')


def test_blank_lines_collapse(gloss_types):
    out, _ = render("अ\n\n<div class=\"x\">y</div>\n\n\n\nआ\n", gloss_types)
    assert out == "अ\n\nआ"


# ---------------------------------------------------------------------------
# Unit: the dict view of a section body
# ---------------------------------------------------------------------------

def test_dict_view_resolves_dictrefs_and_drops_hidden_entries():
    body = (
        'अ <dictref text=" (Ref) " ref="Y"/> '
        '<dict syns="x">दृश्यम्</dict> '
        '<dict syns="h" display="False">गुप्तम् <dictref text="r" ref="Z"/></dict> '
        '<dict syns="s" entry="e"/>आ'
    )
    site, view, caps = de.extract_dict_views(body)
    assert site == "अ  दृश्यम्  आ"
    m = de.REMOVED_MARK  # left where hidden entries were, for the full-chapter renderer's cleanup
    assert view == f'अ <a href="bword://Y"> (Ref) </a> दृश्यम् {m} {m}आ'
    assert [c.syns for c in caps] == [["x"], ["h"], ["s"]]
    assert caps[1].raw_content == 'गुप्तम् <a href="bword://Z">r</a>'


# ---------------------------------------------------------------------------
# End-to-end: generate_dict.py
# ---------------------------------------------------------------------------

PLAY_SECTION = (
    "## प्रथमोऽङ्कः\n"
    '**राजा** – वचनम् <dictref text=" (Ref) " ref="Y"/>\n'
    '<dict syns="अ">दृश्यम् <notes>टिप्पणी</notes></dict>\n'
    '<dict syns="गु" display="False">गुप्तम्</dict>\n'
    '<div class="vritti">वृत्तिः</div>\n'
    '<topic name="ध्वनिः" context="c">विषयः</topic>\n'
)


def play_texts(chapter_dict, second_chapter_body="अन्यत्\n"):
    texts = standard_texts()
    texts["kavya/nataka/as"]["chapters"] = {
        "01": {"meta": {"dict": chapter_dict}, "files": {"01.md": PLAY_SECTION}},
        "02": {"files": {"01.md": second_chapter_body}},
    }
    return texts


def test_full_chapter_entry_end_to_end(tmp_path):
    site = make_site(tmp_path, play_texts({"type": "notes", "chapter_key": "AS-01"}))
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    assert "left out (not in tags_keep): vritti ×1" in r.stdout

    full = (site / "dict" / "plays" / "as" / "01-full.txt").read_text(encoding="utf-8")
    header, record = full.split("- AS-01\n")
    assert record.splitlines() == [
        "<b>प्रथमोऽङ्कः</b>",
        '**राजा** – वचनम् <a href="bword://Y"> (Ref) </a>',
        "दृश्यम् <i>टिप्पणी</i>",
        "विषयः",
    ]
    # the individual entries file is unaffected by tags_keep/full-chapter rules
    entries = (site / "dict" / "plays" / "as" / "01.txt").read_text(encoding="utf-8")
    assert "- अ\nदृश्यम् <i>टिप्पणी</i>" in entries and "- गु\nगुप्तम्" in entries


def test_tags_keep_end_to_end(tmp_path):
    ch = {"type": "notes", "chapter_key": "AS-01", "tags_keep": ["vritti"]}
    site = make_site(tmp_path, play_texts(ch))
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    full = (site / "dict" / "plays" / "as" / "01-full.txt").read_text(encoding="utf-8")
    assert "वृत्तिः" in full and "टिप्पणी" not in full


def test_tags_keep_accepts_a_class_used_elsewhere_in_the_book(tmp_path):
    ch = {"type": "notes", "chapter_key": "AS-01", "tags_keep": ["notes", "kosha"]}
    site = make_site(tmp_path, play_texts(ch, second_chapter_body='<div class="kosha">कोशः</div>\n'))
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("chapter_dict, message", [
    ({"type": "notes", "chapter_key": "K", "tags_keep": ["notez"]}, "'notez' isn't a gloss type or a div class"),
    ({"type": "notes", "chapter_key": "K", "tags_keep": ["details"]}, "details can't be kept"),
    ({"type": "notes", "tags_keep": ["notes"]}, "tags_keep is set but chapter_key isn't"),
    ({"type": "shloka", "chapter_key": "K", "shloka_key_prefix": "AS,99", "tags_keep": ["notes"]},
     "tags_keep only applies to type: notes"),
    ({"chapter_key": "K"}, "has no type:"),
    ({"type": "note"}, "dict.type 'note'"),
])
def test_bad_dict_config_fails(tmp_path, chapter_dict, message):
    site = make_site(tmp_path, play_texts(chapter_dict))
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0
    assert message in r.stderr, r.stderr
    assert not (site / "dict" / "plays" / "as" / "01-full.txt").exists()
    assert not (site / "dict" / "plays" / "as" / "01.txt").exists()  # validated before anything is written


def test_chapter_dict_without_book_folder_fails(tmp_path):
    texts = play_texts({"type": "notes", "chapter_key": "K"})
    del texts["kavya/nataka/as"]["meta"]["dict"]
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "no dict.folder" in r.stderr, r.stderr


def test_trailing_whitespace_is_stripped_from_dict_files(tmp_path):
    """Markdown's two-space hard break is site-only; the dictionary builder
    turns newlines into <br> itself."""
    texts = play_texts({"type": "notes", "chapter_key": "AS-01"})
    texts["kavya/nataka/as"]["chapters"]["01"]["files"]["01.md"] = (
        '**राजा** – वचनम्  \nअपरम्\t\n<dict syns="अ">प्रविष्टिः  \nशेषः  </dict>\n'
    )
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    for name in ("01.txt", "01-full.txt"):
        content = (site / "dict" / "plays" / "as" / name).read_text(encoding="utf-8")
        assert all(line == line.rstrip() for line in content.splitlines()), (name, content)
    full = (site / "dict" / "plays" / "as" / "01-full.txt").read_text(encoding="utf-8")
    assert "**राजा** – वचनम्\nअपरम्\nप्रविष्टिः\nशेषः" in full

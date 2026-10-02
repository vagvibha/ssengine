"""A <topic define=...> body (or entry=) is rendered as Markdown in the
परिभाषा cell: **bold**/*italic* render, a plain newline is a soft break
(a space), and only two trailing spaces or <br> make a hard break."""
import pytest

import generate_indices as gi
from test_topic_forms import defs, ok

R = gi.render_definition_markdown


@pytest.mark.parametrize("src, expected", [
    # the reported case: bold renders, the soft newline is just a space
    ("hello **this**\nis definition of X.", "hello <strong>this</strong> is definition of X."),
    ("*i* and _u_ a_b_c", "<em>i</em> and <em>u</em> a_b_c"),
    # hard breaks: two trailing spaces, or an explicit <br> / <br/>
    ("अ ।  \nब ॥", "अ ।<br>ब ॥"),
    ("अ ।<br>\nब ॥", "अ ।<br>ब ॥"),
    ("अ ।<br/>ब", "अ ।<br>ब"),
    # a blank line (new paragraph) is a visible gap
    ("p1\n\np2", "p1<br><br>p2"),
    # other tags dropped, text kept (as before)
    ("य <span class='x'>र</span> <dict syns=\"a\" entry=\"b\"/>ल", "य र ल"),
    # text is escaped
    ('x < y & z', "x &lt; y &amp; z"),
    # links show as text only — the whole cell is already a link
    ("see [ध्वनिः](../x.md)", "see ध्वनिः"),
    # indented continuation / blockquote markers aren't code or quotes
    ("first\n    second", "first second"),
    ("first\n> second  \n> third", "first second<br>third"),
    # leading/trailing whitespace (incl. a trailing hard break) dropped
    ("\n  अ ॥  \n", "अ ॥"),
])
def test_render(src, expected):
    assert R(src) == expected


@pytest.mark.parametrize("src", ["", "   \n ", "<br>", "<b></b>\n"])
def test_empty(src):
    assert R(src) == ""


def test_output_is_single_line():
    assert "\n" not in R("a\nb  \nc\n\nd")


def test_paired_definition_end_to_end(tmp_path):
    page, ch = ok(tmp_path, 'abc <topic name="माया" define="य">hello **this**\nis definition.</topic>\n')
    [(term, text)] = defs(page)
    assert term == "य" and text == "hello <strong>this</strong> is definition."
    # the passage itself is left exactly as authored
    assert "hello **this**\nis definition." in ch


def test_self_closing_entry_end_to_end(tmp_path):
    page, _ = ok(tmp_path, '<topic name="माया" define="य" entry="*ज*  \nक"/>\n')
    assert "●</span> <em>ज</em><br>क</a>" in page


def test_markup_only_body_is_still_empty_error(tmp_path):
    from test_topic_multi_name import build
    _, r = build(tmp_path, chapter='<topic name="माया" define="य"><br></topic>\n')
    assert r.returncode != 0 and "the body (the definition) is empty" in r.stderr

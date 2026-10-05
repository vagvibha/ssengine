"""`shloka_highlight:` in a book's or chapter's meta.yaml: every shloka
gets highlight="true" unless it sets highlight itself."""
import pytest

import generate_indices as gi
from conftest import make_site, run_script

S_PLAIN = '<div class="shloka">अ ॥१॥</div>'
S_ON = '<div class="shloka" highlight="true">आ ॥२॥</div>'
S_OFF = '<div class="shloka" highlight="false">इ ॥३॥</div>'


def run(body, default):
    return gi.extract_shlokas(body, "", [], "", shloka_highlight_default=default)


def test_default_off_leaves_divs_alone():
    out, shl, _ = run(S_PLAIN + "\n" + S_OFF, False)
    assert 'highlight="true"' not in out
    assert [s.highlight for s in shl] == [False, False]


def test_default_on_injects_once_and_respects_explicit_false():
    out, shl, _ = run("\n".join([S_PLAIN, S_ON, S_OFF]), True)
    assert out.count('highlight="true"') == 2          # injected on plain, kept (not doubled) on S_ON
    assert 'highlight="false"' in out
    assert [s.highlight for s in shl] == [True, True, False]


TEXT = "kavya/padya/ka"
PAGE = "docs/kavya/padya/ka/01.md"


@pytest.mark.parametrize("book_meta,ch_meta,expected", [
    ({}, {}, 0),
    ({"shloka_highlight": True}, {}, 2),
    ({}, {"shloka_highlight": True}, 2),
    ({"shloka_highlight": True}, {"shloka_highlight": False}, 0),   # chapter wins
])
def test_end_to_end(tmp_path, book_meta, ch_meta, expected):
    files = {"a.md": S_PLAIN + "\n\n" + S_OFF.replace("false", "") + "\n"}
    texts = {TEXT: {"meta": {"title": "क", **book_meta}, "chapters": {"01": {"meta": ch_meta, "files": files}}}}
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert (site / PAGE).read_text(encoding="utf-8").count('highlight="true"') == expected


def test_rejects_quoted_bool():
    with pytest.raises(gi.ConfigError):
        gi.check_keys({"shloka_highlight": "true"}, gi.CHAPTER_META_KEYS, "ch/meta.yaml")

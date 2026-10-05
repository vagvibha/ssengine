"""`toc:` in a sections-mode chapter's meta.yaml: headings (unlinked) with
section files nested under them at any depth, or at the top level."""
import pytest

from conftest import make_site, run_script

TEXT = "kavya/padya/ka"
LANDING = "docs/kavya/padya/ka/01/index.md"

FILES = {
    "a.md": "---\ntitle: अ-भागः\n---\nअ\n",
    "b.md": "ब\n",
    "c.md": "क\n",
}

TOC = [
    {"title": "T1", "children": [
        {"title": "T11", "children": [{"file": "a"}]},
        {"file": "b.md"},
    ]},
    {"file": "c"},
]


def build(tmp_path, toc, files=None, style="sections"):
    meta = {"chapter_display_style": style, "toc": toc}
    texts = {TEXT: {"meta": {"title": "क"}, "chapters": {"01": {"meta": meta, "files": files or FILES}}}}
    site = make_site(tmp_path, texts)
    return site, run_script(site, "generate_indices.py")


def test_nested_toc(tmp_path):
    site, r = build(tmp_path, TOC)
    assert r.returncode == 0, r.stderr
    landing = (site / LANDING).read_text(encoding="utf-8")
    expected = "\n".join([
        '- <strong class="sv-toc-heading">T1</strong>',
        '    - <strong class="sv-toc-heading">T11</strong>',
        "        - [अ-भागः](a.md)",
        "    - [b](b.md)",
        "- [c](c.md)",
    ])
    assert expected in landing


def test_without_toc_landing_is_flat(tmp_path):
    texts = {TEXT: {"meta": {"title": "क"}, "chapters": {"01": {
        "meta": {"chapter_display_style": "sections"}, "files": FILES}}}}
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    landing = (site / LANDING).read_text(encoding="utf-8")
    assert "- [अ-भागः](a.md)\n- [b](b.md)\n- [c](c.md)" in landing


def test_toc_ignored_in_full_chapter_mode(tmp_path):
    bad = [{"file": "c"}, {"file": "a"}]  # wrong order and incomplete: still fine here
    site, r = build(tmp_path, bad, style="full_chapter")
    assert r.returncode == 0, r.stderr


def test_ignored_file_and_its_emptied_heading_are_skipped(tmp_path):
    files = dict(FILES, **{"a.md": "---\nignore: true\n---\nअ\n"})
    site, r = build(tmp_path, TOC, files=files)
    assert r.returncode == 0, r.stderr
    landing = (site / LANDING).read_text(encoding="utf-8")
    assert "T11" not in landing and "T1</strong>" in landing


@pytest.mark.parametrize("toc, message", [
    ([], "toc: is empty"),
    ([{"title": "T", "children": []}], "heading 'T' has no children"),
    ([{"title": "T"}], "heading 'T' has no children"),
    ([{"name": "x"}], "needs either 'file:' or 'title:'"),
    ([{"file": "a", "title": "x"}], "unknown key(s) 'title'"),
    ([{"title": "T", "children": [{"file": "a"}], "order": 1}], "unknown key(s) 'order'"),
    ([{"file": "a"}, {"file": "b"}, {"file": "c"}, {"file": "z"}], "file 'z' — no such section"),
    ([{"file": "a"}, {"file": "b"}, {"file": "c"}, {"file": "a.md"}], "file 'a' is listed more than once"),
    ([{"file": "a"}, {"file": "b"}], "doesn't list c.md"),
    ([{"file": "b"}, {"file": "a"}, {"file": "c"}], "different order than their filenames"),
])
def test_bad_toc_fails(tmp_path, toc, message):
    site, r = build(tmp_path, toc)
    assert r.returncode != 0
    assert message in r.stderr, r.stderr

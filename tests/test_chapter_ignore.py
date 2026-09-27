"""`ignore: true` on a chapter — in a chapter directory's meta.yaml, or in
a single-file `<chapter>.md`'s frontmatter — skips the whole chapter, for
both the site and the dictionary."""
from conftest import make_site, run_script

KEPT = {"files": {"01.md": "रक्षितः-पाठः\n"}}


def build(tmp_path, chapters, book_meta=None):
    texts = {"kavya/padya/ka": {"meta": book_meta or {"title": "क"}, "chapters": chapters}}
    site = make_site(tmp_path, texts)
    return site


def test_chapter_meta_ignore_skips_chapter(tmp_path):
    site = build(tmp_path, {"01": KEPT, "02": {"meta": {"ignore": True}, "files": {"01.md": "गुप्तः-पाठः\n"}}})
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert "ignore: true in meta.yaml" in r.stdout

    docs = site / "docs" / "kavya" / "padya" / "ka"
    assert (docs / "01.md").exists()
    assert not (docs / "02.md").exists() and not (docs / "02").exists()
    assert "02.md" not in (docs / "index.md").read_text(encoding="utf-8")
    assert "02.md" not in (site / "mkdocs.yml").read_text(encoding="utf-8")


def test_ignored_chapter_with_no_sections_does_not_warn(tmp_path):
    site = build(tmp_path, {"01": KEPT, "02": {"meta": {"ignore": True}, "files": {}}})
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert "contains no .md sections" not in r.stderr


def test_ignore_false_builds_normally(tmp_path):
    site = build(tmp_path, {"01": {"meta": {"ignore": False}, "files": {"01.md": "पाठः\n"}}})
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert (site / "docs" / "kavya" / "padya" / "ka" / "01.md").exists()


def test_quoted_ignore_is_an_error(tmp_path):
    site = build(tmp_path, {"01": KEPT, "02": {"meta": {"ignore": "true"}, "files": {"01.md": "x\n"}}})
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "ignore should be true or false" in r.stderr


def test_single_file_chapter_frontmatter_ignore(tmp_path):
    site = build(tmp_path, {"01": KEPT})
    book = site / "kavya" / "padya" / "ka"
    (book / "02.md").write_text("---\nignore: true\n---\nगुप्तः-पाठः\n", encoding="utf-8")
    (book / "03.md").write_text("---\nignore: false\n---\nदृश्यः-पाठः\n", encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert "ignore: true in frontmatter" in r.stdout

    docs = site / "docs" / "kavya" / "padya" / "ka"
    assert not (docs / "02.md").exists()
    assert "दृश्यः-पाठः" in (docs / "03.md").read_text(encoding="utf-8")


def test_dictionary_skips_ignored_chapters(tmp_path):
    notes = '<dict syns="अ">प्रविष्टिः</dict>\n'
    site = build(
        tmp_path,
        {
            "01": {"meta": {"dict": {"type": "notes"}}, "files": {"01.md": notes}},
            "02": {"meta": {"ignore": True, "dict": {"type": "notes"}}, "files": {"01.md": notes}},
        },
        book_meta={"title": "क", "dict": {"folder": "kavya"}},
    )
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    out = site / "dict" / "kavya" / "ka"
    assert (out / "01.txt").exists()
    assert not (out / "02.txt").exists()

"""`dict:` in .md frontmatter: a section's `dict.title` add-on (chapter
directory), and the full `dict:` block of a top-level single-.md chapter
(which has no meta.yaml of its own)."""
from conftest import make_site, run_script

BOOK = "kavya/padya/ka"
BOOK_META = {"title": "किरातार्जुनीयम्", "dict": {"folder": "kavya"}}
ENTRY = 'गद्यम् <dict syns="अ">प्रविष्टिः</dict>\n'


def fm(block: str, body: str = ENTRY) -> str:
    return f"---\n{block}\n---\n{body}"


def site_with(tmp_path, chapter: dict):
    return make_site(tmp_path, {BOOK: {"meta": BOOK_META, "chapters": {"01": chapter}}})


def header_title(site, name="01.txt") -> str:
    return (site / "dict" / "kavya" / "ka" / name).read_text(encoding="utf-8").splitlines()[0]


def test_section_title_appended_after_chapter_title(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "notes", "title": "१"}},
        "files": {"01.md": ENTRY, "02.md": fm('dict:\n  title: "[क]"')},
    })
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    assert header_title(site) == "HEADER:title=किरातार्जुनीयम् १ [क]"


def test_section_title_without_chapter_title_has_no_double_space(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": fm("dict:\n  title: क")},
    })
    assert run_script(site, "generate_dict.py").returncode == 0
    assert header_title(site) == "HEADER:title=किरातार्जुनीयम् क"


def test_no_titles_at_all_has_no_trailing_space(tmp_path):
    site = site_with(tmp_path, {"meta": {"dict": {"type": "notes"}}, "files": {"01.md": ENTRY}})
    assert run_script(site, "generate_dict.py").returncode == 0
    assert header_title(site) == "HEADER:title=किरातार्जुनीयम्"


def test_title_in_two_sections_fails_both_scripts(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": fm("dict:\n  title: क"), "02.md": fm("dict:\n  title: ख")},
    })
    for script in ("generate_dict.py", "generate_indices.py"):
        r = run_script(site, script)
        assert r.returncode != 0
        assert "more than one section" in r.stderr and "01.md, 02.md" in r.stderr


def test_chapter_wide_key_in_section_fails(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": fm("dict:\n  title: क\n  type: shloka")},
    })
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0
    assert "type apply to the whole chapter" in r.stderr and "Allowed here: title, syns, skip" in r.stderr


def test_unknown_key_in_section_fails(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": fm("dict:\n  titel: क")},
    })
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "titel" in r.stderr


def test_section_title_on_chapter_without_dict_block_fails(tmp_path):
    site = site_with(tmp_path, {"files": {"01.md": fm("dict:\n  title: क")}})
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "has no dict:" in r.stderr


def test_section_title_in_ignored_section_is_not_counted(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": fm("dict:\n  title: क"), "02.md": fm("ignore: true\ndict:\n  title: ख")},
    })
    assert run_script(site, "generate_dict.py").returncode == 0
    assert header_title(site) == "HEADER:title=किरातार्जुनीयम् क"


def test_top_level_md_chapter_takes_full_dict_block_from_frontmatter(tmp_path):
    site = make_site(tmp_path, {BOOK: {"meta": BOOK_META}})
    (site / BOOK / "07.md").write_text(
        fm('title: सप्तमः\ndict:\n  type: notes\n  title: "[७]"\n  chapter_key: KA-7'), encoding="utf-8")
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    assert header_title(site, "07.txt") == "HEADER:title=किरातार्जुनीयम् [७]"
    assert (site / "dict" / "kavya" / "ka" / "07-full.txt").exists()
    assert run_script(site, "generate_indices.py").returncode == 0


def test_top_level_md_chapter_dict_block_is_validated(tmp_path):
    site = make_site(tmp_path, {BOOK: {"meta": BOOK_META}})
    (site / BOOK / "07.md").write_text(fm("dict:\n  type: notes\n  folder: kavya"), encoding="utf-8")
    for script in ("generate_dict.py", "generate_indices.py"):
        r = run_script(site, script)
        assert r.returncode != 0 and "folder" in r.stderr


def test_top_level_md_chapter_without_dict_block_writes_nothing(tmp_path):
    site = make_site(tmp_path, {BOOK: {"meta": BOOK_META}})
    (site / BOOK / "07.md").write_text(ENTRY, encoding="utf-8")
    assert run_script(site, "generate_dict.py").returncode == 0
    assert not (site / "dict" / "kavya" / "ka" / "07.txt").exists()


SHLOKA = '<div class="shloka">\nपद्यम् ॥१॥\n</div>\n'


def test_section_syns_and_skip_still_allowed_alongside_title(tmp_path):
    site = site_with(tmp_path, {
        "meta": {"dict": {"type": "shloka", "title": "१"}},
        "files": {"01.md": fm("dict:\n  title: क\n  syns: [अ, आ]\n  skip: [इ]", SHLOKA)},
    })
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    out = (site / "dict" / "kavya" / "ka" / "01.txt").read_text(encoding="utf-8")
    assert out.splitlines()[0] == "HEADER:title=किरातार्जुनीयम् १ क"
    assert "+ अ;आ" in out and "- इ" in out


def test_top_level_md_shloka_chapter_skip_is_header_skip_and_syns_per_verse(tmp_path):
    site = make_site(tmp_path, {BOOK: {"meta": BOOK_META}})
    (site / BOOK / "07.md").write_text(
        fm("dict:\n  type: shloka\n  syns: [अ]\n  skip: [इ]", SHLOKA), encoding="utf-8")
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    out = (site / "dict" / "kavya" / "ka" / "07.txt").read_text(encoding="utf-8")
    assert "HEADER:skip=इ" in out
    assert "+ अ" in out and "\n- इ" not in out

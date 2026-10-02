"""Verse navigation (dict.nav: true), data-alt key suffixes, and the
duplicate-key check, in dict.type: shloka chapters."""
import re

import pytest

import dict_render as dr
from conftest import make_site, run_script

NUMS = "०१२३४५६७८९"


def dn(n: int) -> str:
    return "".join(NUMS[int(c)] for c in str(n))


def verse(n: int, alt: str | None = None, syns: str | None = None, ch: int = 1) -> str:
    attrs = (f' data-alt="{alt}"' if alt else "") + (f' syns="{syns}"' if syns else "")
    return f'<div class="shloka"{attrs}>\nपद्यम् {dn(n)} ॥{dn(ch)}।{dn(n)}॥\n</div>\n'


def chapter(files: dict[str, str], **dict_opts) -> dict:
    block = {"type": "shloka", "shloka_key_prefix": "MD,9,99", **dict_opts}
    return {"meta": {"dict": block}, "files": files}


def build(tmp_path, chapters: dict) -> tuple:
    texts = {"kavya/padya/md": {"meta": {"title": "मेघदूतम्", "dict": {"folder": "kavya"}},
                                "chapters": chapters}}
    site = make_site(tmp_path, texts)
    return site, run_script(site, "generate_dict.py")


def out(site, name: str) -> str:
    return (site / "dict" / "kavya" / "md" / name).read_text(encoding="utf-8")


def records(text: str) -> list[str]:
    """Shloka records of a dict file (header lines dropped)."""
    body = "\n".join(ln for ln in text.split("\n") if not ln.startswith("HEADER:"))
    return [r for r in body.split("\n\n") if r.strip()]


def nav_of(record: str) -> str | None:
    """The record's nav line (after its gloss blocks it starts with the
    "<br>" that joins every block to the one before)."""
    last = record.rstrip("\n").split("\n")[-1].removeprefix("<br>")
    return last if last.startswith("‹") else None


def link(key: str, label: str) -> str:
    return f'<a href="bword://{key}">{label}</a>'


# --- unit: shloka_nav_line / shloka_record -----------------------------------

def test_nav_line_all_parts():
    line = dr.shloka_nav_line(("e:MD-1-01", "॥१।१॥"), "MD-01", ("e:MD-1-03", "॥१।३॥"))
    assert line == f'‹ {link("MD-1-01", "॥१।१॥")} · {link("MD-01", "MD-01")} · {link("MD-1-03", "॥१।३॥")} ›'


def test_nav_line_missing_parts_drop_their_separator():
    assert dr.shloka_nav_line(None, "C", ("e:K-2", "२")) == f'‹ {link("C", "C")} · {link("K-2", "२")} ›'
    assert dr.shloka_nav_line(("e:K-1", "१"), None, None) == f'‹ {link("K-1", "१")} ›'
    assert dr.shloka_nav_line(None, None, None) is None


def test_record_nav_is_last_gloss_block():
    r = dr.shloka_record("पद्यम् ॥१॥", [], ["e:K-1"], None, ["<i>a</i>"], nav="‹ x ›")
    assert r.endswith("<i>a</i>\n<br>‹ x ›")
    # no glosses: the nav line takes the (otherwise empty) gloss line
    r = dr.shloka_record("पद्यम् ॥१॥", [], ["e:K-1"], None, [], nav="‹ x ›")
    assert r == "पद्यम् ॥१॥\n====\n+ e:K-1\n‹ x ›"


# --- end to end: verse links -------------------------------------------------

def test_three_verses_prev_up_next(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1) + verse(2) + verse(3)},
                                             nav=True, chapter_key="MD-01")})
    assert r.returncode == 0, r.stderr
    r1, r2, r3 = records(out(site, "01.txt"))
    up = link("MD-01", "MD-01")
    v = {n: link(f"MD-1-0{n}", f"॥१।{dn(n)}॥") for n in (1, 2, 3)}
    assert nav_of(r1) == f"‹ {up} · {v[2]} ›"
    assert nav_of(r2) == f"‹ {v[1]} · {up} · {v[3]} ›"
    assert nav_of(r3) == f"‹ {v[2]} · {up} ›"


def test_no_up_link_without_chapter_key(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1) + verse(2)}, nav=True)})
    assert r.returncode == 0, r.stderr
    r1, r2 = records(out(site, "01.txt"))
    assert nav_of(r1) == f'‹ {link("MD-1-02", "॥१।२॥")} ›'
    assert "MD-01" not in out(site, "01.txt")


def test_single_verse_without_chapter_key_has_no_nav_line(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, nav=True)})
    assert r.returncode == 0, r.stderr
    [r1] = records(out(site, "01.txt"))
    assert nav_of(r1) is None and "‹" not in r1


def test_verses_chain_across_sections_in_order(tmp_path):
    files = {"01.md": verse(1) + verse(2), "02.md": verse(3), "10.md": verse(4)}
    site, r = build(tmp_path, {"01": chapter(files, nav=True)})
    assert r.returncode == 0, r.stderr
    recs = records(out(site, "01.txt"))
    assert len(recs) == 4
    assert link("MD-1-02", "॥१।२॥") in nav_of(recs[2]) and link("MD-1-04", "॥१।४॥") in nav_of(recs[2])


def test_no_links_across_chapters(tmp_path):
    site, r = build(tmp_path, {
        "01": chapter({"01.md": verse(1) + verse(2)}, nav=True, chapter_key="MD-01"),
        "02": chapter({"01.md": verse(1, ch=2) + verse(2, ch=2)}, nav=True, chapter_key="MD-02"),
    })
    assert r.returncode == 0, r.stderr
    last_of_1 = records(out(site, "01.txt"))[-1]
    first_of_2 = records(out(site, "02.txt"))[0]
    assert "MD-2-" not in nav_of(last_of_1) and "MD-02" not in nav_of(last_of_1)
    assert "MD-1-" not in nav_of(first_of_2) and "MD-01" not in nav_of(first_of_2)


def test_nav_off_output_unchanged(tmp_path):
    files = {"01.md": verse(1) + "<anvaya>अ ।</anvaya>\n" + verse(2)}
    site_a, ra = build(tmp_path / "a", {"01": chapter(files, chapter_key="MD-01")})
    site_b, rb = build(tmp_path / "b", {"01": chapter(files, chapter_key="MD-01", nav=False)})
    assert ra.returncode == 0 and rb.returncode == 0
    for name in ("01.txt", "01-full.txt"):
        assert out(site_a, name) == out(site_b, name)
    assert "‹" not in out(site_a, "01.txt")


def test_every_bword_link_resolves_and_no_blank_line_in_records(tmp_path):
    files = {"01.md": verse(1) + "<anvaya>अ ।</anvaya>\n" + verse(2) + verse(2, alt="b") + verse(3)}
    site, r = build(tmp_path, {"01": chapter(files, nav=True, chapter_key="MD-01")})
    assert r.returncode == 0, r.stderr
    txt, full = out(site, "01.txt"), out(site, "01-full.txt")
    keys = {ln[2:].split(";")[0].removeprefix("e:") for ln in txt.split("\n") if ln.startswith("+ ")}
    keys |= {ln[2:] for ln in full.split("\n") if ln.startswith("- ")}
    hrefs = set(re.findall(r'bword://([^"]+)"', txt + full))
    assert hrefs and hrefs <= keys
    recs = records(txt)
    assert len(recs) == 4  # a blank line inside a record would split it
    assert "<br>‹ " in recs[0]  # after the anvaya gloss block
    for rec in recs:
        nav = nav_of(rec)
        assert nav and not re.match(r"(-|\+|====)", nav)


# --- data-alt and duplicate keys ---------------------------------------------

def test_data_alt_suffixes_the_key_only(tmp_path):
    files = {"31.md": verse(31), "31-02.md": verse(31, alt="b"), "31-03.md": verse(31, alt="c")}
    site, r = build(tmp_path, {"01": chapter(files, nav=True, chapter_key="MD-01")})
    assert r.returncode == 0, r.stderr
    txt = out(site, "01.txt")
    assert [ln for ln in txt.split("\n") if ln.startswith("+ ")] == ["+ e:MD-1-31", "+ e:MD-1-31b", "+ e:MD-1-31c"]
    assert txt.count("॥१।३१॥\n====") == 3  # the marker itself is untouched
    r1, r2, r3 = records(txt)
    assert link("MD-1-31b", "॥१।३१॥b") in nav_of(r1)
    assert link("MD-1-31", "॥१।३१॥") in nav_of(r2) and link("MD-1-31c", "॥१।३१॥c") in nav_of(r2)
    full = out(site, "01-full.txt")  # each version's marker links to its own record
    for k in ("MD-1-31", "MD-1-31b", "MD-1-31c"):
        assert f'<a href="bword://{k}">॥१।३१॥</a>' in full


def test_duplicate_key_is_an_error(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"31.md": verse(31), "31-02.md": verse(31)})})
    assert r.returncode != 0
    assert "MD-1-31 is already used" in r.stderr and "31.md" in r.stderr and 'data-alt="b"' in r.stderr
    assert not (site / "dict" / "kavya" / "md" / "01.txt").exists()


def test_duplicate_key_in_same_file_is_an_error(tmp_path):
    _, r = build(tmp_path, {"01": chapter({"01.md": verse(5) + verse(5)})})
    assert r.returncode != 0 and "earlier in this file" in r.stderr


def test_same_alt_twice_is_still_a_duplicate(tmp_path):
    _, r = build(tmp_path, {"01": chapter({"01.md": verse(5) + verse(5, alt="b") + verse(5, alt="b")})})
    assert r.returncode != 0 and "MD-1-05b is already used" in r.stderr


def test_duplicates_without_prefix_are_not_checked(tmp_path):
    # no generated keys -> nothing to collide (syns may legitimately repeat)
    texts = {"01": {"meta": {"dict": {"type": "shloka"}},
                    "files": {"01.md": verse(5, syns="अ") + verse(5, syns="अ")}}}
    _, r = build(tmp_path, texts)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("alt", ["", "b c", "ख", "b;c"])
def test_bad_data_alt_value(tmp_path, alt):
    files = {"01.md": f'<div class="shloka" data-alt="{alt}">\nपद्यम् ॥१।१॥\n</div>\n'}
    _, r = build(tmp_path, {"01": chapter(files)})
    assert r.returncode != 0 and "ASCII letters/digits only" in r.stderr


def test_data_alt_without_prefix_is_an_error(tmp_path):
    texts = {"01": {"meta": {"dict": {"type": "shloka"}},
                    "files": {"01.md": verse(1, alt="b", syns="अ")}}}
    _, r = build(tmp_path, texts)
    assert r.returncode != 0 and "needs dict.shloka_key_prefix" in r.stderr


# --- config ------------------------------------------------------------------

def test_nav_without_prefix_fails(tmp_path):
    texts = {"01": {"meta": {"dict": {"type": "shloka", "nav": True}}, "files": {"01.md": verse(1, syns="अ")}}}
    _, r = build(tmp_path, texts)
    assert r.returncode != 0 and "nav needs shloka_key_prefix" in r.stderr


def test_nav_on_notes_chapter_fails(tmp_path):
    texts = {"01": {"meta": {"dict": {"type": "notes", "nav": True}},
                    "files": {"01.md": 'ग <dict syns="अ">प</dict>\n'}}}
    _, r = build(tmp_path, texts)
    assert r.returncode != 0 and "nav only applies to type: shloka" in r.stderr


def test_nav_typo_fails_strict_validation(tmp_path):
    _, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, navv=True)})
    assert r.returncode != 0 and "navv" in r.stderr


def test_nav_must_be_a_bool(tmp_path):
    _, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, nav="yes")})
    assert r.returncode != 0 and "nav" in r.stderr

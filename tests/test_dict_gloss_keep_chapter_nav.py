"""dict.tags_keep on shloka chapters (which glosses go into each verse
record), the previous/next chapter line on a dict.nav chapter's
full-chapter record, and a book-level dict.skip."""
import pytest

from conftest import make_site, run_script

NUMS = "०१२३४५६७८९"


def dn(n: int) -> str:
    return "".join(NUMS[int(c)] for c in str(n))


def verse(n: int, ch: int = 1) -> str:
    return f'<div class="shloka">\nपद्यम् {dn(n)} ॥{dn(ch)}।{dn(n)}॥\n</div>\n'


GLOSSES = "<anvaya>राम वनं गच्छति ।</anvaya>\n<notes>टिप्पणी</notes>\n<hindi>राम वन जाते हैं</hindi>\n"
GLOSS_TYPES = {
    "supported_css_styles": ["notes", "anvaya"],
    "types": [
        {"data_type": "notes", "css_style": "notes", "label": "टिप्पणी"},
        {"data_type": "anvaya", "css_style": "anvaya", "label": "अन्वयः"},
        {"data_type": "hindi", "css_style": "notes"},
    ],
}


def chapter(files: dict[str, str], **dict_opts) -> dict:
    return {"meta": {"dict": {"type": "shloka", "shloka_key_prefix": "BG,99,99", **dict_opts}}, "files": files}


def build(tmp_path, chapters: dict, book_dict: dict | None = None):
    texts = {"kavya/padya/bg": {"meta": {"title": "गीता", "dict": {"folder": "kavya", **(book_dict or {})}},
                                "chapters": chapters}}
    site = make_site(tmp_path, texts, gloss_types=GLOSS_TYPES)
    return site, run_script(site, "generate_dict.py")


def out(site, name: str) -> str:
    return (site / "dict" / "kavya" / "bg" / name).read_text(encoding="utf-8")


def link(key: str) -> str:
    return f'<a href="bword://{key}">{key}</a>'


# --- tags_keep on shloka chapters --------------------------------------------

def test_default_keeps_every_gloss(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1) + GLOSSES})})
    assert r.returncode == 0, r.stderr
    txt = out(site, "01.txt")
    assert "<b>अन्वयः</b>" in txt and "<b>टिप्पणी</b>" in txt


def test_tags_keep_filters_blocks_but_anvaya_still_keys(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1) + GLOSSES}, tags_keep=["notes"])})
    assert r.returncode == 0, r.stderr
    txt = out(site, "01.txt")
    assert "++ राम वनं गच्छति\n" in txt          # keys from the anvaya, not kept as a block
    assert "<b>अन्वयः</b>" not in txt
    assert "<b>टिप्पणी</b>\n<i>टिप्पणी</i>" in txt
    assert "{{राम वन जाते हैं}}" in txt          # hindi is not a block: unaffected


def test_empty_tags_keep_keeps_no_gloss(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1) + GLOSSES + verse(2)}, tags_keep=[])})
    assert r.returncode == 0, r.stderr
    txt = out(site, "01.txt")
    assert "<b>" not in txt and "<i>" not in txt
    assert "++ राम वनं गच्छति" in txt


def test_tags_keep_unknown_type_fails(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, tags_keep=["bhashya"])})
    assert r.returncode != 0 and "'bhashya' isn't a gloss type of this book" in r.stderr
    assert not (site / "dict" / "kavya" / "bg" / "01.txt").exists()


def test_tags_keep_on_shloka_chapter_needs_no_chapter_key(tmp_path):
    _, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, tags_keep=["notes"])})
    assert r.returncode == 0, r.stderr


# --- chapter prev/next on the full-chapter record ----------------------------

def three_chapters(**opts) -> dict:
    return {f"0{c}": chapter({"01.md": verse(1, c) + verse(2, c)}, chapter_key=f"BG-0{c}", **opts)
            for c in (1, 2, 3)}


def test_full_record_links_neighbouring_chapters(tmp_path):
    site, r = build(tmp_path, three_chapters(nav=True))
    assert r.returncode == 0, r.stderr
    assert out(site, "01-full.txt").endswith(f"\n\n‹ {link('BG-02')} ›\n")
    assert out(site, "02-full.txt").endswith(f"\n\n‹ {link('BG-01')} · {link('BG-03')} ›\n")
    assert out(site, "03-full.txt").endswith(f"\n\n‹ {link('BG-02')} ›\n")


def test_no_chapter_line_without_nav(tmp_path):
    site, r = build(tmp_path, three_chapters())
    assert r.returncode == 0, r.stderr
    assert "‹" not in out(site, "02-full.txt")


def test_chapters_without_chapter_key_are_skipped_over(tmp_path):
    chs = three_chapters(nav=True)
    chs["02"]["meta"]["dict"].pop("chapter_key")
    site, r = build(tmp_path, chs)
    assert r.returncode == 0, r.stderr
    assert out(site, "01-full.txt").endswith(f"‹ {link('BG-03')} ›\n")
    assert out(site, "03-full.txt").endswith(f"‹ {link('BG-01')} ›\n")


def test_single_keyed_chapter_has_no_chapter_line(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, chapter_key="BG-01", nav=True)})
    assert r.returncode == 0, r.stderr
    assert "‹" not in out(site, "01-full.txt")


# --- book-level dict.skip ----------------------------------------------------

def test_book_skip_is_added_before_chapter_skip(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1)}, skip=["इति", "च"])},
                    book_dict={"skip": ["च", "तु"]})
    assert r.returncode == 0, r.stderr
    assert "HEADER:skip=च;तु;इति\n" in out(site, "01.txt")


def test_book_skip_alone(tmp_path):
    site, r = build(tmp_path, {"01": chapter({"01.md": verse(1)})}, book_dict={"skip": "च"})
    assert r.returncode == 0, r.stderr
    assert "HEADER:skip=च\n" in out(site, "01.txt")


def test_book_skip_passes_site_build_validation(tmp_path):
    site, _ = build(tmp_path, {"01": chapter({"01.md": verse(1)})}, book_dict={"skip": ["च"]})
    r = run_script(site, "generate_indices.py")
    assert "unknown key" not in r.stderr, r.stderr

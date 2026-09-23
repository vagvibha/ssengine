"""End-to-end: run the real generate_dict.py (via symlinks, like the
content repos do) against a throwaway site and check what lands in dict/."""
import copy

from conftest import SITE_CONFIG, make_site, read_yaml, run_script

NOTES_CHAPTER = {
    "meta": {"dict": {"type": "notes", "title": "१"}},
    "files": {"01.md": '---\ntitle: एकः\n---\nगद्यम् <dict syns="अ, आ">प्रविष्टिः <notes>टिप्पणी</notes></dict>\n'},
}
EMPTY_NOTES_CHAPTER = {  # dict-enabled, but nothing tagged -> no output file
    "meta": {"dict": {"type": "notes"}},
    "files": {"01.md": "गद्यम् केवलम्\n"},
}
SHLOKA_CHAPTER = {
    "meta": {"dict": {"type": "shloka", "title": "५", "shloka_key_prefix": "KS5,99"}},
    "files": {"01.md": (
        '<div class="shloka" syns="तप्">\nपद्यम् ॥५।१॥\n</div>\n'
        "<anvaya>अन्वयः इह ।</anvaya>\n"
    )},
}
PLAIN_CHAPTER = {"files": {"01.md": "कोऽपि पाठः\n"}}


def standard_texts():
    return {
        "kavya/padya/ks": {"meta": {"title": "कुमारसम्भवम्", "order": 1, "dict": {"folder": "kavya"}},
                           "chapters": {"05": SHLOKA_CHAPTER}},
        "kavya/padya/ka": {"meta": {"title": "किरातार्जुनीयम्", "order": 2, "dict": {"folder": "kavya"}},
                           "chapters": {"01": NOTES_CHAPTER}},
        # declares a folder but no dict-enabled chapters -> not listed
        "kavya/padya/rv": {"meta": {"title": "रघुवंशम्", "order": 3, "dict": {"folder": "kavya"}},
                           "chapters": {"01": PLAIN_CHAPTER}},
        # dict-enabled chapter with no entries -> not listed
        "kavya/padya/mb": {"meta": {"title": "मेघदूतम्", "order": 4, "dict": {"folder": "kavya"}},
                           "chapters": {"01": EMPTY_NOTES_CHAPTER}},
        "kavya/nataka/as": {"meta": {"title": "अभिज्ञानशाकुन्तलम्", "dict": {"folder": "plays"}},
                            "chapters": {"01": NOTES_CHAPTER}},
        # no dict at all
        "kavya/nataka/mv": {"meta": {"title": "मालविकाग्निमित्रम्"}, "chapters": {"01": PLAIN_CHAPTER}},
    }


def test_success_writes_chapter_files_and_meta(tmp_path):
    site = make_site(tmp_path, standard_texts())
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr

    d = site / "dict"
    assert read_yaml(d / "meta.yaml") == {"dictionaries": ["kavya", "plays"]}
    assert read_yaml(d / "kavya" / "meta.yaml") == {"name": "Kavya", "folders": ["ks", "ka"]}
    assert read_yaml(d / "plays" / "meta.yaml") == {"name": "Nataka", "folders": ["as"]}
    assert (d / "meta.yaml").read_text(encoding="utf-8").endswith("dictionaries:\n  - kavya\n  - plays\n")

    # chapter output still lands where it always did
    assert (d / "kavya" / "ks" / "05.txt").exists()
    assert (d / "kavya" / "ka" / "01.txt").exists()
    assert (d / "plays" / "as" / "01.txt").exists()
    assert not (d / "kavya" / "rv").exists()
    assert not (d / "kavya" / "mb" / "01.txt").exists()


def test_chapter_file_contents(tmp_path):
    site = make_site(tmp_path, standard_texts())
    assert run_script(site, "generate_dict.py").returncode == 0

    notes = (site / "dict" / "kavya" / "ka" / "01.txt").read_text(encoding="utf-8")
    assert notes == (
        "HEADER:title=किरातार्जुनीयम् १\nHEADER:type=notes\n"
        "- अ;आ\nप्रविष्टिः <i>टिप्पणी</i>\n"
    )
    shloka = (site / "dict" / "kavya" / "ks" / "05.txt").read_text(encoding="utf-8")
    assert shloka == (
        "HEADER:title=कुमारसम्भवम् ५\nHEADER:type=shloka\n"
        "पद्यम् ॥५।१॥\n====\n+ e:KS5-01;तप्\n++ अन्वयः इह\n<b>अन्वयः</b>\n<i>अन्वयः इह ।</i>\n"
    )


def test_undeclared_folder_fails_build(tmp_path):
    texts = standard_texts()
    texts["kavya/nataka/as"]["meta"]["dict"]["folder"] = "kayva"
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0
    assert "DictConfigError" in r.stderr and "'kayva'" in r.stderr and "kavya/nataka/as/meta.yaml" in r.stderr
    assert not (site / "dict" / "meta.yaml").exists()


def test_undeclared_folder_fails_even_without_enabled_chapters(tmp_path):
    texts = standard_texts()
    texts["kavya/padya/rv"]["meta"]["dict"]["folder"] = "typo"
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "'typo'" in r.stderr


def test_missing_registry_fails_when_texts_use_dict(tmp_path):
    cfg = copy.deepcopy(SITE_CONFIG)
    del cfg["dictionaries"]
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "declared: none" in r.stderr


def test_malformed_registry_fails(tmp_path):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["dictionaries"].append({"name": "Dup", "folder": "kavya"})
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "more than once" in r.stderr


def test_unused_registry_entry_not_listed(tmp_path):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["dictionaries"].insert(0, {"name": "Unused", "folder": "unused"})
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    assert run_script(site, "generate_dict.py").returncode == 0
    assert read_yaml(site / "dict" / "meta.yaml") == {"dictionaries": ["kavya", "plays"]}
    assert not (site / "dict" / "unused").exists()


def test_registry_order_drives_top_level_order(tmp_path):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["dictionaries"].reverse()
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    assert run_script(site, "generate_dict.py").returncode == 0
    assert read_yaml(site / "dict" / "meta.yaml") == {"dictionaries": ["plays", "kavya"]}


def test_same_slug_in_one_folder_fails(tmp_path):
    texts = standard_texts()
    texts["kavya/nataka/ka"] = {"meta": {"title": "अन्यः", "dict": {"folder": "kavya"}}, "chapters": {"01": NOTES_CHAPTER}}
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0 and "dict/kavya/ka/" in r.stderr


def test_no_dict_content_creates_no_dict_dir(tmp_path):
    site = make_site(tmp_path, {"kavya/padya/rv": {"meta": {"title": "रघुवंशम्"}, "chapters": {"01": PLAIN_CHAPTER}}})
    r = run_script(site, "generate_dict.py")
    assert r.returncode == 0, r.stderr
    assert "No dict-enabled chapters" in r.stdout
    assert not (site / "dict").exists()


def test_existing_dict_dir_with_no_output_gets_empty_list(tmp_path):
    site = make_site(tmp_path, {"kavya/padya/rv": {"meta": {"title": "रघुवंशम्"}, "chapters": {"01": PLAIN_CHAPTER}}})
    (site / "dict").mkdir()
    assert run_script(site, "generate_dict.py").returncode == 0
    assert read_yaml(site / "dict" / "meta.yaml") == {"dictionaries": []}


def test_rerun_is_idempotent(tmp_path):
    site = make_site(tmp_path, standard_texts())
    assert run_script(site, "generate_dict.py").returncode == 0
    first = {p: p.read_bytes() for p in (site / "dict").rglob("*") if p.is_file()}
    assert run_script(site, "generate_dict.py").returncode == 0
    second = {p: p.read_bytes() for p in (site / "dict").rglob("*") if p.is_file()}
    assert first == second


def test_malformed_dict_tag_fails_with_context(tmp_path):
    texts = standard_texts()
    texts["kavya/padya/ka"]["chapters"]["01"] = {
        "meta": {"dict": {"type": "notes"}},
        "files": {"01.md": '<dict syns="a">never closed\n'},
    }
    site = make_site(tmp_path, texts)
    r = run_script(site, "generate_dict.py")
    assert r.returncode != 0
    assert "FAILED while processing" in r.stderr and "never closed" in r.stderr

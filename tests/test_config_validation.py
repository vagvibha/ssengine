"""Strict YAML validation: unknown keys and wrong-kind values in
site_config.yaml, gloss_types.yaml and meta.yaml files fail the build."""
import copy

import pytest

import generate_indices as gi
from conftest import GLOSS_TYPES, SITE_CONFIG, make_site, run_script
from test_generate_dict_cli import standard_texts


# ---------------------------------------------------------------------------
# Unit: check_keys
# ---------------------------------------------------------------------------

def test_check_keys_accepts_known_keys_and_empty_values():
    gi.check_keys({"title": "x", "order": 2, "ignore": False, "dict": None}, gi.BOOK_META_KEYS, "m")
    gi.check_keys(None, gi.BOOK_META_KEYS, "m")


@pytest.mark.parametrize("data, message", [
    ({"titel": "x"}, "unknown key(s) 'titel'"),
    ({"title": ["सर्गः-२"]}, "title should be plain text"),
    ({"shloka_toc": "false"}, "shloka_toc should be true or false"),
    ({"dict": "kavya"}, "dict should be a mapping"),
    ({"gloss_types": {"data_type": "x"}}, "gloss_types should be a list"),
    ("just text", "expected a mapping"),
])
def test_check_keys_rejects(data, message):
    with pytest.raises(gi.ConfigError, match=None) as e:
        gi.check_keys(data, gi.BOOK_META_KEYS, "book/meta.yaml")
    assert message in str(e.value) and "book/meta.yaml" in str(e.value)


def test_list_title_error_suggests_quoting():
    with pytest.raises(gi.ConfigError) as e:
        gi.check_keys({"title": ["सर्गः-२"]}, gi.CHAPTER_DICT_KEYS, "ch/meta.yaml: dict")
    assert 'quote it' in str(e.value)


def test_book_source_may_be_a_list():
    gi.validate_book_meta({"title": "x", "source": ["a", "b"]}, "m")


# ---------------------------------------------------------------------------
# End-to-end: both scripts fail on bad YAML
# ---------------------------------------------------------------------------

def _run_both(site):
    return [run_script(site, s) for s in ("generate_indices.py", "generate_dict.py")]


@pytest.mark.parametrize("mutate, message", [
    (lambda t: t["kavya/padya/ka"]["meta"].update(sources="x"), "unknown key(s) 'sources'"),
    (lambda t: t["kavya/padya/ka"]["meta"]["dict"].update(skip=["न"]), "dict: unknown key(s) 'skip'"),
    (lambda t: t["kavya/padya/ka"]["chapters"]["01"]["meta"]["dict"].update(chapter_keys="K"),
     "unknown key(s) 'chapter_keys'"),
    (lambda t: t["kavya/padya/ka"]["chapters"]["01"]["meta"]["dict"].update(title=["१"]),
     "title should be plain text"),
    (lambda t: t["kavya/padya/ka"]["chapters"]["01"]["meta"].update(chapter_display_style="section"),
     "unknown chapter_display_style 'section'"),
    (lambda t: t["kavya/padya/ka"]["meta"].update(order="first"), "'order: 'first'' isn't a number"),
    (lambda t: t["kavya/padya/ka"]["meta"].update(gloss_labels={"notez": "x"}),
     "gloss_labels: references unknown gloss type 'notez'"),
])
def test_bad_meta_fails_both_scripts(tmp_path, mutate, message):
    texts = standard_texts()
    texts["kavya/padya/ka"] = copy.deepcopy(texts["kavya/padya/ka"])
    mutate(texts)
    site = make_site(tmp_path, texts)
    for r in _run_both(site):
        assert r.returncode != 0
        assert message in r.stderr, r.stderr


def test_bad_site_config_fails(tmp_path):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["content_sections"][0]["text_groups"][0]["h2_lable"] = "x"
    site = make_site(tmp_path, standard_texts(), site_config=cfg)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and "unknown key(s) 'h2_lable'" in r.stderr, r.stderr


def test_bad_gloss_types_fails(tmp_path):
    gt = copy.deepcopy(GLOSS_TYPES)
    gt["types"][0]["hidable"] = True
    site = make_site(tmp_path, standard_texts(), gloss_types=gt)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and "unknown key(s) 'hidable'" in r.stderr, r.stderr


def test_unsupported_css_style_fails(tmp_path):
    gt = copy.deepcopy(GLOSS_TYPES)
    gt["types"][0]["css_style"] = "notez"
    site = make_site(tmp_path, standard_texts(), gloss_types=gt)
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and "css_style: 'notez'" in r.stderr, r.stderr


def test_unparseable_meta_fails(tmp_path):
    site = make_site(tmp_path, standard_texts())
    (site / "kavya" / "padya" / "ka" / "meta.yaml").write_text("title: [unclosed\n", encoding="utf-8")
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0 and "could not parse" in r.stderr, r.stderr

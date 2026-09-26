"""default_class wrapping never splits a <details>/<table>, and per-topic
overrides of the परिभाषाः table headings (+ strict topic key checking)."""
import copy
import re

import pytest

import generate_indices as gi
from conftest import SITE_CONFIG, make_site, run_script, _write_yaml


def wrap(body: str, gloss_types: dict, default_class: str = "notes") -> str:
    body = gi.expand_gloss_shorthand(body, gloss_types)
    return gi.process_content_sections(body, default_class, gloss_types)


# ---------------------------------------------------------------------------
# default_class + <details>/<table>
# ---------------------------------------------------------------------------

DETAILS = """Intro.

<details markdown=1 open>
<summary>लोचनम्</summary>
<tika data-name="लोचनम्">
Test
</tika>
</details>

After."""


def test_details_with_gloss_inside_is_not_split(gloss_types):
    out = wrap(DETAILS, gloss_types)
    wrappers = re.findall(r'<div class="gloss[^"]*" data-type="notes">', out)
    assert len(wrappers) == 1  # Intro + details + After: one run, one wrapper
    d_open, d_close = out.index("<details"), out.index("</details>")
    tika = out.index('data-type="tika"')
    assert d_open < tika < d_close                       # tika stayed inside
    assert "</div>" not in out[d_open:tika]              # wrapper didn't close inside
    assert out.rstrip().endswith("</div>")
    assert out.index("</details>") < out.rindex("</div>")  # wrapper closes after it
    assert "<b>लोचनम्</b><br>Test" in out                 # tika rendered on its own merit


def test_table_with_div_inside_is_not_split(gloss_types):
    src = "Before.\n\n<table>\n<tr><td><tika data-name=\"X\">t</tika></td></tr>\n</table>\n\nAfter."
    out = wrap(src, gloss_types)
    t_open, t_close = out.index("<table>"), out.index("</table>")
    seg = out[t_open:t_close]
    assert seg.count("<div") == seg.count("</div>") == 1  # only the tika's own div
    assert len(re.findall(r'data-type="notes"', out)) == 1


def test_standalone_div_outside_details_still_splits_the_default(gloss_types):
    src = DETAILS + '\n\n<tika data-name="Y">standalone</tika>\n\nTail.'
    out = wrap(src, gloss_types)
    assert len(re.findall(r'data-type="notes"', out)) == 2  # before + after the standalone tika
    assert out.index("</details>") < out.index("<b>Y</b>")


def test_details_without_div_unchanged(gloss_types):
    src = "Intro.\n\n<details>\n<summary>s</summary>\n\n```mermaid\ngraph TD; A-->B\n```\n</details>\n\nAfter."
    out = wrap(src, gloss_types)
    assert out.strip() == gi.render_commentary_div("gloss", "notes", "", src, gloss_types)


def test_no_default_class_unchanged(gloss_types):
    body = gi.expand_gloss_shorthand(DETAILS, gloss_types)
    out = gi.process_content_sections(body, "", gloss_types)
    assert 'data-type="notes"' not in out
    assert out.index("<details") < out.index('data-type="tika"') < out.index("</details>")


def test_unbalanced_details_falls_back_to_old_behavior(gloss_types):
    src = "<details>\n<summary>s</summary>\n<tika data-name=\"X\">t</tika>\n\nno close"
    out = wrap(src, gloss_types)  # must not raise, and nothing is absorbed
    assert len(re.findall(r'data-type="notes"', out)) == 2


def test_shloka_inside_details_still_found(gloss_types):
    src = 'x\n\n<details>\n<summary>s</summary>\n<div class="shloka">श्लोकः</div>\n</details>'
    out = wrap(src, gloss_types)
    _, shlokas, _ = gi.extract_shlokas(out, "", [], "", 0)
    assert len(shlokas) == 1


# ---------------------------------------------------------------------------
# Per-topic definitions-table headings
# ---------------------------------------------------------------------------

def topic_site(tmp_path, single_fm: dict, multi_meta: dict):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    cfg["labels"] = {"term_column_heading": "SITE-TERM"}
    chapter = (
        '<topic name="एकम्" define="क">क-def</topic>\n\n'
        '<topic name="द्वे" define="ख">ख-def</topic>\n\n'
        '<topic name="त्रीणि" define="ग">ग-def</topic>\n'
    )
    texts = {"kavya/padya/ka": {"meta": {"title": "क"}, "chapters": {"01": {"files": {"01.md": chapter}}}}}
    site = make_site(tmp_path, texts, site_config=cfg)
    cat = site / "topics" / "cat"
    _write_yaml(cat / "meta.yaml", {"title": "वर्गः"})
    fm = "".join(f"{k}: {v}\n" for k, v in {"title": "एकम्", **single_fm}.items())
    (cat / "one.md").write_text(f"---\n{fm}---\nbody\n", encoding="utf-8")
    _write_yaml(cat / "two" / "meta.yaml", {"title": "द्वे", **multi_meta})
    (cat / "two" / "a.md").write_text("---\norder: 1\n---\npart\n", encoding="utf-8")
    (cat / "three.md").write_text("---\ntitle: त्रीणि\n---\nbody\n", encoding="utf-8")
    return site


def topic_page(site, slug):
    [p] = list((site / "docs").rglob(f"{slug}.md"))
    return p.read_text(encoding="utf-8")


def test_topic_heading_overrides(tmp_path):
    site = topic_site(
        tmp_path,
        {"term_column_heading": "पदम्", "definitions_heading": "लक्षणानि"},
        {"definition_column_heading": "अर्थः", "source_column_heading": "ग्रन्थः"},
    )
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr

    one = topic_page(site, "one")
    assert "## लक्षणानि" in one and "<th>पदम्</th>" in one
    assert "<th>परिभाषा</th>" in one and "<th>मूलम्</th>" in one  # not overridden -> defaults

    two = topic_page(site, "two")
    assert "<th>SITE-TERM</th>" in two                            # site_config label
    assert "<th>अर्थः</th>" in two and "<th>ग्रन्थः</th>" in two
    assert "## परिभाषाः" in two

    three = topic_page(site, "three")
    assert "<th>SITE-TERM</th>" in three and "## परिभाषाः" in three


@pytest.mark.parametrize("where", ["single", "multi"])
def test_unknown_topic_key_is_an_error(tmp_path, where):
    bad = {"term_colum_heading": "x"}
    site = topic_site(tmp_path, bad if where == "single" else {}, bad if where == "multi" else {})
    r = run_script(site, "generate_indices.py")
    assert r.returncode != 0
    assert "term_colum_heading" in r.stderr

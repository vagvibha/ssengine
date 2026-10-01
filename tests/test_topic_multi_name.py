"""`<topic name="X, Y">`: one tag counted for several topics. Every listed
name must be a known topic, and no topic title may contain a comma —
both are hard errors."""
import copy

from conftest import SITE_CONFIG, _write_yaml, make_site, run_script

CHAPTER = (
    '<topic name="माया, अविद्या" context="प्रसङ्गः">पाठः</topic>\n\n'
    '<topic name="अविद्या,माया" define="आवरणम्">आवरण-लक्षणम्</topic>\n\n'
    '<topic name="माया, अविद्या" define="विक्षेपः" entry="विक्षेप-लक्षणम्"/>\n'
)


def build(tmp_path, chapter=CHAPTER, titles=("माया", "अविद्या")):
    cfg = copy.deepcopy(SITE_CONFIG)
    cfg["topics"] = {"dir": "topics", "h1_label": "विषयाः"}
    texts = {"kavya/padya/ka": {"meta": {"title": "क"}, "chapters": {"01": {"files": {"01.md": chapter}}}}}
    site = make_site(tmp_path, texts, site_config=cfg)
    cat = site / "topics" / "cat"
    _write_yaml(cat / "meta.yaml", {"title": "वर्गः"})
    for i, t in enumerate(titles):
        (cat / f"t{i}.md").write_text(f"---\ntitle: \"{t}\"\n---\nविषयः\n", encoding="utf-8")
    return site, run_script(site, "generate_indices.py")


def read(site, rel):
    return (site / "docs" / rel).read_text(encoding="utf-8")


def test_each_topic_gets_the_reference_and_definitions(tmp_path):
    site, r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    for page in ("topics/cat/t0.md", "topics/cat/t1.md"):
        out = read(site, page)
        assert "प्रसङ्गः" in out                                  # the reference
        assert "आवरणम्" in out and "आवरण-लक्षणम्" in out          # paired definition
        assert "विक्षेपः" in out and "विक्षेप-लक्षणम्" in out      # self-closing definition


def test_one_anchor_one_jump_mark_per_topic(tmp_path):
    site, r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    ch = read(site, "kavya/padya/ka/01.md")
    first = ch[ch.index('id="tp1"'):ch.index('id="tp2"')]
    assert first.count("sv-topic-jump") == 2
    assert 'title="माया"' in first and 'title="अविद्या"' in first
    assert 'id="tp3"' not in ch                              # self-closing adds no anchor


def test_single_name_unchanged(tmp_path):
    site, r = build(tmp_path, chapter='<topic name="माया" context="प्रसङ्गः">पाठः</topic>\n')
    assert r.returncode == 0, r.stderr
    assert "प्रसङ्गः" in read(site, "topics/cat/t0.md")
    assert "प्रसङ्गः" not in read(site, "topics/cat/t1.md")


def test_unknown_name_stops_the_build(tmp_path):
    _, r = build(tmp_path, chapter='<topic name="माया, ब्रह्म" context="क">पाठः</topic>\n')
    assert r.returncode != 0 and "unknown topic(s): ब्रह्म" in r.stderr


def test_unknown_single_name_stops_the_build(tmp_path):
    _, r = build(tmp_path, chapter='<topic name="ब्रह्म" context="क">पाठः</topic>\n')
    assert r.returncode != 0 and "unknown topic(s): ब्रह्म" in r.stderr


def test_unknown_name_in_self_closing_stops_the_build(tmp_path):
    _, r = build(tmp_path, chapter='<topic name="ब्रह्म" define="क" entry="ख"/>\n')
    assert r.returncode != 0 and "unknown topic(s): ब्रह्म" in r.stderr


def test_empty_name_in_list_stops_the_build(tmp_path):
    _, r = build(tmp_path, chapter='<topic name="माया, " context="क">पाठः</topic>\n')
    assert r.returncode != 0 and "empty name" in r.stderr


def test_repeated_name_stops_the_build(tmp_path):
    _, r = build(tmp_path, chapter='<topic name="माया, माया" context="क">पाठः</topic>\n')
    assert r.returncode != 0 and "more than once" in r.stderr


def test_comma_in_topic_title_stops_the_build(tmp_path):
    _, r = build(tmp_path, chapter="पाठः\n", titles=("माया", "नायकाः, नायिकाश्च"))
    assert r.returncode != 0 and "contains ','" in r.stderr

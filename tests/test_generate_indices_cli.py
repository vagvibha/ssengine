"""End-to-end smoke test: the real generate_indices.py builds a throwaway
site (via symlinks) and the generated docs look sane."""
from conftest import make_site, run_script
from test_generate_dict_cli import standard_texts


def test_site_build(tmp_path):
    site = make_site(tmp_path, standard_texts())
    r = run_script(site, "generate_indices.py")
    assert r.returncode == 0, r.stderr
    assert (site / "mkdocs.yml").exists()
    assert (site / "docs" / "index.md").exists()

    ka = (site / "docs" / "kavya" / "padya" / "ka" / "01.md").read_text(encoding="utf-8")
    assert "<dict" not in ka and "</dict>" not in ka          # dict tags never reach the site
    assert "<notes>" not in ka and 'data-type="notes"' in ka  # shorthand expanded + rendered
    assert "प्रविष्टिः" in ka                                  # display=True content kept

    ks = (site / "docs" / "kavya" / "padya" / "ks" / "05.md").read_text(encoding="utf-8")
    assert 'data-type="anvaya"' in ks and "<b>अन्वयः</b>" in ks
    assert 'id="s1"' in ks


def test_site_build_is_independent_of_dict_registry(tmp_path):
    """generate_indices.py must not care about dictionaries:/dict.folder
    validation — that's generate_dict.py's job alone."""
    texts = standard_texts()
    texts["kavya/nataka/as"]["meta"]["dict"]["folder"] = "undeclared"
    site = make_site(tmp_path, texts)
    assert run_script(site, "generate_indices.py").returncode == 0

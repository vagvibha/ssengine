"""mkdocs_hooks (Devanagari-safe slugify) and macros_env (xref macro)."""
from types import SimpleNamespace

import pytest

import macros_env
from mkdocs_hooks import devanagari_safe_slugify, expand_superscript_shorthand, on_config, on_page_markdown


@pytest.mark.parametrize("heading,slug", [
    ("प्रभेदाः", "प्रभेदाः"),              # combining marks (ा, ः) survive
    ("ध्वनेः भेदाः", "ध्वनेः-भेदाः"),
    ("<b>Hello</b>, World!", "hello-world"),
    ("  a   b  ", "a-b"),
])
def test_slugify(heading, slug):
    assert devanagari_safe_slugify(heading, "-") == slug


def test_on_config_installs_slugify():
    cfg = on_config({"mdx_configs": {"toc": {"permalink": True}}})
    assert cfg["mdx_configs"]["toc"]["slugify"] is devanagari_safe_slugify
    assert cfg["mdx_configs"]["toc"]["permalink"] is True


def make_xref(src_uri):
    macros = {}
    env = SimpleNamespace(
        page=SimpleNamespace(file=SimpleNamespace(src_uri=src_uri)),
        macro=lambda f: macros.setdefault(f.__name__, f),
    )
    macros_env.define_env(env)
    return macros["xref"]


@pytest.mark.parametrize("src_uri,target,expected", [
    ("shastra/alankarashastra/da/01.md", "topics/x/dhvani.md", "../../../topics/x/dhvani.md"),
    ("shastra/alankarashastra/da/01/index.md", "topics/x/dhvani.md", "../../../../topics/x/dhvani.md"),
    ("index.md", "/topics/x/dhvani/", "topics/x/dhvani.md"),   # leading/trailing slash, no .md
    ("topics/x/a.md", "topics/x/b", "b.md"),
])
def test_xref(src_uri, target, expected):
    assert make_xref(src_uri)(target) == expected


@pytest.mark.parametrize("src,expected", [
    ("सुखं^१ नित्यं^२ स्वप्रकाशं", "सुखं<sup>१</sup> नित्यं<sup>२</sup> स्वप्रकाशं"),
    ("पदम्^१२।", "पदम्<sup>१२</sup>।"),          # multi-digit, punctuation after
    ("x^2 and a^b", "x^2 and a^b"),                 # ASCII digits / letters untouched
    (r"literal \^१ here", "literal ^१ here"),        # escaped
    ("^१ at start", "<sup>१</sup> at start"),
    ("a^१\n```\nb^१\n```\nc^१", "a<sup>१</sup>\n```\nb^१\n```\nc<sup>१</sup>"),  # fenced code untouched
])
def test_superscript_shorthand(src, expected):
    assert expand_superscript_shorthand(src) == expected


def test_on_page_markdown_applies_shorthand():
    assert on_page_markdown("सुखं^१", page=None, config=None, files=None) == "सुखं<sup>१</sup>"

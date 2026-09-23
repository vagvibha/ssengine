"""mkdocs_hooks (Devanagari-safe slugify) and macros_env (xref macro)."""
from types import SimpleNamespace

import pytest

import macros_env
from mkdocs_hooks import devanagari_safe_slugify, on_config


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

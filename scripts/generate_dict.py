#!/usr/bin/env python3
"""
generate_dict.py
==================

Walks every book/chapter with a `dict:` block in its meta.yaml and
writes dict/<folder>/<book>/<chapter>.txt (+ <chapter>-full.txt when
`chapter_key` is set) for the external dictionary-generation workflow,
plus the generated dict/meta.yaml and dict/<folder>/meta.yaml index
files (see "Dictionary registry" below — every `dict.folder` must be
declared in site_config.yaml's `dictionaries:` or the build fails).
Reads SOURCE .md files directly (never docs/), exactly like
generate_indices.py does — this script and that one are independent,
each doing its own pass over the same source tree; neither depends on
the other having run first. Import-only reuse of generate_indices.py
(discovery: SECTIONS/discover_texts/discover_chapters/Text/Chapter/
split_frontmatter/expand_gloss_shorthand) plus dict_extract.py
(<dict>/<dictref> extraction) and dict_render.py (.action/gloss
rendering, shloka key generation).

The full reference for every `dict:` option, tag and output format is
docs/dict.md in this repo.

Any malformed <dict>/<dictref>/shloka-key input or bad `dict:` config
raises (DictSyntaxError / ShlokaKeyError / DictConfigError /
generate_indices.ConfigError propagate straight out of main() with a
non-zero exit code) — there's too much content to eyeball, so a broken build with a
precise file/reason is far safer than silently generating wrong or
partial dictionary data. See dict_extract.py's own docstring for
exactly which cases are fatal.

STATUS — both notes-format and shloka-format are implemented (including
each format's chapter_key full-chapter entry). Confirmed via live
testing against MG's real content (not just the doc's worked example):
  - Whenever `shloka_key_prefix` is set on a dict.type: shloka chapter,
    every shloka's own generated "e:NAME-..." key is prepended to its
    own record's "+" line (as an extra headword, ahead of its syns) —
    this doubles as the lookup target for the bword:// links used in
    the chapter_key full-chapter view (see wrap_marker_with_link,
    which strips the "e:" prefix for the href specifically). So
    shloka_key_prefix now matters independently of chapter_key — set
    it whenever you want per-shloka keys at all, whether or not you
    also want the aggregated full-chapter view.
  - "++" is exactly the अन्वयः-type gloss's own content (tags stripped,
    whitespace collapsed to single spaces); omitted entirely when no
    अन्वयः gloss exists for that shloka.
  - A notes chapter's chapter_key entry is the whole chapter's dict
    view, rendered by dict_render.render_full_chapter_entry: divs kept
    or dropped per dict.tags_keep (default: every gloss type + shloka),
    <dict>/<topic> tags removed with their text kept, <dictref/>
    resolved to bword links, Markdown/HTML reduced to what the
    dictionary supports.
  - A shloka's own gloss divs are everything between its <div
    class="shloka"> and the NEXT such div (or end of the section) —
    only applies for dict.type: shloka (a shloka inside a dict.type:
    notes chapter gets no special treatment at all — see
    render_structural_divs in dict_render.py).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

import generate_indices as gi
import dict_extract as de
import dict_render as dr

DICT_ROOT = gi.ROOT / "dict"
META_FILENAME = "meta.yaml"


# ---------------------------------------------------------------------------
# Dictionary registry (site_config.yaml `dictionaries:`) + meta.yaml output
# ---------------------------------------------------------------------------
#
# Each site's scripts/site_config.yaml declares which top-level dict/
# folders exist and what each dictionary is called:
#
#     dictionaries:
#       - name: Kavya
#         folder: kavya
#       - name: Nataka
#         folder: plays
#
# A text opts in with `dict: folder: <folder>` in its own meta.yaml — and
# that folder MUST be declared here, or the build fails (a typo like
# `kayva` would otherwise silently create a stray dictionary). Several
# texts can share one folder; that's the point of keeping the display
# name here rather than in any one text's meta.yaml.
#
# After a successful run, two kinds of meta.yaml are generated for the
# external dictionary-build tool (both overwritten on every run, never
# hand-edited):
#
#     dict/meta.yaml            dictionaries: [kavya, plays]
#     dict/<folder>/meta.yaml   name: Kavya
#                               folders: [ks, ka]
#
# Only folders/texts that actually had at least one .txt file written on
# THIS run are listed, so the meta always matches what's on disk.


class DictConfigError(ValueError):
    """Bad `dictionaries:` registry in site_config.yaml, or a text whose
    `dict.folder` isn't declared in it. Always fatal."""


def load_dictionaries(site_config: dict) -> dict[str, str]:
    """site_config.yaml's `dictionaries:` list -> {folder: display name},
    in declaration order. Missing/empty -> {} (fine for a site with no
    dict-enabled texts; any text that DOES set dict.folder will then
    fail validation). Anything malformed raises DictConfigError."""
    raw = site_config.get("dictionaries")
    if raw is None:
        return {}
    if not isinstance(raw, list):
        raise DictConfigError(
            f"site_config.yaml: `dictionaries:` must be a list of {{name, folder}} entries, got {raw!r}"
        )
    out: dict[str, str] = {}
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise DictConfigError(f"site_config.yaml: dictionaries[{i}] must be a mapping with name: and folder:, got {entry!r}")
        folder = str(entry.get("folder") or "").strip()
        name = str(entry.get("name") or "").strip()
        if not folder or not name:
            raise DictConfigError(f"site_config.yaml: dictionaries[{i}] needs both a non-empty name: and folder:, got {entry!r}")
        if "/" in folder or "\\" in folder or folder in (".", "..") or folder == META_FILENAME:
            raise DictConfigError(f"site_config.yaml: dictionaries[{i}] folder {folder!r} must be a plain directory name")
        if folder in out:
            raise DictConfigError(f"site_config.yaml: dictionaries: folder {folder!r} is declared more than once")
        out[folder] = name
    return out


def text_dict_folder(text: gi.Text, dictionaries: dict[str, str]) -> str:
    """This text's `dict.folder` ("" if it has none), validated against
    the `dictionaries:` registry — raises DictConfigError if it names a
    folder that isn't declared there. Checked for every text that sets
    dict.folder, whether or not any of its chapters are dict-enabled yet,
    so a typo fails the build straight away."""
    book_dict = text.meta.get("dict") or {}
    if not isinstance(book_dict, dict):
        raise DictConfigError(f"{text.dir}/meta.yaml: `dict:` must be a mapping (e.g. `dict:\\n  folder: kavya`), got {book_dict!r}")
    folder = str(book_dict.get("folder", "") or "").strip()
    if folder and folder not in dictionaries:
        declared = ", ".join(dictionaries) or "none"
        raise DictConfigError(
            f"{text.dir}/meta.yaml: dict.folder {folder!r} is not declared in site_config.yaml "
            f"`dictionaries:` (declared: {declared}). Add it there, or fix the folder name."
        )
    return folder


def build_meta_files(written: dict[str, list[str]], dictionaries: dict[str, str]) -> dict[str, dict]:
    """The generated meta.yaml contents, keyed by path relative to dict/.
    `written` maps folder -> text slugs that had output written this run
    (in discovery order). Top-level folders follow `dictionaries:`
    declaration order; a folder with no written texts is left out."""
    active = [f for f in dictionaries if written.get(f)]
    files: dict[str, dict] = {META_FILENAME: {"dictionaries": active}}
    for folder in active:
        files[f"{folder}/{META_FILENAME}"] = {"name": dictionaries[folder], "folders": list(written[folder])}
    return files


class _IndentedListDumper(yaml.SafeDumper):
    """Indents block lists under their key (`key:\\n  - item`) instead of
    PyYAML's default flush-left style — purely cosmetic, same data."""
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def dump_meta_yaml(data: dict) -> str:
    body = yaml.dump(data, Dumper=_IndentedListDumper, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return "# Generated by generate_dict.py — do not edit by hand.\n" + body


def write_meta_files(dict_root: Path, written: dict[str, list[str]], dictionaries: dict[str, str]) -> list[Path]:
    paths = []
    for rel, data in build_meta_files(written, dictionaries).items():
        path = dict_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump_meta_yaml(data), encoding="utf-8")
        print(f"wrote {path}")
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class DictConfig:
    """This chapter's own `dict:` block, plus its book's (validated) `dict.folder`.
    A chapter with no `dict:` block at all (or no `type:` in it) is not
    dict-enabled — see is_enabled."""

    def __init__(self, text: gi.Text, chapter: gi.Chapter, folder: str):
        self.folder = folder  # already validated against the registry — see text_dict_folder

        block = chapter.meta.get("dict") or {}
        if not isinstance(block, dict):
            raise ValueError(
                f"{text.dir}/{chapter.slug}/meta.yaml: `dict:` must be a mapping "
                f"(e.g. `dict:\\n  type: shloka\\n  shloka_key_prefix: ...`), got {block!r}"
            )
        self.type = str(block.get("type", "")).strip().lower()
        self.title = str(block.get("title", "")).strip()
        self.skip = gi.as_list(block.get("skip"))
        self.auto_shloka = bool(block.get("auto_shloka", True))
        self.chapter_key = str(block.get("chapter_key", "")).strip()
        self.shloka_key_prefix = str(block.get("shloka_key_prefix", "")).strip()
        # None = not set (use the default: every gloss type + shloka);
        # a list (possibly empty) = exactly these names. See
        # dict_render.render_full_chapter_entry.
        self.tags_keep: list[str] | None = (
            [t.lower() for t in gi.as_list(block.get("tags_keep"))] if "tags_keep" in block else None
        )

        where = f"{text.dir}/{chapter.slug}/meta.yaml: dict"
        if block and not self.type:
            raise DictConfigError(f"{where} has no type: (expected 'notes' or 'shloka') — without it nothing is generated")
        if self.type and self.type not in ("notes", "shloka"):
            raise DictConfigError(f"{where}.type '{self.type}' — expected 'notes' or 'shloka'")
        if self.tags_keep is not None:
            if self.type != "notes":
                raise DictConfigError(f"{where}.tags_keep only applies to type: notes chapters")
            if not self.chapter_key:
                raise DictConfigError(f"{where}.tags_keep is set but chapter_key isn't — tags_keep only "
                                      f"affects the chapter_key full-chapter entry")
            never = [t for t in self.tags_keep if t in dr.NEVER_KEEP]
            if never:
                raise DictConfigError(f"{where}.tags_keep: {', '.join(never)} can't be kept (always dropped)")

    @property
    def is_enabled(self) -> bool:
        return bool(self.type)


_TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def write_dict_file(path: Path, content: str) -> None:
    """Write one chapter .txt file with trailing spaces/tabs removed from
    every line. Markdown's two-space hard line break is only there for
    the site; the dictionary builder turns each newline into <br> on its
    own, so trailing whitespace is never meaningful in dict output."""
    path.write_text(_TRAILING_WS_RE.sub("", content), encoding="utf-8")


def out_dir_for(config: DictConfig, text: gi.Text) -> Path:
    return DICT_ROOT / config.folder / text.slug


def base_header(text: gi.Text, config: DictConfig, type_: str, skip: list[str]) -> list[str]:
    """HEADER:title/type, plus HEADER:skip=... only when `skip` is
    non-empty — an empty `dict.skip` is the default (no words to skip),
    so a bare "HEADER:skip=" line for it would just be noise."""
    header = [f"HEADER:title={text.title} {config.title}", f"HEADER:type={type_}"]
    if skip:
        header.append(f"HEADER:skip={';'.join(skip)}")
    return header


# ---------------------------------------------------------------------------
# Notes format
# ---------------------------------------------------------------------------

_BOOK_DIV_NAMES: dict[Path, set[str]] = {}


def book_div_names(text: gi.Text) -> set[str]:
    """Every div name (gloss data-type or class — see
    dict_render.div_name) used anywhere in this book's sections. Cached
    per book: tags_keep is validated against it, so a name that's valid
    for the book can be listed in every chapter's tags_keep even if some
    chapter doesn't happen to use it."""
    if text.dir not in _BOOK_DIV_NAMES:
        names: set[str] = set()
        for ch in gi.discover_chapters(text):
            for section in ch.sections:
                _, body = gi.split_frontmatter(section.read_text(encoding="utf-8"))
                body = gi.expand_gloss_shorthand(body, text.effective_gloss_types, source_for_warning=section)
                names |= dr.div_names_in(body, text.effective_gloss_types)
        _BOOK_DIV_NAMES[text.dir] = names
    return _BOOK_DIV_NAMES[text.dir]


def resolve_tags_keep(text: gi.Text, chapter: gi.Chapter, config: "DictConfig") -> set[str]:
    """The set of div names kept in this chapter's full-chapter entry:
    dict.tags_keep if set (validated — every name must be one of this
    book's gloss types, 'shloka', or a div name used somewhere in this
    book), otherwise the default (every gloss type + shloka)."""
    if config.tags_keep is None:
        return dr.default_tags_keep(text.effective_gloss_types)
    known = dr.default_tags_keep(text.effective_gloss_types) | book_div_names(text)
    unknown = [t for t in config.tags_keep if t not in known]
    if unknown:
        raise DictConfigError(
            f"{text.dir}/{chapter.slug}/meta.yaml: dict.tags_keep: {', '.join(repr(t) for t in unknown)} "
            f"isn't a gloss type or a div class used in this book (known: {', '.join(sorted(known))})"
        )
    return set(config.tags_keep)


def notes_record(syns: list[str], entry_text: str) -> str:
    return f"- {';'.join(syns)}\n{entry_text}"


def process_notes_chapter(text: gi.Text, chapter: gi.Chapter, config: DictConfig) -> bool:
    """Returns True if at least one file was written."""
    wrote = False
    records: list[str] = []
    full_chapter_parts: list[str] = []  # dict view of every section, for chapter_key
    keep = resolve_tags_keep(text, chapter, config) if config.chapter_key else set()  # validate before writing anything

    for section in chapter.sections:
        raw = section.read_text(encoding="utf-8")
        fm, body = gi.split_frontmatter(raw)
        body = gi.expand_gloss_shorthand(body, text.effective_gloss_types, source_for_warning=section)
        _, dict_body, captures = de.extract_dict_views(body, source_for_warning=section)

        for cap in captures:
            if not cap.syns:
                gi.warn(f"{section}: <dict> entry with no syns= — skipping (nothing to key it by)")
                continue
            entry_text = dr.render_notes_entry(cap.raw_content, text.effective_gloss_types, source_for_warning=section)
            records.append(notes_record(cap.syns, entry_text))

        if config.chapter_key:
            full_chapter_parts.append(dict_body.strip())

    out_dir = out_dir_for(config, text)
    out_dir.mkdir(parents=True, exist_ok=True)

    header = base_header(text, config, "notes", config.skip)
    out_path = out_dir / f"{chapter.slug}.txt"
    if not records:
        print(f"skipping {out_path} (no entries)")
    else:
        content = "\n".join(header) + "\n" + "\n\n".join(records) + "\n"
        write_dict_file(out_path, content)
        wrote = True
        print(f"wrote {out_path} ({len(records)} record(s))")

    if config.chapter_key:
        full_body = "\n\n".join(full_chapter_parts).strip()
        full_path = out_dir / f"{chapter.slug}-full.txt"
        if not full_body:
            print(f"skipping {full_path} (no entries)")
        else:
            dropped: dict[str, int] = {}
            full_entry = dr.render_full_chapter_entry(full_body, text.effective_gloss_types, keep, dropped)
            if dropped:
                summary = ", ".join(f"{name} ×{n}" for name, n in sorted(dropped.items()))
                print(f"  {full_path}: left out (not in tags_keep): {summary}")
            full_content = "\n".join(header) + "\n" + notes_record([config.chapter_key], full_entry) + "\n"
            write_dict_file(full_path, full_content)
            wrote = True
            print(f"wrote {full_path} (1 record)")

    return wrote


# ---------------------------------------------------------------------------
# Shloka format
# ---------------------------------------------------------------------------

def wrap_marker_with_link(shloka_text: str, key: str) -> str:
    """The chapter_key full-chapter view's own transform: the shloka's
    LAST ॥...॥ marker gets wrapped in a bword:// link to its key — per
    the spec's own example, the href drops the "e:" prefix that
    shloka_dict_key always returns (`e:KS-03-05` -> `bword://KS-03-05`)."""
    href_key = key[2:] if key.startswith("e:") else key
    matches = list(dr.MARKER_RE.finditer(shloka_text))
    m = matches[-1]
    return f'{shloka_text[:m.start()]}<a href="bword://{href_key}">{m.group(0)}</a>{shloka_text[m.end():]}'


def process_shloka_chapter(text: gi.Text, chapter: gi.Chapter, config: DictConfig) -> bool:
    """Returns True if at least one file was written."""
    wrote = False
    records: list[str] = []
    full_chapter_parts: list[str] = []  # for chapter_key, back-to-back shloka text (linked if shloka_key_prefix set)

    if config.chapter_key and not config.shloka_key_prefix:
        gi.warn(
            f"{text.dir}/{chapter.slug}: chapter_key is set but shloka_key_prefix is not — the full-chapter "
            f"entry will still be generated, but with no <a href=\"bword://...\"> links on any shloka"
        )

    for section in chapter.sections:
        raw = section.read_text(encoding="utf-8")
        fm, body = gi.split_frontmatter(raw)
        body = gi.expand_gloss_shorthand(body, text.effective_gloss_types, source_for_warning=section)
        # dict.type: shloka doesn't use <dict> tags at all (synonyms/skip come from
        # frontmatter or the shloka div's own attrs) — but a bare <dictref> can still
        # appear (e.g. right after a shloka's own ॥...॥ marker, inside its div), so
        # this call still matters, purely for that.
        body, captures = de.extract_dict_and_ref_tags(body, source_for_warning=section)
        if captures:
            gi.warn(
                f"{section}: <dict> tag found in a dict.type: shloka chapter — shloka format doesn't use "
                f"<dict> tags (synonyms/skip come from frontmatter or the shloka div's own attrs); ignored"
            )

        fm_dict = fm.get("dict") or {}
        file_syns = gi.as_list(fm_dict.get("syns"))
        file_skip = gi.as_list(fm_dict.get("skip"))

        tree = gi.parse_divs(body)
        shloka_nodes = [n for n in tree if n.base_cls == "shloka"]

        for i, node in enumerate(shloka_nodes):
            attrs = gi.parse_attrs(node.attrs_str)
            div_syns = de.as_syn_list(attrs.get("syns", ""))
            div_skip = de.as_syn_list(attrs.get("skip", ""))
            syns = div_syns or file_syns
            skip = div_skip or file_skip

            shloka_raw = body[node.tag_end:node.inner_end]

            # A shloka_key_prefix-generated key is itself a valid headword
            # (it's prepended to the "+" line below), so it counts as a
            # de-facto syn — only skip the shloka if there's neither an
            # explicit syn NOR a generated key to look it up by.
            key = None
            if config.shloka_key_prefix:
                key = dr.shloka_dict_key(shloka_raw, config.shloka_key_prefix, source_for_warning=section)

            if not syns and not key:
                gi.warn(f"{section}: shloka with no syns= (div attr or frontmatter) and no shloka_key_prefix — skipping (nothing to key it by)")
                continue

            _, shloka_text = de.resolve_dictrefs_in_text(shloka_raw, source_for_warning=section)
            shloka_text = shloka_text.strip()

            group_start = node.end
            group_end = shloka_nodes[i + 1].start if i + 1 < len(shloka_nodes) else len(body)
            group_text = body[group_start:group_end]
            anvaya, blocks = dr.render_shloka_group(group_text, text.effective_gloss_types, source_for_warning=section)

            # the key doubles as a headword so a bword:// link elsewhere (e.g. the
            # full-chapter view below) can resolve straight to this record
            record_syns = [key] + syns if key else syns
            records.append(dr.shloka_record(shloka_text, skip, record_syns, anvaya, blocks))

            if config.chapter_key:
                if key:
                    full_chapter_parts.append(wrap_marker_with_link(shloka_text, key))
                else:
                    full_chapter_parts.append(shloka_text)

    out_dir = out_dir_for(config, text)
    out_dir.mkdir(parents=True, exist_ok=True)

    header = base_header(text, config, "shloka", config.skip)
    header.append("HEADER:show_anvaya=false")  # always, for every dict.type: shloka file
    if hasattr(config, 'auto_shloka') and not config.auto_shloka:
        header.append(f"HEADER:auto_shloka=false")
    out_path = out_dir / f"{chapter.slug}.txt"
    if not records:
        print(f"skipping {out_path} (no entries)")
    else:
        content = "\n".join(header) + "\n" + "\n\n".join(records) + "\n"
        write_dict_file(out_path, content)
        wrote = True
        print(f"wrote {out_path} ({len(records)} record(s))")

    if config.chapter_key:
        # "always of type notes" (spec) — the full-chapter view is a single
        # notes-style record, even for a dict.type: shloka chapter.
        full_header = base_header(text, config, "notes", config.skip)
        full_body = "\n\n".join(full_chapter_parts).strip()
        full_path = out_dir / f"{chapter.slug}-full.txt"
        if not full_body:
            print(f"skipping {full_path} (no entries)")
        else:
            full_content = "\n".join(full_header) + "\n" + notes_record([config.chapter_key], full_body) + "\n"
            write_dict_file(full_path, full_content)
            wrote = True
            print(f"wrote {full_path} (1 record)")

    return wrote


# ---------------------------------------------------------------------------
# Chapter dispatch
# ---------------------------------------------------------------------------

def process_chapter(text: gi.Text, chapter: gi.Chapter, folder: str) -> bool:
    """Returns True if at least one file was written for this chapter."""
    config = DictConfig(text, chapter, folder)
    if not config.is_enabled:
        return False
    if not config.folder:
        raise DictConfigError(
            f"{text.dir}/{chapter.slug}/meta.yaml has a dict: block, but the book's meta.yaml has no "
            f"dict.folder — nothing would be generated")

    if config.type == "notes":
        return process_notes_chapter(text, chapter, config)
    return process_shloka_chapter(text, chapter, config)


def main() -> int:
    dictionaries = load_dictionaries(gi.SITE_CONFIG)
    any_enabled = False
    written: dict[str, list[str]] = {}   # folder -> text slugs with output, discovery order
    owner: dict[tuple[str, str], Path] = {}  # (folder, slug) -> text dir, to catch output collisions

    for section in gi.SECTIONS:
        for text in gi.discover_texts(section):
            folder = text_dict_folder(text, dictionaries)
            if folder:
                prev = owner.setdefault((folder, text.slug), text.dir)
                if prev != text.dir:
                    raise DictConfigError(
                        f"{text.dir} and {prev} both write to dict/{folder}/{text.slug}/ — "
                        f"two texts sharing a dictionary folder need different directory names"
                    )
            for chapter in gi.discover_chapters(text):
                try:
                    config = DictConfig(text, chapter, folder)
                    if config.is_enabled:
                        any_enabled = True
                    if process_chapter(text, chapter, folder):
                        slugs = written.setdefault(folder, [])
                        if text.slug not in slugs:
                            slugs.append(text.slug)
                except Exception as e:
                    print(f"\nFAILED while processing {text.dir}/{chapter.slug}: {e}", file=sys.stderr)
                    raise

    if not any_enabled:
        print("No dict-enabled chapters found (no chapter meta.yaml has a dict: block with a type:).")

    # Meta files only after everything above succeeded. Skipped entirely
    # when there's no output and no dict/ yet (e.g. a site with no
    # dict-enabled content), so this never creates an empty dict/.
    if written or DICT_ROOT.exists():
        write_meta_files(DICT_ROOT, written, dictionaries)

    if gi.WARNINGS:
        print(f"\n{len(gi.WARNINGS)} warning(s) — see above.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Configuration reference

Every YAML file the engine reads, and every key it accepts. Dictionary
settings (the `dict:` blocks) are in [dict.md](dict.md); the topics area
and the `<topic>` tag are in [topics.md](topics.md).

## Directory layout

```
<site repo>/
  scripts/
    site_config.yaml           site-wide settings (below)
    gloss_types.yaml           gloss/commentary types (below)
    ssengine/                  this engine (git submodule)
  [<content_root>/]            optional wrapper for everything below, down to assets/
  <section>/                   one per content_sections: entry, e.g. kavya/
    <group>/                   one per text_groups: entry (texts/ if none are declared)
      <book>/
        meta.yaml              book settings — required
        <chapter>/             a chapter made of several section files:
          meta.yaml            chapter settings — optional
          *.md                 section files, in filename order (zero-pad: 01, 02, … 10)
        <chapter>.md           or: a single-file chapter (no meta.yaml possible)
  topics/                      the topics area — see topics.md
  assets/                      copied verbatim to docs/assets/
```

With `content_root: contents` in `site_config.yaml`, the sections,
`topics/` and `assets/` all move under `contents/`. Generated output
(`docs/`, `mkdocs.yml`, `dict/`) stays at the repo root, and page URLs
don't change: they come from each section's `dir:` alone.

A `meta.yaml` directly inside `<section>/` is not read. Section-level
display settings live in `site_config.yaml`'s `content_sections:`. Chapters
are ordered by directory or file name; a numeric name (`01`) gets a
numbered nav label, anything else is used as-is.

## Strict validation

Both `generate_indices.py` and `generate_dict.py` fail the build when a
YAML file has:

- **an unknown key.** Nothing reads it, so it's almost always a typo
  (`sources:` for `source:`) or a key at the wrong level (`dict.skip` in a
  book's `meta.yaml`, where only a chapter reads it).
- **a value of the wrong kind:**
  - Text keys must be plain text. `title: [सर्गः-२]` is read by YAML as a
    one-item list, so quote it: `title: "[सर्गः-२]"`.
  - true/false keys must be unquoted `true` or `false`. The string
    `"false"` would count as true.
  - Lists and mappings must be lists and mappings.
- **a value outside its allowed set:** `chapter_display_style`, a
  gloss type's `css_style`, a `gloss_labels` key, and a non-numeric
  `order`.
- **YAML that can't be parsed at all.**

The allowed keys live in one place, the schema tables near the top of
`scripts/generate_indices.py`. This document lists the same keys.

Kinds used below: **text** (a scalar; numbers are fine), **bool**
(`true`/`false`), **list** (a YAML list, or a single value treated as a
one-item list), **mapping**.

---

## `scripts/site_config.yaml` (per site)

| Key | Kind | Meaning |
|---|---|---|
| `site_name` | text | Site title in `mkdocs.yml`. |
| `google_analytics_property` | text | GA4 id (`G-…`). Omit for no analytics. |
| `content_root` | text | Folder, relative to the repo root, holding all content sections, `topics/` and `assets/` (e.g. `contents`). Omit to keep them at the repo root. Must exist; can't be `docs`, `scripts`, `dict` or `site`. Doesn't affect URLs. |
| `theme` | mapping | `primary`, `accent`: Material colours. `language`: Material's UI language code (e.g. `sa`). |
| `labels` | mapping | UI strings the engine writes (see below). Any label left out keeps its default. |
| `topics` | mapping | The topics area (see below). Omit if the site has no topics. |
| `default_chapter_word` | text | Last-resort chapter nav word (default `अध्यायः`). |
| `maintain_shloka_linebreak` | bool | Site default: keep each pada of a shloka on its own line (`<br />`). Default false. A book can override it. |
| `skip_text_index` | bool | Site default for the book key of the same name (single-chapter books go straight to their chapter page). Default false. A book can override it. |
| `dictionaries` | list of mappings | `{name, folder}` per dictionary. See [dict.md](dict.md#site-registry). |
| `content_sections` | list of mappings | The top-level content areas (see below). |

**`labels:`** — `home_title`, `home_nav_label`, `home_button_label`,
`intro_nav_label`, `author_label`, `shloka_list_heading`,
`references_heading`, `definitions_heading`, `term_column_heading`,
`definition_column_heading`, `source_column_heading`, `about_nav_label`
(link text for the About page, default `विषये`).

**About page** — optional. Put an `about.md` at the content root (next to
`assets/`). It is copied to `docs/about.md` with the usual Home pill (any
frontmatter is kept), and linked from one small line at the bottom of the
home page (`<div class="sv-home-footer">`, style it in the site's own
`custom.css` if wanted). It is not added to nav. No `about.md`, no page
and no link.

**`topics:`**

| Key | Kind | Meaning |
|---|---|---|
| `dir` | text | Directory under the content root holding topic categories (default `topics`). |
| `h1_label` | text | Heading and home-card/nav label for the topics area. |
| `chandas_alankara` | bool | Turn on the meter/figure glossaries (`chandas.md`, `alankara.md`) and the छन्दः/अलङ्काराः columns. Default false. |

**`content_sections:`** entries

| Key | Kind | Meaning |
|---|---|---|
| `dir` | text | Directory under the content root, e.g. `kavya`. Also the URL prefix. |
| `h1_label` | text | Section heading and nav label. |
| `default_chapter_word` | text | Chapter nav word for this section. |
| `text_groups` | list of mappings | `{dir, h2_label}`: one sub-directory of texts per group, each under its own heading. |
| `h2_text_label` | text | Heading for the single implicit `texts/` group, used only when `text_groups` is omitted. |

---

## `scripts/gloss_types.yaml` (per site)

| Key | Kind | Meaning |
|---|---|---|
| `supported_css_styles` | list | The only valid `css_style` values (each matches a `.sv-style-<name>` CSS rule). |
| `types` | list of mappings | One entry per gloss `data-type`. |

**`types:`** entries (also the schema for a book's own `gloss_types:`)

| Key | Kind | Meaning |
|---|---|---|
| `data_type` | text | The `data-type="…"` value, also usable as a shorthand tag (`<notes>…</notes>`). |
| `class` | text | Div class it's written under: `gloss` (default) or e.g. `vada`. |
| `css_style` | text | One of `supported_css_styles`. Missing = a warning; not in the list = an error. |
| `label` | text | Fixed label shown before the content. |
| `label_from_attr` | text | Read the label from this div attribute (e.g. `data-name`). If the type also has `label`, that is the fallback for instances that don't set the attribute: with `label: "पूर्वपक्षः"` and `label_from_attr: label`, `<objection>` shows पूर्वपक्षः and `<objection label="कर्मकाण्डी">` shows कर्मकाण्डी. |
| `hideable` | bool | Member of the page's Show/Hide group. Default true. |
| `hidden_by_default` | bool | Starts hidden on page load. |
| `boxed` | text | `open` or `closed`: the shorthand tag's content (`<tika>…</tika>`) is put in a collapsible `<details>` box inside the gloss, starting expanded (`open`) or collapsed (`closed`). The type's label becomes the box's `<summary>` instead of being printed before the content. Show/Hide hides the whole box. Shorthand only — a hand-written `<div>` of this type isn't boxed. Website only — the dictionary shows a boxed gloss like any other (label + content). |
| `exclude_site` | bool | Leave this type out of the website: every div of it (shorthand or hand-written) is removed with its content, including anything nested inside it, before topic tags, `<dict>` tags and shlokas are processed. Default false. Website only — the dictionary is unaffected (use `dict.tags_keep` there). Setting it on the type a chapter uses as `default_class` is an error. To exclude a type in one book only, give that book its own full `gloss_types:` entry. |

**Nesting.** Shorthand tags can nest, e.g. a bhashya holding its own
vada and notes, followed by a tika with vada of its own:

```html
<bhashyam>
…
<objection>…</objection>
<notes>…</notes>
<refute>…</refute>
…
</bhashyam>

<tika data-name="आनन्दगिरिः">
…
<objection label="बौद्धः">…</objection>
<refute>…</refute>
</tika>
```

Each nested tag gets its own label, style and Show/Hide membership, and
stays inside its container (hiding a hideable container hides
everything in it). `default_class` never wraps text inside a
container: that text belongs to the container. Use shorthand tags for
this. A hand-written `<div class="gloss">` opening inside another
`gloss` div still ends the first one, as it always has (the tolerance
for unclosed hand-written divs). In the dictionary, a nested gloss is
rendered inside its container's `<i>…</i>`; in a full-chapter entry
each nested type is kept or dropped by `tags_keep` on its own, and
dropping a container drops everything in it.

---

## Book `meta.yaml` (`<section>/<group>/<book>/meta.yaml`)

| Key | Kind | Meaning |
|---|---|---|
| `title` | text | **Required** (a book without it is skipped with a warning). |
| `author` | text | Shown on the book's index page. |
| `source` | any | Informational only (where the text came from). Never read. |
| `order` | number | Position among texts in its group (then by title). |
| `ignore` | bool | Skip this book entirely. |
| `header` | text | Markdown shown at the top of the book's index page. |
| `chapters` | text | Heading above the chapter list (default `अध्यायाः / भागाः`). |
| `chapter_type` | text | Word used in numeric chapter nav labels, e.g. `सर्गः` → "सर्गः 1". |
| `default_shloka_type` | text | `data-type` given to a `<div class="shloka">` that has none. |
| `default_class` | text | Class that text outside any div is wrapped in (e.g. `dialog-block`). A `<details>` or `<table>` is never split: it goes whole inside the wrapper, and any divs in it still render as their own type. |
| `gloss_types` | list of mappings | Book-only gloss types or full overrides (schema as in `gloss_types.yaml`). |
| `gloss_labels` | mapping | `data_type: label` overrides of a type's fixed label. Unknown type = error. |
| `maintain_shloka_linebreak` | bool | Overrides the site default. |
| `shloka_toc` | bool | Default for whether shlokas are listed in a chapter's श्लोकसूची (default true). |
| `dict` | mapping | Only `folder`. See [dict.md](dict.md#book-metayaml). |
| `skip_text_index` | bool | Overrides the site default. Single-chapter books only (else a build error): no book index page. Links to the book go straight to its chapter page, whose H1 is just the book title and whose ⬆ goes to the section page. `author`/`header`/`chapters` are then unused. |

## Chapter `meta.yaml` (`<book>/<chapter>/meta.yaml`, optional)

| Key | Kind | Meaning |
|---|---|---|
| `chapter_name` | text | Nav label (else `chapter_type`/section word + number). |
| `chapter_display_style` | text | `full_chapter` (default: one page) or `sections` (a landing page plus a page per `.md` file). |
| `ignore` | bool | Skip this chapter entirely (site and dictionary). |
| `default_shloka_type` | text | Overrides the book's. |
| `default_class` | text | Overrides the book's. |
| `shloka_toc` | bool | Overrides the book's. |
| `dict` | mapping | Makes the chapter dictionary-enabled. See [dict.md](dict.md#chapter-metayaml). |

## Topic category `meta.yaml` (`topics/<category>/meta.yaml`)

| Key | Kind | Meaning |
|---|---|---|
| `title` | text | **Required** (a category without it is skipped with a warning). |
| `order` | number | Position among categories (then by title). |
| `expanded_by_default` | bool | Default true: the category's topics are listed under a heading. False: listed inside a collapsed `<details>`. |

## Topic keys (strictly validated)

A single-file topic's frontmatter (`topics/<category>/<topic>.md`) and a
multi-file topic's `meta.yaml` (`topics/<category>/<topic>/meta.yaml`)
take exactly these keys; anything else is an error.

| Key | Kind | Meaning |
|---|---|---|
| `title` | text | **Required.** Also the name `<topic name="…">` tags must use. |
| `order` | number | Position among topics in its category (then by title). |
| `definitions_heading` | text | This page's परिभाषाः heading. Overrides `labels:` in `site_config.yaml`. |
| `term_column_heading` | text | Same, for the table's term column. |
| `definition_column_heading` | text | Same, for the definition column. |
| `source_column_heading` | text | Same, for the source column. |
| `references_heading` | text | This page's सन्दर्भाः heading (the list of places the topic is referenced from). |
| `topic_display_style` | text | Multi-file topic `meta.yaml` only: `single_page` (default: all parts on one page) or `sections` (a page per part, plus separate definitions and references pages). See [topics.md](topics.md#sections-mode). Anything else is an error. |

Each heading falls back to `site_config.yaml`'s `labels:`, then the
built-in default.

---

## Markdown frontmatter (not strictly validated)

Frontmatter in these `.md` files isn't checked for unknown keys yet, so
a typo here is silently ignored.

**Section files** (`<chapter>/*.md`, and a single-file `<chapter>.md`):

| Key | Kind | Meaning |
|---|---|---|
| `title` | text | `sections` mode only: the section's name on the chapter's landing page and in back-links from topic pages. Default: the filename. |
| `ignore` | bool | Skip this section file entirely. In a single-file `<chapter>.md`, skips the whole chapter. |
| `chandas` | text | Default meter for every shloka in the file (a shloka's own `data-chandas=` wins). |
| `alankara` | list | Default figure(s) for every shloka in the file (a shloka's own `data-alankara=` wins). |
| `dict` | mapping | `syns`, `skip`: shloka-format dictionary defaults. See [dict.md](dict.md#shloka-format). |

Any other key is ignored by the engine. Generated pages carry no
frontmatter, so `{{ page.meta.… }}` can't read these either — use
`{% set name = "…" %}` in the body instead.

**Files inside a multi-file topic directory** (`topics/<category>/<topic>/*.md`):
`order` (the order they're joined in, or listed in `sections` mode;
default: filename) and `title` (`sections` mode only: the part's name on
the topic's landing page and in its page heading; default: filename).

**`topics/chandas.md` / `topics/alankara.md`:** `title` (default
`chandas` / `alankara`), `order`.

---

## Which setting wins

When the same thing can be set at several levels, the most specific one
wins. Left to right is least to most specific; "—" means it can't be set
at that level.

| Setting | Site | Book `meta.yaml` | Chapter `meta.yaml` | Section frontmatter | On the element itself |
|---|---|---|---|---|---|
| Shloka type | — | `default_shloka_type` | `default_shloka_type` | — | `<div class="shloka" data-type="…">` |
| Wrapper for loose text | — | `default_class` | `default_class` | — | any explicit `<div>` / gloss tag |
| Shloka listed in श्लोकसूची | (true) | `shloka_toc` | `shloka_toc` | — | `toc="true"` / `toc="false"` |
| Keep shloka line breaks | `maintain_shloka_linebreak` | `maintain_shloka_linebreak` | — | — | — |
| Skip the book index page | `skip_text_index` | `skip_text_index` | — | — | — |
| Meter / figure | — | — | — | `chandas` / `alankara` | `data-chandas=` / `data-alankara=` |
| Chapter nav label | `default_chapter_word` → section's `default_chapter_word` | `chapter_type` (+ number) | `chapter_name` | — | — |
| Gloss type config | `gloss_types.yaml` | `gloss_types` (replaces the whole entry), `gloss_labels` (label only) | — | — | `toggle-hide="true"` / `"false"` |
| Topic-page headings (definitions table, सन्दर्भाः) | `labels:` | — | — | — | topic frontmatter / `meta.yaml` |
| Gloss type left out of the site | `gloss_types.yaml` `exclude_site` | `gloss_types` (whole entry) | — | — | — |

Two details:
- A book's `gloss_types:` entry replaces the site's entry for that type
  entirely — any key it leaves out (`boxed`, `hideable`, …) is unset, not
  inherited.
- `shloka_toc`, `maintain_shloka_linebreak` and `skip_text_index` count as set whenever the
  key is present, so `false` at the book level overrides a site-level
  `true`.

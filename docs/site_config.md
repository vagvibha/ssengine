# Configuration reference

Every YAML file the engine reads, and every key it accepts. Dictionary
settings (the `dict:` blocks) are in [dict.md](dict.md).

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
| `theme` | mapping | `primary`, `accent`: Material colours. `language`: Material's UI language code (e.g. `sa`). |
| `labels` | mapping | UI strings the engine writes (see below). Any label left out keeps its default. |
| `topics` | mapping | The topics area (see below). Omit if the site has no topics. |
| `default_chapter_word` | text | Last-resort chapter nav word (default `अध्यायः`). |
| `maintain_shloka_linebreak` | bool | Site default: keep each pada of a shloka on its own line (`<br />`). Default false. A book can override it. |
| `dictionaries` | list of mappings | `{name, folder}` per dictionary. See [dict.md](dict.md#site-registry). |
| `content_sections` | list of mappings | The top-level content areas (see below). |

**`labels:`** — `home_title`, `home_nav_label`, `home_button_label`,
`intro_nav_label`, `author_label`, `shloka_list_heading`,
`references_heading`, `definitions_heading`, `term_column_heading`,
`definition_column_heading`, `source_column_heading`.

**`topics:`**

| Key | Kind | Meaning |
|---|---|---|
| `dir` | text | Repo-root directory holding topic categories (default `topics`). |
| `h1_label` | text | Heading and home-card/nav label for the topics area. |
| `chandas_alankara` | bool | Turn on the meter/figure glossaries (`chandas.md`, `alankara.md`) and the छन्दः/अलङ्काराः columns. Default false. |

**`content_sections:`** entries

| Key | Kind | Meaning |
|---|---|---|
| `dir` | text | Directory under the repo root, e.g. `kavya`. |
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
| `label_from_attr` | text | Or: read the label from this div attribute (e.g. `data-name`). |
| `hideable` | bool | Member of the page's Show/Hide group. Default true. |
| `hidden_by_default` | bool | Starts hidden on page load. |
| `boxed` | text | `open` or `closed`: the shorthand tag (`<tika>…</tika>`) is wrapped in a collapsible `<details>` box, starting expanded (`open`) or collapsed (`closed`). The type's label becomes the box's `<summary>` instead of being printed inside. Shorthand only — a hand-written `<div>` of this type isn't boxed. |

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

## Chapter `meta.yaml` (`<book>/<chapter>/meta.yaml`, optional)

| Key | Kind | Meaning |
|---|---|---|
| `chapter_name` | text | Nav label (else `chapter_type`/section word + number). |
| `chapter_display_style` | text | `full_chapter` (default: one page) or `sections` (a landing page plus a page per `.md` file). |
| `full_chapter_label` | text | `sections` mode only: also generate a whole-chapter page, listed under this label. |
| `default_shloka_type` | text | Overrides the book's. |
| `default_class` | text | Overrides the book's. |
| `shloka_toc` | bool | Overrides the book's. |
| `dict` | mapping | Makes the chapter dictionary-enabled. See [dict.md](dict.md#chapter-metayaml). |

## Topic `meta.yaml`

- **Category** (`topics/<category>/meta.yaml`): `title` (text, required),
  `order` (number), `expanded_by_default` (bool, default true — false
  collapses the category behind a `<details>`).
- **Multi-file topic** (`topics/<category>/<slug>/meta.yaml`): same keys
  as a single-file topic's frontmatter (below).

## Topic keys (strictly validated)

A single-file topic's frontmatter (`topics/<category>/<topic>.md`) and a
multi-file topic's `meta.yaml` take exactly these keys; anything else is
an error.

| Key | Kind | Meaning |
|---|---|---|
| `title` | text | **Required.** |
| `order` | number | Position among topics in its category (then by title). |
| `definitions_heading` | text | This page's परिभाषाः heading. Overrides `labels:` in `site_config.yaml`. |
| `term_column_heading` | text | Same, for the table's term column. |
| `definition_column_heading` | text | Same, for the definition column. |
| `source_column_heading` | text | Same, for the source column. |

Each heading falls back to `site_config.yaml`'s `labels:`, then the
built-in default.

---

## Other Markdown frontmatter (not strictly validated)

Frontmatter in the `.md` files below isn't checked for unknown keys yet.
Keys the engine reads:

- **Section files:** `title` (section page title in `sections` mode),
  `ignore` (skip the file), `chandas`, `alankara` (default meter/figures
  for its shlokas), `dict: {syns, skip}` (shloka-format dictionary
  defaults, see [dict.md](dict.md#shloka-format)).
- **Files inside a multi-file topic directory:** `order`.

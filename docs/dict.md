# Dictionary generation (`dict/`)

`scripts/generate_dict.py` reads the source `.md` files (never `docs/`)
and writes text files for the external dictionary-build tool:

```
dict/meta.yaml                         generated index (see below)
dict/<folder>/meta.yaml                generated index
dict/<folder>/<book>/<chapter>.txt     one record per entry / shloka
dict/<folder>/<book>/<chapter>-full.txt  the whole chapter as one record (chapter_key)
```

Trailing spaces and tabs are removed from every line of every output
file: Markdown's two-space line break only matters on the site, and the
dictionary builder turns each newline into `<br>` itself. A file with no
records is not written. Any input error fails the run (see
[Errors](#errors)). Unknown keys in any `dict:` block fail both this
script and the site build (see [site_config.md](site_config.md#strict-validation)).

---

## Configuration

### Site registry

In `scripts/site_config.yaml`:

```yaml
dictionaries:
  - name: Kavya        # display name, written to dict/kavya/meta.yaml
    folder: kavya      # top-level folder under dict/
```

### Book `meta.yaml`

```yaml
dict:
  folder: kavya        # must be declared in dictionaries:, else the build fails
```

`folder` is the only key allowed here. Everything else goes in the
chapter's `meta.yaml`. Two books sharing a folder must have different
directory names.

### Chapter `meta.yaml`

A chapter is dictionary-enabled when its `meta.yaml` has a `dict:` block.

| Key | Kind | Formats | Meaning |
|---|---|---|---|
| `type` | text | both | **Required.** `notes` or `shloka`. |
| `title` | text | both | Appended to the book title in `HEADER:title=`. Quote bracketed values: `title: "[सर्गः-१]"`. |
| `skip` | list | both | Words for `HEADER:skip=` (omitted when empty). Chapter-only, no book-level inheritance. |
| `chapter_key` | text | both | Also write `<chapter>-full.txt`: the whole chapter as one notes record under this key. |
| `tags_keep` | list | notes | Which divs the full-chapter record keeps (see [below](#full-chapter-record-notes)). Needs `chapter_key`. |
| `shloka_key_prefix` | text | shloka | Generate a key for every shloka (see [Shloka keys](#shloka-keys)). |
| `auto_shloka` | bool | shloka | `false` adds `HEADER:auto_shloka=false`. Default true. |

The build fails if:
- `dict:` has keys but no `type`, or `type` isn't `notes`/`shloka`
- the book has no `dict.folder`
- `tags_keep` is set on a shloka chapter or without `chapter_key`, lists
  `details`, or names something unknown

---

## Markup

### `<dict>` — a notes entry

```html
<dict syns="अ, आ">content shown on the site AND used as the entry</dict>
<dict syns="अ" display="False">entry only — removed from the site</dict>
<dict syns="अ" entry="short entry text"/>
```

- `syns` is comma (or semicolon) separated. An entry with no `syns` is
  skipped with a warning.
- The self-closing form never displays. `display=` on it must be absent
  or `"False"`.
- Nesting, an unclosed tag or a stray `</dict>` fails the build.
- The tags themselves never reach the site.

### `<dictref/>` — a dictionary-only cross-reference

```html
<dictref text=" (Ref) " ref="Y"/>
```

Removed from the site entirely. In dictionary text it becomes
`<a href="bword://Y"> (Ref) </a>`: inside `<dict>` entries, in shloka
text, and in the full-chapter record. A missing `text` or `ref` fails the
build.

---

## Notes format (`type: notes`)

```
HEADER:title=<book title> <dict.title>
HEADER:type=notes
HEADER:skip=w1;w2            (only when skip is non-empty)
- syn1;syn2
<entry text>

- syn3
<entry text>
```

One record per `<dict>` tag. Entry text rendering:
- `[(…)]{: .action}` spans → `<i>(…)</i>`
- gloss divs → `<b>label</b><i>content</i>` (or `<i>content</i>` for a
  type with no label)
- `<div class="shloka">` → its bare text
- everything else (including `**bold**`) is left exactly as written

### Full-chapter record (notes)

With `chapter_key: AS-01`, `<chapter>-full.txt` holds one record, `- AS-01`,
whose entry is the whole chapter (all its `.md` files in order):

- **Divs** are named by their gloss `data-type` (for gloss-routed
  classes such as `gloss`, `vada`) or else by their class (`shloka`,
  `vritti`, …).
  - A div whose name is in the keep list keeps its content: a gloss as
    `<b>label</b><i>…</i>`, anything else as plain text.
  - Any other div is left out **with its content**.
  - Nested divs follow the same rule on their own, so an unlisted div
    inside a kept one is still dropped.
  - A div with no class passes its content through.
  - Each left-out div name is reported on the console with a count, so a
    class-name typo is easy to spot.
- **Keep list:** `dict.tags_keep` if set, which must name gloss types,
  `shloka`, or div classes used somewhere in the book. Otherwise the
  default: every gloss type plus `shloka`. `tags_keep: []` keeps plain
  text only.
- **`<dict>` / `<topic>` tags** are removed and their text kept.
  `display="False"` and self-closing `<dict>` entries are left out, since
  they aren't part of the text. `<dictref/>` becomes its bword link.
- **Removed entirely:** `<details>` blocks (never keepable), `<audio>`,
  `<video>`, `<script>`, `<style>`, HTML comments, images, footnote
  markers and definitions, `{{ … }}` / `{% … %}` macros, stray
  `{: …}` attribute lists.
- **Markdown:**
  - Headings become `<b>heading</b>`.
  - Links, including `{{ xref() }}` ones, become their text.
  - `.action` spans become `<i>…</i>`, and other `{: .cls}` spans become
    their text.
  - `**bold**`, `*italic*`, list markers and newlines stay as written.
- **HTML:** only `<b>`, `<i>`, `<u>`, `<br>` and bword links survive. Any
  other tag is removed and its text kept.
- A line left holding nothing but removed material is dropped, and runs
  of blank lines collapse to one.

The per-entry `<chapter>.txt` is unaffected by any of this.

---

## Shloka format (`type: shloka`)

No `<dict>` tags; a stray one is warned about and ignored. Each
`<div class="shloka">` becomes one record. Its glosses are everything
from that div up to the next shloka div, or the end of the file.

```
HEADER:title=<book title> <dict.title>
HEADER:type=shloka
HEADER:skip=w1;w2            (only when skip is non-empty)
HEADER:show_anvaya=false     (always)
HEADER:auto_shloka=false     (only when auto_shloka: false)
<shloka text>
====
- <skip words>               (omitted when empty)
+ <key>;<syns>               (key first when shloka_key_prefix is set)
++ <अन्वयः text, final । dropped>   (omitted when there is no anvaya gloss)
<b>label</b>
<i>gloss</i>
<br>
<b>label</b>
<i>gloss</i>
```

- **syns / skip per shloka:** the div's own `syns=` / `skip=` attributes,
  or else the section file's frontmatter `dict: {syns, skip}`.
- A shloka with neither syns nor a generated key is skipped with a
  warning.

### Shloka keys

`shloka_key_prefix: "NAME,w1,w2,…"` takes as many trailing numbers from the
shloka's last `॥…॥` marker as there are width tokens. Each number is
zero-padded to its token's length (the token's digits don't matter, only
how many there are). For the marker `॥५।९।३॥`:

| Prefix | Key |
|---|---|
| `KS5,99` | `e:KS5-03` |
| `KS,9,99` | `e:KS-9-03` |
| `R,9,99,999` | `e:R-5-09-003` |

A shloka with no marker, or too few numbers for the prefix, fails the
build.

### Full-chapter record (shloka)

With `chapter_key`, `<chapter>-full.txt` is one notes-type record holding
every shloka's text back to back. Each shloka's ending marker is linked
to its own record (`<a href="bword://KS5-03">॥५।९।३॥</a>`) when
`shloka_key_prefix` is set; otherwise a warning is printed and there are
no links. `tags_keep` doesn't apply.

---

## Generated index files

After a successful run (both regenerated every time, never hand-edited):

```yaml
# dict/meta.yaml
dictionaries: [kavya, plays]      # folders with output this run, in registry order
# dict/<folder>/meta.yaml
name: Kavya
folders: [ks, ka]                 # books with output this run, in site order
```

## Errors

Fatal (non-zero exit; the generated index files aren't updated, though
chapter files written earlier in the same run stay):
- malformed `<dict>` / `<dictref>`
- a bad shloka marker or `shloka_key_prefix`
- a bad `dictionaries:` registry or undeclared `dict.folder`
- any `dict:` config error listed above
- any unknown key or wrong-kind value in any YAML file

The failing book and chapter are printed before the traceback.

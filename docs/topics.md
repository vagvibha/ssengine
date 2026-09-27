# Topics (विषयाः) and the `<topic>` tag

A site can have a topics area: a set of hand-written pages, one per
subject (रसः, ध्वनिः, …). Texts link into them with `<topic>` tags, and
each topic page automatically collects everything tagged for it:

- a **परिभाषाः** table: every definition of a term, from every text, with
  a link back to the exact passage;
- a **सन्दर्भाः** list: every place the topic is discussed.

The chandas/alankara glossaries are a separate mechanism that lives in
the same area (see [the end of this page](#chandas-and-alankara-glossaries)).

## Turning it on

In `scripts/site_config.yaml`:

```yaml
topics:
  dir: topics          # repo-root directory (default: topics)
  h1_label: विषयाः     # heading, home card and nav label (default: विषयाः)
```

Leave `topics:` out entirely for a site with no topics area.

## Layout

```
topics/
  <category>/                  a group of topics, e.g. sahitya/
    meta.yaml                  title (required), order, expanded_by_default
    <topic>.md                 a single-file topic, OR:
    <topic>/                   a multi-file topic:
      meta.yaml                the topic's keys (title, order, …)
      *.md                     joined in their own order: (default: filename)
  chandas.md, alankara.md      glossaries (only with chandas_alankara: true)
```

Every topic must be inside a category. A `.md` file directly under
`topics/` (other than the two glossaries) is ignored with a warning.

The keys each file takes are in [site_config.md](site_config.md). In
short:

| File | Keys |
|---|---|
| category `meta.yaml` | `title` (required), `order`, `expanded_by_default` |
| topic frontmatter / multi-file topic `meta.yaml` | `title` (required), `order`, `definitions_heading`, `term_column_heading`, `definition_column_heading`, `source_column_heading`, `references_heading` — strictly checked |
| a file inside a multi-file topic | `order` |

A multi-file topic is for a subject too long for one file. Its files are
joined into one page with nothing added between them, exactly as if they
were one file, so give each its own `##` heading if you want one.

## What a topic page shows

For `topics/sahitya/rasa.md` the engine writes `docs/topics/sahitya/rasa.md`
containing, in order:

1. the nav bar (home, and ⬆ to the topics listing);
2. `# <title>`, unless the body already starts with its own `# ` heading;
3. the body, as written (plain Markdown; `{{ xref(…) }}` works);
4. **परिभाषाः**: only if at least one definition names this topic. A
   table with three columns: the term, the definition (linked to its
   passage) and its source (`text — chapter`, plus `— section` in
   `sections` mode). Rows are sorted by term; repeated terms share one
   merged term cell. The heading and column names come from `labels:` in
   `site_config.yaml`, and a topic can override any of the four in its
   own frontmatter.
5. **सन्दर्भाः**: only if at least one reference names this topic. One
   line per reference: `[context](link to the passage) — text — chapter`.
   References appear in build order (sections, then texts, in their
   normal order). The heading is `labels: references_heading` in
   `site_config.yaml`; a topic can override it with its own
   `references_heading`.

The topics listing page (`docs/topics/index.md`) lists every category in
`order`. A category with `expanded_by_default: false` is collapsed behind
a `<details>`.

## The `<topic>` tag

Written anywhere in a text's section files: inside prose, a shloka, or a
gloss. It isn't processed inside topic pages themselves. There are two
forms.

### Paired: `<topic …>passage</topic>`

```html
<topic name="रसः" context="रसस्य स्वरूपम्">विभावानुभावव्यभिचारिसंयोगाद्रसनिष्पत्तिः</topic>
```

| Attribute | Required | Meaning |
|---|---|---|
| `name` | yes | The topic page's `title`, exactly. |
| `context` | one of these | Adds a सन्दर्भाः line to the topic page, with this text as the link. |
| `define` | two | Adds a परिभाषाः row to the topic page for the term given here, using the passage as the definition. |

What each combination gets you:

| You write | On the text page | On the topic page |
|---|---|---|
| `name` + `context` | the passage, then a small ↗ link to the topic | a सन्दर्भाः line |
| `name` + `define` | same | a परिभाषाः row |
| `name` + `context` + `define` | same | both |
| `name` only | same | nothing (warning) |

Details:

- **The passage itself is shown unchanged.** The tag is replaced by an
  invisible anchor around it, so back-links land on the exact spot, not
  just the top of the page.
- **`define` doesn't have to equal `name`.** Several terms can collect on
  one topic page, e.g. `name="साधनचतुष्टयम्" define="शमः"` in one place
  and `name="साधनचतुष्टयम्" define="दमः"` in another.
- **Write definitions as plain text.** For the table cell, HTML tags in
  the passage are stripped and each line becomes its own line in the
  cell. Markdown (`**bold**`, links) is not rendered there and will show
  literally.
- **Repeated references are merged.** Within one chapter, a second
  reference to the same topic with the same `context` text is dropped;
  only the first is listed. Use a different `context` to list both.
- **No nesting.** A `<topic>` opened inside another is left as literal
  text, with a warning.

### Self-closing: `<topic … />`

A definition that isn't shown anywhere in the text: for example, a
standard definition you want on the topic page without publishing the
passage it comes from.

```html
<topic name="साधनचतुष्टयम्" define="तितिक्षा" entry="सहनं सर्वदुःखानामप्रतीकारपूर्वकम्" />
```

| Attribute | Required | Meaning |
|---|---|---|
| `name` | yes | The topic page's `title`. |
| `define` | yes | The term. |
| `entry` | yes | The definition text. Line breaks in it are kept. |

It adds a परिभाषाः row marked with a small ● (hover: टिप्पणीरूपेण उक्तम्),
and its source link opens the chapter page at the top, since there's no
passage to point to. The tag itself is removed from the page. `context`
isn't allowed here (it's ignored with a warning).

### Sections mode and combined chapter pages

In a `sections`-mode chapter, each back-link points to the section's
own page, and its label includes the section's `title`. If the chapter
also has a `full_chapter_label` page, tags on that combined page still
get anchors and ↗ links, but don't add rows or lines a second time.

### Warnings

The build still succeeds; the tag just does less.

| Problem | Result |
|---|---|
| `name` doesn't match any topic's `title` | Passage shown, no ↗ link, nothing added. |
| No `name` | Tag removed, passage shown, nothing added. |
| Neither `context` nor `define` | Anchor and ↗ link only. |
| `define` with an empty passage | No row added. |
| Self-closing tag missing `define` or `entry` | Nothing added. |
| `<topic>` never closed, or `</topic>` with no opening tag | Left as literal text. |

## Chandas and alankara glossaries

With `topics: chandas_alankara: true` in `site_config.yaml`, two more
pages are read: `topics/chandas.md` (meters) and `topics/alankara.md`
(figures of speech). Frontmatter: `title`, `order`.

Each is a hand-written page with one or more HTML tables. A row whose
`<tr>` has a bare `data-glossary-entry` attribute is an entry; its first
cell is the entry's name:

```html
<tr data-glossary-entry>
  <td>वियोगिनी</td>
  <td>…</td>
</tr>
```

Shlokas name their meter and figures with `chandas:` / `alankara:` in a
section file's frontmatter, or `data-chandas="…"` /
`data-alankara="a, b"` on the shloka itself. The name must match an
entry's first cell exactly; anything else gets a warning.

For each entry the engine generates a detail page: the row's other
columns plus every shloka tagged with it. The detail page isn't in the
nav; it's reached by clicking the entry's name, which becomes a link in
the table. The श्लोकसूची tables also get छन्दः and अलङ्काराः columns.
Without `chandas_alankara: true`, none of this happens and the two files
are ignored.

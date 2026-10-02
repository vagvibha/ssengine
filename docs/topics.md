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
  dir: topics          # under content_root (default: topics)
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
      meta.yaml                the topic's keys (title, order, topic_display_style, …)
      *.md                     the parts, in their own order: (default: filename)
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
| multi-file topic `meta.yaml` only | `topic_display_style`: `single_page` (default) or `sections` — strictly checked |
| a file inside a multi-file topic | `order`, `title` (`sections` mode) |

A multi-file topic is for a subject too long for one file. By default
(`topic_display_style: single_page`) its files are joined into one page
with nothing added between them, exactly as if they were one file, so
give each its own `##` heading if you want one. With `sections`, each
file gets its own page instead — see [Sections mode](#sections-mode).

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

### Sections mode

`topic_display_style: sections` in a multi-file topic's `meta.yaml`
splits it across several pages. For `topics/advaita/maya/` with parts
`01.md` and `02.md`:

| Page | Contents |
|---|---|
| `docs/topics/advaita/maya.md` | The landing page: nav bar, `# <title>`, a list of the parts, then a second list linking to the परिभाषाः and सन्दर्भाः pages (each only if it has entries). Same path as a single-page topic, so topic tags, nav and `xref("topics/advaita/maya.md")` link here in either mode. |
| `docs/topics/advaita/maya/01.md`, `…/02.md` | One page per part: ⬆ to the landing page and ←/→ between parts. `# <topic title> — <part title>` unless the part starts with its own `# ` heading. The part title is its `title:` frontmatter, else its filename. |
| `docs/topics/advaita/maya/_definitions.md` | The परिभाषाः table, with ⬆ to the landing page. |
| `docs/topics/advaita/maya/_references.md` | The सन्दर्भाः list, with ⬆ to the landing page. |

The definitions and references pages aren't in the parts' ←/→ sequence;
they're reached from the landing page. The topic has one nav entry, its
landing page. A part file named `_definitions.md`, `_references.md` or
`index.md` is a build error in sections mode. To link to a passage
inside a part, `xref()` the part's own page, e.g.
`xref("topics/advaita/maya/02.md")` — see
[Linking to a topic](#linking-to-a-topic).

The topics listing page (`docs/topics/index.md`) lists every category in
`order`. A category with `expanded_by_default: false` is collapsed behind
a `<details>`.

## Linking to a topic

For a hand-written link to a topic, or to a spot on its page, use the
`xref()` macro. It works from any page: a text's section file or another
topic.

### The page

```markdown
[ध्वनिः]({{ xref("topics/sahitya/dhvani") }})
```

The path is the topic's file under the content root, so it starts with
`topics/`. The `.md` is optional; `xref("topics/sahitya/dhvani.md")` is
the same link. `xref()` turns it into the right relative link from the
page it's written on, so you never count `../`.

### A heading on the page

Put the `#anchor` after the `}}`, as plain text, with no quotes:

```markdown
[लक्षणा]({{ xref("topics/sahitya/shabdashakti") }}#लक्षणा)
```

Devanagari headings get a readable id: the heading text itself,
lowercased, spaces turned into `-`, punctuation dropped. So
`## लक्षणा` has the id `लक्षणा`.

Better still, give the heading an explicit id. The link then survives
rewording the heading:

```markdown
## लक्षणा {#lakshana}
```

```markdown
[लक्षणा]({{ xref("topics/sahitya/shabdashakti") }}#lakshana)
```

An explicit id **replaces** the automatic one: once a heading has
`{#lakshana}`, `#लक्षणा` no longer exists on that page.

### Any other spot on the page

An explicit id isn't limited to headings. Any of these gives a spot on
the page an id you can link to:

| Where | Write |
|---|---|
| a heading | `## परीक्षा {#pariksha}` |
| a whole paragraph | `{: #para-one }` on the line right after the paragraph |
| a word or phrase | `**पदम्**{: #inline-one }` (right after the formatted text) |
| anywhere, invisibly | `[](){#spot-one}` or `<span id="spot-one"></span>` |

All of these also work inside gloss blocks, since the engine renders
Markdown inside them. A link to one is written exactly like a heading
link: `…}}#para-one)`.

### A topic in sections mode

A [sections-mode](#sections-mode) topic's headings are on its part
pages, not its landing page. Link to the part file itself:

```markdown
[श्रवणम्]({{ xref("topics/vishaya/sadhana/shravana") }}#श्रवणम्)
```

`xref("topics/vishaya/sadhana")` plus `#श्रवणम्` opens the landing
page, which lists the parts and has no such heading. In the default
`single_page` mode the reverse holds: all parts are on
`topics/vishaya/sadhana.md`, and there is no `sadhana/shravana` page.
A plain link to the topic (no `#`) works in either mode. A link to a
heading inside a part has to change if you switch the topic's
`topic_display_style`.

If a part has no `# ` heading of its own, the engine adds
`# <topic> — <part title>` at the top of its page; link to the part page
without an `#anchor`.

### Cautions

- **Ids must be unique on each output page.** A `full_chapter` chapter
  joins all its sections onto one page, and a `single_page` topic joins
  all its parts, so an id used in two of them clashes.
- **Don't use `tp1`, `tp2`, …** The engine gives every paired `<topic>`
  tag an anchor named that way.
- **A wrong anchor doesn't fail the build.** `mkdocs build --strict`
  still passes; MkDocs only prints an `INFO` line saying the page has no
  such anchor. A wrong **page** in `xref()` does fail the build. After
  adding or changing anchors, check the build output for those `INFO`
  lines.

## The `<topic>` tag

Written anywhere in a text's section files: inside prose, a shloka, or a
gloss. It isn't processed inside topic pages themselves.

### The two forms

```html
<topic name="रसः" context="रसस्य स्वरूपम्">विभावानुभावव्यभिचारिसंयोगाद्रसनिष्पत्तिः</topic>
<topic name="साधनचतुष्टयम्" define="तितिक्षा" entry="सहनं सर्वदुःखानामप्रतीकारपूर्वकम्"/>
```

- **Paired, `<topic …>body</topic>`:** the body is shown on the page
  unchanged, with an invisible anchor around it (so back-links land on
  that exact spot) and a small ↗ link to the topic after it.
- **Self-closing, `<topic … />`:** nothing is shown on the page — no
  anchor, no ↗. Back-links from the topic page open the chapter page at
  the top. Use it for something you want on the topic page without a
  passage in the text to point at.

| Attribute | Paired | Self-closing | Meaning |
|---|---|---|---|
| `name` | required | required | The topic's `title`, exactly — or several, comma-separated (below). |
| `define` | optional | optional | Adds a परिभाषाः row for this term. |
| `entry` | not allowed | with `define` | The definition text (the body is the definition in the paired form). |
| `context` | optional | optional | Adds a सन्दर्भाः line with this text as the link. |

### What goes on the topic page

- **`define`** adds a परिभाषाः row: the term, and as its definition the
  body (paired) or `entry` (self-closing).
- **`context`** adds a सन्दर्भाः line labelled with its text.
- **Neither, paired:** a सन्दर्भाः line labelled with the body itself.
  It's a link label, so the body must be at most 70 characters (about
  25–30 Devanagari aksharas); for a longer passage, add a short
  `context`.
- **Both `define` and `context`:** both a row and a line.

| You write | परिभाषाः | सन्दर्भाः |
|---|---|---|
| `<topic name="X" define="Y" entry="Z"/>` | Y = Z | — |
| `<topic name="X" define="Y">Z</topic>` | Y = Z | — |
| `<topic name="X" context="Y"/>` | — | Y (opens the page top) |
| `<topic name="X">Y</topic>` | — | Y |
| `<topic name="X" context="C">long passage</topic>` | — | C |
| `<topic name="X" define="Y" context="C">Z</topic>` | Y = Z | C |
| `<topic name="X" define="Y" context="C" entry="Z"/>` | Y = Z (●) | C (opens the page top) |

A definition from the self-closing form is marked with a small ● (hover:
टिप्पणीरूपेण उक्तम्), since there's no passage behind it.

Details:

- **`define` doesn't have to equal `name`.** Several terms can collect on
  one topic page, e.g. `name="साधनचतुष्टयम्" define="शमः"` in one place
  and `name="साधनचतुष्टयम्" define="दमः"` in another.
- **A definition is ordinary Markdown.** In the table cell, `**bold**`
  and `*italic*` render. A plain line break is just a space, as anywhere
  in Markdown; end a line with two spaces or write `<br>` to break it. A
  blank line leaves a visible gap. Links show as their text only, since
  the whole cell already links to the passage. Other HTML tags are
  dropped and their text kept. The passage on the text page is
  unaffected.
- **Repeated references are merged.** Within one chapter, a second
  reference to the same topic with the same label is dropped; only the
  first is listed. Use a different `context` to list both.

### Several topics at once: `name="X, Y"`

When a passage belongs to more than one topic, list them all, separated
by commas (spaces around them don't matter):

```html
<topic name="माया, अविद्या" define="आवरणम्">…</topic>
```

Both forms accept it. The tag then counts for each topic exactly as if
it had been tagged for that topic alone. On the text page a paired tag
gets one ↗ per topic, each showing its topic's name on hover.

### Errors

Anything the engine can't use as written stops the build, with the file
and the tag in the message:

- a name that isn't a topic's `title`, an empty name in a list
  (`name="माया, "`), the same name twice, or no `name` at all;
- a topic `title` containing a comma;
- an attribute not in the table above (e.g. `source=`), or `entry` on a
  paired tag;
- `define` without `entry`, or `entry` without `define` (self-closing);
- a self-closing tag with neither `define`+`entry` nor `context`;
- an empty `define`, `context` or `entry`; an empty body where it's the
  definition or the label;
- a body label over 70 characters;
- a `<topic>` opened inside another, a `</topic>` with no opening tag,
  or a `<topic>` never closed.

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

# Pulling a passage from another file: `<extract/>`

`<extract/>` shows a passage from another section file of the same text
without copying it there. Typical uses:

- in a `chapter_display_style: sections` chapter, one more section that
  gathers some glosses from its sibling files (only the kārikās, or each
  file's सारः, …);
- a whole new chapter that gathers, say, the `### सारः` of every section
  in the text.

```html
### कारिका २

<extract href="da1-02.md" heading="सारः"/>
<extract href="../01/da1-04.md" types="karika, anvaya"/>
```

Put each tag on its own line, and repeat it as many times as needed
(one per source file, or several from the same file).

## Attributes

| Attribute | Required | Meaning |
|---|---|---|
| `href` | yes | The source `.md` file, relative to the file the tag is in. It must be a section file of the **same text** (another chapter is fine), not ignored and not the file itself. |
| `heading` | no | Only the passage under this heading: from the line after it up to the next heading of the same or higher level, or the end of the div the heading is in, or the end of the file. The heading itself is left out (write your own above the tag). It must appear exactly once in the source file and is matched like `<topic heading="...">`: the exact heading text, without the `#`s or a trailing `{#id}`. Without `heading`, the whole file is used. |
| `types` | no | Comma-separated data-types to keep — gloss types (`notes`, `anvaya`, `tika`, …), shloka data-types (`karika`, …), or `shloka` for any verse. A matching div is kept whole (with anything nested in it); a non-matching div is searched for matching divs inside it. Text that isn't inside any div counts as the source chapter's `default_class` (e.g. `vritti`), or — under `heading=` — as the type of the div the heading is in. An unknown name fails the build. Without `types`, everything is kept. |

`heading` and `types` can be combined: the heading picks the passage,
`types` filters it.

## What happens to the pulled text

It is processed exactly as if it had been typed in place (gloss labels,
Show/Hide, heading rules of sections mode, …), except:

- `<dict>`/`<dictref>` tags are removed (their text stays). Dictionary
  output never changes because of an extract — `generate_dict.py` doesn't
  expand extracts at all.
- `<topic>` tags are removed (their text stays), so topic pages don't get
  a second back-reference or definition.
- Pulled verses get `data-extracted="true"` (usable as a CSS hook). They
  are shown and anchored as usual, but get no row in the page's
  श्लोकसूची and no chandas/alankara back-reference — the original page
  already has those. A verse without its own `data-type` gets the source
  chapter's `default_shloka_type`.
- The wrapping div of a `heading=` passage is not copied (a `सारः` inside
  a hidden-by-default `<notes>` would otherwise start hidden), so that
  text — like any untagged text — takes the **extract page's**
  `default_class`.
- After each pulled passage comes a small link back to where it came
  from: `<p class="sv-extract-source"><a …>↗ <section title></a></p>`
  (prefixed with the chapter label when it's another chapter). Style it
  in your site's `custom.css`.

Relative Markdown links and image paths inside the pulled text are not
rewritten, so they break when the extract page is in another directory
(`mkdocs build --strict` reports them). Use `xref()` in content that
gets extracted.

## Errors (the build stops)

- `href` missing, not a `.md`, the file itself, not a section of this
  text (missing, `ignore: true`, or in another text);
- the source is in the **same chapter** and that chapter is
  `full_chapter` — its content is already on the page; extracting from
  your own chapter needs `chapter_display_style: sections`;
- the source file itself contains `<extract/>` (no nesting);
- `heading` not found, or found more than once;
- an unknown name in `types`, an empty `heading`/`types`, an unknown
  attribute, or a tag that isn't self-closing (`<extract …/>`).

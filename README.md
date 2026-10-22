# Static Site Engine

Shared build-engine scripts for the साहित्यशास्त्रम् (sahitya) and शास्त्रम्
(shastra) MkDocs sites. Each site's own repo keeps its own content and
`config/` — this repo holds the Python engine code, pulled in as a git
submodule at `ssengine/` in each site's repo root.

## What's here

- `generate_indices.py` — the main site-generation script. Now genuinely
  identical between both sites (verified byte-for-byte): the one real
  behavioral difference between them — the chandas/alankara meter/figure
  glossary, which shastra's content has no use for — is a config-gated
  feature (`topics: chandas_alankara: true/false` in each site's own
  `site_config.yaml`, default false), not a code fork. When off: no
  chandas.md/alankara.md are read even if present, the श्लोकसूची list has
  no छन्दः/अलङ्काराः columns, and beautifulsoup4 (only needed for that
  hand-authored-table parsing) is never imported at all — a site with
  the flag off doesn't need it installed.
- `dict_extract.py` — `<dict>`/`<dictref>` tag extraction for the
  external dictionary-generation workflow.
- `dict_render.py` — rendering/key-generation for that same workflow.
- `generate_dict.py` — walks the source tree and writes `dict/` output,
  plus the `dict/meta.yaml` / `dict/<folder>/meta.yaml` index files (see
  "Dictionaries" below).
- `mkdocs_hooks.py` — Devanagari-safe slugification hook.
- `macros_env.py` — the `xref()` Jinja macro for hand-authored
  cross-references.

Each site keeps its own `config/` at its repo root (not in this repo):
`site_config.yaml`, `gloss_types.yaml`, `stylesheets/` and
`javascripts/` — those are per-site decisions, not engine code. `docs/`
and `mkdocs.yml` are entirely generated (`config/stylesheets/` and
`config/javascripts/` are copied into `docs/` on every run), so a site
gitignores both.

## Reference docs

- [`docs/site_config.md`](docs/site_config.md) — the directory layout;
  every key in `site_config.yaml`, `gloss_types.yaml`, book/chapter/topic
  `meta.yaml` and Markdown frontmatter; and which setting wins when the
  same thing is set at several levels.
- [`docs/topics.md`](docs/topics.md) — the topics area: topic pages, the
  `<topic>` tag (every form and what it produces), and the
  chandas/alankara glossaries.
- [`docs/dict.md`](docs/dict.md) — the dictionary workflow: every `dict:`
  option, the `<dict>`/`<dictref>` tags, and both output formats
  (including the full-chapter record and `tags_keep`).

Every YAML file is strictly validated: an unknown key, or a value of the
wrong kind (e.g. `title: [x]`, which YAML reads as a list), fails the
build instead of being silently ignored.

## Dictionaries (`dict/`)

Each site declares its dictionaries in its own `config/site_config.yaml`:

```yaml
dictionaries:
  - name: Kavya        # display name, written to dict/kavya/meta.yaml
    folder: kavya      # top-level folder under dict/
  - name: Nataka
    folder: plays
```

A text opts in with `dict: folder: kavya` in its own `meta.yaml` (several
texts can share one folder). If a text's `dict.folder` isn't declared in
`dictionaries:`, `generate_dict.py` fails the build with an error, even
when none of that text's chapters are dict-enabled yet, so a typo is
caught straight away. The build also fails if two texts in the same folder
have the same directory name, because they would overwrite each other's
output.

After a successful run, `generate_dict.py` writes the chapter `.txt` files
as before, then two kinds of index file for the dictionary-build tool:

```yaml
# dict/meta.yaml
dictionaries:
  - kavya
  - plays
```

```yaml
# dict/kavya/meta.yaml
name: Kavya
folders:
  - ks
  - ka
```

Only folders and texts that had at least one `.txt` file written on that
run are listed. Top-level folders follow `dictionaries:` order, and texts
follow the site's normal text order. Both files are regenerated on every
run, so don't edit them by hand. Old output folders are not deleted, but
they drop out of the meta files.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

`tests/` has unit tests for the helpers (gloss shorthand, div parsing,
`<dict>`/`<dictref>` extraction, dict rendering and shloka keys, the
dictionary registry and meta files, the slugify hook, `xref()`), plus
end-to-end tests that build a small throwaway site. That site mounts
this repo at `ssengine/` (a symlink standing in for the submodule), like
a real content repo, and runs `generate_dict.py` / `generate_indices.py`
in a subprocess from the site root.
`.github/workflows/tests.yml` runs the suite on every push to `main` and
on every pull request.

## Setting this up on GitHub

```bash
cd ssengine
git init
git add .
git commit -m "Initial shared engine: dict generation + macros + hooks"
git branch -M main
git remote add origin git@github.com:<you>/ssengine.git
git push -u origin main
```

## Wiring it into a content repo

The engine is a git submodule mounted at `ssengine/` in the site's repo
root. There are no symlinks and no site-level `scripts/` directory: every
script is run from the site's repo root, which is how the engine finds
the site (`config/`, the content, and where to write `docs/`,
`mkdocs.yml` and `dict/`).

```bash
git submodule add git@github.com:<you>/ssengine.git ssengine

python ssengine/scripts/generate_indices.py   # docs/ + mkdocs.yml
python ssengine/scripts/generate_dict.py      # dict/
mkdocs build --strict
```

The generated `mkdocs.yml` loads its hooks and macros from
`ssengine/scripts/`, so the engine must be mounted there. The scripts
fail (before writing anything) if they're run from anywhere but the repo
root, or if the engine running isn't the one at `<root>/ssengine/`.

A site's own files: `config/` (`site_config.yaml`, `gloss_types.yaml`,
`stylesheets/`, `javascripts/`), its content, and a `.gitignore` with
`docs/` and `mkdocs.yml`. Remember to set
`topics: chandas_alankara: true` in sahitya's `site_config.yaml` (other
sites need no change — false is the default).

### Moving from the old `scripts/ssengine` + symlinks setup

From the site's repo root:

```bash
git mv scripts/ssengine ssengine       # moves the submodule and updates .gitmodules
git rm scripts/generate_indices.py scripts/dict_extract.py scripts/dict_render.py \
       scripts/generate_dict.py scripts/mkdocs_hooks.py scripts/macros_env.py
```

Then change `python scripts/<x>.py` to `python ssengine/scripts/<x>.py`
in `.github/workflows/deploy.yml`.

### CI (`.github/workflows/deploy.yml`)

The checkout step needs `submodules: true`:

```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    submodules: true
```

and the build steps run the engine from the repo root:

```yaml
- run: python ssengine/scripts/generate_indices.py
- run: python ssengine/scripts/generate_dict.py
```

### Updating the engine later

Make the fix in a clone of this repo, commit, push. Then in each content
repo:

```bash
cd ssengine
git pull origin main
cd ..
git add ssengine
git commit -m "Update engine submodule"
```

Each site pins its own commit of the engine, so nothing changes for a
site until you deliberately update its submodule pointer — matches your
"infrequent republish is fine" preference from earlier.

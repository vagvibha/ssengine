# Static Site Engine

Shared build-engine scripts for the साहित्यशास्त्रम् (sahitya) and शास्त्रम्
(shastra) MkDocs sites. Each site's own repo keeps its own content,
`gloss_types.yaml`, and `site_config.yaml` — this repo holds the Python
engine code, pulled in as a git submodule at `scripts/`.

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

Each site keeps its own `gloss_types.yaml` and `site_config.yaml`
directly in its own `scripts/` (not in this repo) — those are content
decisions per site, not engine code.

## Dictionaries (`dict/`)

Each site declares its dictionaries in its own `scripts/site_config.yaml`:

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
end-to-end tests that build a small throwaway site. That site links the
engine scripts in with symlinks, like a real content repo, and runs
`generate_dict.py` / `generate_indices.py` in a subprocess.
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

## Wiring it into each content repo as a submodule

From inside `sahitya/` (and separately, identically, inside `shastra/`):

```bash
# remove the now-duplicated copies that live directly in scripts/
git rm scripts/generate_indices.py scripts/dict_extract.py scripts/dict_render.py \
       scripts/generate_dict.py scripts/mkdocs_hooks.py scripts/macros_env.py

# add the ssengine repo as a submodule, checked out AT scripts/ssengine
git submodule add git@github.com:<you>/ssengine.git scripts/engine

# symlink (or copy, if you'd rather not symlink) each shared file back to
# where mkdocs.yml/the build workflow expect to find it
ln -s ssengine/scripts/generate_indices.py scripts/generate_indices.py
ln -s ssengine/scripts/dict_extract.py scripts/dict_extract.py
ln -s ssengine/scripts/dict_render.py scripts/dict_render.py
ln -s ssengine/scripts/generate_dict.py scripts/generate_dict.py
ln -s ssengine/scripts/mkdocs_hooks.py scripts/mkdocs_hooks.py
ln -s ssengine/scripts/macros_env.py scripts/macros_env.py

git add scripts .gitmodules
git commit -m "Pull shared engine scripts in as a submodule"
```

`gloss_types.yaml`/`site_config.yaml` stay exactly where they are in each
site's own `scripts/` — only the six files above move into the
submodule. Remember to set `topics: chandas_alankara: true` in
sahitya's `site_config.yaml` (shastra needs no change — false is the
default).

### CI (`.github/workflows/deploy.yml`)

Add `submodules: true` to the existing checkout step in both repos:

```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    submodules: true
```

### Updating the engine later

Make the fix in a clone of this repo, commit, push. Then in each content
repo:

```bash
cd scripts/engine
git pull origin main
cd ../..
git add scripts/engine
git commit -m "Update engine submodule"
```

Each site pins its own commit of the engine, so nothing changes for a
site until you deliberately update its submodule pointer — matches your
"infrequent republish is fine" preference from earlier.

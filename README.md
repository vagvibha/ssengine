# sahitya-shastra-engine

Shared build-engine scripts for the साहित्यशास्त्रम् (sahitya) and शास्त्रम्
(shastra) MkDocs sites. Each site's own repo keeps its own content,
`gloss_types.yaml`, and `site_config.yaml` — this repo holds only the
Python engine code that's genuinely identical between them, pulled in as
a git submodule at `scripts/`.

## What's here

- `dict_extract.py` — `<dict>`/`<dictref>` tag extraction for the
  external dictionary-generation workflow.
- `dict_render.py` — rendering/key-generation for that same workflow.
- `generate_dict.py` — walks the source tree and writes `dict/` output.
- `mkdocs_hooks.py` — Devanagari-safe slugification hook.
- `macros_env.py` — the `xref()` Jinja macro for hand-authored
  cross-references.

## What's deliberately NOT here yet

`generate_indices.py` — the main site-generation script — is not in this
repo yet. It's *almost* identical between the two sites now (topics,
paribhasha removal, gloss shorthand, and the directory-layout mechanism
are all fully unified), but sahitya's copy still carries the
chandas/alankara meter/figure glossary (TableEntry, build_glossary_page,
render_glossary_entry_page, the Shloka Table's छन्दः/अलङ्काराः columns,
the BeautifulSoup dependency), which shastra's content has no use for.

Folding that in requires making chandas/alankara a genuinely optional,
config-gated feature (only active when a site's `site_config.yaml` says
so — analogous to how `topics:` itself is already optional) rather than
"absent chandas.md just prints a warning on every build," which is what
would happen today if the two copies were merged as-is. Once that's
done, `generate_indices.py` can move into this repo too and both sites
would build from one identical copy end to end.

## Setting this up on GitHub

```bash
cd sahitya-shastra-engine
git init
git add .
git commit -m "Initial shared engine: dict generation + macros + hooks"
git branch -M main
git remote add origin git@github.com:<you>/sahitya-shastra-engine.git
git push -u origin main
```

## Wiring it into each content repo as a submodule

From inside `sahitya/` (and separately, identically, inside `shastra/`):

```bash
# remove the now-duplicated copies that live directly in scripts/
git rm scripts/dict_extract.py scripts/dict_render.py scripts/generate_dict.py \
       scripts/mkdocs_hooks.py scripts/macros_env.py

# add the engine repo as a submodule, checked out AT scripts/engine
git submodule add git@github.com:<you>/sahitya-shastra-engine.git scripts/engine

# symlink (or copy, if you'd rather not symlink) each shared file back to
# where generate_indices.py/mkdocs.yml expect to find it
ln -s engine/scripts/dict_extract.py scripts/dict_extract.py
ln -s engine/scripts/dict_render.py scripts/dict_render.py
ln -s engine/scripts/generate_dict.py scripts/generate_dict.py
ln -s engine/scripts/mkdocs_hooks.py scripts/mkdocs_hooks.py
ln -s engine/scripts/macros_env.py scripts/macros_env.py

git add scripts .gitmodules
git commit -m "Pull shared engine scripts in as a submodule"
```

`generate_indices.py` and `gloss_types.yaml`/`site_config.yaml` stay
exactly where they are in each site's own `scripts/` — only the five
files above move into the submodule.

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

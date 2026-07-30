# Releasing, PyPI and the docs site

**When to reach for this:** cutting a version, the first PyPI publish, or the
docs site has drifted from the code.

## The three pipelines

| Workflow | Fires on | Does |
|---|---|---|
| `tests.yaml` | push / PR | ruff + `pytest` on 3.12 and 3.13 |
| `docs.yaml` | push to `main` | regenerates the gallery, renders Quarto, publishes `gh-pages` |
| `release.yaml` | **published** GitHub release | gates, checks tag ↔ version, builds, publishes to PyPI |

Publishing is triggered by *publishing a GitHub release*, not by pushing a tag.
Cutting the release is the single action that ships a version.

## Cutting a version

Order matters — the gate must run **after** the bump, not before:

1. **Bump both places.** `version` in `pyproject.toml` and `__version__` in
   `prism/__init__.py`. They must agree or `release.yaml` refuses the tag.
2. **Move the `[Unreleased]` block** in `CHANGELOG.md` under a
   `## [X.Y.Z] - YYYY-MM-DD` heading, and leave a fresh empty `[Unreleased]`.
3. **Regenerate the gallery** if anything visual changed:
   `uv run python scripts/build_gallery.py`, then commit the SVGs and the two
   generated pages.
4. **Run the gate now, after the bump:**
   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run python -m pytest -q
   ```
   Read the exit code directly. Never pipe a gate into `tail`/`head` — you get
   the pager's status, and a red gate turns green.
5. **Commit and push**, then cut the release:
   ```bash
   gh release create vX.Y.Z --generate-notes
   ```
6. **Verify by ground truth**, not by a green check mark:
   ```bash
   curl -s https://pypi.org/pypi/prism-svg/json | jq -r .info.version
   uv run --with prism-svg==X.Y.Z --no-project python -c "import prism; print(prism.__version__)"
   ```
   The PyPI index cache can lag a successful publish; a downstream `uv lock` may
   still resolve the previous version until `uv lock --refresh-package prism-svg`.

### The footgun this repo already stepped in

`tests/test_package.py` originally asserted `__version__ == "0.1.0"` against a
hardcoded literal, which means every bump breaks the release gate *inside the
release workflow* until someone edits the test. It now asserts against
`importlib.metadata.version("prism-svg")` — the invariant that actually matters
(the module and the package metadata agree) and one that survives a bump.
Version-identity tests should never pin a literal.

## The first publish (not done yet as of 2026-07-30)

`prism-svg` is **not on PyPI**, there is no `v0.1.0` tag, and the README's
`pip install prism-svg` is therefore still a promise. Before the first release
can succeed, three things must exist:

1. A **trusted publisher** configured on PyPI for the `prism-svg` project:
   owner `apiad`, repo `prism`, workflow `release.yaml`, environment `pypi`.
   For a name that does not exist yet this is a *pending* publisher, created at
   <https://pypi.org/manage/account/publishing/>.
2. A GitHub **environment named `pypi`** on `apiad/prism` (the workflow declares
   it; the OIDC subject includes it, so a mismatch fails the exchange).
3. The name itself claimed — `prism-svg` was unregistered when this was written.
   The publish claims it; nothing else needs doing.

No API token is stored anywhere, and none should be. If a publish fails with an
OIDC error, the mismatch is almost always the environment name or the workflow
filename in the publisher config — not the code.

## The docs site

<https://apiad.github.io/prism> — published from `gh-pages` by `docs.yaml` on
every push to `main`. No manual step.

The site cannot drift from the code, by construction:

- `docs.yaml` runs `scripts/build_gallery.py` **before** rendering, so every
  image on the site is rendered from an example that currently works.
- `docs/catalog.qmd` and `docs/themes.qmd` are *generated files*. Hand-editing
  them is always wrong; the edit is lost on the next push.
- `docs/_quarto.yml` renders `*.qmd` only, so `docs/specs/` and `docs/plans/`
  stay internal design history rather than published pages.
- `tests/test_docs.py` fails if an archetype has no example, the gallery is
  incomplete, a doc page references a missing image, or `SKILL.md` /
  `docs/agents.qmd` name an icon, theme or archetype that does not exist.

Locally:

```bash
uv run python scripts/build_gallery.py
uv run quarto render docs        # output in docs/_site (gitignored)
```

## Links in the README

The README is read on GitHub, where a `.qmd` renders as raw source. Prose links
to documentation should point at the **published site**
(`https://apiad.github.io/prism/catalog.html`), not at `docs/catalog.qmd`.
Relative links are correct only for files GitHub renders — images, `SKILL.md`,
`know-how/*.md`.
